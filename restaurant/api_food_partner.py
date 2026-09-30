"""Food Partner order mapping facade for native Restaurant records."""

import frappe


@frappe.whitelist()
def get_snappfood_modifier_groups(item_name=""):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import get_snappfood_modifier_groups as _get_modifier_groups

	_ensure_management_access()
	return _get_modifier_groups(item_name=item_name)


@frappe.whitelist()
def save_snappfood_modifier_mapping(payload=None):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import save_snappfood_modifier_mapping as _save_modifier_mapping

	_ensure_management_access()
	if isinstance(payload, str):
		payload = frappe.parse_json(payload or "{}")
	if not isinstance(payload, dict):
		payload = {}
	return _save_modifier_mapping(
		item_name=payload.get("item_name") or "",
		parent_item=payload.get("parent_item") or "",
		group_name=payload.get("group_name") or "",
		option_name=payload.get("option_name") or "",
		product_id=payload.get("product_id") or "",
		variation_id=payload.get("variation_id") or "",
		product_hash_id=payload.get("product_hash_id") or "",
		variation_hash_id=payload.get("variation_hash_id") or "",
		menu_item_id=payload.get("menu_item_id") or "",
	)
