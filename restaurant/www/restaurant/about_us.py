import frappe

from restaurant.api import get_menu_boot


def get_context(context):
    context.no_cache = 1
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context.boot = get_menu_boot(branch=frappe.form_dict.get("branch"))
    return context
