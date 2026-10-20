"""Add a separately encrypted account token for Food Partner order actions."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	create_custom_fields(
		{
			"Restaurant Web Settings": [
				{
					"fieldname": "snapp_access_token",
					"label": "Food Partner Order Access Token",
					"fieldtype": "Password",
					"insert_after": "snapp_bearer_token",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Restaurant Web Settings")
	frappe.db.commit()
