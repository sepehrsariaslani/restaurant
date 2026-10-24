"""Add the opt-in Food Partner production and delivery automation setting."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	create_custom_fields(
		{
			"Restaurant Web Settings": [
				{
					"fieldname": "snapp_auto_sync_production_delivery",
					"label": "ساخت خودکار تولید و حوالهٔ تحویل",
					"fieldtype": "Check",
					"default": "0",
					"insert_after": "snapp_require_item_mapping",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Restaurant Web Settings")
	frappe.db.commit()
