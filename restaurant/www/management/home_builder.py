import frappe

from restaurant.api import get_menu_boot

from ._context import _ensure_management_page_access, _ensure_roles, _resolve_context_csrf_token


def get_context(context):
    # The builder's live preview needs the full menu boot (categories,
    # featured items, faq, about sections, currency, page_layout), not the
    # trimmed management boot, so it renders with real content.
    _ensure_management_page_access()
    _ensure_roles({"System Manager"})
    context.csrf_token = _resolve_context_csrf_token()

    menu_boot = get_menu_boot()
    boot = dict(menu_boot or {})
    boot["page_meta"] = {"page_name": "management-home-builder"}
    context.boot = boot
    return context
