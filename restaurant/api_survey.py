"""Verified, per-order customer surveys and product-review moderation."""

import hashlib
import json
import secrets
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, now_datetime

from restaurant import api_club

INVITATION = "Restaurant Survey Invitation"
QUESTION = "Restaurant Survey Question"
RESPONSE = "Restaurant Survey Response"
REVIEW = "Restaurant Customer Review"
QUESTION_TYPES = ("امتیاز ۱ تا ۱۰", "بله/خیر", "متن آزاد", "ویژگی خوب/بد")
QUESTION_SCOPES = ("سفارش", "گروه غذا", "محصول")
REVIEW_STATES = ("در انتظار بررسی", "تأییدشده", "ردشده")

__all__ = [
	"queue_order_survey_invitation", "queue_table_order_survey_invitation", "run_due_survey_invitations",
	"get_public_survey", "get_my_order_survey", "get_my_survey_invitations", "submit_public_survey",
	"get_my_order_survey_summaries", "request_my_order_survey",
	"list_my_customer_reviews", "list_management_survey_questions", "save_management_survey_question",
	"delete_management_survey_question", "list_management_survey_responses", "list_management_survey_invitations",
	"list_management_survey_targets",
	"retry_management_survey_invitation", "list_management_customer_reviews", "review_management_customer_review",
]


def _order_key(doctype, name):
	return f"{doctype}:{name}"


def _redact_survey_url(message, url=""):
	return str(message or "").replace(str(url), "[پیوند امن نظرسنجی]") if url else str(message or "")


def _customer_for_mobile(mobile):
	try:
		from restaurant.api import _find_customer_by_mobile
		return _find_customer_by_mobile(mobile) or ""
	except Exception:
		return ""


def _valid_mobile(value):
	try:
		from restaurant.api import _ensure_mobile
		mobile = _ensure_mobile(value, allow_empty=True)
		return mobile if len(mobile) >= 10 else ""
	except Exception:
		return ""


def _read_order_identity(doctype, name):
	if doctype == "Sales Order":
		if not frappe.db.exists(doctype, name):
			return None
		order = frappe.get_doc(doctype, name)
		if cint(order.docstatus) != 1 or (order.get("restaurant_status") or "").strip().lower() not in ("delivered", "served"):
			return None
		customer = order.customer or ""
		mobile = _valid_mobile(order.get("restaurant_customer_mobile") or api_club._club_customer_mobile(customer))
		return {
			"customer": customer, "customer_name": order.customer_name or (frappe.db.get_value("Customer", customer, "customer_name") if customer else ""),
			"mobile": mobile, "order_code": order.name,
		}
	if doctype == "Restaurant Table Order":
		if not frappe.db.exists(doctype, name):
			return None
		order = frappe.get_doc(doctype, name)
		if (order.status or "").strip().lower() != "paid":
			return None
		from restaurant.api import _extract_table_session_meta
		meta = _extract_table_session_meta(frappe.db.get_value("Restaurant Table Session", order.session, "note") or "")
		mobile = _valid_mobile(meta.get("customer_mobile"))
		customer = _customer_for_mobile(mobile)
		return {"customer": customer, "customer_name": meta.get("customer_name") or (frappe.db.get_value("Customer", customer, "customer_name") if customer else ""), "mobile": mobile, "order_code": order.order_code or order.name}
	return None


def _queue_invitation(doctype, name):
	if not frappe.db.exists("DocType", INVITATION):
		return None
	key = _order_key(doctype, name)
	existing = frappe.db.get_value(INVITATION, {"order_key": key}, "name")
	if existing:
		return frappe.get_doc(INVITATION, existing)
	identity = _read_order_identity(doctype, name)
	if not identity or not identity.get("mobile"):
		return None
	delay = api_club._club_club_settings()["survey_delay_minutes"]
	now = now_datetime()
	doc = frappe.new_doc(INVITATION)
	doc.order_key = key
	doc.reference_doctype = doctype
	doc.reference_name = name
	doc.sales_order = name if doctype == "Sales Order" else None
	doc.table_order = name if doctype == "Restaurant Table Order" else None
	doc.customer = identity.get("customer") or None
	doc.customer_name = identity.get("customer_name") or ""
	doc.mobile = identity["mobile"]
	doc.order_code = identity["order_code"]
	doc.due_at = now + timedelta(minutes=delay)
	doc.expires_at = now + timedelta(days=30)
	doc.status = "در انتظار ارسال"
	doc.insert(ignore_permissions=True)
	return doc


