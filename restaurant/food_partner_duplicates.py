"""Pure matching helpers for manually entered Food Partner orders."""

from math import isfinite
from uuid import uuid4


ITEM_QUANTITY_TOLERANCE = 0.0001
MANUAL_DUPLICATE_SOURCE = "snapp_food_manual_duplicate"
_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_GENERIC_CUSTOMER_NAMES = {
	"guest",
	"snappguest",
	"snappcustomer",
	"poscustomer",
	"customer",
	"مهمان",
	"مشتری",
	"مشتریاسنپ",
	"کاربراسنپ",
}


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


def _normalized_mobile(value):
	digits = "".join(char for char in str(value or "").translate(_DIGIT_TRANSLATION) if char.isdigit())
	if digits.startswith("0098") and len(digits) == 14:
		digits = "0" + digits[4:]
	elif digits.startswith("98") and len(digits) == 12:
		digits = "0" + digits[2:]
	elif len(digits) == 10 and digits.startswith("9"):
		digits = "0" + digits
	return digits


def _normalized_customer_name(value):
	text = str(value or "").strip().casefold().translate(str.maketrans({"ي": "ی", "ك": "ک", "ـ": ""}))
	return "".join(char for char in text if char.isalnum())


def _is_generic_customer_name(value):
	name = _normalized_customer_name(value)
	return name in _GENERIC_CUSTOMER_NAMES or name.startswith(
		("snappguest", "guest", "poscustomer", "مشتریاسنپ", "کاربراسنپ")
	)


def _same_customer(partner_order, local_order):
	partner_external_id = str(partner_order.get("external_customer_id") or "").strip()
	local_external_id = str(local_order.get("external_customer_id") or "").strip()
	if partner_external_id and local_external_id:
		return partner_external_id == local_external_id

	partner_mobile = _normalized_mobile(partner_order.get("mobile"))
	local_mobile = _normalized_mobile(local_order.get("mobile"))
	if partner_mobile and local_mobile:
		return partner_mobile == local_mobile

	partner_name = _normalized_customer_name(partner_order.get("customer_name"))
	local_name = _normalized_customer_name(local_order.get("customer_name"))
	if (
		not partner_name
		or _is_generic_customer_name(partner_name)
		or not local_name
		or _is_generic_customer_name(local_name)
	):
		return False
	return partner_name == local_name


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
	"""Return one same-day manual POS order with the same customer, total and item mix.

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
			if int(local_order.get("docstatus") or 0) not in {0, 1}:
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
		if not _same_customer(partner_order, local_order):
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
		if partner_order.get("manual_duplicate"):
			continue
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


def mark_manual_duplicate_previews(partner_orders, manual_orders):
	"""Mark matching previews, including Partner orders imported before a manual entry."""
	manual_orders_by_date = {}
	for manual_order in manual_orders or []:
		manual_day = _order_day(
			manual_order.get("transaction_date")
			or manual_order.get("created_at")
			or manual_order.get("order_date")
		)
		if manual_day:
			manual_orders_by_date.setdefault(manual_day, []).append(manual_order)

	assignments = assign_manual_duplicates(partner_orders, manual_orders_by_date)
	for partner_order in partner_orders or []:
		order_id = str(partner_order.get("order_id") or "").strip()
		manual_order_name = assignments.get(order_id)
		if manual_order_name:
			partner_order["manual_duplicate"] = True
			partner_order["manual_duplicate_sales_order"] = manual_order_name
	return partner_orders


def claim_manual_duplicate_order(db, sales_order_name, partner_order_id):
	"""Atomically reserve a submitted manual order for one Partner order ID."""
	partner_order_id = str(partner_order_id or "").strip()
	if not partner_order_id:
		return False
	savepoint = f"food_partner_duplicate_claim_{uuid4().hex}"
	db.savepoint(savepoint)
	try:
		row = db.get_value(
			"Sales Order",
		sales_order_name,
			["restaurant_external_source", "restaurant_external_order_id"],
			as_dict=True,
			for_update=True,
		)
		if not row:
			db.rollback(save_point=savepoint)
			return False

		existing_source = str(row.get("restaurant_external_source") or "").strip()
		existing_order_id = str(row.get("restaurant_external_order_id") or "").strip()
		if existing_source == MANUAL_DUPLICATE_SOURCE and existing_order_id == partner_order_id:
			db.rollback(save_point=savepoint)
			return True
		if existing_source or existing_order_id:
			db.rollback(save_point=savepoint)
			return False

		db.set_value(
			"Sales Order",
			sales_order_name,
			{
				"restaurant_external_source": MANUAL_DUPLICATE_SOURCE,
				"restaurant_external_order_id": partner_order_id,
			},
			update_modified=False,
		)
		return True
	except Exception as error:
		db.rollback(save_point=savepoint)
		if _is_transaction_conflict(error):
			return False
		raise


def _is_transaction_conflict(error):
	"""Recognize retryable database contention without hiding other failures."""
	sqlstate = getattr(error, "sqlstate", None) or getattr(error, "pgcode", None)
	if sqlstate in {"40001", "40P01"}:
		return True
	error_code = (getattr(error, "args", ()) or (None,))[0]
	return error_code in {1205, 1213}
