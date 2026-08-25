# Copyright (c) 2026, Restaurant and contributors
"""Organizational (B2B) customers: contracts, sub-accounts (معین), credit and
consolidated invoicing.

Reuses ERPNext base doctypes (``Customer`` for the organization itself —
customer_kind = «سازمانی», ``Sales Order``/``Sales Invoice`` for orders and
invoices). Only the two contract/member doctypes are new because ERPNext has
no equivalent for restaurant org-order rules (daily/monthly caps, allowed
days/hours, address restrictions, per-member sub-accounts).

Endpoints are re-exported into ``restaurant.api`` (star-import at the bottom
of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import json

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from restaurant.api import (
	_ensure_management_access,
	_has_column,
)

__all__ = [
	"_org_ensure_ops_ready",
	"org_validate_order",
	# boot & contracts
	"get_management_org_boot",
	"list_management_org_contracts",
	"save_management_org_contract",
	"delete_management_org_contract",
	# members (معین)
	"list_management_org_members",
	"save_management_org_member",
	"delete_management_org_member",
	"org_member_login",
	# assigning customers to orgs
	"assign_management_customer_organization",
	# credit monitoring
	"get_management_org_credit",
	# org orders & excel
	"list_management_org_orders",
	"export_management_org_orders_excel",
	# consolidated invoicing
	"create_management_org_invoice",
	# accountant portal (guest)
	"org_portal_login",
	"org_portal_overview",
	"org_portal_orders",
	"org_portal_invoices",
]

ORG_CONTRACT_DOCTYPE = "Restaurant Organization Contract"
ORG_MEMBER_DOCTYPE = "Restaurant Organization Member"
ORG_INVOICE_MODES = ["پس از هر سفارش", "هفتگی", "ماهانه"]
ORG_CONTRACT_STATUSES = ["پیش‌نویس", "فعال", "تعلیق", "پایان‌یافته"]
WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
_ORG_EXPORT_COLUMNS = [
	"کد سفارش",
	"تاریخ",
	"معین",
	"مشتری",
	"مبلغ (ریال)",
	"وضعیت",
	"فاکتور تجمیعی",
]


# ---------------------------------------------------------------------------
# Lazy bridges (import-cycle safety)
# ---------------------------------------------------------------------------


def _org_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	return getattr(api_feature_pack, helper_name)(*args, **kwargs)


def _org_club_call(helper_name, *args, **kwargs):
	from restaurant import api_club

	return getattr(api_club, helper_name)(*args, **kwargs)


def _org_parse_json(value, fallback=None):
	if fallback is None:
		fallback = {}
	if isinstance(value, (dict, list)):
		return value
	try:
		return json.loads(value) if value else fallback
	except Exception:
		return fallback


def _org_parse_payload(payload):
	data = _org_parse_json(payload, {})
	return data if isinstance(data, dict) else {}


def _org_list(value):
	items = _org_parse_json(value, [])
	return items if isinstance(items, list) else []


# ---------------------------------------------------------------------------
# Custom fields
# ---------------------------------------------------------------------------


def _org_ensure_ops_ready():
	_org_fp_call(
		"_fp_ensure_custom_fields",
		"Sales Order",
		[
			{"fieldname": "restaurant_org_invoice", "label": _("فاکتور تجمیعی سازمان"), "fieldtype": "Link", "options": "Sales Invoice"},
		],
		anchor_candidates=["restaurant_organization", "restaurant_status"],
	)
	_org_fp_call(
		"_fp_ensure_custom_fields",
		"Sales Invoice",
		[
			{"fieldname": "restaurant_organization", "label": _("سازمان"), "fieldtype": "Link", "options": "Customer"},
			{"fieldname": "restaurant_org_contract", "label": _("قرارداد سازمانی"), "fieldtype": "Link", "options": ORG_CONTRACT_DOCTYPE},
		],
		anchor_candidates=["customer", "customer_name"],
	)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _org_active_contract(organization):
	if not organization or not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		return None
	rows = frappe.get_all(
		ORG_CONTRACT_DOCTYPE,
		filters={"organization": organization, "status": "فعال"},
		fields=["name"],
		order_by="creation desc",
		limit_page_length=1,
		ignore_permissions=True,
	)
	return rows[0].get("name") if rows else ""


def _org_get_contract(name):
	if not name or not frappe.db.exists(ORG_CONTRACT_DOCTYPE, name):
		return None
	return frappe.get_doc(ORG_CONTRACT_DOCTYPE, name)


def _org_resolve_member_for_customer(customer_name):
	"""Member record linked to this club customer (if any)."""
	if not customer_name or not frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		return None
	rows = frappe.get_all(
		ORG_MEMBER_DOCTYPE,
		filters={"member_customer": customer_name, "is_active": 1},
		fields=["name"],
		limit_page_length=1,
		ignore_permissions=True,
	)
	return rows[0].get("name") if rows else ""


def _org_authenticate_member(username, access_code):
	username = (username or "").strip()
	access_code = (access_code or "").strip()
	if not username or not frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		frappe.throw(_("نام کاربری معین الزامی است."))
	rows = frappe.get_all(
		ORG_MEMBER_DOCTYPE,
		filters={"username": username},
		fields=["name", "organization", "full_name", "access_code", "is_active", "member_customer", "daily_cap", "monthly_cap", "role_title", "mobile"],
		limit_page_length=1,
		ignore_permissions=True,
	)
	if not rows:
		frappe.throw(_("معینی با این نام کاربری یافت نشد."))
	member = rows[0]
	if not cint(member.get("is_active")):
		frappe.throw(_("این معین غیرفعال است."))
	stored = (member.get("access_code") or "").strip()
	if stored and stored != access_code:
		frappe.throw(_("رمز عبور معین اشتباه است."))
	return member


def _org_usage(organization, member_customer="", member_name=""):
	"""Real-time credit monitoring: usage today / this month for the org (or a member)."""
	conditions = ["so.docstatus = 1", "COALESCE(so.restaurant_status,'') != 'cancelled'"]
	params = {}
	if member_name:
		conditions.append("COALESCE(so.restaurant_org_member,'') = %(member)s")
		params["member"] = member_name
	else:
		conditions.append("COALESCE(so.restaurant_organization,'') = %(org)s")
		params["org"] = organization
	if member_customer and not member_name:
		conditions.append("so.customer = %(cust)s")
		params["cust"] = member_customer

	base = "SELECT {agg} FROM `tabSales Order` so WHERE " + " AND ".join(conditions)
	rows = frappe.db.sql(
		base.format(agg=(
			"COALESCE(SUM(CASE WHEN so.transaction_date = CURDATE() THEN so.grand_total ELSE 0 END),0) AS day_usage, "
			"COALESCE(SUM(CASE WHEN DATE_FORMAT(so.transaction_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m') THEN so.grand_total ELSE 0 END),0) AS month_usage, "
			"COUNT(CASE WHEN so.transaction_date = CURDATE() THEN 1 END) AS day_count"
		)),
		params,
		as_dict=True,
	)
	row = rows[0] if rows else {}
	return {
		"day_usage": flt(row.get("day_usage")),
		"month_usage": flt(row.get("month_usage")),
		"day_count": cint(row.get("day_count")),
	}


def _weekday_persian(date_str=None):
	try:
		dt = getdate(date_str or today())
	except Exception:
		dt = getdate(today())
	# python weekday(): Monday=0 .. Sunday=6 → Persian: شنبه=Saturday
	mapping = {5: "شنبه", 6: "یکشنبه", 0: "دوشنبه", 1: "سه‌شنبه", 2: "چهارشنبه", 3: "پنجشنبه", 4: "جمعه"}
	return mapping.get(dt.weekday(), "شنبه")


def _org_check_contract_rules(contract, member, amount, delivery_address_name=""):
	"""Enforce allowed days/hours, daily/monthly caps and address restrictions."""
	org = contract.organization
	label = frappe.db.get_value("Customer", org, "customer_name") or org

	# 1) allowed weekdays
	allowed_days = [d for d in _org_list(contract.allowed_days) if isinstance(d, str) and d.strip()]
	if allowed_days:
		today_name = _weekday_persian()
		if today_name not in allowed_days:
			frappe.throw(_("سفارش‌گذاری «{0}» امروز ({1}) برای این قرارداد مجاز نیست.").format(label, today_name))

	# 2) allowed hours
	from_hour = cint(contract.allowed_from_hour)
	to_hour = cint(contract.allowed_to_hour)
	if to_hour and (from_hour or to_hour):
		hour = now_datetime().hour
		if not (from_hour <= hour < to_hour):
			frappe.throw(
				_("ساعت سفارش‌گذاری «{0}» از {1} تا {2} است.").format(label, from_hour, to_hour)
			)

	# 3) address restriction
	if cint(contract.restrict_addresses):
		allowed = [a for a in _org_list(contract.allowed_addresses) if isinstance(a, str) and a.strip()]
		address_name = (delivery_address_name or "").strip()
		if allowed and address_name not in allowed:
			frappe.throw(_("سفارش «{0}» فقط به آدرس‌های تعریف‌شده در قرارداد مجاز است.").format(label))

	# 4) caps — member overrides contract (0 = inherit / unlimited)
	amount = flt(amount)
	member_caps = member or {}
	daily_cap = flt(member_caps.get("daily_cap")) or flt(contract.daily_order_cap)
	monthly_cap = flt(member_caps.get("monthly_cap")) or flt(contract.monthly_order_cap)
	usage = _org_usage(org)
	member_usage = {"day_usage": 0.0, "month_usage": 0.0}
	if member and member.get("name"):
		member_usage = _org_usage(org, member_name=member.get("name"))

	if daily_cap > 0:
		used = member_usage.get("day_usage") if member and flt(member_caps.get("daily_cap")) else usage.get("day_usage")
		if used + amount > daily_cap:
			frappe.throw(
				_("سقف سفارش روزانه «{0}» ({1} ریال) تکمیل است؛ مصرف امروز: {2} ریال.").format(
					member.get("full_name") if member and flt(member_caps.get("daily_cap")) else label,
					frappe.format_value(daily_cap, {"fieldtype": "Currency"}),
					frappe.format_value(used, {"fieldtype": "Currency"}),
				)
			)
	if monthly_cap > 0:
		used = member_usage.get("month_usage") if member and flt(member_caps.get("monthly_cap")) else usage.get("month_usage")
		if used + amount > monthly_cap:
			frappe.throw(
				_("سقف سفارش ماهانه «{0}» ({1} ریال) تکمیل است؛ مصرف این ماه: {2} ریال.").format(
					member.get("full_name") if member and flt(member_caps.get("monthly_cap")) else label,
					frappe.format_value(monthly_cap, {"fieldtype": "Currency"}),
					frappe.format_value(used, {"fieldtype": "Currency"}),
				)
			)


def org_validate_order(order_context, customer_name, amount, delivery_address_name=""):
	"""Called from ``_create_sales_order`` (pre-insert). Returns binding dict
	``{organization, org_member, org_member_name}`` — empty dict when the order
	is not an organizational order. Throws (rolls the txn back) on rule hits.
	"""
	ctx = order_context if isinstance(order_context, dict) else {}
	if not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		return {}

	member = None
	username = (ctx.get("org_member") or "").strip()
	if username:
		member = _org_authenticate_member(username, ctx.get("org_access_code"))
	organization = member.get("organization") if member else ""

	if not organization and customer_name and _has_column("Customer", "restaurant_organization"):
		organization = (frappe.db.get_value("Customer", customer_name, "restaurant_organization") or "").strip()
	if not organization and customer_name:
		member_name = _org_resolve_member_for_customer(customer_name)
		if member_name:
			member = frappe.get_doc(ORG_MEMBER_DOCTYPE, member_name).as_dict()
			organization = member.get("organization")
	if not organization:
		return {}

	contract_name = _org_active_contract(organization)
	if not contract_name:
		# Org without active contract binds for reporting but has no limits
		return {
			"organization": organization,
			"org_member": member.get("full_name") if member else "",
			"org_member_code": member.get("username") if member else "",
		}
	contract = _org_get_contract(contract_name)
	_org_check_contract_rules(contract, member, amount, delivery_address_name=delivery_address_name)
	return {
		"organization": organization,
		"org_member": member.get("full_name") if member else "",
		"org_member_code": member.get("username") if member else "",
		"via_contract": contract_name,
	}


# ---------------------------------------------------------------------------
# Boot, contracts, members
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_org_boot():
	_ensure_management_access()
	_org_ensure_ops_ready()
	orgs = 0
	if _has_column("Customer", "restaurant_customer_kind"):
		orgs = frappe.db.count("Customer", {"disabled": 0, "restaurant_customer_kind": "سازمانی"}) or 0

	contracts_active = 0
	members = 0
	if frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		contracts_active = frappe.db.count(ORG_CONTRACT_DOCTYPE, {"status": "فعال"}) or 0
	if frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		members = frappe.db.count(ORG_MEMBER_DOCTYPE, {"is_active": 1}) or 0

	month_usage = 0.0
	if _has_column("Sales Order", "restaurant_organization"):
		rows = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(grand_total),0) AS total FROM `tabSales Order`
			WHERE docstatus = 1
				AND COALESCE(restaurant_organization,'') != ''
				AND COALESCE(restaurant_status,'') != 'cancelled'
				AND DATE_FORMAT(transaction_date, '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')
			""",
			as_dict=True,
		)
		month_usage = flt(rows[0].get("total")) if rows else 0.0

	return {
		"kpis": {
			"organizations": cint(orgs),
			"active_contracts": cint(contracts_active),
			"members": cint(members),
			"month_usage": month_usage,
		},
		"weekdays": WEEKDAYS,
		"invoice_modes": ORG_INVOICE_MODES,
		"contract_statuses": ORG_CONTRACT_STATUSES,
	}


