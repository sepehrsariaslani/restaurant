import frappe


def execute():
    if not frappe.db.exists("DocType", "Restaurant Print Brand Settings"):
        return

    defaults = {
        "brand_name": "رستوران نمونه دن فلو",
        "brand_subtitle": "سامانه مدیریت رستوران",
        "show_brand_subtitle": 1,
        "header_background_color": "#4A2522",
        "header_text_color": "#FFFFFF",
        "accent_color": "#C08A2A",
        "table_header_background_color": "#F7F2E3",
        "border_color": "#D8C8B3",
        "footer_text": "این نسخه برای چاپ داخلی مجموعه است.",
    }

    changed = False
    for fieldname, value in defaults.items():
        current = frappe.db.get_single_value("Restaurant Print Brand Settings", fieldname)
        if current in (None, ""):
            frappe.db.set_single_value("Restaurant Print Brand Settings", fieldname, value, update_modified=False)
            changed = True

    if changed:
        frappe.db.commit()

    frappe.clear_cache(doctype="Restaurant Print Brand Settings")
