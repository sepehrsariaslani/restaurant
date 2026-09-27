"""Customer self-service over native Customer, Contact and Address records."""
import base64
import hashlib
import hmac
import json
import secrets
import time

import frappe
from frappe import _

CUSTOMER_SESSION_TTL = 7 * 24 * 60 * 60


def _session_key(token):
	return "restaurant:customer-session:" + hashlib.sha256(token.encode()).hexdigest()


def _revoked_session_key(token):
	return "restaurant:customer-session-revoked:" + hashlib.sha256(token.encode()).hexdigest()


def _session_secret():
	config = getattr(frappe, "conf", {}) or {}
	try:
		secret = config.get("encryption_key")
	except AttributeError:
		secret = getattr(config, "encryption_key", None)
	return str(secret or "").strip()


def _signed_session_token(customer, mobile):
	secret = _session_secret()
	if not secret:
		return ""

	payload = {
		"customer": str(customer),
		"mobile": str(mobile or ""),
		"expires_at": int(time.time()) + CUSTOMER_SESSION_TTL,
	}
	encoded = base64.urlsafe_b64encode(
		json.dumps(payload, separators=(",", ":")).encode("utf-8")
	).decode("ascii").rstrip("=")
	signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
	return "rc1.{0}.{1}".format(encoded, signature)


def _decode_signed_session(token):
	secret = _session_secret()
	parts = str(token or "").split(".", 2)
	if not secret or len(parts) != 3 or parts[0] != "rc1":
		return None

	encoded, signature = parts[1], parts[2]
	expected = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
	if not hmac.compare_digest(signature, expected):
		return None
	try:
		padding = "=" * (-len(encoded) % 4)
		payload = json.loads(base64.urlsafe_b64decode(encoded + padding).decode("utf-8"))
		if int(payload.get("expires_at") or 0) <= int(time.time()):
			return None
		customer = str(payload.get("customer") or "").strip()
		if not customer:
			return None
		return {"customer": customer, "mobile": str(payload.get("mobile") or "")}
	except (ValueError, TypeError, json.JSONDecodeError):
		return None


def _authenticated_customer_identity():
	"""Recover a customer identity from an authenticated Frappe website session."""
	try:
		user_name = str(getattr(getattr(frappe, "session", None), "user", "") or "").strip()
		if not user_name or user_name == "Guest" or not frappe.db.exists("User", user_name):
			return None
		user = frappe.get_doc("User", user_name)
		if user.user_type != "Website User" or not user.enabled:
			return None
		customer_name = frappe.db.get_value(
			"Portal User", {"user": user_name, "parenttype": "Customer"}, "parent"
		)
		if not customer_name or not frappe.db.exists("Customer", customer_name):
			return None
		customer = frappe.get_doc("Customer", customer_name)
		if customer.disabled:
			return None
		return {
			"customer": customer_name,
			"mobile": str(user.mobile_no or customer.get("mobile_no") or ""),
		}
	except Exception:
		return None


def issue_customer_session(customer, mobile):
	token = _signed_session_token(customer, mobile) or secrets.token_urlsafe(32)
	frappe.cache().set_value(
		_session_key(token),
		{"customer": customer, "mobile": mobile},
		expires_in_sec=CUSTOMER_SESSION_TTL,
	)
	return token


def _require_customer(token):
	token = str(token or "").strip()
	cache = frappe.cache()
	if token and cache.get_value(_revoked_session_key(token)):
		frappe.throw(_("نشست حساب پایان یافته است؛ دوباره وارد شوید."), frappe.PermissionError)
	identity = cache.get_value(_session_key(token)) if token else None
	if not isinstance(identity, dict) or not identity.get("customer"):
		identity = _decode_signed_session(token) if token else None
	if not isinstance(identity, dict) or not identity.get("customer"):
		identity = _authenticated_customer_identity()
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


SIGNUP_VERIFICATION_DOCTYPE = "Restaurant Customer Signup Verification"
COACH_INVITATION_DOCTYPE = "Restaurant Coach Invitation"


