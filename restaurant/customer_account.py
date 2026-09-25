"""Customer self-service over native Customer, Contact and Address records."""
import hashlib
import secrets

import frappe
from frappe import _


def _session_key(token):
	return "restaurant:customer-session:" + hashlib.sha256(token.encode()).hexdigest()


def issue_customer_session(customer, mobile):
	token = secrets.token_urlsafe(32)
	frappe.cache().set_value(_session_key(token), {"customer": customer, "mobile": mobile}, expires_in_sec=7 * 24 * 60 * 60)
	return token


def _require_customer(token):
	identity = frappe.cache().get_value(_session_key(str(token or ""))) if token else None
	if not isinstance(identity, dict) or not identity.get("customer"):
		frappe.throw(_("برای ویرایش حساب، دوباره با شماره موبایل وارد شوید."), frappe.PermissionError)
	if not frappe.db.exists("Customer", identity["customer"]):
		frappe.throw(_("حساب مشتری پیدا نشد؛ دوباره وارد شوید."), frappe.PermissionError)
	return identity


@frappe.whitelist(allow_guest=True)
def save_profile(customer_token=None, name=None, email=None):
	identity = _require_customer(customer_token)
	name = str(name or "").strip()
	email = str(email or "").strip()
	if not name:
		frappe.throw(_("نام و نام خانوادگی را وارد کنید."))
	if email:
		frappe.utils.validate_email_address(email, throw=True)
	customer = frappe.get_doc("Customer", identity["customer"])
	contact_name = customer.get("customer_primary_contact")
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		if not any(row.link_doctype == "Customer" and row.link_name == customer.name for row in contact.get("links", [])):
			frappe.throw(_("اطلاعات تماس به این حساب متصل نیست."), frappe.PermissionError)
	else:
		contact = frappe.get_doc({"doctype": "Contact", "first_name": name, "links": [{"link_doctype": "Customer", "link_name": customer.name}]})
		contact.append("phone_nos", {"phone": identity["mobile"], "is_primary_mobile_no": 1})
	contact.first_name = name
	contact.last_name = ""
	# Keep secondary addresses; update only the primary email owned by this contact.
	primary = next((row for row in contact.get("email_ids", []) if row.is_primary), None)
	if primary and email:
		primary.email_id = email
	elif primary:
		contact.remove(primary)
	elif email:
		contact.append("email_ids", {"email_id": email, "is_primary": 1})
	contact.save(ignore_permissions=True)
	customer.customer_name = name
	customer.customer_primary_contact = contact.name
	customer.email_id = contact.email_id
	customer.save(ignore_permissions=True)
	return {"customer": {"name": customer.customer_name, "mobile": identity["mobile"], "email": contact.email_id or "", "customer_id": customer.name}}


@frappe.whitelist(allow_guest=True)
def archive_address(customer_token=None, address_id=None):
	identity = _require_customer(customer_token)
	doc = frappe.get_doc("Address", address_id)
	if not any(row.link_doctype == "Customer" and row.link_name == identity["customer"] for row in doc.get("links", [])):
		frappe.throw(_("این آدرس متعلق به حساب شما نیست."), frappe.PermissionError)
	doc.disabled = 1
	doc.save(ignore_permissions=True)
	return {"success": True}
