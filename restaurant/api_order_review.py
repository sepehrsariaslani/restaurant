"""Management actions for reviewing website and Food Partner orders."""

import json

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from restaurant.order_review import (
	ORDER_REVIEW_APPROVED,
	ORDER_REVIEW_FIELD,
	ORDER_REVIEW_PENDING,
	ORDER_REVIEW_REJECTED,
)

__all__ = ["review_management_order"]


def _order_has_column(fieldname):
	return frappe.db.has_column("Sales Order", fieldname)


def validate_sales_order_submission(doc, method=None):
	"""Keep a pending or rejected order out of native submitted workflows."""
	status = doc.get(ORDER_REVIEW_FIELD) or ORDER_REVIEW_APPROVED
	if status in {ORDER_REVIEW_PENDING, ORDER_REVIEW_REJECTED}:
		frappe.throw(_("ابتدا سفارش را بررسی و تأیید کنید."))


def _food_partner_invoice_payload(order):
	from restaurant.snapp_sync import _get_settings, normalize_snapp_order

	raw_payload = {}
	if order.get("restaurant_external_payload_json"):
		try:
			raw_payload = json.loads(order.restaurant_external_payload_json)
		except (TypeError, ValueError):
			raw_payload = {}
	settings = _get_settings()
	payload = {}
	if isinstance(raw_payload, dict) and raw_payload:
		try:
			payload = normalize_snapp_order(
				raw_payload,
				amount_multiplier=settings.get("amount_multiplier") or 1,
			)
		except Exception:
			payload = {}

	for source_field, target_key in (
		("restaurant_external_order_id", "order_id"),
		("restaurant_external_bill_number", "bill_number"),
		("restaurant_external_state", "external_state"),
		("restaurant_external_payment_method", "payment_method"),
		("restaurant_external_customer_id", "external_customer_id"),
	):
		if _order_has_column(source_field):
			payload[target_key] = order.get(source_field) or payload.get(target_key) or ""
	payload.setdefault("raw", raw_payload)
	return payload


def _release_coupon_reservation(order_name):
	if not _order_has_column("restaurant_payload_json") or not frappe.db.exists("DocType", "Restaurant Coupon"):
		return
	raw_payload = frappe.db.get_value("Sales Order", order_name, "restaurant_payload_json") or ""
	try:
		rows = json.loads(raw_payload)
	except (TypeError, ValueError):
		return
	if not isinstance(rows, list):
		return
	coupon_code = next(
		(
			str(row.get("coupon") or "").strip()
			for row in rows
			if isinstance(row, dict) and row.get("discount_source") == "coupon" and row.get("coupon")
		),
		"",
	)
	if not coupon_code:
		return
	from restaurant.api import _find_coupon_doc

	coupon = _find_coupon_doc(coupon_code)
	if not coupon:
		return
	used_count = cint(coupon.get("used_count") or 0)
	if used_count > 0:
		frappe.db.set_value("Restaurant Coupon", coupon.name, "used_count", used_count - 1, update_modified=False)


@frappe.whitelist()
def review_management_order(order_name="", decision="", note=""):
	"""Approve or reject a pending customer-originated Sales Order."""
	from restaurant.api import _append_sales_order_note, _ensure_management_access, _set_restaurant_order_status

	_ensure_management_access()
	order_name = (order_name or "").strip()
	decision = (decision or "").strip().lower()
	if not order_name or not frappe.db.exists("Sales Order", order_name):
		frappe.throw(_("سفارش یافت نشد."), frappe.DoesNotExistError)
	if not _order_has_column(ORDER_REVIEW_FIELD):
		frappe.throw(_("وضعیت بررسی سفارش‌ها هنوز روی پایگاه داده فعال نشده است."))
	if decision not in {"approve", "reject"}:
		frappe.throw(_("عملیات بررسی سفارش معتبر نیست."))

	# Serialize review actions across POS devices. A second device must read the
	# committed state after the first device has reviewed this Sales Order.
	frappe.db.sql(
		"SELECT name FROM `tabSales Order` WHERE name = %s FOR UPDATE",
		order_name,
	)
	current = frappe.db.get_value("Sales Order", order_name, ORDER_REVIEW_FIELD) or ORDER_REVIEW_APPROVED
	target_status = ORDER_REVIEW_APPROVED if decision == "approve" else ORDER_REVIEW_REJECTED
	if current == target_status:
		return {
			"status": "success",
			"order_name": order_name,
			"review_status": current,
			"sales_invoice": "",
			"idempotent": True,
		}
	if current != ORDER_REVIEW_PENDING:
		frappe.throw(_("این سفارش دیگر در انتظار بررسی نیست."))

	now = now_datetime()
	stage = "ثبت وضعیت بررسی"
	invoice_name = ""
	try:
		updates = {ORDER_REVIEW_FIELD: target_status}
		if _order_has_column("restaurant_order_reviewed_by"):
			updates["restaurant_order_reviewed_by"] = frappe.session.user
		if _order_has_column("restaurant_order_reviewed_at"):
			updates["restaurant_order_reviewed_at"] = now
		if _order_has_column("restaurant_order_review_note"):
			updates["restaurant_order_review_note"] = (note or "").strip()[:2000]
		frappe.db.set_value("Sales Order", order_name, updates, update_modified=False)

		if decision == "approve":
			stage = "ثبت سفارش فروش"
			order = frappe.get_doc("Sales Order", order_name)
			if order.docstatus == 0:
				order.flags.ignore_permissions = True
				order.submit()
			stage = "تغییر وضعیت رستوران"
			_set_restaurant_order_status(order_name, "confirmed", force=True)
			_append_sales_order_note(order_name, f"[ORDER REVIEW] سفارش تأیید شد توسط {frappe.session.user}.")
			external_source = order.get("restaurant_external_source") if _order_has_column("restaurant_external_source") else ""
			if external_source == "snapp_food":
				from restaurant.snapp_sync import _ensure_sales_invoice_for_order, _get_settings

				settings = _get_settings()
				if settings.get("auto_sync_invoices"):
					stage = "ثبت فاکتور Food Partner"
					invoice_result = _ensure_sales_invoice_for_order(
						order_name,
						_food_partner_invoice_payload(order),
					)
					invoice_name = invoice_result.get("sales_invoice") or ""
		else:
			stage = "رد سفارش"
			_set_restaurant_order_status(order_name, "cancelled", force=True)
			message = (note or "").strip()
			_append_sales_order_note(
				order_name,
				"[ORDER REVIEW] سفارش رد شد." + (f" دلیل: {message}" if message else ""),
			)
			_release_coupon_reservation(order_name)

		stage = "ثبت نهایی تراکنش"
		frappe.db.commit()
	except Exception as exc:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "Food Partner order review failed")
		message = str(exc).strip() or "خطای نامشخص"
		frappe.throw(
			_("بررسی سفارش در مرحلهٔ {0} ناموفق بود: {1}").format(stage, message[:500]),
			frappe.ValidationError,
		)

	return {
		"status": "success",
		"order_name": order_name,
		"review_status": target_status,
		"sales_invoice": invoice_name,
	}
