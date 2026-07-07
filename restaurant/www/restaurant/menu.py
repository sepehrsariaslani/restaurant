import frappe

from restaurant.api import get_menu_boot, table_boot


def _resolve_table_context():
    qr_token = (frappe.form_dict.get("qr_token") or frappe.form_dict.get("table_token") or "").strip()
    if not qr_token:
        return None

    try:
        table_payload = table_boot(qr_token)
        return {
            "qr_token": qr_token,
            "table": table_payload.get("table"),
            "session": table_payload.get("session"),
        }
    except Exception:
        frappe.log_error(frappe.get_traceback(), "restaurant.menu.table_boot_failed")
        return {
            "qr_token": qr_token,
            "error": "invalid_or_inactive_table_token",
        }


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()

    table_context = _resolve_table_context()
    branch = (frappe.form_dict.get("branch") or "").strip()
    if not branch and table_context:
        branch = (table_context.get("table", {}) or {}).get("branch", "") or ""

    boot = get_menu_boot(branch=branch)
    boot["active_branch"] = branch
    if table_context:
        boot["table_context"] = table_context

    context.boot = boot
    return context