def _serialize_contract(doc):
	org_label = frappe.db.get_value("Customer", doc.get("organization"), "customer_name") if doc.get("organization") else ""
	return {
		"name": doc.get("name"),
		"organization": doc.get("organization") or "",
		"organization_label": org_label or doc.get("organization") or "",
		"contract_no": doc.get("contract_no") or "",
		"start_date": str(doc.get("start_date") or ""),
		"end_date": str(doc.get("end_date") or ""),
		"status": doc.get("status") or "فعال",
		"daily_order_cap": flt(doc.get("daily_order_cap")),
		"monthly_order_cap": flt(doc.get("monthly_order_cap")),
		"allowed_days": _org_list(doc.get("allowed_days")),
		"allowed_from_hour": cint(doc.get("allowed_from_hour")),
		"allowed_to_hour": cint(doc.get("allowed_to_hour")),
		"restrict_addresses": cint(doc.get("restrict_addresses")),
		"allowed_addresses": _org_list(doc.get("allowed_addresses")),
		"invoice_mode": doc.get("invoice_mode") or "ماهانه",
		"portal_access_code_set": bool((doc.get("portal_access_code") or "").strip()),
		"note": doc.get("note") or "",
	}


@frappe.whitelist()
def list_management_org_contracts(status="", search=""):
	_ensure_management_access()
	if not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		return {"contracts": [], "count": 0}
	filters = {}
	if status and status in ORG_CONTRACT_STATUSES:
		filters["status"] = status
	rows = frappe.get_all(ORG_CONTRACT_DOCTYPE, filters=filters, fields=["name"], order_by="creation desc", limit_page_length=300, ignore_permissions=True)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		doc = frappe.get_doc(ORG_CONTRACT_DOCTYPE, row["name"]).as_dict()
		item = _serialize_contract(doc)
		if search and search not in (item["organization_label"] or "").lower() and search not in (item["contract_no"] or "").lower():
			continue
		items.append(item)
	return {"contracts": items, "count": len(items)}


