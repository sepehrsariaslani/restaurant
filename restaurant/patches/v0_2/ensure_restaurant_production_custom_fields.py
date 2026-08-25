import frappe


CUSTOM_FIELDS = {
    "Item": [
        {
            "fieldname": "restaurant_allow_customization",
            "label": "Restaurant Allow Customization",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_modifier_groups",
        },
        {
            "fieldname": "restaurant_bom_template",
            "label": "Restaurant BOM Template",
            "fieldtype": "Link",
            "options": "BOM",
            "insert_after": "restaurant_allow_customization",
        },
        {
            "fieldname": "restaurant_recipe_yield_qty",
            "label": "Restaurant Recipe Yield Qty",
            "fieldtype": "Float",
            "default": "1",
            "insert_after": "restaurant_bom_template",
        },
        {
            "fieldname": "restaurant_recipe_uom",
            "label": "Restaurant Recipe UOM",
            "fieldtype": "Link",
            "options": "UOM",
            "insert_after": "restaurant_recipe_yield_qty",
        },
        {
            "fieldname": "restaurant_nutrition_kcal",
            "label": "Restaurant Nutrition Kcal",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_recipe_uom",
        },
        {
            "fieldname": "restaurant_nutrition_protein_g",
            "label": "Restaurant Nutrition Protein (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_kcal",
        },
        {
            "fieldname": "restaurant_nutrition_carb_g",
            "label": "Restaurant Nutrition Carb (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_protein_g",
        },
        {
            "fieldname": "restaurant_nutrition_fat_g",
            "label": "Restaurant Nutrition Fat (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_carb_g",
        },
        {
            "fieldname": "restaurant_requires_bom",
            "label": "Restaurant Requires BOM",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_nutrition_fat_g",
        },
        {
            "fieldname": "restaurant_auto_add_to_order",
            "label": "Restaurant Auto Add To Order",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_requires_bom",
        },
        {
            "fieldname": "restaurant_auto_add_qty",
            "label": "Restaurant Auto Add Qty",
            "fieldtype": "Float",
            "default": "1",
            "insert_after": "restaurant_auto_add_to_order",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_include_service_items",
            "label": "Restaurant Include Service Items",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_payload_json",
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_pricing_breakdown_json",
            "label": "Restaurant Pricing Breakdown JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_selection_summary",
        },
        {
            "fieldname": "restaurant_extra_charge",
            "label": "Restaurant Extra Charge",
            "fieldtype": "Currency",
            "default": "0",
            "insert_after": "restaurant_pricing_breakdown_json",
        },
        {
            "fieldname": "restaurant_production_ticket",
            "label": "Restaurant Production Ticket",
            "fieldtype": "Link",
            "options": "Restaurant Production Ticket",
            "insert_after": "restaurant_extra_charge",
        },
        {
            "fieldname": "restaurant_is_auto_added",
            "label": "Restaurant Is Auto Added",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_production_ticket",
        },
        {
            "fieldname": "restaurant_requires_production",
            "label": "Restaurant Requires Production",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_is_auto_added",
        },
    ],
    "Work Order": [
        {
            "fieldname": "restaurant_sales_order",
            "label": "Restaurant Sales Order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "insert_after": "sales_order",
        },
        {
            "fieldname": "restaurant_sales_order_item",
            "label": "Restaurant Sales Order Item",
            "fieldtype": "Data",
            "insert_after": "restaurant_sales_order",
        },
        {
            "fieldname": "restaurant_order_code",
            "label": "Restaurant Order Code",
            "fieldtype": "Data",
            "insert_after": "restaurant_sales_order_item",
        },
        {
            "fieldname": "restaurant_production_ticket",
            "label": "Restaurant Production Ticket",
            "fieldtype": "Link",
            "options": "Restaurant Production Ticket",
            "insert_after": "restaurant_order_code",
        },
        {
            "fieldname": "restaurant_customization_json",
            "label": "Restaurant Customization JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_production_ticket",
        },
    ],
}


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
        **field_def,
    }

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
    for dt, field_defs in CUSTOM_FIELDS.items():
        for field_def in field_defs:
            _ensure_custom_field(dt, field_def)

    frappe.clear_cache()
    frappe.db.commit()
