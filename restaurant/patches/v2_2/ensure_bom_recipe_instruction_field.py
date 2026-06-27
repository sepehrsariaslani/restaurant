import frappe


def _ensure_custom_field(fieldname, values):
	if frappe.db.exists("Custom Field", {"dt": "BOM", "fieldname": fieldname}):
		custom_field = frappe.get_doc("Custom Field", {"dt": "BOM", "fieldname": fieldname})
		changed = False
		for key, value in values.items():
			if custom_field.get(key) != value:
				custom_field.set(key, value)
				changed = True
		if changed:
			custom_field.save(ignore_permissions=True)
		return

	custom_field = frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "BOM",
			"fieldname": fieldname,
			**values,
		}
	)
	custom_field.insert(ignore_permissions=True)


def execute():
	if not frappe.db.exists("DocType", "BOM"):
		return

	_ensure_custom_field(
		"restaurant_recipe_instruction",
		{
			"label": "Restaurant Recipe Instruction",
			"fieldtype": "Small Text",
			"insert_after": "is_default",
			"translatable": 0,
			"read_only": 0,
			"hidden": 0,
			"print_hide": 1,
			"no_copy": 0,
		},
	)

	frappe.clear_cache(doctype="BOM")
