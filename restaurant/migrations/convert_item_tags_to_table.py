import frappe

def execute():
    """One-time migration: convert restaurant_item_tags from Small Text to child table"""
    
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

    # 2. Create child table (istable=1) - link table
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

    # 3. Remove old Table MultiSelect field if exists
    old_fieldname = "restaurant_item_tag_links"
    old_cf = frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": old_fieldname})
    if old_cf:
        frappe.delete_doc("Custom Field", old_cf, ignore_permissions=True)
        frappe.clear_cache(doctype="Item")
        print("Removed old field: restaurant_item_tag_links")

    # 4. Add Table field on Item (istable child table directly)
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
            print(f"Warning adding field: {e}")
    else:
        print("Exists: restaurant_item_tag_table")

    # 5. Migrate data from old comma-separated field
    old = "restaurant_item_tags"
    if not frappe.db.has_column("Item", old):
        print(f"Old field '{old}' does not exist, skipping migration")
        return

    items = frappe.get_all(
        "Item",
        filters={old: ["!=", ""]},
        fields=["name", old],
        limit_page_length=5000,
    )

    migrated = 0
    for ir in items:
        tags_str = (ir.get(old) or "").strip()
        if not tags_str:
            continue
        tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]
        if not tag_names:
            continue

        item_doc = frappe.get_doc("Item", ir.name)
        existing_links = item_doc.get(fname) or []

        for tn in tag_names:
            ev = frappe.db.get_value("Restaurant Item Tag", {"title": tn}, "name")
            if ev:
                tdn = ev
            else:
                td = frappe.new_doc("Restaurant Item Tag")
                td.title = tn
                td.insert(ignore_permissions=True)
                tdn = td.name

            if not any(l.get("tag") == tdn for l in existing_links):
                item_doc.append(fname, {"tag": tdn})
                existing_links = item_doc.get(fname) or []

        try:
            item_doc.save(ignore_permissions=True)
            migrated += 1
        except Exception as e:
            print(f"  Err {ir.name}: {e}")

    frappe.db.commit()
    print(f"Migrated: {migrated}/{len(items)} items")
