"""Short opaque tokens used by the public order survey link."""

from __future__ import annotations

import hashlib
import re
import secrets


_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,25}$")


def generate_token() -> str:
	return secrets.token_urlsafe(15)


def token_digest(token: str) -> str:
	return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()


def token_is_valid(token: str) -> bool:
	return bool(_TOKEN_PATTERN.fullmatch(str(token or "").strip()))


def issue_token(sales_order: str, customer: str = "", mobile: str = "", expires_at=None) -> str:
	"""Persist only a digest and return a short opaque token for the survey URL."""
	import frappe

	if not sales_order:
		raise ValueError("sales_order is required")
	for _ in range(5):
		token = generate_token()
		if not frappe.db.exists("Restaurant Survey Token", {"token_hash": token_digest(token)}):
			break
	else:
		raise RuntimeError("could not allocate a unique survey token")

	doc = frappe.get_doc(
		{
			"doctype": "Restaurant Survey Token",
			"sales_order": sales_order,
			"customer": customer or None,
			"mobile": mobile or "",
			"token_hash": token_digest(token),
			"expires_at": expires_at,
		}
	)
	doc.insert(ignore_permissions=True)
	return token


def resolve_token(token: str, now=None):
	"""Resolve a token internally without ever exposing the persisted digest."""
	import frappe
	from frappe.utils import get_datetime, now_datetime

	token = str(token or "").strip()
	if not token_is_valid(token) or not frappe.db.exists("DocType", "Restaurant Survey Token"):
		return None
	row = frappe.db.get_value(
		"Restaurant Survey Token",
		{"token_hash": token_digest(token)},
		["sales_order", "customer", "mobile", "expires_at", "revoked_at"],
		as_dict=True,
	)
	if not row or row.get("revoked_at"):
		return None
	current = get_datetime(now) if now else now_datetime()
	expires_at = row.get("expires_at")
	if expires_at and get_datetime(expires_at) <= current:
		return None
	return {
		"sales_order": row.get("sales_order") or "",
		"customer": row.get("customer") or "",
		"mobile": row.get("mobile") or "",
	}


def revoke_token(token: str) -> bool:
	"""Invalidate a token that was created for a failed SMS attempt."""
	import frappe
	from frappe.utils import now_datetime

	token = str(token or "").strip()
	if not token_is_valid(token) or not frappe.db.exists("DocType", "Restaurant Survey Token"):
		return False
	name = frappe.db.get_value("Restaurant Survey Token", {"token_hash": token_digest(token)}, "name")
	if not name:
		return False
	frappe.db.set_value("Restaurant Survey Token", name, "revoked_at", now_datetime(), update_modified=False)
	return True
