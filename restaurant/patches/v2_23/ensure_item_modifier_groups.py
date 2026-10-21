"""Allow native Item add-ons without inventing a manufacturing recipe."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Item"):
		return
	create_custom_fields({"Item": [{
		"fieldname": "restaurant_modifier_groups",
		"label": "گروه‌های افزودنی رستوران",
		"fieldtype": "Table",
		"options": "Restaurant Menu Item Modifier",
		"insert_after": "restaurant_food_partner_modifier_mappings",
		"description": "افزودنی‌های مستقل از فرمول؛ گروه‌های فرمول BOM نیز حفظ می‌شوند.",
	}]}, ignore_validate=True)
	frappe.clear_cache(doctype="Item")
	frappe.db.commit()
