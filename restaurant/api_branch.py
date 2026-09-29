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
from frappe.utils import cint, flt, get_time, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_company_branch_fields,
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
BRANCH_SCHEDULE_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


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
		_ensure_company_branch_fields()
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
	for extra in (
		"restaurant_is_branch",
		"restaurant_branch_active",
		"restaurant_public_title",
		"restaurant_branch_address",
		"restaurant_branch_phone",
		"restaurant_branch_lat",
		"restaurant_branch_lng",
		"restaurant_pickup_available",
		"restaurant_delivery_available",
		"restaurant_delivery_eta_min",
		"restaurant_delivery_eta_max",
		"restaurant_delivery_fee",
		"restaurant_delivery_radius_km",
	):
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
	branch_rows = _br_branch_rows()
	schedule_map = _br_week_schedule_map()
	branches = [_serialize_branch(row, schedule_map) for row in branch_rows]
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


def _br_week_schedule_map():
	if not frappe.db.exists("DocType", "Restaurant Branch Schedule"):
		return {}
	rows = frappe.get_all(
		"Restaurant Branch Schedule",
		fields=["branch", "day_of_week", "is_open", "opening_time", "closing_time"],
		ignore_permissions=True,
		limit_page_length=2000,
	)
	result = {}
	for row in rows:
		branch = (row.get("branch") or "").strip()
		day = (row.get("day_of_week") or "").strip()
		if branch and day in BRANCH_SCHEDULE_DAYS:
			result.setdefault(branch, {})[day] = row
	return result


def _br_time_label(value):
	return str(value or "").strip()[:5]


def _serialize_branch(row, schedule_map=None):
	branch_name = row.get("name")
	stored_schedule = (schedule_map or {}).get(branch_name, {})
	weekly_schedule = []
	for day in BRANCH_SCHEDULE_DAYS:
		schedule = stored_schedule.get(day) or {}
		weekly_schedule.append(
			{
				"day_of_week": day,
				"is_open": cint(schedule.get("is_open") if schedule.get("is_open") not in (None, "") else 1),
				"opening_time": _br_time_label(schedule.get("opening_time")),
				"closing_time": _br_time_label(schedule.get("closing_time")),
			}
		)
	return {
		"name": branch_name,
		"company_name": row.get("company_name") or row.get("name"),
		"abbr": row.get("abbr") or "",
		"label": _br_branch_label(row),
		"is_branch": cint(row.get("restaurant_is_branch")),
		"is_active": cint(row.get("restaurant_branch_active")) if row.get("restaurant_branch_active") is not None else 1,
		"address": row.get("restaurant_branch_address") or "",
		"phone": row.get("restaurant_branch_phone") or "",
		"lat": flt(row.get("restaurant_branch_lat"), 6),
		"lng": flt(row.get("restaurant_branch_lng"), 6),
		"pickup_available": cint(row.get("restaurant_pickup_available") if row.get("restaurant_pickup_available") is not None else 1),
		"delivery_available": cint(row.get("restaurant_delivery_available") if row.get("restaurant_delivery_available") is not None else 1),
		"delivery_eta_min": cint(row.get("restaurant_delivery_eta_min") or 35),
		"delivery_eta_max": cint(row.get("restaurant_delivery_eta_max") or 45),
		"delivery_fee": flt(row.get("restaurant_delivery_fee") or 0),
		"delivery_radius_km": flt(row.get("restaurant_delivery_radius_km") or 0),
		"weekly_schedule": weekly_schedule,
	}


@frappe.whitelist()
def list_management_branches(active_only=0):
	_ensure_management_access()
	rows = _br_branch_rows(active_only=cint(active_only))
	schedule_map = _br_week_schedule_map()
	return {"branches": [_serialize_branch(row, schedule_map) for row in rows], "count": len(rows)}