def queue_order_survey_invitation(order_name):
	try:
		return _queue_invitation("Sales Order", order_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant survey invitation queue failed")
		return None


def queue_table_order_survey_invitation(order_name):
	try:
		return _queue_invitation("Restaurant Table Order", order_name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant table survey invitation queue failed")
		return None


def _item_payload(row_name, item_code, title, qty):
	fields = ["name", "item_name", "item_group", "image"]
	if api_club._has_column("Item", "restaurant_slug"):
		fields.append("restaurant_slug")
	if api_club._has_column("Item", "restaurant_category"):
		fields.append("restaurant_category")
	item = frappe.db.get_value("Item", item_code, fields, as_dict=True) or {}
	return {
		"order_item": row_name, "item": item_code, "title": title or item.get("item_name") or item_code,
		"qty": flt(qty), "image": item.get("image") or "", "item_slug": item.get("restaurant_slug") or "",
		"item_group": item.get("item_group") or "",
	}


def _load_order(invitation):
	items = []
	if invitation.reference_doctype == "Sales Order":
		if not frappe.db.exists("Sales Order", invitation.reference_name):
			return None
		order = frappe.get_doc("Sales Order", invitation.reference_name)
		if cint(order.docstatus) != 1 or (order.get("restaurant_status") or "").strip().lower() not in ("delivered", "served"):
			return None
		for row in order.items or []:
			if cint(row.get("restaurant_is_auto_added")) or not frappe.db.exists("Item", row.item_code):
				continue
			items.append(_item_payload(row.name, row.item_code, row.item_name, row.qty))
	elif invitation.reference_doctype == "Restaurant Table Order":
		if not frappe.db.exists("Restaurant Table Order", invitation.reference_name):
			return None
		order = frappe.get_doc("Restaurant Table Order", invitation.reference_name)
		if (order.status or "").strip().lower() != "paid":
			return None
		for row in order.items or []:
			if not row.menu_item or not frappe.db.exists("Item", row.menu_item):
				continue
			title = frappe.db.get_value("Item", row.menu_item, "item_name") or row.menu_item
			items.append(_item_payload(row.name, row.menu_item, title, row.quantity))
	else:
		return None
	return {"order_code": invitation.order_code or invitation.reference_name, "customer_name": invitation.customer_name or "", "items": items}


def _questions_for(items):
	questions = frappe.get_all(QUESTION, filters={"is_active": 1}, fields=["name", "question", "answer_type", "scope", "target_item_group", "target_item", "sort_order"], order_by="sort_order asc, creation asc", limit_page_length=200)
	order_questions = [q for q in questions if (q.get("scope") or "سفارش") == "سفارش"]
	for item in items:
		item["questions"] = [q for q in questions if ((q.get("scope") == "گروه غذا" and q.get("target_item_group") == item.get("item_group")) or (q.get("scope") == "محصول" and q.get("target_item") == item.get("item")))]
	return order_questions, items


def _invitation_by_token(token):
	if not token or not frappe.db.exists("DocType", INVITATION):
		return None
	digest = hashlib.sha256(str(token).strip().encode("utf-8")).hexdigest()
	name = frappe.db.get_value(INVITATION, {"token_hash": digest}, "name")
	return frappe.get_doc(INVITATION, name) if name else None


def _owned_invitation(name, customer_token):
	from restaurant.api import _customer_session_identity
	identity = _customer_session_identity(customer_token, required=True)
	invitation = frappe.get_doc(INVITATION, name)
	if invitation.customer and invitation.customer == identity.get("customer"):
		return invitation
	if _valid_mobile(invitation.mobile) and _valid_mobile(identity.get("mobile")) == _valid_mobile(invitation.mobile):
		return invitation
	frappe.throw(_("این دعوت متعلق به حساب شما نیست."), frappe.PermissionError)


def _survey_context(invitation, include_saved_answers=False):
	answered = bool(invitation.submitted_at or invitation.status == "تکمیل‌شده")
	if answered and not include_saved_answers:
		return {"valid": 1, "answered": 1, "order_code": invitation.order_code}
	if not answered and invitation.expires_at and get_datetime(invitation.expires_at) < now_datetime():
		return {"valid": 0, "expired": 1, "message": _("مهلت ثبت این نظرسنجی به پایان رسیده است.")}
	if not answered and invitation.due_at and get_datetime(invitation.due_at) > now_datetime():
		return {"valid": 0, "message": _("این نظرسنجی هنوز فعال نشده است.")}
	order = _load_order(invitation)
	if not order:
		return {"valid": 0, "message": _("این سفارش برای ثبت نظرسنجی در دسترس نیست.")}
	order_questions, items = _questions_for(order["items"])
	result = {"valid": 1, "answered": int(answered), "invitation": invitation.name, "order_code": order["order_code"], "customer_name": order["customer_name"], "items": items, "order_questions": order_questions}
	if answered and include_saved_answers:
		response = frappe.db.get_value(RESPONSE, {"source_key": invitation.order_key}, ["service_rating", "comment", "answers_json"], as_dict=True) or {}
		try:
			result["answers"] = json.loads(response.get("answers_json") or "[]")
		except Exception:
			result["answers"] = []
		result["service_rating"] = cint(response.get("service_rating") or 0)
		result["comment"] = response.get("comment") or ""
		reviews = frappe.get_all(REVIEW, filters={"invitation": invitation.name}, fields=["order_item", "score_10", "rating", "comment", "strengths_json", "weaknesses_json", "moderation_status", "manager_reply"], limit_page_length=300, ignore_permissions=True)
		by_line = {row.order_item: row for row in reviews}
		for item in items:
			row = by_line.get(item["order_item"])
			if not row:
				continue
			try:
				strengths = json.loads(row.get("strengths_json") or "[]")
			except Exception:
				strengths = []
			try:
				weaknesses = json.loads(row.get("weaknesses_json") or "[]")
			except Exception:
				weaknesses = []
			item["saved_review"] = {
				"score_10": cint(row.get("score_10") or flt(row.get("rating") or 0) * 2),
				"comment": row.get("comment") or "", "strengths": strengths, "weaknesses": weaknesses,
				"moderation_status": row.get("moderation_status") or "در انتظار بررسی", "manager_reply": row.get("manager_reply") or "",
			}
		result["editing"] = 1
	return result


@frappe.whitelist(allow_guest=True)
def get_public_survey(token=""):
	invitation = _invitation_by_token(token)
	if not invitation:
		return {"valid": 0, "message": _("پیوند نظرسنجی معتبر نیست.")}
	return _survey_context(invitation)


@frappe.whitelist(allow_guest=True)
def get_my_order_survey(invitation_name="", customer_token=None, edit=0):
	if not invitation_name or not frappe.db.exists(INVITATION, invitation_name):
		return {"valid": 0, "message": _("دعوت نظرسنجی پیدا نشد.")}
	invitation = _owned_invitation(invitation_name, customer_token)
	if cint(edit) and not (invitation.submitted_at or invitation.status == "تکمیل‌شده"):
		return {"valid": 0, "message": _("این نظرسنجی هنوز ثبت نشده و قابل ویرایش نیست.")}
	return _survey_context(invitation, include_saved_answers=bool(cint(edit)))


def _order_owned_by_identity(order_identity, identity):
	if not order_identity or not identity:
		return False
	if order_identity.get("customer") and order_identity.get("customer") == identity.get("customer"):
		return True
	return bool(_valid_mobile(order_identity.get("mobile")) and _valid_mobile(order_identity.get("mobile")) == _valid_mobile(identity.get("mobile")))


def _sales_order_owner_identity(name):
	if not frappe.db.exists("Sales Order", name):
		return None
	order = frappe.get_doc("Sales Order", name)
	customer = order.customer or ""
	return {
		"customer": customer,
		"customer_name": order.customer_name or (frappe.db.get_value("Customer", customer, "customer_name") if customer else ""),
		"mobile": _valid_mobile(order.get("restaurant_customer_mobile") or api_club._club_customer_mobile(customer)),
	}


def _customer_order_survey_summary(sales_order, invitation=None):
	if not invitation:
		return {"answered": 0, "can_request": 1, "reviews": []}
	answered = bool(invitation.get("submitted_at") or invitation.get("status") == "تکمیل‌شده")
	response = frappe.db.get_value(RESPONSE, {"source_key": _order_key("Sales Order", sales_order)}, ["overall_rating", "service_rating", "comment", "entry_date"], as_dict=True) or {}
	review_rows = frappe.get_all(REVIEW, filters={"invitation": invitation.name}, fields=["name", "order_item", "item", "score_10", "rating", "comment", "strengths_json", "weaknesses_json", "moderation_status", "manager_reply", "replied_at"], order_by="creation asc", limit_page_length=100, ignore_permissions=True)
	reviews = []
	for row in review_rows:
		item = frappe.db.get_value("Item", row.item, ["item_name", "image"], as_dict=True) if row.item else {}
		try:
			strengths = json.loads(row.get("strengths_json") or "[]")
		except Exception:
			strengths = []
		try:
			weaknesses = json.loads(row.get("weaknesses_json") or "[]")
		except Exception:
			weaknesses = []
		reviews.append({
			"name": row.name, "order_item": row.order_item, "item": row.item,
			"item_title": (item or {}).get("item_name") or row.item or "غذا",
			"image": (item or {}).get("image") or "", "score_10": cint(row.get("score_10") or flt(row.get("rating") or 0) * 2),
			"comment": row.get("comment") or "", "strengths": strengths, "weaknesses": weaknesses,
			"moderation_status": row.get("moderation_status") or "در انتظار بررسی",
			"manager_reply": row.get("manager_reply") or "", "replied_at": str(row.get("replied_at") or ""),
		})
	return {
		"invitation": invitation.name, "answered": int(answered),
		"can_request": int(not answered), "can_edit": int(answered),
		"status": invitation.get("status") or "", "submitted_at": str(invitation.get("submitted_at") or ""),
		"overall_rating": cint(response.get("overall_rating") or 0), "service_rating": cint(response.get("service_rating") or 0),
		"comment": response.get("comment") or "", "entry_date": str(response.get("entry_date") or ""),
		"reviews": reviews,
	}


@frappe.whitelist(allow_guest=True)
def get_my_order_survey_summaries(order_names=None, customer_token=None):
	"""Return review status only for completed orders owned by the signed-in account."""
	from restaurant.api import _customer_session_identity
	identity = _customer_session_identity(customer_token, required=True)
	if isinstance(order_names, str):
		order_names = api_club._club_parse_json(order_names, [])
	if not isinstance(order_names, list):
		frappe.throw(_("سفارش‌های درخواستی معتبر نیستند."))
	names = list(dict.fromkeys(str(name or "").strip() for name in order_names if str(name or "").strip()))[:100]
	for name in names:
		if not _order_owned_by_identity(_sales_order_owner_identity(name), identity):
			frappe.throw(_("یکی از سفارش‌ها متعلق به حساب شما نیست."), frappe.PermissionError)
	if not names or not frappe.db.exists("DocType", INVITATION):
		return {"summaries": {}}
	invitations = frappe.get_all(INVITATION, filters={"sales_order": ["in", names]}, fields=["name", "sales_order", "status", "submitted_at", "due_at", "expires_at"], limit_page_length=100, ignore_permissions=True)
	by_order = {row.sales_order: row for row in invitations}
	summaries = {}
	for name in names:
		if not _read_order_identity("Sales Order", name):
			summaries[name] = {"answered": 0, "can_request": 0, "reviews": []}
		else:
			summaries[name] = _customer_order_survey_summary(name, by_order.get(name))
	return {"summaries": summaries}


@frappe.whitelist(allow_guest=True)
def request_my_order_survey(order_name="", customer_token=None):
	"""Activate an account-only survey after an explicit customer request; never queue SMS."""
	from restaurant.api import _customer_session_identity
	identity = _customer_session_identity(customer_token, required=True)
	order_name = str(order_name or "").strip()
	order_identity = _read_order_identity("Sales Order", order_name)
	if not _order_owned_by_identity(order_identity, identity):
		frappe.throw(_("سفارش تکمیل‌شده‌ای با این شناسه برای حساب شما پیدا نشد."), frappe.PermissionError)
	invitation = _queue_invitation("Sales Order", order_name)
	if not invitation:
		frappe.throw(_("برای این سفارش امکان ثبت نظر وجود ندارد."))
	if invitation.submitted_at or invitation.status == "تکمیل‌شده":
		return {"status": "answered", "invitation": invitation.name, "href": f"/survey?invitation={invitation.name}&edit=1"}
	now = now_datetime()
	invitation.due_at = now
	invitation.expires_at = now + timedelta(days=30)
	invitation.status = "بدون درگاه"
	invitation.token_hash = ""
	invitation.last_error = ""
	invitation.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "ready", "invitation": invitation.name, "href": f"/survey?invitation={invitation.name}"}


@frappe.whitelist(allow_guest=True)
def get_my_survey_invitations(customer_token=None):
	from restaurant.api import _customer_session_identity
	identity = _customer_session_identity(customer_token, required=True)
	customer, mobile = identity.get("customer") or "", _valid_mobile(identity.get("mobile"))
	rows = frappe.get_all(INVITATION, filters={"submitted_at": ["is", "not set"], "expires_at": [">=", now_datetime()]}, fields=["name", "customer", "mobile", "order_code", "due_at", "status", "expires_at"], order_by="creation desc", limit_page_length=100, ignore_permissions=True)
	out = []
	for row in rows:
		if row.customer != customer and (not mobile or _valid_mobile(row.mobile) != mobile):
			continue
		if get_datetime(row.due_at) > now_datetime():
			continue
		out.append({**row, "href": f"/survey?invitation={row.name}"})
	return {"invitations": out, "count": len(out)}


def _validate_answers(payload, order_items):
	questions = {q.name: q for q in frappe.get_all(QUESTION, filters={"is_active": 1}, fields=["name", "question", "answer_type", "scope", "target_item_group", "target_item"], limit_page_length=200)}
	items = {x["order_item"]: x for x in order_items}
	answers = payload.get("answers") or []
	if not isinstance(answers, list):
		frappe.throw(_("پاسخ پرسش‌ها نامعتبر است."))
	validated = []
	seen = set()
	for answer in answers:
		if not isinstance(answer, dict):
			continue
		question = questions.get(str(answer.get("question") or ""))
		if not question:
			frappe.throw(_("یکی از پرسش‌ها دیگر فعال نیست؛ صفحه را تازه‌سازی کنید."))
		row_key = str(answer.get("order_item") or "")
		answer_key = (question.name, row_key)
		if answer_key in seen:
			frappe.throw(_("برای هر پرسش فقط یک پاسخ ارسال کنید."))
		seen.add(answer_key)
		scope = question.get("scope") or "سفارش"
		if scope == "سفارش" and row_key:
			frappe.throw(_("پرسش عمومی سفارش به غذا متصل نیست."), frappe.PermissionError)
		if scope != "سفارش":
			if row_key not in items:
				frappe.throw(_("پاسخ به محصولی خارج از سفارش ارسال شده است."), frappe.PermissionError)
			line = items[row_key]
			if scope == "محصول" and question.target_item != line["item"]:
				frappe.throw(_("این پرسش برای محصول انتخاب‌شده نیست."), frappe.PermissionError)
			if scope == "گروه غذا" and question.target_item_group != line["item_group"]:
				frappe.throw(_("این پرسش برای گروه انتخاب‌شده نیست."), frappe.PermissionError)
		value, kind = answer.get("value"), question.answer_type
		if kind == "امتیاز ۱ تا ۱۰":
			value = cint(value)
			if not 1 <= value <= 10:
				frappe.throw(_("امتیاز باید بین ۱ تا ۱۰ باشد."))
		elif kind == "بله/خیر":
			if value not in ("بله", "خیر"):
				frappe.throw(_("پاسخ بله/خیر نامعتبر است."))
		elif kind == "ویژگی خوب/بد":
			if value not in ("نقطه قوت", "نیاز به بهبود"):
				frappe.throw(_("انتخاب ویژگی نامعتبر است."))
		else:
			value = str(value or "").strip()[:500]
			if not value:
				continue
		validated.append({"question": question.question, "question_id": question.name, "answer_type": kind, "order_item": row_key, "value": value})
	return validated


@frappe.whitelist(allow_guest=True)
def submit_public_survey(payload=None):
	payload = api_club._club_parse_json(payload, {}) if isinstance(payload, str) else api_club._club_parse_payload(payload)
	token, invite_name = str(payload.get("token") or "").strip(), str(payload.get("invitation") or "").strip()
	is_edit = bool(cint(payload.get("edit")))
	if token:
		if is_edit:
			frappe.throw(_("ویرایش نظر فقط از حساب مشتری انجام می‌شود."), frappe.PermissionError)
		invitation = _invitation_by_token(token)
		if not invitation:
			frappe.throw(_("پیوند نظرسنجی معتبر نیست."), frappe.PermissionError)
	elif invite_name:
		invitation = _owned_invitation(invite_name, payload.get("customer_token"))
	else:
		frappe.throw(_("دعوت معتبر نظرسنجی لازم است."), frappe.PermissionError)
	was_submitted = bool(invitation.submitted_at or invitation.status == "تکمیل‌شده")
	if was_submitted and not is_edit:
		frappe.throw(_("برای این سفارش قبلاً نظرسنجی ثبت شده است."))
	if is_edit and not was_submitted:
		frappe.throw(_("این نظرسنجی هنوز ثبت نشده است و قابل ویرایش نیست."), frappe.PermissionError)
	if not is_edit and invitation.due_at and get_datetime(invitation.due_at) > now_datetime():
		frappe.throw(_("زمان ثبت این نظرسنجی هنوز نرسیده است."), frappe.PermissionError)
	if not is_edit and invitation.expires_at and get_datetime(invitation.expires_at) < now_datetime():
		frappe.throw(_("مهلت ثبت این نظرسنجی به پایان رسیده است."))
	order = _load_order(invitation)
	if not order:
		frappe.throw(_("وضعیت سفارش اجازه ثبت نظر نمی‌دهد."))
	response_name = frappe.db.get_value(RESPONSE, {"source_key": invitation.order_key}, "name")
	if is_edit and not response_name:
		frappe.throw(_("پاسخ قبلی برای ویرایش پیدا نشد."))
	if not is_edit and response_name:
		frappe.throw(_("برای این سفارش قبلاً نظرسنجی ثبت شده است."))
	existing_reviews = frappe.get_all(REVIEW, filters={"invitation": invitation.name}, fields=["name", "order_item"], limit_page_length=300, ignore_permissions=True) if is_edit else []
	item_by_row = {x["order_item"]: x for x in order["items"]}
	answers = _validate_answers(payload, order["items"])
	review_inputs = payload.get("items") or []
	if not isinstance(review_inputs, list):
		frappe.throw(_("امتیاز غذاها نامعتبر است."))
	seen, reviews = set(), []
	for value in review_inputs:
		if not isinstance(value, dict):
			continue
		row_key = str(value.get("order_item") or "")
		if row_key not in item_by_row or row_key in seen:
			frappe.throw(_("غذای خارج از سفارش یا تکراری ارسال شده است."), frappe.PermissionError)
		seen.add(row_key)
		score = cint(value.get("score_10"))
		if not 1 <= score <= 10:
			frappe.throw(_("امتیاز هر غذا باید بین ۱ تا ۱۰ باشد."))
		strengths = value.get("strengths") if isinstance(value.get("strengths"), list) else []
		weaknesses = value.get("weaknesses") if isinstance(value.get("weaknesses"), list) else []
		reviews.append({"line": item_by_row[row_key], "score": score, "comment": str(value.get("comment") or "").strip()[:2000], "strengths": [str(x)[:120] for x in strengths[:20]], "weaknesses": [str(x)[:120] for x in weaknesses[:20]]})
	if is_edit and any(row.order_item not in seen for row in existing_reviews):
		frappe.throw(_("برای حفظ نظرهای قبلی، امتیاز غذاهایی را که قبلاً ارزیابی کرده‌اید پاک نکنید."))
	service_rating = cint(payload.get("service_rating") or 0)
	if service_rating and not 1 <= service_rating <= 10:
		frappe.throw(_("امتیاز خدمت‌رسانی باید بین ۱ تا ۱۰ باشد."))
	review_scores = {entry["line"]["order_item"]: entry["score"] for entry in reviews}
	order_question_scores = [cint(answer["value"]) for answer in answers if not answer.get("order_item") and answer["answer_type"] == "امتیاز ۱ تا ۱۰"]
	order_feature_score = service_rating or (round(sum(order_question_scores) / len(order_question_scores)) if order_question_scores else 0)
	for answer in answers:
		row_key = answer.get("order_item") or ""
		score = review_scores.get(row_key) if row_key else order_feature_score
		if row_key and not score:
			frappe.throw(_("برای پاسخ به پرسش اختصاصی، ابتدا به همان غذا امتیاز بدهید."))
		if answer["answer_type"] == "ویژگی خوب/بد":
			value = answer["value"]
			if score and ((score >= 7 and value != "نقطه قوت") or (score <= 3 and value != "نیاز به بهبود")):
				frappe.throw(_("ویژگی انتخاب‌شده با امتیاز این غذا هم‌خوانی ندارد."))
	scores = [x["score"] for x in reviews] + ([service_rating] if service_rating else []) + [cint(x["value"]) for x in answers if x["answer_type"] == "امتیاز ۱ تا ۱۰"]
	if not scores:
		frappe.throw(_("دست‌کم به یک غذا یا خدمت‌رسانی امتیاز بدهید."))
	response = frappe.get_doc(RESPONSE, response_name) if is_edit else frappe.new_doc(RESPONSE)
	response.invitation = invitation.name
	response.source_key = invitation.order_key
	response.order_code = invitation.order_code
	response.sales_order = invitation.sales_order or None
	response.table_order = invitation.table_order or None
	response.customer = invitation.customer or None
	response.mobile = invitation.mobile
	response.overall_rating = round(sum(scores) / len(scores))
	response.service_rating = service_rating
	response.answers_json = json.dumps(answers, ensure_ascii=False)
	response.comment = str(payload.get("comment") or "").strip()[:2000]
	response.entry_date = now_datetime()
	if is_edit:
		response.save(ignore_permissions=True)
	else:
		response.insert(ignore_permissions=True)
	for value in reviews:
		line = value["line"]
		line_key = f"{invitation.order_key}:{line['order_item']}"
		existing_review_name = frappe.db.get_value(REVIEW, {"source_line_key": line_key}, "name")
		if existing_review_name and not is_edit:
			frappe.throw(_("برای یکی از غذاهای سفارش نظر ثبت شده است."))
		doc = frappe.get_doc(REVIEW, existing_review_name) if existing_review_name else frappe.new_doc(REVIEW)
		doc.invitation = invitation.name
		doc.source_line_key = line_key
		doc.order_item = line["order_item"]
		doc.customer_name = invitation.customer_name or "مشتری ویدرخت"
		doc.mobile = invitation.mobile
		doc.item = line["item"]
		doc.item_slug = line["item_slug"]
		doc.sales_order = invitation.sales_order or None
		doc.table_order = invitation.table_order or None
		doc.order_code = invitation.order_code
		doc.score_10 = value["score"]
		doc.rating = value["score"] / 2
		doc.title = _("خرید تأییدشده")
		doc.comment = value["comment"]
		doc.strengths_json = json.dumps(value["strengths"], ensure_ascii=False)
		doc.weaknesses_json = json.dumps(value["weaknesses"], ensure_ascii=False)
		doc.moderation_status = "در انتظار بررسی"
		doc.is_approved = 0
		if existing_review_name:
			doc.save(ignore_permissions=True)
		else:
			doc.insert(ignore_permissions=True)
	if not was_submitted:
		invitation.status = "تکمیل‌شده"
		invitation.submitted_at = now_datetime()
		invitation.save(ignore_permissions=True)
	settings = api_club._club_club_settings()
	if response.overall_rating <= settings["survey_alert_threshold"] and not cint(response.dissatisfaction_alerted):
		response.dissatisfaction_alerted = api_club._club_alert_dissatisfaction(response, settings["survey_alert_threshold"], settings["survey_alert_users"])
		response.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": response.name, "reviews": len(reviews), "alerted": response.dissatisfaction_alerted, "edited": int(is_edit)}


def _question_payload(rows):
	return [dict(row) for row in rows]


@frappe.whitelist()
def list_management_survey_questions(include_inactive=0):
	api_club._ensure_management_access()
	filters = {} if cint(include_inactive) else {"is_active": 1}
	rows = frappe.get_all(QUESTION, filters=filters, fields=["name", "question", "answer_type", "scope", "target_item_group", "target_item", "sort_order", "is_active"], order_by="sort_order asc, creation asc", limit_page_length=200)
	return {"questions": _question_payload(rows), "count": len(rows)}


@frappe.whitelist()
def save_management_survey_question(payload=None):
	api_club._ensure_management_access()
	data = api_club._club_parse_json(payload, {})
	name, question = str(data.get("name") or "").strip(), str(data.get("question") or "").strip()
	if not question:
		frappe.throw(_("متن سوال الزامی است."))
	answer_type = str(data.get("answer_type") or QUESTION_TYPES[0]).strip()
	scope = str(data.get("scope") or "سفارش").strip()
	if answer_type not in QUESTION_TYPES or scope not in QUESTION_SCOPES:
		frappe.throw(_("نوع پاسخ یا دامنهٔ سوال معتبر نیست."))
	if scope == "گروه غذا" and not frappe.db.exists("Item Group", data.get("target_item_group")):
		frappe.throw(_("گروه غذا را انتخاب کنید."))
	if scope == "محصول" and not frappe.db.exists("Item", data.get("target_item")):
		frappe.throw(_("محصول را انتخاب کنید."))
	doc = frappe.get_doc(QUESTION, name) if name and frappe.db.exists(QUESTION, name) else frappe.new_doc(QUESTION)
	doc.question, doc.answer_type, doc.scope = question, answer_type, scope
	doc.target_item_group = data.get("target_item_group") if scope == "گروه غذا" else None
	doc.target_item = data.get("target_item") if scope == "محصول" else None
	doc.sort_order, doc.is_active = cint(data.get("sort_order")), cint(data.get("is_active", 1))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": doc.name}


@frappe.whitelist()
def delete_management_survey_question(name=""):
	api_club._ensure_management_access()
	if not frappe.db.exists(QUESTION, name):
		frappe.throw(_("پرسش پیدا نشد."))
	frappe.delete_doc(QUESTION, name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def list_management_survey_targets():
	api_club._ensure_management_access()
	groups = frappe.get_all("Item Group", filters={"is_group": 0}, fields=["name", "item_group_name"], order_by="item_group_name asc", limit_page_length=1000)
	items = frappe.get_all("Item", filters={"disabled": 0, "is_sales_item": 1}, fields=["name", "item_name", "item_group"], order_by="item_name asc", limit_page_length=2000)
	return {"groups": groups, "items": items}


@frappe.whitelist()
def list_management_survey_responses(date_from="", date_to="", search="", min_rating=0, max_rating=0):
	api_club._ensure_management_access()
	rows = frappe.get_all(RESPONSE, fields=["name", "invitation", "order_code", "sales_order", "table_order", "customer", "mobile", "overall_rating", "service_rating", "comment", "dissatisfaction_alerted", "entry_date", "answers_json"], order_by="creation desc", limit_page_length=500)
	needle, low, high = str(search or "").strip().lower(), cint(min_rating), cint(max_rating)
	out = []
	for row in rows:
		date = str(row.entry_date or "")[:10]
		if date_from and date < str(date_from) or date_to and date > str(date_to):
			continue
		if low and cint(row.overall_rating) < low or high and cint(row.overall_rating) > high:
			continue
		customer_name = frappe.db.get_value("Customer", row.customer, "customer_name") if row.customer else ""
		if needle and needle not in " ".join(str(x or "") for x in (row.order_code, row.mobile, customer_name, row.comment)).lower():
			continue
		try:
			answers = json.loads(row.answers_json or "[]")
		except Exception:
			answers = []
		out.append({**row, "customer_name": customer_name or row.customer or "", "answers": answers, "entry_date": str(row.entry_date or "")})
	return {"responses": out, "count": len(out)}


@frappe.whitelist()
def list_management_survey_invitations(limit=100):
	api_club._ensure_management_access()
	rows = frappe.get_all(INVITATION, fields=["name", "order_code", "customer_name", "mobile", "status", "due_at", "attempts", "last_error", "submitted_at", "expires_at"], order_by="creation desc", limit_page_length=min(max(cint(limit), 1), 300))
	for row in rows:
		row.can_retry = not row.submitted_at and (not row.expires_at or get_datetime(row.expires_at) >= now_datetime())
	return {"invitations": rows, "count": len(rows)}


@frappe.whitelist()
def retry_management_survey_invitation(name=""):
	api_club._ensure_management_access()
	if not frappe.db.exists(INVITATION, name):
		frappe.throw(_("دعوت نظرسنجی پیدا نشد."))
	doc = frappe.get_doc(INVITATION, name)
	if doc.submitted_at or doc.expires_at and get_datetime(doc.expires_at) < now_datetime():
		frappe.throw(_("دعوت تکمیل شده یا مهلت آن تمام شده است."))
	doc.status, doc.due_at, doc.token_hash, doc.last_error = "در انتظار ارسال", now_datetime(), "", ""
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "queued", "name": doc.name}


@frappe.whitelist()
def list_management_customer_reviews(status="", search="", limit=200):
	api_club._ensure_management_access()
	filters = {"moderation_status": status} if status in REVIEW_STATES else {}
	rows = frappe.get_all(REVIEW, filters=filters, fields=["name", "customer_name", "mobile", "item", "item_slug", "order_code", "score_10", "rating", "comment", "strengths_json", "weaknesses_json", "moderation_status", "manager_reply", "creation"], order_by="creation desc", limit_page_length=min(max(cint(limit), 1), 500), ignore_permissions=True)
	needle, out = str(search or "").strip().lower(), []
	for row in rows:
		item = frappe.db.get_value("Item", row.item, ["item_name", "image"], as_dict=True) if row.item else {}
		if needle and needle not in " ".join(str(x or "") for x in (row.customer_name, row.mobile, row.order_code, (item or {}).get("item_name"), row.comment)).lower():
			continue
		for field in ("strengths_json", "weaknesses_json"):
			try:
				row[field] = json.loads(row[field] or "[]")
			except Exception:
				row[field] = []
		out.append({**row, "score_10": cint(row.score_10 or flt(row.rating) * 2), "item_title": (item or {}).get("item_name") or row.item or "", "image": (item or {}).get("image") or "", "created_at": str(row.creation or "")})
	return {"reviews": out, "count": len(out)}


@frappe.whitelist()
def review_management_customer_review(name="", moderation_status="", manager_reply=None):
	api_club._ensure_management_access()
	if moderation_status and moderation_status not in REVIEW_STATES:
		frappe.throw(_("وضعیت بررسی نامعتبر است."))
	if not frappe.db.exists(REVIEW, name):
		frappe.throw(_("نظر محصول پیدا نشد."))
	doc = frappe.get_doc(REVIEW, name)
	if moderation_status:
		doc.moderation_status = moderation_status
		doc.is_approved = 1 if moderation_status == "تأییدشده" else 0
	if manager_reply is not None:
		doc.manager_reply = str(manager_reply or "").strip()[:2000]
		doc.replied_at = now_datetime() if doc.manager_reply else None
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "moderation_status": doc.moderation_status, "manager_reply": doc.manager_reply or ""}