@frappe.whitelist()
def save_management_org_contract(payload=None):
	_ensure_management_access()
	_org_ensure_ops_ready()
	if not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		frappe.throw(_("ماژول قرارداد سازمانی هنوز آماده نیست (migrate لازم است)."))
	payload = _org_parse_payload(payload)
	organization = (payload.get("organization") or "").strip()
	if not organization or not frappe.db.exists("Customer", organization):
		frappe.throw(_("مشتری سازمانی الزامی است (نوع مشتری را روی «سازمانی» بگذارید)."))
	# mark customer as organizational automatically (معرفی دستی به اشتراک سازمانی)
	if _has_column("Customer", "restaurant_customer_kind"):
		frappe.db.set_value("Customer", organization, "restaurant_customer_kind", "سازمانی", update_modified=False)

	name = (payload.get("name") or "").strip()
	if name and frappe.db.exists(ORG_CONTRACT_DOCTYPE, name):
		doc = frappe.get_doc(ORG_CONTRACT_DOCTYPE, name)
	else:
		doc = frappe.new_doc(ORG_CONTRACT_DOCTYPE)
		doc.organization = organization
		if not (payload.get("contract_no") or "").strip():
			doc.contract_no = "CT-" + frappe.generate_hash(length=6).upper()
	doc.contract_no = (payload.get("contract_no") or doc.contract_no or "").strip()
	doc.start_date = (payload.get("start_date") or str(today()))[:10]
	doc.end_date = (payload.get("end_date") or "")[:10] or None
	status = (payload.get("status") or doc.status or "فعال").strip()
	doc.status = status if status in ORG_CONTRACT_STATUSES else "فعال"
	doc.daily_order_cap = flt(payload.get("daily_order_cap"))
	doc.monthly_order_cap = flt(payload.get("monthly_order_cap"))
	allowed_days = payload.get("allowed_days")
	if allowed_days is not None:
		days = [d for d in _org_list(allowed_days) if d in WEEKDAYS]
		doc.allowed_days = json.dumps(days, ensure_ascii=False)
	if payload.get("allowed_from_hour") is not None:
		doc.allowed_from_hour = min(max(cint(payload.get("allowed_from_hour")), 0), 23)
	if payload.get("allowed_to_hour") is not None:
		doc.allowed_to_hour = min(max(cint(payload.get("allowed_to_hour")), 0), 24)
	if payload.get("restrict_addresses") is not None:
		doc.restrict_addresses = cint(payload.get("restrict_addresses"))
	if payload.get("allowed_addresses") is not None:
		doc.allowed_addresses = json.dumps(_org_list(payload.get("allowed_addresses")), ensure_ascii=False)
	invoice_mode = (payload.get("invoice_mode") or doc.invoice_mode or "ماهانه").strip()
	doc.invoice_mode = invoice_mode if invoice_mode in ORG_INVOICE_MODES else "ماهانه"
	if payload.get("portal_access_code") is not None:
		doc.portal_access_code = (payload.get("portal_access_code") or "").strip()
	doc.note = (payload.get("note") or doc.note or "").strip()
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"status": "success", "contract": _serialize_contract(doc.as_dict())}


