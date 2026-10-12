"""Create the native Restaurant roles without changing existing role setup."""

from __future__ import annotations

import frappe


RESTAURANT_ROLES = (
	"Restaurant Manager",
	"Restaurant Supervisor",
	"Restaurant Cashier",
	"Restaurant Waiter",
	"Restaurant Chef",
)


def execute():
	created = []
	for role_name in RESTAURANT_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"is_custom": 1,
				"desk_access": 1,
			}
		).insert(ignore_permissions=True)
		created.append(role_name)

	if created:
		frappe.clear_cache(doctype="Role")
	return {"created": created}
