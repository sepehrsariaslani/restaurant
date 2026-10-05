"""Keep Food Partner choice mappings with their native parent Item."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Item"):
		return

	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "restaurant_food_partner_modifier_mappings",
					"label": "نگاشت Modifierهای Food Partner",
					"fieldtype": "Long Text",
					"insert_after": "restaurant_external_mapping_status",
					"hidden": 1,
					"read_only": 1,
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Item")
	frappe.db.commit()
