# Copyright (c) 2026, Restaurant and contributors
"""Smart inventory management pack for the restaurant management SPA.

Everything here is surfaced under ``/management/inventory`` and re-exported into
``restaurant.api`` (see the star-import at the bottom of ``api.py``) so the
frontend keeps calling ``/api/method/restaurant.api.<endpoint>``.

Provided features (on top of the already existing BOM/production pipeline):

- Raw material registry (unlimited items, per-warehouse reorder points)
- Unlimited warehouses CRUD
- Manual stock in/out/transfer with movement kinds
- Purchase orders from suppliers + receiving against them
- Reorder-point alerts, one-click draft purchase orders
- Production planning (required materials vs. live stock) + manual
  manufacture entries straight from a recipe (BOM)
- Waste / damage tracking and out-of-order (اوتی) loss log
- Physical stock count & reconciliation (Stock Reconciliation)
- Live product cost (بهای تمام‌شده) report from recipes
- Stock overview in both quantity and monetary terms
"""

import json
from html import escape as html_escape

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_get_currency,
	_has_column,
	_item_uom_conversion_to_stock,
	_management_get_print_brand_settings,
	_table_columns_from_rows,
)


def _inv_fp_call(helper_name, *args, **kwargs):
	"""Lazy bridge into ``restaurant.api_feature_pack``.

	Feature-pack helpers must NOT be imported at module top: when a migrate
	patch imports ``api_feature_pack`` first, it (partially) initializes
	``restaurant.api`` whose tail re-imports this module — top-level imports
	of ``api_feature_pack`` would then hit a partially-initialized module and
	raise ImportError. Importing at call time avoids the import cycle.
	"""
	from restaurant import api_feature_pack

	return getattr(api_feature_pack, helper_name)(*args, **kwargs)

__all__ = [
	# constants/helpers used elsewhere
	"STOCK_MOVEMENT_KINDS",
	"PURCHASE_ORDER_DOCTYPE",
	"ORDER_LOSS_DOCTYPE",
	# custom field provisioning
	"_inv_ensure_ops_ready",
	# boot
	"get_management_inventory_boot",
	# material requests
	"list_management_material_requests",
	"get_management_material_request",
	"save_management_material_request",
	"update_management_material_request_status",
	"create_management_purchase_from_material_request",
	"get_management_material_request_print",
	"list_management_uoms",
	# raw materials
	"list_management_raw_materials",
	"get_management_raw_material_detail",
	"save_management_raw_material",
	# warehouses
	"list_management_warehouses",
	"save_management_warehouse",
	"delete_management_warehouse",
	# stock overview
	"get_management_stock_overview",
	# movements
	"create_management_stock_movement",
	"list_management_stock_movements",
	# suppliers & purchases
	"list_management_suppliers",
	"save_management_supplier",
	"list_management_purchase_orders",
	"get_management_purchase_order",
	"save_management_purchase_order",
	"update_management_purchase_order_status",
	"receive_management_purchase_order",
	# reorder alerts
	"get_management_reorder_alerts",
	"create_management_purchase_from_alerts",
	# production planning
	"get_management_production_plan",
	"create_management_production_entry",
	# order losses (اوتی / خسارت / مرجوعی)
	"save_management_order_loss",
	"list_management_order_losses",
	"get_management_waste_loss_report",
	# reconciliation
	"get_management_reconciliation_context",
	"submit_management_stock_reconciliation",
	"list_management_stock_reconciliations",
	"get_management_stock_reconciliation",
	# costing
	"get_management_product_cost_report",
	# BI reports (reports center)
	"MANAGEMENT_INVENTORY_REPORTS",
	"get_management_report_inventory_valuation",
	"get_management_report_stock_movements",
	"get_management_report_inventory_waste",
	"inv_build_report_bi",
	# excel
	"MATERIAL_EXPORT_COLUMNS",
	"export_management_materials_excel",
	"import_management_materials_excel",
	# dashboard + print
	"get_management_inventory_alerts_summary",
	"get_management_inventory_purchase_print",
]


STOCK_MOVEMENT_KINDS = {
	"purchase_receipt": "دریافت خرید",
	"manual_receipt": "ورود دستی",
	"manual_issue": "خروج دستی",
	"transfer": "انتقال",
	"waste": "ضایعات",
	"damage": "خسارت",
	"production": "تولید دستی",
	"return_to_stock": "مرجوعی به انبار",
}
MOVEMENT_KIND_LABELS = list(STOCK_MOVEMENT_KINDS.values())

PURCHASE_ORDER_DOCTYPE = "Restaurant Inventory Purchase Order"
PURCHASE_ORDER_ITEM_DOCTYPE = "Restaurant Inventory Purchase Order Item"
ORDER_LOSS_DOCTYPE = "Restaurant Order Loss Entry"
PURCHASE_ORDER_STATUSES = ["پیش‌نویس", "ارسال‌شده", "دریافت جزئی", "دریافت کامل", "لغوشده"]
PURCHASE_STATUS_DRAFT = PURCHASE_ORDER_STATUSES[0]
PURCHASE_STATUS_SENT = PURCHASE_ORDER_STATUSES[1]
PURCHASE_STATUS_PARTIAL = PURCHASE_ORDER_STATUSES[2]
PURCHASE_STATUS_COMPLETE = PURCHASE_ORDER_STATUSES[3]
PURCHASE_STATUS_CANCELLED = PURCHASE_ORDER_STATUSES[4]
MATERIAL_REQUEST_DOCTYPE = "Material Request"
MATERIAL_REQUEST_ITEM_DOCTYPE = "Material Request Item"
MATERIAL_REQUEST_STATUS_LABELS = {
	"draft": "پیش‌نویس",
	"pending": "در انتظار خرید",
	"partially ordered": "خرید جزئی",
	"ordered": "خرید کامل",
	"stopped": "متوقف‌شده",
	"cancelled": "لغوشده",
	"issued": "صادرشده",
	"transferred": "منتقل‌شده",
}
ORDER_LOSS_KINDS = ["اوت شده", "خسارت", "مرجوعی به انبار"]

INVENTORY_MODULE_ERRORS = _("Restaurant Inventory")


# ---------------------------------------------------------------------------
# Custom field provisioning (runtime, idempotent)
# ---------------------------------------------------------------------------


def _inv_ensure_item_fields():
	"""Marker fields on Item for raw materials and purchasing defaults."""
	_inv_fp_call("_fp_ensure_custom_fields",
		"Item",
		[
			{
				"fieldname": "restaurant_raw_material",
				"label": _("ماده اولیه انبار"),
				"fieldtype": "Check",
			},
			{
				"fieldname": "restaurant_purchase_rate",
				"label": _("آخرین نرخ خرید"),
				"fieldtype": "Currency",
			},
			{
				"fieldname": "restaurant_default_supplier",
				"label": _("تأمین‌کننده پیش‌فرض"),
				"fieldtype": "Link",
				"options": "Supplier",
			},
		],
		anchor_candidates=[
			"restaurant_packaging_price",
			"restaurant_out_of_stock",
			"restaurant_enabled",
			"is_stock_item",
		],
	)


def _inv_ensure_stock_entry_fields():
	"""Movement classification fields on Stock Entry (waste, damage, ...)."""
	_inv_fp_call("_fp_ensure_custom_fields",
		"Stock Entry",
		[
			{
				"fieldname": "restaurant_movement_kind",
				"label": _("نوع گردش انبار (رستوران)"),
				"fieldtype": "Select",
				"options": "\n" + "\n".join(MOVEMENT_KIND_LABELS),
			},
			{
				"fieldname": "restaurant_reference_note",
				"label": _("شرح گردش (رستوران)"),
				"fieldtype": "Small Text",
			},
		],
		anchor_candidates=["remarks", "posting_time"],
	)


def _inv_ensure_inventory_settings_fields():
	"""Inventory defaults on Restaurant Web Settings."""
	_inv_fp_call("_fp_ensure_custom_fields",
		"Restaurant Web Settings",
		[
			{
				"fieldname": "restaurant_inventory_section",
				"label": _("انبارداری هوشمند"),
				"fieldtype": "Section Break",
			},
			{
				"fieldname": "restaurant_inventory_default_warehouse",
				"label": _("انبار پیش‌فرض مواد اولیه"),
				"fieldtype": "Link",
				"options": "Warehouse",
			},
			{
				"fieldname": "restaurant_inventory_waste_warehouse",
				"label": _("انبار ضایعات"),
				"fieldtype": "Link",
				"options": "Warehouse",
			},
			{
				"fieldname": "restaurant_waste_as_transfer",
				"label": _("ثبت ضایعات به‌صورت انتقال به انبار ضایعات"),
				"fieldtype": "Check",
			},
		],
		anchor_candidates=[
			"restaurant_ops_feature_section",
			"restaurant_packaging_enabled",
			"restaurant_work_shifts_json",
		],
	)


def _inv_ensure_ops_ready():
	_inv_ensure_item_fields()
	_inv_ensure_stock_entry_fields()
	_inv_ensure_inventory_settings_fields()


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------


def _inv_parse_payload(payload):
	"""Accept dict payloads or JSON strings; fall back to form_dict."""
	if payload is None:
		payload = {}
	if isinstance(payload, str):
		try:
			payload = json.loads(payload.strip() or "{}")
		except Exception:
			payload = {}
	if not isinstance(payload, dict) and hasattr(frappe, "form_dict"):
		try:
			payload = dict(frappe.form_dict or {})
		except Exception:
			payload = {}
	return payload or {}


def _inv_normalize_list(value):
	if isinstance(value, str):
		try:
			parsed = json.loads(value)
			if isinstance(parsed, list):
				return parsed
		except Exception:
			return [row.strip() for row in value.split(",") if row.strip()]
		return []
	return list(value or []) if isinstance(value, (list, tuple)) else []


def _inv_clean_item_code(value):
	return (value or "").strip()


def _inv_default_company():
	try:
		default = frappe.defaults.get_global_default("company")
		if default and frappe.db.exists("Company", default):
			return default
	except Exception:
		pass
	companies = frappe.get_all("Company", pluck="name", limit_page_length=1)
	return companies[0] if companies else ""


def _inv_leaf_warehouses():
	try:
		rows = frappe.get_all(
			"Warehouse",
			filters={"is_group": 0, "disabled": 0},
			pluck="name",
			order_by="name",
		)
		return rows or []
	except Exception:
		return []


def _inv_warehouse_exists(name):
	return bool(name) and frappe.db.exists("Warehouse", name)


def _inv_get_inventory_settings():
	getter = None
	try:
		from restaurant.api import _get_single_setting

		getter = _get_single_setting
	except Exception:
		getter = None

	def read(fieldname, default=""):
		if getter:
			try:
				return getter("Restaurant Web Settings", fieldname, default)
			except Exception:
				return default
		try:
			return frappe.db.get_single_value("Restaurant Web Settings", fieldname) or default
		except Exception:
			return default

	return {
		"default_warehouse": (read("restaurant_inventory_default_warehouse", "") or "").strip(),
		"waste_warehouse": (read("restaurant_inventory_waste_warehouse", "") or "").strip(),
		"waste_as_transfer": cint(read("restaurant_waste_as_transfer", 0) or 0) == 1,
	}


def _inv_resolve_warehouse(value, fallback=""):
	value = (value or "").strip()
	if value and _inv_warehouse_exists(value):
		return value
	if fallback and _inv_warehouse_exists(fallback):
		return fallback
	settings = _inv_get_inventory_settings()
	if settings["default_warehouse"] and _inv_warehouse_exists(settings["default_warehouse"]):
		return settings["default_warehouse"]
	leaf = _inv_leaf_warehouses()
	return leaf[0] if leaf else ""


def _inv_item_meta(item_codes):
	"""Return {item_code: {name, item_name, stock_uom, item_group, disabled}}."""
	codes = [c for c in {(_inv_clean_item_code(c)) for c in (item_codes or [])} if c]
	if not codes:
		return {}
	rows = frappe.get_all(
		"Item",
		filters={"name": ["in", codes]},
		fields=["name", "item_name", "stock_uom", "item_group", "disabled"],
	)
	return {row["name"]: row for row in rows}


def _inv_stock_map(item_codes=None, warehouse=""):
	"""Aggregate Bin quantities: {item: {qty, value, rate, warehouses:{wh:{qty,rate,value}}}}."""
	warehouses = _inv_leaf_warehouses()
	if warehouse:
		warehouses = [warehouse] if _inv_warehouse_exists(warehouse) else []
	if not warehouses:
		return {}

	conditions = ["`warehouse` IN %(warehouses)s"]
	params = {"warehouses": tuple(warehouses)}
	codes = [c for c in {(_inv_clean_item_code(c)) for c in (item_codes or [])} if c]
	if item_codes is not None:
		if not codes:
			return {}
		conditions.append("`item_code` IN %(codes)s")
		params["codes"] = tuple(codes)

	rows = frappe.db.sql(
		"""
		SELECT item_code, warehouse, actual_qty, valuation_rate, stock_value
		FROM `tabBin`
		WHERE {conditions}
		""".format(
			conditions=" AND ".join(conditions)
		),
		params,
		as_dict=True,
	)

	result = {}
	for row in rows:
		item = row.get("item_code")
		if not item:
			continue
		bucket = result.setdefault(item, {"qty": 0.0, "value": 0.0, "rate": 0.0, "warehouses": {}})
		qty = flt(row.get("actual_qty"))
		value = flt(row.get("stock_value"))
		bucket["qty"] += qty
		bucket["value"] += value
		bucket["warehouses"][row.get("warehouse")] = {
			"qty": qty,
			"rate": flt(row.get("valuation_rate")),
			"value": value,
		}
	for item, bucket in result.items():
		bucket["rate"] = flt(bucket["value"] / bucket["qty"], 6) if bucket["qty"] else 0.0
	return result


def _inv_purchase_rate(item_code):
	"""Fallback chain for a raw material rate: custom field → pricing doc → Item Price → Bin rate."""
	item_code = _inv_clean_item_code(item_code)
	if not item_code:
		return 0.0
	if _has_column("Item", "restaurant_purchase_rate"):
		rate = flt(frappe.db.get_value("Item", item_code, "restaurant_purchase_rate"))
		if rate:
			return rate
	try:
		row = frappe.db.get_value(
			"Restaurant Raw Material Pricing",
			{"material_code": item_code, "status": "Active"},
			"current_price",
		)
		if flt(row):
			return flt(row)
	except Exception:
		pass
	try:
		row = frappe.db.sql(
			"""
			SELECT price_list_rate FROM `tabItem Price`
			WHERE item_code=%s AND buying=1
			ORDER BY valid_from DESC, creation DESC LIMIT 1
			""",
			(item_code,),
		)
		if row and flt(row[0][0]):
			return flt(row[0][0])
	except Exception:
		pass
	stock = _inv_stock_map(item_codes=[item_code]).get(item_code)
	return flt(stock.get("rate")) if stock else 0.0


def _inv_default_supplier(item_code):
	item_code = _inv_clean_item_code(item_code)
	if not item_code:
		return ""
	if _has_column("Item", "restaurant_default_supplier"):
		supplier = frappe.db.get_value("Item", item_code, "restaurant_default_supplier") or ""
		if supplier:
			return supplier
	try:
		row = frappe.db.get_value(
			"Restaurant Raw Material Pricing",
			{"material_code": item_code, "status": "Active"},
			"primary_supplier",
		)
		if row:
			return row
	except Exception:
		pass
	return ""


def _inv_update_purchase_tracking(item_code, rate, supplier=""):
	"""Persist latest purchase rate (and optional supplier) on the Item."""
	item_code = _inv_clean_item_code(item_code)
	if not item_code or not frappe.db.exists("Item", item_code):
		return
	updates = {}
	if _has_column("Item", "restaurant_purchase_rate") and flt(rate):
		updates["restaurant_purchase_rate"] = flt(rate)
	if supplier and _has_column("Item", "restaurant_default_supplier"):
		updates["restaurant_default_supplier"] = supplier
	if updates:
		frappe.db.set_value("Item", item_code, updates, update_modified=False)


def _inv_item_is_raw_material(item_row):
	if _has_column("Item", "restaurant_raw_material") and cint(item_row.get("restaurant_raw_material")):
		return True
	enabled_col = _has_column("Item", "restaurant_enabled")
	if enabled_col and cint(item_row.get("restaurant_enabled") or 0):
		return False
	return cint(item_row.get("is_stock_item")) == 1