def _signup_token_digest(token):
	return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def _signup_mobile(value):
	from restaurant.api import _ensure_mobile

	return _ensure_mobile(value, allow_empty=False)


def _verified_signup_customer(name, email, mobile):
	"""Link only an exact email+mobile match; never claim a Customer by phone alone."""
	from restaurant.api import _ensure_mobile

	customers = frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		fields=["name", "customer_name", "email_id", "mobile_no"],
		limit_page_length=0,
		ignore_permissions=True,
	)
	phone_matches = [row for row in customers if _ensure_mobile(row.mobile_no, allow_empty=True) == mobile]
	email_matches = [row for row in customers if str(row.email_id or "").strip().lower() == email]
	exact = [row for row in phone_matches if str(row.email_id or "").strip().lower() == email]
	if len(exact) > 1 or len(email_matches) > 1:
		frappe.throw(_("چند مشتری با این اطلاعات پیدا شد؛ پشتیبانی باید حساب‌ها را یکپارچه کند."))
	if exact:
		return frappe.get_doc("Customer", exact[0].name)
	if phone_matches or email_matches:
		frappe.throw(_("این ایمیل یا شماره به حساب دیگری متصل است. برای اتصال امن، اطلاعات مشتری را با پشتیبانی بررسی کنید."))

	customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	territory = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value("Territory", {"is_group": 0}, "name")
	if not customer_group or not territory:
		frappe.throw(_("گروه مشتری و قلمرو پیش‌فرض فروش باید تنظیم شده باشند."))
	customer_name = name
	if frappe.db.exists("Customer", customer_name):
		customer_name = "{0} ({1})".format(name[:120], mobile[-4:])
	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": customer_name,
		"customer_type": "Individual",
		"customer_group": customer_group,
		"territory": territory,
		"mobile_no": mobile,
		"email_id": email,
	}).insert(ignore_permissions=True)
	return customer


