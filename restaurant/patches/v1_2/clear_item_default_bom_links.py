import frappe
from frappe.utils import cint


def execute():
    if not frappe.db.exists("DocType", "Item"):
        return
    if not frappe.db.has_column("Item", "default_bom"):
        return

    has_restaurant_enabled = frappe.db.has_column("Item", "restaurant_enabled")
    fields = ["name", "default_bom"]
    if has_restaurant_enabled:
        fields.append("restaurant_enabled")

    rows = frappe.get_all(
        "Item",
        filters={"default_bom": ["!=", ""]},
        fields=fields,
        ignore_permissions=True,
    )

    changed = 0
    for row in rows:
        bom_name = (row.get("default_bom") or "").strip()
        if not bom_name:
            continue

        is_restaurant_item = cint(row.get("restaurant_enabled")) == 1 if has_restaurant_enabled else False
        is_stale_link = not frappe.db.exists("BOM", bom_name)
        if not is_restaurant_item and not is_stale_link:
            continue

        frappe.db.set_value("Item", row.name, "default_bom", "", update_modified=False)
        changed += 1

    if changed:
        frappe.clear_cache()
        frappe.db.commit()
