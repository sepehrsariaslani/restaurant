import frappe
from frappe.utils import flt


def _default_uom():
	for candidate in ("عدد", "Nos", "Unit", "واحد"):
		if frappe.db.exists("UOM", candidate):
			return candidate
	return frappe.db.get_value("UOM", {}, "name") or "Nos"


def _service_item_group():
	for candidate in ("خدمات", "Services", "Products", "محصولات"):
		if frappe.db.exists("Item Group", candidate):
			return candidate
	return frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "Products"


def _default_selling_price_list():
	try:
		from restaurant.api import _default_selling_price_list as app_default_selling_price_list

		default_price_list = (app_default_selling_price_list() or "").strip()
		if default_price_list:
			return default_price_list
	except Exception:
		pass

	for candidate in ("فروش استاندارد", "Standard Selling"):
		if frappe.db.exists("Price List", candidate):
			return candidate
	return frappe.db.get_value("Price List", {"selling": 1}, "name") or ""


def _ensure_option_item(option_name):
	option_name = (option_name or "").strip()
	if not option_name:
		return ""
	existing = frappe.db.get_value("Item", {"item_name": option_name}, "name") or (
		option_name if frappe.db.exists("Item", option_name) else ""
	)
	if existing:
		return existing

	item = frappe.new_doc("Item")
	item.item_code = option_name
	item.item_name = option_name
	item.item_group = _service_item_group()
	item.stock_uom = _default_uom()
	item.is_stock_item = 0
	item.include_item_in_manufacturing = 0
	item.insert(ignore_permissions=True)
	return item.name


def _ensure_item_price(item_code, option_uom, rate, price_list):
	if not item_code or not price_list:
		return
	filters = {
		"item_code": item_code,
		"price_list": price_list,
		"selling": 1,
	}
	existing = frappe.db.get_value("Item Price", filters, "name")
	if existing:
		frappe.db.set_value(
			"Item Price",
			existing,
			{
				"price_list_rate": flt(rate),
				"uom": option_uom or None,
			},
			update_modified=False,
		)
		return

	doc = frappe.new_doc("Item Price")
	doc.item_code = item_code
	doc.price_list = price_list
	doc.selling = 1
	doc.uom = option_uom or None
	doc.price_list_rate = flt(rate)
	doc.insert(ignore_permissions=True)


def execute():
	if not frappe.db.exists("DocType", "Restaurant Modifier Group"):
		return

	price_list = _default_selling_price_list()
	changed = 0
	for group_name in frappe.get_all("Restaurant Modifier Group", pluck="name", ignore_permissions=True):
		doc = frappe.get_doc("Restaurant Modifier Group", group_name)
		doc_changed = False
		for row in doc.get("options") or []:
			action_type = (row.get("action_type") or "add_on").strip() or "add_on"
			if action_type != "add_on":
				continue
			option_name = (row.get("option_name") or "").strip()
			option_item = (row.get("option_item") or "").strip()
			if not option_item:
				option_item = _ensure_option_item(option_name)
				if option_item:
					row.option_item = option_item
					doc_changed = True
			if not option_item:
				continue

			stock_uom = frappe.db.get_value("Item", option_item, "stock_uom") or _default_uom()
			if not (row.get("option_uom") or "").strip():
				row.option_uom = stock_uom
				doc_changed = True
			option_qty = flt(row.get("option_qty") or 1)
			if option_qty <= 0:
				option_qty = 1
				row.option_qty = option_qty
				doc_changed = True
			rate = flt(row.get("price_delta") or 0) / option_qty
			_ensure_item_price(option_item, row.get("option_uom") or stock_uom, rate, price_list)

		if doc_changed:
			doc.save(ignore_permissions=True)
			changed += 1

	if changed:
		frappe.clear_cache(doctype="Restaurant Modifier Group")
	frappe.db.commit()