@frappe.whitelist(allow_guest=True)
def list_my_customer_reviews(customer_token=None):
	from restaurant.api import _customer_session_identity
	identity = _customer_session_identity(customer_token, required=True)
	customer, mobile = identity.get("customer") or "", _valid_mobile(identity.get("mobile"))
	invites = frappe.get_all(INVITATION, filters={"customer": customer}, pluck="name", limit_page_length=0, ignore_permissions=True) if customer else []
	filters = [["Restaurant Customer Review", "invitation", "in", invites]] if invites else [["Restaurant Customer Review", "mobile", "=", mobile]]
	rows = frappe.get_all(REVIEW, filters=filters, fields=["name", "invitation", "customer_name", "mobile", "item", "score_10", "rating", "comment", "moderation_status", "manager_reply", "replied_at", "creation"], order_by="creation desc", limit_page_length=200, ignore_permissions=True)
	out = []
	for row in rows:
		if row.invitation not in invites and (not mobile or _valid_mobile(row.mobile) != mobile):
			continue
		item = frappe.db.get_value("Item", row.item, ["item_name", "image"], as_dict=True) if row.item else {}
		out.append({**row, "score_10": cint(row.score_10 or flt(row.rating) * 2), "item_title": (item or {}).get("item_name") or row.item or "", "image": (item or {}).get("image") or "", "created_at": str(row.creation or "")})
	return {"reviews": out, "count": len(out)}