def _inv_stock_entry_payload(doc):
	return {
		"name": doc.name,
		"stock_entry_type": doc.get("stock_entry_type") or "",
		"posting_date": str(doc.get("posting_date") or ""),
		"posting_time": str(doc.get("posting_time") or ""),
		"from_warehouse": doc.get("from_warehouse") or "",
		"to_warehouse": doc.get("to_warehouse") or "",
		"movement_kind": doc.get("restaurant_movement_kind") or "",
		"note": doc.get("restaurant_reference_note") or "",
		"total_amount": flt(doc.get("total_amount")),
		"items": [
			{
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name") or "",
				"qty": flt(row.get("qty")),
				"uom": row.get("uom") or row.get("stock_uom") or "",
				"s_warehouse": row.get("s_warehouse") or "",
				"t_warehouse": row.get("t_warehouse") or "",
				"basic_rate": flt(row.get("basic_rate")),
				"basic_amount": flt(row.get("basic_amount")),
			}
			for row in (doc.get("items") or [])
		],
	}


def _inv_build_stock_entry(*, entry_type, kind_label, lines, source_warehouse="", target_warehouse="", note="", posting_date=""):
	"""Create + submit a classified Stock Entry; raises on validation errors."""
	if not lines:
		frappe.throw(_("حداقل یک قلم برای ثبت گردش انبار لازم است."))

	entry = frappe.new_doc("Stock Entry")
	entry.stock_entry_type = entry_type
	entry.purpose = entry_type
	entry.posting_date = posting_date or today()
	entry.company = _inv_default_company()
	if source_warehouse:
		entry.from_warehouse = source_warehouse
	if target_warehouse:
		entry.to_warehouse = target_warehouse
	if _has_column("Stock Entry", "restaurant_movement_kind"):
		entry.restaurant_movement_kind = kind_label
	if _has_column("Stock Entry", "restaurant_reference_note") and note:
		entry.restaurant_reference_note = note
	entry.remarks = note or _("ثبت‌شده از مدیریت انبار رستوران")

	for line in lines:
		item_code = _inv_clean_item_code(line.get("item_code"))
		if not item_code or not frappe.db.exists("Item", item_code):
			frappe.throw(_("کالای نامعتبر: {0}").format(item_code or "-"))
		qty = flt(line.get("qty"))
		uom = (line.get("uom") or "").strip()
		if uom:
			factor = _item_uom_conversion_to_stock(item_code, uom)
			qty = qty * factor
		qty = flt(qty, 4)
		if qty <= 0:
			frappe.throw(_("مقدار برای {0} باید بزرگ‌تر از صفر باشد.").format(item_code))
		row = entry.append("items", {})
		row.item_code = item_code
		row.qty = qty
		if source_warehouse and entry_type != "Material Receipt":
			row.s_warehouse = source_warehouse
		if target_warehouse and entry_type != "Material Issue":
			row.t_warehouse = target_warehouse
		if entry_type == "Material Receipt":
			rate = flt(line.get("rate")) or _inv_purchase_rate(item_code)
			if rate:
				row.basic_rate = rate
			row.allow_zero_valuation_rate = 1

	entry.insert(ignore_permissions=True)
	entry.submit()
	return entry


def _inv_safe_execute(fn, error_prefix):
	try:
		return fn()
	except frappe.ValidationError:
		raise
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), INVENTORY_MODULE_ERRORS)
		frappe.throw(_("{0}: {1}").format(error_prefix, str(exc)[:200]))


# ---------------------------------------------------------------------------
# Boot / context
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_inventory_boot():
	"""KPIs and option payloads for the inventory dashboard."""
	_ensure_management_access()
	_inv_ensure_ops_ready()

	settings = _inv_get_inventory_settings()
	leaf = _inv_leaf_warehouses()

	material_filters = {"is_stock_item": 1}
	materials_total = frappe.db.count("Item", material_filters) or 0
	if _has_column("Item", "restaurant_raw_material"):
		materials_total = frappe.db.count(
			"Item",
			[["is_stock_item", "=", 1], ["restaurant_raw_material", "=", 1]],
		) or materials_total

	stock_rows = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(actual_qty),0) AS qty, COALESCE(SUM(stock_value),0) AS value
		FROM `tabBin`
		WHERE warehouse IN %(warehouses)s
		""",
		{"warehouses": tuple(leaf or ["__none__"])},
		as_dict=True,
	)
	total_qty = flt(stock_rows[0].get("qty")) if stock_rows else 0
	total_value = flt(stock_rows[0].get("value")) if stock_rows else 0

	below_reorder = len(get_management_reorder_alerts(limit=500).get("alerts") or [])

	waste_30d = 0.0
	if _has_column("Stock Entry", "restaurant_movement_kind"):
		row = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(ABS(sle.stock_value_difference)),0) AS amount
			FROM `tabStock Ledger Entry` sle
			INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
			WHERE sle.voucher_type='Stock Entry' AND sle.is_cancelled=0
			  AND se.restaurant_movement_kind IN (%(w)s, %(d)s)
			  AND sle.posting_date >= %(df)s
			""",
			{"w": STOCK_MOVEMENT_KINDS["waste"], "d": STOCK_MOVEMENT_KINDS["damage"], "df": add_days(today(), -30)},
			as_dict=True,
		)
		waste_30d = flt(row[0].get("amount")) if row else 0.0

	open_purchases = frappe.db.count(
		PURCHASE_ORDER_DOCTYPE,
		{"status": ["in", [PURCHASE_STATUS_DRAFT, PURCHASE_STATUS_SENT, PURCHASE_STATUS_PARTIAL]]},
	) or 0

	return {
		"kpis": {
			"materials_total": cint(materials_total),
			"warehouses_total": len(leaf),
			"below_reorder": cint(below_reorder),
			"stock_qty_total": flt(total_qty),
			"stock_value_total": flt(total_value),
			"waste_damage_30d_value": flt(waste_30d),
			"open_purchase_orders": cint(open_purchases),
		},
		"warehouses": frappe.get_all(
			"Warehouse",
			fields=["name", "warehouse_name", "parent_warehouse", "is_group", "disabled", "company"],
			order_by="name",
			limit_page_length=500,
		),
		"leaf_warehouses": leaf,
		"suppliers": frappe.get_all(
			"Supplier",
			fields=["name", "supplier_name", "supplier_group", "disabled"],
			order_by="supplier_name",
			limit_page_length=500,
		),
		"item_groups": frappe.get_all(
			"Item Group",
			fields=["name", "parent_item_group"],
			order_by="name",
			limit_page_length=500,
		),
		"settings": settings,
		"default_company": _inv_default_company(),
		"movement_kinds": STOCK_MOVEMENT_KINDS,
		"purchase_statuses": PURCHASE_ORDER_STATUSES,
		"loss_kinds": ORDER_LOSS_KINDS,
	}


@frappe.whitelist()
def list_management_uoms(search="", limit=100):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "UOM"):
		return {"uoms": []}
	search = str(search or "").strip()
	filters = {"enabled": 1} if _has_column("UOM", "enabled") else {}
	or_filters = None
	if search:
		or_filters = {"name": ["like", f"%{search}%"]}
	rows = frappe.get_all("UOM", filters=filters, or_filters=or_filters, fields=["name"], order_by="name asc", limit_page_length=min(max(cint(limit) or 100, 1), 500), ignore_permissions=True)
	return {"uoms": [row.get("name") for row in rows if row.get("name")]}


# ---------------------------------------------------------------------------
# Material requests (ERPNext Material Request)
# ---------------------------------------------------------------------------


def _inv_material_request_status(doc):
	if cint(doc.get("docstatus") or 0) == 0:
		return "draft"
	if cint(doc.get("docstatus") or 0) == 2:
		return "cancelled"
	return (doc.get("status") or "pending").strip().lower() or "pending"


def _inv_material_request_status_label(status):
	return MATERIAL_REQUEST_STATUS_LABELS.get(str(status or "").strip().lower(), str(status or "ثبت‌شده"))


def _inv_material_request_item_payload(row):
	return {
		"idx": cint(row.get("idx") or 0),
		"item_code": row.get("item_code") or "",
		"item_name": row.get("item_name") or row.get("item_code") or "",
		"description": row.get("description") or "",
		"qty": flt(row.get("qty")),
		"uom": row.get("uom") or row.get("stock_uom") or "",
		"stock_uom": row.get("stock_uom") or row.get("uom") or "",
		"conversion_factor": flt(row.get("conversion_factor") or 1),
		"warehouse": row.get("warehouse") or "",
		"schedule_date": str(row.get("schedule_date") or ""),
		"rate": flt(row.get("rate")),
		"amount": flt(row.get("amount")),
		"ordered_qty": flt(row.get("ordered_qty")),
	}


def _inv_material_request_payload(doc, include_items=True):
	status = _inv_material_request_status(doc)
	payload = {
		"name": doc.name,
		"status": status,
		"status_label": _inv_material_request_status_label(status),
		"docstatus": cint(doc.get("docstatus") or 0),
		"material_request_type": doc.get("material_request_type") or "Purchase",
		"transaction_date": str(doc.get("transaction_date") or ""),
		"schedule_date": str(doc.get("schedule_date") or ""),
		"company": doc.get("company") or "",
		"set_warehouse": doc.get("set_warehouse") or "",
		"owner": doc.get("owner") or "",
		"creation": str(doc.get("creation") or ""),
		"note": doc.get("remarks") or doc.get("description") or "",
		"total_qty": 0.0,
		"item_count": 0,
		"items_preview": [],
		"items": [],
	}
	if include_items:
		items = [_inv_material_request_item_payload(row) for row in (doc.get("items") or [])]
		payload["items"] = items
		payload["item_count"] = len(items)
		payload["total_qty"] = flt(sum(flt(row.get("qty")) for row in items))
		payload["items_preview"] = [
			{"item_code": row["item_code"], "item_name": row["item_name"], "qty": row["qty"], "uom": row["uom"]}
			for row in items[:4]
		]
	return payload


def _inv_material_request_purchases(request_name):
	if not frappe.db.exists("DocType", PURCHASE_ORDER_DOCTYPE):
		return []
	needle = f"%درخواست مواد {request_name}%"
	rows = frappe.get_all(
		PURCHASE_ORDER_DOCTYPE,
		filters={"note": ["like", needle]},
		fields=["name", "supplier_name", "status", "posting_date", "grand_total"],
		order_by="creation desc",
		limit_page_length=20,
	)
	return [
		{
			"name": row.name,
			"supplier_name": row.get("supplier_name") or "",
			"status": row.get("status") or PURCHASE_STATUS_DRAFT,
			"posting_date": str(row.get("posting_date") or ""),
			"grand_total": flt(row.get("grand_total")),
		}
		for row in rows
	]


@frappe.whitelist()
def list_management_material_requests(status="", search="", date_from="", date_to="", limit=50, offset=0):
	_ensure_management_access()
	if not frappe.db.exists("DocType", MATERIAL_REQUEST_DOCTYPE):
		return {"requests": [], "count": 0, "doctype_available": False}
	limit = min(max(cint(limit) or 50, 1), 200)
	offset = max(cint(offset) or 0, 0)
	filters = {}
	status_key = str(status or "").strip().lower()
	if status_key == "draft":
		filters["docstatus"] = 0
	elif status_key == "cancelled":
		filters["docstatus"] = 2
	elif status_key:
		filters["docstatus"] = 1
		filters["status"] = status
	if date_from:
		filters["transaction_date"] = [">=", getdate(date_from)]
	if date_to:
		filters["transaction_date"] = ["between", [getdate(date_from or date_to), getdate(date_to)]]

	rows = frappe.get_all(
		MATERIAL_REQUEST_DOCTYPE,
		filters=filters,
		fields=[
			"name", "status", "docstatus", "material_request_type", "transaction_date",
			"schedule_date", "company", "set_warehouse", "owner", "creation",
		],
		order_by="transaction_date desc, creation desc",
		limit_start=offset,
		limit_page_length=limit,
		ignore_permissions=True,
	)
	search_text = str(search or "").strip().lower()
	result = []
	for row in rows:
		payload = _inv_material_request_payload(row, include_items=False)
		if search_text:
			if search_text not in str(row.name or "").lower() and search_text not in str(row.get("company") or "").lower():
				child_match = frappe.db.exists(
					MATERIAL_REQUEST_ITEM_DOCTYPE,
					{"parent": row.name, "item_code": ["like", f"%{search_text}%"]},
				)
				if not child_match:
					child_match = frappe.db.exists(
						MATERIAL_REQUEST_ITEM_DOCTYPE,
						{"parent": row.name, "item_name": ["like", f"%{search_text}%"]},
					)
				if not child_match:
					continue
		# Keep list queries light, but expose a useful item preview.
			child_rows = frappe.get_all(
				MATERIAL_REQUEST_ITEM_DOCTYPE,
				filters={"parent": row.name},
				fields=["item_code", "item_name", "qty", "uom", "stock_uom"],
				order_by="idx asc",
				limit_page_length=4,
				ignore_permissions=True,
			)
			payload["items_preview"] = [_inv_material_request_item_payload(child) for child in child_rows]
			payload["item_count"] = frappe.db.count(MATERIAL_REQUEST_ITEM_DOCTYPE, {"parent": row.name}) or 0
			payload["total_qty"] = flt(
				frappe.db.sql(
					f"SELECT COALESCE(SUM(qty),0) FROM `tab{MATERIAL_REQUEST_ITEM_DOCTYPE}` WHERE parent=%s",
					(row.name,),
				)[0][0]
			)
		payload["purchase_orders"] = _inv_material_request_purchases(row.name)
		result.append(payload)
	return {"requests": result, "count": len(result), "doctype_available": True}


