import frappe


CUSTOM_FIELDS = {
    "Item": [
        {
            "fieldname": "restaurant_nutrition_sugar_g",
            "label": "Restaurant Nutrition Sugar (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_carb_g",
        }
    ],
    "BOM": [
        {
            "fieldname": "restaurant_nutrition_kcal",
            "label": "Restaurant Nutrition Kcal",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_menu_item_ref",
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
            "fieldname": "restaurant_nutrition_sugar_g",
            "label": "Restaurant Nutrition Sugar (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_carb_g",
        },
        {
            "fieldname": "restaurant_nutrition_fat_g",
            "label": "Restaurant Nutrition Fat (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_sugar_g",
        },
    ],
    "BOM Item": [
        {
            "fieldname": "restaurant_nutrition_kcal",
            "label": "Restaurant Nutrition Kcal",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_multiplier_qty",
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
            "fieldname": "restaurant_nutrition_sugar_g",
            "label": "Restaurant Nutrition Sugar (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_carb_g",
        },
        {
            "fieldname": "restaurant_nutrition_fat_g",
            "label": "Restaurant Nutrition Fat (g)",
            "fieldtype": "Float",
            "default": "0",
            "insert_after": "restaurant_nutrition_sugar_g",
        },
    ],
}


def _ensure_custom_field(dt, field_def):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
        "module": "Restaurant",
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
