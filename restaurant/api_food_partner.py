"""Food Partner order mapping facade for native Restaurant records."""

import frappe


@frappe.whitelist()
def get_snappfood_menu_products():
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import get_snappfood_menu_products as _get_menu_products

	_ensure_management_access()
	try:
		return _get_menu_products()
	except frappe.ValidationError as exc:
		return {"status": "error", "error": str(exc), "count": 0, "items": []}


@frappe.whitelist()
def update_snappfood_product_description(product_hash_id="", description=""):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import update_snappfood_product_description as _update_description

	_ensure_management_access()
	return _update_description(product_hash_id=product_hash_id, description=description)


@frappe.whitelist()
def update_snappfood_variation_description(variation_id="", description=""):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import update_snappfood_variation_description as _update_description

	_ensure_management_access()
	return _update_description(variation_id=variation_id, description=description)


@frappe.whitelist()
def set_snappfood_variation_status(variation_id="", active=None):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import set_snappfood_variation_status as _set_status

	_ensure_management_access()
	return _set_status(variation_id=variation_id, active=active)


@frappe.whitelist()
def set_snappfood_menu_item_status(item_id="", active=None):
	from restaurant.api import _ensure_management_access
	from restaurant.snapp_sync import set_snappfood_menu_item_status as _set_status

	_ensure_management_access()
	return _set_status(item_id=item_id, active=active)


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
		mapping_mode=payload.get("mapping_mode") or "modifier",
		product_id=payload.get("product_id") or "",
		variation_id=payload.get("variation_id") or "",
		product_hash_id=payload.get("product_hash_id") or "",
		variation_hash_id=payload.get("variation_hash_id") or "",
		menu_item_id=payload.get("menu_item_id") or "",
	)
