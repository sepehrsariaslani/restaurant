import frappe

from ._context import build_context


def get_context(context):
    item_name = (frappe.form_dict.get("item_name") or frappe.form_dict.get("item") or "").strip()
    return build_context(
        context,
        "management-product",
        extra_boot={"item_name": item_name},
    )
