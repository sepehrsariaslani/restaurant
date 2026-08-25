import frappe


CUSTOM_FIELD_DEF = {
    "fieldname": "custom_snapp_code",
    "label": "Custom Snapp Code",
    "fieldtype": "Data",
    "insert_after": "restaurant_external_menu_item_id",
    "search_index": 1,
    "module": "Restaurant",
}


def _ensure_custom_field(dt, field_def):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
        **field_def,
    }

    if existing_name:
        doc = frappe.get_doc("Custom Field", existing_name)
        changed = False
        for key, value in payload.items():
            if key == "doctype":
                continue
            if doc.get(key) != value:
                doc.set(key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def _delete_custom_field(dt, fieldname):
    field_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "name")
    if not field_name:
        return
    doc = frappe.get_doc("Custom Field", field_name)
    doc.delete(ignore_permissions=True, force=1)


def _backfill_custom_snapp_code():
    if not frappe.db.has_column("Item", "custom_snapp_code"):
        return

    rows = frappe.get_all(
        "Item",
        filters=[["item_code", "like", "SNP-%"]],
        fields=["name", "item_code", "custom_snapp_code"],
        ignore_permissions=True,
        limit_page_length=0,
    )
    for row in rows:
        if (row.get("custom_snapp_code") or "").strip():
            continue
        code = (row.get("item_code") or "").strip()
        if not code:
            continue
        frappe.db.set_value("Item", row.get("name"), "custom_snapp_code", code, update_modified=False)


def execute():
    _ensure_custom_field("Item", CUSTOM_FIELD_DEF)
    _delete_custom_field("BOM", "restaurant_menu_item_ref")
    _backfill_custom_snapp_code()
    frappe.clear_cache()
    frappe.db.commit()
