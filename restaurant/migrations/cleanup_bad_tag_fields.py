import frappe

def execute():
    """Clean up bad custom fields from previous failed migration"""
    bad_fields = frappe.db.sql("""
        SELECT name, fieldname 
        FROM `tabCustom Field` 
        WHERE dt='Item' AND fieldname IN ('restaurant_item_tag_table', 'restaurant_item_tag_links')
    """, as_dict=True)
    
    for bf in bad_fields:
        print(f"Deleting: {bf['name']} ({bf['fieldname']})")
        frappe.delete_doc("Custom Field", bf['name'], ignore_permissions=True)
    
    frappe.db.commit()
    print(f"Cleaned up {len(bad_fields)} bad custom fields")
