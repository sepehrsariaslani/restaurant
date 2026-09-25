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


def _customer_password_user(customer):
	return [str(row.get("user") or "").strip() for row in customer.get("portal_users", []) if row.get("user")]


def _customer_password_result(customer, mobile, email="", token=None):
	return {
		"success": True,
		"customer_token": token or issue_customer_session(customer.name, mobile),
		"customer": {
			"customer_id": customer.name,
			"name": customer.customer_name or "",
			"mobile": mobile,
			"email": email or "",
		},
	}


@frappe.whitelist(allow_guest=True)
def customer_login_password(identifier=None, password=None, mobile=None):
	"""Authenticate a website customer by their verified email or mobile number."""
	identifier = str(identifier or mobile or "").strip()
	password = str(password or "")
	if not identifier or not password:
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور را وارد کنید."), frappe.AuthenticationError)
	if frappe.get_system_settings("disable_user_pass_login"):
		frappe.throw(_("ورود با رمز عبور در این سامانه غیرفعال است؛ از ورود پیامکی استفاده کنید."), frappe.AuthenticationError)

	from restaurant.api import _ensure_mobile

	if "@" in identifier:
		user_name = identifier.lower()
	else:
		normalized_mobile = _ensure_mobile(identifier, allow_empty=True)
		if not normalized_mobile:
			frappe.throw(_("شماره همراه یا رمز عبور نادرست است."), frappe.AuthenticationError)
		users = frappe.get_all(
			"User",
			filters={"mobile_no": normalized_mobile, "user_type": "Website User"},
			fields=["name"],
			limit_page_length=2,
			ignore_permissions=True,
		)
		if len(users) != 1:
			frappe.throw(_("شماره همراه یا رمز عبور نادرست است."), frappe.AuthenticationError)
		user_name = users[0].name

	if not frappe.db.exists("User", user_name):
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور نادرست است."), frappe.AuthenticationError)
	user = frappe.get_doc("User", user_name)
	if user.user_type != "Website User" or not user.enabled:
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور نادرست است."), frappe.AuthenticationError)

	customer_name = frappe.db.get_value(
		"Portal User", {"user": user.name, "parenttype": "Customer"}, "parent"
	)
	if not customer_name or not frappe.db.exists("Customer", customer_name):
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور نادرست است."), frappe.AuthenticationError)
	customer = frappe.get_doc("Customer", customer_name)
	if customer.disabled:
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور نادرست است."), frappe.AuthenticationError)

	try:
		from frappe.auth import LoginManager, validate_ip_address

		login_manager = LoginManager()
		login_manager.authenticate(user=user.name, pwd=password)
	except frappe.AuthenticationError:
		frappe.throw(_("ایمیل یا شماره همراه و رمز عبور نادرست است."), frappe.AuthenticationError)

	from frappe.twofactor import should_run_2fa

	if should_run_2fa(user.name):
		frappe.throw(_("برای این حساب، ورود پیامکی را انتخاب کنید."), frappe.AuthenticationError)
	if login_manager.force_user_to_reset_password():
		frappe.throw(_("رمز عبور این حساب نیاز به بازنشانی دارد؛ از ورود پیامکی استفاده کنید."), frappe.AuthenticationError)
	validate_ip_address(user.name)
	login_manager.validate_hour()

	normalized_mobile = _ensure_mobile(user.mobile_no or customer.mobile_no, allow_empty=True)
	if not normalized_mobile:
		frappe.throw(_("برای حساب مشتری شماره همراه ثبت نشده است."), frappe.AuthenticationError)
	return _customer_password_result(customer, normalized_mobile, user.email or "")


@frappe.whitelist(allow_guest=True)
def customer_register_password(customer_token=None, name=None, email=None, password=None):
	"""Create or update a native website account after mobile OTP verification."""
	identity = _require_customer(customer_token)
	from restaurant.api import _ensure_mobile

	mobile = _ensure_mobile(identity.get("mobile"), allow_empty=False)
	password = str(password or "")
	if len(password) < 8:
		frappe.throw(_("رمز عبور باید دست‌کم ۸ نویسه باشد."))
	name = str(name or "").strip()
	email = str(email or "").strip().lower()
	if email:
		frappe.utils.validate_email_address(email, throw=True)

	customer = frappe.get_doc("Customer", identity["customer"])
	if customer.disabled:
		frappe.throw(_("حساب مشتری غیرفعال است."), frappe.PermissionError)
	linked_users = _customer_password_user(customer)
	if len(linked_users) > 1:
		frappe.throw(_("برای این حساب بیش از یک کاربر متصل است؛ با پشتیبانی تماس بگیرید."))

	user = frappe.get_doc("User", linked_users[0]) if linked_users else None
	if user:
		if user.user_type != "Website User" or not user.enabled:
			frappe.throw(_("حساب مشتری برای ساخت رمز عبور در دسترس نیست."), frappe.PermissionError)
		if email and user.name.lower() != email:
			frappe.throw(_("این حساب با ایمیل دیگری ثبت شده است؛ با شماره همراه وارد شوید."))
		resolved_email = user.email or ""
	else:
		matching_users = frappe.get_all(
			"User",
			filters={"mobile_no": mobile},
			fields=["name"],
			limit_page_length=1,
			ignore_permissions=True,
		)
		resolved_email = email or str(customer.email_id or "").strip().lower()
		if matching_users:
			frappe.throw(_("برای این شماره حساب دیگری ثبت شده است؛ ابتدا با کد یک‌بارمصرف وارد شوید."))
		if not resolved_email:
			resolved_email = "customer-{0}@login.invalid".format(mobile)
		if frappe.db.exists("User", resolved_email):
			frappe.throw(_("این ایمیل قبلاً برای حساب دیگری ثبت شده است."))

	profile_email = email or customer.email_id or ""
	if name or profile_email:
		save_profile(customer_token=customer_token, name=name or customer.customer_name, email=profile_email)
		customer = frappe.get_doc("Customer", identity["customer"])

	if user:
		user.new_password = password
		user.save(ignore_permissions=True)
	else:
		user = frappe.get_doc({
			"doctype": "User",
			"email": resolved_email,
			"first_name": name or customer.customer_name or mobile,
			"mobile_no": mobile,
			"user_type": "Website User",
			"enabled": 1,
			"send_welcome_email": 0,
			"new_password": password,
		})
		user.flags.no_welcome_mail = True
		user.insert(ignore_permissions=True)
		customer.append("portal_users", {"user": user.name})
		customer.save(ignore_permissions=True)

	return _customer_password_result(customer, mobile, email or customer.email_id or "", token=customer_token)


@frappe.whitelist(allow_guest=True)
def customer_session(customer_token=None):
	identity = _require_customer(customer_token)
	customer = frappe.get_doc("Customer", identity["customer"])
	return _customer_password_result(customer, identity.get("mobile") or "", customer.email_id or "", token=customer_token)


@frappe.whitelist(allow_guest=True)
def customer_logout(customer_token=None):
	if customer_token:
		frappe.cache().delete_value(_session_key(str(customer_token)))
	return {"success": True}


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
