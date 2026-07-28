# Copyright (c) 2026, Restaurant and contributors
"""Reservations & appointment management.

- Online/phone/counter reservation capture (guest form + management desk).
- Date/time, table/seat selection, party size, status lifecycle.
- Automatic SMS reminder before the reservation (hourly scheduler job)
  reusing the customer-club SMS machinery.

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime, today

from restaurant.api import (
	_ensure_management_access,
	_has_column,
	_management_get_print_brand_settings,
	_parse_json,
)

__all__ = [
	"RESERVATION_DOCTYPE",
	"RESERVATION_STATUSES",
	"_rsv_ensure_ops_ready",
	"list_management_reservations",
	"save_management_reservation",
	"update_management_reservation_status",
	"delete_management_reservation",
	"get_management_reservation_boot",
	"get_public_reservation_context",
	"submit_public_reservation",
	"run_reservation_reminders",
]

RESERVATION_DOCTYPE = "Restaurant Reservation"
RESERVATION_STATUSES = ["در انتظار", "تاییدشده", "نشست", "لغوشده", "حاضر‌نشد"]
RESERVATION_SOURCES = ["سایت", "تلفنی", "صندوق"]


# ---------------------------------------------------------------------------
# Lazy bridges (import-cycle safety)
# ---------------------------------------------------------------------------


def _rsv_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	fn = getattr(api_feature_pack, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_feature_pack helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _rsv_club_call(helper_name, *args, **kwargs):
	from restaurant import api_club

	fn = getattr(api_club, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_club helper missing: {helper_name}")
	return fn(*args, **kwargs)


# ---------------------------------------------------------------------------
# Provisioning (custom fields / settings)
# ---------------------------------------------------------------------------


def _rsv_ensure_ops_ready():
	"""Idempotently create Web Settings fields used by reservations."""
	try:
		_rsv_fp_call(
			"_fp_ensure_custom_fields",
			"Restaurant Web Settings",
			[
				{"fieldname": "restaurant_reservation_section", "label": "تنظیمات رزرواسیون", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_reservation_enabled", "label": "رزرواسیون فعال", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_reservation_reminder_hours", "label": "ساعت‌های قبل از رزرو برای یادآوری", "fieldtype": "Int", "default": "2"},
				{"fieldname": "restaurant_reservation_column", "label": "", "fieldtype": "Column Break"},
				{"fieldname": "restaurant_reservation_sms_reminder_enabled", "label": "یادآوری پیامکی رزرو", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_reservation_min_party", "label": "حداقل نفرات", "fieldtype": "Int", "default": "1"},
				{"fieldname": "restaurant_reservation_max_party", "label": "حداکثر نفرات", "fieldtype": "Int", "default": "20"},
			],
			anchor_candidates=["restaurant_club_section", "restaurant_inventory_section", "restaurant_pos_section", "configuration_tab"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant reservation ensure fields failed")


def _rsv_setting(fieldname, default=None):
	try:
		value = frappe.db.get_single_value("Restaurant Web Settings", fieldname)
		return default if value in (None, "") else value
	except Exception:
		return default


def _rsv_settings():
	return {
		"enabled": cint(_rsv_setting("restaurant_reservation_enabled", 1)) == 1,
		"reminder_hours": cint(_rsv_setting("restaurant_reservation_reminder_hours", 2)) or 2,
		"sms_reminder_enabled": cint(_rsv_setting("restaurant_reservation_sms_reminder_enabled", 1)) == 1,
		"min_party": cint(_rsv_setting("restaurant_reservation_min_party", 1)) or 1,
		"max_party": cint(_rsv_setting("restaurant_reservation_max_party", 20)) or 20,
	}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rsv_tables():
	"""Active bookable tables/seats."""
	if not frappe.db.exists("DocType", "Restaurant Table"):
		return []
	fields = ["name", "table_number", "location", "is_active", "status"]
	try:
		rows = frappe.get_all(
			"Restaurant Table",
			filters={"is_active": 1},
			fields=fields,
			order_by="table_number asc",
			limit_page_length=300,
		)
	except Exception:
		rows = []
	return [
		{
			"name": row.get("name"),
			"table_name": row.get("table_number") or row.get("name"),
			"location": row.get("location") or "",
			"status": row.get("status") or "",
		}
		for row in rows
	]


def _rsv_reservation_datetime(row):
	date_part = str(row.get("reservation_date") or today())
	time_part = str(row.get("reservation_time") or "19:00")
	if len(time_part) > 5:
		time_part = time_part[:5]
	try:
		return get_datetime(f"{date_part} {time_part}:00")
	except Exception:
		return get_datetime(f"{today()} 19:00:00")


def _serialize_reservation(row):
	return {
		"name": row.get("name"),
		"customer_name": row.get("customer_name") or "",
		"mobile": row.get("mobile") or "",
		"reservation_date": str(row.get("reservation_date") or ""),
		"reservation_time": str(row.get("reservation_time") or "")[:5],
		"party_size": cint(row.get("party_size")),
		"restaurant_table": row.get("restaurant_table") or "",
		"table_label": row.get("restaurant_table") or "",
		"status": row.get("status") or "در انتظار",
		"source": row.get("source") or "سایت",
		"note": row.get("note") or "",
		"reminder_sent": cint(row.get("reminder_sent")),
		"creation": str(row.get("creation") or ""),
	}


def _rsv_validate_payload(payload):
	customer_name = (payload.get("customer_name") or "").strip()
	mobile = (payload.get("mobile") or "").strip()
	if not customer_name:
		frappe.throw(_("نام مشتری الزامی است."))
	if not mobile:
		frappe.throw(_("شماره موبایل برای یادآوری رزرو الزامی است."))
	reservation_date = (payload.get("reservation_date") or "").strip()
	if not reservation_date:
		frappe.throw(_("تاریخ رزرو الزامی است."))
	reservation_time = (payload.get("reservation_time") or "").strip()[:5] or "19:00"
	party_size = cint(payload.get("party_size")) or 1
	settings = _rsv_settings()
	party_size = max(settings["min_party"], min(settings["max_party"], party_size))
	table = (payload.get("restaurant_table") or "").strip()
	if table and _has_column("Restaurant Table", "name") and not frappe.db.exists("Restaurant Table", table):
		frappe.throw(_("جایگاه انتخاب‌شده یافت نشد: {0}").format(table))
	return {
		"customer_name": customer_name,
		"mobile": mobile,
		"reservation_date": reservation_date,
		"reservation_time": reservation_time,
		"party_size": party_size,
		"restaurant_table": table,
		"note": (payload.get("note") or "").strip(),
		"status": payload.get("status") if payload.get("status") in RESERVATION_STATUSES else "در انتظار",
		"source": payload.get("source") if payload.get("source") in RESERVATION_SOURCES else "سایت",
	}


def _rsv_notify_managers(reservation, subject):
	"""Notification Log fan-out to management users."""
	recipients = []
	try:
		recipients = [
			row["parent"]
			for row in frappe.get_all(
				"Has Role",
				filters={"role": ["in", ["System Manager", "Restaurant Manager"]]},
				fields=["parent"],
			)
			if row.get("parent") not in ("Guest", "Administrator")
		][:5]
	except Exception:
		recipients = []
	for user in recipients:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"type": "Alert",
					"document_type": RESERVATION_DOCTYPE,
					"document_name": reservation.get("name"),
					"from_user": frappe.session.user if frappe.session.user != "Guest" else "Administrator",
					"for_user": user,
					"subject": subject,
					"email_content": _("{0} — {1} نفر، {2} ساعت {3}").format(
						reservation.get("customer_name"),
						reservation.get("party_size"),
						reservation.get("reservation_date"),
						reservation.get("reservation_time"),
					),
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Restaurant reservation notify failed")


# ---------------------------------------------------------------------------
# Management endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_reservation_boot():
	_ensure_management_access()
	_rsv_ensure_ops_ready()
	settings = _rsv_settings()
	counts = {}
	if frappe.db.exists("DocType", RESERVATION_DOCTYPE):
		rows = frappe.get_all(
			RESERVATION_DOCTYPE,
			filters={"reservation_date": today()},
			fields=["status", "COUNT(*) AS count"],
			group_by="status",
		)
		counts = {row.get("status"): cint(row.get("count")) for row in rows}
	return {
		"settings": settings,
		"tables": _rsv_tables(),
		"statuses": RESERVATION_STATUSES,
		"sources": RESERVATION_SOURCES,
		"today_counts": counts,
		"today": today(),
	}


@frappe.whitelist()
def list_management_reservations(date_from="", date_to="", status="", table="", search="", limit=100, offset=0):
	_ensure_management_access()
	if not frappe.db.exists("DocType", RESERVATION_DOCTYPE):
		return {"reservations": [], "count": 0}
	filters = {}
	if date_from and date_to:
		filters["reservation_date"] = ["between", [date_from, date_to]]
	elif date_from:
		filters["reservation_date"] = [">=", date_from]
	elif date_to:
		filters["reservation_date"] = ["<=", date_to]
	if status:
		filters["status"] = status
	if table:
		filters["restaurant_table"] = table
	rows = frappe.get_all(
		RESERVATION_DOCTYPE,
		filters=filters,
		fields=["name", "customer_name", "mobile", "reservation_date", "reservation_time", "party_size", "restaurant_table", "status", "source", "note", "reminder_sent", "creation"],
		order_by="reservation_date asc, reservation_time asc",
		limit_start=cint(offset),
		limit_page_length=min(cint(limit) or 100, 300),
	)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		if search and search not in (row.get("customer_name") or "").lower() and search not in (row.get("mobile") or "").lower():
			continue
		items.append(_serialize_reservation(row))
	return {"reservations": items, "count": len(items)}


@frappe.whitelist()
def save_management_reservation(payload=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", RESERVATION_DOCTYPE):
		frappe.throw(_("داکتایپ رزرو هنوز ساخته نشده است؛ لطفاً migrate اجرا کنید."))
	payload = _parse_json(payload, {})
	data = _rsv_validate_payload(payload)
	name = (payload.get("name") or "").strip()
	if name and frappe.db.exists(RESERVATION_DOCTYPE, name):
		doc = frappe.get_doc(RESERVATION_DOCTYPE, name)
	else:
		doc = frappe.new_doc(RESERVATION_DOCTYPE)
	for key, value in data.items():
		setattr(doc, key, value)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "reservation": _serialize_reservation(doc.as_dict())}


@frappe.whitelist()
def update_management_reservation_status(payload=None):
	_ensure_management_access()
	payload = _parse_json(payload, {})
	name = (payload.get("name") or "").strip()
	status = (payload.get("status") or "").strip()
	if status not in RESERVATION_STATUSES:
		frappe.throw(_("وضعیت نامعتبر است: {0}").format(status or "-"))
	if not frappe.db.exists(RESERVATION_DOCTYPE, name):
		frappe.throw(_("رزرو یافت نشد: {0}").format(name or "-"))
	frappe.db.set_value(RESERVATION_DOCTYPE, name, "status", status, update_modified=False)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def delete_management_reservation(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(RESERVATION_DOCTYPE, name):
		frappe.throw(_("رزرو یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(RESERVATION_DOCTYPE, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


# ---------------------------------------------------------------------------
# Public (guest) endpoint
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def get_public_reservation_context():
	"""Bookable tables + settings for the public /reserve page."""
	_rsv_ensure_ops_ready()
	settings = _rsv_settings()
	return {
		"enabled": settings["enabled"],
		"tables": _rsv_tables(),
		"min_party": settings["min_party"],
		"max_party": settings["max_party"],
		"brand": _management_get_print_brand_settings(),
	}


@frappe.whitelist(allow_guest=True)
def submit_public_reservation(payload=None):
	"""Guest reservation from the online /reserve page."""
	settings = _rsv_settings()
	if not settings["enabled"]:
		frappe.throw(_("رزرو آنلاین در حال حاضر غیرفعال است."))
	if not frappe.db.exists("DocType", RESERVATION_DOCTYPE):
		frappe.throw(_("رزرواسیون هنوز راه‌اندازی نشده است."))
	payload = _parse_json(payload, {})
	data = _rsv_validate_payload(payload)
	data["source"] = "سایت"
	doc = frappe.new_doc(RESERVATION_DOCTYPE)
	for key, value in data.items():
		setattr(doc, key, value)
	doc.status = "در انتظار"
	doc.insert(ignore_permissions=True)
	_rsv_notify_managers(doc.as_dict(), _("رزرو جدید از سایت"))
	frappe.db.commit()
	return {"status": "success", "reservation_code": doc.name}


# ---------------------------------------------------------------------------
# Automatic SMS reminder (hourly scheduler)
# ---------------------------------------------------------------------------


def run_reservation_reminders():
	"""Send SMS reminders for upcoming reservations (called hourly)."""
	if not frappe.db.exists("DocType", RESERVATION_DOCTYPE):
		return {"status": "skipped", "reason": "doctype-missing"}
	settings = _rsv_settings()
	if not settings["sms_reminder_enabled"]:
		return {"status": "skipped", "reason": "disabled"}
	now = now_datetime()
	rows = frappe.get_all(
		RESERVATION_DOCTYPE,
		filters={"status": ["in", ["در انتظار", "تاییدشده"]], "reminder_sent": 0, "reservation_date": [">=", today()]},
		fields=["name", "customer_name", "mobile", "reservation_date", "reservation_time", "party_size", "restaurant_table", "status"],
		limit_page_length=100,
	)
	sent = 0
	for row in rows:
		res_dt = _rsv_reservation_datetime(row)
		delta_hours = (res_dt - now).total_seconds() / 3600.0
		if delta_hours < 0 or delta_hours > settings["reminder_hours"]:
			continue
		message = _(
			"{0} عزیز، رزرو شما برای امروز ساعت {1} به تعداد {2} نفر ثبت است. منتظر حضورتان هستیم."
		).format(row.get("customer_name"), str(row.get("reservation_time") or "")[:5], cint(row.get("party_size")))
		try:
			send_status, send_note = _rsv_club_call("_club_send_sms_now", row.get("mobile"), message)
			_rsv_club_call(
				"_club_log_sms",
				mobile=row.get("mobile"),
				message=message,
				kind="دستی",
				status_note=(send_status, send_note),
			)
			sent += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Restaurant reservation SMS reminder failed")
		frappe.db.set_value(RESERVATION_DOCTYPE, row["name"], "reminder_sent", 1, update_modified=False)
	frappe.db.commit()
	return {"status": "success", "reminded": sent}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _rsv_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_rsv_register_into_api_module()
