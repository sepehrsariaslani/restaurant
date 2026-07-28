# Copyright (c) 2026, Restaurant and contributors
"""Menu engineering: profit/popularity matrix with smart recommendations.

Classifies each sellable product into the classic 2x2 menu-engineering
matrix (popularity x margin) and generates actionable suggestions:
raise price, cut cost, advertise, or remove — plus an optimal price
suggestion derived from the live BOM cost and a target margin.

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_management_datetime_bounds,
	_table_columns_from_rows,
)

__all__ = [
	"MENUENG_REPORT_KEYS",
	"menueng_build_report_bi",
	"get_management_report_menu_engineering",
]

MENUENG_REPORT_KEYS = {"menu-engineering"}

QUADRANTS = {
	"star": _("ستاره (پرفروش و پرسود)"),
	"workhorse": _("اسب کار (پرفروش، حاشیه کم)"),
	"puzzle": _("معما (کم‌فروش، حاشیه خوب)"),
	"dog": _("نامناسب (کم‌فروش و کم‌سود)"),
}

ACTION_RAISE_PRICE = _("افزایش قیمت")
ACTION_CUT_COST = _("کاهش بهای تمام‌شده")
ACTION_ADVERTISE = _("تبلیغات و عرضه بهتر")
ACTION_KEEP = _("حفظ و تقویت")
ACTION_REMOVE = _("حذف یا بازطراحی")


# ---------------------------------------------------------------------------
# Data assembly
# ---------------------------------------------------------------------------


def _me_ops_call(helper_name, *args, **kwargs):
	"""Lazy bridge into api_ops (import-cycle safety)."""
	from restaurant import api_ops

	fn = getattr(api_ops, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_ops helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _me_sold_items(date_from=None, date_to=None, branch=None):
	"""Per-item sales aggregation over confirmed Sales Orders."""
	if not frappe.db.exists("DocType", "Sales Order"):
		return []
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	conditions = ["so.docstatus = 1", "so.creation BETWEEN %(start)s AND %(end)s"]
	params = {"start": start_dt, "end": end_dt}
	if branch:
		conditions.append("so.company = %(branch)s")
		params["branch"] = branch
	return frappe.db.sql(
		f"""
		SELECT soi.item_code, MAX(soi.item_name) AS item_name,
			   SUM(soi.qty) AS qty, SUM(soi.amount) AS revenue,
			   AVG(soi.rate) AS avg_price
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE {' AND '.join(conditions)}
		GROUP BY soi.item_code
		ORDER BY qty DESC
		""",
		params,
		as_dict=True,
	)


def compute_menu_engineering(date_from=None, date_to=None, target_margin_pct=65, min_margin_pct=25, branch=None):
	"""Build the full menu-engineering dataset for a window."""
	target_margin = flt(target_margin_pct) or 65.0
	min_margin = flt(min_margin_pct)
	rows = _me_sold_items(date_from=date_from, date_to=date_to, branch=branch)
	cost_map = _me_ops_call("_ops_unit_cost_map")

	items = []
	for row in rows:
		qty = flt(row.get("qty"))
		revenue = flt(row.get("revenue"))
		if qty <= 0:
			continue
		price = flt(revenue / qty, 2) if revenue else flt(row.get("avg_price"))
		cost = flt(cost_map.get(row["item_code"], 0))
		margin_value = flt(price - cost, 2)
		margin_pct = flt((margin_value / price) * 100, 1) if price > 0 else 0.0
		suggested_price = 0
		if cost > 0 and target_margin < 100:
			raw = cost / (1 - target_margin / 100.0)
			suggested_price = int(round(raw / 1000.0) * 1000)  # round to thousands
		items.append(
			{
				"item_code": row["item_code"],
				"item_name": row.get("item_name") or row["item_code"],
				"qty": qty,
				"revenue": flt(revenue),
				"price": price,
				"cost": cost,
				"margin_value": margin_value,
				"margin_pct": margin_pct,
				"total_profit": flt(margin_value * qty),
				"suggested_price": suggested_price,
			}
		)
	if not items:
		return {"items": [], "summary": _me_empty_summary(target_margin), "quadrants": {}}

	avg_qty = sum(i["qty"] for i in items) / len(items)
	margin_values = [i["margin_pct"] for i in items if i["price"] > 0]
	avg_margin = sum(margin_values) / len(margin_values) if margin_values else 0.0

	quadrants = {"star": [], "workhorse": [], "puzzle": [], "dog": []}
	profitable = 0
	loss_making = 0
	for item in items:
		high_pop = item["qty"] >= avg_qty
		high_margin = item["margin_pct"] >= avg_margin
		if high_pop and high_margin:
			key = "star"
		elif high_pop and not high_margin:
			key = "workhorse"
		elif not high_pop and high_margin:
			key = "puzzle"
		else:
			key = "dog"
		if key == "star":
			action = ACTION_KEEP
			if item["suggested_price"] and item["suggested_price"] > item["price"] * 1.05:
				action = _("حفظ؛ کاندید افزایش قیمت جزئی تا {0}").format(f"{item['suggested_price']:,}")
		elif key == "workhorse":
			parts = []
			if item["suggested_price"] and item["suggested_price"] > item["price"]:
				parts.append(_("افزایش قیمت به حدود {0}").format(f"{item['suggested_price']:,}"))
			parts.append(ACTION_CUT_COST)
			action = _(" یا ").join(parts)
		elif key == "puzzle":
			action = _("{0} (کمپین، جایگاه بهتر در منو، ترکیب با ستاره‌ها)").format(ACTION_ADVERTISE)
		else:
			action = ACTION_REMOVE
		if item["cost"] <= 0:
			action = _("ابتدا دستور پخت/بهای خرید را تکمیل کنید؛ سپس ") + action
		item["quadrant"] = key
		item["quadrant_label"] = QUADRANTS[key]
		item["action"] = action
		if item["margin_pct"] >= target_margin:
			profitable += 1
		if item["margin_pct"] < min_margin or item["margin_value"] < 0:
			loss_making += 1
		quadrants[key].append(item["item_name"])

	summary = {
		"items_count": len(items),
		"total_qty": flt(sum(i["qty"] for i in items)),
		"total_revenue": flt(sum(i["revenue"] for i in items)),
		"total_profit": flt(sum(i["total_profit"] for i in items)),
		"avg_popularity_qty": flt(avg_qty, 1),
		"avg_margin_pct": flt(avg_margin, 1),
		"target_margin_pct": target_margin,
		"min_margin_pct": min_margin,
		"profitable_count": profitable,
		"loss_count": loss_making,
		"stars": len(quadrants["star"]),
		"workhorses": len(quadrants["workhorse"]),
		"puzzles": len(quadrants["puzzle"]),
		"dogs": len(quadrants["dog"]),
	}
	return {"items": items, "summary": summary, "quadrants": quadrants}


def _me_empty_summary(target_margin):
	return {
		"items_count": 0,
		"total_qty": 0,
		"total_revenue": 0,
		"total_profit": 0,
		"avg_popularity_qty": 0,
		"avg_margin_pct": 0,
		"target_margin_pct": flt(target_margin),
		"min_margin_pct": 0,
		"profitable_count": 0,
		"loss_count": 0,
		"stars": 0,
		"workhorses": 0,
		"puzzles": 0,
		"dogs": 0,
	}


# ---------------------------------------------------------------------------
# Report endpoint
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_menu_engineering(date_from=None, date_to=None, target_margin_pct=65, branch=None):
	_ensure_management_access()
	data = compute_menu_engineering(date_from=date_from, date_to=date_to, target_margin_pct=target_margin_pct, branch=branch)
	rows = [
		{
			"item": item["item_name"],
			"item_code": item["item_code"],
			"quadrant": item["quadrant_label"],
			"qty": item["qty"],
			"revenue": item["revenue"],
			"price": item["price"],
			"cost": item["cost"],
			"margin_value": item["margin_value"],
			"margin_pct": item["margin_pct"],
			"total_profit": item["total_profit"],
			"suggested_price": item["suggested_price"],
			"action": item["action"],
		}
		for item in data["items"]
	]
	return _compose_management_report(
		"menu-engineering",
		_("مهندسی منو و پیشنهادهای هوشمند"),
		data["summary"],
		rows,
		date_from=date_from,
		date_to=date_to,
		orders=[],
	)


# ---------------------------------------------------------------------------
# BI
# ---------------------------------------------------------------------------


def menueng_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	kpis = [
		_bi_kpi("me-items", _("اقلام فروخته‌شده"), cint(summary.get("items_count")), "count", None),
		_bi_kpi("me-profitable", _("پرسود (حاشیه ≥ هدف)"), cint(summary.get("profitable_count")), "count", None),
		_bi_kpi("me-loss", _("زیان‌ده / حاشیه پایین"), cint(summary.get("loss_count")), "count", None),
		_bi_kpi("me-profit", _("سود ناخالص کل"), flt(summary.get("total_profit")), "money", None),
		_bi_kpi("me-margin", _("میانگین حاشیه سود"), flt(summary.get("avg_margin_pct")), "percent", None),
	]

	quadrant_rows = [
		{"quadrant": QUADRANTS["star"], "count": cint(summary.get("stars"))},
		{"quadrant": QUADRANTS["workhorse"], "count": cint(summary.get("workhorses"))},
		{"quadrant": QUADRANTS["puzzle"], "count": cint(summary.get("puzzles"))},
		{"quadrant": QUADRANTS["dog"], "count": cint(summary.get("dogs"))},
	]
	charts = [
		{
			"key": "me-quadrants",
			"type": "donut",
			"title": _("توزیع محصولات در ماتریس مهندسی منو"),
			"data": quadrant_rows,
			"label_key": "quadrant",
			"value_key": "count",
		},
		{
			"key": "me-top-margin",
			"type": "bar",
			"title": _("۱۰ قلم برتر بر اساس سود کل"),
			"x_key": "item",
			"series": [
				{
					"key": "total_profit",
					"label": _("سود کل"),
					"color": "#2f6f5c",
					"values": [flt(r.get("total_profit")) for r in sorted(rows, key=lambda r: flt(r.get("total_profit")), reverse=True)[:10]],
				}
			],
			"categories": [r.get("item") for r in sorted(rows, key=lambda r: flt(r.get("total_profit")), reverse=True)[:10]],
		},
	]

	tables = [
		{
			"key": "me-all",
			"title": _("جدول کامل مهندسی منو (قیمت، بها، حاشیه، پیشنهاد)"),
			"columns": _table_columns_from_rows(rows),
			"rows": rows,
		},
		{
			"key": "me-loss",
			"title": _("اقلام زیان‌ده (اولویت اصلاح قیمت/هزینه یا حذف)"),
			"columns": _table_columns_from_rows(rows),
			"rows": [r for r in rows if flt(r.get("margin_pct")) < flt(summary.get("min_margin_pct")) or flt(r.get("margin_value")) < 0],
		},
		{
			"key": "me-stars",
			"title": _("ستاره‌های منو (حفظ و تبلیغ)"),
			"columns": _table_columns_from_rows(rows),
			"rows": [r for r in rows if r.get("quadrant") == QUADRANTS["star"]],
		},
	]

	insights = []
	top_star = next((r for r in sorted(rows, key=lambda r: flt(r.get("total_profit")), reverse=True) if r.get("quadrant") == QUADRANTS["star"]), None)
	if top_star:
		insights.append(
			{
				"key": "me-star",
				"severity": "info",
				"text": _("پرسودترین محصول: «{0}» با سود {1}. آن را در دید بهتر منو نگه دارید.").format(
					top_star.get("item"), f"{flt(top_star.get('total_profit')):,}"
				),
			}
		)
	if cint(summary.get("loss_count")) > 0:
		insights.append(
			{
				"key": "me-loss",
				"severity": "warn",
				"text": _("{0} قلم حاشیه سود پایین‌تر از {1}٪ دارند؛ قیمت‌گذاری یا پیمانه مواد آن‌ها را بازبینی کنید.").format(
					cint(summary.get("loss_count")), flt(summary.get("min_margin_pct"))
				),
			}
		)
	if cint(summary.get("puzzles")) > 0:
		insights.append(
			{
				"key": "me-puzzle",
				"severity": "info",
				"text": _("{0} قلم حاشیه خوب اما فروش کم دارند؛ با کمپین باشگاه مشتریان یا جایگاه بهتر در منو آن‌ها را تبلیغ کنید.").format(
					cint(summary.get("puzzles"))
				),
			}
		)

	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _me_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_me_register_into_api_module()
