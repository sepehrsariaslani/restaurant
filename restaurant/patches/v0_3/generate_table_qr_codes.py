import frappe


def _has_legacy_base64_svg(file_url):
    if not file_url:
        return False

    try:
        path = frappe.get_site_path("public", file_url.lstrip("/"))
        with open(path, "rb") as f:
            head = f.read(16).strip()
        if not head:
            return True
        if head.startswith(b"<"):
            return False
        return head.startswith(b"PD94") or head.startswith(b"PHN2")
    except Exception:
        return True


def execute():
    if not frappe.db.exists("DocType", "Restaurant Table"):
        return

    rows = frappe.get_all(
        "Restaurant Table",
        fields=["name", "qr_code_token", "qr_target_url", "qr_code_image"],
        ignore_permissions=True,
        limit_page_length=5000,
    )

    for row in rows:
        should_skip = (
            row.qr_code_token
            and row.qr_target_url
            and row.qr_live_url
            and row.qr_code_image
            and not _has_legacy_base64_svg(row.qr_code_image)
        )
        if should_skip:
            continue

        doc = frappe.get_doc("Restaurant Table", row.name)
        if _has_legacy_base64_svg(doc.qr_code_image):
            doc.qr_code_image = ""
        doc.save(ignore_permissions=True)