@frappe.whitelist()
def get_management_material_request(name=""):
	_ensure_management_access()
	name = str(name or "").strip()
	if not frappe.db.exists(MATERIAL_REQUEST_DOCTYPE, name):
		frappe.throw(_("درخواست مواد یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(MATERIAL_REQUEST_DOCTYPE, name)
	return {
		"request": _inv_material_request_payload(doc),
		"purchase_orders": _inv_material_request_purchases(name),
	}


def _inv_set_doc_field(doc, fieldname, value):
	if doc.meta.get_field(fieldname):
		doc.set(fieldname, value)


@frappe.whitelist()
def save_management_material_request(payload=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", MATERIAL_REQUEST_DOCTYPE):
		frappe.throw(_("داکتایپ Material Request در ERPNext فعال نیست."))
	data = _inv_parse_payload(payload)
	name = str(data.get("name") or "").strip()
	if name:
		if not frappe.db.exists(MATERIAL_REQUEST_DOCTYPE, name):
			frappe.throw(_("درخواست مواد یافت نشد: {0}").format(name))
		doc = frappe.get_doc(MATERIAL_REQUEST_DOCTYPE, name)
		if cint(doc.docstatus) != 0:
			frappe.throw(_("فقط درخواست‌های پیش‌نویس قابل ویرایش هستند."))
	else:
		doc = frappe.new_doc(MATERIAL_REQUEST_DOCTYPE)

	company = str(data.get("company") or _inv_default_company() or "").strip()
	if not company:
		frappe.throw(_("شرکت پیش‌فرض برای درخواست مواد مشخص نشده است."))
	transaction_date = data.get("transaction_date") or today()
	schedule_date = data.get("schedule_date") or transaction_date
	_inv_set_doc_field(doc, "material_request_type", str(data.get("material_request_type") or "Purchase"))
	_inv_set_doc_field(doc, "company", company)
	_inv_set_doc_field(doc, "requested_by", str(data.get("requested_by") or frappe.session.user or "").strip())
	_inv_set_doc_field(doc, "transaction_date", transaction_date)
	_inv_set_doc_field(doc, "schedule_date", schedule_date)
	_inv_set_doc_field(doc, "set_warehouse", str(data.get("set_warehouse") or "").strip())
	_inv_set_doc_field(doc, "remarks", str(data.get("note") or "").strip())
	_inv_set_doc_field(doc, "description", str(data.get("note") or "").strip())

	doc.set("items", [])
	valid_rows = 0
	for line in _inv_normalize_list(data.get("items")):
		item_code = _inv_clean_item_code(line.get("item_code"))
		qty = flt(line.get("qty"))
		if not item_code or qty <= 0 or not frappe.db.exists("Item", item_code):
			continue
		meta = frappe.db.get_value("Item", item_code, ["item_name", "stock_uom"], as_dict=True) or {}
		uom = str(line.get("uom") or meta.get("stock_uom") or "").strip()
		# Always resolve the ERPNext conversion for the selected UOM. The
		# frontend sends the default factor as a convenience, but a cashier may
		# change the UOM before saving the request.
		factor = flt(_item_uom_conversion_to_stock(item_code, uom) or 0)
		if factor <= 0:
			factor = flt(line.get("conversion_factor") or 1)
		row = doc.append("items", {})
		_inv_set_doc_field(row, "item_code", item_code)
		_inv_set_doc_field(row, "item_name", meta.get("item_name") or item_code)
		_inv_set_doc_field(row, "description", str(line.get("description") or "").strip())
		_inv_set_doc_field(row, "qty", qty)
		_inv_set_doc_field(row, "uom", uom)
		_inv_set_doc_field(row, "stock_uom", meta.get("stock_uom") or uom)
		_inv_set_doc_field(row, "conversion_factor", factor)
		_inv_set_doc_field(row, "warehouse", str(line.get("warehouse") or data.get("set_warehouse") or "").strip())
		_inv_set_doc_field(row, "schedule_date", line.get("schedule_date") or schedule_date)
		_inv_set_doc_field(row, "rate", flt(line.get("rate") or 0))
		_inv_set_doc_field(row, "amount", flt(line.get("amount") or 0))
		valid_rows += 1

	if not valid_rows:
		frappe.throw(_("حداقل یک ماده معتبر با مقدار بیشتر از صفر لازم است."))

	doc.flags.ignore_permissions = True
	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	if cint(data.get("submit") or 0) == 1 and cint(doc.docstatus) == 0:
		doc.submit()
	frappe.db.commit()
	return {"status": "success", "request": _inv_material_request_payload(doc)}


@frappe.whitelist()
def update_management_material_request_status(payload=None):
	_ensure_management_access()
	data = _inv_parse_payload(payload)
	name = str(data.get("name") or "").strip()
	action = str(data.get("action") or data.get("status") or "").strip().lower()
	if not frappe.db.exists(MATERIAL_REQUEST_DOCTYPE, name):
		frappe.throw(_("درخواست مواد یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(MATERIAL_REQUEST_DOCTYPE, name)
	doc.flags.ignore_permissions = True
	if action in {"submit", "ثبت", "ثبت نهایی"} and cint(doc.docstatus) == 0:
		doc.submit()
	elif action in {"cancel", "cancelled", "لغو", "لغوشده"} and cint(doc.docstatus) == 1:
		doc.cancel()
	else:
		frappe.throw(_("عملیات وضعیت درخواست مواد مجاز نیست."))
	frappe.db.commit()
	return {"status": "success", "request": _inv_material_request_payload(doc)}


@frappe.whitelist()
def create_management_purchase_from_material_request(payload=None):
	_ensure_management_access()
	data = _inv_parse_payload(payload)
	name = str(data.get("name") or "").strip()
	if not frappe.db.exists(MATERIAL_REQUEST_DOCTYPE, name):
		frappe.throw(_("درخواست مواد یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(MATERIAL_REQUEST_DOCTYPE, name)
	if cint(doc.docstatus) == 2:
		frappe.throw(_("از درخواست لغوشده نمی‌توان سفارش خرید ساخت."))

	selected = {}
	for line in _inv_normalize_list(data.get("items")):
		code = _inv_clean_item_code(line.get("item_code"))
		qty = flt(line.get("qty"))
		if code and qty > 0:
			selected[code] = selected.get(code, 0.0) + qty
	if not selected:
		for row in doc.get("items") or []:
			selected[row.item_code] = selected.get(row.item_code, 0.0) + flt(row.qty)

	purchase_lines = []
	for row in doc.get("items") or []:
		code = row.item_code
		qty = min(flt(row.qty), selected.get(code, 0.0))
		if not code or qty <= 0:
			continue
		purchase_lines.append({
			"item_code": code,
			"qty": qty,
			"uom": row.uom or row.stock_uom or "",
			"rate": flt(row.rate) or _inv_purchase_rate(code),
		})
		selected[code] = max(selected.get(code, 0.0) - qty, 0.0)
	if not purchase_lines:
		frappe.throw(_("هیچ قلمی برای انتقال به خرید انتخاب نشده است."))

	purchase = save_management_purchase_order({
		"supplier": str(data.get("supplier") or "").strip(),
		"target_warehouse": str(data.get("target_warehouse") or doc.get("set_warehouse") or "").strip(),
		"posting_date": today(),
		"note": f"درخواست مواد {name}",
		"items": purchase_lines,
	})
	return {"status": "success", "material_request": name, "purchase": purchase.get("order") or {}}


def _inv_material_request_print_html(payload):
	brand = _management_get_print_brand_settings()
	font_family = html_escape(str(brand.get("print_font_family") or "Peyda"))
	font_size = min(max(cint(brand.get("print_font_size") or 11), 8), 24)
	items = []
	for index, row in enumerate(payload.get("items") or [], 1):
		items.append(
			f"<div class='line'><span class='index'>{index}</span><span class='name'>{html_escape(str(row.get('item_name') or row.get('item_code') or ''))}<small>{html_escape(str(row.get('item_code') or ''))}</small></span><strong>{flt(row.get('qty')):,.3f} {html_escape(str(row.get('uom') or ''))}</strong></div>"
		)
	return f"""
<style>
@page {{ size: 80mm auto; margin: 3mm; }}
* {{ box-sizing: border-box; }}
body {{ direction: rtl; margin: 0; font-family: '{font_family}', Peyda, Tahoma, sans-serif; color: #34261F; font-size: {font_size}px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.receipt {{ width: 74mm; margin: 0 auto; }}
.head {{ text-align: center; border-bottom: 1px dashed #D8C8B4; padding-bottom: 8px; }}
.head h1 {{ margin: 0; font-size: {font_size + 3}px; }}
.head p {{ margin: 3px 0 0; color: #6F7B56; font-size: 10px; }}
.meta {{ display: grid; gap: 3px; padding: 8px 0; border-bottom: 1px dashed #D8C8B4; }}
.meta-row {{ display: flex; justify-content: space-between; gap: 5px; }}
.lines {{ display: grid; gap: 4px; padding: 8px 0; }}
.line {{ display: flex; align-items: flex-start; gap: 5px; padding-bottom: 4px; border-bottom: 1px dotted #E5DCCF; }}
.index {{ width: 18px; height: 18px; flex: 0 0 auto; border-radius: 50%; background: #F3E1DA; text-align: center; font-size: 10px; }}
.name {{ flex: 1; font-weight: 700; }}
.name small {{ display: block; color: #746454; font-size: 9px; font-weight: 400; }}
.line strong {{ white-space: nowrap; font-size: 10px; }}
.total {{ display: flex; justify-content: space-between; border-top: 1px dashed #D8C8B4; padding-top: 6px; font-weight: 800; }}
.note {{ margin-top: 8px; color: #746454; font-size: 10px; white-space: pre-line; }}
</style>
<div class='receipt'>
  <div class='head'><h1>{html_escape(str(brand.get('brand_name') or 'درخواست مواد'))}</h1><p>درخواست مواد اولیه • {html_escape(str(payload.get('name') or ''))}</p></div>
  <div class='meta'><div class='meta-row'><span>تاریخ ثبت</span><strong>{html_escape(str(payload.get('transaction_date') or ''))}</strong></div><div class='meta-row'><span>تاریخ نیاز</span><strong>{html_escape(str(payload.get('schedule_date') or ''))}</strong></div><div class='meta-row'><span>انبار مقصد</span><strong>{html_escape(str(payload.get('set_warehouse') or '—'))}</strong></div></div>
  <div class='lines'>{''.join(items)}</div>
  <div class='total'><span>تعداد اقلام</span><span>{len(payload.get('items') or [])} قلم • {flt(payload.get('total_qty')):,.3f}</span></div>
  {f"<div class='note'>یادداشت: {html_escape(str(payload.get('note') or ''))}</div>" if payload.get('note') else ''}
</div>
"""


@frappe.whitelist()
def get_management_material_request_print(name=""):
	_ensure_management_access()
	result = get_management_material_request(name)
	return {"status": "success", "name": name, "html": _inv_material_request_print_html(result["request"])}


# ---------------------------------------------------------------------------
# Raw materials
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_raw_materials(search="", include_inactive=0, limit=100, offset=0, include_all_stock=0):
	"""List raw materials with live stock quantity and value."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 100, 1), 500)
	offset = max(cint(offset) or 0, 0)

	fields = ["name", "item_name", "item_group", "stock_uom", "disabled", "is_stock_item"]
	if _has_column("Item", "restaurant_enabled"):
		fields.append("restaurant_enabled")
	if _has_column("Item", "restaurant_raw_material"):
		fields.append("restaurant_raw_material")
	if _has_column("Item", "restaurant_purchase_rate"):
		fields.append("restaurant_purchase_rate")
	if _has_column("Item", "restaurant_default_supplier"):
		fields.append("restaurant_default_supplier")

	filters = {"is_stock_item": 1}
	if not cint(include_inactive):
		filters["disabled"] = 0
	search = (search or "").strip()
	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = {"name": ["like", like], "item_name": ["like", like], "item_group": ["like", like]}

	rows = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="item_name",
		limit_start=offset,
		limit_page_length=limit + 1,
	)
	has_more = len(rows) > limit
	rows = rows[:limit]

	materials = rows if cint(include_all_stock) else [row for row in rows if _inv_item_is_raw_material(row)]
	names = [row["name"] for row in materials]
	stock = _inv_stock_map(item_codes=names)

	reorder_map = {}
	if names and frappe.db.exists("DocType", "Item Reorder"):
		for row in frappe.get_all(
			"Item Reorder",
			filters={"parent": ["in", names], "parenttype": "Item"},
			fields=["parent", "warehouse", "warehouse_reorder_level", "warehouse_reorder_qty"],
		):
			reorder_map.setdefault(row["parent"], []).append(
				{
					"warehouse": row.get("warehouse") or "",
					"level": flt(row.get("warehouse_reorder_level")),
					"request_qty": flt(row.get("warehouse_reorder_qty")),
				}
			)

	items = []
	for row in materials:
		code = row["name"]
		stock_row = stock.get(code) or {"qty": 0.0, "value": 0.0, "rate": 0.0, "warehouses": {}}
		reorders = reorder_map.get(code) or []
		levels = [flt(r["level"]) for r in reorders if flt(r["level"]) > 0]
		below = any(
			flt(r["level"]) > 0
			and flt((stock_row.get("warehouses") or {}).get(r["warehouse"], {}).get("qty", 0.0)) <= flt(r["level"])
			for r in reorders
		)
		rate = flt(row.get("restaurant_purchase_rate")) or _inv_purchase_rate(code)
		items.append(
			{
				"name": code,
				"item_name": row.get("item_name") or code,
				"item_group": row.get("item_group") or "",
				"stock_uom": row.get("stock_uom") or "",
				"disabled": cint(row.get("disabled") or 0),
				"qty": flt(stock_row["qty"]),
				"value": flt(stock_row["value"]),
				"rate": flt(stock_row["rate"]),
				"purchase_rate": flt(rate),
				"default_supplier": row.get("restaurant_default_supplier") or _inv_default_supplier(code),
				"reorder_levels": reorders,
				"min_reorder_level": min(levels) if levels else 0.0,
				"below_reorder": bool(below),
				"warehouses": stock_row.get("warehouses") or {},
			}
		)

	return {
		"items": items,
		"has_more": has_more,
		"count": len(items),
		"total_value": flt(sum(row["value"] for row in items)),
	}


@frappe.whitelist()
def get_management_raw_material_detail(item_code=""):
	"""Single material detail: stock per warehouse + latest movements."""
	_ensure_management_access()
	item_code = _inv_clean_item_code(item_code)
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(_("ماده اولیه یافت نشد: {0}").format(item_code or "-"))

	doc = frappe.get_doc("Item", item_code)
	stock = _inv_stock_map(item_codes=[item_code]).get(item_code) or {
		"qty": 0.0,
		"value": 0.0,
		"rate": 0.0,
		"warehouses": {},
	}

	movements = frappe.db.sql(
		"""
		SELECT posting_date, posting_time, warehouse, actual_qty, stock_value_difference,
			   voucher_type, voucher_no
		FROM `tabStock Ledger Entry`
		WHERE item_code=%s AND is_cancelled=0
		ORDER BY posting_date DESC, posting_time DESC LIMIT 15
		""",
		(item_code,),
		as_dict=True,
	)

	reorder_levels = []
	if frappe.db.exists("DocType", "Item Reorder"):
		reorder_levels = [
			{
				"warehouse": row.get("warehouse") or "",
				"level": flt(row.get("warehouse_reorder_level")),
				"request_qty": flt(row.get("warehouse_reorder_qty")),
			}
			for row in (doc.get("reorder_levels") or [])
		]

	return {
		"name": doc.name,
		"item_name": doc.item_name or doc.name,
		"item_group": doc.get("item_group") or "",
		"stock_uom": doc.get("stock_uom") or "",
		"disabled": cint(doc.get("disabled") or 0),
		"is_stock_item": cint(doc.get("is_stock_item") or 0),
		"is_raw_material": bool(_inv_item_is_raw_material(doc.as_dict())),
		"purchase_rate": _inv_purchase_rate(doc.name),
		"default_supplier": _inv_default_supplier(doc.name),
		"qty": flt(stock["qty"]),
		"value": flt(stock["value"]),
		"rate": flt(stock["rate"]),
		"warehouses": stock.get("warehouses") or {},
		"reorder_levels": reorder_levels,
		"movements": [
			{
				"posting_date": str(row.get("posting_date") or ""),
				"posting_time": str(row.get("posting_time") or ""),
				"warehouse": row.get("warehouse") or "",
				"qty_change": flt(row.get("actual_qty")),
				"value_change": flt(row.get("stock_value_difference")),
				"voucher": row.get("voucher_no") or "",
				"voucher_type": row.get("voucher_type") or "",
			}
			for row in movements
		],
	}


def _inv_upsert_raw_material(payload):
	"""Create/update an Item as a raw material. No guard/commit (used by bulk import too)."""
	item_code = _inv_clean_item_code(payload.get("name") or payload.get("item_code"))
	item_name = (payload.get("item_name") or "").strip()
	if not item_name:
		frappe.throw(_("نام ماده اولیه الزامی است."))

	created = False
	if item_code and frappe.db.exists("Item", item_code):
		doc = frappe.get_doc("Item", item_code)
	else:
		item_code = item_code or item_name
		if frappe.db.exists("Item", item_code):
			frappe.throw(_("کالایی با این کد از قبل وجود دارد: {0}").format(item_code))
		doc = frappe.new_doc("Item")
		doc.item_code = item_code
		doc.item_name = item_name
		doc.is_stock_item = 1
		doc.is_sales_item = 0
		doc.is_purchase_item = 1
		created = True

	doc.item_name = item_name
	if payload.get("item_group"):
		doc.item_group = (payload.get("item_group") or "").strip()
	elif created and not doc.item_group:
		groups = frappe.get_all("Item Group", pluck="name", limit_page_length=1)
		doc.item_group = groups[0] if groups else "All Item Groups"
	if payload.get("stock_uom"):
		doc.stock_uom = (payload.get("stock_uom") or "").strip()
	elif created and not doc.stock_uom:
		doc.stock_uom = "Nos"
	doc.is_stock_item = 1
	doc.disabled = cint(payload.get("disabled") or 0)

	if _has_column("Item", "restaurant_raw_material"):
		doc.restaurant_raw_material = 1
	if _has_column("Item", "restaurant_enabled"):
		doc.restaurant_enabled = 0
	if _has_column("Item", "include_item_in_manufacturing"):
		doc.include_item_in_manufacturing = 1
	if _has_column("Item", "restaurant_purchase_rate") and payload.get("purchase_rate") is not None:
		doc.restaurant_purchase_rate = flt(payload.get("purchase_rate"))
	if _has_column("Item", "restaurant_default_supplier") and payload.get("default_supplier"):
		supplier = (payload.get("default_supplier") or "").strip()
		if supplier and frappe.db.exists("Supplier", supplier):
			doc.restaurant_default_supplier = supplier

	if frappe.db.exists("DocType", "Item Reorder") and "reorder_levels" in payload:
		doc.set("reorder_levels", [])
		for row in _inv_normalize_list(payload.get("reorder_levels")):
			warehouse = (row.get("warehouse") or "").strip()
			if not warehouse or not _inv_warehouse_exists(warehouse):
				continue
			doc.append(
				"reorder_levels",
				{
					"warehouse": warehouse,
					"warehouse_reorder_level": flt(row.get("level")),
					"warehouse_reorder_qty": flt(row.get("request_qty")),
					"material_request_type": "Purchase",
				},
			)

	doc.save(ignore_permissions=True)

	opening = payload.get("opening") if isinstance(payload.get("opening"), dict) else None
	opening_entry = None
	if created and opening and flt(opening.get("qty")) > 0:
		warehouse = (opening.get("warehouse") or "").strip()
		if warehouse and _inv_warehouse_exists(warehouse):
			entry = _inv_build_stock_entry(
				entry_type="Material Receipt",
				kind_label=STOCK_MOVEMENT_KINDS["manual_receipt"],
				lines=[{"item_code": doc.name, "qty": flt(opening.get("qty")), "rate": flt(opening.get("rate") or payload.get("purchase_rate"))}],
				target_warehouse=warehouse,
				note=_("موجودی اولیه ماده اولیه"),
			)
			opening_entry = entry.name

	return {
		"created": created,
		"item_code": doc.name,
		"opening_entry": opening_entry or "",
	}


@frappe.whitelist()
def save_management_raw_material(payload=None):
	"""Create or update a raw material (unlimited registry)."""
	_ensure_management_access()
	_inv_ensure_item_fields()
	result = _inv_upsert_raw_material(_inv_parse_payload(payload))
	frappe.db.commit()
	return {"status": "success", **result}


# ---------------------------------------------------------------------------
# Warehouses (unlimited)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_warehouses():
	"""All warehouses with quantity/value aggregates."""
	_ensure_management_access()
	rows = frappe.get_all(
		"Warehouse",
		fields=["name", "warehouse_name", "parent_warehouse", "is_group", "disabled", "company"],
		order_by="name",
		limit_page_length=1000,
	)
	stats = frappe.db.sql(
		"""
		SELECT warehouse, COALESCE(SUM(actual_qty),0) AS qty, COALESCE(SUM(stock_value),0) AS value
		FROM `tabBin`
		GROUP BY warehouse
		""",
		as_dict=True,
	)
	stat_map = {row["warehouse"]: row for row in stats}
	items = []
	for row in rows:
		stat = stat_map.get(row["name"]) or {}
		items.append(
			{
				"name": row["name"],
				"warehouse_name": row.get("warehouse_name") or row["name"],
				"parent_warehouse": row.get("parent_warehouse") or "",
				"is_group": cint(row.get("is_group") or 0),
				"disabled": cint(row.get("disabled") or 0),
				"company": row.get("company") or "",
				"qty": flt(stat.get("qty")),
				"value": flt(stat.get("value")),
			}
		)
	return {"warehouses": items, "count": len(items)}


@frappe.whitelist()
def save_management_warehouse(payload=None):
	"""Create or update a warehouse."""
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	warehouse_name = (payload.get("warehouse_name") or "").strip()
	if not warehouse_name and not name:
		frappe.throw(_("نام انبار الزامی است."))

	created = False
	if name and frappe.db.exists("Warehouse", name):
		doc = frappe.get_doc("Warehouse", name)
		if warehouse_name and warehouse_name != doc.warehouse_name:
			doc.warehouse_name = warehouse_name
	else:
		doc = frappe.new_doc("Warehouse")
		doc.warehouse_name = warehouse_name
		doc.company = (payload.get("company") or "").strip() or _inv_default_company()
		if not doc.company:
			frappe.throw(_("برای ساخت انبار ابتدا شرکت (Company) را تعریف کنید."))
		created = True

	if payload.get("parent_warehouse") is not None:
		parent = (payload.get("parent_warehouse") or "").strip()
		doc.parent_warehouse = parent if parent and _inv_warehouse_exists(parent) else None
	doc.is_group = cint(payload.get("is_group") or 0)
	doc.disabled = cint(payload.get("disabled") or 0)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "created": created, "name": doc.name}


@frappe.whitelist()
def delete_management_warehouse(name=""):
	"""Delete a warehouse (or disable it when ledger data exists)."""
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists("Warehouse", name):
		frappe.throw(_("انبار یافت نشد: {0}").format(name or "-"))
	if frappe.db.get_value("Warehouse", name, "is_group") and frappe.db.exists("Warehouse", {"parent_warehouse": name}):
		frappe.throw(_("این انبار گروه است و زیرمجموعه دارد؛ ابتدا زیرمجموعه‌ها را جابه‌جا کنید."))

	bin_qty = flt(
		frappe.db.sql(
			"SELECT COALESCE(SUM(actual_qty),0) FROM `tabBin` WHERE warehouse=%s", (name,)
		)[0][0]
	)
	if abs(bin_qty) > 1e-9:
		frappe.throw(_("انبار دارای موجودی است و قابل حذف نیست؛ آن را غیرفعال کنید."))

	has_sle = frappe.db.exists("Stock Ledger Entry", {"warehouse": name, "is_cancelled": 0})
	if has_sle:
		frappe.db.set_value("Warehouse", name, "disabled", 1, update_modified=False)
		frappe.db.commit()
		return {"status": "success", "disabled": True, "name": name}

	frappe.delete_doc("Warehouse", name, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"status": "success", "deleted": True, "name": name}


# ---------------------------------------------------------------------------
# Stock overview (quantity + monetary)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_stock_overview(warehouse="", search="", only_materials=0, limit=400, offset=0):
	"""Live stock levels: quantity and value per item (optionally per warehouse)."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 400, 1), 1000)
	offset = max(cint(offset) or 0, 0)

	search = (search or "").strip()
	warehouse = (warehouse or "").strip()

	bin_rows = frappe.db.sql(
		"""
		SELECT item_code, warehouse, actual_qty, valuation_rate, stock_value
		FROM `tabBin`
		WHERE (%(warehouse)s = '' OR warehouse = %(warehouse)s)
		  AND actual_qty != 0
		ORDER BY item_code
		""",
		{"warehouse": warehouse if _inv_warehouse_exists(warehouse) else ""},
		as_dict=True,
	)

	by_item = {}
	for row in bin_rows:
		bucket = by_item.setdefault(
			row["item_code"], {"qty": 0.0, "value": 0.0, "warehouses": {}}
		)
		bucket["qty"] += flt(row.get("actual_qty"))
		bucket["value"] += flt(row.get("stock_value"))
		bucket["warehouses"][row.get("warehouse")] = {
			"qty": flt(row.get("actual_qty")),
			"value": flt(row.get("stock_value")),
			"rate": flt(row.get("valuation_rate")),
		}

	codes = list(by_item.keys())
	meta = _inv_item_meta(codes)
	if _has_column("Item", "restaurant_raw_material") and cint(only_materials):
		raw_flags = {
			row["name"]: row
			for row in frappe.get_all(
				"Item",
				filters={"name": ["in", codes]},
				fields=["name", "restaurant_enabled", "restaurant_raw_material"],
			)
		}
		codes = [code for code in codes if raw_flags.get(code) and _inv_item_is_raw_material(raw_flags[code])]

	if search:
		needle = search.lower()
		codes = [
			code
			for code in codes
			if needle in code.lower()
			or needle in ((meta.get(code) or {}).get("item_name") or "").lower()
		]
	codes.sort(key=lambda code: ((meta.get(code) or {}).get("item_name") or code))

	total_filtered = len(codes)
	paged = codes[offset : offset + limit]

	items = []
	for code in paged:
		bucket = by_item[code]
		info = meta.get(code) or {}
		items.append(
			{
				"item_code": code,
				"item_name": info.get("item_name") or code,
				"stock_uom": info.get("stock_uom") or "",
				"qty": flt(bucket["qty"]),
				"value": flt(bucket["value"]),
				"rate": flt(bucket["value"] / bucket["qty"], 6) if bucket["qty"] else 0.0,
				"warehouses": bucket["warehouses"],
			}
		)

	return {
		"items": items,
		"total_items": total_filtered,
		"count": len(items),
		"total_value": flt(sum(by_item[code]["value"] for code in codes)),
		"total_qty": flt(sum(by_item[code]["qty"] for code in codes)),
	}


# ---------------------------------------------------------------------------
# Manual movements (receipt / issue / transfer / waste / damage)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def create_management_stock_movement(payload=None):
	"""Manual stock in/out/transfer plus waste & damage posting."""
	_ensure_management_access()
	_inv_ensure_stock_entry_fields()
	payload = _inv_parse_payload(payload)

	movement_type = (payload.get("movement_type") or "").strip()
	settings = _inv_get_inventory_settings()
	lines = _inv_normalize_list(payload.get("lines"))
	note = (payload.get("reason") or payload.get("note") or "").strip()
	posting_date = (payload.get("posting_date") or "").strip() or today()

	source = (payload.get("from_warehouse") or "").strip()
	target = (payload.get("to_warehouse") or "").strip()

	if movement_type == "receipt":
		target = _inv_resolve_warehouse(target)
		if not target:
			frappe.throw(_("انبار مقصد برای ورود کالا انتخاب نشده است."))
		entry_type, kind = "Material Receipt", STOCK_MOVEMENT_KINDS["manual_receipt"]
	elif movement_type == "issue":
		source = _inv_resolve_warehouse(source)
		if not source:
			frappe.throw(_("انبار مبدأ برای خروج کالا انتخاب نشده است."))
		entry_type, kind = "Material Issue", STOCK_MOVEMENT_KINDS["manual_issue"]
	elif movement_type == "transfer":
		if not (_inv_warehouse_exists(source) and _inv_warehouse_exists(target)):
			frappe.throw(_("برای انتقال، هر دو انبار مبدأ و مقصد باید مشخص باشند."))
		if source == target:
			frappe.throw(_("انبار مبدأ و مقصد نمی‌توانند یکسان باشند."))
		entry_type, kind = "Material Transfer", STOCK_MOVEMENT_KINDS["transfer"]
	elif movement_type == "waste":
		source = _inv_resolve_warehouse(source)
		if not source:
			frappe.throw(_("انبار مبدأ برای ثبت ضایعات انتخاب نشده است."))
		kind = STOCK_MOVEMENT_KINDS["waste"]
		if settings["waste_as_transfer"] and settings["waste_warehouse"] and _inv_warehouse_exists(settings["waste_warehouse"]):
			entry_type, target = "Material Transfer", settings["waste_warehouse"]
		else:
			entry_type = "Material Issue"
	elif movement_type == "damage":
		source = _inv_resolve_warehouse(source)
		if not source:
			frappe.throw(_("انبار مبدأ برای ثبت خسارت انتخاب نشده است."))
		entry_type, kind = "Material Issue", STOCK_MOVEMENT_KINDS["damage"]
	else:
		frappe.throw(_("نوع گردش نامعتبر است: {0}").format(movement_type or "-"))

	entry = _inv_safe_execute(
		lambda: _inv_build_stock_entry(
			entry_type=entry_type,
			kind_label=kind,
			lines=lines,
			source_warehouse=source if entry_type != "Material Receipt" else "",
			target_warehouse=target if entry_type != "Material Issue" else "",
			note=note,
			posting_date=posting_date,
		),
		_("ثبت گردش انبار ناموفق بود"),
	)
	frappe.db.commit()
	return {"status": "success", "stock_entry": _inv_stock_entry_payload(entry)}


@frappe.whitelist()
def list_management_stock_movements(
	date_from="",
	date_to="",
	warehouse="",
	item_code="",
	kind="",
	limit=50,
	offset=0,
):
	"""Classified stock movement history (from Stock Ledger Entries)."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 50, 1), 300)
	offset = max(cint(offset) or 0, 0)

	has_kind_col = _has_column("Stock Entry", "restaurant_movement_kind")
	kind_labels = [STOCK_MOVEMENT_KINDS.get(k, k) for k in _inv_normalize_list(kind) if k]
	kind_labels += [k.strip() for k in (kind or "").split(",") if k.strip() and not STOCK_MOVEMENT_KINDS.get(k.strip())] if isinstance(kind, str) else []
	kind_labels = sorted({k for k in kind_labels if k in MOVEMENT_KIND_LABELS})

	conditions = ["sle.voucher_type = 'Stock Entry'", "sle.is_cancelled = 0"]
	params = {"limit": limit, "offset": offset}
	if has_kind_col and kind_labels:
		conditions.append("se.restaurant_movement_kind IN %(kinds)s")
		params["kinds"] = tuple(kind_labels)
	elif has_kind_col:
		conditions.append("COALESCE(se.restaurant_movement_kind,'') != ''")
	else:
		conditions.append("se.stock_entry_type IN ('Material Receipt','Material Issue','Material Transfer')")

	if date_from:
		conditions.append("sle.posting_date >= %(date_from)s")
		params["date_from"] = getdate(date_from)
	if date_to:
		conditions.append("sle.posting_date <= %(date_to)s")
		params["date_to"] = getdate(date_to)
	if warehouse and _inv_warehouse_exists(warehouse):
		conditions.append("sle.warehouse = %(warehouse)s")
		params["warehouse"] = warehouse
	if _inv_clean_item_code(item_code):
		conditions.append("sle.item_code = %(item_code)s")
		params["item_code"] = _inv_clean_item_code(item_code)

	kind_select = "se.restaurant_movement_kind" if has_kind_col else "se.stock_entry_type"
	note_select = "se.restaurant_reference_note" if _has_column("Stock Entry", "restaurant_reference_note") else "se.remarks"

	rows = frappe.db.sql(
		"""
		SELECT sle.posting_date, sle.posting_time, sle.item_code, sle.warehouse,
			   sle.actual_qty, sle.stock_value_difference, sle.voucher_no,
			   {kind_select} AS movement_kind, {note_select} AS note,
			   i.item_name, i.stock_uom
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		LEFT JOIN `tabItem` i ON i.name = sle.item_code
		WHERE {conditions}
		ORDER BY sle.posting_date DESC, sle.posting_time DESC
		LIMIT %(limit)s OFFSET %(offset)s
		""".format(
			kind_select=kind_select,
			note_select=note_select,
			conditions=" AND ".join(conditions),
		),
		params,
		as_dict=True,
	)

	return {
		"movements": [
			{
				"posting_date": str(row.get("posting_date") or ""),
				"posting_time": str(row.get("posting_time") or ""),
				"item_code": row.get("item_code") or "",
				"item_name": row.get("item_name") or row.get("item_code") or "",
				"stock_uom": row.get("stock_uom") or "",
				"warehouse": row.get("warehouse") or "",
				"qty_change": flt(row.get("actual_qty")),
				"value_change": flt(row.get("stock_value_difference")),
				"voucher": row.get("voucher_no") or "",
				"kind": row.get("movement_kind") or "",
				"note": row.get("note") or "",
			}
			for row in rows
		],
		"count": len(rows),
	}


# ---------------------------------------------------------------------------
# Suppliers & purchase orders
# ---------------------------------------------------------------------------


@frappe.whitelist()
def list_management_suppliers(search="", limit=100, offset=0):
	_ensure_management_access()
	search = (search or "").strip()
	filters = {}
	or_filters = {"name": ["like", f"%{search}%"], "supplier_name": ["like", f"%{search}%"]} if search else None
	rows = frappe.get_all(
		"Supplier",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "supplier_name", "supplier_group", "disabled"],
		order_by="supplier_name",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 500),
	)
	return {"suppliers": rows, "count": len(rows)}


@frappe.whitelist()
def save_management_supplier(payload=None):
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	supplier_name = (payload.get("supplier_name") or "").strip()
	if not supplier_name:
		frappe.throw(_("نام تأمین‌کننده الزامی است."))

	created = False
	if name and frappe.db.exists("Supplier", name):
		doc = frappe.get_doc("Supplier", name)
	else:
		if frappe.db.exists("Supplier", supplier_name):
			doc = frappe.get_doc("Supplier", supplier_name)
		else:
			doc = frappe.new_doc("Supplier")
			doc.supplier_name = supplier_name
			created = True
	doc.supplier_name = supplier_name
	if payload.get("supplier_group"):
		group = (payload.get("supplier_group") or "").strip()
		if group and frappe.db.exists("Supplier Group", group):
			doc.supplier_group = group
	if not doc.get("supplier_group"):
		groups = frappe.get_all("Supplier Group", pluck="name", limit_page_length=1)
		if groups:
			doc.supplier_group = groups[0]
	doc.disabled = cint(payload.get("disabled") or 0)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "created": created, "name": doc.name}


def _inv_po_doc_payload(doc, include_items=True):
	receipts = []
	try:
		receipts = json.loads(doc.get("received_entries_json") or "[]")
	except Exception:
		receipts = []
	payload = {
		"name": doc.name,
		"supplier": doc.get("supplier") or "",
		"supplier_name": doc.get("supplier_name") or doc.get("supplier") or "",
		"posting_date": str(doc.get("posting_date") or ""),
		"expected_date": str(doc.get("expected_date") or ""),
		"status": doc.get("status") or PURCHASE_STATUS_DRAFT,
		"target_warehouse": doc.get("target_warehouse") or "",
		"total_qty": flt(doc.get("total_qty")),
		"grand_total": flt(doc.get("grand_total")),
		"note": doc.get("note") or "",
		"receipts": receipts,
		"received_qty_total": 0.0,
		"received_pct": 0.0,
	}
	if include_items:
		items = []
		received_total = 0.0
		qty_total = 0.0
		for row in doc.get("items") or []:
			received_qty = flt(row.get("received_qty"))
			qty = flt(row.get("qty"))
			received_total += received_qty
			qty_total += qty
			items.append(
				{
					"idx": row.get("idx"),
					"item_code": row.get("item_code"),
					"item_name": row.get("item_name") or row.get("item_code"),
					"uom": row.get("uom") or "",
					"qty": qty,
					"rate": flt(row.get("rate")),
					"amount": flt(row.get("amount")),
					"received_qty": received_qty,
					"remaining_qty": max(qty - received_qty, 0.0),
				}
			)
		payload["items"] = items
		payload["received_qty_total"] = received_total
		payload["received_pct"] = flt((received_total / qty_total) * 100, 1) if qty_total else 0.0
	return payload


@frappe.whitelist()
def list_management_purchase_orders(status="", search="", limit=50, offset=0):
	_ensure_management_access()
	limit = min(max(cint(limit) or 50, 1), 200)
	offset = max(cint(offset) or 0, 0)
	filters = {}
	if status and status in PURCHASE_ORDER_STATUSES:
		filters["status"] = status
	rows = frappe.get_all(
		PURCHASE_ORDER_DOCTYPE,
		filters=filters,
		fields=["name", "supplier", "supplier_name", "posting_date", "status", "total_qty", "grand_total"],
		order_by="creation desc",
		limit_start=offset,
		limit_page_length=limit,
	)
	search = (search or "").strip()
	if search:
		needle = search.lower()
		rows = [
			row
			for row in rows
			if needle in (row.get("name") or "").lower() or needle in (row.get("supplier_name") or "").lower()
		]
	return {
		"orders": [
			{
				"name": row["name"],
				"supplier": row.get("supplier") or "",
				"supplier_name": row.get("supplier_name") or row.get("supplier") or "",
				"posting_date": str(row.get("posting_date") or ""),
				"status": row.get("status") or PURCHASE_STATUS_DRAFT,
				"total_qty": flt(row.get("total_qty")),
				"grand_total": flt(row.get("grand_total")),
			}
			for row in rows
		],
		"count": len(rows),
	}


@frappe.whitelist()
def get_management_purchase_order(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(PURCHASE_ORDER_DOCTYPE, name):
		frappe.throw(_("سفارش خرید یافت نشد: {0}").format(name or "-"))
	return {"order": _inv_po_doc_payload(frappe.get_doc(PURCHASE_ORDER_DOCTYPE, name))}


@frappe.whitelist()
def save_management_purchase_order(payload=None):
	"""Create or update a draft purchase order for raw materials."""
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	name = (payload.get("name") or "").strip()

	if name:
		if not frappe.db.exists(PURCHASE_ORDER_DOCTYPE, name):
			frappe.throw(_("سفارش خرید یافت نشد: {0}").format(name))
		doc = frappe.get_doc(PURCHASE_ORDER_DOCTYPE, name)
		if doc.status != PURCHASE_STATUS_DRAFT:
			frappe.throw(_("فقط سفارش‌های پیش‌نویس قابل ویرایش هستند."))
	else:
		doc = frappe.new_doc(PURCHASE_ORDER_DOCTYPE)

	supplier = (payload.get("supplier") or "").strip()
	if supplier and not frappe.db.exists("Supplier", supplier):
		frappe.throw(_("تأمین‌کننده یافت نشد: {0}").format(supplier))
	doc.supplier = supplier or None
	doc.supplier_name = frappe.db.get_value("Supplier", supplier, "supplier_name") if supplier else ""
	doc.posting_date = payload.get("posting_date") or today()
	doc.expected_date = payload.get("expected_date") or ""
	warehouse = (payload.get("target_warehouse") or "").strip()
	if warehouse and _inv_warehouse_exists(warehouse):
		doc.target_warehouse = warehouse
	doc.note = (payload.get("note") or "").strip()

	doc.set("items", [])
	total_qty = 0.0
	grand_total = 0.0
	for line in _inv_normalize_list(payload.get("items")):
		item_code = _inv_clean_item_code(line.get("item_code"))
		if not item_code or not frappe.db.exists("Item", item_code):
			continue
		qty = flt(line.get("qty"))
		if qty <= 0:
			continue
		rate = flt(line.get("rate")) or _inv_purchase_rate(item_code)
		row = doc.append("items", {})
		row.item_code = item_code
		row.item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
		row.uom = (line.get("uom") or "").strip() or (frappe.db.get_value("Item", item_code, "stock_uom") or "")
		row.qty = qty
		row.rate = rate
		row.amount = flt(qty * rate)
		row.received_qty = 0
		total_qty += qty
		grand_total += row.amount

	if not doc.items:
		frappe.throw(_("حداقل یک قلم معتبر برای سفارش خرید لازم است."))
	doc.total_qty = flt(total_qty)
	doc.grand_total = flt(grand_total)
	doc.status = PURCHASE_STATUS_DRAFT
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "order": _inv_po_doc_payload(doc)}


@frappe.whitelist()
def update_management_purchase_order_status(payload=None):
	"""Send or cancel a purchase order."""
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	target_status = (payload.get("status") or "").strip()
	if not frappe.db.exists(PURCHASE_ORDER_DOCTYPE, name):
		frappe.throw(_("سفارش خرید یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(PURCHASE_ORDER_DOCTYPE, name)

	allowed = {
		PURCHASE_STATUS_SENT: [PURCHASE_STATUS_DRAFT],
		PURCHASE_STATUS_CANCELLED: [PURCHASE_STATUS_DRAFT, PURCHASE_STATUS_SENT],
		PURCHASE_STATUS_DRAFT: [PURCHASE_STATUS_SENT],
	}
	if target_status not in allowed:
		frappe.throw(_("وضعیت نامعتبر است: {0}").format(target_status or "-"))
	if doc.status not in allowed[target_status]:
		frappe.throw(_("تغییر وضعیت از «{0}» به «{1}» مجاز نیست.").format(doc.status, target_status))
	doc.status = target_status
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "order": _inv_po_doc_payload(doc)}


@frappe.whitelist()
def receive_management_purchase_order(payload=None):
	"""Receive (partially or fully) against a purchase order → Material Receipt."""
	_ensure_management_access()
	_inv_ensure_stock_entry_fields()
	payload = _inv_parse_payload(payload)
	name = (payload.get("name") or "").strip()
	if not frappe.db.exists(PURCHASE_ORDER_DOCTYPE, name):
		frappe.throw(_("سفارش خرید یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(PURCHASE_ORDER_DOCTYPE, name)
	if doc.status not in (PURCHASE_STATUS_SENT, PURCHASE_STATUS_PARTIAL):
		frappe.throw(_("دریافت فقط برای سفارش‌های «ارسال‌شده» یا «دریافت جزئی» ممکن است."))

	warehouse = _inv_resolve_warehouse(payload.get("warehouse") or doc.target_warehouse)
	if not warehouse:
		frappe.throw(_("انبار مقصد برای دریافت کالا مشخص نشده است."))

	requested = {}
	for line in _inv_normalize_list(payload.get("lines")):
		key = _inv_clean_item_code(line.get("item_code"))
		qty = flt(line.get("qty"))
		if key and qty > 0:
			requested[key] = requested.get(key, 0.0) + qty
	if not requested:
		frappe.throw(_("هیچ مقدار دریافتی معتبری ارسال نشده است."))

	lines = []
	for row in doc.get("items") or []:
		code = row.get("item_code")
		if code not in requested:
			continue
		remaining = max(flt(row.get("qty")) - flt(row.get("received_qty")), 0.0)
		receive_qty = min(requested.pop(code), remaining)
		if receive_qty <= 0:
			continue
		rate = flt(row.get("rate")) or _inv_purchase_rate(code)
		lines.append({"item_code": code, "qty": receive_qty, "rate": rate})
		row.received_qty = flt(row.get("received_qty")) + receive_qty
		_inv_update_purchase_tracking(code, rate, doc.get("supplier") or "")

	if not lines:
		frappe.throw(_("مقادیر دریافتی از باقی‌مانده اقلام بیشتر است."))

	entry = _inv_safe_execute(
		lambda: _inv_build_stock_entry(
			entry_type="Material Receipt",
			kind_label=STOCK_MOVEMENT_KINDS["purchase_receipt"],
			lines=lines,
			target_warehouse=warehouse,
			note=_("دریافت از سفارش خرید {0}").format(doc.name),
		),
		_("ثبت دریافت خرید ناموفق بود"),
	)

	all_received = all(
		flt(row.get("received_qty")) >= flt(row.get("qty")) - 1e-9 for row in (doc.get("items") or [])
	)
	doc.status = PURCHASE_STATUS_COMPLETE if all_received else PURCHASE_STATUS_PARTIAL
	receipts = []
	try:
		receipts = json.loads(doc.get("received_entries_json") or "[]")
	except Exception:
		receipts = []
	receipts.append(entry.name)
	doc.received_entries_json = json.dumps(receipts)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": "success",
		"stock_entry": _inv_stock_entry_payload(entry),
		"order": _inv_po_doc_payload(doc),
	}


# ---------------------------------------------------------------------------
# Reorder point alerts
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_reorder_alerts(warehouse="", limit=200):
	"""Materials at or below their reorder point, grouped per warehouse."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 200, 1), 1000)
	if not frappe.db.exists("DocType", "Item Reorder"):
		return {"alerts": [], "count": 0}

	warehouse_filter = (warehouse or "").strip()
	conditions = ["ir.warehouse_reorder_level > 0"]
	params = {"limit": limit}
	if warehouse_filter and _inv_warehouse_exists(warehouse_filter):
		conditions.append("ir.warehouse = %(warehouse)s")
		params["warehouse"] = warehouse_filter

	rows = frappe.db.sql(
		"""
		SELECT ir.parent AS item_code, ir.warehouse,
			   ir.warehouse_reorder_level AS level,
			   ir.warehouse_reorder_qty AS request_qty,
			   i.item_name, i.stock_uom, i.disabled
		FROM `tabItem Reorder` ir
		INNER JOIN `tabItem` i ON i.name = ir.parent
		WHERE {conditions} AND i.disabled = 0
		""".format(
			conditions=" AND ".join(conditions)
		),
		params,
		as_dict=True,
	)

	codes = sorted({row["item_code"] for row in rows})
	stock = _inv_stock_map(item_codes=codes)

	alerts = []
	for row in rows:
		code = row["item_code"]
		bucket = stock.get(code) or {}
		wh_qty = flt((bucket.get("warehouses") or {}).get(row["warehouse"], {}).get("qty", 0.0))
		if wh_qty > flt(row["level"]):
			continue
		suggested = flt(row["request_qty"])
		if suggested <= 0:
			suggested = max(flt(row["level"]) * 2 - wh_qty, flt(row["level"]) or 1.0)
		alerts.append(
			{
				"item_code": code,
				"item_name": row.get("item_name") or code,
				"stock_uom": row.get("stock_uom") or "",
				"warehouse": row.get("warehouse") or "",
				"level": flt(row["level"]),
				"available": wh_qty,
				"suggested_qty": flt(suggested, 3),
				"default_supplier": _inv_default_supplier(code),
				"purchase_rate": _inv_purchase_rate(code),
			}
		)
	alerts.sort(key=lambda item: (item["available"] / item["level"]) if item["level"] else 1.0)
	return {"alerts": alerts[:limit], "count": len(alerts[:limit])}


@frappe.whitelist()
def create_management_purchase_from_alerts(payload=None):
	"""Turn reorder alerts into draft purchase orders (grouped per default supplier)."""
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	warehouse = (payload.get("target_warehouse") or "").strip()
	entries = []
	for row in _inv_normalize_list(payload.get("items")):
		item_code = _inv_clean_item_code(row.get("item_code"))
		qty = flt(row.get("qty"))
		if item_code and qty > 0 and frappe.db.exists("Item", item_code):
			entries.append({"item_code": item_code, "qty": qty})
	if not entries:
		frappe.throw(_("قلمی برای ثبت سفارش انتخاب نشده است."))

	by_supplier = {}
	for entry in entries:
		supplier = _inv_default_supplier(entry["item_code"])
		by_supplier.setdefault(supplier, []).append(entry)

	created = []
	for supplier, lines in by_supplier.items():
		result = save_management_purchase_order(
			{
				"supplier": supplier,
				"target_warehouse": warehouse,
				"note": _("ایجاد خودکار از هشدار نقطه سفارش"),
				"items": lines,
			}
		)
		created.append({"supplier": supplier or _("بدون تأمین‌کننده"), "order": result["order"]["name"]})

	return {"status": "success", "created": created, "count": len(created)}


# ---------------------------------------------------------------------------
# Production planning & manual manufacture
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_production_plan(date_from="", date_to=""):
	"""Required raw materials vs. live stock for pending production tickets."""
	_ensure_management_access()
	date_to = getdate(date_to) if date_to else today()
	date_from = getdate(date_from) if date_from else add_days(date_to, -6)

	tickets = frappe.db.sql(
		"""
		SELECT name, menu_item, menu_item_name, qty, status, source_warehouse, DATE(creation) AS day
		FROM `tabRestaurant Production Ticket`
		WHERE status IN ('planned','in_progress')
		  AND DATE(creation) BETWEEN %(df)s AND %(dt)s
		""",
		{"df": date_from, "dt": date_to},
		as_dict=True,
	)
	ticket_names = [row["name"] for row in tickets]

	required = {}
	if ticket_names:
		components = frappe.db.sql(
			"""
			SELECT c.item_code, c.item_name, c.stock_uom, c.source_warehouse, SUM(c.final_qty) AS qty
			FROM `tabRestaurant Production Component` c
			WHERE c.parent IN %(names)s AND c.parenttype = 'Restaurant Production Ticket'
			GROUP BY c.item_code, c.source_warehouse, c.item_name, c.stock_uom
			""",
			{"names": tuple(ticket_names)},
			as_dict=True,
		)
		for row in components:
			code = row.get("item_code")
			if not code:
				continue
			bucket = required.setdefault(
				code,
				{
					"item_name": row.get("item_name") or code,
					"stock_uom": row.get("stock_uom") or "",
					"required": 0.0,
					"warehouses": {},
				},
			)
			bucket["required"] += flt(row.get("qty"))
			if row.get("source_warehouse"):
				bucket["warehouses"][row["source_warehouse"]] = bucket["warehouses"].get(row["source_warehouse"], 0.0) + flt(row.get("qty"))

	stock = _inv_stock_map(item_codes=list(required.keys()))
	materials = []
	for code, bucket in required.items():
		available = flt((stock.get(code) or {}).get("qty"))
		shortage = max(bucket["required"] - available, 0.0)
		materials.append(
			{
				"item_code": code,
				"item_name": bucket["item_name"],
				"stock_uom": bucket["stock_uom"],
				"required": flt(bucket["required"], 3),
				"available": available,
				"shortage": flt(shortage, 3),
				"warehouses": bucket["warehouses"],
			}
		)
	materials.sort(key=lambda row: -row["shortage"])

	products = {}
	for ticket in tickets:
		key = ticket.get("menu_item") or ""
		if not key:
			continue
		bucket = products.setdefault(
			key, {"item_name": ticket.get("menu_item_name") or key, "qty": 0.0, "tickets": 0}
		)
		bucket["qty"] += flt(ticket.get("qty"))
		bucket["tickets"] += 1

	return {
		"date_from": str(date_from),
		"date_to": str(date_to),
		"ticket_count": len(tickets),
		"materials": materials,
		"products": [
			{"menu_item": key, **bucket} for key, bucket in sorted(products.items(), key=lambda kv: -kv[1]["qty"])
		],
		"summary": {
			"materials_required": len(materials),
			"materials_shortage": sum(1 for row in materials if row["shortage"] > 0),
			"tickets": len(tickets),
		},
	}


@frappe.whitelist()
def create_management_production_entry(payload=None):
	"""Manual production: consume recipe materials and book the finished product."""
	_ensure_management_access()
	_inv_ensure_stock_entry_fields()
	payload = _inv_parse_payload(payload)

	bom_name = (payload.get("bom") or "").strip()
	menu_item = _inv_clean_item_code(payload.get("menu_item") or payload.get("item_code"))
	qty = flt(payload.get("qty"))
	if qty <= 0:
		frappe.throw(_("مقدار تولید باید بزرگ‌تر از صفر باشد."))

	if not bom_name and menu_item:
		bom_name = frappe.db.get_value(
			"BOM",
			{"item": menu_item, "is_active": 1, "is_default": 1, "docstatus": 1},
			"name",
		) or frappe.db.get_value(
			"BOM", {"item": menu_item, "is_active": 1, "docstatus": 1}, "name", order_by="creation desc"
		)
	if not bom_name or not frappe.db.exists("BOM", bom_name):
		frappe.throw(_("فرمول تولید (BOM) برای این محصول یافت نشد."))
	bom_doc = frappe.get_doc("BOM", bom_name)
	menu_item = bom_doc.item

	settings = _inv_get_inventory_settings()
	source = _inv_resolve_warehouse(payload.get("source_warehouse") or "", settings["default_warehouse"])
	target = _inv_resolve_warehouse(payload.get("target_warehouse") or "", source)
	if not source or not target:
		frappe.throw(_("انبار مبدأ (مواد اولیه) و مقصد (محصول) را مشخص کنید."))

	def build():
		entry = frappe.new_doc("Stock Entry")
		entry.stock_entry_type = "Manufacture"
		entry.purpose = "Manufacture"
		entry.posting_date = payload.get("posting_date") or today()
		entry.company = bom_doc.company or _inv_default_company()
		entry.bom_no = bom_doc.name
		entry.from_bom = 1
		entry.fg_completed_qty = qty
		entry.from_warehouse = source
		entry.to_warehouse = target
		if _has_column("Stock Entry", "restaurant_movement_kind"):
			entry.restaurant_movement_kind = STOCK_MOVEMENT_KINDS["production"]
		if _has_column("Stock Entry", "restaurant_reference_note"):
			entry.restaurant_reference_note = _("تولید دستی از فرمول {0}").format(bom_doc.name)
		entry.remarks = _("تولید {0} × {1} ({2})").format(flt(qty, 3), menu_item, bom_doc.name)
		entry.get_items()
		for row in entry.items:
			if row.t_warehouse:
				row.t_warehouse = target
			if row.s_warehouse:
				row.s_warehouse = source
			elif row.is_finished_item:
				row.t_warehouse = target
				row.s_warehouse = None
			else:
				row.s_warehouse = source
		entry.insert(ignore_permissions=True)
		entry.submit()
		return entry

	entry = _inv_safe_execute(build, _("ثبت تولید ناموفق بود"))
	frappe.db.commit()
	return {"status": "success", "stock_entry": _inv_stock_entry_payload(entry), "bom": bom_doc.name}


# ---------------------------------------------------------------------------
# Order losses (اوتی‌ها و خسارات)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def save_management_order_loss(payload=None):
	"""Log an out/damage/return-to-stock event tied to an order."""
	_ensure_management_access()
	_inv_ensure_stock_entry_fields()
	payload = _inv_parse_payload(payload)

	loss_kind = (payload.get("loss_kind") or "").strip()
	if loss_kind not in ORDER_LOSS_KINDS:
		frappe.throw(_("نوع نامعتبر است. گزینه‌ها: {0}").format("، ".join(ORDER_LOSS_KINDS)))

	item_code = _inv_clean_item_code(payload.get("item_code"))
	if not item_code or not frappe.db.exists("Item", item_code):
		frappe.throw(_("کالا/محصول نامعتبر است."))
	qty = flt(payload.get("qty"))
	if qty <= 0:
		frappe.throw(_("مقدار باید بزرگ‌تر از صفر باشد."))

	doc = frappe.new_doc(ORDER_LOSS_DOCTYPE)
	doc.loss_kind = loss_kind
	doc.source_type = (payload.get("source_type") or "دستی").strip()
	doc.source_reference = (payload.get("source_reference") or "").strip()
	doc.item_code = item_code
	doc.item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
	doc.qty = qty
	doc.uom = (payload.get("uom") or "").strip() or (frappe.db.get_value("Item", item_code, "stock_uom") or "")
	doc.entry_date = payload.get("entry_date") or today()
	doc.reason = (payload.get("reason") or "").strip()
	doc.note = (payload.get("note") or "").strip()

	rate = flt(payload.get("rate")) or _inv_purchase_rate(item_code)
	doc.amount = flt(payload.get("amount")) or flt(qty * rate)

	warehouse = (payload.get("warehouse") or "").strip()
	stock_entry_name = ""
	if loss_kind == "خسارت":
		warehouse = _inv_resolve_warehouse(warehouse)
		if warehouse:
			entry = _inv_safe_execute(
				lambda: _inv_build_stock_entry(
					entry_type="Material Issue",
					kind_label=STOCK_MOVEMENT_KINDS["damage"],
					lines=[{"item_code": item_code, "qty": qty, "uom": doc.uom}],
					source_warehouse=warehouse,
					note=_("خسارت: {0} ({1})").format(doc.reason or "-", doc.source_reference or "دستی"),
				),
				_("ثبت خروج خسارت از انبار ناموفق بود"),
			)
			stock_entry_name = entry.name
	elif loss_kind == "مرجوعی به انبار":
		warehouse = _inv_resolve_warehouse(warehouse)
		if warehouse:
			entry = _inv_safe_execute(
				lambda: _inv_build_stock_entry(
					entry_type="Material Receipt",
					kind_label=STOCK_MOVEMENT_KINDS["return_to_stock"],
					lines=[{"item_code": item_code, "qty": qty, "uom": doc.uom, "rate": rate}],
					target_warehouse=warehouse,
					note=_("مرجوعی به انبار: {0} ({1})").format(doc.reason or "-", doc.source_reference or "دستی"),
				),
				_("ثبت مرجوعی به انبار ناموفق بود"),
			)
			stock_entry_name = entry.name

	if warehouse and _inv_warehouse_exists(warehouse):
		doc.warehouse = warehouse
	if stock_entry_name:
		doc.stock_entry = stock_entry_name
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "name": doc.name, "stock_entry": stock_entry_name}


@frappe.whitelist()
def list_management_order_losses(date_from="", date_to="", loss_kind="", limit=100, offset=0):  # noqa: A002
	_ensure_management_access()
	filters = {}
	if loss_kind and loss_kind in ORDER_LOSS_KINDS:
		filters["loss_kind"] = loss_kind
	if date_from or date_to:
		date_filter = ["between", [getdate(date_from) if date_from else "2000-01-01", getdate(date_to) if date_to else today()]]
		filters["entry_date"] = date_filter
	rows = frappe.get_all(
		ORDER_LOSS_DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"loss_kind",
			"source_type",
			"source_reference",
			"item_code",
			"item_name",
			"qty",
			"uom",
			"warehouse",
			"reason",
			"amount",
			"stock_entry",
			"entry_date",
		],
		order_by="creation desc",
		limit_start=cint(offset) or 0,
		limit_page_length=min(max(cint(limit) or 100, 1), 500),
	)
	return {
		"losses": [
			{
				**row,
				"entry_date": str(row.get("entry_date") or ""),
				"qty": flt(row.get("qty")),
				"amount": flt(row.get("amount")),
			}
			for row in rows
		],
		"count": len(rows),
	}


@frappe.whitelist()
def get_management_waste_loss_report(date_from="", date_to="", warehouse=""):
	"""Waste/damage valuation + order-loss summary for a period."""
	_ensure_management_access()
	date_to = getdate(date_to) if date_to else today()
	date_from = getdate(date_from) if date_from else add_days(date_to, -29)

	kind_sql = ""
	params = {"df": date_from, "dt": date_to}
	warehouse_cond = ""
	if warehouse and _inv_warehouse_exists(warehouse):
		warehouse_cond = " AND sle.warehouse = %(warehouse)s"
		params["warehouse"] = warehouse
	if _has_column("Stock Entry", "restaurant_movement_kind"):
		kind_sql = "se.restaurant_movement_kind"
	else:
		kind_sql = "''"

	rows = frappe.db.sql(
		"""
		SELECT {kind_sql} AS kind, sle.item_code, i.item_name,
			   SUM(ABS(sle.actual_qty)) AS qty, SUM(ABS(sle.stock_value_difference)) AS value,
			   COUNT(DISTINCT sle.voucher_no) AS vouchers
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		LEFT JOIN `tabItem` i ON i.name = sle.item_code
		WHERE sle.voucher_type='Stock Entry' AND sle.is_cancelled=0
		  AND sle.posting_date BETWEEN %(df)s AND %(dt)s
		  {warehouse_cond}
		  AND {kind_sql} IN (%(w)s, %(d)s, %(r)s)
		GROUP BY kind, sle.item_code, i.item_name
		ORDER BY value DESC
		""".format(
			kind_sql=kind_sql,
			warehouse_cond=warehouse_cond,
		),
		{**params, "w": STOCK_MOVEMENT_KINDS["waste"], "d": STOCK_MOVEMENT_KINDS["damage"], "r": STOCK_MOVEMENT_KINDS["return_to_stock"]},
		as_dict=True,
	)

	loss_rows = frappe.get_all(
		ORDER_LOSS_DOCTYPE,
		filters={"entry_date": ["between", [date_from, date_to]]},
		fields=["loss_kind", "COUNT(*) AS count", "SUM(amount) AS amount"],
		group_by="loss_kind",
	)

	out_rows = [
		{
			"kind": row.get("kind") or "",
			"item_code": row.get("item_code") or "",
			"item_name": row.get("item_name") or row.get("item_code") or "",
			"qty": flt(row.get("qty"), 3),
			"value": flt(row.get("value")),
			"vouchers": cint(row.get("vouchers")),
		}
		for row in rows
	]
	return {
		"date_from": str(date_from),
		"date_to": str(date_to),
		"by_item": out_rows,
		"totals": {
			"waste_value": flt(sum(row["value"] for row in out_rows if row["kind"] == STOCK_MOVEMENT_KINDS["waste"])),
			"damage_value": flt(sum(row["value"] for row in out_rows if row["kind"] == STOCK_MOVEMENT_KINDS["damage"])),
			"return_value": flt(sum(row["value"] for row in out_rows if row["kind"] == STOCK_MOVEMENT_KINDS["return_to_stock"])),
			"movement_count": sum(row["vouchers"] for row in out_rows),
		},
		"order_losses": [
			{"loss_kind": row.get("loss_kind") or "", "count": cint(row.get("count")), "amount": flt(row.get("amount"))}
			for row in loss_rows
		],
	}


# ---------------------------------------------------------------------------
# Physical stock count & reconciliation
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_reconciliation_context(warehouse="", search=""):
	"""System quantities for a warehouse to seed a physical count worksheet."""
	_ensure_management_access()
	warehouse = _inv_resolve_warehouse(warehouse)
	if not warehouse:
		frappe.throw(_("انبار برای انبارگردانی انتخاب نشده است."))

	company = frappe.db.get_value("Warehouse", warehouse, "company") or _inv_default_company()
	company_defaults = {}
	if company and frappe.db.exists("Company", company):
		company_doc = frappe.get_cached_doc("Company", company)
		company_defaults = {
			"company": company,
			"expense_account": company_doc.get("stock_adjustment_account") or "",
			"cost_center": company_doc.get("cost_center") or "",
		}

	params = {"warehouse": warehouse}
	search_cond = ""
	search = (search or "").strip()
	if search:
		search_cond = " AND (i.name LIKE %(needle)s OR i.item_name LIKE %(needle)s)"
		params["needle"] = f"%{search}%"

	rows = frappe.db.sql(
		"""
		SELECT b.item_code, i.item_name, i.stock_uom, b.actual_qty, b.valuation_rate
		FROM `tabBin` b
		INNER JOIN `tabItem` i ON i.name = b.item_code
		WHERE b.warehouse = %(warehouse)s AND b.actual_qty != 0 {search_cond}
		ORDER BY i.item_name
		LIMIT 500
		""".format(
			search_cond=search_cond
		),
		params,
		as_dict=True,
	)

	return {
		"warehouse": warehouse,
		"company": company_defaults,
		"config_ready": bool(company_defaults.get("expense_account") and company_defaults.get("cost_center")),
		"items": [
			{
				"item_code": row.get("item_code"),
				"item_name": row.get("item_name") or row.get("item_code"),
				"stock_uom": row.get("stock_uom") or "",
				"system_qty": flt(row.get("actual_qty")),
				"valuation_rate": flt(row.get("valuation_rate")),
			}
			for row in rows
		],
	}


@frappe.whitelist()
def submit_management_stock_reconciliation(payload=None):
	"""Submit a Stock Reconciliation and return counted-vs-system differences."""
	_ensure_management_access()
	payload = _inv_parse_payload(payload)
	warehouse = _inv_resolve_warehouse(payload.get("warehouse"))
	if not warehouse:
		frappe.throw(_("انبار برای انبارگردانی انتخاب نشده است."))

	lines = []
	for row in _inv_normalize_list(payload.get("items")):
		item_code = _inv_clean_item_code(row.get("item_code"))
		if item_code and frappe.db.exists("Item", item_code):
			lines.append({"item_code": item_code, "qty": flt(row.get("qty")), "rate": flt(row.get("valuation_rate"))})
	if not lines:
		frappe.throw(_("هیچ قلم شمارش‌شده‌ای ارسال نشده است."))

	company = frappe.db.get_value("Warehouse", warehouse, "company") or _inv_default_company()
	company_doc = frappe.get_cached_doc("Company", company) if company else None
	expense_account = company_doc.get("stock_adjustment_account") if company_doc else ""
	cost_center = company_doc.get("cost_center") if company_doc else ""
	if not expense_account or not cost_center:
		frappe.throw(
			_("حساب تعدیل موجودی یا مرکز هزینه در شرکت «{0}» تنظیم نشده است.").format(company or "-")
			+ " "
			+ _("لطفاً در ERPNext → Company مقادیر Stock Adjustment Account و Cost Center را تکمیل کنید.")
	)

	prev_stock = _inv_stock_map(item_codes=[row["item_code"] for row in lines], warehouse=warehouse)

	def build():
		doc = frappe.new_doc("Stock Reconciliation")
		doc.purpose = "Stock Reconciliation"
		doc.company = company
		doc.posting_date = payload.get("posting_date") or today()
		doc.posting_time = now_datetime().strftime("%H:%M:%S")
		doc.expense_account = expense_account
		doc.cost_center = cost_center
		for line in lines:
			row = doc.append("items", {})
			row.item_code = line["item_code"]
			row.warehouse = warehouse
			row.qty = line["qty"]
			if line["rate"]:
				row.valuation_rate = line["rate"]
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc

	doc = _inv_safe_execute(build, _("ثبت انبارگردانی ناموفق بود"))

	diff_rows = []
	for line in lines:
		prev = flt((prev_stock.get(line["item_code"]) or {}).get("qty"))
		rate = line["rate"] or flt((prev_stock.get(line["item_code"]) or {}).get("rate"))
		diff_qty = flt(line["qty"] - prev, 4)
		diff_rows.append(
			{
				"item_code": line["item_code"],
				"prev_qty": prev,
				"new_qty": flt(line["qty"], 4),
				"diff_qty": diff_qty,
				"rate": flt(rate, 6),
				"diff_value": flt(diff_qty * rate),
			}
		)
	frappe.db.commit()
	return {
		"status": "success",
		"name": doc.name,
		"warehouse": warehouse,
		"difference_amount": flt(doc.get("difference_amount")),
		"rows": diff_rows,
	}


@frappe.whitelist()
def list_management_stock_reconciliations(limit=30):
	_ensure_management_access()
	rows = frappe.get_all(
		"Stock Reconciliation",
		filters={"docstatus": 1},
		fields=["name", "posting_date", "posting_time", "company", "difference_amount"],
		order_by="posting_date desc, posting_time desc",
		limit_page_length=min(max(cint(limit) or 30, 1), 200),
	)
	return {
		"reconciliations": [
			{
				"name": row["name"],
				"posting_date": str(row.get("posting_date") or ""),
				"posting_time": str(row.get("posting_time") or ""),
				"company": row.get("company") or "",
				"difference_amount": flt(row.get("difference_amount")),
			}
			for row in rows
		],
		"count": len(rows),
	}


@frappe.whitelist()
def get_management_stock_reconciliation(name=""):
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists("Stock Reconciliation", name):
		frappe.throw(_("سند انبارگردانی یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc("Stock Reconciliation", name)
	rows = frappe.db.sql(
		"""
		SELECT item_code, warehouse, actual_qty, stock_value_difference
		FROM `tabStock Ledger Entry`
		WHERE voucher_type='Stock Reconciliation' AND voucher_no=%s AND is_cancelled=0
		""",
		(name,),
		as_dict=True,
	)
	return {
		"name": doc.name,
		"posting_date": str(doc.get("posting_date") or ""),
		"company": doc.get("company") or "",
		"difference_amount": flt(doc.get("difference_amount")),
		"docstatus": cint(doc.docstatus),
		"rows": [
			{
				"item_code": row.get("item_code"),
				"warehouse": row.get("warehouse") or "",
				"diff_qty": flt(row.get("actual_qty"), 4),
				"diff_value": flt(row.get("stock_value_difference")),
			}
			for row in rows
		],
	}


# ---------------------------------------------------------------------------
# Product costing (بهای تمام‌شده)
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_product_cost_report(search="", limit=200):
	"""Live unit cost for products with an active recipe (BOM)."""
	_ensure_management_access()
	limit = min(max(cint(limit) or 200, 1), 500)
	search = (search or "").strip()

	conditions = ["b.docstatus = 1", "b.is_active = 1", "b.is_default = 1"]
	params = {"limit": limit}
	if search:
		conditions.append("(b.item LIKE %(needle)s OR i.item_name LIKE %(needle)s)")
		params["needle"] = f"%{search}%"

	boms = frappe.db.sql(
		"""
		SELECT b.name, b.item, b.quantity, i.item_name
		FROM `tabBOM` b
		LEFT JOIN `tabItem` i ON i.name = b.item
		WHERE {conditions}
		ORDER BY i.item_name
		LIMIT %(limit)s
		""".format(
			conditions=" AND ".join(conditions)
		),
		params,
		as_dict=True,
	)
	if not boms:
		return {"products": [], "count": 0}

	component_rows = frappe.get_all(
		"BOM Item",
		filters={"parent": ["in", [row["name"] for row in boms]], "parenttype": "BOM"},
		fields=["parent", "item_code", "item_name", "qty", "uom", "stock_uom"],
	)
	components_by_bom = {}
	all_codes = set()
	for row in component_rows:
		components_by_bom.setdefault(row["parent"], []).append(row)
		if row.get("item_code"):
			all_codes.add(row["item_code"])
	all_codes.update(row["item"] for row in boms)

	meta = _inv_item_meta(list(all_codes))
	rate_cache = {}

	def component_rate(code):
		if code not in rate_cache:
			rate_cache[code] = _inv_purchase_rate(code)
		return rate_cache[code]

	sale_prices = {}
	try:
		price_rows = frappe.db.sql(
			"""
			SELECT item_code, MIN(price_list_rate) AS rate
			FROM `tabItem Price`
			WHERE item_code IN %(codes)s AND selling = 1
			GROUP BY item_code
			""",
			{"codes": tuple(row["item"] for row in boms)},
			as_dict=True,
		)
		sale_prices = {row["item_code"]: flt(row.get("rate")) for row in price_rows}
	except Exception:
		sale_prices = {}

	products = []
	for bom in boms:
		output_qty = flt(bom.get("quantity")) or 1.0
		components = components_by_bom.get(bom["name"]) or []
		total_cost = 0.0
		missing_prices = 0
		component_payload = []
		for row in components:
			code = row.get("item_code")
			if not code:
				continue
			qty = flt(row.get("qty"))
			uom = (row.get("uom") or "").strip()
			stock_uom = (row.get("stock_uom") or (meta.get(code) or {}).get("stock_uom") or "").strip()
			if uom and stock_uom and uom != stock_uom:
				qty = qty * _item_uom_conversion_to_stock(code, uom)
			rate = component_rate(code)
			if rate <= 0:
				missing_prices += 1
			amount = qty * rate
			total_cost += amount
			component_payload.append(
				{
					"item_code": code,
					"item_name": row.get("item_name") or code,
					"qty": flt(qty, 4),
					"uom": stock_uom or uom,
					"rate": flt(rate, 6),
					"amount": flt(amount),
				}
			)
		unit_cost = total_cost / output_qty if output_qty else 0.0
		sale_price = sale_prices.get(bom["item"], 0.0)
		margin_amount = sale_price - unit_cost
		margin_pct = (margin_amount / sale_price * 100) if sale_price else 0.0
		products.append(
			{
				"item_code": bom["item"],
				"item_name": bom.get("item_name") or bom["item"],
				"bom": bom["name"],
				"output_qty": flt(output_qty, 3),
				"unit_cost": flt(unit_cost),
				"sale_price": flt(sale_price),
				"margin_amount": flt(margin_amount),
				"margin_pct": flt(margin_pct, 1),
				"missing_prices": missing_prices,
				"components": component_payload,
			}
		)

	return {"products": products, "count": len(products)}


# ---------------------------------------------------------------------------
# BI reports: inventory valuation / movements / waste & losses
# ---------------------------------------------------------------------------

MANAGEMENT_INVENTORY_REPORTS = {"inventory-valuation", "stock-movements", "inventory-waste"}


def _inv_valuation_rows():
	stock = _inv_stock_map()
	if not stock:
		return []
	meta = _inv_item_meta(list(stock.keys()))
	total_value = sum(flt(bucket["value"]) for bucket in stock.values())
	rows = []
	for code, bucket in stock.items():
		info = meta.get(code) or {}
		value = flt(bucket["value"])
		rows.append(
			{
				"item": code,
				"item_name": info.get("item_name") or code,
				"uom": info.get("stock_uom") or "",
				"qty": flt(bucket["qty"], 3),
				"rate": flt(bucket["rate"]),
				"value": value,
				"warehouses": len(bucket.get("warehouses") or {}),
				"share_percent": flt((value / total_value) * 100, 1) if total_value else 0.0,
			}
		)
	rows.sort(key=lambda row: -row["value"])
	return rows


@frappe.whitelist()
def get_management_report_inventory_valuation(date_from=None, date_to=None):
	_ensure_management_access()
	rows = _inv_valuation_rows()
	summary = {
		"items": len(rows),
		"total_qty": round(sum(flt(row["qty"]) for row in rows), 2),
		"total_value": flt(sum(flt(row["value"]) for row in rows)),
	}
	return _compose_management_report(
		"inventory-valuation",
		"Inventory Valuation",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


def _inv_movement_kind_select():
	if _has_column("Stock Entry", "restaurant_movement_kind"):
		return "COALESCE(NULLIF(se.restaurant_movement_kind,''), se.stock_entry_type)"
	return "se.stock_entry_type"


def _inv_movement_rows(date_from, date_to):
	date_to = getdate(date_to) if date_to else today()
	date_from = getdate(date_from) if date_from else add_days(date_to, -29)
	rows = frappe.db.sql(
		"""
		SELECT {kind_sql} AS kind, sle.item_code, i.item_name,
			   SUM(CASE WHEN sle.actual_qty > 0 THEN sle.actual_qty ELSE 0 END) AS in_qty,
			   SUM(CASE WHEN sle.actual_qty < 0 THEN -sle.actual_qty ELSE 0 END) AS out_qty,
			   SUM(ABS(sle.stock_value_difference)) AS value,
			   COUNT(DISTINCT sle.voucher_no) AS vouchers
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		LEFT JOIN `tabItem` i ON i.name = sle.item_code
		WHERE sle.voucher_type='Stock Entry' AND sle.is_cancelled=0
		  AND sle.posting_date BETWEEN %(df)s AND %(dt)s
		GROUP BY kind, sle.item_code, i.item_name
		ORDER BY value DESC
		LIMIT 500
		""".format(
			kind_sql=_inv_movement_kind_select()
		),
		{"df": date_from, "dt": date_to},
		as_dict=True,
	)
	return [
		{
			"kind": row.get("kind") or "",
			"item": row.get("item_code") or "",
			"item_name": row.get("item_name") or row.get("item_code") or "",
			"qty_in": flt(row.get("in_qty"), 3),
			"qty_out": flt(row.get("out_qty"), 3),
			"value": flt(row.get("value")),
			"vouchers": cint(row.get("vouchers")),
		}
		for row in rows
	]


@frappe.whitelist()
def get_management_report_stock_movements(date_from=None, date_to=None):
	_ensure_management_access()
	rows = _inv_movement_rows(date_from, date_to)
	summary = {
		"rows": len(rows),
		"total_vouchers": sum(cint(row["vouchers"]) for row in rows),
		"total_value": flt(sum(flt(row["value"]) for row in rows)),
	}
	return _compose_management_report(
		"stock-movements",
		"Stock Movements",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


def _inv_waste_report_rows(date_from, date_to):
	date_to = getdate(date_to) if date_to else today()
	date_from = getdate(date_from) if date_from else add_days(date_to, -29)
	label_map = {
		STOCK_MOVEMENT_KINDS["waste"],
		STOCK_MOVEMENT_KINDS["damage"],
		STOCK_MOVEMENT_KINDS["return_to_stock"],
	}
	rows = []
	for row in _inv_movement_rows(date_from, date_to):
		if row["kind"] not in label_map:
			continue
		rows.append(
			{
				"kind": row["kind"],
				"item": row["item"],
				"item_name": row["item_name"],
				"qty": flt(row["qty_in"] + row["qty_out"], 3),
				"value": row["value"],
				"events": cint(row["vouchers"]),
			}
		)
	loss_rows = frappe.get_all(
		ORDER_LOSS_DOCTYPE,
		filters={"entry_date": ["between", [date_from, date_to]]},
		fields=["loss_kind", "item_code", "item_name", "SUM(qty) AS qty", "SUM(amount) AS amount", "COUNT(*) AS events"],
		group_by="loss_kind, item_code, item_name",
	)
	for row in loss_rows:
		rows.append(
			{
				"kind": row.get("loss_kind") or "",
				"item": row.get("item_code") or "",
				"item_name": row.get("item_name") or row.get("item_code") or "",
				"qty": flt(row.get("qty"), 3),
				"value": flt(row.get("amount")),
				"events": cint(row.get("events")),
			}
		)
	rows.sort(key=lambda row: -row["value"])
	return rows


@frappe.whitelist()
def get_management_report_inventory_waste(date_from=None, date_to=None):
	_ensure_management_access()
	rows = _inv_waste_report_rows(date_from, date_to)
	summary = {
		"rows": len(rows),
		"total_value": flt(sum(flt(row["value"]) for row in rows)),
		"events": sum(cint(row["events"]) for row in rows),
	}
	return _compose_management_report(
		"inventory-waste",
		"Inventory Waste & Losses",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=[],
	)


def inv_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	"""BI payload (KPIs, charts, tables, insights) for inventory reports."""
	kpis, charts, insights = [], [], []
	tables = [{"key": "report-table", "title": title, "columns": _table_columns_from_rows(rows), "rows": rows}]

	if report_key == "inventory-valuation":
		top = rows[0] if rows else {}
		kpis = [
			_bi_kpi("items", _("اقلام دارای موجودی"), len(rows), "count", 0),
			_bi_kpi("total_value", _("ارزش کل موجودی"), flt(summary.get("total_value")), "money", 0),
			_bi_kpi(
				"top_item_value",
				_("بیشترین ارزش یک قلم"),
				flt(top.get("value")) if top else 0,
				"money",
				0,
			),
		]
		labels = [row.get("item_name") for row in rows[:10]]
		charts = [
			{
				"key": "valuation-top",
				"title": _("۱۰ قلم پرارزش انبار"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "value",
						"label": _("ارزش"),
						"color": "#2f6f5c",
						"values": [flt(row.get("value")) for row in rows[:10]],
					}
				],
			}
		]
		if top:
			insights.append(
				{
					"key": "top-value-item",
					"severity": "info",
					"text": _("بیشترین ارزش انبار مربوط به «{0}» است ({1}٪ از کل).").format(
						top.get("item_name"), top.get("share_percent")
					),
				}
			)

	elif report_key == "stock-movements":
		by_kind = {}
		for row in rows:
			bucket = by_kind.setdefault(row["kind"], {"value": 0.0, "vouchers": 0})
			bucket["value"] += flt(row["value"])
			bucket["vouchers"] += cint(row["vouchers"])
		kpis = [
			_bi_kpi("vouchers", _("اسناد گردش"), cint(summary.get("total_vouchers")), "count", 0),
			_bi_kpi("items", _("اقلام گردش‌یافته"), len({row["item"] for row in rows}), "count", 0),
			_bi_kpi("value", _("مجموع ارزش گردش"), flt(summary.get("total_value")), "money", 0),
		]
		charts = [
			{
				"key": "movement-kinds",
				"title": _("گردش بر اساس نوع"),
				"type": "bar",
				"unit": "money",
				"labels": list(by_kind.keys()),
				"series": [
					{
						"key": "value",
						"label": _("ارزش گردش"),
						"color": "#3e8ed0",
						"values": [flt(bucket["value"]) for bucket in by_kind.values()],
					}
				],
			}
		]
		if rows:
			insights.append(
				{
					"key": "busiest-item",
					"severity": "info",
					"text": _("بیشترین گردش مربوط به «{0}» است.").format(rows[0].get("item_name")),
				}
			)

	elif report_key == "inventory-waste":
		waste_value = sum(flt(row["value"]) for row in rows if row["kind"] == STOCK_MOVEMENT_KINDS["waste"])
		damage_value = sum(flt(row["value"]) for row in rows if row["kind"] == STOCK_MOVEMENT_KINDS["damage"])
		out_amount = sum(flt(row["value"]) for row in rows if row["kind"] == ORDER_LOSS_KINDS[0])
		kpis = [
			_bi_kpi("waste_value", _("ارزش ضایعات"), waste_value, "money", 0),
			_bi_kpi("damage_value", _("ارزش خسارات"), damage_value, "money", 0),
			_bi_kpi("out_amount", _("مبلغ اوتی‌ها"), out_amount, "money", 0),
			_bi_kpi("events", _("رویدادها"), cint(summary.get("events")), "count", 0),
		]
		by_kind = {}
		for row in rows:
			by_kind[row["kind"]] = by_kind.get(row["kind"], 0.0) + flt(row["value"])
		charts = [
			{
				"key": "waste-kinds",
				"title": _("سوخت بر اساس نوع"),
				"type": "bar",
				"unit": "money",
				"labels": list(by_kind.keys()),
				"series": [
					{
						"key": "value",
						"label": _("ارزش"),
						"color": "#b84f4f",
						"values": [flt(value) for value in by_kind.values()],
					}
				],
			}
		]
		top = rows[0] if rows else None
		if top:
			insights.append(
				{
					"key": "top-waste",
					"severity": "warn",
					"text": _("پرسوخت‌ترین قلم: «{0}» ({1}).").format(
						top.get("item_name"),
						top.get("kind"),
					),
				}
			)

	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Excel export / import for raw materials
# ---------------------------------------------------------------------------

MATERIAL_EXPORT_COLUMNS = [
	"item_code",
	"item_name",
	"item_group",
	"stock_uom",
	"purchase_rate",
	"default_supplier",
	"reorder_levels",
	"disabled",
	"current_qty",
	"stock_value",
]
MATERIAL_IMPORT_HEADER_ALIASES = {
	"item_code": ["item_code", "code", "کد کالا", "کد"],
	"item_name": ["item_name", "name", "نام کالا", "نام"],
	"item_group": ["item_group", "group", "گروه کالا", "گروه"],
	"stock_uom": ["stock_uom", "uom", "واحد", "واحد اندازه‌گیری"],
	"purchase_rate": ["purchase_rate", "rate", "نرخ خرید", "آخرین نرخ خرید"],
	"default_supplier": ["default_supplier", "supplier", "تأمین‌کننده", "تامین‌کننده", "تأمین‌کننده پیش‌فرض"],
	"opening_qty": ["opening_qty", "opening", "opening_stock", "موجودی اولیه", "موجودی اول دوره"],
	"opening_warehouse": ["opening_warehouse", "warehouse", "انبار", "انبار موجودی اولیه"],
	"reorder_levels": ["reorder_levels", "reorder", "نقطه سفارش"],
	"disabled": ["disabled", "غیرفعال"],
}


def _inv_serialize_reorder_levels(rows):
	parts = []
	for row in rows or []:
		if row.get("warehouse"):
			parts.append(
				"{}:{}:{}".format(row["warehouse"], flt(row.get("level")), flt(row.get("request_qty")))
			)
	return "; ".join(parts)


def _inv_parse_reorder_levels(text):
	entries = []
	for part in str(text or "").replace("،", ";").split(";"):
		part = part.strip()
		if not part:
			continue
		pieces = part.split(":")
		warehouse = pieces[0].strip()
		if not _inv_warehouse_exists(warehouse):
			continue
		entries.append(
			{
				"warehouse": warehouse,
				"level": flt(pieces[1]) if len(pieces) > 1 else 0,
				"request_qty": flt(pieces[2]) if len(pieces) > 2 else 0,
			}
		)
	return entries


def _inv_parse_disabled_flag(value):
	text = str(value or "").strip().lower()
	if not text:
		return 0
	if text in {"1", "true", "yes", "y", "غیرفعال", "بله", "✓", "✔"}:
		return 1
	return 0


def _inv_normalize_import_headers(header_row):
	mapping = {}
	for key, aliases in MATERIAL_IMPORT_HEADER_ALIASES.items():
		normalized = {alias.strip().lower() for alias in aliases}
		for idx, cell in enumerate(header_row or []):
			if str(cell or "").strip().lower() in normalized:
				mapping[idx] = key
	return mapping


@frappe.whitelist()
def export_management_materials_excel(search=""):
	"""Export raw materials (with stock + reorder info) as an .xlsx file."""
	_ensure_management_access()
	_inv_ensure_item_fields()

	payload = list_management_raw_materials(search=search, include_inactive=1, limit=1000)
	data = [list(MATERIAL_EXPORT_COLUMNS)]
	for row in payload["items"]:
		data.append(
			[
				row["name"],
				row["item_name"],
				row["item_group"],
				row["stock_uom"],
				flt(row["purchase_rate"]),
				row["default_supplier"] or "",
				_inv_serialize_reorder_levels(row["reorder_levels"]),
				cint(row["disabled"]),
				flt(row["qty"]),
				flt(row["value"]),
			]
		)

	try:
		from frappe.utils.xlsxutils import make_xlsx
	except Exception:
		frappe.throw(_("خروجی اکسل روی این سرور در دسترس نیست (xlsxutils)."))

	xlsx_file = make_xlsx(data, "Raw Materials")
	file_name = "restaurant-materials-{}.xlsx".format(now_datetime().strftime("%Y%m%d-%H%M%S"))
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": xlsx_file.getvalue(),
			"is_private": 1,
			"folder": "Home",
		}
	).insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": "success",
		"file_url": file_doc.file_url,
		"file_name": file_doc.file_name,
		"rows": max(len(data) - 1, 0),
		"columns": list(MATERIAL_EXPORT_COLUMNS),
	}


def _inv_import_material_record(record, update_existing=1, dry_run=0):
	record = record or {}
	item_code = _inv_clean_item_code(record.get("item_code"))
	item_name = (record.get("item_name") or "").strip()
	if not item_code and not item_name:
		frappe.throw(_("کد یا نام کالا الزامی است."))
	item_code = item_code or item_name

	exists = frappe.db.exists("Item", item_code)
	if exists and not cint(update_existing):
		return {"status": "skipped", "mode": "update"}
	if cint(dry_run):
		return {"status": "success", "mode": "update" if exists else "create"}

	payload = {
		"name": item_code if exists else "",
		"item_code": item_code,
		"item_name": item_name or item_code,
		"item_group": (record.get("item_group") or "").strip() or None,
		"stock_uom": (record.get("stock_uom") or "").strip() or None,
		"purchase_rate": flt(record.get("purchase_rate")),
		"disabled": _inv_parse_disabled_flag(record.get("disabled")),
	}
	supplier = (record.get("default_supplier") or "").strip()
	if supplier and frappe.db.exists("Supplier", supplier):
		payload["default_supplier"] = supplier
	reorder_entries = _inv_parse_reorder_levels(record.get("reorder_levels"))
	if record.get("reorder_levels") is not None:
		payload["reorder_levels"] = reorder_entries
	# Opening stock support: create/update → Material Receipt in the chosen warehouse
	opening_qty = flt(record.get("opening_qty"))
	opening_warehouse = _inv_resolve_warehouse(record.get("opening_warehouse"))
	if opening_qty > 0 and opening_warehouse:
		payload["opening"] = {"qty": opening_qty, "warehouse": opening_warehouse}
	result = _inv_upsert_raw_material(payload)
	opening_note = ""
	if payload.get("opening") and result.get("opening_entry"):
		opening_note = result.get("opening_entry")
	elif opening_qty > 0 and exists:
		# Manual receipt for existing items too (opening applies on update as a stock-in)
		warehouse = opening_warehouse
		if warehouse and _inv_warehouse_exists(warehouse):
			entry = _inv_build_stock_entry(
				entry_type="Material Receipt",
				kind_label=STOCK_MOVEMENT_KINDS["manual_receipt"],
				lines=[{"item_code": item_code, "qty": opening_qty, "rate": flt(payload.get("purchase_rate"))}],
				target_warehouse=warehouse,
				note=_("موجودی اولیه ماده اولیه (ورود اکسل)"),
			)
			opening_note = entry.name
	return {"status": "success", "mode": "update" if exists else "create", "opening_entry": opening_note, **{k: v for k, v in result.items() if k != "opening_entry"}}


@frappe.whitelist()
def import_management_materials_excel(
	file_url=None, file_name=None, update_existing=1, dry_run=0
):
	"""Bulk import raw materials from an uploaded .xlsx/.csv file."""
	_ensure_management_access()
	_inv_ensure_item_fields()

	raw = _inv_fp_call("_fp_load_upload_content", file_url=file_url)
	rows = _inv_fp_call("_fp_parse_tabular_rows", raw, file_name=file_name or (file_url or ""))
	if len(rows) < 2:
		frappe.throw(_("فایل بارگذاری‌شده سطر داده ندارد."))

	header_mapping = _inv_normalize_import_headers(rows[0])
	if not header_mapping:
		frappe.throw(
			_("سرستون‌ها شناسایی نشد. ستون‌های مورد انتظار: {0}").format(
				", ".join(MATERIAL_EXPORT_COLUMNS)
			)
		)

	records = []
	for row in rows[1:]:
		if not any(str(cell or "").strip() for cell in row):
			continue
		record = {}
		for idx, key in header_mapping.items():
			if idx < len(row):
				record[key] = row[idx]
		records.append(record)
	if not records:
		frappe.throw(_("فایل بارگذاری‌شده سطر داده ندارد."))

	summary = {"created": 0, "updated": 0, "skipped": 0, "errors": []}
	for index, record in enumerate(records, start=2):
		try:
			result = _inv_import_material_record(record, update_existing=update_existing, dry_run=dry_run)
			if result.get("status") == "skipped":
				summary["skipped"] += 1
			elif result.get("mode") == "update":
				summary["updated"] += 1
			else:
				summary["created"] += 1
		except Exception as error:
			summary["errors"].append(
				{"row": index, "item_code": record.get("item_code") or "", "message": str(error)[:180]}
			)

	if not cint(dry_run):
		frappe.db.commit()
	return {"status": "success", "dry_run": cint(dry_run), "total_rows": len(records), **summary}


# ---------------------------------------------------------------------------
# Dashboard summary + purchase order print
# ---------------------------------------------------------------------------


def _inv_waste_value_since(days=30):
	if not _has_column("Stock Entry", "restaurant_movement_kind"):
		return 0.0
	row = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(ABS(sle.stock_value_difference)),0) AS amount
		FROM `tabStock Ledger Entry` sle
		INNER JOIN `tabStock Entry` se ON se.name = sle.voucher_no
		WHERE sle.voucher_type='Stock Entry' AND sle.is_cancelled=0
		  AND se.restaurant_movement_kind IN (%(w)s, %(d)s)
		  AND sle.posting_date >= %(df)s
		""",
		{"w": STOCK_MOVEMENT_KINDS["waste"], "d": STOCK_MOVEMENT_KINDS["damage"], "df": add_days(today(), -days)},
		as_dict=True,
	)
	return flt(row[0].get("amount")) if row else 0.0


def _inv_stock_totals():
	leaf = _inv_leaf_warehouses()
	row = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(actual_qty),0) AS qty, COALESCE(SUM(stock_value),0) AS value
		FROM `tabBin`
		WHERE warehouse IN %(warehouses)s
		""",
		{"warehouses": tuple(leaf or ["__none__"])},
		as_dict=True,
	)
	return (flt(row[0].get("qty")), flt(row[0].get("value"))) if row else (0.0, 0.0)


def _inv_alert_summary():
	below = len(get_management_reorder_alerts(limit=500).get("alerts") or [])
	stock_qty, stock_value = _inv_stock_totals()
	return {
		"below_reorder": cint(below),
		"waste_damage_30d_value": _inv_waste_value_since(30),
		"stock_value_total": stock_value,
		"stock_qty_total": stock_qty,
		"warehouses_total": len(_inv_leaf_warehouses()),
		"open_purchase_orders": cint(
			frappe.db.count(
				PURCHASE_ORDER_DOCTYPE,
				{"status": ["in", [PURCHASE_STATUS_DRAFT, PURCHASE_STATUS_SENT, PURCHASE_STATUS_PARTIAL]]},
			)
			or 0
		),
	}


@frappe.whitelist()
def get_management_inventory_alerts_summary():
	"""Lightweight KPIs for the dashboard inventory widget."""
	_ensure_management_access()
	return _inv_alert_summary()


def _inv_purchase_order_print_html(doc):
	"""POS/thermal-width purchase receipt using the dashboard print settings."""
	brand = _management_get_print_brand_settings()
	font_family = html_escape(str(brand.get("print_font_family") or "Peyda"))
	font_size = min(max(cint(brand.get("print_font_size") or 11), 8), 24)
	brand_name = html_escape(str(brand.get("brand_name") or "رستوران"))
	currency = html_escape(_get_currency())

	item_rows = []
	for idx, row in enumerate(doc.get("items") or [], start=1):
		item_name = html_escape(str(row.get("item_name") or row.get("item_code") or ""))
		item_code = html_escape(str(row.get("item_code") or ""))
		uom = html_escape(str(row.get("uom") or ""))
		qty = flt(row.get("qty"))
		rate = flt(row.get("rate"))
		amount = flt(row.get("amount"))
		received = flt(row.get("received_qty"))
		item_rows.append(
			f"""
			<div class="item-row">
				<div class="item-head"><span class="item-index">{idx}</span><strong>{item_name}</strong><b>{qty:,.3f} {uom}</b></div>
				<div class="item-code">{item_code}</div>
				<div class="item-meta"><span>نرخ: {rate:,.0f}</span><span>مبلغ: {amount:,.0f}</span><span>دریافت: {received:,.3f}</span></div>
			</div>
			"""
		)

	return f"""
<style>
@page {{ size: 80mm auto; margin: 3mm; }}
@font-face {{ font-family: Peyda; src: url('/fonts/Pevda-Reqular.ttf') format('truetype'); font-weight: 400; }}
@font-face {{ font-family: Peyda; src: url('/fonts/Peyda-Bold.ttf') format('truetype'); font-weight: 700; }}
@font-face {{ font-family: Peyda; src: url('/fonts/Peyda-ExtraBold.ttf') format('truetype'); font-weight: 800; }}
* {{ box-sizing: border-box; }}
body {{ direction: rtl; margin: 0; font-family: '{font_family}', Peyda, Tahoma, sans-serif; color: #34261F; font-size: {font_size}px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.receipt {{ width: 74mm; margin: 0 auto; line-height: 1.45; }}
.header {{ text-align: center; padding: 4px 0 8px; border-bottom: 1px dashed #D8C8B4; }}
.header h1 {{ margin: 0; font-size: {font_size + 3}px; font-weight: 800; }}
.header p {{ margin: 2px 0 0; color: #6F7B56; font-size: 10px; }}
.meta {{ display: grid; gap: 3px; padding: 8px 0; border-bottom: 1px dashed #D8C8B4; }}
.meta-row {{ display: flex; justify-content: space-between; gap: 6px; font-size: 10px; }}
.meta-row strong {{ font-weight: 700; text-align: left; }}
.items {{ display: grid; gap: 5px; padding: 8px 0; }}
.item-row {{ padding: 4px 0 6px; border-bottom: 1px dotted #E5DCCF; }}
.item-head {{ display: grid; grid-template-columns: 18px minmax(0, 1fr) auto; gap: 4px; align-items: start; }}
.item-index {{ width: 18px; height: 18px; border-radius: 50%; background: #F3E1DA; text-align: center; font-size: 10px; line-height: 18px; }}
.item-head strong {{ min-width: 0; font-size: 10px; }}
.item-head b {{ white-space: nowrap; font-size: 10px; }}
.item-code {{ margin-right: 22px; color: #746454; font-size: 9px; }}
.item-meta {{ display: flex; justify-content: space-between; gap: 5px; margin-right: 22px; color: #6F7B56; font-size: 9px; }}
.totals {{ display: grid; gap: 4px; border-top: 1px dashed #D8C8B4; padding-top: 7px; }}
.total-row {{ display: flex; justify-content: space-between; gap: 6px; font-size: 10px; }}
.total-row strong {{ font-weight: 800; }}
.total-row.final {{ font-size: 12px; font-weight: 800; }}
.note {{ margin-top: 8px; color: #746454; font-size: 9px; white-space: pre-line; }}
.footer {{ margin-top: 8px; padding-top: 6px; border-top: 1px dashed #D8C8B4; text-align: center; color: #6F7B56; font-size: 9px; }}
</style>
<div class="receipt">
  <header class="header"><h1>{brand_name}</h1><p>سفارش خرید مواد اولیه • {html_escape(str(doc.name))}</p></header>
  <div class="meta">
    <div class="meta-row"><span>تأمین‌کننده</span><strong>{html_escape(str(doc.get('supplier_name') or doc.get('supplier') or '—'))}</strong></div>
    <div class="meta-row"><span>وضعیت</span><strong>{html_escape(str(doc.get('status') or ''))}</strong></div>
    <div class="meta-row"><span>تاریخ سفارش</span><strong>{html_escape(str(doc.get('posting_date') or ''))}</strong></div>
    <div class="meta-row"><span>انبار مقصد</span><strong>{html_escape(str(doc.get('target_warehouse') or '—'))}</strong></div>
  </div>
  <div class="items">{''.join(item_rows)}</div>
  <div class="totals">
    <div class="total-row"><span>جمع تعداد</span><strong>{flt(doc.get('total_qty')):,.3f}</strong></div>
    <div class="total-row final"><span>مبلغ کل</span><strong>{flt(doc.get('grand_total')):,.0f} {currency}</strong></div>
  </div>
  {f"<div class='note'>یادداشت: {html_escape(str(doc.get('note') or ''))}</div>" if doc.get('note') else ''}
  <div class="footer">فرم خرید داخلی مجموعه</div>
</div>
"""


@frappe.whitelist()
def get_management_inventory_purchase_print(name=""):
	"""Printable branded HTML for a purchase order."""
	_ensure_management_access()
	name = (name or "").strip()
	if not frappe.db.exists(PURCHASE_ORDER_DOCTYPE, name):
		frappe.throw(_("سفارش خرید یافت نشد: {0}").format(name or "-"))
	doc = frappe.get_doc(PURCHASE_ORDER_DOCTYPE, name)
	return {"status": "success", "name": doc.name, "html": _inv_purchase_order_print_html(doc)}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _inv_register_into_api_module():
	"""Push this module's public API onto ``restaurant.api``.

	Same safeguard as the feature pack: if this module gets imported before
	``api.py`` finishes initializing (e.g. via a migrate patch), api.py's
	``from restaurant.api_inventory import *`` copies nothing and the endpoint
	paths would 404. Setting the attributes here covers both import orders.
	"""
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_inv_register_into_api_module()
