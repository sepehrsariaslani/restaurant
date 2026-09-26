import frappe


ITEM_FIELDS = [
	{
		"fieldname": "restaurant_nutrition_verified",
		"label": "Restaurant Nutrition Verified",
		"fieldtype": "Check",
		"default": "0",
		"insert_after": "restaurant_nutrition_fat_g",
	},
	{
		"fieldname": "restaurant_allergen_reviewed",
		"label": "Restaurant Allergens Reviewed",
		"fieldtype": "Check",
		"default": "0",
		"insert_after": "restaurant_allergen_tags",
	},
	{
		"fieldname": "restaurant_meal_slots",
		"label": "Restaurant Meal Slots",
		"fieldtype": "Small Text",
		"insert_after": "restaurant_allergen_reviewed",
	},
	{
		"fieldname": "restaurant_ingredient_tags",
		"label": "Restaurant Ingredient Tags",
		"fieldtype": "Small Text",
		"insert_after": "restaurant_meal_slots",
	},
	{
		"fieldname": "restaurant_ingredients_reviewed",
		"label": "Restaurant Ingredients Reviewed",
		"fieldtype": "Check",
		"default": "0",
		"insert_after": "restaurant_ingredient_tags",
	},
]


def execute():
	for field_def in ITEM_FIELDS:
		name = frappe.db.get_value("Custom Field", {"dt": "Item", "fieldname": field_def["fieldname"]}, "name")
		payload = {"doctype": "Custom Field", "dt": "Item", "module": "Restaurant", **field_def}
		if name:
			doc = frappe.get_doc("Custom Field", name)
			for key, value in payload.items():
				if key != "doctype" and doc.get(key) != value:
					doc.set(key, value)
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(payload).insert(ignore_permissions=True)
	frappe.clear_cache(doctype="Item")
	frappe.db.commit()
