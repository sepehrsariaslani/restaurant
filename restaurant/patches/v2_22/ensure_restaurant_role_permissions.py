"""Install non-destructive DocType permission defaults for restaurant roles."""

from __future__ import annotations

import frappe
from frappe.permissions import add_permission

from restaurant.role_permissions import ROLE_DOCTYPE_PERMISSIONS


PERMISSION_FLAGS = (
	"read",
	"write",
	"create",
	"delete",
	"submit",
	"cancel",
	"amend",
	"report",
	"export",
	"import",
	"share",
	"print",
	"email",
	"select",
)


def _existing_custom_permission(doctype: str, role: str):
	return frappe.db.get_value(
		"Custom DocPerm",
		{"parent": doctype, "role": role, "permlevel": 0, "if_owner": 0},
		"name",
	)


def ensure_restaurant_role_permissions() -> dict[str, list[str]]:
	created: list[str] = []
	preserved: list[str] = []
	for role, doctype_map in ROLE_DOCTYPE_PERMISSIONS.items():
		if not frappe.db.exists("Role", role):
			continue
		for doctype, permissions in doctype_map.items():
			if not frappe.db.exists("DocType", doctype):
				continue
			name = _existing_custom_permission(doctype, role)
			if name:
				preserved.append(f"{role}: {doctype}")
				continue

			add_permission(doctype, role, ptype="read")
			name = _existing_custom_permission(doctype, role)
			if not name:
				continue
			fields = {flag: int(flag in permissions) for flag in PERMISSION_FLAGS}
			frappe.db.set_value("Custom DocPerm", name, fields, update_modified=False)
			created.append(f"{role}: {doctype}")
			frappe.clear_cache(doctype=doctype)

	return {"created": created, "preserved": preserved}


def execute():
	return ensure_restaurant_role_permissions()