@frappe.whitelist(allow_guest=True)
def customer_register_email(name=None, email=None, mobile=None, password=None, referral_code=None):
	"""Create a disabled website login and activate it only from a verified email link."""
	if not frappe.db.exists("DocType", SIGNUP_VERIFICATION_DOCTYPE):
		frappe.throw(_("ثبت‌نام با ایمیل هنوز آماده نشده است؛ ساختار برنامه باید به‌روزرسانی شود."))
	name = str(name or "").strip()[:140]
	email = str(email or "").strip().lower()
	password = str(password or "")
	mobile = _signup_mobile(mobile)
	referral_code = "".join(str(referral_code or "").upper().split())[:40]
	if len(name) < 2:
		frappe.throw(_("نام و نام خانوادگی را وارد کنید."))
	frappe.utils.validate_email_address(email, throw=True)
	if len(password) < 8:
		frappe.throw(_("رمز عبور باید دست‌کم ۸ نویسه باشد."))
	if frappe.get_system_settings("disable_user_pass_login"):
		frappe.throw(_("ثبت‌نام با رمز عبور در این سامانه غیرفعال است."))
	from restaurant.api_club import _club_ensure_ops_ready, _club_find_referral_owner

	_club_ensure_ops_ready()
	if referral_code:
		if not _club_find_referral_owner(referral_code):
			frappe.throw(_("کد معرفی معتبر نیست."))
	cache = frappe.cache()
	guard = "restaurant:customer-signup-email:{0}".format(hashlib.sha256(email.encode()).hexdigest())
	if cache.get_value(guard):
		frappe.throw(_("درخواست تأیید برای این ایمیل همین تازگی فرستاده شده است؛ صندوق ورودی را بررسی کنید."))

	token = secrets.token_urlsafe(36)
	user_name = frappe.db.exists("User", email)
	verification = None
	if user_name:
		user = frappe.get_doc("User", user_name)
		if user.enabled or user.user_type != "Website User":
			frappe.throw(_("این ایمیل قبلاً برای حسابی ثبت شده است؛ وارد شوید یا بازیابی رمز را انجام دهید."))
		pending = frappe.get_all(
			SIGNUP_VERIFICATION_DOCTYPE,
			filters={"user": user.name, "status": ["in", ["در انتظار تأیید", "منقضی"]]},
			fields=["name"],
			limit_page_length=2,
			ignore_permissions=True,
		)
		if len(pending) != 1:
			frappe.throw(_("این ایمیل برای یک حساب دیگر رزرو شده است؛ با پشتیبانی تماس بگیرید."))
		verification = frappe.get_doc(SIGNUP_VERIFICATION_DOCTYPE, pending[0].name)
		user.first_name = name
		user.mobile_no = mobile
		user.new_password = password
		user.save(ignore_permissions=True)
		verification.update({
			"email": email,
			"mobile": mobile,
			"customer_name": name,
			"referral_code": referral_code,
			"token_hash": _signup_token_digest(token),
			"expires_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=24),
			"status": "در انتظار تأیید",
			"requested_at": frappe.utils.now_datetime(),
		})
		verification.save(ignore_permissions=True)
	else:
		user = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": name,
			"mobile_no": mobile,
			"user_type": "Website User",
			"enabled": 0,
			"send_welcome_email": 0,
			"new_password": password,
		})
		user.flags.no_welcome_mail = True
		user.insert(ignore_permissions=True)
		verification = frappe.get_doc({
			"doctype": SIGNUP_VERIFICATION_DOCTYPE,
			"user": user.name,
			"email": email,
			"mobile": mobile,
			"customer_name": name,
			"referral_code": referral_code,
			"token_hash": _signup_token_digest(token),
			"expires_at": frappe.utils.add_to_date(frappe.utils.now_datetime(), hours=24),
			"status": "در انتظار تأیید",
			"requested_at": frappe.utils.now_datetime(),
		}).insert(ignore_permissions=True)
	verify_url = frappe.utils.get_url("/customer/login?verify_email={0}".format(token))
	frappe.sendmail(
		recipients=[email],
		subject=_("تأیید ایمیل حساب مشتری"),
		message=_("<p>برای فعال‌سازی حساب {0}، پیوند زیر را باز کنید:</p><p><a href=\"{1}\">تأیید ایمیل و ورود</a></p><p>این پیوند تا ۲۴ ساعت معتبر است.</p>").format(frappe.utils.escape_html(name), verify_url),
		delayed=True,
	)
	cache.set_value(guard, 1, expires_in_sec=60)
	return {"status": "verification_sent", "email": email, "expires_in_hours": 24}


