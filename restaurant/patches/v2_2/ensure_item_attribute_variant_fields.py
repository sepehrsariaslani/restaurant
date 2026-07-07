import frappe


CUSTOM_FIELDS = {
    "Item Attribute": [
        {
            "fieldname": "restaurant_show_in_website",
            "label": "نمایش در سایت",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "numeric_values",
        },
        {
            "fieldname": "restaurant_selection_only",
            "label": "جزئیات انتخابی (فقط داخل محصول)",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_show_in_website",
        },
    ],
    "Item Attribute Value": [
        {
            "fieldname": "restaurant_is_default",
            "label": "پیش فرض",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "abbr",
        },
    ],
}


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {"doctype": "Custom Field", "dt": dt, "module": "Restaurant", **field_def}

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


def execute():
    for dt, field_defs in CUSTOM_FIELDS.items():
        for field_def in field_defs:
            _ensure_custom_field(dt, field_def)

    frappe.clear_cache()
    frappe.db.commit()

