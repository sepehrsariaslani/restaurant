"""Ensure club & ops custom fields exist after migrate:

- Customer: membership/referral codes, birth date, tier & segment
- Sales Order: referral code, cashback flag, kitchen prep timestamps,
  courier assignment & third-party delivery fields
- Restaurant Web Settings: customer club, SMS, survey alert and
  third-party delivery provider settings
"""

import frappe


def execute():
	try:
		from restaurant import api_club

		api_club._club_ensure_ops_ready()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Restaurant v2_9 ensure_club_custom_fields failed",
		)
	try:
		from restaurant import api_ops

		api_ops._ops_ensure_ops_ready()
		frappe.db.commit()
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"Restaurant v2_9 ensure_ops_custom_fields failed",
		)
