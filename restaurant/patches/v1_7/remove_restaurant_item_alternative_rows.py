import frappe


def _delete_custom_field_if_exists(dt, fieldname):
    name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": fieldname}, "name")
    if name:
        frappe.delete_doc("Custom Field", name, force=1, ignore_permissions=True)


def execute():
    _delete_custom_field_if_exists("BOM", "restaurant_item_alternative_rows")
    _delete_custom_field_if_exists("BOM Item", "restaurant_alternative_items")

    if frappe.db.exists("DocType", "Restaurant BOM Item Alternative"):
        frappe.delete_doc("DocType", "Restaurant BOM Item Alternative", force=1, ignore_permissions=True)

    frappe.db.commit()