@frappe.whitelist(allow_guest=True)
def customer_verify_email(token=None):
	"""Consume one email token, attach the native Customer portal user and bind referral."""
	if not frappe.db.exists("DocType", SIGNUP_VERIFICATION_DOCTYPE):
		frappe.throw(_("ثبت‌نام با ایمیل هنوز آماده نشده است."))
	from restaurant.api_club import _club_ensure_ops_ready

	_club_ensure_ops_ready()
	digest = _signup_token_digest(token)
	verification_name = frappe.db.get_value(SIGNUP_VERIFICATION_DOCTYPE, {"token_hash": digest}, "name")
	if not verification_name:
		frappe.throw(_("پیوند تأیید معتبر نیست یا قبلاً استفاده شده است."), frappe.PermissionError)
	verification = frappe.get_doc(SIGNUP_VERIFICATION_DOCTYPE, verification_name)
	if verification.status != "در انتظار تأیید" or frappe.utils.get_datetime(verification.expires_at) < frappe.utils.now_datetime():
		if verification.status == "در انتظار تأیید":
			verification.db_set("status", "منقضی", update_modified=False)
		frappe.throw(_("پیوند تأیید منقضی شده است؛ دوباره ثبت‌نام کنید."), frappe.PermissionError)
	if not frappe.db.exists("User", verification.user):
		frappe.throw(_("حساب کاربری پیدا نشد؛ دوباره ثبت‌نام کنید."), frappe.DoesNotExistError)
	user = frappe.get_doc("User", verification.user)
	if user.user_type != "Website User" or user.enabled:
		frappe.throw(_("این درخواست ثبت‌نام دیگر قابل استفاده نیست."), frappe.PermissionError)
	customer = _verified_signup_customer(verification.customer_name, verification.email, _signup_mobile(verification.mobile))
	portal_user = frappe.db.exists("Portal User", {"parent": customer.name, "user": user.name, "parenttype": "Customer"})
	if not portal_user:
		customer.append("portal_users", {"user": user.name})
		customer.save(ignore_permissions=True)
	user.enabled = 1
	user.save(ignore_permissions=True)
	frappe.db.set_value(SIGNUP_VERIFICATION_DOCTYPE, verification.name, {
		"customer": customer.name,
		"status": "تأییدشده",
		"verified_at": frappe.utils.now_datetime(),
	}, update_modified=False)
	customer_token = issue_customer_session(customer.name, verification.mobile)
	referral_code = verification.referral_code
	if not referral_code and frappe.db.exists("DocType", COACH_INVITATION_DOCTYPE):
		from restaurant.api import _ensure_mobile
		pending = frappe.get_all(
			COACH_INVITATION_DOCTYPE,
			filters={"status": "در انتظار ثبت‌نام", "email": verification.email},
			fields=["name", "coach", "mobile", "email"],
			limit_page_length=0,
			ignore_permissions=True,
		)
		matches = [row for row in pending if _ensure_mobile(row.mobile, allow_empty=True) == _ensure_mobile(verification.mobile, allow_empty=True)]
		if len(matches) == 1:
			from restaurant.api_club import _club_assign_referral_code, bind_my_referral_code

			referral_code = _club_assign_referral_code(matches[0].coach)
			bind_my_referral_code(customer_token=customer_token, referral_code=referral_code)
			frappe.db.set_value(COACH_INVITATION_DOCTYPE, matches[0].name, {
				"status": "ثبت‌نام و اتصال‌شده",
				"customer": customer.name,
				"claimed_at": frappe.utils.now_datetime(),
			}, update_modified=False)
	elif referral_code:
		from restaurant.api_club import _club_find_referral_owner, bind_my_referral_code

		binding = bind_my_referral_code(customer_token=customer_token, referral_code=referral_code)
		coach = _club_find_referral_owner(referral_code)
		if binding.get("relation") == "coach" and coach and frappe.db.exists("DocType", COACH_INVITATION_DOCTYPE):
			from restaurant.api import _ensure_mobile

			pending = frappe.get_all(
				COACH_INVITATION_DOCTYPE,
				filters={"coach": coach, "status": "در انتظار ثبت‌نام", "email": verification.email},
				fields=["name", "mobile"],
				limit_page_length=0,
				ignore_permissions=True,
			)
			for invite in pending:
				if _ensure_mobile(invite.mobile, allow_empty=True) == _ensure_mobile(verification.mobile, allow_empty=True):
					frappe.db.set_value(COACH_INVITATION_DOCTYPE, invite.name, {
						"status": "ثبت‌نام و اتصال‌شده",
						"customer": customer.name,
						"claimed_at": frappe.utils.now_datetime(),
					}, update_modified=False)
	frappe.db.commit()
	return _customer_password_result(customer, verification.mobile, verification.email, token=customer_token)


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
def customer_register_password(customer_token=None, name=None, email=None, password=None, referral_code=None):
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

	if referral_code:
		from restaurant.api_club import bind_my_coach_invite

		bind_my_coach_invite(customer_token=customer_token, referral_code=referral_code)
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
	token_is_valid = bool(
		customer_token
		and (
			_decode_signed_session(customer_token)
			or frappe.cache().get_value(_session_key(str(customer_token)))
		)
	)
	return _customer_password_result(
		customer,
		identity.get("mobile") or "",
		customer.email_id or "",
		token=customer_token if token_is_valid else None,
	)


@frappe.whitelist(allow_guest=True)
def customer_logout(customer_token=None):
	if customer_token:
		cache = frappe.cache()
		cache.set_value(_revoked_session_key(str(customer_token)), 1, expires_in_sec=CUSTOMER_SESSION_TTL)
		cache.delete_value(_session_key(str(customer_token)))
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
