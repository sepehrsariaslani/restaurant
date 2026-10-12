"""Persist the POS Profile used for each Restaurant management order."""

from __future__ import annotations

import frappe


FIELDNAME = "restaurant_pos_profile"


def execute():
	if not frappe.db.exists("DocType", "Sales Order") or not frappe.db.exists("DocType", "POS Profile"):
		return
	if frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": FIELDNAME}):
		return

	frappe.get_doc(
		{
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"fieldname": FIELDNAME,
			"label": "Restaurant POS Profile",
			"fieldtype": "Link",
			"options": "POS Profile",
			"insert_after": "customer",
			"read_only": 1,
			"hidden": 1,
			"no_copy": 1,
			"description": "POS Profile selected for this Restaurant order.",
		}
	).insert(ignore_permissions=True)
	frappe.clear_cache(doctype="Sales Order")
