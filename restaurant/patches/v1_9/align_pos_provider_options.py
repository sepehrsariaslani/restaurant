import frappe


def execute():
    custom_name = frappe.db.get_value(
        "Custom Field",
        {"dt": "Restaurant Web Settings", "fieldname": "restaurant_pos_payment_provider"},
        "name",
    )
    if custom_name:
        doc = frappe.get_doc("Custom Field", custom_name)
        options = "manual\nlocal_node\nwebhook"
        changed = False
        if doc.options != options:
            doc.options = options
            changed = True
        if doc.default != "local_node":
            doc.default = "local_node"
            changed = True
        if changed:
            doc.save(ignore_permissions=True)

    frappe.clear_cache()
    frappe.db.commit()
