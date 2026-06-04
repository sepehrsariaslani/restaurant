import frappe


def execute():
    if not frappe.db.exists("DocType", "BOM Item"):
        return
    if not frappe.db.has_column("BOM Item", "restaurant_is_replaceable"):
        return

    if frappe.db.has_column("BOM Item", "allow_alternative_item"):
        frappe.db.sql(
            """
            UPDATE `tabBOM Item`
            SET restaurant_is_replaceable = 1
            WHERE IFNULL(allow_alternative_item, 0) = 1
            """
        )

    frappe.db.commit()
