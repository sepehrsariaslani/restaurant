import frappe
from frappe import _

from restaurant.api import get_item_detail, table_boot


def _resolve_slug_from_request():
    slug = (frappe.form_dict.get("slug") or "").strip()
    if slug:
        return slug

    path = (frappe.local.request.path or "").strip("/")
    parts = path.split("/")
    if len(parts) >= 3 and parts[-2] == "item":
        return parts[-1]

    return ""


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
        frappe.log_error(frappe.get_traceback(), "restaurant.item.table_boot_failed")
        return {
            "qr_token": qr_token,
            "error": "invalid_or_inactive_table_token",
        }


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()

    slug = _resolve_slug_from_request()
    table_context = _resolve_table_context()
    branch = (frappe.form_dict.get("branch") or "").strip()
    if not branch and table_context:
        branch = (table_context.get("table", {}) or {}).get("branch", "") or ""

    boot = {
        "item_slug": slug,
        "edit_line": (frappe.form_dict.get("edit") or "").strip(),
        "active_branch": branch,
    }

    if slug:
        try:
            boot.update(get_item_detail(slug, branch=branch))
        except frappe.DoesNotExistError:
            frappe.local.flags.redirect_location = "/menu"
            raise frappe.Redirect
        except Exception:
            frappe.log_error(frappe.get_traceback(), "restaurant.item.get_item_detail_failed")
            boot["item_error"] = _("Menu item could not be loaded.")
    else:
        boot["item_error"] = _("Item slug is required.")

    if table_context:
        boot["table_context"] = table_context

    context.boot = boot
    return context
