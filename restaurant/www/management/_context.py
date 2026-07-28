import time
from urllib.parse import quote

import frappe

from restaurant.api import get_menu_boot


def _ensure_management_page_access():
    if frappe.session.user == "Guest":
        request = getattr(frappe.local, "request", None)
        request_path = str(getattr(request, "path", "") or "/management").strip() or "/management"
        query_string = getattr(request, "query_string", "") or ""
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8", errors="ignore")
        query_string = str(query_string).strip()
        redirect_to = f"{request_path}?{query_string}" if query_string else request_path
        frappe.local.flags.redirect_location = f"/management/login?redirect_to={quote(redirect_to, safe='')}"
        raise frappe.Redirect
    roles = set(frappe.get_roles(frappe.session.user))
    if not roles.intersection({"System Manager", "Desk User"}):
        frappe.throw("You don't have access to management pages.", frappe.PermissionError)


def _is_tabsessions_conflict(error):
    message = str(error or "").lower()
    return "1020" in message and "tabsessions" in message


def _resolve_context_csrf_token():
    existing = str((frappe.local.session.data or {}).get("csrf_token") or "").strip()
    if existing:
        return existing

    for attempt in range(3):
        try:
            return frappe.sessions.get_csrf_token()
        except Exception as error:
            if not _is_tabsessions_conflict(error):
                raise
            frappe.db.rollback()
            if attempt < 2:
                time.sleep(0.05 * (attempt + 1))

    token = str((frappe.local.session.data or {}).get("csrf_token") or "").strip()
    if token:
        return token

    # Fallback to avoid crashing management page render in rare session races.
    token = frappe.generate_hash()
    frappe.local.session.data.csrf_token = token
    try:
        frappe.local.session_obj.update(force=True)
    except Exception:
        pass
    return token


def _ensure_roles(required_roles):
    normalized_roles = set(required_roles or [])
    if not normalized_roles:
        return
    user = frappe.session.user
    if user == "Administrator":
        return
    roles = set(frappe.get_roles(user))
    if not roles.intersection(normalized_roles):
        frappe.throw("You don't have permission to access this page.", frappe.PermissionError)



import os

def _get_frontend_version():
    try:
        # Cache busting strategy: Use the actual modified time of the built asset
        # so it auto-updates precisely when `npm run build` is executed.
        asset_path = frappe.get_app_path("restaurant", "public", "frontend", "assets", "index.js")
        if os.path.exists(asset_path):
            return str(int(os.path.getmtime(asset_path)))
    except Exception:
        pass
    
    # Fallback to frappe's system build version
    return frappe.utils.get_build_version()


def build_context(context, page_name, extra_boot=None, required_roles=None):
    _ensure_management_page_access()
    _ensure_roles(required_roles)
    context.csrf_token = _resolve_context_csrf_token()
    menu_boot = get_menu_boot()

    boot = {
        "branding": menu_boot.get("branding") or {},
        "theme_settings": menu_boot.get("theme_settings") or {},
        "page_meta": {
            "page_name": page_name,
        },
    }
    if isinstance(extra_boot, dict):
        boot.update(extra_boot)
    context.boot = boot
    context.frontend_version = _get_frontend_version()
    return context
