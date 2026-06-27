import frappe


def _resolve_order_page():
	path = (getattr(frappe.local.request, "path", "") or "").strip("/").replace("_", "-")
	if path in {"order", "order/start"}:
		return "order-start"
	if path.startswith("order/type"):
		return "order-type"
	if path.startswith("order/dine-in"):
		return "order-dine-in"
	if path.startswith("order/pickup"):
		return "order-pickup"
	if path.startswith("order/delivery"):
		return "order-delivery"
	return "not-found"


def get_context(context):
	context.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.page = _resolve_order_page()
	context.boot = {
		"page": context.page,
		"branding": {
			"name": "Veederakht Restaurant",
			"tagline": "منوی آنلاین",
		},
		"currency": "IRR",
	}
	return context
