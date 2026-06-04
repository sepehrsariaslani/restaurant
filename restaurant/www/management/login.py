from urllib.parse import unquote

import frappe

from restaurant.api import get_menu_boot
from restaurant.www.management._context import _resolve_context_csrf_token


def _resolve_redirect_target():
    redirect_to = (
        (frappe.form_dict.get("redirect_to") or frappe.form_dict.get("redirect") or "").strip()
    )
    if redirect_to:
        redirect_to = unquote(redirect_to)
    if not redirect_to or not redirect_to.startswith("/desk"):
        return "/desk"
    return redirect_to


def get_context(context):
    context.csrf_token = _resolve_context_csrf_token()

    branding = {}
    theme_settings = {}
    try:
        menu_boot = get_menu_boot()
        branding = menu_boot.get("branding") or {}
        theme_settings = menu_boot.get("theme_settings") or {}
    except Exception:
        branding = {}
        theme_settings = {}

    context.boot = {
        "branding": branding,
        "theme_settings": theme_settings,
        "login_redirect_to": _resolve_redirect_target(),
        "page_meta": {"page_name": "management-login"},
    }
    return context
