# Copyright (c) 2026, Restaurant and contributors
"""Call center & VOIP caller-ID integration.

- PBX/VOIP webhook: when a customer calls, the PBX posts the caller
  number and a live call-log is created; the operator screen (call-center
  page) pops the customer card instantly.
- Customer card: club data (tier/segment/wallet), purchase history,
  VIP / dissatisfied / debtor alerts and addresses.
- Register orders via POS deep-link and push cashier notes.

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, now_datetime, today

from restaurant.api import (
	_ensure_management_access,
	_has_column,
	_parse_json,
)

__all__ = [
	"CALL_DOCTYPE",
	"_cc_ensure_ops_ready",
	"voip_incoming_call",
	"list_management_call_logs",
	"claim_management_call_log",
	"resolve_management_call_log",
	"get_call_center_customer",
	"send_call_center_note",
	"get_management_call_center_boot",
]

CALL_DOCTYPE = "Restaurant Call Log"
CALL_STATUSES = ["جدید", "در حال پاسخ", "پاسخ‌داده‌شده"]


# ---------------------------------------------------------------------------
# Lazy bridges
# ---------------------------------------------------------------------------


def _cc_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	fn = getattr(api_feature_pack, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_feature_pack helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _cc_api_call(helper_name, *args, **kwargs):
	from restaurant import api

	fn = getattr(api, helper_name, None)
	if not callable(fn):
		return None
	try:
		return fn(*args, **kwargs)
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"callcenter bridge failed: {helper_name}")
		return None


# ---------------------------------------------------------------------------
# Provisioning & settings
# ---------------------------------------------------------------------------


def _cc_ensure_ops_ready():
	try:
		_cc_fp_call(
			"_fp_ensure_custom_fields",
			"Restaurant Web Settings",
			[
				{"fieldname": "restaurant_callcenter_section", "label": "مرکز تماس و کالر آیدی", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_callcenter_enabled", "label": "مرکز تماس فعال", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_voip_token", "label": "توکن وب‌هوک VOIP", "fieldtype": "Data"},
				{"fieldname": "restaurant_callcenter_column", "label": "", "fieldtype": "Column Break"},
				{"fieldname": "restaurant_callcenter_notify_roles", "label": "نقش‌های دریافت‌کننده نوتیفیکیشن تماس", "fieldtype": "Data", "description": "جدا با کاما — پیش‌فرض: System Manager, Restaurant Manager"},
			],
			anchor_candidates=["restaurant_reservation_section", "restaurant_tax_section", "restaurant_club_section", "configuration_tab"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant callcenter ensure fields failed")


def _cc_setting(fieldname, default=None):
	try:
		value = frappe.db.get_single_value("Restaurant Web Settings", fieldname)
		return default if value in (None, "") else value
	except Exception:
		return default


# ---------------------------------------------------------------------------
# Customer lookup helpers
# ---------------------------------------------------------------------------


def _cc_find_customer_by_mobile(mobile):
	digits = "".join(ch for ch in str(mobile or "") if ch.isdigit())
	if len(digits) < 7:
		return ""
	for fieldname in ("mobile_no", "customer_primary_mobile"):
		if not _has_column("Customer", fieldname):
			continue
		exact = frappe.db.get_value("Customer", filters={fieldname: mobile.strip()}, fieldname="name")
		if exact:
			return exact
		candidates = frappe.get_all(
			"Customer",
			filters={fieldname: ["like", f"%{digits[-7:]}"]},
			fields=["name", fieldname],
			limit_page_length=5,
		)
		for row in candidates:
			cdigits = "".join(ch for ch in str(row.get(fieldname) or "") if ch.isdigit())
			if cdigits and (cdigits.endswith(digits[-7:]) or digits.endswith(cdigits[-7:])):
				return row["name"]
	return ""


def _cc_customer_addresses(customer):
	addresses = []
	try:
		links = frappe.get_all(
			"Dynamic Link",
			filters={"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
			fields=["parent"],
			limit_page_length=5,
		)
		for link in links:
			addr = frappe.db.get_value(
				"Address",
				link["parent"],
				["address_line1", "city", "state"],
				as_dict=True,
			)
			if addr:
				label = "، ".join(p for p in (addr.get("address_line1"), addr.get("city")) if p)
				if label:
					addresses.append(label)
	except Exception:
		pass
	if not addresses and _has_column("Customer", "customer_primary_address"):
		val = frappe.db.get_value("Customer", customer, "customer_primary_address")
		if val:
			addresses.append(val)
	return addresses


def _cc_customer_profile(customer):
	"""Full call-center profile for a Customer docname (may be empty)."""
	profile = {
		"found": 0,
		"customer": "",
		"customer_name": "",
		"mobile": "",
		"membership_code": "",
		"referral_code": "",
		"tier": "",
		"segment": "",
		"wallet_balance": 0.0,
		"birth_date": "",
		"addresses": [],
		"orders": [],
		"stats": {"orders_count": 0, "total_spent": 0.0, "avg_order": 0.0, "last_order": ""},
		"alerts": {"is_vip": 0, "dissatisfied": 0, "debtor_amount": 0.0},
	}
	if not customer:
		return profile
	row = frappe.db.get_value(
		"Customer",
		customer,
		["name", "customer_name", "mobile_no", "restaurant_membership_code", "restaurant_referral_code", "restaurant_customer_tier", "restaurant_customer_segment", "restaurant_birth_date"],
		as_dict=True,
	)
	if not row:
		return profile
	profile.update(
		{
			"found": 1,
			"customer": row.get("name"),
			"customer_name": row.get("customer_name") or row.get("name"),
			"mobile": (row.get("mobile_no") or "").strip(),
			"membership_code": row.get("restaurant_membership_code") or "",
			"referral_code": row.get("restaurant_referral_code") or "",
			"tier": row.get("restaurant_customer_tier") or "",
			"segment": row.get("restaurant_customer_segment") or "",
			"birth_date": str(row.get("restaurant_birth_date") or ""),
		}
	)
	profile["alerts"]["is_vip"] = 1 if profile["tier"] == "VIP" else 0
	profile["addresses"] = _cc_customer_addresses(customer)

	# Wallet balance
	try:
		wallet_balance = frappe.db.get_value("Restaurant Customer Wallet", {"customer": customer}, "balance")
		profile["wallet_balance"] = flt(wallet_balance)
	except Exception:
		pass

	# Orders + stats
	if frappe.db.exists("DocType", "Sales Order"):
		orders = frappe.get_all(
			"Sales Order",
			filters={"customer": customer, "docstatus": 1},
			fields=["name", "transaction_date", "grand_total", "restaurant_status", "restaurant_order_type", "company"],
			order_by="creation desc",
			limit_page_length=8,
		)
		profile["orders"] = [
			{
				"name": o["name"],
				"date": str(o.get("transaction_date") or ""),
				"grand_total": flt(o.get("grand_total")),
				"status": o.get("restaurant_status") or "",
				"channel": o.get("restaurant_order_type") or "",
				"branch": o.get("company") or "",
			}
			for o in orders
		]
		stat_row = frappe.db.sql(
			"""SELECT COUNT(*) AS c, COALESCE(SUM(grand_total),0) AS t, MAX(transaction_date) AS last FROM `tabSales Order` WHERE customer = %(c)s AND docstatus = 1""",
			{"c": customer},
			as_dict=True,
		)
		if stat_row:
			count = cint(stat_row[0].get("c"))
			total = flt(stat_row[0].get("t"))
			profile["stats"] = {
				"orders_count": count,
				"total_spent": total,
				"avg_order": flt(total / count) if count else 0.0,
				"last_order": str(stat_row[0].get("last") or ""),
			}

	# Debtor (outstanding sales invoices)
	if frappe.db.exists("DocType", "Sales Invoice"):
		debt_row = frappe.db.sql(
			"""SELECT COALESCE(SUM(outstanding_amount),0) AS debt FROM `tabSales Invoice` WHERE customer = %(c)s AND docstatus = 1 AND outstanding_amount > 0""",
			{"c": customer},
			as_dict=True,
		)
		if debt_row:
			profile["alerts"]["debtor_amount"] = flt(debt_row[0].get("debt"))

	# Dissatisfied: recent low survey response or review
	try:
		survey_hit = frappe.db.sql(
			"""
			SELECT COUNT(*) AS c FROM `tabRestaurant Survey Response`
			WHERE customer = %(c)s AND overall_rating <= 2 AND creation >= %(df)s
			""",
			{"c": customer, "df": add_days(now_datetime(), -90)},
			as_dict=True,
		)
		if survey_hit and cint(survey_hit[0].get("c")) > 0:
			profile["alerts"]["dissatisfied"] = 1
	except Exception:
		pass
	try:
		if frappe.db.exists("DocType", "Restaurant Customer Review") and not profile["alerts"]["dissatisfied"]:
			review_hit = frappe.db.count(
				"Restaurant Customer Review",
				{"customer": customer, "rating": ["<=", 2]},
			)
			if cint(review_hit) > 0:
				profile["alerts"]["dissatisfied"] = 1
	except Exception:
		pass

	# Suggested branch (most-ordered company, fallback handled by caller)
	if profile["orders"]:
		branches = {}
		for o in profile["orders"]:
			if o["branch"]:
				branches[o["branch"]] = branches.get(o["branch"], 0) + 1
		if branches:
			profile["suggested_branch"] = max(branches, key=branches.get)
	return profile


# ---------------------------------------------------------------------------
# VOIP webhook (guest, token-guarded)
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def voip_incoming_call(mobile="", token="", exten=""):
	"""PBX webhook: a call arrived → create a live call log + return customer info.

	POST /api/method/restaurant.api.voip_incoming_call
	Params: mobile (caller number), token (must match Restaurant Web Settings
	`restaurant_voip_token` when configured), exten (operator extension, optional).
	"""
	mobile = (mobile or "").strip()
	if not mobile:
		frappe.throw(_("شماره تماس ارسال نشده است."))
	expected = (_cc_setting("restaurant_voip_token", "") or "").strip()
	if expected and (token or "").strip() != expected:
		frappe.throw(_("توکن VOIP نامعتبر است."), frappe.PermissionError)
	if not frappe.db.exists("DocType", CALL_DOCTYPE):
		frappe.throw(_("داکتایپ مرکز تماس هنوز ساخته نشده؛ migrate اجرا کنید."))
	customer = _cc_find_customer_by_mobile(mobile)
	doc = frappe.new_doc(CALL_DOCTYPE)
	doc.caller_mobile = mobile
	doc.direction = "ورودی"
	doc.customer = customer or None
	doc.customer_name = frappe.db.get_value("Customer", customer, "customer_name") if customer else ""
	doc.status = "جدید"
	doc.exten = (exten or "").strip()
	doc.entry_date = now_datetime()
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	profile = _cc_customer_profile(customer) if customer else {"found": 0}
	return {"status": "success", "call": doc.name, "customer": profile}


# ---------------------------------------------------------------------------
# Operator screen endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_call_center_boot():
	_ensure_management_access()
	_cc_ensure_ops_ready()
	counts = {}
	if frappe.db.exists("DocType", CALL_DOCTYPE):
		rows = frappe.get_all(CALL_DOCTYPE, fields=["status", "COUNT(*) AS count"], group_by="status")
		counts = {row.get("status"): cint(row.get("count")) for row in rows}
	webhook_url = frappe.utils.get_url("/api/method/restaurant.api.voip_incoming_call")
	return {
		"counts": counts,
		"statuses": CALL_STATUSES,
		"webhook_url": webhook_url,
		"token_set": bool((_cc_setting("restaurant_voip_token", "") or "").strip()),
		"enabled": cint(_cc_setting("restaurant_callcenter_enabled", 1)) == 1,
	}


@frappe.whitelist()
def list_management_call_logs(status="", limit=20, since=""):
	"""Polling endpoint for the operator popup + call list."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", CALL_DOCTYPE):
		return {"calls": [], "count": 0}
	filters = {}
	if status:
		filters["status"] = status
	if since:
		filters["entry_date"] = [">", since]
	rows = frappe.get_all(
		CALL_DOCTYPE,
		filters=filters,
		fields=["name", "caller_mobile", "customer", "customer_name", "status", "agent", "exten", "note", "entry_date"],
		order_by="entry_date desc",
		limit_page_length=min(cint(limit) or 20, 100),
	)
	return {
		"calls": [
			{
				**row,
				"entry_date": str(row.get("entry_date") or ""),
			}
			for row in rows
		],
		"count": len(rows),
	}