@frappe.whitelist()
def delete_management_org_contract(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not name or not frappe.db.exists(ORG_CONTRACT_DOCTYPE, name):
		frappe.throw(_("قرارداد یافت نشد: {0}").format(name or "-"))
	frappe.delete_doc(ORG_CONTRACT_DOCTYPE, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "deleted": name}


def _serialize_member(row):
	org_label = frappe.db.get_value("Customer", row.get("organization"), "customer_name") if row.get("organization") else ""
	return {
		"name": row.get("name"),
		"organization": row.get("organization") or "",
		"organization_label": org_label or row.get("organization") or "",
		"member_customer": row.get("member_customer") or "",
		"full_name": row.get("full_name") or "",
		"mobile": row.get("mobile") or "",
		"username": row.get("username") or "",
		"role_title": row.get("role_title") or "",
		"daily_cap": flt(row.get("daily_cap")),
		"monthly_cap": flt(row.get("monthly_cap")),
		"is_active": cint(row.get("is_active")),
	}


@frappe.whitelist()
def list_management_org_members(organization="", search=""):
	_ensure_management_access()
	if not frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		return {"members": [], "count": 0}
	filters = {}
	if organization:
		filters["organization"] = organization
	rows = frappe.get_all(ORG_MEMBER_DOCTYPE, filters=filters, fields=["*"], order_by="creation desc", limit_page_length=400, ignore_permissions=True)
	search = (search or "").strip().lower()
	items = []
	for row in rows:
		item = _serialize_member(row)
		if search and search not in (item["full_name"] or "").lower() and search not in (item["username"] or "").lower() and search not in (item["mobile"] or "").lower():
			continue
		items.append(item)
	return {"members": items, "count": len(items)}


@frappe.whitelist()
def save_management_org_member(payload=None):
	"""تعریف معین (نام کاربری و رمز عبور) برای مشتری سازمانی."""
	_ensure_management_access()
	if not frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		frappe.throw(_("ماژول معین سازمانی هنوز آماده نیست (migrate لازم است)."))
	payload = _org_parse_payload(payload)
	organization = (payload.get("organization") or "").strip()
	full_name = (payload.get("full_name") or "").strip()
	if not organization or not frappe.db.exists("Customer", organization):
		frappe.throw(_("سازمان الزامی است."))
	if not full_name:
		frappe.throw(_("نام و نام خانوادگی معین الزامی است."))
	username = (payload.get("username") or "").strip()
	mobile = (payload.get("mobile") or "").strip()
	if not username:
		username = mobile or ("u" + frappe.generate_hash(length=6).lower())

	name = (payload.get("name") or "").strip()
	if name and frappe.db.exists(ORG_MEMBER_DOCTYPE, name):
		doc = frappe.get_doc(ORG_MEMBER_DOCTYPE, name)
	else:
		if frappe.db.exists(ORG_MEMBER_DOCTYPE, {"username": username}):
			frappe.throw(_("این نام کاربری قبلاً برای معین دیگری ثبت شده است."))
		doc = frappe.new_doc(ORG_MEMBER_DOCTYPE)
	doc.organization = organization
	doc.full_name = full_name
	doc.mobile = mobile
	doc.username = username
	if payload.get("access_code") is not None:
		doc.access_code = (payload.get("access_code") or "").strip()
	doc.role_title = (payload.get("role_title") or doc.role_title or "").strip()
	doc.daily_cap = flt(payload.get("daily_cap"))
	doc.monthly_cap = flt(payload.get("monthly_cap"))
	if payload.get("is_active") is not None:
		doc.is_active = cint(payload.get("is_active"))
	else:
		doc.is_active = 1

	# معرفی دستی مشتری باشگاه به اشتراک سازمانی (اختیاری)
	member_customer = (payload.get("member_customer") or "").strip()
	if not member_customer and mobile and _has_column("Customer", "mobile_no"):
		member_customer = frappe.db.get_value("Customer", {"mobile_no": mobile, "disabled": 0}, "name") or ""
	if member_customer and frappe.db.exists("Customer", member_customer):
		doc.member_customer = member_customer
		if _has_column("Customer", "restaurant_organization"):
			frappe.db.set_value("Customer", member_customer, "restaurant_organization", organization, update_modified=False)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()
	return {"status": "success", "member": _serialize_member(doc.as_dict())}


@frappe.whitelist()
def delete_management_org_member(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not name or not frappe.db.exists(ORG_MEMBER_DOCTYPE, name):
		frappe.throw(_("معین یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(ORG_MEMBER_DOCTYPE, name)
	member_customer = doc.member_customer
	frappe.delete_doc(ORG_MEMBER_DOCTYPE, name, ignore_permissions=True)
	if member_customer and _has_column("Customer", "restaurant_organization"):
		frappe.db.set_value("Customer", member_customer, "restaurant_organization", "", update_modified=False)
	frappe.db.commit()
	return {"status": "success", "deleted": name}


@frappe.whitelist()
def assign_management_customer_organization(payload=None):
	"""معرفی دستی مشتری به اشتراک سازمانی (بدون معین)."""
	_ensure_management_access()
	payload = _org_parse_payload(payload)
	customer = (payload.get("customer") or "").strip()
	organization = (payload.get("organization") or "").strip()
	if not customer or not frappe.db.exists("Customer", customer):
		frappe.throw(_("مشتری یافت نشد: {0}").format(customer or "-"))
	if organization and not frappe.db.exists("Customer", organization):
		frappe.throw(_("سازمان یافت نشد: {0}").format(organization or "-"))
	if not _has_column("Customer", "restaurant_organization"):
		_org_club_call("_club_ensure_ops_ready")
	frappe.db.set_value("Customer", customer, "restaurant_organization", organization, update_modified=False)
	frappe.db.commit()
	return {"status": "success", "customer": customer, "organization": organization}


@frappe.whitelist(allow_guest=True)
def org_member_login(username="", access_code=""):
	"""Login of an organizational sub-account (معین) for ordering."""
	member = _org_authenticate_member(username, access_code)
	org_label = frappe.db.get_value("Customer", member.get("organization"), "customer_name") or member.get("organization")
	customer_name = ""
	if member.get("member_customer"):
		customer_name = frappe.db.get_value("Customer", member.get("member_customer"), "customer_name") or ""
	return {
		"status": "success",
		"member": {
			"username": member.get("username"),
			"full_name": member.get("full_name"),
			"role_title": member.get("role_title") or "",
			"organization": member.get("organization"),
			"organization_label": org_label,
			"customer": member.get("member_customer") or "",
			"customer_name": customer_name,
			"mobile": member.get("mobile") or "",
		},
	}


# ---------------------------------------------------------------------------
# Real-time credit monitoring (رصد لحظه‌ای وضعیت اعتبار سازمان)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_org_credit(organization=""):
	_ensure_management_access()
	organization = (organization or "").strip()
	if not organization or not frappe.db.exists("Customer", organization):
		frappe.throw(_("سازمان یافت نشد: {0}").format(organization or "-"))
	contract_name = _org_active_contract(organization)
	contract = _org_get_contract(contract_name) if contract_name else None
	usage = _org_usage(organization)

	members_usage = []
	if frappe.db.exists("DocType", ORG_MEMBER_DOCTYPE):
		for row in frappe.get_all(
			ORG_MEMBER_DOCTYPE,
			filters={"organization": organization, "is_active": 1},
			fields=["name", "full_name", "username", "daily_cap", "monthly_cap", "role_title"],
			ignore_permissions=True,
		):
			mu = _org_usage(organization, member_name=row.get("full_name"))
			members_usage.append(
				{
					**row,
					"day_usage": mu["day_usage"],
					"month_usage": mu["month_usage"],
					"day_count": mu["day_count"],
					"uninvoiced": _org_uninvoiced_total(organization, member_name=row.get("full_name")),
				}
			)

	return {
		"organization": organization,
		"organization_label": frappe.db.get_value("Customer", organization, "customer_name") or organization,
		"contract": _serialize_contract(contract.as_dict()) if contract else None,
		"usage": {**usage, "uninvoiced": _org_uninvoiced_total(organization)},
		"members": members_usage,
	}


def _org_uninvoiced_total(organization, member_name=""):
	if not _has_column("Sales Order", "restaurant_org_invoice"):
		return 0.0
	conditions = [
		"docstatus = 1",
		"COALESCE(restaurant_status,'') != 'cancelled'",
		"COALESCE(restaurant_organization,'') = %(org)s",
		"COALESCE(restaurant_org_invoice,'') = ''",
	]
	params = {"org": organization}
	if member_name:
		conditions.append("COALESCE(restaurant_org_member,'') = %(member)s")
		params["member"] = member_name
	rows = frappe.db.sql(
		"SELECT COALESCE(SUM(grand_total),0) AS total, COUNT(*) AS count FROM `tabSales Order` WHERE " + " AND ".join(conditions),
		params,
		as_dict=True,
	)
	return {"total": flt(rows[0].get("total")) if rows else 0.0, "count": cint(rows[0].get("count")) if rows else 0}


# ---------------------------------------------------------------------------
# Org orders (لیست + خروجی اکسل)
# ---------------------------------------------------------------------------


def _org_orders_rows(organization, date_from="", date_to="", member="", invoiced="", search="", limit=500, offset=0):
	if not _has_column("Sales Order", "restaurant_organization"):
		return []
	conditions = ["so.docstatus = 1", "COALESCE(so.restaurant_organization,'') = %(org)s"]
	params = {"org": organization}
	if date_from:
		conditions.append("so.transaction_date >= %(df)s")
		params["df"] = str(date_from)[:10]
	if date_to:
		conditions.append("so.transaction_date <= %(dt)s")
		params["dt"] = str(date_to)[:10]
	if member:
		conditions.append("COALESCE(so.restaurant_org_member,'') = %(member)s")
		params["member"] = member
	if invoiced == "yes":
		conditions.append("COALESCE(so.restaurant_org_invoice,'') != ''")
	elif invoiced == "no":
		conditions.append("COALESCE(so.restaurant_org_invoice,'') = ''")
	if search:
		conditions.append("(so.name LIKE %(needle)s OR so.customer_name LIKE %(needle)s)")
		params["needle"] = f"%{search}%"
	return frappe.db.sql(
		"""
		SELECT so.name, so.transaction_date, so.customer, so.customer_name, so.grand_total,
			COALESCE(so.restaurant_status,'') AS status,
			COALESCE(so.restaurant_org_member,'') AS org_member,
			COALESCE(so.restaurant_org_invoice,'') AS org_invoice
		FROM `tabSales Order` so
		WHERE {where}
		ORDER BY so.transaction_date DESC, so.creation DESC
		LIMIT %(limit)s OFFSET %(offset)s
		""".format(where=" AND ".join(conditions)),
		{**params, "limit": min(max(cint(limit) or 500, 1), 2000), "offset": max(cint(offset) or 0, 0)},
		as_dict=True,
	)


@frappe.whitelist()
def list_management_org_orders(organization="", date_from="", date_to="", member="", invoiced="", search="", limit=200, offset=0):
	_ensure_management_access()
	organization = (organization or "").strip()
	if not organization:
		frappe.throw(_("سازمان را انتخاب کنید."))
	rows = _org_orders_rows(organization, date_from, date_to, member, invoiced, search, limit=limit, offset=offset)
	un = _org_uninvoiced_total(organization)
	return {
		"orders": [
			{
				"name": row["name"],
				"date": str(row.get("transaction_date") or ""),
				"customer": row.get("customer") or "",
				"customer_name": row.get("customer_name") or "",
				"grand_total": flt(row.get("grand_total")),
				"status": row.get("status") or "",
				"org_member": row.get("org_member") or "",
				"org_invoice": row.get("org_invoice") or "",
			}
			for row in rows
		],
		"count": len(rows),
		"uninvoiced": un,
	}


@frappe.whitelist()
def export_management_org_orders_excel(organization="", date_from="", date_to="", member="", invoiced="", search=""):
	"""خروجی اکسل سفارش‌های سازمانی."""
	_ensure_management_access()
	organization = (organization or "").strip()
	if not organization:
		frappe.throw(_("سازمان را انتخاب کنید."))
	rows = _org_orders_rows(organization, date_from, date_to, member, invoiced, search, limit=2000)
	data = [list(_ORG_EXPORT_COLUMNS)]
	for row in rows:
		data.append(
			[
				row["name"],
				str(row.get("transaction_date") or ""),
				row.get("org_member") or "-",
				row.get("customer_name") or row.get("customer") or "-",
				flt(row.get("grand_total")),
				row.get("status") or "-",
				row.get("org_invoice") or "-",
			]
		)
	# totals row
	data.append(["جمع", "", "", "", sum(flt(r.get("grand_total")) for r in rows), "", ""])
	try:
		from frappe.utils.xlsxutils import make_xlsx
	except Exception:
		frappe.throw(_("خروجی اکسل روی این سرور در دسترس نیست (xlsxutils)."))
	org_label = frappe.db.get_value("Customer", organization, "customer_name") or organization
	xlsx_file = make_xlsx(data, "Org Orders")
	file_name = "org-orders-{}.xlsx".format(now_datetime().strftime("%Y%m%d-%H%M%S"))
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": xlsx_file.getvalue(),
			"is_private": 1,
			"folder": "Home",
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": "success",
		"file_url": file_doc.file_url,
		"file_name": file_doc.file_name,
		"rows": len(rows),
		"organization": org_label,
	}


# ---------------------------------------------------------------------------
# Consolidated invoicing (صدور یک فاکتور برای چند سفارش سازمانی)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def create_management_org_invoice(payload=None):
	"""صدور فاکتور تجمیعی سازمانی از چند سفارش + همگام‌سازی وضعیت."""
	_ensure_management_access()
	_org_ensure_ops_ready()
	payload = _org_parse_payload(payload)
	organization = (payload.get("organization") or "").strip()
	if not organization or not frappe.db.exists("Customer", organization):
		frappe.throw(_("سازمان یافت نشد: {0}").format(organization or "-"))
	order_names = payload.get("order_names") or []
	if isinstance(order_names, str):
		order_names = _org_list(order_names)
	orders = [o for o in order_names if isinstance(o, str) and o.strip()]
	if not orders:
		frappe.throw(_("حداقل یک سفارش برای صدور فاکتور انتخاب کنید."))

	valid = []
	for so_name in orders:
		so_name = so_name.strip()
		if not frappe.db.exists("Sales Order", so_name):
			continue
		if cint(frappe.db.get_value("Sales Order", so_name, "docstatus")) != 1:
			frappe.throw(_("سفارش {0} تأییدنشده است.").format(so_name))
		if _has_column("Sales Order", "restaurant_org_invoice") and frappe.db.get_value("Sales Order", so_name, "restaurant_org_invoice"):
			frappe.throw(_("سفارش {0} قبلاً در فاکتور تجمیعی دیگری قرار گرفته است.").format(so_name))
		valid.append(so_name)
	if not valid:
		frappe.throw(_("سفارش معتبری برای صدور فاکتور یافت نشد."))

	company = frappe.db.get_value("Sales Order", valid[0], "company")
	si = frappe.new_doc("Sales Invoice")
	si.customer = organization
	si.company = company
	si.posting_date = today()
	if _has_column("Sales Invoice", "restaurant_organization"):
		si.restaurant_organization = organization
	contract_name = _org_active_contract(organization)
	if contract_name and _has_column("Sales Invoice", "restaurant_org_contract"):
		si.restaurant_org_contract = contract_name
	si.set("remarks", "")
	notes = []

	income_seen = set()
	for so_name in valid:
		so = frappe.get_doc("Sales Order", so_name)
		notes.append(so_name)
		for item in so.get("items") or []:
			line = {
				"item_code": item.get("item_code"),
				"item_name": item.get("item_name") or item.get("item_code"),
				"description": item.get("description") or item.get("item_name") or item.get("item_code"),
				"qty": flt(item.get("qty")),
				"uom": item.get("uom") or item.get("stock_uom") or "Nos",
				"rate": flt(item.get("rate")),
			}
			if item.get("income_account"):
				line["income_account"] = item.get("income_account")
			elif not income_seen:
				default_income = frappe.db.get_value("Company", company, "default_income_account") or ""
				if default_income and default_income not in income_seen:
					line["income_account"] = default_income
			income_seen.add(line.get("income_account") or "")
			si.append("items", line)
	si.set("remarks", _("فاکتور تجمیعی سازمانی — سفارش‌ها: {0}").format("، ".join(notes)))
	si.flags.ignore_permissions = True
	si.insert(ignore_permissions=True)

	for so_name in valid:
		if _has_column("Sales Order", "restaurant_org_invoice"):
			frappe.db.set_value("Sales Order", so_name, "restaurant_org_invoice", si.name, update_modified=False)
	frappe.db.commit()
	return {
		"status": "success",
		"sales_invoice": si.name,
		"orders": valid,
		"grand_total": flt(si.grand_total),
	}


# ---------------------------------------------------------------------------
# Accountant portal (دسترسی آنلاین حسابدار سازمان به فاکتورها)
# ---------------------------------------------------------------------------


def _org_portal_verify(organization, access_code):
	organization = (organization or "").strip()
	access_code = (access_code or "").strip()
	if not organization or not frappe.db.exists("DocType", ORG_CONTRACT_DOCTYPE):
		frappe.throw(_("سازمان یافت نشد."))
	rows = frappe.get_all(
		ORG_CONTRACT_DOCTYPE,
		filters={"organization": organization, "portal_access_code": access_code, "status": ["in", ["فعال", "تعلیق"]]},
		fields=["name"],
		ignore_permissions=True,
		limit_page_length=1,
	)
	if not access_code or not rows:
		frappe.throw(_("کد دسترسی نامعتبر است."))
	return rows[0]["name"]


@frappe.whitelist(allow_guest=True)
def org_portal_login(organization="", access_code=""):
	contract_name = _org_portal_verify(organization, access_code)
	contract = _org_get_contract(contract_name)
	return {
		"status": "success",
		"organization": organization,
		"organization_label": frappe.db.get_value("Customer", organization, "customer_name") or organization,
		"contract_no": contract.contract_no or "",
		"invoice_mode": contract.invoice_mode or "",
		"contract_status": contract.status or "",
	}


@frappe.whitelist(allow_guest=True)
def org_portal_overview(organization="", access_code=""):
	"""اعتبار لحظه‌ای + اقلام فاکتورنشده — نمای آنلاین حسابدار سازمان."""
	contract_name = _org_portal_verify(organization, access_code)
	contract = _org_get_contract(contract_name)
	usage = _org_usage(organization)
	un = _org_uninvoiced_total(organization)
	return {
		"organization": organization,
		"organization_label": frappe.db.get_value("Customer", organization, "customer_name") or organization,
		"contract_no": contract.contract_no or "",
		"invoice_mode": contract.invoice_mode or "",
		"daily_order_cap": flt(contract.daily_order_cap),
		"monthly_order_cap": flt(contract.monthly_order_cap),
		"day_usage": usage["day_usage"],
		"month_usage": usage["month_usage"],
		"uninvoiced_total": un["total"],
		"uninvoiced_count": un["count"],
	}


@frappe.whitelist(allow_guest=True)
def org_portal_orders(organization="", access_code="", date_from="", date_to="", limit=200):
	_org_portal_verify(organization, access_code)
	rows = _org_orders_rows((organization or "").strip(), date_from, date_to, "", "", "", limit=limit)
	return {
		"orders": [
			{
				"name": row["name"],
				"date": str(row.get("transaction_date") or ""),
				"grand_total": flt(row.get("grand_total")),
				"status": row.get("status") or "",
				"org_member": row.get("org_member") or "",
				"org_invoice": row.get("org_invoice") or "",
			}
			for row in rows
		],
		"count": len(rows),
	}


@frappe.whitelist(allow_guest=True)
def org_portal_invoices(organization="", access_code="", limit=100):
	_org_portal_verify(organization, access_code)
	organization = (organization or "").strip()
	filters = {"customer": organization, "docstatus": 1}
	conditions = ["customer = %(org)s", "docstatus = 1"]
	params = {"org": organization, "limit": min(max(cint(limit) or 100, 1), 500)}
	if _has_column("Sales Invoice", "restaurant_organization"):
		conditions.append("COALESCE(restaurant_organization,'') = %(org)s")
	rows = frappe.db.sql(
		"""
		SELECT name, posting_date, grand_total, outstanding_amount, status
		FROM `tabSales Invoice`
		WHERE {where}
		ORDER BY posting_date DESC, creation DESC
		LIMIT %(limit)s
		""".format(where=" AND ".join(conditions)),
		params,
		as_dict=True,
	)
	return {
		"invoices": [
			{
				"name": row["name"],
				"posting_date": str(row.get("posting_date") or ""),
				"grand_total": flt(row.get("grand_total")),
				"outstanding_amount": flt(row.get("outstanding_amount")),
				"status": row.get("status") or "",
			}
			for row in rows
		],
		"count": len(rows),
	}
