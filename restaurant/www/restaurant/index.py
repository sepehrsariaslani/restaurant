import frappe

from restaurant.api import get_menu_boot
from restaurant.www._frontend import get_frontend_version


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context.boot = get_menu_boot()
    context.frontend_version = get_frontend_version(context)
    return context
