import frappe
from restaurant.api import get_public_site_boot
from restaurant.www._frontend import get_frontend_version


def get_context(context):
	context.no_cache = 1
	order_code = frappe.form_dict.get("name") or frappe.form_dict.get("order_code") or ""
	context.boot = {
		**get_public_site_boot(),
		"page": "customer-order-detail" if order_code else "customer-orders",
		"order_code": order_code,
	}
	context.frontend_version = get_frontend_version(context)
	context.csrf_token = frappe.sessions.get_csrf_token()
	return context
