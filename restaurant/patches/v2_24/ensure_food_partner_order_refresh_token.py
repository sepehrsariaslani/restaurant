"""Add encrypted Food Partner refresh token for order actions."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	create_custom_fields(
		{
			"Restaurant Web Settings": [
				{
					"fieldname": "snapp_order_refresh_token",
					"label": "Food Partner Order Refresh Token",
					"fieldtype": "Password",
					"insert_after": "snapp_access_token",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.clear_cache(doctype="Restaurant Web Settings")
	frappe.db.commit()
