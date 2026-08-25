import frappe


def _get_image_field():
    """Return the first available image field on Item."""
    for fieldname in ("image", "item_image", "website_image"):
        if frappe.db.has_column("Item", fieldname):
            return fieldname
    return "image"


def execute():
    """Backfill item images from File attachments for items that have an image attachment
    but the image field is empty. This fixes items uploaded via the Management panel
    where the image was saved as a File attachment but not copied to the image field."""
    image_field = _get_image_field()

    items = frappe.get_all(
        "Item",
        filters={
            "disabled": 0,
            "image": ["in", ["", None]],
        },
        fields=["name", "item_name"],
        limit=500,
    )

    updated = 0
    errors = []
    for item in items:
        try:
            attachments = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Item",
                    "attached_to_name": item.name,
                    "is_private": 0,
                },
                fields=["name", "file_url"],
                order_by="creation asc",
                limit=10,
            )
        except Exception as e:
            errors.append(f"{item.name}: {e}")
            continue

        for att in attachments or []:
            file_url = att.get("file_url") or ""
            if file_url and ("/files/" in file_url or "http" in file_url):
                try:
                    frappe.db.set_value("Item", item.name, image_field, file_url, update_modified=False)
                    updated += 1
                except Exception as e:
                    errors.append(f"{item.name} set_value: {e}")
                break

    frappe.db.commit()
    msg = f"Updated {updated} item images from attachments."
    if errors:
        msg += f" Errors: {'; '.join(errors[:5])}"
    return msg
