import frappe


def get_context(context):
	frappe.local.flags.redirect_location = "/assets/restaurant/frontend/manifest.webmanifest?v=20260705c"
	raise frappe.Redirect
