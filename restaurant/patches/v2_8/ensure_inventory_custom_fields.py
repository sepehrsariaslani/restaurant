"""Ensure inventory-pack custom fields exist after migrate:

- Item: restaurant_raw_material, restaurant_purchase_rate, restaurant_default_supplier
- Stock Entry: restaurant_movement_kind, restaurant_reference_note
- Restaurant Web Settings: inventory defaults (warehouses, waste handling)
"""

import frappe


def execute():
	try:
		from restaurant import api_inventory

		api_inventory._inv_ensure_ops_ready()
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Restaurant v2_8 ensure_inventory_custom_fields failed",
		)
