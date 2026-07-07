import frappe


FIELDNAME = "restaurant_is_default_selling"


def execute():
    if not frappe.db.exists("DocType", "Price List"):
        return

    payload = {
        "doctype": "Custom Field",
        "dt": "Price List",
        "fieldname": FIELDNAME,
        "label": "Default Selling Price List",
        "fieldtype": "Check",
        "insert_after": "selling",
        "default": "0",
        "module": "Restaurant",
    }

    existing_name = frappe.db.get_value("Custom Field", {"dt": "Price List", "fieldname": FIELDNAME}, "name")
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

    if frappe.db.has_column("Price List", FIELDNAME):
        current_default = frappe.db.get_value("Price List", {"selling": 1, FIELDNAME: 1}, "name")
        if not current_default:
            fallback = frappe.db.get_value("Price List", {"selling": 1}, "name")
            if fallback:
                frappe.db.set_value("Price List", fallback, FIELDNAME, 1, update_modified=True)

    frappe.clear_cache(doctype="Price List")
    frappe.db.commit()
