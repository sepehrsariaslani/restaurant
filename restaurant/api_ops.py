# Copyright (c) 2026, Restaurant and contributors
"""Courier operations, KDS extras and cost-control (finance) for the SPA.

- Delivery zones (geofence circles), order↔courier assignment, courier app
  (guest, code-based) and third-party courier platform connectors.
- Kitchen-display extras: prep-time timestamps, POS ready notifications and
  kitchen performance analytics.
- Cost control: budgets, live expenses, monthly P&L, break-even and ROI.

Endpoints are re-exported into ``restaurant.api`` (star-import at the bottom
of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import json
import math

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_has_column,
	_item_uom_conversion_to_stock,
	_table_columns_from_rows,
)

__all__ = [
	"OPS_REPORT_KEYS",
	"ops_build_report_bi",
	"_ops_ensure_ops_ready",
	# zones
	"list_management_delivery_zones",
	"save_management_delivery_zone",
	"delete_management_delivery_zone",
	"check_management_delivery_point",
	# courier assignment & app
	"assign_management_order_courier",
	"courier_app_login",
	"courier_app_deliveries",
	"courier_app_action",
	# third party delivery platforms
	"get_management_delivery_provider_settings",
	"set_management_delivery_provider_settings",
	"dispatch_management_delivery_provider",
	"optimize_management_courier_route",
	# kitchen display extras
	"get_management_pos_kitchen_notifications",
	"ops_kitchen_mark",
	# budgets & finance
	"list_management_budgets",
	"save_management_budget",
	"delete_management_budget",
	"get_management_cost_control_boot",
	"compute_management_roi",
	# reports
	"get_management_report_courier_performance",
	"get_management_report_kitchen_performance",
	"get_management_report_profit_loss",
	"get_management_report_breakeven",
	"get_management_report_waiter_performance",
]

OPS_REPORT_KEYS = {"courier-performance", "kitchen-performance", "profit-loss", "breakeven", "waiter-performance"}
ZONE_DOCTYPE = "Restaurant Delivery Zone"
BUDGET_DOCTYPE = "Restaurant Budget"
COURIER_DOCTYPE = "Restaurant Courier"
DELIVERY_PROVIDERS = ["", "اسنپ‌باکس", "تپسی‌باکس", "الوپیک", "سایر"]
BUDGET_PERIODS = ["ماهانه", "سالانه"]


# ---------------------------------------------------------------------------
# Lazy bridges (import-cycle safety)
# ---------------------------------------------------------------------------


def _ops_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	return getattr(api_feature_pack, helper_name)(*args, **kwargs)


def _ops_parse_json(value, fallback=None):
	if fallback is None:
		fallback = {}
	if isinstance(value, type(fallback)):
		return value
	try:
		parsed = json.loads(str(value or "").strip() or "null")
	except Exception:
		return fallback
	return parsed if parsed is not None else fallback


def _ops_parse_payload(payload):
	if payload is None:
		payload = {}
	if isinstance(payload, str):
		payload = _ops_parse_json(payload, {})
	if not isinstance(payload, dict):
		try:
			payload = dict(frappe.form_dict or {})
		except Exception:
			payload = {}
	return payload or {}


# ---------------------------------------------------------------------------
# Custom field provisioning (runtime, idempotent)
# ---------------------------------------------------------------------------


def _ops_ensure_sales_order_fields():
	_ops_fp_call(
		"_fp_ensure_custom_fields",
		"Sales Order",
		[
			{"fieldname": "restaurant_courier", "label": _("پیک سفارش"), "fieldtype": "Link", "options": "Restaurant Courier"},
			{"fieldname": "restaurant_courier_assigned_at", "label": _("زمان تخصیص پیک"), "fieldtype": "Datetime"},
			{"fieldname": "restaurant_delivery_provider", "label": _("پلتفرم ارسال"), "fieldtype": "Data"},
			{"fieldname": "restaurant_delivery_provider_ref", "label": _("کد رهگیری پلتفرم"), "fieldtype": "Data"},
			{"fieldname": "restaurant_delivery_provider_status", "label": _("وضعیت پلتفرم"), "fieldtype": "Data"},
			{"fieldname": "restaurant_route_index", "label": _("ترتیب مسیر ارسال"), "fieldtype": "Int"},
		],
		anchor_candidates=["restaurant_kitchen_ready_at", "restaurant_referral_code", "restaurant_status"],
	)


def _ops_ensure_settings_fields():
	_ops_fp_call(
		"_fp_ensure_custom_fields",
		"Restaurant Web Settings",
		[
			{"fieldname": "restaurant_delivery_section", "label": _("پیک و ارسال"), "fieldtype": "Section Break"},
			{"fieldname": "restaurant_delivery_zone_enabled", "label": _("کنترل محدوده ارسال فعال است"), "fieldtype": "Check"},
			{"fieldname": "restaurant_delivery_provider", "label": _("پلتفرم ارسال ثالث"), "fieldtype": "Select", "options": "\n" + "\n".join(DELIVERY_PROVIDERS[1:])},
			{"fieldname": "restaurant_delivery_provider_token", "label": _("توکن پلتفرم ارسال"), "fieldtype": "Data"},
			{"fieldname": "restaurant_delivery_provider_base_url", "label": _("آدرس API پلتفرم"), "fieldtype": "Data"},
		],
		anchor_candidates=["restaurant_club_section", "restaurant_inventory_section"],
	)


def _ops_ensure_ops_ready():
	_ops_ensure_sales_order_fields()
	_ops_ensure_settings_fields()


def _ops_setting(fieldname, default=""):
	try:
		return frappe.db.get_single_value("Restaurant Web Settings", fieldname) or default
	except Exception:
		return default


def _ops_set_setting(fieldname, value):
	frappe.db.set_single_value("Restaurant Web Settings", fieldname, value, update_modified=True)


# ---------------------------------------------------------------------------
# Delivery zones (geofence)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_delivery_zones(include_inactive=0):
	_ensure_management_access()
	filters = {} if cint(include_inactive) else {"is_active": 1}
	rows = frappe.get_all(
		ZONE_DOCTYPE,
		filters=filters,
		fields=["name", "zone_name", "center_lat", "center_lng", "radius_km", "delivery_fee", "min_order_amount", "is_active", "notes"],
		order_by="zone_name",
		limit_page_length=300,
	)
	return {
		"zones": [
			{
				**row,
				"center_lat": flt(row.get("center_lat"), 6),
				"center_lng": flt(row.get("center_lng"), 6),
				"radius_km": flt(row.get("radius_km"), 2),
				"delivery_fee": flt(row.get("delivery_fee")),
				"min_order_amount": flt(row.get("min_order_amount")),
			}
			for row in rows
		],
		"zone_control_enabled": cint(_ops_setting("restaurant_delivery_zone_enabled", 0)),
		"count": len(rows),
	}


@frappe.whitelist()
def save_management_delivery_zone(payload=None):
	_ensure_management_access()
	payload = _ops_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	zone_name = (payload.get("zone_name") or "").strip()
	if not zone_name:
		frappe.throw(_("نام محدوده الزامی است."))
	if name and frappe.db.exists(ZONE_DOCTYPE, name):
		doc = frappe.get_doc(ZONE_DOCTYPE, name)
	else:
		doc = frappe.new_doc(ZONE_DOCTYPE)
	doc.zone_name = zone_name
	doc.center_lat = flt(payload.get("center_lat"), 6)
	doc.center_lng = flt(payload.get("center_lng"), 6)
	doc.radius_km = flt(payload.get("radius_km"), 2) or 3
	doc.delivery_fee = flt(payload.get("delivery_fee"))
	doc.min_order_amount = flt(payload.get("min_order_amount"))
	doc.is_active = cint(payload.get("is_active", 1))
	doc.notes = (payload.get("notes") or "").strip()
	doc.save(ignore_permissions=True)
	if "zone_control_enabled" in payload:
		_ops_set_setting("restaurant_delivery_zone_enabled", cint(payload.get("zone_control_enabled")))
	frappe.db.commit()
	return {"status": "success", "name": doc.name}


@frappe.whitelist()
def delete_management_delivery_zone(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(ZONE_DOCTYPE, name):
		frappe.throw(_("محدوده یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(ZONE_DOCTYPE, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def check_management_delivery_point(lat=0, lng=0):
	"""Return matching zones for a geo point (haversine on zone circles)."""
	_ensure_management_access()
	lat = flt(lat, 6)
	lng = flt(lng, 6)
	if not lat or not lng:
		frappe.throw(_("مختصات جغرافیایی معتبر نیست."))
	matches = []
	for zone in list_management_delivery_zones(include_inactive=0)["zones"]:
		distance = _ops_haversine_km(lat, lng, zone["center_lat"], zone["center_lng"])
		if zone["radius_km"] <= 0 or distance <= zone["radius_km"]:
			matches.append({"zone": zone["zone_name"], "name": zone["name"], "distance_km": flt(distance, 2), "delivery_fee": zone["delivery_fee"], "min_order_amount": zone["min_order_amount"]})
	return {"matches": matches, "allowed": bool(matches), "count": len(matches)}


def _ops_haversine_km(lat1, lng1, lat2, lng2):
	radius = 6371.0
	d_lat = math.radians(lat2 - lat1)
	d_lng = math.radians(lng2 - lng1)
	a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
	return 2 * radius * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Order ↔ courier assignment + courier app (guest)
# ---------------------------------------------------------------------------


def _ops_courier_by_mobile(mobile, access_code):
	mobile = (mobile or "").strip()
	access_code = (access_code or "").strip()
	if not mobile or not access_code:
		return None
	row = frappe.db.get_value(
		COURIER_DOCTYPE,
		{"mobile": mobile, "is_active": 1},
		["name", "courier_name", "courier_code", "access_code"],
		as_dict=True,
	) if _has_column(COURIER_DOCTYPE, "access_code") else None
	if row and (row.get("access_code") or "").strip() == access_code:
		return row
	return None


def _ops_courier_orders(courier_name, include_delivered=0):
	statuses = ["courier_handoff", "on_the_way"]
	if cint(include_delivered):
		statuses.append("delivered")
	filters = {
		"docstatus": 1,
		"restaurant_courier": courier_name,
		"restaurant_status": ["in", statuses],
	}
	fields = ["name", "customer_name", "customer", "grand_total", "transaction_date", "restaurant_status", "restaurant_order_type", "restaurant_address", "restaurant_phone", "creation"]
	if _has_column("Sales Order", "restaurant_route_index"):
		fields.append("restaurant_route_index")
	rows = frappe.get_all(
		"Sales Order",
		filters=filters,
		fields=fields,
		order_by="creation desc",
		limit_page_length=100,
		ignore_permissions=True,
	)
	# بهینه‌سازی چیدمان بر اساس مسیر: سفارش‌های دارای ترتیب مسیر، اول و به ترتیب
	if _has_column("Sales Order", "restaurant_route_index"):
		rows = sorted(rows, key=lambda r: (cint(r.get("restaurant_route_index") or 0) == 0, cint(r.get("restaurant_route_index") or 0), str(r.get("creation") or "")), reverse=False)
	orders = []
	for row in rows:
		address = frappe.db.get_value("Sales Order", row["name"], "address_display") if _has_column("Sales Order", "address_display") else ""
		order_code = row.get("name")
		items = frappe.get_all(
			"Sales Order Item",
			filters={"parent": row["name"]},
			fields=["item_name", "qty"],
			order_by="idx",
			limit_page_length=50,
		)
		orders.append(
			{
				"name": order_code,
				"customer_name": row.get("customer_name") or "",
				"address": address or (row.get("restaurant_address") or ""),
				"phone": row.get("restaurant_phone") or _ops_customer_mobile(row.get("customer")),
				"grand_total": flt(row.get("grand_total")),
				"status": row.get("restaurant_status") or "",
				"route_index": cint(row.get("restaurant_route_index") or 0),
				"items": [{"title": i.get("item_name"), "qty": flt(i.get("qty"))} for i in items],
				"creation": str(row.get("creation") or ""),
			}
		)
	return orders


def _ops_customer_mobile(customer_name):
	if not customer_name:
		return ""
	for fieldname in ("mobile_no", "customer_primary_mobile"):
		if _has_column("Customer", fieldname):
			value = frappe.db.get_value("Customer", customer_name, fieldname)
			if value:
				return (value or "").strip()
	return ""


@frappe.whitelist()
def assign_management_order_courier(payload=None):
	"""Assign a courier to a delivery order (orders page / POS)."""
	_ensure_management_access()
	_ops_ensure_sales_order_fields()
	payload = _ops_parse_payload(payload)
	order_name = (payload.get("order_name") or payload.get("order_code") or "").strip()
	courier = (payload.get("courier") or "").strip()
	if not order_name:
		frappe.throw(_("سفارش انتخاب نشده است."))
	if not frappe.db.exists("Sales Order", order_name):
		frappe.throw(_("سفارش یافت نشد: {0}").format(order_name))
	if courier and not frappe.db.exists(COURIER_DOCTYPE, courier):
		by_code = frappe.db.get_value(COURIER_DOCTYPE, {"courier_code": courier}, "name")
		by_name = frappe.db.get_value(COURIER_DOCTYPE, {"courier_name": courier}, "name")
		courier = by_code or by_name or ""
		if not courier:
			frappe.throw(_("پیک یافت نشد: {0}").format(payload.get("courier")))
	updates = {"restaurant_courier": courier or None, "restaurant_courier_assigned_at": now_datetime() if courier else None}
	frappe.db.set_value("Sales Order", order_name, updates, update_modified=False)
	if courier and _has_column("Sales Order", "restaurant_status"):
		current = frappe.db.get_value("Sales Order", order_name, "restaurant_status") or ""
		if current in ("ready", "preparing", "confirmed", "new"):
			try:
				from restaurant.api import _set_restaurant_order_status

				_set_restaurant_order_status(order_name, "courier_handoff")
			except Exception:
				frappe.db.set_value("Sales Order", order_name, "restaurant_status", "courier_handoff", update_modified=False)
	frappe.db.commit()
	return {"status": "success", "order": order_name, "courier": courier}


@frappe.whitelist(allow_guest=True)
def courier_app_login(mobile="", access_code=""):
	"""Courier app login with mobile + access code (guest, PWA)."""
	courier = _ops_courier_by_mobile(mobile, access_code)
	if not courier:
		frappe.throw(_("مشخصات پیک نامعتبر است."), frappe.PermissionError)
	today_deliveries = frappe.db.count(
		"Sales Order",
		{
			"docstatus": 1,
			"restaurant_courier": courier["name"],
			"restaurant_status": "delivered",
			"transaction_date": today(),
		},
	)
	pending = frappe.db.count(
		"Sales Order",
		{"docstatus": 1, "restaurant_courier": courier["name"], "restaurant_status": ["in", ["courier_handoff", "on_the_way"]]},
	)
	return {
		"status": "success",
		"courier": {"name": courier["name"], "courier_name": courier.get("courier_name"), "courier_code": courier.get("courier_code")},
		"today_delivered": cint(today_deliveries),
		"pending": cint(pending),
	}


@frappe.whitelist(allow_guest=True)
def courier_app_deliveries(mobile="", access_code=""):
	courier = _ops_courier_by_mobile(mobile, access_code)
	if not courier:
		frappe.throw(_("مشخصات پیک نامعتبر است."), frappe.PermissionError)
	return {"orders": _ops_courier_orders(courier["name"])}


@frappe.whitelist(allow_guest=True)
def courier_app_action(mobile="", access_code="", order_name="", action=""):
	"""Courier advances delivery: pickup (on_the_way) / delivered."""
	courier = _ops_courier_by_mobile(mobile, access_code)
	if not courier:
		frappe.throw(_("مشخصات پیک نامعتبر است."), frappe.PermissionError)
	order_name = (order_name or "").strip()
	action = (action or "").strip()
	assigned = frappe.db.get_value("Sales Order", order_name, "restaurant_courier") if frappe.db.exists("Sales Order", order_name) else ""
	if assigned != courier["name"]:
		frappe.throw(_("این سفارش به شما تخصیص نیافته است."), frappe.PermissionError)
	current = frappe.db.get_value("Sales Order", order_name, "restaurant_status") or ""
	target = {"pickup": "on_the_way", "deliver": "delivered"}.get(action)
	if not target:
		frappe.throw(_("عملیات نامعتبر است: {0}").format(action or "-"))
	valid = (current == "courier_handoff" and target == "on_the_way") or (current == "on_the_way" and target == "delivered")
	if not valid:
		frappe.throw(_("تغییر وضعیت از «{0}» به «{1}» مجاز نیست.").format(current, target))
	from restaurant.api import _set_restaurant_order_status

	_set_restaurant_order_status(order_name, target)
	frappe.db.commit()
	return {"status": "success", "order": order_name, "new_status": target}


# ---------------------------------------------------------------------------
# Third-party courier platforms (SnappBox / Alopeyk / other)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_delivery_provider_settings():
	_ensure_management_access()
	return {
		"provider": (_ops_setting("restaurant_delivery_provider", "") or "").strip(),
		"token_set": bool((_ops_setting("restaurant_delivery_provider_token", "") or "").strip()),
		"base_url": (_ops_setting("restaurant_delivery_provider_base_url", "") or "").strip(),
		"zone_control_enabled": cint(_ops_setting("restaurant_delivery_zone_enabled", 0)),
		"providers": [p for p in DELIVERY_PROVIDERS if p],
	}


@frappe.whitelist()
def set_management_delivery_provider_settings(payload=None):
	_ensure_management_access()
	_ops_ensure_settings_fields()
	payload = _ops_parse_payload(payload)
	provider = (payload.get("provider") or "").strip()
	if provider and provider not in DELIVERY_PROVIDERS:
		frappe.throw(_("پلتفرم نامعتبر است: {0}").format(provider))
	_ops_set_setting("restaurant_delivery_provider", provider)
	if "token" in payload:
		_ops_set_setting("restaurant_delivery_provider_token", (payload.get("token") or "").strip())
	if "base_url" in payload:
		_ops_set_setting("restaurant_delivery_provider_base_url", (payload.get("base_url") or "").strip())
	if "zone_control_enabled" in payload:
		_ops_set_setting("restaurant_delivery_zone_enabled", cint(payload.get("zone_control_enabled")))
	frappe.db.commit()
	return {"status": "success", **get_management_delivery_provider_settings()}


@frappe.whitelist()
def dispatch_management_delivery_provider(payload=None):
	"""Send a delivery request to the configured third-party courier platform."""
	_ensure_management_access()
	_ops_ensure_sales_order_fields()
	_ops_ensure_settings_fields()
	payload = _ops_parse_payload(payload)
	order_name = (payload.get("order_name") or "").strip()
	if not frappe.db.exists("Sales Order", order_name):
		frappe.throw(_("سفارش یافت نشد: {0}").format(order_name or "-"))

	settings = get_management_delivery_provider_settings()
	provider = (payload.get("provider") or settings["provider"] or "").strip()
	if not provider:
		frappe.throw(_("پلتفرم ارسال در تنظیمات انتخاب نشده است."))
	token = (_ops_setting("restaurant_delivery_provider_token", "") or "").strip()
	base_url = settings["base_url"]
	if not token or not base_url:
		frappe.throw(_("توکن یا آدرس API پلتفرم ارسال تنظیم نشده است."))

	so = frappe.get_doc("Sales Order", order_name)
	body = {
		"order_id": so.name,
		"customer_name": so.get("customer_name") or "",
		"customer_phone": _ops_customer_mobile(so.get("customer")),
		"destination_address": so.get("address_display") or (so.get("restaurant_address") or ""),
		"amount": flt(so.get("grand_total")),
		"created_at": str(so.get("creation") or ""),
		"comment": (so.get("restaurant_order_note") or "")[:300],
	}
	headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}", "X-Api-Key": token}

	ref = ""
	status = "خطا"
	note = ""
	try:
		import urllib.request

		request = urllib.request.Request(
			base_url.rstrip("/"),
			data=json.dumps(body).encode("utf-8"),
			headers=headers,
			method="POST",
		)
		with urllib.request.urlopen(request, timeout=20) as response:  # nosec B310 - configured URL
			raw = response.read().decode("utf-8", "ignore")
		parsed = _ops_parse_json(raw, {})
		ref = str(parsed.get("id") or parsed.get("tracking_code") or parsed.get("order_id") or "") if isinstance(parsed, dict) else ""
		status = "ثبت‌شده"
		note = str(raw)[:200]
	except Exception as exc:
		note = str(exc)[:200]
		frappe.log_error(frappe.get_traceback(), f"Restaurant delivery dispatch failed ({provider})")

	frappe.db.set_value(
		"Sales Order",
		order_name,
		{
			"restaurant_delivery_provider": provider,
			"restaurant_delivery_provider_ref": ref,
			"restaurant_delivery_provider_status": status,
		},
		update_modified=False,
	)
	frappe.db.commit()
	if status != "ثبت‌شده":
		frappe.throw(_("ثبت سفارش در پلتفرم ناموفق بود: {0}").format(note))
	return {"status": "success", "provider": provider, "reference": ref, "note": note}


# ---------------------------------------------------------------------------
# Route optimization (بهینه‌سازی چیدمان سفارش‌ها بر اساس مسیر)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def optimize_management_courier_route(payload=None):
	"""چیدمان بهینه سفارش‌های در حال ارسال یک پیک (نزدیک‌ترین همسایه).

	Optional start point from the courier's current location, otherwise the
	centroid of the orders. Orders without coordinates keep their place at
	the end of the run. Persists ``restaurant_route_index`` on each order so
	the courier app lists them in driving order.
	"""
	_ensure_management_access()
	_ops_ensure_sales_order_fields()
	payload = _ops_parse_payload(payload)
	courier = (payload.get("courier") or "").strip()
	if not courier or not frappe.db.exists(COURIER_DOCTYPE, courier):
		frappe.throw(_("پیک یافت نشد: {0}").format(courier or "-"))

	filters = {
		"docstatus": 1,
		"restaurant_courier": courier,
		"restaurant_status": ["in", ["courier_handoff", "on_the_way"]],
	}
	fields = ["name", "customer_name", "creation"]
	if _has_column("Sales Order", "restaurant_delivery_lat"):
		fields += ["restaurant_delivery_lat", "restaurant_delivery_lng"]
	rows = frappe.get_all("Sales Order", filters=filters, fields=fields, order_by="creation asc", limit_page_length=200, ignore_permissions=True)
	if not rows:
		return {"status": "success", "optimized": 0, "orders": []}

	located = [r for r in rows if flt(r.get("restaurant_delivery_lat")) and flt(r.get("restaurant_delivery_lng"))]
	unlocated = [r for r in rows if r not in located]

	start_lat = flt(payload.get("lat"))
	start_lng = flt(payload.get("lng"))
	if not (start_lat and start_lng) and located:
		start_lat = flt(sum(flt(r.get("restaurant_delivery_lat")) for r in located) / len(located), 6)
		start_lng = flt(sum(flt(r.get("restaurant_delivery_lng")) for r in located) / len(located), 6)

	ordered = []
	remaining = list(located)
	cur_lat, cur_lng = start_lat, start_lng
	while remaining:
		best_idx = 0
		best_dist = None
		for idx, row in enumerate(remaining):
			if not (cur_lat and cur_lng):
				dist = 0.0
			else:
				dist = _ops_haversine_km(cur_lat, cur_lng, flt(row.get("restaurant_delivery_lat")), flt(row.get("restaurant_delivery_lng")))
			if best_dist is None or dist < best_dist:
				best_dist = dist
				best_idx = idx
		chosen = remaining.pop(best_idx)
		ordered.append(chosen)
		cur_lat = flt(chosen.get("restaurant_delivery_lat"))
		cur_lng = flt(chosen.get("restaurant_delivery_lng"))

	final = ordered + unlocated
	for position, row in enumerate(final, start=1):
		frappe.db.set_value("Sales Order", row["name"], "restaurant_route_index", position, update_modified=False)
	frappe.db.commit()
	return {
		"status": "success",
		"optimized": len(final),
		"located": len(located),
		"orders": [
			{"name": row["name"], "customer_name": row.get("customer_name") or "", "route_index": idx}
			for idx, row in enumerate(final, start=1)
		],
	}


# ---------------------------------------------------------------------------
# Kitchen display extras: timestamps, POS notifications, analytics
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_pos_kitchen_notifications(since=""):
	"""Kitchen→cashier: orders that became ready since the client marker."""
	_ensure_management_access()
	if not _has_column("Sales Order", "restaurant_kitchen_ready_at"):
		return {"orders": [], "count": 0}
	filters = {"docstatus": 1, "restaurant_kitchen_ready_at": ["is", "set"]}
	if since:
		filters["restaurant_kitchen_ready_at"] = [">", since]
	rows = frappe.get_all(
		"Sales Order",
		filters=filters,
		fields=["name", "customer_name", "restaurant_order_type", "restaurant_kitchen_ready_at", "grand_total"],
		order_by="restaurant_kitchen_ready_at desc",
		limit_page_length=25,
	)
	return {
		"orders": [
			{
				"name": row["name"],
				"customer_name": row.get("customer_name") or "",
				"channel": row.get("restaurant_order_type") or "",
				"ready_at": str(row.get("restaurant_kitchen_ready_at") or ""),
				"grand_total": flt(row.get("grand_total")),
			}
			for row in rows
			if (frappe.db.get_value("Sales Order", row["name"], "restaurant_status") or "") == "ready"
		],
		"count": len(rows),
		"now": str(now_datetime()),
	}


def ops_kitchen_mark(so_name, status):
	"""Stamp prep-time fields on the Sales Order (called from kitchen flows)."""
	if not frappe.db.exists("Sales Order", so_name):
		return
	updates = {}
	if status == "preparing" and _has_column("Sales Order", "restaurant_kitchen_started_at"):
		if not frappe.db.get_value("Sales Order", so_name, "restaurant_kitchen_started_at"):
			updates["restaurant_kitchen_started_at"] = now_datetime()
	elif status == "ready":
		if _has_column("Sales Order", "restaurant_kitchen_ready_at"):
			updates["restaurant_kitchen_ready_at"] = now_datetime()
	if updates:
		frappe.db.set_value("Sales Order", so_name, updates, update_modified=False)


# ---------------------------------------------------------------------------
# Budgets & cost control (finance)
# ---------------------------------------------------------------------------


def _ops_fixed_monthly_cost():
	try:
		return flt(frappe.db.get_single_value("Fixed Costs Settings", "current_monthly_fixed_costs"))
	except Exception:
		return 0.0


def _ops_unit_cost_map():
	"""{item_code: live unit cost} from default active BOMs (like the cost report)."""
	costs = {}
	if not frappe.db.exists("DocType", "BOM"):
		return costs
	boms = frappe.db.sql(
		"""
		SELECT b.name, b.item, b.quantity
		FROM `tabBOM` b
		WHERE b.docstatus = 1 AND b.is_active = 1 AND b.is_default = 1
		""",
		as_dict=True,
	)
	if not boms:
		return costs
	components = frappe.get_all(
		"BOM Item",
		filters={"parent": ["in", [row["name"] for row in boms]], "parenttype": "BOM"},
		fields=["parent", "item_code", "qty", "uom", "stock_uom"],
	)
	by_bom = {}
	codes = set()
	for row in components:
		by_bom.setdefault(row["parent"], []).append(row)
		if row.get("item_code"):
			codes.add(row["item_code"])
	rates = {}
	for code in codes:
		rate = 0.0
		if _has_column("Item", "restaurant_purchase_rate"):
			rate = flt(frappe.db.get_value("Item", code, "restaurant_purchase_rate"))
		if not rate:
			rate = flt(
				frappe.db.sql(
					"SELECT COALESCE(SUM(valuation_rate * actual_qty) / NULLIF(SUM(actual_qty),0), 0) FROM `tabBin` WHERE item_code=%s",
					(code,),
				)[0][0]
			)
		rates[code] = rate
	for bom in boms:
		output_qty = flt(bom.get("quantity")) or 1.0
		total = 0.0
		for row in by_bom.get(bom["name"], []):
			code = row.get("item_code")
			if not code:
				continue
			qty = flt(row.get("qty"))
			uom = (row.get("uom") or "").strip()
			stock_uom = (row.get("stock_uom") or "").strip()
			if uom and stock_uom and uom != stock_uom:
				qty = qty * _item_uom_conversion_to_stock(code, uom)
			total += qty * rates.get(code, 0.0)
		costs[bom["item"]] = total / output_qty if output_qty else 0.0
	# non-BOM stock products (drinks etc.) → their own valuation rate
	return costs


def _ops_waste_value_by_month(year):
	rows = frappe.db.sql(
		"""
		SELECT MONTH(sle.posting_date) AS month, SUM(ABS(sle.stock_value_difference)) AS value
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		WHERE sle.voucher_type='Stock Entry' AND sle.is_cancelled=0
		  AND YEAR(sle.posting_date) = %(year)s
		  AND se.restaurant_movement_kind IN ('ضایعات', 'خسارت')
		GROUP BY MONTH(sle.posting_date)
		""",
		{"year": cint(year)},
		as_dict=True,
	) if _has_column("Stock Entry", "restaurant_movement_kind") else []
	return {cint(row.get("month")): flt(row.get("value")) for row in rows}


def _ops_monthly_pl(year):
	"""12-month P&L rows: revenue, COGS, fixed, waste, net."""
	year = cint(year) or cint(getdate(today()).year)
	revenue_rows = frappe.db.sql(
		"""
		SELECT MONTH(transaction_date) AS month,
			   COUNT(*) AS orders, COALESCE(SUM(grand_total),0) AS revenue
		FROM `tabSales Order`
		WHERE docstatus = 1 AND status != 'Cancelled' AND YEAR(transaction_date) = %(year)s
		GROUP BY MONTH(transaction_date)
		""",
		{"year": year},
		as_dict=True,
	)
	qty_rows = frappe.db.sql(
		"""
		SELECT MONTH(so.transaction_date) AS month, soi.item_code, SUM(soi.qty) AS qty
		FROM `tabSales Order Item` soi
		INNER JOIN `tabSales Order` so ON so.name = soi.parent
		WHERE so.docstatus = 1 AND so.status != 'Cancelled' AND YEAR(so.transaction_date) = %(year)s
		GROUP BY MONTH(so.transaction_date), soi.item_code
		""",
		{"year": year},
		as_dict=True,
	)
	cost_map = _ops_unit_cost_map()
	fallback_rates = {}
	waste_map = _ops_waste_value_by_month(year)
	fixed = _ops_fixed_monthly_cost()

	cogs_map = {}
	for row in qty_rows:
		month = cint(row.get("month"))
		code = row.get("item_code")
		if not code:
			continue
		rate = cost_map.get(code)
		if rate is None:
			if code not in fallback_rates:
				fallback_rates[code] = flt(
					frappe.db.sql(
						"SELECT COALESCE(SUM(valuation_rate * actual_qty) / NULLIF(SUM(actual_qty),0), 0) FROM `tabBin` WHERE item_code=%s",
						(code,),
					)[0][0]
				)
			rate = fallback_rates[code]
		cogs_map[month] = cogs_map.get(month, 0.0) + flt(row.get("qty")) * flt(rate)

	rows = []
	for month in range(1, 13):
		rev_row = next((r for r in revenue_rows if cint(r.get("month")) == month), {})
		revenue = flt(rev_row.get("revenue"))
		cogs = flt(cogs_map.get(month, 0.0))
		waste = flt(waste_map.get(month, 0.0))
		gross = revenue - cogs
		net = gross - fixed - waste
		rows.append(
			{
				"month": month,
				"revenue": revenue,
				"cogs": cogs,
				"orders": cint(rev_row.get("orders")),
				"gross_profit": flt(gross),
				"fixed_costs": fixed,
				"waste": waste,
				"net_profit": flt(net),
				"margin_pct": flt((net / revenue) * 100, 1) if revenue else 0.0,
			}
		)
	return rows


@frappe.whitelist()
def list_management_budgets(fiscal_year="", period=""):
	_ensure_management_access()
	filters = {}
	if cint(fiscal_year):
		filters["fiscal_year"] = cint(fiscal_year)
	if period in BUDGET_PERIODS:
		filters["period"] = period
	rows = frappe.get_all(
		BUDGET_DOCTYPE,
		filters=filters,
		fields=["name", "title", "period", "fiscal_year", "month", "category", "planned_amount", "is_active", "notes"],
		order_by="fiscal_year desc, month asc",
		limit_page_length=300,
	)
	return {"budgets": rows, "count": len(rows)}


@frappe.whitelist()
def save_management_budget(payload=None):
	_ensure_management_access()
	payload = _ops_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	title = (payload.get("title") or "").strip()
	if not title:
		frappe.throw(_("عنوان بودجه الزامی است."))
	if name and frappe.db.exists(BUDGET_DOCTYPE, name):
		doc = frappe.get_doc(BUDGET_DOCTYPE, name)
	else:
		doc = frappe.new_doc(BUDGET_DOCTYPE)
	doc.title = title
	period = (payload.get("period") or "ماهانه").strip()
	doc.period = period if period in BUDGET_PERIODS else "ماهانه"
	doc.fiscal_year = cint(payload.get("fiscal_year")) or cint(getdate(today()).year)
	doc.month = cint(payload.get("month")) if doc.period == "ماهانه" else 0
	doc.category = (payload.get("category") or "").strip()
	doc.planned_amount = flt(payload.get("planned_amount"))
	doc.is_active = cint(payload.get("is_active", 1))
	doc.notes = (payload.get("notes") or "").strip()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": doc.name}


@frappe.whitelist()
def delete_management_budget(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(BUDGET_DOCTYPE, name):
		frappe.throw(_("بودجه یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(BUDGET_DOCTYPE, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def get_management_cost_control_boot(fiscal_year=""):
	"""Live expense tracking + break-even inputs for the cost-control page."""
	_ensure_management_access()
	year = cint(fiscal_year) or cint(getdate(today()).year)
	rows = _ops_monthly_pl(year)
	current_month = cint(getdate(today()).month) if year == cint(getdate(today()).year) else 12
	current = rows[current_month - 1] if rows else {}
	total_revenue = sum(r["revenue"] for r in rows)
	total_cogs = sum(r["cogs"] for r in rows)
	cogs_ratio = (total_cogs / total_revenue) if total_revenue else 0.0
	fixed = _ops_fixed_monthly_cost()
	breakeven_monthly = fixed / (1 - cogs_ratio) if cogs_ratio < 1 else 0.0

	monthly_budget = frappe.get_all(
		BUDGET_DOCTYPE,
		filters={"fiscal_year": year, "period": "ماهانه", "month": current_month, "is_active": 1},
		fields=["planned_amount"],
	)
	monthly_budget_amount = sum(flt(r.get("planned_amount")) for r in monthly_budget)
	month_expense = flt(current.get("cogs")) + fixed + flt(current.get("waste"))

	return {
		"fiscal_year": year,
		"kpis": {
			"fixed_monthly_cost": fixed,
			"current_month_revenue": flt(current.get("revenue")),
			"current_month_cogs": flt(current.get("cogs")),
			"current_month_waste": flt(current.get("waste")),
			"current_month_net": flt(current.get("net_profit")),
			"year_revenue": flt(total_revenue),
			"year_net": flt(sum(r["net_profit"] for r in rows)),
			"cogs_ratio_pct": flt(cogs_ratio * 100, 1),
			"breakeven_monthly_sales": flt(breakeven_monthly),
			"breakeven_daily_sales": flt(breakeven_monthly / 30.0),
			"safety_margin_pct": flt(((current.get("revenue", 0) - breakeven_monthly) / current.get("revenue", 1)) * 100, 1) if current.get("revenue") else 0.0,
			"monthly_budget_amount": monthly_budget_amount,
			"monthly_budget_used_pct": flt((month_expense / monthly_budget_amount) * 100, 1) if monthly_budget_amount else 0.0,
		},
		"pl_rows": rows,
	}


@frappe.whitelist()
def compute_management_roi(payload=None):
	"""ROI + payback period from the current-year monthly P&L."""
	_ensure_management_access()
	payload = _ops_parse_payload(payload)
	investment = flt(payload.get("investment"))
	if investment <= 0:
		frappe.throw(_("مبلغ سرمایه‌گذاری را وارد کنید (بزرگ‌تر از صفر)."))
	year = cint(payload.get("fiscal_year")) or cint(getdate(today()).year)
	rows = _ops_monthly_pl(year)
	nets = [r["net_profit"] for r in rows if r["revenue"] > 0]
	if not nets:
		frappe.throw(_("برای محاسبه بازگشت سرمایه ابتدا باید فروش ثبت‌شده در این سال داشته باشید."))
	avg_monthly_net = sum(nets) / len(nets)
	monthly_cash = avg_monthly_net if avg_monthly_net > 0 else 0.0
	payback_months = flt(investment / monthly_cash, 1) if monthly_cash else 0.0
	roi_year_1 = flt((avg_monthly_net * 12 / investment) * 100, 1) if investment else 0.0
	return {
		"investment": investment,
		"months_with_sales": len(nets),
		"avg_monthly_net_profit": flt(avg_monthly_net),
		"payback_months": payback_months,
		"roi_annual_pct": roi_year_1,
		"fiscal_year": year,
	}


# ---------------------------------------------------------------------------
# Report-center reports for ops/finance
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_courier_performance(date_from=None, date_to=None):
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT restaurant_courier AS courier, COUNT(*) AS delivered,
			   COALESCE(SUM(grand_total),0) AS revenue,
			   AVG(TIMESTAMPDIFF(MINUTE, creation, modified)) AS avg_minutes
		FROM `tabSales Order`
		WHERE docstatus = 1 AND restaurant_status = 'delivered'
		  AND COALESCE(restaurant_courier,'') != ''
		  AND transaction_date BETWEEN %(df)s AND %(dt)s
		GROUP BY restaurant_courier
		ORDER BY delivered DESC
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	) if _has_column("Sales Order", "restaurant_courier") else []
	out = []
	for row in rows:
		courier_name = ""
		if row.get("courier"):
			courier_name = frappe.db.get_value(COURIER_DOCTYPE, row["courier"], "courier_name") or row["courier"]
		out.append(
			{
				"courier": row.get("courier") or "",
				"courier_name": courier_name,
				"delivered": cint(row.get("delivered")),
				"revenue": flt(row.get("revenue")),
				"avg_minutes": flt(row.get("avg_minutes"), 1),
			}
		)
	summary = {
		"couriers": len(out),
		"delivered": sum(r["delivered"] for r in out),
		"revenue": flt(sum(r["revenue"] for r in out)),
	}
	return _compose_management_report(
		"courier-performance",
		"Courier Performance",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_waiter_performance(date_from=None, date_to=None):
	"""عملکرد گارسون‌ها: سفارش‌های ثبت‌شده به نام هر گارسون."""
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = frappe.db.sql(
		"""
		SELECT COALESCE(NULLIF(restaurant_waiter_name,''), restaurant_waiter) AS waiter_label,
			COUNT(*) AS orders, COALESCE(SUM(grand_total),0) AS revenue,
			AVG(grand_total) AS avg_order
		FROM `tabSales Order`
		WHERE docstatus = 1
		  AND COALESCE(restaurant_status,'') != 'cancelled'
		  AND (COALESCE(restaurant_waiter,'') != '' OR COALESCE(restaurant_waiter_name,'') != '')
		  AND transaction_date BETWEEN %(df)s AND %(dt)s
		GROUP BY waiter_label
		ORDER BY orders DESC
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	) if _has_column("Sales Order", "restaurant_waiter") else []
	out = [
		{
			"waiter": row.get("waiter_label") or "-",
			"orders": cint(row.get("orders")),
			"revenue": flt(row.get("revenue")),
			"avg_order": flt(row.get("avg_order")),
		}
		for row in rows
	]
	summary = {
		"waiters": len(out),
		"orders": sum(r["orders"] for r in out),
		"revenue": flt(sum(r["revenue"] for r in out)),
	}
	return _compose_management_report(
		"waiter-performance",
		"Waiter Performance",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_kitchen_performance(date_from=None, date_to=None):
	_ensure_management_access()
	date_to = str(date_to or today())
	date_from = str(date_from or add_days(date_to, -29))
	rows = []
	if _has_column("Sales Order", "restaurant_kitchen_ready_at") and _has_column("Sales Order", "restaurant_kitchen_started_at"):
		rows = frappe.db.sql(
			"""
			SELECT DATE(transaction_date) AS day, COUNT(*) AS orders,
				   AVG(TIMESTAMPDIFF(MINUTE, restaurant_kitchen_started_at, restaurant_kitchen_ready_at)) AS avg_prep,
				   MAX(TIMESTAMPDIFF(MINUTE, restaurant_kitchen_started_at, restaurant_kitchen_ready_at)) AS max_prep
			FROM `tabSales Order`
			WHERE docstatus = 1
			  AND restaurant_kitchen_ready_at IS NOT NULL
			  AND restaurant_kitchen_started_at IS NOT NULL
			  AND transaction_date BETWEEN %(df)s AND %(dt)s
			GROUP BY DATE(transaction_date)
			ORDER BY day ASC
			""",
			{"df": date_from, "dt": date_to},
			as_dict=True,
		)
	out = [
		{
			"day": str(row.get("day") or ""),
			"orders": cint(row.get("orders")),
			"avg_prep_minutes": flt(row.get("avg_prep"), 1),
			"max_prep_minutes": flt(row.get("max_prep"), 1),
		}
		for row in rows
	]
	summary = {
		"days": len(out),
		"orders": sum(r["orders"] for r in out),
		"avg_prep": flt(sum(r["avg_prep_minutes"] * r["orders"] for r in out) / max(sum(r["orders"] for r in out), 1), 1),
	}
	return _compose_management_report(
		"kitchen-performance",
		"Kitchen Performance",
		summary,
		out,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_profit_loss(date_from=None, date_to=None):
	_ensure_management_access()
	year = cint(getdate(date_from).year) if date_from else cint(getdate(today()).year)
	rows = _ops_monthly_pl(year)
	summary = {
		"revenue": flt(sum(r["revenue"] for r in rows)),
		"cogs": flt(sum(r["cogs"] for r in rows)),
		"gross": flt(sum(r["gross_profit"] for r in rows)),
		"net": flt(sum(r["net_profit"] for r in rows)),
		"year": year,
	}
	return _compose_management_report(
		"profit-loss",
		"Profit & Loss",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


@frappe.whitelist()
def get_management_report_breakeven(date_from=None, date_to=None):
	_ensure_management_access()
	year = cint(getdate(date_from).year) if date_from else cint(getdate(today()).year)
	rows = _ops_monthly_pl(year)
	total_revenue = sum(r["revenue"] for r in rows)
	total_cogs = sum(r["cogs"] for r in rows)
	ratio = (total_cogs / total_revenue) if total_revenue else 0.0
	fixed = _ops_fixed_monthly_cost()
	waste_avg = flt(sum(r["waste"] for r in rows) / max(len([r for r in rows if r["revenue"] > 0]), 1))
	breakeven_sales = (fixed + waste_avg) / (1 - ratio) if ratio < 1 else 0.0
	current_month = rows[cint(getdate(today()).month) - 1] if year == cint(getdate(today()).year) else rows[-1]
	actual = flt(current_month.get("revenue"))
	steps = []
	for factor in (0.8, 0.9, 1.0, 1.1, 1.2):
		sales = actual * factor if actual else breakeven_sales * factor
		profit = sales * (1 - ratio) - fixed - waste_avg
		steps.append(
			{
				"scenario": f"{int(factor * 100)}٪ فروش فعلی",
				"sales": flt(sales),
				"profit": flt(profit),
				"profitable": 1 if profit > 0 else 0,
			}
		)
	summary = {
		"cogs_ratio_pct": flt(ratio * 100, 1),
		"fixed_monthly": fixed,
		"waste_monthly_avg": waste_avg,
		"breakeven_sales": flt(breakeven_sales),
		"current_sales": actual,
		"safety_margin_pct": flt(((actual - breakeven_sales) / actual) * 100, 1) if actual else 0.0,
	}
	return _compose_management_report(
		"breakeven",
		"Break-Even Analysis",
		summary,
		steps,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


def ops_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	"""BI payload for ops/finance reports."""
	kpis, charts, insights = [], [], []
	tables = [{"key": "report-table", "title": title, "columns": _table_columns_from_rows(rows), "rows": rows}]

	if report_key == "courier-performance":
		kpis = [
			_bi_kpi("couriers", _("پیک‌های فعال"), cint(summary.get("couriers")), "count", 0),
			_bi_kpi("delivered", _("تحویل‌های انجام‌شده"), cint(summary.get("delivered")), "count", 0),
			_bi_kpi("revenue", _("مبلغ تحویل‌شده"), flt(summary.get("revenue")), "money", 0),
		]
		if rows:
			labels = [row.get("courier_name") or row.get("courier") for row in rows[:10]]
			charts = [
				{
					"key": "courier-deliveries",
					"title": _("تحویل به تفکیک پیک"),
					"type": "bar",
					"unit": "count",
					"labels": labels,
					"series": [{"key": "delivered", "label": _("تحویل"), "color": "#2f6f5c", "values": [cint(r.get("delivered")) for r in rows[:10]]}],
				}
			]
			fastest = min(rows, key=lambda r: r.get("avg_minutes") or 9999)
			insights.append({"key": "fastest", "severity": "info", "text": _("سریع‌ترین پیک: «{0}» (میانگین {1} دقیقه).").format(fastest.get("courier_name") or fastest.get("courier"), fastest.get("avg_minutes"))})

	elif report_key == "waiter-performance":
		kpis = [
			_bi_kpi("waiters", _("گارسون‌های فعال"), cint(summary.get("waiters")), "count", 0),
			_bi_kpi("orders", _("سفارش‌های ثبت‌شده"), cint(summary.get("orders")), "count", 0),
			_bi_kpi("revenue", _("فروش ثبت‌شده"), flt(summary.get("revenue")), "money", 0),
		]
		if rows:
			charts = [
				{
					"key": "waiter-orders",
					"title": _("سفارش به تفکیک گارسون"),
					"type": "bar",
					"unit": "count",
					"labels": [row.get("waiter") for row in rows[:10]],
					"series": [{"key": "orders", "label": _("سفارش"), "color": "#8b5cf6", "values": [cint(r.get("orders")) for r in rows[:10]]}],
				}
			]
			best = max(rows, key=lambda r: r.get("revenue") or 0)
			insights.append({"key": "best-waiter", "severity": "info", "text": _("بیشترین فروش: «{0}».").format(best.get("waiter"))})

	elif report_key == "kitchen-performance":
		kpis = [
			_bi_kpi("orders", _("سفارش‌های آماده‌شده"), cint(summary.get("orders")), "count", 0),
			_bi_kpi("avg_prep", _("میانگین آماده‌سازی (دقیقه)"), flt(summary.get("avg_prep")), "number", 0),
			_bi_kpi("days", _("روزهای دارای داده"), cint(summary.get("days")), "count", 0),
		]
		if rows:
			charts = [
				{
					"key": "prep-trend",
					"title": _("روند زمان آماده‌سازی"),
					"type": "line",
					"unit": "number",
					"labels": [row.get("day") for row in rows],
					"series": [{"key": "avg", "label": _("میانگین دقیقه"), "color": "#2f6f5c", "values": [flt(r.get("avg_prep_minutes")) for r in rows]}],
				}
			]
			slowest = max(rows, key=lambda r: r.get("avg_prep_minutes") or 0)
			insights.append({"key": "slowest-day", "severity": "warn", "text": _("کندترین روز آماده‌سازی: {0} (میانگین {1} دقیقه).").format(slowest.get("day"), slowest.get("avg_prep_minutes"))})

	elif report_key == "profit-loss":
		kpis = [
			_bi_kpi("revenue", _("درآمد سال"), flt(summary.get("revenue")), "money", 0),
			_bi_kpi("cogs", _("بهای فروش"), flt(summary.get("cogs")), "money", 0),
			_bi_kpi("gross", _("سود ناخالص"), flt(summary.get("gross")), "money", 0),
			_bi_kpi("net", _("سود خالص"), flt(summary.get("net")), "money", 0),
		]
		charts = [
			{
				"key": "pl-trend",
				"title": _("روند ماهانه سود خالص"),
				"type": "line",
				"unit": "money",
				"labels": [f"ماه {r['month']}" for r in rows],
				"series": [
					{"key": "net", "label": _("سود خالص"), "color": "#2f6f5c", "values": [flt(r.get("net_profit")) for r in rows]},
					{"key": "revenue", "label": _("درآمد"), "color": "#3e8ed0", "values": [flt(r.get("revenue")) for r in rows]},
				],
			}
		]
		loss_months = [r for r in rows if r["revenue"] > 0 and r["net_profit"] < 0]
		if loss_months:
			insights.append({"key": "loss-months", "severity": "warn", "text": _("{0} ماه با زیان خالص در این سال ثبت شده است.").format(len(loss_months))})

	elif report_key == "breakeven":
		kpis = [
			_bi_kpi("breakeven", _("نقطه سربه‌سر (فروش ماهانه)"), flt(summary.get("breakeven_sales")), "money", 0),
			_bi_kpi("current", _("فروش ماه جاری"), flt(summary.get("current_sales")), "money", 0),
			_bi_kpi("safety", _("حاشیه امنیت"), flt(summary.get("safety_margin_pct")), "percent", 0),
			_bi_kpi("cogs_ratio", _("نسبت بهای فروش"), flt(summary.get("cogs_ratio_pct")), "percent", 0),
		]
		if rows:
			charts = [
				{
					"key": "sensitivity",
					"title": _("تحلیل حساسیت سود به فروش"),
					"type": "bar",
					"unit": "money",
					"labels": [row.get("scenario") for row in rows],
					"series": [{"key": "profit", "label": _("سود خالص"), "color": "#2f6f5c", "values": [flt(r.get("profit")) for r in rows]}],
				}
			]
		insights.append({"key": "breakeven-hint", "severity": "info", "text": _("برای پوشش هزینه‌ها، حداقل فروش ماهانه باید حدود «{0}» باشد.").format(summary.get("breakeven_sales"))})

	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _ops_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_ops_register_into_api_module()
