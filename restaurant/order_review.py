"""Shared approval state for customer-originated store orders."""

from contextlib import contextmanager


ORDER_REVIEW_FIELD = "restaurant_order_review_status"
ORDER_REVIEW_PENDING = "در انتظار بررسی"
ORDER_REVIEW_APPROVED = "تأیید شده"
ORDER_REVIEW_REJECTED = "رد شده"


def get_order_review_status(order_name):
	import frappe

	if not frappe.db.has_column("Sales Order", ORDER_REVIEW_FIELD):
		return ORDER_REVIEW_APPROVED
	return frappe.db.get_value("Sales Order", order_name, ORDER_REVIEW_FIELD) or ORDER_REVIEW_APPROVED


def order_is_approved(order_name):
	return get_order_review_status(order_name) == ORDER_REVIEW_APPROVED


def require_order_approved(order_name):
	import frappe
	from frappe import _

	status = get_order_review_status(order_name)
	if status != ORDER_REVIEW_APPROVED:
		frappe.throw(_("ابتدا سفارش باید در بخش «نیازمند بررسی» تأیید شود."))


def should_require_customer_order_review():
	import frappe

	return not bool(getattr(frappe.local, "_restaurant_internal_order_creation", False))


@contextmanager
def internal_order_creation():
	"""Mark an order built by POS or a trusted server workflow as pre-approved."""
	import frappe

	attribute = "_restaurant_internal_order_creation"
	previous = getattr(frappe.local, attribute, False)
	setattr(frappe.local, attribute, True)
	try:
		yield
	finally:
		if previous:
			setattr(frappe.local, attribute, previous)
		else:
			try:
				delattr(frappe.local, attribute)
			except AttributeError:
				pass
