# Copyright (c) 2026, Restaurant and contributors
"""Multi-branch management.

Branches are modeled as ERPNext Companies (flagged with the existing
``restaurant_is_branch`` custom field); every Sales Order carries the
company/branch it belongs to, so sales, COGS and live performance can be
reported aggregated or per branch. Customer transfer between branches is
tracked via the ``restaurant_branch`` custom field on Customer.

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_has_column,
	_management_datetime_bounds,
	_parse_json,
	_table_columns_from_rows,
)

__all__ = [
	"BRANCH_REPORT_KEYS",
	"branch_build_report_bi",
	"_br_ensure_ops_ready",
	"list_management_branches",
	"save_management_branch",
	"update_management_branch_status",
	"transfer_management_customer_branch",
	"get_management_branch_boot",
	"suggest_nearest_branch",
	"get_management_report_branch_performance",
]

BRANCH_REPORT_KEYS = {"branch-performance"}


# ---------------------------------------------------------------------------
# Lazy bridges
# ---------------------------------------------------------------------------


def _br_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	fn = getattr(api_feature_pack, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_feature_pack helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _br_ops_call(helper_name, *args, **kwargs):
	from restaurant import api_ops

	fn = getattr(api_ops, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_ops helper missing: {helper_name}")
	return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# Provisioning
# ---------------------------------------------------------------------------


def _br_ensure_ops_ready():
	try:
		_br_fp_call(
			"_fp_ensure_custom_fields",
			"Customer",
			[
				{"fieldname": "restaurant_branch_section", "label": "شعبه", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_branch", "label": "شعبه اصلی مشتری", "fieldtype": "Link", "options": "Company"},
			],
			anchor_candidates=["restaurant_club_section", "customer_type", "customer_group"],
		)
		_br_fp_call(
			"_fp_ensure_custom_fields",
			"Warehouse",
			[
				{"fieldname": "restaurant_branch", "label": "شعبه", "fieldtype": "Link", "options": "Company"},
			],
			anchor_candidates=["warehouse_type", "company"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant branch ensure fields failed")


# ---------------------------------------------------------------------------
# Branch helpers
# ---------------------------------------------------------------------------


def _br_branch_rows(active_only=False):
	"""Companies flagged as restaurant branches."""
	if not frappe.db.exists("DocType", "Company"):
		return []
	filters = {}
	if _has_column("Company", "restaurant_is_branch"):
		filters["restaurant_is_branch"] = 1
	if active_only and _has_column("Company", "restaurant_branch_active"):
		filters["restaurant_branch_active"] = 1
	fields = ["name", "company_name", "abbr"]
	for extra in ("restaurant_is_branch", "restaurant_branch_active", "restaurant_public_title", "restaurant_branch_address", "restaurant_branch_phone", "restaurant_branch_lat", "restaurant_branch_lng"):
		if _has_column("Company", extra):
			fields.append(extra)
	rows = frappe.get_all("Company", filters=filters, fields=fields, order_by="company_name asc", limit_page_length=200)
	if not rows and filters:
		# fallback: no branches flagged yet → show all companies so the page is usable
		rows = frappe.get_all("Company", fields=fields, order_by="company_name asc", limit_page_length=200)
	return rows


def _br_branch_label(row):
	return (row.get("restaurant_public_title") or row.get("company_name") or row.get("name") or "").strip()


def _br_sales_by_period(date_from=None, date_to=None):
	"""{company: {orders, sales}} over submitted Sales Orders in window."""
	if not frappe.db.exists("DocType", "Sales Order"):
		return {}
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	rows = frappe.db.sql(
		"""
		SELECT company, COUNT(*) AS orders, COALESCE(SUM(grand_total),0) AS sales
		FROM `tabSales Order`
		WHERE docstatus = 1 AND creation BETWEEN %(start)s AND %(end)s
		GROUP BY company
		""",
		{"start": start_dt, "end": end_dt},
		as_dict=True,
	)
	return {row["company"]: {"orders": cint(row["orders"]), "sales": flt(row["sales"])} for row in rows}


# ---------------------------------------------------------------------------
# Management endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_branch_boot():
	_ensure_management_access()
	_br_ensure_ops_ready()
	branches = [_serialize_branch(row) for row in _br_branch_rows()]
	today_sales = _br_sales_by_period(today(), today())
	for branch in branches:
		kpi = today_sales.get(branch["name"]) or {}
		branch["today_orders"] = cint(kpi.get("orders"))
		branch["today_sales"] = flt(kpi.get("sales"))
	customers_by_branch = {}
	if _has_column("Customer", "restaurant_branch"):
		rows = frappe.get_all(
			"Customer",
			filters={"disabled": 0, "restaurant_branch": ["!=", ""]},
			fields=["restaurant_branch", "COUNT(*) AS count"],
			group_by="restaurant_branch",
		)
		customers_by_branch = {row["restaurant_branch"]: cint(row["count"]) for row in rows}
	for branch in branches:
		branch["customers"] = customers_by_branch.get(branch["name"], 0)
	return {
		"branches": branches,
		"branch_count": len(branches),
		"max_recommended": 5,
		"warehouses": frappe.get_all("Warehouse", fields=["name", "restaurant_branch"] if _has_column("Warehouse", "restaurant_branch") else ["name"], filters={"is_group": 0}, limit_page_length=300) if frappe.db.exists("DocType", "Warehouse") else [],
	}


def _serialize_branch(row):
	return {
		"name": row.get("name"),
		"company_name": row.get("company_name") or row.get("name"),
		"abbr": row.get("abbr") or "",
		"label": _br_branch_label(row),
		"is_branch": cint(row.get("restaurant_is_branch")),
		"is_active": cint(row.get("restaurant_branch_active")) if row.get("restaurant_branch_active") is not None else 1,
		"address": row.get("restaurant_branch_address") or "",
		"phone": row.get("restaurant_branch_phone") or "",
		"lat": flt(row.get("restaurant_branch_lat"), 6),
		"lng": flt(row.get("restaurant_branch_lng"), 6),
	}


@frappe.whitelist()
def list_management_branches(active_only=0):
	_ensure_management_access()
	rows = _br_branch_rows(active_only=cint(active_only))
	return {"branches": [_serialize_branch(row) for row in rows], "count": len(rows)}


@frappe.whitelist()
def save_management_branch(payload=None):
	"""Create/update a branch (ERPNext Company with branch fields)."""
	_ensure_management_access()
	payload = _parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	company_name = (payload.get("company_name") or "").strip()
	if not company_name and not name:
		frappe.throw(_("نام شعبه الزامی است."))
	if name and frappe.db.exists("Company", name):
		doc = frappe.get_doc("Company", name)
	else:
		if frappe.db.exists("Company", company_name):
			doc = frappe.get_doc("Company", company_name)
		else:
			doc = frappe.new_doc("Company")
			# New ERPNext company → default CoA/warehouses/etc. get provisioned.
			base = frappe.get_all("Company", filters={}, fields=["default_currency", "country"], limit_page_length=1)
			doc.company_name = company_name
			doc.abbr = (payload.get("abbr") or company_name[:3]).strip()
			doc.default_currency = (payload.get("default_currency") or (base[0].get("default_currency") if base else "") or "IRR").strip()
			doc.country = (payload.get("country") or (base[0].get("country") if base else "") or "Iran").strip()
	field_map = {
		"restaurant_is_branch": lambda v: cint(v),
		"restaurant_branch_active": lambda v: cint(v),
		"restaurant_public_title": lambda v: (v or "").strip(),
		"restaurant_branch_address": lambda v: (v or "").strip(),
		"restaurant_branch_phone": lambda v: (v or "").strip(),
		"restaurant_branch_lat": lambda v: flt(v, 6),
		"restaurant_branch_lng": lambda v: flt(v, 6),
	}
	for fieldname, normalize in field_map.items():
		if payload.get(fieldname) is not None and hasattr(doc, fieldname):
			setattr(doc, fieldname, normalize(payload.get(fieldname)))
	if payload.get("company_name"):
		doc.company_name = company_name
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "branch": _serialize_branch(doc.as_dict())}


@frappe.whitelist()
def update_management_branch_status(payload=None):
	_ensure_management_access()
	payload = _parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	if not frappe.db.exists("Company", name):
		frappe.throw(_("شعبه یافت نشد: {0}").format(name or "-"))
	if _has_column("Company", "restaurant_branch_active"):
		frappe.db.set_value("Company", name, "restaurant_branch_active", cint(payload.get("is_active")), update_modified=False)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def transfer_management_customer_branch(payload=None):
	"""Move a customer to another branch (single or bulk by mobile)."""
	_ensure_management_access()
	_br_ensure_ops_ready()
	payload = _parse_json(payload, {})
	customer = (payload.get("customer") or "").strip()
	target = (payload.get("target_branch") or "").strip()
	if not customer or not target:
		frappe.throw(_("مشتری و شعبه مقصد الزامی است."))
	if not frappe.db.exists("Customer", customer):
		by_mobile = frappe.db.get_value("Customer", filters={"mobile_no": customer}, fieldname="name")
		customer = by_mobile or ""
	if not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد."))
	if not frappe.db.exists("Company", target):
		frappe.throw(_("شعبه مقصد یافت نشد: {0}").format(target))
	previous = frappe.db.get_value("Customer", customer, "restaurant_branch") if _has_column("Customer", "restaurant_branch") else ""
	frappe.db.set_value("Customer", customer, "restaurant_branch", target, update_modified=False)
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Customer",
				"reference_name": customer,
				"content": _("انتقال از شعبه «{0}» به «{1}»").format(previous or "-", target),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass
	frappe.db.commit()
	return {"status": "success", "customer": customer, "from_branch": previous, "to_branch": target}


@frappe.whitelist()
def suggest_nearest_branch(mobile="", customer=""):
	"""Suggest the branch a customer usually orders from (or first active branch)."""
	customer_name = (customer or "").strip()
	mobile = (mobile or "").strip()
	if not customer_name and mobile:
		customer_name = frappe.db.get_value("Customer", filters={"mobile_no": mobile}, fieldname="name") or ""
	suggested = ""
	if customer_name and frappe.db.exists("Sales Order", {"customer": customer_name}):
		row = frappe.db.sql(
			"""SELECT company, COUNT(*) AS c FROM `tabSales Order` WHERE customer = %(c)s AND docstatus = 1 GROUP BY company ORDER BY c DESC LIMIT 1""",
			{"c": customer_name},
			as_dict=True,
		)
		if row:
			suggested = row[0]["company"]
	if not suggested:
		branches = _br_branch_rows(active_only=True)
		suggested = branches[0]["name"] if branches else ""
	return {"suggested_branch": suggested, "customer": customer_name}


# ---------------------------------------------------------------------------
# Branch performance report
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_branch_performance(date_from=None, date_to=None):
	_ensure_management_access()
	sales_map = _br_sales_by_period(date_from=date_from, date_to=date_to)
	cost_map = _br_ops_call("_ops_unit_cost_map")
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	cogs_rows = frappe.db.sql(
		"""
		SELECT so.company, soi.item_code, SUM(soi.qty) AS qty
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE so.docstatus = 1 AND so.creation BETWEEN %(start)s AND %(end)s
		GROUP BY so.company, soi.item_code
		""",
		{"start": start_dt, "end": end_dt},
		as_dict=True,
	)
	cogs_map = {}
	for row in cogs_rows:
		cogs_map[row["company"]] = cogs_map.get(row["company"], 0.0) + flt(row["qty"]) * flt(cost_map.get(row["item_code"], 0.0))

	labels = {row["name"]: _br_branch_label(row) for row in _br_branch_rows()}
	rows = []
	for company, kpi in sorted(sales_map.items(), key=lambda kv: flt(kv[1]["sales"]), reverse=True):
		sales = flt(kpi["sales"])
		cogs = flt(cogs_map.get(company, 0.0))
		rows.append(
			{
				"branch": labels.get(company, company),
				"company": company,
				"orders": cint(kpi["orders"]),
				"sales": sales,
				"cogs": cogs,
				"gross_profit": flt(sales - cogs),
				"avg_order": flt(sales / cint(kpi["orders"])) if cint(kpi["orders"]) else 0.0,
			}
		)
	summary = {
		"branches": len(rows),
		"orders_total": sum(r["orders"] for r in rows),
		"sales_total": flt(sum(r["sales"] for r in rows)),
		"gross_total": flt(sum(r["gross_profit"] for r in rows)),
	}
	return _compose_management_report(
		"branch-performance",
		_("عملکرد شعب (تجمیعی و تفکیکی)"),
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		orders=[],
	)


# ---------------------------------------------------------------------------
# BI
# ---------------------------------------------------------------------------


def branch_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	kpis = [
		_bi_kpi("br-count", _("شعب دارای فروش"), cint(summary.get("branches")), "count", None),
		_bi_kpi("br-sales", _("فروش تجمیعی"), flt(summary.get("sales_total")), "money", None),
		_bi_kpi("br-orders", _("سفارش‌ها"), cint(summary.get("orders_total")), "count", None),
		_bi_kpi("br-gross", _("سود ناخالص تجمیعی"), flt(summary.get("gross_total")), "money", None),
	]
	charts = [
		{
			"key": "br-sales-bar",
			"type": "bar",
			"title": _("فروش هر شعبه"),
			"categories": [r.get("branch") for r in rows],
			"series": [{"key": "sales", "label": _("فروش"), "color": "#2f6f5c", "values": [flt(r.get("sales")) for r in rows]}],
		},
		{
			"key": "br-profit-bar",
			"type": "bar",
			"title": _("سود ناخالص هر شعبه"),
			"categories": [r.get("branch") for r in rows],
			"series": [{"key": "gross", "label": _("سود ناخالص"), "color": "#3e8ed0", "values": [flt(r.get("gross_profit")) for r in rows]}],
		},
	]
	tables = [
		{"key": "br-table", "title": _("جدول تفکیکی شعب"), "columns": _table_columns_from_rows(rows), "rows": rows},
	]
	insights = []
	if rows:
		best = max(rows, key=lambda r: flt(r.get("sales")))
		worst = min(rows, key=lambda r: flt(r.get("sales")))
		if len(rows) > 1:
			insights.append(
				{
					"key": "br-best-worst",
					"severity": "info",
					"text": _("قوی‌ترین شعبه «{0}» با فروش {1} و ضعیف‌ترین «{2}» با فروش {3} است.").format(
						best.get("branch"), f"{flt(best.get('sales')):,}", worst.get("branch"), f"{flt(worst.get('sales')):,}"
					),
				}
			)
	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _br_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_br_register_into_api_module()
