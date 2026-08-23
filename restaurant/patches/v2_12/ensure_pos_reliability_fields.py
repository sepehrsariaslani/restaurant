import frappe


FIELDNAME = "restaurant_pos_client_order_key"


def execute():
    if frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": FIELDNAME}):
        return

    frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": FIELDNAME,
            "label": "POS Client Order Key",
            "fieldtype": "Data",
            "insert_after": "restaurant_secondary_customer",
            "read_only": 1,
            "no_copy": 1,
            "unique": 1,
            "description": "Idempotency key used when replaying offline POS orders.",
        }
    ).insert(ignore_permissions=True)
    frappe.clear_cache(doctype="Sales Order")
