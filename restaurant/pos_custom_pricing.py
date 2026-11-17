"""Line scoped custom pricing for the management POS.

Overrides are applied to a server-calculated line and returned as part of its
pricing/customization snapshot. This module intentionally has no Frappe or
database dependency: it cannot change shared Item or Item Price records.
"""

from copy import deepcopy
import math


_ALLOWED_KEYS = {"base_unit_price", "modifier_unit_prices", "ingredient_unit_prices"}


def _number(value, label):
	if isinstance(value, bool):
		raise ValueError(f"{label} must be a finite number.")
	try:
		result = float(value)
	except (TypeError, ValueError, OverflowError):
		raise ValueError(f"{label} must be a finite number.")
	if not math.isfinite(result):
		raise ValueError(f"{label} must be a finite number.")
	return result


def _price(value, label):
	result = _number(value, label)
	if result < 0:
		raise ValueError(f"{label} must be a finite non-negative price.")
	return result


def _rows(value, label):
	if value in (None, ""):
		return []
	if not isinstance(value, list):
		raise ValueError(f"{label} must be a list.")
	if any(not isinstance(row, dict) for row in value):
		raise ValueError(f"Each {label} entry must be an object.")
	return value


def _single_match(rows, predicate, description):
	matches = [row for row in rows if predicate(row)]
	if len(matches) != 1:
		raise ValueError(f"Custom price must match exactly one selected {description}.")
	return matches[0]


