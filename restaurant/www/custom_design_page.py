import frappe
from restaurant.www._frontend import get_frontend_version


def get_context(context):
    from restaurant.api import get_menu_boot
    from restaurant.page_layout import get_public_design_page
    slug = frappe.form_dict.get("slug") or frappe.local.request.path.rstrip("/").split("/")[-1]
    context.design_page = get_public_design_page(slug)
    context.design_title = context.design_page["metadata"]["title"]
    context.design_description = context.design_page["metadata"]["description"]
    context.boot = get_menu_boot()
    context.frontend_version = get_frontend_version(context)
    context.no_cache = 1
    return context
