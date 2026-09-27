"""Public collaboration intake, with conversion into canonical ERPNext Customer records."""

import json
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from restaurant.api import _ensure_management_access, _ensure_mobile

REQUEST_DOCTYPE = "Restaurant Collaboration Request"
COLLABORATION_TYPES = {"سازمان و محل کار", "باشگاه ورزشی", "مربی و شاگردان"}
FREQUENCIES = {"روزانه", "هفتگی", "ماهانه", "بر اساس قرارداد"}
WEEKDAYS = {"شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"}

__all__ = [
	"submit_public_collaboration_request",
	"list_management_collaboration_requests",
	"review_management_collaboration_request",
]


def _parse_payload(payload):
	if isinstance(payload, str):
		try:
			payload = json.loads(payload)
		except (TypeError, ValueError):
			payload = {}
	return payload if isinstance(payload, dict) else {}


def _clean_text(value, limit):
	return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value or "")).strip()[:limit]


def _validate_application(data):
	kind = _clean_text(data.get("collaboration_type"), 40)
	contact = _clean_text(data.get("contact_name"), 140)
	organization = _clean_text(data.get("organization_name"), 180)
	mobile = _ensure_mobile(data.get("mobile"))
	address = _clean_text(data.get("address"), 700)
	frequency = _clean_text(data.get("frequency"), 30)
	if kind not in COLLABORATION_TYPES:
		frappe.throw(_("نوع همکاری انتخاب‌شده معتبر نیست."))
	if not contact or not organization:
		frappe.throw(_("نام رابط و نام مجموعه را وارد کنید."))
	if len(address) < 8:
		frappe.throw(_("نشانی محل فعالیت را کامل وارد کنید."))
	if not cint(data.get("accepted_terms")):
		frappe.throw(_("برای ثبت درخواست، پذیرش قوانین همکاری الزامی است."))
	if frequency and frequency not in FREQUENCIES:
		frappe.throw(_("تناوب پیشنهادی معتبر نیست."))
	weekdays = data.get("weekdays") or []
	if isinstance(weekdays, str):
		try:
			weekdays = json.loads(weekdays)
		except (TypeError, ValueError):
			weekdays = []
	if not isinstance(weekdays, list):
		weekdays = []
	weekdays = sorted({str(day).strip() for day in weekdays if str(day).strip() in WEEKDAYS}, key=list(WEEKDAYS).index)
	if frequency == "هفتگی" and not weekdays:
		frappe.throw(_("برای برنامه هفتگی دست‌کم یک روز را انتخاب کنید."))
	email = _clean_text(data.get("email"), 160).lower()
	if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
		frappe.throw(_("نشانی ایمیل معتبر نیست."))
	return {
		"collaboration_type": kind,
		"contact_name": contact,
		"mobile": mobile,
		"email": email,
		"organization_name": organization,
		"address": address,
		"expected_members": max(0, min(cint(data.get("expected_members")), 100000)),
		"meal_count": max(0, min(cint(data.get("meal_count")), 10000)),
		"frequency": frequency,
		"weekdays": json.dumps(weekdays, ensure_ascii=False),
		"delivery_time": _clean_text(data.get("delivery_time"), 8),
		"start_date": _clean_text(data.get("start_date"), 10),
		"details": _clean_text(data.get("details"), 1000),
		"accepted_terms": 1,
	}


@frappe.whitelist(allow_guest=True)
def submit_public_collaboration_request(payload=None):
	"""Save a rate-limited public application; no customer or contract is created yet."""
	if not frappe.db.exists("DocType", REQUEST_DOCTYPE):
		frappe.throw(_("فرم همکاری هنوز آماده نشده است."))
	data = _validate_application(_parse_payload(payload))
	cache = frappe.cache()
	key = "restaurant:collaboration-request:{}".format(frappe.generate_hash(data["mobile"], length=20))
	if cache.get_value(key):
		frappe.throw(_("درخواست شما اخیراً ثبت شده است؛ لطفاً پیش از ارسال دوباره منتظر تماس همکاران ما بمانید."))
	doc = frappe.get_doc({"doctype": REQUEST_DOCTYPE, **data})
	doc.insert(ignore_permissions=True)
	cache.set_value(key, 1, expires_in_sec=3600)
	frappe.db.commit()
	return {"status": "success", "request_id": doc.name}


def _request_row(doc):
	return {
		"name": doc.name,
		"status": doc.status,
		"collaboration_type": doc.collaboration_type,
		"contact_name": doc.contact_name,
		"mobile": doc.mobile,
		"email": doc.email,
		"organization_name": doc.organization_name,
		"address": doc.address,
		"expected_members": cint(doc.expected_members),
		"meal_count": cint(doc.meal_count),
		"frequency": doc.frequency,
		"weekdays": doc.weekdays,
		"delivery_time": str(doc.delivery_time or ""),
		"start_date": str(doc.start_date or ""),
		"details": doc.details,
		"customer": doc.customer,
		"review_note": doc.review_note,
		"creation": str(doc.creation or ""),
	}


@frappe.whitelist()
def list_management_collaboration_requests(status="", limit=100):
	_ensure_management_access()
	filters = {"status": status} if status in {"جدید", "در حال بررسی", "تأییدشده", "ردشده"} else {}
	rows = frappe.get_all(
		REQUEST_DOCTYPE,
		filters=filters,
		fields=["name"],
		order_by="creation desc",
		limit_page_length=min(max(cint(limit) or 100, 1), 300),
		ignore_permissions=True,
	)
	return {"requests": [_request_row(frappe.get_doc(REQUEST_DOCTYPE, row.name)) for row in rows]}