def apply_custom_price_overrides(line_calc, overrides, item_code=""):
	"""Apply validated, per-order price overrides to a calculated POS line.

	Contract:
	- ``base_unit_price`` is the selected Item/variant's full unit price.
	- ``modifier_unit_prices`` contains ``group``, ``option`` and ``unit_rate``
	  in the selected modifier's ``pricing_uom``.
	- ``ingredient_unit_prices`` contains ``ingredient_key``, ``item_code`` and
	  ``unit_rate`` in the selected BOM alternative's stock UOM.
	"""
	if not isinstance(line_calc, dict):
		raise ValueError("A calculated POS line is required.")
	if not isinstance(overrides, dict):
		raise ValueError("Custom price overrides must be an object.")
	unknown = set(overrides) - _ALLOWED_KEYS
	if unknown:
		raise ValueError(f"Unsupported custom price override: {sorted(unknown)[0]}.")

	result = deepcopy(line_calc)
	pricing = result.setdefault("pricing_breakdown", {})
	customization = result.setdefault("normalized_customization", {})
	if not isinstance(pricing, dict) or not isinstance(customization, dict):
		raise ValueError("The calculated POS line has an invalid pricing snapshot.")

	base_price = _price(overrides["base_unit_price"], "Base unit price") if "base_unit_price" in overrides else None
	modifier_overrides = _rows(overrides.get("modifier_unit_prices"), "modifier unit prices")
	ingredient_overrides = _rows(overrides.get("ingredient_unit_prices"), "ingredient unit prices")
	unit_adjustment = 0.0
	modifier_delta_change = 0.0
	ingredient_delta_change = 0.0
	snapshot = {}
	if item_code:
		snapshot["item_code"] = str(item_code).strip()

	if base_price is not None:
		previous_base = _price(pricing.get("base_price"), "Calculated base unit price")
		unit_adjustment += base_price - previous_base
		pricing["base_price"] = base_price
		snapshot["base_unit_price"] = base_price

	selected_modifiers = customization.get("selected_modifiers") or []
	if not isinstance(selected_modifiers, list):
		raise ValueError("The calculated modifier snapshot is invalid.")
	pricing_modifiers = pricing.get("modifiers") or []
	if not isinstance(pricing_modifiers, list):
		pricing_modifiers = []
	modifier_snapshot = []
	seen_modifier_keys = set()
	for override in modifier_overrides:
		if set(override) - {"group", "option", "unit_rate"}:
			raise ValueError("Modifier price entries only support group, option and unit_rate.")
		group = str(override.get("group") or "").strip()
		option = str(override.get("option") or "").strip()
		if not group or not option:
			raise ValueError("Modifier price overrides require group and option.")
		modifier_key = (group, option)
		if modifier_key in seen_modifier_keys:
			raise ValueError("Custom price payload contains a duplicate modifier target.")
		seen_modifier_keys.add(modifier_key)
		unit_rate = _price(override.get("unit_rate"), "Modifier unit rate")
		modifier = _single_match(
			selected_modifiers,
			lambda row: row.get("group") == group and row.get("option") == option,
			"modifier",
		)
		if modifier.get("type") == "variant_selection" or "pricing_qty_in_stock_uom" not in modifier:
			raise ValueError("Custom price must match exactly one selected modifier with pricing details.")
		pricing_qty = _price(
			modifier.get("pricing_qty_in_stock_uom"), "Selected modifier quantity"
		)
		old_delta = _number(modifier.get("pricing_delta", 0), "Calculated modifier price")
		new_delta = unit_rate * pricing_qty
		modifier.update({"unit_rate": unit_rate, "pricing_delta": new_delta, "custom_price_override": 1})
		modifier_delta_change += new_delta - old_delta
		modifier_snapshot.append(
			{
				"group": group,
				"option": option,
				"item_code": modifier.get("item_code") or "",
				"pricing_qty_in_stock_uom": pricing_qty,
				"pricing_uom": modifier.get("pricing_uom") or "",
				"unit_rate": unit_rate,
				"pricing_delta": new_delta,
			}
		)
		for pricing_modifier in pricing_modifiers:
			if pricing_modifier.get("group") == group and pricing_modifier.get("option") == option:
				pricing_modifier.update(
					{"unit_rate": unit_rate, "pricing_delta": new_delta, "custom_price_override": 1}
				)
		for component_rows in (pricing.get("ingredients") or [], result.get("ingredient_components") or []):
			for component in component_rows:
				if (
					component.get("source_type") == "modifier_add_on"
					and component.get("modifier_group") == group
					and component.get("ingredient_key") == option
				):
					component.update(
						{
							"custom_price_unit_rate": unit_rate,
							"pricing_delta": new_delta,
							"custom_price_override": 1,
						}
					)
		for selection in result.get("selections") or []:
			if (
				selection.get("kind") == "modifier"
				and selection.get("group") == group
				and selection.get("option") == option
			):
				selection["delta_price"] = new_delta
	if modifier_overrides:
		unit_adjustment += modifier_delta_change
		pricing["modifier_delta_total"] = float(pricing.get("modifier_delta_total") or 0) + modifier_delta_change
		snapshot["modifier_unit_prices"] = modifier_snapshot

	ingredients = pricing.get("ingredients")
	if not isinstance(ingredients, list):
		ingredients = result.get("ingredient_components") or []
	ingredient_snapshot = []
	seen_ingredient_keys = set()
	for override in ingredient_overrides:
		if set(override) - {"ingredient_key", "item_code", "unit_rate"}:
			raise ValueError("Ingredient price entries only support ingredient_key, item_code and unit_rate.")
		ingredient_key = str(override.get("ingredient_key") or "").strip()
		item_code = str(override.get("item_code") or "").strip()
		if not ingredient_key or not item_code:
			raise ValueError("Ingredient price overrides require ingredient_key and item_code.")
		ingredient_identity = (ingredient_key, item_code)
		if ingredient_identity in seen_ingredient_keys:
			raise ValueError("Custom price payload contains a duplicate ingredient target.")
		seen_ingredient_keys.add(ingredient_identity)
		unit_rate = _price(override.get("unit_rate"), "Ingredient unit rate")
		component = _single_match(
			ingredients,
			lambda row: row.get("source_type") == "bom_item"
			and row.get("ingredient_key") == ingredient_key
			and row.get("selected_alternative_item") == item_code,
			"BOM alternative",
		)
		if "pricing_qty_in_stock_uom" not in component or "base_pricing_total_price" not in component:
			raise ValueError("The selected BOM alternative has no complete pricing snapshot.")
		pricing_qty = _price(component.get("pricing_qty_in_stock_uom"), "Alternative quantity")
		base_total = _price(component.get("base_pricing_total_price"), "Base ingredient price")
		base_qty = _price(
			component.get("base_qty_in_stock_uom")
			or _number(component.get("base_qty", 0), "Base ingredient quantity")
			* _number(component.get("base_multiplier", 1), "Base ingredient multiplier"),
			"Base ingredient quantity",
		)
		base_unit_rate = _price(
			component.get("base_pricing_unit_rate")
			if component.get("base_pricing_unit_rate") not in (None, "")
			else (base_total / base_qty if base_qty else 0),
			"Base ingredient unit rate",
		)
		old_delta = _number(component.get("pricing_delta", 0), "Calculated ingredient price")
		new_delta = unit_rate * pricing_qty - base_total
		component.update(
			{
				"custom_price_unit_rate": unit_rate,
				"pricing_delta": new_delta,
				"custom_price_override": 1,
			}
		)
		for mirror in result.get("ingredient_components") or []:
			if (
				mirror.get("source_type") == "bom_item"
				and mirror.get("ingredient_key") == ingredient_key
				and mirror.get("selected_alternative_item") == item_code
			):
				mirror.update(
					{
						"custom_price_unit_rate": unit_rate,
						"pricing_delta": new_delta,
						"custom_price_override": 1,
					}
				)
		ingredient_delta_change += new_delta - old_delta
		ingredient_snapshot.append(
			{
				"ingredient_key": ingredient_key,
				"base_item_code": component.get("base_item_code") or "",
				"item_code": item_code,
				"base_qty_in_stock_uom": base_qty,
				"selected_qty_in_stock_uom": pricing_qty,
				"base_unit_rate": base_unit_rate,
				"unit_rate": unit_rate,
				"base_total_price": base_total,
				"selected_total_price": unit_rate * pricing_qty,
				"pricing_delta": new_delta,
				"base_stock_uom": component.get("base_stock_uom") or "",
				"selected_stock_uom": component.get("stock_uom") or component.get("pricing_uom") or "",
			}
		)
		for selection in result.get("selections") or []:
			if (
				selection.get("kind") == "ingredient_alternative"
				and selection.get("ingredient_key") == ingredient_key
				and selection.get("item_code") == item_code
			):
				selection["delta_price"] = new_delta
		for alternative in customization.get("selected_alternatives") or []:
			if (
				alternative.get("ingredient_key") == ingredient_key
				and alternative.get("alternative_item") == item_code
			):
				alternative.update(
					{
						"unit_rate": unit_rate,
						"pricing_qty_in_stock_uom": pricing_qty,
						"pricing_delta": new_delta,
						"custom_price_override": 1,
					}
				)
		for alternative in pricing.get("selected_alternatives") or []:
			if (
				alternative.get("ingredient_key") == ingredient_key
				and alternative.get("alternative_item") == item_code
			):
				alternative.update(
					{
						"unit_rate": unit_rate,
						"pricing_qty_in_stock_uom": pricing_qty,
						"pricing_delta": new_delta,
						"custom_price_override": 1,
					}
				)
	if ingredient_overrides:
		unit_adjustment += ingredient_delta_change
		pricing["ingredient_delta_total"] = float(pricing.get("ingredient_delta_total") or 0) + ingredient_delta_change
		snapshot["ingredient_unit_prices"] = ingredient_snapshot

	unit_price = float(result.get("unit_price") or 0) + unit_adjustment
	if not math.isfinite(unit_price) or unit_price < 0:
		raise ValueError("Custom prices cannot make the POS line unit price negative.")
	qty = float(result.get("qty") or 0)
	line_total = unit_price * qty
	result["unit_price"] = unit_price
	result["line_total"] = line_total
	result["extra_charge"] = unit_price - float(pricing.get("base_price") or 0)
	pricing["unit_price"] = unit_price
	pricing["line_total"] = line_total
	pricing["extra_charge"] = result["extra_charge"]
	if snapshot:
		customization["custom_price_overrides"] = deepcopy(snapshot)
		pricing["custom_price_overrides"] = deepcopy(snapshot)
	return result
