import frappe

def execute():
    """Step 1: Clean up bad custom fields"""
    bad = frappe.db.sql("""
        SELECT name, fieldname FROM `tabCustom Field` 
        WHERE dt='Item' AND fieldname IN ('restaurant_item_tag_table', 'restaurant_item_tag_links')
    """, as_dict=True)
    for b in bad:
        frappe.delete_doc("Custom Field", b['name'], ignore_permissions=True)
        print(f"Deleted: {b['fieldname']}")
    frappe.db.commit()
    print(f"Cleaned {len(bad)} fields")