def _br_normalize_weekly_schedule(value):
	if value is None:
		return None
	if not isinstance(value, list):
		frappe.throw(_("برنامه هفتگی سفارش‌گیری معتبر نیست."))
	by_day = {}
	for row in value:
		if not isinstance(row, dict):
			frappe.throw(_("یکی از روزهای برنامه سفارش‌گیری معتبر نیست."))
		day = str(row.get("day_of_week") or "").strip()
		if day not in BRANCH_SCHEDULE_DAYS or day in by_day:
			frappe.throw(_("روزهای برنامه سفارش‌گیری تکراری یا نامعتبر است."))
		is_open = cint(row.get("is_open") if row.get("is_open") not in (None, "") else 0)
		opening = _br_time_label(row.get("opening_time"))
		closing = _br_time_label(row.get("closing_time"))
		if is_open:
			if not opening or not closing:
				frappe.throw(_("برای روزهای فعال، ساعت شروع و پایان سفارش‌گیری را وارد کنید."))
			try:
				opening_time = get_time(opening)
				closing_time = get_time(closing)
			except Exception:
				frappe.throw(_("ساعت واردشده معتبر نیست."))
			if opening_time == closing_time:
				frappe.throw(_("ساعت شروع و پایان سفارش‌گیری نمی‌تواند یکسان باشد."))
		else:
			opening = ""
			closing = ""
		by_day[day] = {"day_of_week": day, "is_open": is_open, "opening_time": opening, "closing_time": closing}
	if len(by_day) != len(BRANCH_SCHEDULE_DAYS):
		frappe.throw(_("برای هر هفت روز هفته وضعیت سفارش‌گیری را مشخص کنید."))
	return [by_day[day] for day in BRANCH_SCHEDULE_DAYS]


def _br_save_weekly_schedule(branch_name, schedule_rows):
	if not frappe.db.exists("DocType", "Restaurant Branch Schedule"):
		frappe.throw(_("جدول ساعت کاری شعبه در این سایت در دسترس نیست."))
	for row in schedule_rows:
		existing_name = frappe.db.get_value(
			"Restaurant Branch Schedule",
			{"branch": branch_name, "day_of_week": row["day_of_week"]},
			"name",
		)
		doc = frappe.get_doc("Restaurant Branch Schedule", existing_name) if existing_name else frappe.new_doc("Restaurant Branch Schedule")
		doc.branch = branch_name
		doc.day_of_week = row["day_of_week"]
		doc.is_open = row["is_open"]
		doc.opening_time = row["opening_time"]
		doc.closing_time = row["closing_time"]
		doc.save(ignore_permissions=True)


@frappe.whitelist()
def save_management_branch(payload=None):
	"""Create/update a branch (ERPNext Company with branch fields)."""
	_ensure_management_access()
	_br_ensure_ops_ready()
	payload = _parse_json(payload, {})
	weekly_schedule = _br_normalize_weekly_schedule(payload.get("weekly_schedule")) if "weekly_schedule" in payload else None
	name = (payload.get("name") or "").strip()
	company_name = (payload.get("company_name") or "").strip()
	if not company_name and not name:
		frappe.throw(_("نام شعبه الزامی است."))
	delivery_radius = flt(payload.get("restaurant_delivery_radius_km") or 0)
	if delivery_radius < 0:
		frappe.throw(_("شعاع ارسال نمی‌تواند منفی باشد."))
	if delivery_radius > 0:
		latitude = payload.get("restaurant_branch_lat")
		longitude = payload.get("restaurant_branch_lng")
		if latitude in (None, "") or longitude in (None, "") or (flt(latitude) == 0 and flt(longitude) == 0):
			frappe.throw(_("برای تعیین شعاع ارسال، موقعیت شعبه را روی نقشه مشخص کنید."))
	if cint(payload.get("restaurant_delivery_eta_max") or 45) < cint(payload.get("restaurant_delivery_eta_min") or 35):
		frappe.throw(_("حداکثر زمان ارسال باید برابر یا بیشتر از حداقل زمان باشد."))
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
		"restaurant_pickup_available": lambda v: cint(v),
		"restaurant_delivery_available": lambda v: cint(v),
		"restaurant_delivery_eta_min": lambda v: cint(v),
		"restaurant_delivery_eta_max": lambda v: cint(v),
		"restaurant_delivery_fee": lambda v: flt(v),
		"restaurant_delivery_radius_km": lambda v: flt(v, 2),
	}
	for fieldname, normalize in field_map.items():
		if payload.get(fieldname) is not None and hasattr(doc, fieldname):
			setattr(doc, fieldname, normalize(payload.get(fieldname)))
	if payload.get("company_name"):
		doc.company_name = company_name
	doc.save(ignore_permissions=True)
	if weekly_schedule is not None:
		_br_save_weekly_schedule(doc.name, weekly_schedule)
	frappe.db.commit()
	return {"status": "success", "branch": _serialize_branch(doc.as_dict(), _br_week_schedule_map())}


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
