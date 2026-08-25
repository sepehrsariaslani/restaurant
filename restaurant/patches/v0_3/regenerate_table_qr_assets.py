import frappe

from restaurant.patches.v0_3.generate_table_qr_codes import _has_legacy_base64_svg


def execute():
    if not frappe.db.exists("DocType", "Restaurant Table"):
        return

    rows = frappe.get_all(
        "Restaurant Table",
        fields=["name", "qr_code_image"],
        ignore_permissions=True,
        limit_page_length=5000,
    )

    for row in rows:
        doc = frappe.get_doc("Restaurant Table", row.name)
        if _has_legacy_base64_svg(doc.qr_code_image):
            doc.qr_code_image = ""
        doc.save(ignore_permissions=True)
