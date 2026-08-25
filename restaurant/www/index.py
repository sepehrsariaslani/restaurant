import frappe


def get_context(context):
    frappe.local.flags.redirect_location = "/restaurant"
    raise frappe.Redirect