@frappe.whitelist()
def claim_management_call_log(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(CALL_DOCTYPE, name):
		frappe.throw(_("تماس یافت نشد."))
	frappe.db.set_value(CALL_DOCTYPE, name, {"status": "در حال پاسخ", "agent": frappe.session.user}, update_modified=False)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def resolve_management_call_log(name="", note=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(CALL_DOCTYPE, name):
		frappe.throw(_("تماس یافت نشد."))
	updates = {"status": "پاسخ‌داده‌شده", "agent": frappe.session.user}
	if note:
		updates["note"] = (note or "").strip()
	frappe.db.set_value(CALL_DOCTYPE, name, updates, update_modified=False)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def get_call_center_customer(mobile=""):
	"""Customer card for the operator screen (by phone number)."""
	_ensure_management_access()
	customer = _cc_find_customer_by_mobile(mobile)
	profile = _cc_customer_profile(customer)
	if not profile.get("found"):
		profile["mobile"] = (mobile or "").strip()
	return profile


@frappe.whitelist()
def send_call_center_note(payload=None):
	"""Send a note to the destination branch register (notification + order note)."""
	_ensure_management_access()
	payload = _parse_json(payload, {})
	note = (payload.get("note") or "").strip()
	if not note:
		frappe.throw(_("متن یادداشت الزامی است."))
	order_name = (payload.get("order_name") or "").strip()
	branch = (payload.get("branch") or "").strip()
	if order_name and frappe.db.exists("Sales Order", order_name):
		_cc_api_call("_append_sales_order_note", order_name, f"[CALL CENTER] {note}")
	roles_raw = (_cc_setting("restaurant_callcenter_notify_roles", "") or "System Manager, Restaurant Manager")
	roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
	recipients = []
	try:
		recipients = [
			row["parent"]
			for row in frappe.get_all("Has Role", filters={"role": ["in", roles]}, fields=["parent"])
			if row.get("parent") not in ("Guest", "Administrator")
		][:8]
	except Exception:
		pass
	subject = _("یادداشت مرکز تماس") + (f" — {order_name}" if order_name else "") + (f" ({branch})" if branch else "")
	for user in recipients:
		try:
			frappe.get_doc(
				{
					"doctype": "Notification Log",
					"type": "Alert",
					"document_type": "Sales Order" if order_name else CALL_DOCTYPE,
					"document_name": order_name or "-",
					"from_user": frappe.session.user,
					"for_user": user,
					"subject": subject,
					"email_content": note,
				}
			).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Restaurant callcenter note failed")
	frappe.db.commit()
	return {"status": "success", "notified": len(recipients)}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _cc_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_cc_register_into_api_module()
