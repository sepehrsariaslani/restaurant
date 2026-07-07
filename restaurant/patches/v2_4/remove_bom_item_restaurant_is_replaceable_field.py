import frappe


def execute():
    custom_field_name = frappe.db.get_value(
        "Custom Field",
        {"dt": "BOM Item", "fieldname": "restaurant_is_replaceable"},
        "name",
    )
    if not custom_field_name:
        return

    frappe.delete_doc("Custom Field", custom_field_name, force=1, ignore_permissions=True)
    frappe.clear_cache(doctype="BOM Item")
    frappe.db.commit()
