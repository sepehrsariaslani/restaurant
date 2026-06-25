import frappe

def execute():
    """Main migration: create Restaurant Item Tag doctype + child table + migrate data"""
    
    # 1. Create Restaurant Item Tag doctype
    if not frappe.db.exists("DocType", "Restaurant Item Tag"):
        doc = frappe.new_doc("DocType")
        doc.name = "Restaurant Item Tag"
        doc.module = "Restaurant"
        doc.custom = 1
        doc.is_tree = 0
        doc.editable_grid = 1
        doc.track_changes = 0
        doc.document_type = "Document"
        doc.append("fields", {
            "fieldname": "title",
            "fieldtype": "Data",
            "label": "عنوان تگ",
            "reqd": 1,
            "in_list_view": 1,
            "in_standard_filter": 1,
            "search_index": 1,
        })
        doc.append("fields", {
            "fieldname": "color",
            "fieldtype": "Color",
            "label": "رنگ",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created: Restaurant Item Tag")
    else:
        print("Exists: Restaurant Item Tag")

    # 2. Create child table
    if not frappe.db.exists("DocType", "Restaurant Item Tag Link"):
        doc = frappe.new_doc("DocType")
        doc.name = "Restaurant Item Tag Link"
        doc.module = "Restaurant"
        doc.custom = 1
        doc.istable = 1
        doc.append("fields", {
            "fieldname": "tag",
            "fieldtype": "Link",
            "label": "تگ",
            "options": "Restaurant Item Tag",
            "in_list_view": 1,
            "reqd": 1,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Created: Restaurant Item Tag Link")
    else:
        print("Exists: Restaurant Item Tag Link")

    # 3. Add Table field on Item
    fname = "restaurant_item_tag_table"
    if not frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": fname}):
        try:
            frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Item",
                "fieldname": fname,
                "label": "تگ‌های محصول",
                "fieldtype": "Table",
                "options": "Restaurant Item Tag Link",
                "insert_after": "restaurant_allergen_tags",
            }).insert(ignore_permissions=True)
            frappe.clear_cache(doctype="Item")
            print("Added: restaurant_item_tag_table")
        except Exception as e:
            print(f"Error adding field: {e}")
    else:
        print("Exists: restaurant_item_tag_table")

    # 4. Migrate data
    old = "restaurant_item_tags"
    if not frappe.db.has_column("Item", old):
        print(f"Old field '{old}' does not exist")
        return

    items = frappe.get_all("Item", filters={old: ["!=", ""]}, fields=["name", old], limit_page_length=5000)
    migrated = 0
    
    for ir in items:
        tags_str = (ir.get(old) or "").strip()
        if not tags_str:
            continue
        tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
        if not tag_names:
            continue

        # Build tag links without loading full doc (to avoid broken child table issues)
        links = []
        for tn in tag_names:
            ev = frappe.db.get_value("Restaurant Item Tag", {"title": tn}, "name")
            if ev:
                tdn = ev
            else:
                td = frappe.new_doc("Restaurant Item Tag")
                td.title = tn
                td.insert(ignore_permissions=True)
                tdn = td.name
            links.append(tdn)

        # Insert child table rows directly via SQL
        for tdn in links:
            exists = frappe.db.sql("""
                SELECT name FROM `tabRestaurant Item Tag Link` 
                WHERE parent=%s AND parenttype='Item' AND parentfield=%s AND tag=%s
            """, (ir.name, fname, tdn))
            if not exists:
                frappe.db.sql("""
                    INSERT INTO `tabRestaurant Item Tag Link` 
                    (name, parent, parenttype, parentfield, tag, idx, creation, modified, modified_by, owner, docstatus)
                    VALUES (%s, %s, 'Item', %s, %s, %s, NOW(), NOW(), 'Administrator', 'Administrator', 0)
                """, (frappe.generate_hash(length=10), ir.name, fname, tdn, len(links)))
        
        migrated += 1

    frappe.db.commit()
    print(f"Migrated: {migrated}/{len(items)} items")