def _default_customer_group():
	group = frappe.db.get_single_value("Selling Settings", "customer_group")
	if group and frappe.db.exists("Customer Group", group):
		return group
	return frappe.db.get_value("Customer Group", {"is_group": 0}, "name")


def _default_territory():
	territory = frappe.db.get_single_value("Selling Settings", "territory")
	if territory and frappe.db.exists("Territory", territory):
		return territory
	return frappe.db.get_value("Territory", {"is_group": 0}, "name")


def _get_or_create_customer_for_request(doc):
	from restaurant import api_club

	api_club._club_ensure_ops_ready()
	if doc.collaboration_type == "مربی و شاگردان" and api_club._has_column("Customer", "mobile_no"):
		customer = frappe.db.get_value("Customer", {"mobile_no": doc.mobile, "disabled": 0}, "name") or ""
	else:
		customer = frappe.db.get_value("Customer", {"customer_name": doc.organization_name, "disabled": 0}, "name") or ""
	if customer:
		customer_doc = frappe.get_doc("Customer", customer)
	else:
		customer_doc = frappe.new_doc("Customer")
		customer_doc.customer_name = doc.organization_name if doc.collaboration_type != "مربی و شاگردان" else doc.contact_name
		customer_doc.customer_type = "Individual" if doc.collaboration_type == "مربی و شاگردان" else "Company"
		customer_group = _default_customer_group()
		territory = _default_territory()
		if not customer_group or not territory:
			frappe.throw(_("برای ساخت مشتری ابتدا گروه مشتری و قلمرو پیش‌فرض فروش را تنظیم کنید."))
		customer_doc.customer_group = customer_group
		customer_doc.territory = territory
		customer_doc.mobile_no = doc.mobile
		customer_doc.email_id = doc.email or ""
		customer_doc.insert(ignore_permissions=True)
		customer = customer_doc.name
	if api_club._has_column("Customer", "restaurant_customer_kind"):
		frappe.db.set_value("Customer", customer, "restaurant_customer_kind", "حقیقی" if doc.collaboration_type == "مربی و شاگردان" else "سازمانی", update_modified=False)
	return customer


@frappe.whitelist()
def review_management_collaboration_request(name="", decision="", note="", coach_discount_percent=5, coach_commission_percent=5, customer_group="", customer=""):
	_ensure_management_access()
	name = _clean_text(name, 140)
	decision = _clean_text(decision, 20)
	if decision not in {"approve", "reject", "review"}:
		frappe.throw(_("اقدام بررسی معتبر نیست."))
	if not frappe.db.exists(REQUEST_DOCTYPE, name):
		frappe.throw(_("درخواست همکاری یافت نشد."))
	doc = frappe.get_doc(REQUEST_DOCTYPE, name)
	if doc.status == "تأییدشده" and decision == "approve":
		return {"status": "success", "request": _request_row(doc)}
	if decision == "approve":
		from restaurant import api_club

		api_club._club_ensure_customer_fields()
		is_coach = doc.collaboration_type == "مربی و شاگردان"
		if is_coach:
			customer = _clean_text(customer, 140)
			if not customer or not frappe.db.exists("Customer", customer) or frappe.db.get_value("Customer", customer, "disabled"):
				frappe.throw(_("برای تأیید مربی، یک Customer موجود را صریحاً انتخاب کنید؛ از روی شمارهٔ فرم حساب به‌صورت خودکار متصل نمی‌شود."))
		else:
			customer = _get_or_create_customer_for_request(doc)
		discount = min(max(flt(coach_discount_percent or 0), 0), 50)
		commission = min(max(flt(coach_commission_percent or 0), 0), 50)
		if is_coach and discount + commission > 100:
			frappe.throw(_("جمع درصد تخفیف شاگرد و سهم مربی نمی‌تواند از ۱۰۰٪ بیشتر شود."))
		if is_coach and customer_group:
			if not frappe.db.exists("Customer Group", customer_group) or frappe.db.get_value("Customer Group", customer_group, "is_group"):
				frappe.throw(_("برای مربی یک گروه نهایی مشتری انتخاب کنید."))
			frappe.db.set_value("Customer", customer, "customer_group", customer_group, update_modified=False)
		if frappe.db.has_column("Customer", "restaurant_collaboration_type"):
			frappe.db.set_value("Customer", customer, "restaurant_collaboration_type", doc.collaboration_type, update_modified=False)
		if frappe.db.has_column("Customer", "restaurant_collaboration_status"):
			frappe.db.set_value("Customer", customer, "restaurant_collaboration_status", "تأییدشده", update_modified=False)
		if frappe.db.has_column("Customer", "restaurant_coach_invites_enabled"):
			frappe.db.set_value("Customer", customer, "restaurant_coach_invites_enabled", int(is_coach), update_modified=False)
		if is_coach:
			frappe.db.set_value("Customer", customer, "restaurant_coach_discount_percent", discount, update_modified=False)
			frappe.db.set_value("Customer", customer, "restaurant_coach_commission_percent", commission, update_modified=False)
		doc.customer = customer
		doc.status = "تأییدشده"
	elif decision == "reject":
		doc.status = "ردشده"
	else:
		doc.status = "در حال بررسی"
	doc.review_note = _clean_text(note, 1000)
	doc.reviewed_by = frappe.session.user
	doc.reviewed_at = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "request": _request_row(doc)}
