import frappe


def execute():
    has_replaceable_column = frappe.db.has_column("BOM Item", "restaurant_is_replaceable")
    has_allow_alternative_column = frappe.db.has_column("BOM Item", "allow_alternative_item")

    if has_replaceable_column and has_allow_alternative_column:
        frappe.db.sql(
            """
            UPDATE `tabBOM Item`
            SET allow_alternative_item = 1
            WHERE IFNULL(restaurant_is_replaceable, 0) = 1
              AND IFNULL(allow_alternative_item, 0) = 0
            """
        )

    if has_replaceable_column:
        frappe.db.sql_ddl("ALTER TABLE `tabBOM Item` DROP COLUMN `restaurant_is_replaceable`")

    frappe.clear_cache(doctype="BOM Item")
    frappe.db.commit()
