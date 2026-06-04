import frappe


SETTINGS_FIELDS = [
    {
        "fieldname": "restaurant_menu_highlight_section",
        "label": "بلاک ویژه منو",
        "fieldtype": "Section Break",
        "insert_after": "primary_cta_label",
    },
    {
        "fieldname": "restaurant_menu_highlight_enabled",
        "label": "نمایش بلاک ویژه در منو",
        "fieldtype": "Check",
        "default": "1",
        "insert_after": "restaurant_menu_highlight_section",
    },
    {
        "fieldname": "restaurant_menu_highlight_title",
        "label": "عنوان بلاک ویژه",
        "fieldtype": "Data",
        "default": "ویژه و پرفروش",
        "insert_after": "restaurant_menu_highlight_enabled",
    },
    {
        "fieldname": "restaurant_menu_highlight_show_featured",
        "label": "نمایش آیتم های ویژه",
        "fieldtype": "Check",
        "default": "1",
        "insert_after": "restaurant_menu_highlight_title",
    },
    {
        "fieldname": "restaurant_menu_highlight_featured_limit",
        "label": "تعداد آیتم ویژه",
        "fieldtype": "Int",
        "default": "10",
        "insert_after": "restaurant_menu_highlight_show_featured",
    },
    {
        "fieldname": "restaurant_menu_highlight_show_best_seller",
        "label": "نمایش آیتم های پرفروش",
        "fieldtype": "Check",
        "default": "1",
        "insert_after": "restaurant_menu_highlight_featured_limit",
    },
    {
        "fieldname": "restaurant_menu_highlight_best_seller_limit",
        "label": "تعداد آیتم پرفروش",
        "fieldtype": "Int",
        "default": "10",
        "insert_after": "restaurant_menu_highlight_show_best_seller",
    },
]

ITEM_FIELDS = [
    {
        "fieldname": "restaurant_is_best_seller",
        "label": "Restaurant Is Best Seller",
        "fieldtype": "Check",
        "default": "0",
        "insert_after": "restaurant_is_featured",
    },
]


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {"doctype": "Custom Field", "dt": dt, "module": "Restaurant", **field_def}

    if existing_name:
        doc = frappe.get_doc("Custom Field", existing_name)
        changed = False
        for key, value in payload.items():
            if key == "doctype":
                continue
            if doc.get(key) != value:
                doc.set(key, value)
                changed = True
        if changed:
            doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def execute():
    if frappe.db.exists("DocType", "Restaurant Web Settings"):
        for field_def in SETTINGS_FIELDS:
            _ensure_custom_field("Restaurant Web Settings", field_def)

    if frappe.db.exists("DocType", "Item"):
        for field_def in ITEM_FIELDS:
            _ensure_custom_field("Item", field_def)

    frappe.clear_cache(doctype="Restaurant Web Settings")
    frappe.clear_cache(doctype="Item")
    frappe.db.commit()
