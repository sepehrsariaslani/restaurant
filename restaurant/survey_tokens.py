"""Secure token lifecycle for Sales Order survey invitations."""

import hashlib
import hmac
import secrets

import frappe
from frappe.utils import get_datetime, now_datetime


INVITATION = "Restaurant Survey Invitation"
TOKEN_BYTES = 15

__all__ = ["generate_token", "issue_token", "resolve_token", "revoke_token", "token_digest"]


def generate_token():
	"""Return a URL-safe token that fits SMS.ir's 25-character value limit."""
	return secrets.token_urlsafe(TOKEN_BYTES)


def token_digest(token):
	return hashlib.sha256(str(token or "").strip().encode("utf-8")).hexdigest()


def _invitation_for_digest(digest):
	name = frappe.db.get_value(INVITATION, {"token_hash": digest}, "name")
	if not name:
		return None
	invitation = frappe.get_doc(INVITATION, name)
	stored_digest = str(invitation.get("token_hash") or "")
	return invitation if hmac.compare_digest(stored_digest, digest) else None


def _canonical_order_identity(order_name):
	"""Load the same canonical Sales Order identity used by survey APIs."""
	try:
		from restaurant.api_survey import _read_order_identity
	except (ImportError, AttributeError) as exc:
		raise ValueError("امکان اعتبارسنجی سفارش نظرسنجی فراهم نیست") from exc

	identity = _read_order_identity("Sales Order", order_name)
	if not identity or not identity.get("mobile"):
		raise ValueError("سفارش معتبر یا شماره موبایل معتبر برای نظرسنجی پیدا نشد")
	return identity


def issue_token(order_name, customer, mobile, expires_at):
	"""Create or refresh the secure invitation for a Sales Order."""
	order_name = str(order_name or "").strip()
	if not order_name:
		raise ValueError("Sales Order is required for a survey token")
	identity = _canonical_order_identity(order_name)

	key = f"Sales Order:{order_name}"
	name = frappe.db.get_value(INVITATION, {"order_key": key}, "name")
	invitation = frappe.get_doc(INVITATION, name) if name else frappe.new_doc(INVITATION)
	token = generate_token()
	now = now_datetime()

	invitation.order_key = key
	invitation.reference_doctype = "Sales Order"
	invitation.reference_name = order_name
	invitation.sales_order = order_name
	invitation.customer = identity.get("customer") or None
	invitation.customer_name = identity.get("customer_name") or ""
	invitation.mobile = str(identity["mobile"]).strip()
	invitation.order_code = identity.get("order_code") or order_name
	invitation.due_at = now
	invitation.expires_at = get_datetime(expires_at)
	invitation.token_hash = token_digest(token)
	invitation.status = "ارسال‌شده"
	invitation.last_error = ""
	if name:
		invitation.save(ignore_permissions=True)
	else:
		invitation.insert(ignore_permissions=True)
	return token


def revoke_token(token):
	"""Invalidate the matching invitation after an SMS provider failure."""
	if not str(token or "").strip():
		return None
	invitation = _invitation_for_digest(token_digest(token))
	if not invitation:
		return None
	invitation.token_hash = ""
	invitation.status = "ناموفق"
	invitation.save(ignore_permissions=True)
	return None


def resolve_token(token):
	"""Resolve a non-expired token without returning or persisting the raw value."""
	if not str(token or "").strip():
		return None
	invitation = _invitation_for_digest(token_digest(token))
	if not invitation:
		return None
	if invitation.get("expires_at") and get_datetime(invitation.expires_at) < now_datetime():
		return None
	return invitation
