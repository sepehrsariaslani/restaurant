"""Pure matching helpers for manually entered Food Partner orders."""

from math import isfinite


ITEM_QUANTITY_TOLERANCE = 0.0001


def _order_day(value):
	return str(value or "").strip().replace("T", " ", 1)[:10]


def _positive_quantity(value):
	try:
		quantity = float(value)
	except (TypeError, ValueError):
		return None
	return quantity if isfinite(quantity) and quantity > 0 else None


def _amount(value):
	try:
		amount = float(str(value if value not in (None, "") else 0).replace(",", ""))
	except (TypeError, ValueError):
		return None
	return amount if isfinite(amount) else None


def _item_signature(rows, *, partner=False):
	quantities = {}
	for row in rows or []:
		if partner:
			mapped_item = row.get("mapped_item") or {}
			mapped_modifier = row.get("mapped_modifier") or {}
			mapped_alternative = row.get("mapped_alternative") or {}
			item_code = mapped_item.get("item_code")
			if not item_code and mapped_modifier.get("mapping_mode") == "modifier":
				# Standalone add-on rows are folded into their parent POS item
				# during import and do not become separate Sales Order items.
				continue
			if not item_code and mapped_modifier.get("mapping_mode") in {"item_modifier", "item_alternative"}:
				item_code = mapped_modifier.get("parent_item_code") or mapped_modifier.get("parent_item")
			if not item_code and mapped_alternative.get("mapping_mode") == "item_alternative":
				item_code = mapped_alternative.get("parent_item_code") or mapped_alternative.get("parent_item")
		else:
			item_code = row.get("item_code")

		item_code = str(item_code or "").strip()
		quantity = _positive_quantity(row.get("qty"))
		if not item_code or quantity is None:
			return None
		quantities[item_code] = quantities.get(item_code, 0.0) + quantity
	return quantities or None


def _same_items(partner_items, local_items):
	partner_signature = _item_signature(partner_items, partner=True)
	local_signature = _item_signature(local_items)
	if not partner_signature or not local_signature or partner_signature.keys() != local_signature.keys():
		return False
	return all(
		abs(partner_signature[item_code] - local_signature[item_code]) <= ITEM_QUANTITY_TOLERANCE
		for item_code in partner_signature
	)


def has_comparable_partner_items(partner_order):
	"""Return whether every Partner line resolves to a local item identity."""
	return bool(_item_signature(partner_order.get("items"), partner=True))


def find_manual_duplicate(partner_order, manual_orders, used_order_names=None, amount_tolerance=1.0):
	"""Return one same-day manual POS order with an identical total and item mix.

	When supplied, ``used_order_names`` is updated with the matched local order
	name so a batch of similar Partner orders cannot all consume one manual row.
	"""
	if partner_order.get("manual_duplicate_date_checkable") is False:
		return None
	partner_day = _order_day(partner_order.get("created_at"))
	partner_total = _amount(partner_order.get("final_amount"))
	partner_items = _item_signature(partner_order.get("items"), partner=True)
	if not partner_day or partner_total is None or not partner_items:
		return None

	used_names = used_order_names if used_order_names is not None else set()
	try:
		tolerance = max(float(amount_tolerance), 0.0)
	except (TypeError, ValueError):
		tolerance = 1.0

	for local_order in manual_orders or []:
		name = str(local_order.get("name") or "").strip()
		if not name or name in used_names:
			continue
		try:
			if int(local_order.get("docstatus") or 0) != 1:
				continue
		except (TypeError, ValueError):
			continue
		if str(local_order.get("source") or "web").strip().lower() not in {"web", "restaurant"}:
			continue
		if str(local_order.get("external_source") or "").strip() or str(local_order.get("external_order_id") or "").strip():
			continue

		local_day = _order_day(
			local_order.get("transaction_date")
			or local_order.get("created_at")
			or local_order.get("order_date")
		)
		local_total = _amount(
			local_order.get("grand_total")
			if local_order.get("grand_total") not in (None, "")
			else local_order.get("total_amount")
		)
		if local_day != partner_day or local_total is None:
			continue
		if abs(partner_total - local_total) > tolerance:
			continue
		if not _same_items(partner_order.get("items"), local_order.get("items")):
			continue

		used_names.add(name)
		return local_order
	return None


def assign_manual_duplicates(partner_orders, manual_orders_by_date):
	"""Assign at most one manual order to each matching Partner order in a full batch."""
	used_names_by_date = {}
	assignments = {}
	for partner_order in partner_orders or []:
		order_id = str(partner_order.get("order_id") or "").strip()
		partner_day = _order_day(partner_order.get("created_at"))
		if not order_id or not partner_day:
			continue
		used_names = used_names_by_date.setdefault(partner_day, set())
		manual_order = find_manual_duplicate(
			partner_order,
			(manual_orders_by_date or {}).get(partner_day) or [],
			used_order_names=used_names,
		)
		if manual_order:
			assignments[order_id] = str(manual_order.get("name") or "")
	return assignments
