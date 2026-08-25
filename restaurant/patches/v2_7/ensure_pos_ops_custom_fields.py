"""Ensure feature-pack custom fields exist after migrate:

- Item: restaurant_out_of_stock, restaurant_packaging_price
- Sales Order: restaurant_packaging_fee
- Restaurant Web Settings: packaging + work-shift settings block
"""

import frappe


def execute():
	try:
		from restaurant import api_feature_pack

		api_feature_pack._fp_ensure_ops_ready()
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Restaurant v2_7 ensure_pos_ops_custom_fields failed",
		)
