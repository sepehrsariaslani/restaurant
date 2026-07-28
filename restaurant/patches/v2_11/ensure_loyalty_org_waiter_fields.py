"""Ensure customer-club extras and organizational/waiter custom fields
exist after migrate:

- Customer: customer kind (حقیقی/حقوقی/سازمانی), organization link and
  loyalty points balance
- Sales Order: points earned, organization/member binding, waiter,
  consolidated org invoice link, courier route index
- Sales Invoice: organization & contract links
- Address: guidance video URL
- Restaurant Web Settings: loyalty point earning/redemption/expiry tiers
"""

import frappe


def _run(label, fn):
	try:
		fn()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Restaurant v2_11 {label} failed")


def execute():
	try:
		from restaurant import api_club

		_run("club fields", api_club._club_ensure_ops_ready)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant v2_11 club import failed")

	try:
		from restaurant import api_org

		_run("org fields", api_org._org_ensure_ops_ready)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant v2_11 org import failed")

	try:
		from restaurant import api_ops

		_run("ops route fields", api_ops._ops_ensure_sales_order_fields)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant v2_11 ops import failed")

	try:
		from restaurant import api as restaurant_api

		_run("address video field", restaurant_api._ensure_checkout_address_fields)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant v2_11 address fields failed")

	frappe.db.commit()
