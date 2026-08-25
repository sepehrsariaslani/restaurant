# Copyright (c) 2026, Restaurant and contributors
"""Self-order kiosk & food-court kiosk.

- Management CRUD for food-court booths (Restaurant Vendor) and the
  ``restaurant_vendor`` link on Item, so every order can be grouped per booth.
- Guest kiosk endpoints powering the standalone ``/kiosk`` page
  (menu comes from the existing storefront endpoints; orders are created
  through the same ``_create_sales_order`` pipeline the website uses, so
  KDS, printers, printers, loyalty and payments stay identical).
- Per-booth sales report (food-court management).

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_create_sales_order,
	_ensure_management_access,
	_has_column,
	_management_datetime_bounds,
	_parse_json,
	_table_columns_from_rows,
)

__all__ = [
	"KIOSK_REPORT_KEYS",
	"VENDOR_DOCTYPE",
	"kiosk_build_report_bi",
	"_ko_ensure_ops_ready",
	"list_management_vendors",
	"save_management_vendor",
	"delete_management_vendor",
	"get_kiosk_boot",
	"kiosk_place_order",
	"get_management_report_vendor_sales",
]

KIOSK_REPORT_KEYS = {"vendor-sales"}
VENDOR_DOCTYPE = "Restaurant Vendor"


# ---------------------------------------------------------------------------
# Lazy bridges
# ---------------------------------------------------------------------------


def _ko_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	fn = getattr(api_feature_pack, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_feature_pack helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _ko_ops_call(helper_name, *args, **kwargs):
	from restaurant import api_ops

	fn = getattr(api_ops, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_ops helper missing: {helper_name}")
	return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# Provisioning & settings
# ---------------------------------------------------------------------------


def _ko_ensure_ops_ready():
	try:
		_ko_fp_call(
			"_fp_ensure_custom_fields",
			"Item",
			[
				{"fieldname": "restaurant_vendor_section", "label": "غرفه فودکورت", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_vendor", "label": "غرفه", "fieldtype": "Link", "options": VENDOR_DOCTYPE},
			],
			anchor_candidates=["restaurant_branch", "item_group", "stock_uom"],
		)
		_ko_fp_call(
			"_fp_ensure_custom_fields",
			"Restaurant Web Settings",
			[
				{"fieldname": "restaurant_kiosk_section", "label": "کیوسک سفارش‌گیر", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_kiosk_enabled", "label": "کیوسک فعال", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_kiosk_title", "label": "عنوان کیوسک", "fieldtype": "Data"},
				{"fieldname": "restaurant_kiosk_brand_color", "label": "رنگ برند کیوسک", "fieldtype": "Color"},
				{"fieldname": "restaurant_kiosk_column", "label": "", "fieldtype": "Column Break"},
				{"fieldname": "restaurant_kiosk_foodcourt_mode", "label": "حالت فودکورت (چند غرفه)", "fieldtype": "Check", "default": "0"},
				{"fieldname": "restaurant_kiosk_sms_ready", "label": "اطلاع آماده‌سازی با پیامک", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_kiosk_default_branch", "label": "شعبه پیش‌فرض کیوسک", "fieldtype": "Link", "options": "Company"},
			],
			anchor_candidates=["restaurant_callcenter_section", "restaurant_reservation_section", "restaurant_club_section", "configuration_tab"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant kiosk ensure fields failed")


def _ko_setting(fieldname, default=None):
	try:
		value = frappe.db.get_single_value("Restaurant Web Settings", fieldname)
		return default if value in (None, "") else value
	except Exception:
		return default


# ---------------------------------------------------------------------------
# Vendor (booth) management
# ---------------------------------------------------------------------------


def _serialize_vendor(row):
	return {
		"name": row.get("name"),
		"vendor_name": row.get("vendor_name") or "",
		"brand_color": row.get("brand_color") or "",
		"logo": row.get("logo") or "",
		"branch": row.get("branch") or "",
		"is_active": cint(row.get("is_active")),
		"description": row.get("description") or "",
	}


@frappe.whitelist()
def list_management_vendors(include_inactive=0):
	_ensure_management_access()
	if not frappe.db.exists("DocType", VENDOR_DOCTYPE):
		return {"vendors": [], "count": 0}
	filters = {}
	if not cint(include_inactive):
		filters["is_active"] = 1
	rows = frappe.get_all(
		VENDOR_DOCTYPE,
		filters=filters,
		fields=["name", "vendor_name", "brand_color", "logo", "branch", "is_active", "description"],
		order_by="vendor_name asc",
		limit_page_length=300,
	)
	return {"vendors": [_serialize_vendor(row) for row in rows], "count": len(rows)}


@frappe.whitelist()
def save_management_vendor(payload=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", VENDOR_DOCTYPE):
		frappe.throw(_("داکتایپ غرفه هنوز ساخته نشده؛ migrate اجرا کنید."))
	payload = _parse_json(payload, {})
	vendor_name = (payload.get("vendor_name") or "").strip()
	if not vendor_name:
		frappe.throw(_("نام غرفه الزامی است."))
	name = (payload.get("name") or "").strip()
	if name and frappe.db.exists(VENDOR_DOCTYPE, name):
		doc = frappe.get_doc(VENDOR_DOCTYPE, name)
	else:
		doc = frappe.new_doc(VENDOR_DOCTYPE)
	doc.vendor_name = vendor_name
	for fieldname in ("brand_color", "logo", "description"):
		if payload.get(fieldname) is not None:
			setattr(doc, fieldname, (payload.get(fieldname) or "").strip())
	if payload.get("branch") is not None:
		doc.branch = (payload.get("branch") or "").strip() or None
	if payload.get("is_active") is not None:
		doc.is_active = cint(payload.get("is_active"))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "vendor": _serialize_vendor(doc.as_dict())}


@frappe.whitelist()
def delete_management_vendor(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(VENDOR_DOCTYPE, name):
		frappe.throw(_("غرفه یافت نشد."))
	frappe.delete_doc(VENDOR_DOCTYPE, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


# ---------------------------------------------------------------------------
# Kiosk guest endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def get_kiosk_boot():
	"""Kiosk page boot: branding, mode, vendors, default branch."""
	_ko_ensure_ops_ready()
	vendors = []
	if frappe.db.exists("DocType", VENDOR_DOCTYPE):
		vendors = [
			_serialize_vendor(row)
			for row in frappe.get_all(
				VENDOR_DOCTYPE,
				filters={"is_active": 1},
				fields=["name", "vendor_name", "brand_color", "logo", "branch", "is_active", "description"],
				order_by="vendor_name asc",
				limit_page_length=100,
			)
		]
	return {
		"enabled": cint(_ko_setting("restaurant_kiosk_enabled", 1)) == 1,
		"title": (_ko_setting("restaurant_kiosk_title", "") or "").strip(),
		"brand_color": (_ko_setting("restaurant_kiosk_brand_color", "") or "").strip(),
		"foodcourt_mode": cint(_ko_setting("restaurant_kiosk_foodcourt_mode", 0)) == 1,
		"sms_ready": cint(_ko_setting("restaurant_kiosk_sms_ready", 1)) == 1,
		"default_branch": (_ko_setting("restaurant_kiosk_default_branch", "") or "").strip(),
		"vendors": vendors,
	}


@frappe.whitelist(allow_guest=True)
def kiosk_place_order(payload=None):
	"""Create (and submit) a kiosk order through the standard order pipeline."""
	if cint(_ko_setting("restaurant_kiosk_enabled", 1)) != 1:
		frappe.throw(_("کیوسک در حال حاضر غیرفعال است."))
	payload = _parse_json(payload, {})
	items = payload.get("items") or []
	cart_items = []
	for raw in items:
		if not isinstance(raw, dict):
			continue
		slug = (raw.get("item_slug") or raw.get("slug") or "").strip()
		qty = max(flt(raw.get("qty") or 1), 0.5)
		if slug:
			cart_items.append({"item_slug": slug, "qty": qty, "note": (raw.get("note") or "").strip()})
	if not cart_items:
		frappe.throw(_("حداقل یک آیتم در سبد سفارش الزامی است."))

	customer_name = (payload.get("customer_name") or "").strip() or _("مشتری کیوسک")
	mobile = (payload.get("mobile") or "").strip()
	branch = (payload.get("branch") or _ko_setting("restaurant_kiosk_default_branch", "") or "").strip()
	note = (payload.get("note") or "").strip()
	pickup_sms = cint(payload.get("pickup_sms"))

	# Per-vendor grouping info for the kitchen + receipt
	vendor_map = {}
	if _has_column("Item", "restaurant_vendor"):
		slugs = [line["item_slug"] for line in cart_items]
		try:
			rows = frappe.get_all(
				"Item",
				filters={"restaurant_slug": ["in", slugs]},
				fields=["restaurant_slug", "restaurant_vendor"],
				limit_page_length=len(slugs) + 5,
			)
			vendor_map = {row["restaurant_slug"]: row["restaurant_vendor"] for row in rows if row.get("restaurant_vendor")}
		except Exception:
			vendor_map = {}
	vendors_in_order = sorted({vendor_map.get(line["item_slug"]) for line in cart_items if vendor_map.get(line["item_slug"])})
	note_parts = [note] if note else []
	note_parts.append(_("[کیوسک]"))
	if vendors_in_order:
		note_parts.append(_("غرفه‌ها: {0}").format("، ".join(str(v) for v in vendors_in_order)))
	if pickup_sms:
		note_parts.append(_("اطلاع آماده‌سازی با پیامک"))

	so = _create_sales_order(
		customer_name=customer_name,
		mobile=mobile,
		order_type="takeaway",
		address="",
		note=" | ".join(note_parts),
		cart_items=cart_items,
		order_context={"branch": branch, "source": "kiosk"},
	)
	if so.docstatus == 0:
		so.flags.ignore_permissions = True
		so.save(ignore_permissions=True)
		so.submit()
	else:
		so.save(ignore_permissions=True)
	frappe.db.commit()

	totals_by_vendor = {}
	if vendors_in_order:
		for line in cart_items:
			vendor = vendor_map.get(line["item_slug"])
			if not vendor:
				continue
			totals_by_vendor[vendor] = totals_by_vendor.get(vendor, 0) + 1
	return {
		"status": "success",
		"order_code": so.name,
		"grand_total": flt(so.grand_total or so.total),
		"vendors": vendors_in_order,
		"vendor_item_counts": totals_by_vendor,
		"tracking_note": _("کد پیگیری سفارش شما: {0}").format(so.name),
	}


# ---------------------------------------------------------------------------
# Vendor sales report
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_vendor_sales(date_from=None, date_to=None):
	_ensure_management_access()
	rows = []
	summary = {"vendors": 0, "qty_total": 0.0, "revenue_total": 0.0, "cogs_total": 0.0, "profit_total": 0.0, "unassigned_revenue": 0.0}
	if _has_column("Item", "restaurant_vendor") and frappe.db.exists("DocType", "Sales Order"):
		start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
		sold = frappe.db.sql(
			"""
			SELECT soi.item_code, MAX(soi.item_name) AS item_name, SUM(soi.qty) AS qty, SUM(soi.amount) AS revenue
			FROM `tabSales Order Item` soi
			INNER JOIN `tabSales Order` so ON so.name = soi.parent
			WHERE so.docstatus = 1 AND so.creation BETWEEN %(start)s AND %(end)s
			GROUP BY soi.item_code
			""",
			{"start": start_dt, "end": end_dt},
			as_dict=True,
		)
		vendor_of = {}
		item_names = [row["item_code"] for row in sold]
		if item_names:
			meta = frappe.get_all("Item", filters={"name": ["in", item_names]}, fields=["name", "restaurant_vendor"], limit_page_length=len(item_names) + 5)
			vendor_of = {m["name"]: (m.get("restaurant_vendor") or "") for m in meta}
		cost_map = _ko_ops_call("_ops_unit_cost_map")
		per_vendor = {}
		for row in sold:
			vendor = vendor_of.get(row["item_code"]) or ""
			bucket = per_vendor.setdefault(vendor, {"qty": 0.0, "revenue": 0.0, "cogs": 0.0, "items": 0})
			qty = flt(row["qty"])
			bucket["qty"] += qty
			bucket["revenue"] += flt(row["revenue"])
			bucket["cogs"] += qty * flt(cost_map.get(row["item_code"], 0.0))
			bucket["items"] += 1
		for vendor, bucket in sorted(per_vendor.items(), key=lambda kv: flt(kv[1]["revenue"]), reverse=True):
			if not vendor:
				summary["unassigned_revenue"] = flt(bucket["revenue"])
			rows.append(
				{
					"vendor": vendor or _("(بدون غرفه)"),
					"items": cint(bucket["items"]),
					"qty": flt(bucket["qty"]),
					"revenue": flt(bucket["revenue"]),
					"cogs": flt(bucket["cogs"]),
					"gross_profit": flt(bucket["revenue"] - bucket["cogs"]),
					"margin_pct": flt(((bucket["revenue"] - bucket["cogs"]) / bucket["revenue"]) * 100, 1) if bucket["revenue"] else 0.0,
				}
			)
		summary.update(
			{
				"vendors": len([v for v in per_vendor if v]),
				"qty_total": flt(sum(r["qty"] for r in rows)),
				"revenue_total": flt(sum(r["revenue"] for r in rows)),
				"cogs_total": flt(sum(r["cogs"] for r in rows)),
				"profit_total": flt(sum(r["gross_profit"] for r in rows)),
			}
		)
	return _compose_management_report(
		"vendor-sales",
		_("فروش به تفکیک غرفه (فودکورت)"),
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		orders=[],
	)


# ---------------------------------------------------------------------------
# BI
# ---------------------------------------------------------------------------


def kiosk_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	kpis = [
		_bi_kpi("vs-vendors", _("غرفه‌ها"), cint(summary.get("vendors")), "count", None),
		_bi_kpi("vs-revenue", _("فروش کل"), flt(summary.get("revenue_total")), "money", None),
		_bi_kpi("vs-profit", _("سود ناخالص"), flt(summary.get("profit_total")), "money", None),
		_bi_kpi("vs-unassigned", _("فروش بدون غرفه"), flt(summary.get("unassigned_revenue")), "money", None),
	]
	charts = [
		{
			"key": "vs-bar",
			"type": "bar",
			"title": _("فروش هر غرفه"),
			"categories": [r.get("vendor") for r in rows],
			"series": [{"key": "revenue", "label": _("فروش"), "color": "#e3a72f", "values": [flt(r.get("revenue")) for r in rows]}],
		}
	]
	tables = [
		{"key": "vs-table", "title": _("جدول غرفه‌ها"), "columns": _table_columns_from_rows(rows), "rows": rows},
	]
	insights = []
	if flt(summary.get("unassigned_revenue")) > 0:
		insights.append(
			{
				"key": "vs-unassigned",
				"severity": "warn",
				"text": _("به مبلغ {0} فروش روی اقلام بدون غرفه ثبت شده؛ برای گزارش دقیق فودکورت، غرفه هر قلم را مشخص کنید.").format(f"{flt(summary.get('unassigned_revenue')):,}"),
			}
		)
	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _ko_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_ko_register_into_api_module()
