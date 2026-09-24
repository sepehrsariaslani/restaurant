import frappe

from restaurant.www._frontend import get_frontend_version


def get_context(context):
	frappe.local.flags.redirect_location = (
		f"/assets/restaurant/frontend/manifest.webmanifest?v={get_frontend_version(context)}"
	)
	raise frappe.Redirect
