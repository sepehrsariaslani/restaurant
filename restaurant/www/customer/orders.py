import frappe


def get_context(context):
	context.no_cache = 1
	context.boot = {
		"page": "customer-orders",
	}
	context.csrf_token = frappe.sessions.get_csrf_token()
	return context
