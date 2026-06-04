import frappe

from ._context import build_context


def _resolve_report_key():
    report_key = (frappe.form_dict.get("report_key") or "").strip()
    if report_key:
        return report_key

    path = (frappe.local.request.path or "").strip("/")
    parts = path.split("/")
    if len(parts) >= 3 and parts[-2] == "reports":
        return (parts[-1] or "").strip()
    return ""


def get_context(context):
    return build_context(
        context,
        "management-report",
        extra_boot={"report_key": _resolve_report_key()},
    )
