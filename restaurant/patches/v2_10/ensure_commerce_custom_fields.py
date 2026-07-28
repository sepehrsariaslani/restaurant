"""Ensure commerce-pack custom fields exist after migrate:

- Customer: primary branch link
- Warehouse: branch link
- Item: food-court vendor link
- Restaurant Web Settings: reservation, moadian (tax), call-center/VOIP
  and kiosk settings sections
"""

import frappe


def _run(module_name, fn_name, label):
	try:
		module = __import__(f"restaurant.{module_name}", fromlist=[fn_name])
		getattr(module, fn_name)()
	except Exception:
		frappe.log_error(frappe.get_traceback(), f"Restaurant v2_10 {label} failed")


def execute():
	_run("api_reserve", "_rsv_ensure_ops_ready", "reservation fields")
	_run("api_tax", "_tax_ensure_ops_ready", "tax (moadian) fields")
	_run("api_branch", "_br_ensure_ops_ready", "branch fields")
	_run("api_callcenter", "_cc_ensure_ops_ready", "callcenter fields")
	_run("api_kiosk", "_ko_ensure_ops_ready", "kiosk/vendor fields")
	frappe.db.commit()