def run_due_survey_invitations(limit=50):
	if not frappe.db.exists("DocType", INVITATION):
		return {"sent": 0, "skipped": 0, "failed": 0}
	now = now_datetime()
	rows = frappe.get_all(INVITATION, filters={"status": "در انتظار ارسال", "due_at": ["<=", now], "expires_at": [">=", now], "submitted_at": ["is", "not set"]}, fields=["name"], order_by="due_at asc", limit_page_length=min(max(cint(limit), 1), 100))
	result = {"sent": 0, "skipped": 0, "failed": 0}
	for row in rows:
		try:
			locked = frappe.db.sql(f"SELECT name FROM `tab{INVITATION}` WHERE name=%s AND status='در انتظار ارسال' FOR UPDATE", row.name)
			if not locked:
				continue
			doc = frappe.get_doc(INVITATION, row.name)
			settings = api_club._club_club_settings()
			if not settings["sms_enabled"]:
				status, note, text = "بدون درگاه", _("ارسال پیامک غیرفعال است؛ مشتری می‌تواند از حسابش نظر ثبت کند."), ""
			else:
				token = secrets.token_urlsafe(32)
				doc.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
				doc.status = "در حال ارسال"
				doc.attempts = cint(doc.attempts) + 1
				doc.save(ignore_permissions=True)
				frappe.db.commit()
				link = f"{frappe.utils.get_url()}/survey?token={token}"
				template = settings["sms_templates"].get("survey_invite", api_club.DEFAULT_SMS_TEMPLATES["survey_invite"])
				text = api_club._club_render_sms(template, doc.customer_name, order=doc.order_code, link=link)
				status, note = api_club._club_send_sms_now(doc.mobile, text)
			link_to_redact = link if settings["sms_enabled"] else ""
			log_text = _redact_survey_url(text, link_to_redact)
			safe_note = _redact_survey_url(note, link_to_redact)
			sms = api_club._club_log_sms(mobile=doc.mobile, message=log_text or safe_note, kind="نظرسنجی سفارش", customer=doc.customer or "", template_key="survey_invite", status_note=(status, safe_note), reference_doctype=INVITATION, reference_name=doc.name)
			doc.sms_message = sms.name
			doc.status = "ارسال‌شده" if status == "ارسال‌شده" else "بدون درگاه" if status == "بدون درگاه" else "ناموفق"
			doc.last_error = safe_note or ""
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			result["sent" if status == "ارسال‌شده" else "skipped" if status == "بدون درگاه" else "failed"] += 1
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "Restaurant survey invitation send failed")
			try:
				frappe.db.set_value(INVITATION, row.name, {"status": "ناموفق", "last_error": _("ارسال انجام نشد؛ از پنل دوباره تلاش کنید.")}, update_modified=False)
				frappe.db.commit()
			except Exception:
				pass
			result["failed"] += 1
	return result
