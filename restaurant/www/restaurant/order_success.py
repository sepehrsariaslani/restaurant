import frappe


def _resolve_code_from_request():
    code = (frappe.form_dict.get("order_code") or "").strip()
    if code:
        return code

    path = (frappe.local.request.path or "").strip("/")
    parts = path.split("/")
    if len(parts) >= 3 and parts[-2] == "order-success":
        return parts[-1]

    return ""


def get_context(context):
    context.csrf_token = frappe.sessions.get_csrf_token()
    frappe.db.commit()
    context.boot = {
        "order_code": _resolve_code_from_request(),
        "mobile": (frappe.form_dict.get("mobile") or "").strip(),
    }
    return context
