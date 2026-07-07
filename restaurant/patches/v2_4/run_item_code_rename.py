import frappe


def _normalize_item_name(value):
    text = " ".join(str(value or "").split()).strip()
    return text.replace("/", "-").replace("\\", "-").strip()


def execute():
    has_snapp_code_field = frappe.db.has_column("Item", "custom_snapp_code")
    fields = ["name", "item_code", "item_name", "is_sales_item"]
    if has_snapp_code_field:
        fields.append("custom_snapp_code")

    rows = frappe.get_all(
        "Item",
        fields=fields,
        limit_page_length=0,
        ignore_permissions=True,
    )

    updated_snapp_code = 0
    renamed_count = 0
    skipped_count = 0
    errors = []

    for row in rows:
        if int(row.get("is_sales_item") or 0) != 1:
            continue

        item_name_doc = (row.get("name") or "").strip()
        item_code = (row.get("item_code") or "").strip()
        item_name = _normalize_item_name(row.get("item_name"))

        if has_snapp_code_field and item_code.startswith("SNP-") and not (row.get("custom_snapp_code") or "").strip():
            frappe.db.set_value("Item", item_name_doc, "custom_snapp_code", item_code, update_modified=False)
            updated_snapp_code += 1

        if not item_name:
            skipped_count += 1
            continue
        if item_name == item_name_doc:
            continue

        candidate = item_name[:120]
        if not candidate:
            skipped_count += 1
            continue

        if frappe.db.exists("Item", candidate) and candidate != item_name_doc:
            suffix = 1
            while True:
                suffix_text = f"-{suffix}"
                attempt = f"{candidate[: 120 - len(suffix_text)]}{suffix_text}"
                if not frappe.db.exists("Item", attempt):
                    candidate = attempt
                    break
                suffix += 1

        try:
            frappe.rename_doc(
                "Item",
                item_name_doc,
                candidate,
                force=True,
                merge=False,
                show_alert=False,
            )
            renamed_count += 1
        except Exception as exc:
            errors.append(
                {
                    "item": item_name_doc,
                    "error": str(exc),
                }
            )

    frappe.db.commit()
    return {
        "updated_snapp_code": updated_snapp_code,
        "renamed_count": renamed_count,
        "skipped_count": skipped_count,
        "errors_count": len(errors),
        "errors": errors[:20],
    }
