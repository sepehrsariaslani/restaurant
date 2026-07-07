import frappe


def execute():
    payload = {
        "doctype": "Custom Field",
        "dt": "BOM Item",
        "fieldname": "restaurant_can_remove",
        "label": "قابل حذف توسط مشتری",
        "fieldtype": "Check",
        "insert_after": "restaurant_is_included_by_default",
        "default": "0",
        "module": "Restaurant",
    }

    existing_name = frappe.db.get_value(
        "Custom Field",
        {"dt": "BOM Item", "fieldname": "restaurant_can_remove"},
        "name",
    )

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
    else:
        frappe.get_doc(payload).insert(ignore_permissions=True)

    frappe.clear_cache(doctype="BOM Item")
    frappe.db.commit()
