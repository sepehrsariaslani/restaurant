"""Add company-scoped Moadian settings and encrypt the legacy singleton token."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.utils.password import set_encrypted_password


def execute():
	if not frappe.db.exists("DocType", "Company"):
		return

	fields = [
		{
			"fieldname": "custom_moadian_section",
			"label": "تنظیمات اتصال مؤدیان",
			"fieldtype": "Section Break",
			"insert_after": "tax_id",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_enabled",
			"label": "Moadian Connection Enabled",
			"fieldtype": "Check",
			"insert_after": "custom_moadian_section",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_sandbox",
			"label": "Moadian Sandbox Mode",
			"fieldtype": "Check",
			"insert_after": "custom_moadian_enabled",
			"default": "1",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_api_url",
			"label": "Moadian API URL",
			"fieldtype": "Data",
			"insert_after": "custom_moadian_sandbox",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_memory_code",
			"label": "Moadian Tax Memory Code",
			"fieldtype": "Data",
			"insert_after": "custom_moadian_api_url",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_auth_token",
			"label": "Moadian API Token",
			"fieldtype": "Password",
			"insert_after": "custom_moadian_memory_code",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_economic_code",
			"label": "Moadian Economic Code",
			"fieldtype": "Data",
			"insert_after": "custom_moadian_auth_token",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
		{
			"fieldname": "custom_moadian_auto_submit",
			"label": "Moadian Daily Auto Submit",
			"fieldtype": "Check",
			"insert_after": "custom_moadian_economic_code",
			"hidden": 1,
			"read_only": 1,
			"no_copy": 1,
		},
	]
	create_custom_fields({"Company": fields}, ignore_validate=True)
	_encrypt_legacy_singleton_token()
	frappe.clear_cache(doctype="Company")


def _encrypt_legacy_singleton_token():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	token = frappe.db.get_single_value(
		"Restaurant Web Settings",
		"restaurant_tax_auth_token",
		cache=False,
	)
	token = str(token or "").strip()
	if not token or set(token) == {"*"}:
		return

	set_encrypted_password(
		"Restaurant Web Settings",
		"Restaurant Web Settings",
		token,
		"restaurant_tax_auth_token",
	)
	frappe.db.set_single_value(
		"Restaurant Web Settings",
		"restaurant_tax_auth_token",
		"*" * len(token),
		update_modified=False,
	)
