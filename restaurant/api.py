import json
import math
import os
import random
import re
import string
import copy
from base64 import b64decode
from collections import defaultdict
from html import escape as html_escape
from itertools import product
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc
from frappe.twofactor import get_qr_svg_code
from frappe.utils import (
	add_days,
	cint,
	flt,
	get_datetime,
	get_datetime_str,
	get_time,
	getdate,
	now_datetime,
	nowdate,
	today,
)

MAX_PAGE_SIZE = 50
ORDER_STATUSES = ["new", "confirmed", "preparing", "ready", "delivered", "cancelled"]
ORDER_TYPES = {"dine_in", "takeaway", "delivery"}
DELIVERY_MODES = {"pickup", "delivery"}
ORDER_CONTEXT_TYPES = {"dine_in", "pickup", "delivery"}
DINE_IN_STATUS_FLOW = ["new", "confirmed", "preparing", "ready", "served"]
PICKUP_STATUS_FLOW = ["new", "confirmed", "preparing", "ready", "delivered"]
DELIVERY_STATUS_FLOW = ["new", "confirmed", "preparing", "courier_handoff", "on_the_way", "delivered"]
POS_PAYMENT_METHODS = {"cash", "card", "credit"}
POS_PAYMENT_STATUSES = {"pending", "paid", "failed", "cancelled"}
POS_PAYMENT_PROVIDERS = {"manual", "local_node", "webhook"}
POS_PAYMENT_SUCCESS_TOKENS = {"success", "successful", "paid", "approved", "ok", "done"}
POS_PAYMENT_PENDING_TOKENS = {"pending", "processing", "queued", "in_progress", "waiting"}
POS_HARDWARE_EVENT_SEVERITIES = {"info", "warn", "error"}
DEFAULT_SELLING_PRICE_LIST_FIELD = "restaurant_is_default_selling"
RESTAURANT_STATUS_FLOW = ["new", "confirmed", "preparing", "ready", "delivered"]
CORE_ORDER_STATUS_MAP = {
	"draft": "new",
	"to deliver and bill": "confirmed",
	"to bill": "confirmed",
	"to deliver": "preparing",
	"completed": "delivered",
	"cancelled": "cancelled",
}
# Schema helpers are called from every POS write.  Keep their warm-state in
# the worker so normal orders do not repeat Custom Field metadata queries.
_CHECKOUT_SALES_ORDER_FIELDS_READY_SITES = set()
# These markers were historically appended to the customer note field by
# POS state transitions. They are internal audit data, not cashier notes and
# must never be shown on or printed with the customer receipt.
_AUTOMATIC_POS_NOTE_MARKERS = (
    "[ORDER]",
    "[SETTLE]",
    "[PRODUCE]",
    "[DELIVER_ONLY]",
    "[PAYMENT]",
    "[KITCHEN]",
    "[ERROR]",
    "[PRINT_PRODUCTION]",
    "روش پرداخت:",
    "جایگاه:",
    "مهمان:",
    "ادامه فاکتور",
)

DEFAULT_CHECKOUT_MAP_CONFIG = {
	"provider": "neshan",
	"script_url": "https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.js",
	"style_url": "https://static.neshan.org/sdk/leaflet/1.4.0/leaflet.css",
	"default_lat": 35.6997,
	"default_lng": 51.3381,
	"default_zoom": 13,
}
MANAGEMENT_THEME_GLOBAL_DEFAULT_KEY = "restaurant_management_theme_settings_v1"
MANAGEMENT_SITE_LOADER_GLOBAL_DEFAULT_KEY = "restaurant_management_loader_settings_v1"
MANAGEMENT_DISPLAY_VARIANT_KEY = "restaurant_management_display_variant_v1"
MANAGEMENT_SITE_SETTINGS_BLOB_KEY = "restaurant_management_site_settings_v1"
MANAGEMENT_DISPLAY_VARIANT_DEFAULTS = {
	"header_variant": "classic",
	"menu_search_variant": "search-card",
	"hero_section_variant": "off",
	"footer_variant": "full",
	"card_variant": "classic",
	"hero_image_position": "center",
	"category_rail_variant": "pill",
}
MANAGEMENT_KITCHEN_PRINT_MODE_DEFAULT = "parent_with_components"
MANAGEMENT_KITCHEN_PRINT_MODES = (
	"parent_only",
	"parent_with_components",
	"components_grouped_by_step",
)
MANAGEMENT_KITCHEN_PRINT_MODE_ALIASES = {
	"full_selections": MANAGEMENT_KITCHEN_PRINT_MODE_DEFAULT,
	"full detail": MANAGEMENT_KITCHEN_PRINT_MODE_DEFAULT,
	"step only": "components_grouped_by_step",
	"option only": MANAGEMENT_KITCHEN_PRINT_MODE_DEFAULT,
}
MANAGEMENT_STOCK_CONSUMPTION_MODE_DEFAULT = "consume_selected_components"
MANAGEMENT_STOCK_CONSUMPTION_MODES = (
	"no_stock_deduction",
	"consume_selected_components",
	"create_dynamic_bom",
	"use_sales_order_exploded_components",
	"manual_kitchen_consumption",
)
MANAGEMENT_STOCK_CONSUMPTION_MODE_ALIASES = {
	"from_builder": MANAGEMENT_STOCK_CONSUMPTION_MODE_DEFAULT,
	"per option": MANAGEMENT_STOCK_CONSUMPTION_MODE_DEFAULT,
	"per step": "create_dynamic_bom",
	"fixed": "no_stock_deduction",
}
MANAGEMENT_HEADER_VARIANTS = {"classic", "minimal", "hero", "glass"}
MANAGEMENT_MENU_SEARCH_VARIANTS = {"search-card", "off"}
MANAGEMENT_HERO_SECTION_VARIANTS = {"off", "slider", "fullscreen", "banner", "cover", "foodbar"}
MANAGEMENT_FOOTER_VARIANTS = {"off", "full", "minimal"}
MANAGEMENT_THEME_LEGACY_DEFAULTS = {
	"primary": "#2563EB",
	"accent": "#DC2626",
	"success": "#16A34A",
	"danger": "#DC2626",
	"warning": "#D97706",
	"surface": "#FFFFFF",
	"text": "#0F172A",
	"muted": "#64748B",
	"posPrimary": "#015A72",
	"posAccent": "#FF9836",
	"posSuccess": "#0B7D4A",
	"posDanger": "#AB3535",
	"posWarning": "#F59E0B",
}
MANAGEMENT_THEME_DEFAULTS = {
	"primary": "#6F4A31",
	"accent": "#C98D42",
	"success": "#2F8F5B",
	"danger": "#B84F4F",
	"warning": "#C67B2A",
	"surface": "#FBF8F4",
	"surfaceAlt": "#F1E7DB",
	"background": "#F6F1EA",
	"border": "#D5C3AF",
	"text": "#3F2A1D",
	"textSecondary": "#654A38",
	"muted": "#846B58",
	"posPrimary": "#6F4A31",
	"posAccent": "#C98D42",
	"posSuccess": "#0B7D4A",
	"posDanger": "#AB3535",
	"posWarning": "#F59E0B",
}
MANAGEMENT_THEME_HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
MANAGEMENT_SITE_LOADER_PRESETS = {
	"steaming-bowl",
	"noodle-bowl",
	"burger-stack",
	"club-sandwich",
	"coffee-cup",
	"pizza-slice",
	"donut-bite",
}
MANAGEMENT_SITE_LOADER_DEFAULTS = {
	"loader_enabled": 1,
	"loader_mode": "preset",
	"loader_preset": "steaming-bowl",
	"loader_title": "در حال آماده سازی سفارش",
	"loader_subtitle": "آشپزخانه مشغول آماده کردن سفارش شماست...",
	"loader_min_duration_ms": 1400,
	"loader_overlay_color": "#F6F4ED",
	"loader_accent_color": "#6A9A6B",
	"loader_custom_code": "",
}

NUTRITION_KEY_FIELD_MAP = {
	"kcal": "restaurant_nutrition_kcal",
	"protein_g": "restaurant_nutrition_protein_g",
	"carb_g": "restaurant_nutrition_carb_g",
	"sugar_g": "restaurant_nutrition_sugar_g",
	"fat_g": "restaurant_nutrition_fat_g",
}


def _parse_json(value, default):
	if value is None:
		return default
	if isinstance(value, (dict, list)):
		return value
	if isinstance(value, str):
		stripped = value.strip()
		if not stripped:
			return default
		try:
			return json.loads(stripped)
		except Exception:
			return default
	return default


def _stable_json_dumps(value):
	try:
		return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
	except Exception:
		return ""


def _normalize_json_text_field(value, default=None):
	default_value = {} if default is None else default
	if value in (None, ""):
		return "" if default_value in (None, "") else _stable_json_dumps(default_value)
	if isinstance(value, (dict, list)):
		return _stable_json_dumps(value)
	if isinstance(value, str):
		stripped = value.strip()
		if not stripped:
			return "" if default_value in (None, "") else _stable_json_dumps(default_value)
		parsed = _parse_json(stripped, None)
		if parsed is not None:
			return _stable_json_dumps(parsed)
		return stripped
	return _stable_json_dumps(default_value)


def _normalize_theme_hex(color, fallback):
	raw = (color or "").strip()
	if not MANAGEMENT_THEME_HEX_RE.match(raw):
		return fallback
	if len(raw) == 4:
		expanded = "".join(ch * 2 for ch in raw[1:])
		return f"#{expanded}".upper()
	return raw.upper()


def _sanitize_management_theme_settings(payload=None):
	source = payload if isinstance(payload, dict) else {}
	return {
		key: _normalize_theme_hex(source.get(key), default_value)
		for key, default_value in MANAGEMENT_THEME_DEFAULTS.items()
	}


def _is_legacy_default_theme_settings(payload):
	source = payload if isinstance(payload, dict) else {}
	if not source:
		return False
	for key, default_value in MANAGEMENT_THEME_LEGACY_DEFAULTS.items():
		if _normalize_theme_hex(source.get(key), default_value) != default_value:
			return False
	return True


def _load_management_theme_settings():
	try:
		raw = frappe.defaults.get_global_default(MANAGEMENT_THEME_GLOBAL_DEFAULT_KEY)
		parsed = _parse_json(raw, {})
	except Exception:
		parsed = {}
	if _is_legacy_default_theme_settings(parsed):
		return _sanitize_management_theme_settings({})
	return _sanitize_management_theme_settings(parsed)


def _split_tags(raw_value):
	"""Return list of tag titles from either old comma-separated string or new child table"""
	if not raw_value:
		return []
	# If it's already a list (from child table), extract titles
	if isinstance(raw_value, list):
		titles = []
		for item in raw_value:
			if isinstance(item, dict):
				title = item.get("title") or item.get("tag_title") or ""
				if title:
					titles.append(str(title).strip())
			elif isinstance(item, str) and item.strip():
				titles.append(item.strip())
		return titles
	# Old comma-separated string
	parts = []
	for chunk in str(raw_value).replace("\n", ",").split(","):
		tag = (chunk or "").strip()
		if tag:
			parts.append(tag)
	return parts


def _item_tag_tables_ready():
	"""Return True only when the optional restaurant item tag doctypes and tables exist."""
	try:
		if not frappe.db.exists("DocType", "Restaurant Item Tag"):
			return False
		if not frappe.db.exists("DocType", "Restaurant Item Tag Link"):
			return False
		return bool(frappe.db.sql("SHOW TABLES LIKE %s", "tabRestaurant Item Tag Link"))
	except Exception:
		return False


def _get_item_tag_titles(item_name):
	"""Get tag titles for an item from the optional tag child table."""
	if not item_name or not _item_tag_tables_ready():
		return []
	try:
		links = frappe.db.sql(
			"SELECT tag FROM `tabRestaurant Item Tag Link` WHERE parent=%s AND parentfield='restaurant_item_tag_table' ORDER BY idx",
			(item_name,),
			as_dict=True,
		)
	except Exception:
		return []
	titles = []
	for link in links:
		try:
			title = frappe.db.get_value("Restaurant Item Tag", link.tag, "title")
		except Exception:
			title = None
		if title:
			titles.append(str(title))
	return titles


def _read_field(source, fieldname):
	if not source:
		return None
	if isinstance(source, dict):
		return source.get(fieldname)
	if hasattr(source, "get"):
		return source.get(fieldname)
	return getattr(source, fieldname, None)


def _json_safe_datetime(value):
	if value in (None, ""):
		return None
	if isinstance(value, str):
		return value
	try:
		return get_datetime_str(value)
	except Exception:
		return str(value)


def _optional_float(source, fieldname):
	value = _read_field(source, fieldname)
	if value in (None, ""):
		return None
	return flt(value)


def _item_uom_conversion_to_stock(item_code, source_uom):
	details = _item_uom_conversion_details_to_stock(item_code, source_uom)
	return flt(details.get("factor") or 0) or 1.0


def _item_uom_conversion_details_to_stock(item_code, source_uom):
	item_code = (item_code or "").strip()
	source_uom = (source_uom or "").strip()
	stock_uom = (frappe.db.get_value("Item", item_code, "stock_uom") or "").strip() if item_code else ""
	if not item_code:
		return {
			"factor": 1.0,
			"stock_uom": stock_uom,
			"source_uom": source_uom,
			"has_conversion": 0,
			"is_same_uom": 0,
		}

	if not source_uom:
		source_uom = stock_uom

	if not stock_uom or source_uom == stock_uom:
		return {
			"factor": 1.0,
			"stock_uom": stock_uom,
			"source_uom": source_uom,
			"has_conversion": 1 if stock_uom else 0,
			"is_same_uom": 1 if stock_uom and source_uom == stock_uom else 0,
		}

	conversion_factor = frappe.db.get_value(
		"UOM Conversion Detail",
		{"parent": item_code, "uom": source_uom},
		"conversion_factor",
	)
	if conversion_factor not in (None, ""):
		return {
			"factor": max(flt(conversion_factor), 0),
			"stock_uom": stock_uom,
			"source_uom": source_uom,
			"has_conversion": 1,
			"is_same_uom": 0,
		}

	try:
		from erpnext.stock.doctype.item.item import get_uom_conv_factor

		fallback = get_uom_conv_factor(source_uom, stock_uom)
		if fallback not in (None, ""):
			return {
				"factor": max(flt(fallback), 0),
				"stock_uom": stock_uom,
				"source_uom": source_uom,
				"has_conversion": 1,
				"is_same_uom": 0,
			}
	except Exception:
		pass

	return {
		"factor": 0.0,
		"stock_uom": stock_uom,
		"source_uom": source_uom,
		"has_conversion": 0,
		"is_same_uom": 0,
	}


def _normalize_modifier_option_quantity_rules(option_row=None):
	option_row = option_row or {}
	base_qty = flt(option_row.get("option_qty") or 1)
	if base_qty <= 0:
		base_qty = 1

	step_raw = option_row.get("qty_step")
	qty_step = flt(step_raw if step_raw not in (None, "") else base_qty)
	if qty_step <= 0:
		qty_step = base_qty

	min_raw = option_row.get("min_qty")
	min_qty = flt(min_raw if min_raw not in (None, "") else 0)
	if min_qty < 0:
		min_qty = 0

	max_default = max(base_qty, qty_step, base_qty * 4)
	max_raw = option_row.get("max_qty")
	max_qty = flt(max_raw if max_raw not in (None, "") else max_default)
	max_qty = max(max_qty, min_qty, base_qty)

	return {
		"option_qty": base_qty,
		"base_qty": base_qty,
		"min_qty": min_qty,
		"max_qty": max_qty,
		"qty_step": qty_step,
	}


def _nutrition_factor_from_item_qty(item_code, qty, uom=None):
	qty_value = flt(qty or 0)
	if qty_value <= 0:
		return 0.0

	factor_to_stock = _item_uom_conversion_to_stock(item_code, uom)
	return qty_value * factor_to_stock


def _normalize_nutrition_totals(totals):
	payload = {}
	for key in NUTRITION_KEY_FIELD_MAP:
		payload[key] = round(flt((totals or {}).get(key) or 0), 4)
	return payload


def _add_nutrition_to_totals(totals, item_nutrition, factor):
	if not isinstance(totals, dict):
		return
	if factor <= 0:
		return
	for key in NUTRITION_KEY_FIELD_MAP:
		totals[key] = flt(totals.get(key) or 0) + (flt((item_nutrition or {}).get(key) or 0) * factor)


def _nutrition_payload_from_totals(totals):
	normalized = _normalize_nutrition_totals(totals)
	kcal = flt(normalized.get("kcal") or 0)
	protein_g = flt(normalized.get("protein_g") or 0)
	protein_percent = None
	if kcal > 0:
		protein_percent = round(min((protein_g * 4 * 100.0) / kcal, 100.0), 1)

	return {
		"kcal": round(kcal, 1),
		"protein_g": round(protein_g, 1),
		"carb_g": round(flt(normalized.get("carb_g") or 0), 1),
		"sugar_g": round(flt(normalized.get("sugar_g") or 0), 1),
		"fat_g": round(flt(normalized.get("fat_g") or 0), 1),
		"protein_percent": protein_percent,
	}


def _nutrition_per_unit_payload(item_doc):
	nutrition = _nutrition_payload(item_doc or {})
	recipe_yield_qty = flt(_read_field(item_doc, "restaurant_recipe_yield_qty") or 0)
	if recipe_yield_qty > 1e-8:
		divisor = recipe_yield_qty
		for key in ("kcal", "protein_g", "carb_g", "sugar_g", "fat_g"):
			value = nutrition.get(key)
			if value is None:
				continue
			nutrition[key] = round(flt(value) / divisor, 4)
		kcal = flt(nutrition.get("kcal") or 0)
		protein_g = flt(nutrition.get("protein_g") or 0)
		if kcal > 0:
			nutrition["protein_percent"] = round(min((protein_g * 4 * 100.0) / kcal, 100.0), 1)
		else:
			nutrition["protein_percent"] = None
	return nutrition


def _available_item_nutrition_fields():
	fields = []
	for fieldname in NUTRITION_KEY_FIELD_MAP.values():
		if _has_column("Item", fieldname):
			fields.append(fieldname)
	return fields


def _nutrition_payload(source):
	kcal = _optional_float(source, NUTRITION_KEY_FIELD_MAP["kcal"])
	protein_g = _optional_float(source, NUTRITION_KEY_FIELD_MAP["protein_g"])
	carb_g = _optional_float(source, NUTRITION_KEY_FIELD_MAP["carb_g"])
	sugar_g = _optional_float(source, NUTRITION_KEY_FIELD_MAP["sugar_g"])
	fat_g = _optional_float(source, NUTRITION_KEY_FIELD_MAP["fat_g"])

	protein_percent = None
	if kcal and protein_g is not None and kcal > 0:
		protein_percent = round(min((protein_g * 4 * 100.0) / kcal, 100.0), 1)

	return {
		"kcal": round(kcal, 1) if kcal is not None else None,
		"protein_g": round(protein_g, 1) if protein_g is not None else None,
		"carb_g": round(carb_g, 1) if carb_g is not None else None,
		"sugar_g": round(sugar_g, 1) if sugar_g is not None else None,
		"fat_g": round(fat_g, 1) if fat_g is not None else None,
		"protein_percent": protein_percent,
	}


def _normalize_slug(value):
	return (value or "").strip().lower()


def _public_menu_slugify(value):
	normalized = (value or "").strip().lower()
	normalized = re.sub(r"\s+", "-", normalized)
	normalized = re.sub(r"[^\w\u0600-\u06FF-]+", "", normalized)
	normalized = re.sub(r"-+", "-", normalized).strip("-")
	return normalized


def _get_currency(company=None):
	company = (company or "").strip()
	if company and frappe.db.exists("Company", company):
		company_currency = frappe.db.get_value("Company", company, "default_currency")
		if company_currency:
			return company_currency

	settings_currency = frappe.db.get_single_value("Restaurant Web Settings", "default_currency")
	if settings_currency:
		return settings_currency

	currency = frappe.db.get_single_value("Global Defaults", "default_currency")
	if currency:
		return currency

	company_currency = frappe.db.get_value("Company", {}, "default_currency")
	return company_currency or "IRR"


def _get_single_setting(doctype, fieldname, default=None):
	if not _has_column(doctype, fieldname):
		return default
	value = frappe.db.get_single_value(doctype, fieldname)
	return value if value not in (None, "") else default


def _first_non_empty(*values):
	for value in values:
		if value not in (None, ""):
			return value
	return ""


def _to_bounded_float(value, minimum=None, maximum=None):
	if value in (None, ""):
		return None
	number = flt(value)
	if minimum is not None and number < minimum:
		return None
	if maximum is not None and number > maximum:
		return None
	return number


def _get_checkout_map_settings():
	provider = (
		(
			_get_single_setting("Restaurant Web Settings", "restaurant_checkout_map_provider", "neshan")
			or "neshan"
		)
		.strip()
		.lower()
	)
	api_key = (
		frappe.conf.get("restaurant_neshan_api_key")
		or frappe.conf.get("neshan_api_key")
		or _get_single_setting("Restaurant Web Settings", "restaurant_neshan_api_key", "")
		or ""
	).strip()

	script_url = (
		frappe.conf.get("restaurant_neshan_script_url")
		or _get_single_setting("Restaurant Web Settings", "restaurant_neshan_script_url", "")
		or DEFAULT_CHECKOUT_MAP_CONFIG["script_url"]
	).strip()
	style_url = (
		frappe.conf.get("restaurant_neshan_style_url")
		or _get_single_setting("Restaurant Web Settings", "restaurant_neshan_style_url", "")
		or DEFAULT_CHECKOUT_MAP_CONFIG["style_url"]
	).strip()

	default_lat = _to_bounded_float(
		_first_non_empty(
			frappe.conf.get("restaurant_checkout_default_lat"),
			_get_single_setting("Restaurant Web Settings", "restaurant_checkout_default_lat", ""),
		),
		minimum=-90,
		maximum=90,
	)
	default_lng = _to_bounded_float(
		_first_non_empty(
			frappe.conf.get("restaurant_checkout_default_lng"),
			_get_single_setting("Restaurant Web Settings", "restaurant_checkout_default_lng", ""),
		),
		minimum=-180,
		maximum=180,
	)
	default_zoom = cint(
		_first_non_empty(
			frappe.conf.get("restaurant_checkout_default_zoom"),
			_get_single_setting("Restaurant Web Settings", "restaurant_checkout_default_zoom", ""),
			DEFAULT_CHECKOUT_MAP_CONFIG["default_zoom"],
		)
	)
	if default_zoom < 6:
		default_zoom = DEFAULT_CHECKOUT_MAP_CONFIG["default_zoom"]

	return {
		"provider": provider or "neshan",
		"api_key": api_key,
		"script_url": script_url,
		"style_url": style_url,
		"default_lat": default_lat if default_lat is not None else DEFAULT_CHECKOUT_MAP_CONFIG["default_lat"],
		"default_lng": default_lng if default_lng is not None else DEFAULT_CHECKOUT_MAP_CONFIG["default_lng"],
		"default_zoom": default_zoom,
	}


def _normalize_payment_method(value):
	method = (value or "cash").strip().lower()
	if method not in POS_PAYMENT_METHODS:
		return "cash"
	return method


def _normalize_payment_status(value):
	status = (value or "pending").strip().lower()
	if status not in POS_PAYMENT_STATUSES:
		return "pending"
	return status


def _get_pos_hardware_settings():
	defaults = {
		"enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_pos_payment_enabled", 0))
		== 1,
		"provider": (
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_payment_provider", "manual")
			or "manual"
		)
		.strip()
		.lower(),
		"default_method": _normalize_payment_method(
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_default_payment_method", "cash")
		),
		"terminal_id": (
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_terminal_id", "") or ""
		).strip(),
		"local_node_base_url": "http://127.0.0.1:27100",
		"local_node_api_key": "",
		"local_node_timeout_ms": 8000,
		"enabled_drivers": [],
		"scale": {
			"enabled": True,
			"prefix": "20",
			"item_code_digits": 5,
			"weight_digits": 5,
			"checksum_digits": 1,
			"weight_divisor": 1000,
		},
	}

	if frappe.db.exists("DocType", "Restaurant POS Hardware Settings"):
		settings_doc = frappe.get_cached_doc("Restaurant POS Hardware Settings")
		defaults["enabled"] = cint(settings_doc.get("enable_card_payment") or 0) == 1
		defaults["provider"] = (settings_doc.get("payment_provider") or "manual").strip().lower()
		defaults["default_method"] = _normalize_payment_method(
			settings_doc.get("default_payment_method") or "cash"
		)
		defaults["terminal_id"] = (settings_doc.get("default_terminal_id") or "").strip()
		defaults["local_node_base_url"] = (
			settings_doc.get("local_node_base_url") or defaults["local_node_base_url"]
		).strip()
		defaults["local_node_api_key"] = (settings_doc.get("local_node_api_key") or "").strip()
		defaults["local_node_timeout_ms"] = max(cint(settings_doc.get("local_node_timeout_ms") or 8000), 1000)
		defaults["enabled_drivers"] = _parse_json(settings_doc.get("enabled_drivers_json"), []) or []
		defaults["scale"] = {
			"enabled": cint(settings_doc.get("scale_enabled") or 0) == 1,
			"prefix": (settings_doc.get("scale_prefix") or "20").strip() or "20",
			"item_code_digits": max(cint(settings_doc.get("scale_item_code_digits") or 5), 2),
			"weight_digits": max(cint(settings_doc.get("scale_weight_digits") or 5), 2),
			"checksum_digits": max(cint(settings_doc.get("scale_checksum_digits") or 1), 0),
			"weight_divisor": max(cint(settings_doc.get("scale_weight_divisor") or 1000), 1),
		}

	defaults["provider"] = (defaults.get("provider") or "manual").strip().lower()
	if defaults["provider"] not in POS_PAYMENT_PROVIDERS:
		defaults["provider"] = "manual"

	return defaults


def _call_local_hardware_node(path, payload=None, settings=None, method="POST"):
	payload = payload or {}
	settings = settings or _get_pos_hardware_settings()
	base_url = (settings.get("local_node_base_url") or "").strip()
	if not base_url:
		return {
			"ok": False,
			"http_status": 0,
			"response": {},
			"raw_response": "",
			"error": _("Local hardware node URL is not configured."),
			"request": payload,
		}

	request_url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
	headers = {"Content-Type": "application/json"}
	local_api_key = (settings.get("local_node_api_key") or "").strip()
	if local_api_key:
		headers["X-Local-Api-Key"] = local_api_key

	timeout_seconds = max(flt(settings.get("local_node_timeout_ms") or 8000) / 1000.0, 1.0)
	http_status = 0
	raw_response = ""
	response_payload = {}
	try:
		encoded_body = frappe.as_json(payload).encode("utf-8") if method != "GET" else None
		request = Request(request_url, data=encoded_body, headers=headers, method=method)
		with urlopen(request, timeout=timeout_seconds) as response:
			http_status = cint(response.getcode() or 0)
			raw_response = response.read().decode("utf-8", errors="ignore")
	except HTTPError as exc:
		http_status = cint(exc.code or 0)
		try:
			raw_response = exc.read().decode("utf-8", errors="ignore")
		except Exception:
			raw_response = str(exc)
	except URLError as exc:
		return {
			"ok": False,
			"http_status": 0,
			"response": {},
			"raw_response": "",
			"error": _("Local hardware node is unreachable: {0}").format(str(exc.reason or exc)),
			"request": payload,
		}
	except Exception as exc:
		return {
			"ok": False,
			"http_status": 0,
			"response": {},
			"raw_response": "",
			"error": _("Local hardware node request failed: {0}").format(str(exc)),
			"request": payload,
		}

	if raw_response:
		parsed = _parse_json(raw_response, {})
		if isinstance(parsed, dict):
			response_payload = parsed
		else:
			response_payload = {"raw_response": raw_response}

	return {
		"ok": 200 <= http_status < 300,
		"http_status": http_status,
		"response": response_payload,
		"raw_response": raw_response,
		"error": response_payload.get("message") if isinstance(response_payload, dict) else "",
		"request": payload,
	}


def _request_local_node_pos_payment(order_payload, payment_input, settings):
	request_payload = {
		"request_id": (payment_input.get("request_id") or "").strip() or frappe.generate_hash(length=12),
		"order_id": order_payload.get("order_id"),
		"invoice_no": order_payload.get("order_code") or order_payload.get("order_id"),
		"terminal_id": (payment_input.get("terminal_id") or settings.get("terminal_id") or "").strip(),
		"amount": cint(round(flt(order_payload.get("grand_total") or 0))),
		"currency": _get_currency(),
		"timeout_ms": max(cint(settings.get("local_node_timeout_ms") or 8000), 1000),
		"provider": (payment_input.get("provider_hint") or "").strip(),
	}

	node_result = _call_local_hardware_node(
		"/v1/payment/sale", payload=request_payload, settings=settings, method="POST"
	)
	response_payload = node_result.get("response") or {}

	node_status = (
		(
			response_payload.get("status")
			or response_payload.get("result")
			or response_payload.get("payment_status")
			or ""
		)
		.strip()
		.lower()
	)

	status = "failed"
	if node_status in {"approved", "paid", "success", "successful"}:
		status = "paid"
	elif node_status in POS_PAYMENT_PENDING_TOKENS:
		status = "pending"
	elif node_result.get("ok") and (response_payload.get("rrn") or response_payload.get("reference_no")):
		status = "paid"

	message = (
		response_payload.get("message")
		or response_payload.get("detail")
		or node_result.get("error")
		or _("Card payment result received from local hardware node.")
	)

	return {
		"method": "card",
		"provider": "local_node",
		"status": status,
		"reference_no": response_payload.get("reference_no") or response_payload.get("trace_no") or "",
		"rrn": response_payload.get("rrn") or "",
		"trace_no": response_payload.get("trace_no") or "",
		"masked_pan": response_payload.get("masked_pan") or "",
		"message": message,
		"provider_payload": {
			"request": request_payload,
			"http_status": node_result.get("http_status") or 0,
			"response": response_payload,
			"raw_response": node_result.get("raw_response") or "",
			"node_ok": bool(node_result.get("ok")),
		},
	}


def _get_pos_payment_settings():
	hardware_settings = _get_pos_hardware_settings()
	timeout_seconds = cint(
		_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_timeout_seconds", 20)
	)
	if timeout_seconds < 5:
		timeout_seconds = 5

	success_tokens = {
		token.strip().lower()
		for token in _split_tags(
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_success_values", "")
		)
		if token.strip()
	}
	if not success_tokens:
		success_tokens = set(POS_PAYMENT_SUCCESS_TOKENS)

	return {
		"enabled": bool(hardware_settings.get("enabled")),
		"provider": hardware_settings.get("provider") or "manual",
		"default_method": _normalize_payment_method(hardware_settings.get("default_method") or "cash"),
		"terminal_id": (hardware_settings.get("terminal_id") or "").strip(),
		"local_node_base_url": (hardware_settings.get("local_node_base_url") or "").strip(),
		"local_node_api_key": (hardware_settings.get("local_node_api_key") or "").strip(),
		"local_node_timeout_ms": max(cint(hardware_settings.get("local_node_timeout_ms") or 8000), 1000),
		"scale": hardware_settings.get("scale") or {},
		"webhook_url": (
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_url", "") or ""
		).strip(),
		"webhook_api_key": (
			_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_api_key", "") or ""
		).strip(),
		"webhook_timeout_seconds": timeout_seconds,
		"success_tokens": success_tokens,
	}


def _management_pos_payment_boot():
	settings = _get_pos_payment_settings()
	pos_defaults = _parse_json(frappe.defaults.get_global_default("restaurant_pos_defaults") or "{}", {})
	if not isinstance(pos_defaults, dict):
		pos_defaults = {}
	default_method = _normalize_payment_method(pos_defaults.get("default_payment_method") or settings["default_method"])
	default_option = str(pos_defaults.get("default_payment_option") or "").strip()
	return {
		"enabled": settings["enabled"],
		"provider": settings["provider"],
		"default_method": default_method,
		"default_option": default_option,
		"terminal_id": settings["terminal_id"],
		"supports_card": settings["enabled"],
		"local_node": {
			"configured": bool(settings["local_node_base_url"]),
			"base_url": settings["local_node_base_url"],
			"timeout_ms": settings["local_node_timeout_ms"],
		},
		"webhook_configured": bool(settings["webhook_url"]),
		"scale": settings.get("scale") or {},
	}


def _get_pos_profile_user_default():
	for key in ("pos_profile", "POS Profile", "pos profile"):
		try:
			value = frappe.defaults.get_user_default(key)
		except Exception:
			value = ""
		if value:
			return str(value).strip()
	return ""


def _pick_first_profile_value(payload, fieldnames, default=""):
	for fieldname in fieldnames:
		value = payload.get(fieldname)
		if value not in (None, ""):
			return value
	return default


def _pick_profile_bool(payload, fieldnames):
	for fieldname in fieldnames:
		value = payload.get(fieldname)
		if value in (None, ""):
			continue
		return bool(cint(value))
	return False


def _collect_open_pos_shift():
	if not frappe.db.exists("DocType", "POS Opening Shift"):
		return {}

	fields = ["name", "creation", "modified"]
	for fieldname in (
		"status",
		"pos_profile",
		"company",
		"posting_date",
		"period_start_date",
		"opening_amount",
		"user",
	):
		if _has_column("POS Opening Shift", fieldname):
			fields.append(fieldname)

	filters = {}
	if _has_column("POS Opening Shift", "status"):
		filters["status"] = "Open"
	if _has_column("POS Opening Shift", "user"):
		filters["user"] = frappe.session.user
	elif _has_column("POS Opening Shift", "owner"):
		filters["owner"] = frappe.session.user

	rows = frappe.get_all(
		"POS Opening Shift",
		fields=fields,
		filters=filters,
		order_by="modified desc",
		ignore_permissions=True,
		limit_page_length=1,
	)
	if not rows:
		return {}

	row = rows[0]
	return {
		"name": row.get("name") or "",
		"status": row.get("status") or "Open",
		"pos_profile": (row.get("pos_profile") or "").strip(),
		"company": row.get("company") or "",
		"opened_at": _json_safe_datetime(
			row.get("period_start_date") or row.get("creation") or row.get("posting_date")
		),
		"opening_amount": flt(row.get("opening_amount") or 0),
	}


def _serialize_pos_profile_detail(profile_name):
	if not profile_name or not frappe.db.exists("POS Profile", profile_name):
		return {}

	doc = frappe.get_doc("POS Profile", profile_name)
	payload = doc.as_dict()

	payments = []
	for table_fieldname in ("payments", "modes_of_payment", "payment_methods"):
		rows = payload.get(table_fieldname) or []
		if not isinstance(rows, list):
			continue
		for row in rows:
			mode = (
				(row.get("mode_of_payment") or "")
				or (row.get("payment_method") or "")
				or (row.get("default_mode_of_payment") or "")
			).strip()
			if not mode:
				continue
			payments.append(
				{
					"mode_of_payment": mode,
					"type": (row.get("type") or "").strip(),
					"account": (row.get("account") or "").strip(),
					"default": bool(cint(row.get("default") or row.get("is_default"))),
				}
			)
		if payments:
			break

	users = []
	for table_fieldname in ("applicable_for_users", "users", "allowed_users"):
		rows = payload.get(table_fieldname) or []
		if not isinstance(rows, list):
			continue
		for row in rows:
			user = (row.get("user") or row.get("default_user") or "").strip()
			if user and user not in users:
				users.append(user)
		if users:
			break

	currency = _pick_first_profile_value(payload, ("currency",), "")
	if not currency:
		currency = _get_currency()

	profile_title = _pick_first_profile_value(payload, ("title", "pos_profile_name", "name"), profile_name)
	profile_company = _pick_first_profile_value(payload, ("company",), "")
	profile_warehouse = _pick_first_profile_value(payload, ("warehouse", "set_warehouse"), "")
	profile_price_list = _pick_first_profile_value(payload, ("selling_price_list", "price_list"), "")
	profile_customer = _pick_first_profile_value(payload, ("customer",), "")
	profile_cost_center = _pick_first_profile_value(payload, ("cost_center",), "")

	allow_rate_change = _pick_profile_bool(payload, ("allow_rate_change", "allow_user_to_edit_rate"))
	allow_discount_change = _pick_profile_bool(
		payload, ("allow_discount_change", "allow_user_to_edit_discount")
	)
	ignore_pricing_rule = _pick_profile_bool(payload, ("ignore_pricing_rule",))
	update_stock = _pick_profile_bool(payload, ("update_stock",))
	allow_negative_stock = _pick_profile_bool(payload, ("allow_negative_stock",))
	print_receipt_on_order_complete = _pick_profile_bool(payload, ("print_receipt_on_order_complete",))
	disabled = _pick_profile_bool(payload, ("disabled",))

	return {
		"name": profile_name,
		"title": profile_title,
		"company": profile_company,
		"warehouse": profile_warehouse,
		"selling_price_list": profile_price_list,
		"customer": profile_customer,
		"cost_center": profile_cost_center,
		"currency": currency,
		"campaign": _pick_first_profile_value(payload, ("campaign",), ""),
		"taxes_and_charges": _pick_first_profile_value(
			payload,
			("taxes_and_charges", "taxes_and_charges_template"),
			"",
		),
		"write_off_account": _pick_first_profile_value(payload, ("write_off_account",), ""),
		"write_off_cost_center": _pick_first_profile_value(payload, ("write_off_cost_center",), ""),
		"disabled": disabled,
		"allow_rate_change": allow_rate_change,
		"allow_discount_change": allow_discount_change,
		"ignore_pricing_rule": ignore_pricing_rule,
		"update_stock": update_stock,
		"allow_negative_stock": allow_negative_stock,
		"print_receipt_on_order_complete": print_receipt_on_order_complete,
		"capabilities": [
			{
				"key": "allow_rate_change",
				"label": "تغییر نرخ آیتم",
				"enabled": allow_rate_change,
			},
			{
				"key": "allow_discount_change",
				"label": "تغییر تخفیف",
				"enabled": allow_discount_change,
			},
			{
				"key": "ignore_pricing_rule",
				"label": "نادیده گرفتن Pricing Rule",
				"enabled": ignore_pricing_rule,
			},
			{
				"key": "update_stock",
				"label": "ثبت انبار همزمان با فروش",
				"enabled": update_stock,
			},
			{
				"key": "allow_negative_stock",
				"label": "اجازه موجودی منفی",
				"enabled": allow_negative_stock,
			},
			{
				"key": "print_receipt_on_order_complete",
				"label": "چاپ خودکار رسید",
				"enabled": print_receipt_on_order_complete,
			},
		],
		"payments": payments,
		"users": users,
	}


def _management_pos_profile_payload(profile_name=None, include_profiles=True):
	if not frappe.db.exists("DocType", "POS Profile"):
		return {
			"current_user": frappe.session.user,
			"active_profile": "",
			"active_source": "none",
			"profiles": [],
			"profile": {},
			"opening_shift": _collect_open_pos_shift(),
			"options": _management_pos_profile_options() if include_profiles else {},
		}

	fields = ["name", "modified"]
	for fieldname in (
		"company",
		"warehouse",
		"set_warehouse",
		"currency",
		"disabled",
		"title",
		"pos_profile_name",
	):
		if _has_column("POS Profile", fieldname):
			fields.append(fieldname)

	order_by = "modified desc, name asc"
	if _has_column("POS Profile", "disabled"):
		order_by = "disabled asc, " + order_by

	rows = frappe.get_all(
		"POS Profile",
		fields=fields,
		order_by=order_by,
		ignore_permissions=True,
		limit_page_length=200,
	)

	shift = _collect_open_pos_shift()
	shift_profile = (shift.get("pos_profile") or "").strip()
	requested_profile = (profile_name or "").strip()
	user_default_profile = _get_pos_profile_user_default()

	profile_names = []
	profile_map = {}
	for row in rows:
		row_name = str(row.get("name") or "").strip()
		if not row_name:
			continue
		profile_names.append(row_name)
		profile_map[row_name] = row

	active_source = "fallback"
	active_profile = ""
	if requested_profile and requested_profile in profile_map:
		active_profile = requested_profile
		active_source = "requested"
	elif shift_profile and shift_profile in profile_map:
		active_profile = shift_profile
		active_source = "open_shift"
	elif user_default_profile and user_default_profile in profile_map:
		active_profile = user_default_profile
		active_source = "user_default"
	elif profile_names:
		active_profile = profile_names[0]

	if include_profiles:
		profiles = []
		for row in rows:
			row_name = (row.get("name") or "").strip()
			profiles.append(
				{
					"name": row_name,
					"title": row.get("title") or row.get("pos_profile_name") or row_name,
					"company": row.get("company") or "",
					"warehouse": row.get("warehouse") or row.get("set_warehouse") or "",
					"currency": row.get("currency") or _get_currency(),
					"disabled": bool(cint(row.get("disabled") or 0)),
					"active": row_name == active_profile,
					"has_open_shift": bool(shift_profile and shift_profile == row_name),
				}
			)
	else:
		profiles = []

	return {
		"current_user": frappe.session.user,
		"active_profile": active_profile,
		"active_source": active_source,
		"profiles": profiles,
		"profile": _serialize_pos_profile_detail(active_profile),
		"opening_shift": shift,
		"options": _management_pos_profile_options() if include_profiles else {},
	}


def _management_pos_profile_summary():
	payload = _management_pos_profile_payload(include_profiles=False)
	profile = payload.get("profile") or {}
	shift = payload.get("opening_shift") or {}
	return {
		"name": profile.get("name") or "",
		"title": profile.get("title") or profile.get("name") or "",
		"company": profile.get("company") or "",
		"warehouse": profile.get("warehouse") or "",
		"selling_price_list": profile.get("selling_price_list") or "",
		"currency": profile.get("currency") or _get_currency(),
		"has_open_shift": bool(shift.get("name")),
		"shift_name": shift.get("name") or "",
		"shift_opened_at": shift.get("opened_at"),
		"shift_status": shift.get("status") or "",
		"payments": profile.get("payments") or [],
	}


def _resolve_doc_fieldname(doc, candidates):
	for fieldname in candidates:
		if not fieldname:
			continue
		try:
			if doc.meta.has_field(fieldname):
				return fieldname
		except Exception:
			pass
	return ""


def _resolve_meta_fieldname(meta, candidates):
	for fieldname in candidates:
		if not fieldname:
			continue
		try:
			if meta.has_field(fieldname):
				return fieldname
		except Exception:
			pass
	return ""


def _named_doc_options(doctype, label_fields=(), filters=None, limit=500):
	if not frappe.db.exists("DocType", doctype):
		return []

	selected_label_fields = [field for field in (label_fields or []) if _has_column(doctype, field)]
	fields = ["name"] + selected_label_fields
	rows = frappe.get_all(
		doctype,
		fields=fields,
		filters=filters or {},
		order_by="name asc",
		ignore_permissions=True,
		limit_page_length=max(cint(limit), 1),
	)

	options = []
	for row in rows:
		label = ""
		for fieldname in selected_label_fields:
			value = str(row.get(fieldname) or "").strip()
			if value:
				label = value
				break
		options.append(
			{
				"value": row.get("name"),
				"label": label or row.get("name"),
			}
		)
	return options


def _management_pos_profile_options():
	user_filters = {"enabled": 1} if _has_column("User", "enabled") else {}
	return {
		"companies": _named_doc_options("Company", label_fields=("company_name", "abbr")),
		"warehouses": _named_doc_options("Warehouse", label_fields=("warehouse_name",)),
		"price_lists": _named_doc_options("Price List", label_fields=("price_list_name", "currency")),
		"customers": _named_doc_options("Customer", label_fields=("customer_name",)),
		"cost_centers": _named_doc_options("Cost Center", label_fields=("cost_center_name",)),
		"accounts": _named_doc_options("Account", label_fields=("account_name",)),
		"taxes_templates": _named_doc_options("Sales Taxes and Charges Template", label_fields=("title",)),
		"modes_of_payment": _named_doc_options("Mode of Payment", label_fields=("type",)),
		"users": _named_doc_options("User", label_fields=("full_name",), filters=user_filters),
		"currencies": _named_doc_options("Currency", label_fields=("currency_name",)),
	}


def _apply_pos_profile_payment_rows(doc, table_fieldname, payments):
	if payments is None:
		return
	field_meta = doc.meta.get_field(table_fieldname)
	child_dt = field_meta.options if field_meta else ""
	if not child_dt:
		return
	child_meta = frappe.get_meta(child_dt)

	mode_field = _resolve_meta_fieldname(
		child_meta, ("mode_of_payment", "payment_method", "default_mode_of_payment")
	)
	if not mode_field:
		return
	account_field = _resolve_meta_fieldname(child_meta, ("account", "default_account", "paid_to"))
	type_field = _resolve_meta_fieldname(child_meta, ("type", "mode_type"))
	default_field = _resolve_meta_fieldname(child_meta, ("default", "is_default"))

	doc.set(table_fieldname, [])
	for row in payments:
		if not isinstance(row, dict):
			continue
		mode = str(row.get("mode_of_payment") or row.get("payment_method") or "").strip()
		if not mode:
			continue

		row_payload = {mode_field: mode}
		if account_field:
			row_payload[account_field] = str(row.get("account") or "").strip()
		if type_field:
			row_payload[type_field] = str(row.get("type") or "").strip()
		if default_field:
			row_payload[default_field] = cint(row.get("default"))
		doc.append(table_fieldname, row_payload)


def _apply_pos_profile_user_rows(doc, table_fieldname, users):
	if users is None:
		return
	field_meta = doc.meta.get_field(table_fieldname)
	child_dt = field_meta.options if field_meta else ""
	if not child_dt:
		return
	child_meta = frappe.get_meta(child_dt)

	user_field = _resolve_meta_fieldname(child_meta, ("user", "default_user"))
	if not user_field:
		return

	doc.set(table_fieldname, [])
	unique_users = []
	for value in users:
		user = str(value or "").strip()
		if user and user not in unique_users:
			unique_users.append(user)
	for user in unique_users:
		doc.append(table_fieldname, {user_field: user})


def _request_webhook_pos_payment(order_payload, payment_input, settings):
	endpoint = (settings.get("webhook_url") or "").strip()
	if not endpoint:
		return {
			"method": "card",
			"provider": "webhook",
			"status": "failed",
			"reference_no": "",
			"rrn": "",
			"message": _("POS webhook URL is not configured."),
			"provider_payload": {},
		}

	request_payload = {
		"order_id": order_payload.get("order_id"),
		"order_code": order_payload.get("order_code"),
		"amount": flt(order_payload.get("grand_total")),
		"currency": _get_currency(),
		"cashier": frappe.session.user,
		"terminal_id": (payment_input.get("terminal_id") or settings.get("terminal_id") or "").strip(),
	}

	headers = {"Content-Type": "application/json"}
	api_key = (settings.get("webhook_api_key") or "").strip()
	if api_key:
		headers["Authorization"] = f"Bearer {api_key}"

	raw_response = ""
	response_payload = {}
	http_status = 0
	try:
		body = frappe.as_json(request_payload).encode("utf-8")
		request = Request(endpoint, data=body, headers=headers, method="POST")
		with urlopen(request, timeout=settings.get("webhook_timeout_seconds") or 20) as response:
			http_status = cint(response.getcode() or 0)
			raw_response = response.read().decode("utf-8", errors="ignore")
	except HTTPError as exc:
		http_status = cint(exc.code or 0)
		try:
			raw_response = exc.read().decode("utf-8", errors="ignore")
		except Exception:
			raw_response = str(exc)
	except URLError as exc:
		return {
			"method": "card",
			"provider": "webhook",
			"status": "failed",
			"reference_no": "",
			"rrn": "",
			"message": _("POS webhook request failed: {0}").format(str(exc.reason or exc)),
			"provider_payload": {"request": request_payload},
		}
	except Exception as exc:
		return {
			"method": "card",
			"provider": "webhook",
			"status": "failed",
			"reference_no": "",
			"rrn": "",
			"message": _("POS webhook request failed: {0}").format(str(exc)),
			"provider_payload": {"request": request_payload},
		}

	if raw_response:
		parsed_payload = _parse_json(raw_response, {})
		if isinstance(parsed_payload, dict):
			response_payload = parsed_payload
		else:
			response_payload = {"raw_response": raw_response}

	provider_status = (
		response_payload.get("status")
		or response_payload.get("result")
		or response_payload.get("payment_status")
		or ""
	)
	provider_status = provider_status.strip().lower()

	if provider_status in settings.get("success_tokens", set()):
		status = "paid"
	elif provider_status in POS_PAYMENT_PENDING_TOKENS:
		status = "pending"
	elif 200 <= http_status < 300 and (
		response_payload.get("reference_no")
		or response_payload.get("reference")
		or response_payload.get("rrn")
		or response_payload.get("transaction_id")
	):
		status = "paid"
	elif 200 <= http_status < 300:
		status = "pending"
	else:
		status = "failed"

	message = (
		response_payload.get("message")
		or response_payload.get("detail")
		or response_payload.get("error")
		or ""
	)
	if not message:
		message = (
			_("POS payment processed.") if status == "paid" else _("POS payment is pending confirmation.")
		)

	return {
		"method": "card",
		"provider": "webhook",
		"status": status,
		"reference_no": (
			response_payload.get("reference_no")
			or response_payload.get("reference")
			or response_payload.get("transaction_id")
			or ""
		),
		"rrn": response_payload.get("rrn") or response_payload.get("retrieval_ref") or "",
		"message": message,
		"provider_payload": {
			"request": request_payload,
			"http_status": http_status,
			"response": response_payload,
			"raw_response": raw_response,
		},
	}


def _set_restaurant_order_status(order_name, next_status, force=False):
	if not order_name or not _has_column("Sales Order", "restaurant_status"):
		return ""

	normalized_next = (next_status or "").strip().lower()
	if normalized_next not in set(RESTAURANT_STATUS_FLOW + ["cancelled"]):
		return ""

	current = (frappe.db.get_value("Sales Order", order_name, "restaurant_status") or "").strip().lower()
	if not current:
		current = "new"
	if current == "cancelled" and not force:
		return current

	if force:
		frappe.db.set_value(
			"Sales Order", order_name, "restaurant_status", normalized_next, update_modified=False
		)
		return normalized_next

	if current == normalized_next:
		return current

	flow_rank = {value: idx for idx, value in enumerate(RESTAURANT_STATUS_FLOW)}
	current_rank = flow_rank.get(current, -1)
	next_rank = flow_rank.get(normalized_next, -1)
	if next_rank < current_rank:
		return current

	frappe.db.set_value(
		"Sales Order", order_name, "restaurant_status", normalized_next, update_modified=False
	)
	if normalized_next == "delivered":
		try:
			club_apply_fulfillment_effects(order_name)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Restaurant delivered club effects failed")
	return normalized_next


def _get_sales_order_payment_status(order_name):
	if not order_name or not _has_column("Sales Order", "restaurant_payment_status"):
		return ""
	return (frappe.db.get_value("Sales Order", order_name, "restaurant_payment_status") or "").strip().lower()


def _ensure_production_auto_setting_fields():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	field_defs = [
		{
			"fieldname": "restaurant_auto_flow_section",
			"label": "اتوماسیون تولید رستوران",
			"fieldtype": "Section Break",
			"insert_after": "restaurant_pos_webhook_success_values",
		},
		{
			"fieldname": "restaurant_auto_flow_enabled",
			"label": "فعال‌سازی اتوماسیون کامل",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_section",
		},
		{
			"fieldname": "restaurant_auto_flow_on_order_submit",
			"label": "اجرا بعد از ثبت سفارش",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_enabled",
		},
		{
			"fieldname": "restaurant_auto_flow_on_payment",
			"label": "اجرا بعد از پرداخت",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_on_order_submit",
		},
		{
			"fieldname": "restaurant_auto_flow_submit_work_order",
			"label": "ثبت خودکار دستور تولید",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_on_payment",
		},
		{
			"fieldname": "restaurant_auto_flow_material_transfer",
			"label": "انتقال خودکار مواد اولیه",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "restaurant_auto_flow_submit_work_order",
		},
		{
			"fieldname": "restaurant_auto_flow_manufacture",
			"label": "ثبت خودکار تولید",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_material_transfer",
		},
		{
			"fieldname": "restaurant_auto_flow_submit_stock_entries",
			"label": "ثبت نهایی خودکار اسناد انبار",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_manufacture",
		},
		{
			"fieldname": "restaurant_auto_flow_mark_ready",
			"label": "تغییر خودکار وضعیت به آماده",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_submit_stock_entries",
		},
		{
			"fieldname": "restaurant_auto_flow_mark_delivered_on_paid",
			"label": "تحویل خودکار بعد از پرداخت",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_mark_ready",
		},
		{
			"fieldname": "restaurant_auto_flow_create_delivery_note",
			"label": "ایجاد خودکار حواله تحویل",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "restaurant_auto_flow_mark_delivered_on_paid",
		},
		{
			"fieldname": "restaurant_auto_flow_submit_delivery_note",
			"label": "ثبت نهایی خودکار حواله تحویل",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_auto_flow_create_delivery_note",
		},
	]

	for field_def in field_defs:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Restaurant Web Settings", "fieldname": field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Restaurant Web Settings",
			"module": "Restaurant",
			**field_def,
		}

		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			changed = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
			continue

		frappe.get_doc(payload).insert(ignore_permissions=True)

	frappe.clear_cache(doctype="Restaurant Web Settings")


def _production_auto_settings():
	_ensure_production_auto_setting_fields()
	return {
		"enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_enabled", 1))
		== 1,
		"on_order_submit": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_on_order_submit", 1)
		)
		== 1,
		"on_payment": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_on_payment", 1)
		)
		== 1,
		"submit_work_order": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_submit_work_order", 1)
		)
		== 1,
		"material_transfer": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_material_transfer", 0)
		)
		== 1,
		"manufacture": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_manufacture", 1)
		)
		== 1,
		"mark_ready": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_mark_ready", 1)
		)
		== 1,
		"mark_delivered_on_paid": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_mark_delivered_on_paid", 1)
		)
		== 1,
		"create_delivery_note_on_paid": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_create_delivery_note", 0)
		)
		== 1,
		"submit_stock_entries": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_submit_stock_entries", 1)
		)
		== 1,
		"submit_delivery_note": cint(
			_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_submit_delivery_note", 1)
		)
		== 1,
	}


def _normalize_time_string(value, fallback):
	raw = (value or "").strip()
	if not raw:
		return fallback
	try:
		return get_time(raw).strftime("%H:%M:%S")
	except Exception:
		return fallback


def _ensure_pos_shift_setting_fields():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return

	field_defs = [
		{
			"fieldname": "restaurant_pos_shift_settings_section",
			"label": "تنظیمات افتتاحیه و اختتامیه POS",
			"fieldtype": "Section Break",
			"insert_after": "restaurant_auto_flow_submit_delivery_note",
		},
		{
			"fieldname": "restaurant_pos_opening_enabled",
			"label": "فعال سازی افتتاحیه POS",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_pos_shift_settings_section",
		},
		{
			"fieldname": "restaurant_pos_opening_time",
			"label": "ساعت پیش فرض افتتاحیه",
			"fieldtype": "Time",
			"default": "08:00:00",
			"insert_after": "restaurant_pos_opening_enabled",
		},
		{
			"fieldname": "restaurant_pos_opening_cash_float",
			"label": "موجودی اولیه صندوق",
			"fieldtype": "Currency",
			"default": "0",
			"insert_after": "restaurant_pos_opening_time",
		},
		{
			"fieldname": "restaurant_pos_opening_checklist_required",
			"label": "الزام چک لیست افتتاحیه",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_pos_opening_cash_float",
		},
		{
			"fieldname": "restaurant_pos_opening_note_template",
			"label": "متن پیش فرض افتتاحیه",
			"fieldtype": "Small Text",
			"insert_after": "restaurant_pos_opening_checklist_required",
		},
		{
			"fieldname": "restaurant_pos_closing_enabled",
			"label": "فعال سازی اختتامیه POS",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_pos_opening_note_template",
		},
		{
			"fieldname": "restaurant_pos_closing_time",
			"label": "ساعت پیش فرض اختتامیه",
			"fieldtype": "Time",
			"default": "23:00:00",
			"insert_after": "restaurant_pos_closing_enabled",
		},
		{
			"fieldname": "restaurant_pos_closing_expected_cash",
			"label": "موجودی هدف اختتامیه",
			"fieldtype": "Currency",
			"default": "0",
			"insert_after": "restaurant_pos_closing_time",
		},
		{
			"fieldname": "restaurant_pos_closing_tolerance",
			"label": "تلرانس اختلاف صندوق",
			"fieldtype": "Currency",
			"default": "0",
			"insert_after": "restaurant_pos_closing_expected_cash",
		},
		{
			"fieldname": "restaurant_pos_closing_checklist_required",
			"label": "الزام چک لیست اختتامیه",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "restaurant_pos_closing_tolerance",
		},
		{
			"fieldname": "restaurant_pos_closing_note_template",
			"label": "متن پیش فرض اختتامیه",
			"fieldtype": "Small Text",
			"insert_after": "restaurant_pos_closing_checklist_required",
		},
	]

	for field_def in field_defs:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Restaurant Web Settings", "fieldname": field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Restaurant Web Settings",
			"module": "Restaurant",
			**field_def,
		}

		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			changed = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
			continue

		frappe.get_doc(payload).insert(ignore_permissions=True)

	frappe.clear_cache(doctype="Restaurant Web Settings")


def _pos_shift_settings():
	_ensure_pos_shift_setting_fields()
	return {
		"opening": {
			"enabled": cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_enabled", 1)
			)
			== 1,
			"time": (
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_time", "08:00:00")
				or "08:00:00"
			),
			"cash_float": flt(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_cash_float", 0)
			),
			"checklist_required": cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_checklist_required", 1)
			)
			== 1,
			"note_template": (
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_note_template", "")
				or ""
			).strip(),
		},
		"closing": {
			"enabled": cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_enabled", 1)
			)
			== 1,
			"time": (
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_time", "23:00:00")
				or "23:00:00"
			),
			"expected_cash": flt(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_expected_cash", 0)
			),
			"tolerance": flt(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_tolerance", 0)
			),
			"checklist_required": cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_checklist_required", 1)
			)
			== 1,
			"note_template": (
				_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_note_template", "")
				or ""
			).strip(),
		},
	}


def _create_work_order_stock_entry(
	work_order_name, purpose, qty, submit_doc=True, allow_negative_stock=False
):
	"""Create Stock Entry for a Work Order - uses get_items() before insert()"""
	wo = frappe.get_doc("Work Order", work_order_name)
	se = frappe.new_doc("Stock Entry")
	se.flags.ignore_permissions = True
	se.company = wo.company
	se.work_order = work_order_name
	se.from_bom = 1
	se.bom_no = wo.bom_no
	se.fg_completed_qty = flt(qty)
	se.use_multi_level_bom = 0
	se.set_process_loss = 0
	
	if purpose == "Material Transfer for Manufacture":
		se.stock_entry_type = "Material Transfer for Manufacture"
		se.purpose = "Material Transfer for Manufacture"
		se.to_warehouse = wo.wip_warehouse or wo.source_warehouse
	elif purpose == "Manufacture":
		se.stock_entry_type = "Manufacture"
		se.purpose = "Manufacture"
	else:
		se.stock_entry_type = purpose
		se.purpose = purpose
	
	# Get items from BOM BEFORE insert
	se.get_items()
	
	# Allow zero valuation rate for all items (مواد اولیه ممکنه قیمت نداشته باشن)
	for item in se.get("items") or []:
		item.allow_zero_valuation_rate = 1
	
	if purpose == "Material Transfer for Manufacture":
		to_remove = []
		for item in se.get("items") or []:
			if item.is_finished_item:
				to_remove.append(item)
			else:
				if not item.s_warehouse:
					item.s_warehouse = wo.source_warehouse
				if item.t_warehouse:
					item.t_warehouse = None
		for item in to_remove:
			se.items.remove(item)
		if not se.get("items"):
			return "already_done_no_items"
	elif purpose == "Manufacture":
		for item in se.get("items") or []:
			if item.is_finished_item:
				if not item.t_warehouse and wo.fg_warehouse:
					item.t_warehouse = wo.fg_warehouse
				if item.s_warehouse:
					item.s_warehouse = None
			else:
				if not item.s_warehouse:
					item.s_warehouse = wo.wip_warehouse or wo.source_warehouse
				if item.t_warehouse:
					item.t_warehouse = None
	
	se.flags.ignore_validate = True
	se.insert()
	if submit_doc:
		_submit_stock_document(se, allow_negative_stock=allow_negative_stock)
	else:
		se.save()
	return se.name
def _existing_delivery_note_for_sales_order(so_name, submitted_only=False):
	if not so_name or not frappe.db.exists("DocType", "Delivery Note Item"):
		return ""

	filters = {"against_sales_order": so_name, "docstatus": 1}
	row = frappe.get_all(
		"Delivery Note Item",
		filters=filters,
		fields=["parent"],
		order_by="creation desc",
		limit_page_length=1,
		ignore_permissions=True,
	)
	if row:
		# Double-check the parent actually IS a Delivery Note (not SI)
		parent = row[0].parent
		if frappe.db.exists("Delivery Note", parent):
			return parent
	return ""


def _submit_stock_document(doc, allow_negative_stock=False):
	if not allow_negative_stock:
		doc.submit()
		return

	previous_value = cint(frappe.db.get_single_value("Stock Settings", "allow_negative_stock"))
	changed = previous_value != 1
	if changed:
		frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)
		frappe.clear_cache(doctype="Stock Settings")

	try:
		doc.submit()
	finally:
		if changed:
			frappe.db.set_single_value("Stock Settings", "allow_negative_stock", previous_value)
			frappe.clear_cache(doctype="Stock Settings")


def _create_delivery_note_for_sales_order(
	so_name, fg_warehouse_map=None, submit_doc=True, allow_negative_stock=False
):
	"""Create Delivery Note from SO - forces qty regardless of delivered_qty"""
	fg_warehouse_map = fg_warehouse_map or {}
	# Check if a DN already exists
	if so_name and frappe.db.exists("DocType", "Delivery Note Item"):
		row = frappe.get_all("Delivery Note Item",
			filters={"against_sales_order": so_name, "docstatus": ["!=", 2]},
			fields=["parent"], limit=1, ignore_permissions=True)
		if row and frappe.db.exists("Delivery Note", row[0].parent):
			return row[0].parent

	so = frappe.get_doc("Sales Order", so_name)
	dn = frappe.new_doc("Delivery Note")
	dn.company = so.company
	dn.customer = so.customer
	dn.set_posting_time = 1
	dn.posting_date = today()
	dn.posting_time = frappe.utils.nowtime()
	dn.flags.ignore_permissions = True

	# Get default warehouse
	default_wh = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""

	for item in so.items:
		pending_qty = flt(item.qty) - flt(item.delivered_qty)
		if pending_qty <= 0:
			continue
		warehouse = fg_warehouse_map.get(item.item_code) or item.warehouse or default_wh
		if not warehouse:
			item_default = frappe.get_all("Item Default",
				filters={"parent": item.item_code, "company": so.company},
				fields=["default_warehouse"], limit=1, ignore_permissions=True)
			if item_default:
				warehouse = item_default[0].default_warehouse or ""
		dn.append("items", {
			"item_code": item.item_code,
			"item_name": item.item_name,
			"description": item.description or "",
			"qty": pending_qty,
			"rate": item.rate,
			"amount": pending_qty * flt(item.rate),
			"uom": item.uom,
			"stock_uom": item.stock_uom or item.uom,
			"conversion_factor": item.conversion_factor or 1,
			"warehouse": warehouse,
			"against_sales_order": so_name,
			"so_detail": item.name,
			"allow_zero_valuation_rate": 1,
		})

	if not dn.items:
		return ""

	dn.insert()
	if submit_doc:
		_submit_stock_document(dn, allow_negative_stock=allow_negative_stock)
	return dn.name
def _run_sales_order_auto_flow(
	order_name, trigger="manual", payment_status=None, force=False, allow_negative_stock=False
):
	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		return {"status": "skipped", "reason": "order_not_found"}

	settings = _production_auto_settings()
	trigger_name = (trigger or "manual").strip().lower() or "manual"
	if not settings.get("enabled") and not force:
		return {"status": "skipped", "reason": "disabled"}
	if trigger_name == "order_submit" and not settings.get("on_order_submit") and not force:
		return {"status": "skipped", "reason": "on_submit_disabled"}
	if trigger_name == "payment" and not settings.get("on_payment") and not force:
		return {"status": "skipped", "reason": "on_payment_disabled"}

	so_doc = frappe.get_doc("Sales Order", so_name)
	summary = {
		"status": "success",
		"sales_order": so_name,
		"trigger": trigger_name,
		"created_tickets": [],
		"created_work_orders": [],
		"submitted_work_orders": [],
		"stock_entries": [],
		"delivery_note": "",
		"fg_warehouse_map": {},
		"errors": [],
		"final_restaurant_status": "",
	}

	ticket_names = []
	if frappe.db.exists("DocType", "Restaurant Production Ticket"):
		ticket_names = frappe.get_all(
			"Restaurant Production Ticket",
			filters={"sales_order": so_name},
			pluck="name",
			ignore_permissions=True,
			order_by="creation asc",
		)

	if not ticket_names:
		try:
			creation_payload = _create_production_for_sales_order(so_doc)
			summary["created_tickets"] = creation_payload.get("production_tickets") or []
			summary["created_work_orders"] = creation_payload.get("work_orders") or []
			ticket_names = summary["created_tickets"]
		except Exception:
			summary["errors"].append(_("Production ticket creation failed."))
			frappe.log_error(frappe.get_traceback(), f"Restaurant Auto Flow Ticket Create ({so_name})")

	work_order_names = set()
	ticket_docs = []
	fg_warehouse_map = {}
	for ticket_name in ticket_names:
		if not frappe.db.exists("Restaurant Production Ticket", ticket_name):
			continue
		ticket_doc = frappe.get_doc("Restaurant Production Ticket", ticket_name)
		ticket_docs.append(ticket_doc)
		if ticket_doc.get("menu_item") and ticket_doc.get("fg_warehouse"):
			fg_warehouse_map[ticket_doc.get("menu_item")] = ticket_doc.get("fg_warehouse")
		work_order_name = (ticket_doc.get("work_order") or "").strip()
		if work_order_name:
			work_order_names.add(work_order_name)

	any_started = False
	completed_tickets = 0
	for ticket_doc in ticket_docs:
		work_order_name = (ticket_doc.get("work_order") or "").strip()
		if not work_order_name or not frappe.db.exists("Work Order", work_order_name):
			summary["errors"].append(_("Work Order missing for ticket {0}.").format(ticket_doc.name))
			continue

		wo_doc = frappe.get_doc("Work Order", work_order_name)
		if settings.get("submit_work_order") and cint(wo_doc.docstatus) == 0:
			try:
				wo_doc.flags.ignore_permissions = True
				wo_doc.submit()
				summary["submitted_work_orders"].append(wo_doc.name)
				wo_doc = frappe.get_doc("Work Order", wo_doc.name)
			except Exception:
				summary["errors"].append(_("Could not submit Work Order {0}.").format(wo_doc.name))
				frappe.log_error(frappe.get_traceback(), f"Restaurant Auto Flow WO Submit ({wo_doc.name})")
				continue

		if cint(wo_doc.docstatus) != 1:
			continue

		any_started = True
		if (ticket_doc.get("status") or "").strip().lower() == "planned":
			ticket_doc.db_set("status", "in_progress", update_modified=False)

		pending_transfer = max(flt(wo_doc.qty) - flt(wo_doc.material_transferred_for_manufacturing), 0)
		if settings.get("material_transfer") and pending_transfer > 1e-8 and not cint(wo_doc.skip_transfer):
			try:
				se_name = _create_work_order_stock_entry(
					wo_doc.name,
					"Material Transfer for Manufacture",
					pending_transfer,
					submit_doc=settings.get("submit_stock_entries"),
					allow_negative_stock=allow_negative_stock,
				)
				if se_name:
					summary["stock_entries"].append(se_name)
			except Exception:
				summary["errors"].append(
					_("Material transfer failed for Work Order {0}.").format(wo_doc.name)
				)
				frappe.log_error(
					frappe.get_traceback(),
					f"Restaurant Auto Flow Transfer ({wo_doc.name})",
				)

		wo_doc = frappe.get_doc("Work Order", wo_doc.name)
		pending_manufacture = max(flt(wo_doc.qty) - flt(wo_doc.produced_qty), 0)
		if settings.get("manufacture") and pending_manufacture > 1e-8:
			try:
				se_name = _create_work_order_stock_entry(
					wo_doc.name,
					"Manufacture",
					pending_manufacture,
					submit_doc=settings.get("submit_stock_entries"),
					allow_negative_stock=allow_negative_stock,
				)
				if se_name:
					summary["stock_entries"].append(se_name)
			except Exception:
				summary["errors"].append(
					_("Manufacture entry failed for Work Order {0}.").format(wo_doc.name)
				)
				frappe.log_error(
					frappe.get_traceback(),
					f"Restaurant Auto Flow Manufacture ({wo_doc.name})",
				)

		wo_doc = frappe.get_doc("Work Order", wo_doc.name)
		if hasattr(wo_doc, "update_work_order_qty"):
			try:
				wo_doc.update_work_order_qty()
			except Exception:
				pass
		if hasattr(wo_doc, "update_status"):
			try:
				wo_doc.update_status()
			except Exception:
				pass

		if flt(wo_doc.produced_qty) >= flt(wo_doc.qty) - 1e-8:
			completed_tickets += 1
			if (ticket_doc.get("status") or "").strip().lower() != "completed":
				ticket_doc.db_set("status", "completed", update_modified=False)
		else:
			if (ticket_doc.get("status") or "").strip().lower() == "planned":
				ticket_doc.db_set("status", "in_progress", update_modified=False)

	has_production = bool(ticket_docs)
	summary["fg_warehouse_map"] = fg_warehouse_map
	all_completed = has_production and completed_tickets == len(ticket_docs)
	if any_started:
		_set_restaurant_order_status(so_name, "preparing")
	if settings.get("mark_ready") and (all_completed or not has_production):
		_set_restaurant_order_status(so_name, "ready")

	effective_payment_status = (
		(payment_status or _get_sales_order_payment_status(so_name) or "").strip().lower()
	)
	if effective_payment_status == "paid" and settings.get("mark_delivered_on_paid"):
		if settings.get("create_delivery_note_on_paid"):
			try:
				summary["delivery_note"] = _create_delivery_note_for_sales_order(
					so_name,
					fg_warehouse_map=fg_warehouse_map,
					submit_doc=settings.get("submit_delivery_note"),
				)
			except Exception:
				summary["errors"].append(_("Delivery Note creation failed."))
				frappe.log_error(frappe.get_traceback(), f"Restaurant Auto Flow Delivery Note ({so_name})")
		_set_restaurant_order_status(so_name, "delivered")

	summary["final_restaurant_status"] = (
		frappe.db.get_value("Sales Order", so_name, "restaurant_status")
		if _has_column("Sales Order", "restaurant_status")
		else ""
	) or ""
	return summary


def _save_management_pos_payment(order_name, payment_result, run_auto_flow=True, auto_flow_trigger="payment"):
	if not order_name or not frappe.db.exists("Sales Order", order_name):
		return {}

	updates = {}
	if _has_column("Sales Order", "restaurant_payment_method"):
		updates["restaurant_payment_method"] = payment_result.get("method") or ""
	if _has_column("Sales Order", "restaurant_payment_provider"):
		updates["restaurant_payment_provider"] = payment_result.get("provider") or ""
	if _has_column("Sales Order", "restaurant_payment_status"):
		updates["restaurant_payment_status"] = payment_result.get("status") or ""
	if _has_column("Sales Order", "restaurant_payment_reference"):
		updates["restaurant_payment_reference"] = payment_result.get("reference_no") or ""
	if _has_column("Sales Order", "restaurant_payment_rrn"):
		updates["restaurant_payment_rrn"] = payment_result.get("rrn") or ""
	if _has_column("Sales Order", "restaurant_payment_payload_json"):
		updates["restaurant_payment_payload_json"] = frappe.as_json(
			payment_result.get("provider_payload") or {}
		)

	if updates:
		frappe.db.set_value("Sales Order", order_name, updates, update_modified=False)

	if not run_auto_flow:
		return {"status": "skipped", "reason": "manual_payment_update"}

	return _run_sales_order_auto_flow(
		order_name,
		trigger=auto_flow_trigger or "payment",
		payment_status=(payment_result.get("status") or "").strip().lower(),
	)


def _insert_management_pos_payment_log(order_payload, payment_result):
	if not frappe.db.exists("DocType", "Restaurant POS Payment Log"):
		return

	so_name = (order_payload.get("order_id") or "").strip()
	order_code = (order_payload.get("order_code") or so_name).strip()
	provider_payload = payment_result.get("provider_payload") or {}
	request_payload = provider_payload.get("request") or {}
	response_payload = provider_payload.get("response") or {}
	request_id = (
		request_payload.get("request_id")
		or provider_payload.get("request_id")
		or f"{order_code}-{frappe.generate_hash(length=6)}"
	)

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Restaurant POS Payment Log",
				"request_id": request_id,
				"sales_order": so_name,
				"order_code": order_code,
				"amount": flt(order_payload.get("grand_total") or 0),
				"currency": _get_currency(),
				"provider": payment_result.get("provider") or "",
				"terminal_id": request_payload.get("terminal_id") or "",
				"payment_method": payment_result.get("method") or "",
				"status": payment_result.get("status") or "",
				"rrn": payment_result.get("rrn") or "",
				"trace_no": payment_result.get("trace_no") or response_payload.get("trace_no") or "",
				"masked_pan": payment_result.get("masked_pan") or response_payload.get("masked_pan") or "",
				"latency_ms": cint(provider_payload.get("latency_ms") or 0),
				"request_payload_json": frappe.as_json(request_payload),
				"response_payload_json": frappe.as_json(response_payload),
				"error_text": (payment_result.get("message") or "")[:140],
				"cashier": frappe.session.user,
			}
		)
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant POS Payment Log Insert Failed")


def _insert_management_hardware_event(
	event_type, severity, message, payload=None, related_order=None, source="pos"
):
	if not frappe.db.exists("DocType", "Restaurant POS Hardware Event"):
		return

	clean_severity = (severity or "info").strip().lower()
	if clean_severity not in POS_HARDWARE_EVENT_SEVERITIES:
		clean_severity = "info"

	try:
		doc = frappe.get_doc(
			{
				"doctype": "Restaurant POS Hardware Event",
				"event_type": (event_type or "system").strip().lower() or "system",
				"severity": clean_severity,
				"source": (source or "pos").strip() or "pos",
				"message": (message or "")[:140],
				"payload_json": frappe.as_json(payload or {}),
				"related_order": (related_order or "").strip(),
				"event_at": now_datetime(),
			}
		)
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant POS Hardware Event Insert Failed")


def _clean_automatic_pos_note(note_value):
	"""Return only text explicitly entered by the cashier/customer."""
	parts = []
	for raw_part in re.split(r"[|\n]", str(note_value or "")):
		part = raw_part.strip()
		if not part:
			continue
		if any(marker in part for marker in _AUTOMATIC_POS_NOTE_MARKERS):
			continue
		parts.append(part)
	return " | ".join(parts)


def _append_sales_order_note(order_name, note_line):
	if not order_name or not _has_column("Sales Order", "restaurant_note"):
		return

	existing_note = frappe.db.get_value("Sales Order", order_name, "restaurant_note") or ""
	clean_existing = _clean_automatic_pos_note(existing_note)
	is_automatic = any(marker in str(note_line or "") for marker in _AUTOMATIC_POS_NOTE_MARKERS)
	if is_automatic:
		# Also clean legacy POS markers when the order changes state.
		if clean_existing != str(existing_note or "").strip():
			frappe.db.set_value("Sales Order", order_name, "restaurant_note", clean_existing, update_modified=False)
		return

	clean_line = str(note_line or "").strip()
	if not clean_line:
		if clean_existing != str(existing_note or "").strip():
			frappe.db.set_value("Sales Order", order_name, "restaurant_note", clean_existing, update_modified=False)
		return
	merged_note = f"{clean_existing} | {clean_line}".strip(" |") if clean_existing else clean_line
	frappe.db.set_value("Sales Order", order_name, "restaurant_note", merged_note, update_modified=False)


def _process_management_pos_payment(order_payload, payment_input):
	payment_input = _parse_json(payment_input, {})
	if not isinstance(payment_input, dict):
		payment_input = {}

	settings = _get_pos_payment_settings()
	method = _normalize_payment_method(payment_input.get("method") or settings.get("default_method"))
	provider = (payment_input.get("provider") or settings.get("provider") or "manual").strip().lower()
	if provider not in POS_PAYMENT_PROVIDERS:
		provider = settings.get("provider") or "manual"

	payment_result = {
		"method": method,
		"mode_of_payment": (payment_input.get("mode_of_payment") or "").strip(),
		"provider": provider,
		"status": "paid" if method == "cash" else "pending",
		"reference_no": "",
		"rrn": "",
		"message": (
			_("Cash payment recorded.")
			if method == "cash"
			else _("Credit sale recorded. Payment will be collected later.")
			if method == "credit"
			else _("Card payment is pending.")
		),
		"provider_payload": {},
	}

	manual_reference = (payment_input.get("reference_no") or payment_input.get("reference") or "").strip()
	manual_rrn = (payment_input.get("rrn") or "").strip()

	if method == "card":
		if settings.get("enabled") and provider == "local_node":
			payment_result = _request_local_node_pos_payment(order_payload, payment_input, settings)
		elif settings.get("enabled") and provider == "webhook":
			payment_result = _request_webhook_pos_payment(order_payload, payment_input, settings)
		elif not settings.get("enabled"):
			payment_result["status"] = "pending"
			payment_result["message"] = _("POS integration is disabled. Confirm payment manually.")
		else:
			payment_result["status"] = "pending"
			payment_result["message"] = _("Manual card payment mode. Confirm transaction after POS approval.")
	elif method == "credit":
		payment_result["status"] = "pending"
		payment_result["message"] = _("Credit sale recorded. Payment will be collected later.")

	if manual_reference:
		payment_result["reference_no"] = manual_reference
	if manual_rrn:
		payment_result["rrn"] = manual_rrn

	if not payment_result.get("mode_of_payment"):
		payment_result["mode_of_payment"] = (payment_input.get("mode_of_payment") or "").strip()

	if method == "card" and (manual_reference or manual_rrn):
		payment_result["status"] = "paid"
		payment_result["message"] = _("Card payment confirmed manually.")

	payment_result["status"] = _normalize_payment_status(payment_result.get("status"))
	automation_payload = _save_management_pos_payment(order_payload.get("order_id"), payment_result)
	_insert_management_pos_payment_log(order_payload, payment_result)
	payment_result["automation"] = automation_payload or {}

	if payment_result.get("message"):
		_append_sales_order_note(order_payload.get("order_id"), f"[PAYMENT] {payment_result['message']}")

	if payment_result.get("status") == "failed":
		_insert_management_hardware_event(
			event_type="card_pos",
			severity="error",
			message=payment_result.get("message") or "Card payment failed",
			payload=payment_result.get("provider_payload") or {},
			related_order=order_payload.get("order_id"),
		)

	return payment_result


def _get_branding_payload():
	# Layer 1: defaults
	result = {
		"name": "Restaurant",
		"tagline": "منوی آنلاین تازه، سریع و شفاف",
		"hero_title": "سالادهای تازه و غذای سالم روز",
		"hero_subtitle": "با انتخاب کامل مواد داخل هر غذا، سفارش مهمان را سریع ثبت کنید.",
		"hero_image": "",
		"primary_cta_label": "ورود به منو",
		"header_variant": "classic",
		"menu_search_variant": "search-card",
		"hero_section_variant": "off",
		"footer_variant": "full",
		"card_variant": "classic",
		"hero_section_title": "",
		"hero_section_description": "",
		"hero_section_cta": "",
		"hero_variant_contents": {},
		"footer_description": "",
		"footer_phone": "",
		"footer_email": "",
		"footer_address": "",
		"footer_instagram": "",
		"footer_telegram": "",
		"footer_copyright": "",
	}

	# Layer 2: web_settings blob (primary storage)
	try:
		raw_blob = frappe.defaults.get_global_default(MANAGEMENT_SITE_SETTINGS_BLOB_KEY)
		blob = _parse_json(raw_blob, {})
		if isinstance(blob, dict) and blob:
			for key in result:
				if key in blob and blob[key] not in (None, ""):
					result[key] = blob[key]
	except Exception:
		pass

	# Layer 3: display variant settings
	try:
		raw_dv = frappe.defaults.get_global_default(MANAGEMENT_DISPLAY_VARIANT_KEY)
		dv = _parse_json(raw_dv, {})
		if isinstance(dv, dict):
			for key in [
				"header_variant",
				"menu_search_variant",
				"hero_section_variant",
				"footer_variant",
				"card_variant",
			]:
				if key in dv and dv[key] not in (None, ""):
					result[key] = dv[key]
	except Exception:
		pass

	# Layer 4: Restaurant Web Settings DocType (only basic fields)
	try:
		if frappe.db.exists("DocType", "Restaurant Web Settings"):
			settings = frappe.get_cached_doc("Restaurant Web Settings")
			for key in ["tagline", "hero_title", "hero_subtitle", "hero_image", "primary_cta_label"]:
				val = settings.get(key)
				if val not in (None, ""):
					result[key] = val
			# brand_name is special - use the field directly
			brand_name = settings.get("brand_name")
			if brand_name not in (None, ""):
				result["name"] = brand_name
	except Exception:
		pass

	return result


def _get_hero_slides(branch=None):
	if not frappe.db.exists("DocType", "Restaurant Hero Slide"):
		return []

	filters = {"is_active": 1}
	if branch and _has_column("Restaurant Hero Slide", "branch"):
		filters["branch"] = ["in", [branch, ""]]

	rows = frappe.get_all(
		"Restaurant Hero Slide",
		filters=filters,
		fields=[
			"name",
			"title",
			"subtitle",
			"image",
			"linked_item",
			"cta_label",
			"cta_url",
			"sort_order",
		],
		ignore_permissions=True,
		order_by="sort_order asc, modified asc",
	)

	image_field = _core_item_image_field()
	slides = []
	for row in rows:
		item_slug = ""
		item_image = ""
		if row.linked_item:
			item_data = (
				frappe.db.get_value(
					"Item",
					row.linked_item,
					["restaurant_slug", f"{image_field} as image", "item_name"],
					as_dict=True,
				)
				or {}
			)
			item_slug = (item_data.get("restaurant_slug") or "").strip()
			item_image = (item_data.get("image") or "").strip()
			if not row.title:
				row.title = item_data.get("item_name") or row.title

		cta_url = (row.cta_url or "").strip()
		if item_slug:
			cta_url = f"/restaurant/item/{item_slug}"
		elif not cta_url:
			cta_url = "/restaurant/menu"

		slides.append(
			{
				"name": row.name,
				"title": row.title or "",
				"subtitle": row.subtitle or "",
				"image": row.image or item_image,
				"cta_label": row.cta_label or "مشاهده محصول",
				"cta_url": cta_url,
				"item_slug": item_slug,
				"sort_order": cint(row.sort_order),
			}
		)

	return slides


def _get_about_us_sections():
	if not frappe.db.exists("DocType", "Restaurant About Section"):
		return []

	doctype = "Restaurant About Section"
	available_fields = ["name"]
	for fieldname in [
		"section_type",
		"title",
		"subtitle",
		"badge",
		"founded_year",
		"icon",
		"year_label",
		"highlight",
		"body_text",
		"image",
		"stat_label",
		"stat_value",
		"sort_order",
		"is_active",
	]:
		if _has_column(doctype, fieldname):
			available_fields.append(fieldname)

	filters = {"is_active": 1} if _has_column(doctype, "is_active") else {}
	order_by = "sort_order asc, modified asc" if _has_column(doctype, "sort_order") else "modified asc"

	rows = frappe.get_all(
		doctype,
		filters=filters,
		fields=available_fields,
		ignore_permissions=True,
		order_by=order_by,
	)

	return [
		{
			"name": row.get("name"),
			"section_type": row.get("section_type") or "story",
			"title": row.get("title") or "",
			"subtitle": row.get("subtitle") or "",
			"badge": row.get("badge") or "",
			"founded_year": row.get("founded_year") or "",
			"icon": row.get("icon") or "",
			"year_label": row.get("year_label") or "",
			"highlight": cint(row.get("highlight")),
			"body_text": row.get("body_text") or "",
			"image": row.get("image") or "",
			"stat_label": row.get("stat_label") or "",
			"stat_value": row.get("stat_value") or "",
			"sort_order": cint(row.get("sort_order")),
			"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
		}
		for row in rows
	]


def _get_faq_items():
	if not frappe.db.exists("DocType", "Restaurant FAQ"):
		return []

	doctype = "Restaurant FAQ"
	available_fields = ["name"]
	for fieldname in ["question", "answer", "sort_order", "is_active"]:
		if _has_column(doctype, fieldname):
			available_fields.append(fieldname)

	filters = {"is_active": 1} if _has_column(doctype, "is_active") else {}
	order_by = "sort_order asc, modified asc" if _has_column(doctype, "sort_order") else "modified asc"

	rows = frappe.get_all(
		doctype,
		filters=filters,
		fields=available_fields,
		ignore_permissions=True,
		order_by=order_by,
	)

	return [
		{
			"name": row.get("name"),
			"question": row.get("question") or "",
			"answer": row.get("answer") or "",
			"sort_order": cint(row.get("sort_order")),
			"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
		}
		for row in rows
	]


def _has_column(doctype, fieldname):
	try:
		return frappe.db.has_column(doctype, fieldname)
	except Exception:
		return False


def _has_doctype_field(doctype, fieldname):
	try:
		meta = frappe.get_meta(doctype)
		if meta.has_field(fieldname):
			return True
		return bool(
			frappe.db.get_value(
				"Custom Field",
				{"dt": doctype, "fieldname": fieldname},
				"name",
			)
		)
	except Exception:
		return False


def _ensure_coming_soon_field():
	if _has_column("Item", "restaurant_coming_soon"):
		return True
	try:
		setup_coming_soon_field()
		frappe.clear_cache(doctype="Item")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.ensure_coming_soon_field")
	return _has_column("Item", "restaurant_coming_soon")


def _has_core_menu_support():
	return all(
		[
			_has_column("Item", "restaurant_enabled"),
			_has_column("Item", "restaurant_slug"),
			_has_column("Item", "restaurant_category"),
			_has_column("Item Group", "restaurant_is_menu_category"),
			_has_column("Item Group", "restaurant_is_subcategory"),
			_has_column("Item Group", "restaurant_slug"),
		]
	)


def _use_core_menu_data():
	if not _has_core_menu_support():
		frappe.throw(_("Core restaurant fields are not installed on Item/Item Group."))
	return True


def _core_item_image_field():
	for fieldname in ("image", "item_image", "website_image"):
		if _has_column("Item", fieldname):
			return fieldname
	return "image"


def sync_item_image_from_attachment(doc, method=None):
	"""After insert/update Item: if image field is empty but attachments have images,
	use the first attached image as the item's image."""
	if not doc or not doc.name:
		return

	image_field = _core_item_image_field()
	current_image = getattr(doc, image_field, "") or ""
	if current_image:
		return

	# Find first image attachment
	try:
		attachments = frappe.get_all(
			"File",
			filters={
				"attached_to_doctype": "Item",
				"attached_to_name": doc.name,
				"is_private": 0,
			},
			fields=["name", "file_url"],
			order_by="creation asc",
			limit=10,
		)
	except Exception:
		return

	for att in attachments or []:
		file_url = att.get("file_url") or ""
		if file_url and ("/files/" in file_url or "http" in file_url):
			try:
				frappe.db.set_value("Item", doc.name, image_field, file_url, update_modified=False)
			except Exception:
				pass
			break


def sync_item_image_from_file_attachment(doc, method=None):
	"""After insert on File: if the file is attached to an Item and the Item's
	image field is empty, use this file's URL as the item's image.
	This handles images uploaded via Management panel (POS/back-office)."""
	if not doc or not doc.name:
		return

	# Only process files attached to Item
	if doc.get("attached_to_doctype") != "Item" or not doc.get("attached_to_name"):
		return

	item_name = doc.get("attached_to_name")
	file_url = doc.get("file_url") or ""

	if not file_url:
		return

	# Check if item already has an image
	image_field = _core_item_image_field()
	current_image = frappe.db.get_value("Item", item_name, image_field) or ""
	if current_image:
		return

	# Set the file as item's image
	try:
		frappe.db.set_value("Item", item_name, image_field, file_url, update_modified=False)
		print(f"HOOK FIRED: Set image for {item_name} to {file_url}")
	except Exception as e:
		print(f"HOOK ERROR: {e}")


def sync_item_image_on_file_change(doc, method=None):
	"""Wildcard on_update hook: when any doc is updated, check if it's a File
	attached to an Item — if so, sync the Item's image field."""
	if doc.doctype != "File":
		return
	attached_to_doctype = getattr(doc, "attached_to_doctype", "") or ""
	attached_to_name = getattr(doc, "attached_to_name", "") or ""
	if attached_to_doctype != "Item" or not attached_to_name:
		return
	file_url = (getattr(doc, "file_url", "") or "").strip()
	if not file_url or file_url.startswith("http"):
		return  # skip external URLs or empty
	try:
		image_field = _core_item_image_field()
		current_image = frappe.db.get_value("Item", attached_to_name, image_field) or ""
		if not current_image:
			frappe.db.set_value("Item", attached_to_name, image_field, file_url, update_modified=False)
			print(f"FILE HOOK: Set image for {attached_to_name} to {file_url}")
	except Exception as e:
		print(f"FILE HOOK ERROR: {e}")


def _core_item_filters(branch=None):
	filters = {
		"disabled": 0,
		"restaurant_enabled": 1,
	}
	if _has_column("Item", "variant_of"):
		filters["variant_of"] = ["in", ["", None]]
	if branch and _has_column("Item", "restaurant_branch"):
		filters["restaurant_branch"] = ["in", [branch, ""]]
	return filters


def _core_category_filters(is_subcategory=0):
	filters = {
		"restaurant_is_menu_category": 1,
		"restaurant_is_subcategory": cint(is_subcategory),
	}
	if _has_column("Item Group", "restaurant_active"):
		filters["restaurant_active"] = 1
	return filters


def _ensure_item_group_homepage_field():
	"""Ensure show_on_homepage custom field exists on Item Group"""
	fieldname = "show_on_homepage"
	if _has_column("Item Group", fieldname):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item Group",
				"fieldname": fieldname,
				"label": "نمایش در صفحه اصلی",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "restaurant_active",
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Item Group")
	except Exception:
		pass


def _ensure_item_group_menu_icon_field():
	"""Ensure restaurant_menu_icon custom field exists on Item Group."""
	fieldname = "restaurant_menu_icon"
	if _has_column("Item Group", fieldname):
		return True
	try:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Item Group", "fieldname": fieldname},
			"name",
		)
		if not existing_name:
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": "Item Group",
					"module": "Restaurant",
					"fieldname": fieldname,
					"label": "آیکون منو",
					"fieldtype": "Data",
					"description": "نام آیکون Lucide برای نمایش گروه در صفحه منو",
					"insert_after": "image",
				}
			).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Item Group")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.ensure_item_group_menu_icon_field")
	return _has_column("Item Group", fieldname)


@frappe.whitelist()
def setup_menu_group_icon_field():
	_ensure_management_access()
	created = _ensure_item_group_menu_icon_field()
	frappe.db.commit()
	return {"ok": True, "ready": bool(created)}


def _ensure_item_tags_field():
	"""Ensure restaurant_item_tags custom field exists on Item"""
	fieldname = "restaurant_item_tags"
	if _has_column("Item", fieldname):
		return
	try:
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"fieldname": fieldname,
				"label": "تگ‌های محصول",
				"fieldtype": "Small Text",
				"description": "تگ‌ها را با کاما جدا کنید. مثال: رژیمی, پرفروش, وگان",
				"insert_after": "restaurant_allergen_tags",
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Item")
	except Exception:
		pass
	if _has_column("Item", "item_image"):
		return "item_image"
	return "image"


def _bom_item_show_fieldname():
	if _has_column("BOM Item", "show_in_website"):
		return "show_in_website"
	if _has_column("BOM Item", "show_in_print"):
		return "show_in_print"
	return ""


def _bom_item_show_value(row, default=1):
	raw = None
	if isinstance(row, dict):
		raw = row.get("show_in_website")
		if raw in (None, ""):
			raw = row.get("show_in_print")
	else:
		getter = getattr(row, "get", None)
		if callable(getter):
			raw = getter("show_in_website")
			if raw in (None, ""):
				raw = getter("show_in_print")
		if raw in (None, ""):
			raw = getattr(row, "show_in_website", None)
			if raw in (None, ""):
				raw = getattr(row, "show_in_print", None)
	if raw in (None, ""):
		return cint(default)
	return cint(raw)


def _get_core_category_meta_map():
	rows = frappe.get_all(
		"Item Group",
		filters=_core_category_filters(is_subcategory=0),
		fields=["name", "item_group_name", "restaurant_slug"],
		ignore_permissions=True,
	)
	return {
		row.name: {
			"title": row.item_group_name,
			"slug": row.restaurant_slug,
		}
		for row in rows
	}


def _get_core_subcategory_meta_map():
	rows = frappe.get_all(
		"Item Group",
		filters=_core_category_filters(is_subcategory=1),
		fields=["name", "item_group_name", "restaurant_slug", "parent_item_group", "restaurant_sort_order"],
		ignore_permissions=True,
	)
	return {
		row.name: {
			"title": row.item_group_name,
			"slug": row.restaurant_slug,
			"category": row.parent_item_group,
			"sort_order": cint(row.restaurant_sort_order),
		}
		for row in rows
	}


def _get_default_item_price_rate(row, price_list=None):
	price_list = (price_list or _get_default_selling_price_list_name() or "").strip()
	if not price_list:
		return None

	candidates = []
	for value in (row.get("name"), row.get("item_code")):
		normalized = (value or "").strip()
		if normalized and normalized not in candidates:
			candidates.append(normalized)

	for item_code in candidates:
		rate = frappe.db.get_value(
			"Item Price",
			{
				"item_code": item_code,
				"price_list": price_list,
				"selling": 1,
			},
			"price_list_rate",
		)
		if rate not in (None, ""):
			return flt(rate)
	return None


def _resolve_default_selling_item_pricing(item_code, qty, uom=None, price_list=None):
	item_code = (item_code or "").strip()
	source_uom = (uom or "").strip()
	requested_qty = flt(qty or 0)
	default_price_list = (price_list or _default_selling_price_list() or "").strip()
	payload = {
		"item_code": item_code,
		"price_list": default_price_list,
		"source_uom": source_uom,
		"stock_uom": "",
		"qty": requested_qty,
		"qty_in_stock_uom": 0.0,
		"conversion_factor": 1.0,
		"unit_rate": 0.0,
		"total_price": 0.0,
		"price_status": "ok",
		"is_selectable": 1,
		"disabled": 0,
		"item_disabled": 0,
		"availability_status": "available",
		"unavailable_reason": "",
	}

	if not item_code:
		payload.update(
			{
				"price_status": "missing_item",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_item",
				"unavailable_reason": _("No pricing item is linked."),
			}
		)
		return payload

	if not frappe.db.exists("Item", item_code):
		payload.update(
			{
				"price_status": "missing_item",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_item",
				"unavailable_reason": _("Item not found: {0}").format(item_code),
			}
		)
		return payload

	item_meta = frappe.db.get_value("Item", item_code, ["stock_uom", "disabled"], as_dict=True) or {}
	payload["stock_uom"] = (item_meta.get("stock_uom") or "").strip()
	if not payload["source_uom"]:
		payload["source_uom"] = payload["stock_uom"]

	if _has_column("Item", "disabled") and cint(item_meta.get("disabled") or 0) == 1:
		payload.update(
			{
				"price_status": "inactive",
				"is_selectable": 0,
				"disabled": 1,
				"item_disabled": 1,
				"availability_status": "inactive",
				"unavailable_reason": _("Linked item is disabled in ERPNext."),
			}
		)
		return payload

	conversion = _item_uom_conversion_details_to_stock(item_code, payload["source_uom"])
	payload["stock_uom"] = (conversion.get("stock_uom") or payload["stock_uom"] or "").strip()
	payload["source_uom"] = (conversion.get("source_uom") or payload["source_uom"] or "").strip()
	payload["conversion_factor"] = flt(conversion.get("factor") or 0)
	if not cint(conversion.get("has_conversion")) or flt(payload["conversion_factor"]) <= 0:
		payload.update(
			{
				"price_status": "missing_conversion",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_conversion",
				"unavailable_reason": _("No valid UOM conversion found for {0} to {1}.").format(
					payload["source_uom"] or _("selected UOM"),
					payload["stock_uom"] or _("stock UOM"),
				),
			}
		)
		return payload

	payload["qty_in_stock_uom"] = flt(requested_qty * payload["conversion_factor"])
	if payload["qty_in_stock_uom"] < 0:
		payload["qty_in_stock_uom"] = 0

	if not default_price_list:
		payload.update(
			{
				"price_status": "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_price",
				"unavailable_reason": _("No default selling price list is configured."),
			}
		)
		return payload

	rate = _get_default_item_price_rate({"item_code": item_code}, price_list=default_price_list)
	if rate in (None, ""):
		payload.update(
			{
				"price_status": "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_price",
				"unavailable_reason": _("No Item Price found for {0} in {1}.").format(
					item_code,
					default_price_list,
				),
			}
		)
		return payload

	payload["unit_rate"] = flt(rate)
	payload["total_price"] = flt(payload["unit_rate"] * flt(payload["qty_in_stock_uom"] or 0))
	return payload


def _resolve_ingredient_alternative_pricing(
	base_item_code,
	base_qty,
	base_uom,
	alternative_item_code,
	alternative_qty,
	alternative_uom=None,
	price_list=None,
):
	base_pricing = _resolve_default_selling_item_pricing(
		base_item_code,
		base_qty,
		uom=base_uom,
		price_list=price_list,
	)
	alternative_pricing = _resolve_default_selling_item_pricing(
		alternative_item_code,
		alternative_qty,
		uom=alternative_uom,
		price_list=price_list,
	)

	payload = {
		"price_delta": 0.0,
		"resolved_price_delta": 0.0,
		"price_status": "ok",
		"price_list": alternative_pricing.get("price_list") or base_pricing.get("price_list") or "",
		"price_source": "item_price",
		"price_item_code": (alternative_item_code or "").strip(),
		"is_selectable": 1,
		"disabled": 0,
		"item_disabled": cint(alternative_pricing.get("item_disabled") or 0),
		"unavailable_reason": "",
		"availability_status": "available",
		"conversion_factor": flt(alternative_pricing.get("conversion_factor") or 1) or 1,
		"unit_rate": flt(alternative_pricing.get("unit_rate") or 0),
		"base_price": flt(alternative_pricing.get("total_price") or 0),
		"alternative_price": flt(alternative_pricing.get("total_price") or 0),
		"comparison_base_item_code": (base_item_code or "").strip(),
		"comparison_base_unit_rate": flt(base_pricing.get("unit_rate") or 0),
		"comparison_base_price": flt(base_pricing.get("total_price") or 0),
		"alternative_qty_in_stock_uom": flt(alternative_pricing.get("qty_in_stock_uom") or 0),
		"base_qty_in_stock_uom": flt(base_pricing.get("qty_in_stock_uom") or 0),
	}

	if cint(base_pricing.get("is_selectable") or 0) != 1:
		payload.update(
			{
				"price_status": base_pricing.get("price_status") or "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": base_pricing.get("availability_status") or "missing_price",
				"unavailable_reason": base_pricing.get("unavailable_reason")
				or _("Base ingredient price could not be resolved."),
			}
		)
		return payload

	if cint(alternative_pricing.get("is_selectable") or 0) != 1:
		payload.update(
			{
				"price_status": alternative_pricing.get("price_status") or "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"item_disabled": cint(alternative_pricing.get("item_disabled") or 0),
				"availability_status": alternative_pricing.get("availability_status") or "missing_price",
				"unavailable_reason": alternative_pricing.get("unavailable_reason")
				or _("Alternative item price could not be resolved."),
			}
		)
		return payload

	delta = flt(alternative_pricing.get("total_price") or 0) - flt(base_pricing.get("total_price") or 0)
	payload["price_delta"] = delta
	payload["resolved_price_delta"] = delta
	return payload


def _resolve_modifier_option_pricing(option_row=None, price_list=None):
	option_row = option_row or {}
	action_type = (
		option_row.get("action_type") or option_row.get("modifier_type") or "add_on"
	).strip() or "add_on"
	option_item_code = (option_row.get("option_item") or "").strip()
	legacy_price_delta = flt(option_row.get("price_delta") or 0)
	active_value = option_row.get("is_active")
	is_active = 1 if active_value in (None, "") else cint(active_value)
	default_price_list = (price_list or _default_selling_price_list() or "").strip()
	qty_rules = _normalize_modifier_option_quantity_rules(option_row)
	base_qty = flt(qty_rules.get("option_qty") or 1)

	payload = {
		"price_delta": 0.0,
		"resolved_price_delta": 0.0,
		"price_status": "ok",
		"price_list": default_price_list,
		"price_source": "item_price",
		"price_item_code": option_item_code,
		"is_selectable": 1,
		"disabled": 0,
		"item_disabled": 0,
		"unavailable_reason": "",
		"availability_status": "available",
		"stock_uom": "",
		"option_uom": (option_row.get("option_uom") or "").strip(),
		"base_qty": base_qty,
		"conversion_factor": 1.0,
		"unit_rate": 0.0,
		"base_price": 0.0,
		"base_qty_in_stock_uom": base_qty,
	}

	if not is_active:
		payload.update(
			{
				"price_status": "inactive",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "inactive",
				"unavailable_reason": _("This modifier is inactive."),
			}
		)
		return payload

	if not option_item_code:
		if action_type == "bom_variant":
			return payload
		if action_type == "add_on":
			payload.update(
				{
					"price_status": "ok",
					"price_source": "manual",
					"price_item_code": "",
					"unit_rate": flt(legacy_price_delta / base_qty) if base_qty > 1e-8 else flt(legacy_price_delta),
					"base_price": flt(legacy_price_delta),
					"price_delta": flt(legacy_price_delta),
					"resolved_price_delta": flt(legacy_price_delta),
				}
			)
			return payload
		payload.update(
			{
				"price_status": "missing_item",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_item",
				"unavailable_reason": _("No pricing item is linked to this modifier."),
			}
		)
		return payload

	if not frappe.db.exists("Item", option_item_code):
		payload.update(
			{
				"price_status": "missing_item",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_item",
				"unavailable_reason": _("Modifier pricing item not found: {0}").format(option_item_code),
			}
		)
		return payload

	item_meta = frappe.db.get_value(
		"Item",
		option_item_code,
		["stock_uom", "disabled"],
		as_dict=True,
	) or {}
	payload["stock_uom"] = (item_meta.get("stock_uom") or "").strip()
	if not payload["option_uom"]:
		payload["option_uom"] = payload["stock_uom"]

	if _has_column("Item", "disabled") and cint(item_meta.get("disabled") or 0) == 1:
		payload.update(
			{
				"price_status": "inactive",
				"is_selectable": 0,
				"disabled": 1,
				"item_disabled": 1,
				"availability_status": "inactive",
				"unavailable_reason": _("Linked modifier item is disabled in ERPNext."),
			}
		)
		return payload

	if action_type == "add_on":
		conversion = _item_uom_conversion_details_to_stock(option_item_code, payload["option_uom"])
		payload["stock_uom"] = (conversion.get("stock_uom") or payload["stock_uom"] or "").strip()
		payload["option_uom"] = (conversion.get("source_uom") or payload["option_uom"] or "").strip()
		payload["conversion_factor"] = flt(conversion.get("factor") or 0)
		if not cint(conversion.get("has_conversion")) or flt(payload["conversion_factor"]) <= 0:
			payload.update(
				{
					"price_status": "missing_conversion",
					"is_selectable": 0,
					"disabled": 1,
					"availability_status": "missing_conversion",
					"unavailable_reason": _("No valid UOM conversion found for {0} to {1}.").format(
						payload["option_uom"] or _("selected UOM"),
						payload["stock_uom"] or _("stock UOM"),
					),
				}
			)
			return payload
		payload["base_qty_in_stock_uom"] = flt(base_qty * payload["conversion_factor"])

	if not default_price_list:
		payload.update(
			{
				"price_status": "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_price",
				"unavailable_reason": _("No default selling price list is configured."),
			}
		)
		return payload

	rate = _get_default_item_price_rate({"item_code": option_item_code}, price_list=default_price_list)
	if rate in (None, ""):
		payload.update(
			{
				"price_status": "missing_price",
				"is_selectable": 0,
				"disabled": 1,
				"availability_status": "missing_price",
				"unavailable_reason": _("No Item Price found for {0} in {1}.").format(
					option_item_code,
					default_price_list,
				),
			}
		)
		return payload

	payload["unit_rate"] = flt(rate)
	payload["base_price"] = flt(payload["unit_rate"] * flt(payload.get("base_qty_in_stock_uom") or 0))
	payload["price_delta"] = flt(payload["base_price"])
	payload["resolved_price_delta"] = flt(payload["base_price"])
	return payload


def _serialize_core_item(row, category_meta_map=None, subcategory_meta_map=None):
	category_meta_map = category_meta_map or {}
	subcategory_meta_map = subcategory_meta_map or {}
	category_meta = category_meta_map.get(row.restaurant_category, {})
	subcategory_meta = subcategory_meta_map.get(row.restaurant_subcategory, {})
	item_price = _get_default_item_price_rate(row)
	base_price = (
		item_price if item_price is not None else (flt(row.restaurant_base_price) or flt(row.standard_rate))
	)
	nutrition = _nutrition_payload(row)

	return {
		"name": row.name,
		"slug": row.restaurant_slug,
		"title": row.item_name,
		"short_desc": row.restaurant_short_desc,
		"base_price": base_price,
		"image": row.image,
		"category": row.restaurant_category,
		"category_title": category_meta.get("title"),
		"category_slug": category_meta.get("slug"),
		"subcategory": row.restaurant_subcategory,
		"subcategory_title": subcategory_meta.get("title"),
		"subcategory_slug": subcategory_meta.get("slug"),
		"sort_order": cint(row.get("restaurant_sort_order") or 0),
		"restaurant_sort_order": cint(row.get("restaurant_sort_order") or 0),
		"nutrition": nutrition,
		"nutrition_kcal": nutrition.get("kcal"),
		"nutrition_protein_g": nutrition.get("protein_g"),
		"nutrition_carb_g": nutrition.get("carb_g"),
		"nutrition_sugar_g": nutrition.get("sugar_g"),
		"nutrition_fat_g": nutrition.get("fat_g"),
		"nutrition_protein_percent": nutrition.get("protein_percent"),
		"has_customization": cint(row.get("has_customization") or 0),
		"has_bom": cint(row.get("has_bom") or 0),
		"restaurant_is_customizable": cint(row.get("restaurant_is_customizable") or 0),
		"restaurant_builder_active": cint(row.get("restaurant_builder_active") or 0),
		"restaurant_builder_template": row.get("restaurant_builder_template") or "",
		"restaurant_customize_button_label": row.get("restaurant_customize_button_label") or "",
		"restaurant_allow_direct_add": cint(row.get("restaurant_allow_direct_add") or 0),
		"tags": _split_tags(getattr(row, "restaurant_item_tags", None))
		or _get_item_tag_titles(getattr(row, "name", None)),
		"coming_soon": cint(getattr(row, "restaurant_coming_soon", 0)),
	}


def _count_core_menu_items(filters=None, or_filters=None):
	if not or_filters:
		return frappe.db.count("Item", filters=filters)

	template_rows = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=["count(name) as total"],
		ignore_permissions=True,
		limit_page_length=1,
	)
	if not template_rows:
		return 0
	return cint(template_rows[0].get("total") or 0)


def _get_items_with_bom(item_names):
	"""Return a dict of {item_name: True} for items that have an active BOM."""
	names = [n for n in (item_names or []) if n]
	if not names:
		return {}
	bom_rows = frappe.get_all(
		"BOM",
		filters={
			"item": ["in", names],
			"is_active": 1,
			"docstatus": ["!=", 2],
		},
		fields=["item"],
		ignore_permissions=True,
		limit_page_length=5000,
	)
	result = {}
	for row in bom_rows or []:
		item_code = (row.get("item") or "").strip()
		if item_code and item_code not in result:
			result[item_code] = True
	return result


def _menu_item_customization_flags(item_names=None):
	names = []
	for value in item_names or []:
		name = (value or "").strip()
		if name and name not in names:
			names.append(name)
	if not names:
		return {}

	bom_rows = frappe.get_all(
		"BOM",
		filters={
			"item": ["in", names],
			"is_active": 1,
			"docstatus": ["!=", 2],
		},
		fields=["name", "item", "is_default", "docstatus", "modified"],
		order_by="item asc, is_default desc, docstatus desc, modified desc",
		ignore_permissions=True,
		limit_page_length=5000,
	)

	item_bom_map = {}
	for row in bom_rows or []:
		item_code = (row.get("item") or "").strip()
		bom_name = (row.get("name") or "").strip()
		if not item_code or not bom_name or item_code in item_bom_map:
			continue
		item_bom_map[item_code] = bom_name

	bom_names = [value for value in item_bom_map.values() if value]
	if not bom_names:
		return {name: 0 for name in names}

	bom_has_modifier_map = {}
	if frappe.db.exists("DocType", "Restaurant BOM Modifier"):
		modifier_rows = frappe.get_all(
			"Restaurant BOM Modifier",
			filters={"parent": ["in", bom_names]},
			fields=["parent"],
			ignore_permissions=True,
			limit_page_length=5000,
		)
		for row in modifier_rows or []:
			parent = (row.get("parent") or "").strip()
			if parent:
				bom_has_modifier_map[parent] = 1

	bom_has_visible_ingredient_map = {}
	bom_item_fields = ["parent"]
	bom_item_show_field = _bom_item_show_fieldname()
	if bom_item_show_field:
		bom_item_fields.append(bom_item_show_field)
	ingredient_rows = frappe.get_all(
		"BOM Item",
		filters={"parent": ["in", bom_names]},
		fields=bom_item_fields,
		ignore_permissions=True,
		limit_page_length=10000,
	)
	for row in ingredient_rows or []:
		parent = (row.get("parent") or "").strip()
		if not parent:
			continue
		show_on_website = bool(_bom_item_show_value(row, default=1))
		if show_on_website:
			bom_has_visible_ingredient_map[parent] = 1

	flags = {}
	for item_name in names:
		bom_name = item_bom_map.get(item_name)
		if not bom_name:
			flags[item_name] = 0
			continue
		flags[item_name] = (
			1 if (bom_has_modifier_map.get(bom_name) or bom_has_visible_ingredient_map.get(bom_name)) else 0
		)
	return flags


def _ensure_display_variant_setting_fields():
	if not frappe.db.exists("DocType", "Restaurant Web Settings"):
		return
	field_defs = [
		{
			"fieldname": "card_variant",
			"label": "Card Variant",
			"fieldtype": "Data",
			"default": "classic",
			"insert_after": "hero_section_variant",
		},
		{
			"fieldname": "hero_image_position",
			"label": "Hero Image Position",
			"fieldtype": "Data",
			"default": "center",
			"insert_after": "card_variant",
		},
		{
			"fieldname": "category_rail_variant",
			"label": "Category Rail Variant",
			"fieldtype": "Data",
			"default": "pill",
			"insert_after": "hero_image_position",
		},
	]
	for field_def in field_defs:
		try:
			if _has_doctype_field("Restaurant Web Settings", field_def["fieldname"]):
				existing = frappe.db.get_value(
					"Custom Field",
					{"dt": "Restaurant Web Settings", "fieldname": field_def["fieldname"]},
					"name",
				)
				if not existing:
					continue
				doc = frappe.get_doc("Custom Field", existing)
				changed = False
				for key, value in field_def.items():
					if doc.get(key) != value:
						doc.set(key, value)
						changed = True
				if changed:
					doc.save(ignore_permissions=True)
			else:
				payload = {
					"doctype": "Custom Field",
					"dt": "Restaurant Web Settings",
					**field_def,
				}
				frappe.get_doc(payload).insert(ignore_permissions=True)
		except Exception:
			pass
	try:
		frappe.clear_cache(doctype="Restaurant Web Settings")
	except Exception:
		pass


def _ensure_menu_highlight_setting_fields():
	if frappe.db.exists("DocType", "Restaurant Web Settings"):
		settings_field_defs = [
			{
				"fieldname": "restaurant_menu_highlight_section",
				"label": "بلاک ویژه منو",
				"fieldtype": "Section Break",
				"insert_after": "primary_cta_label",
			},
			{
				"fieldname": "restaurant_menu_highlight_enabled",
				"label": "نمایش بلاک ویژه در منو",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "restaurant_menu_highlight_section",
			},
			{
				"fieldname": "restaurant_menu_highlight_title",
				"label": "عنوان بلاک ویژه",
				"fieldtype": "Data",
				"default": "ویژه و پرفروش",
				"insert_after": "restaurant_menu_highlight_enabled",
			},
			{
				"fieldname": "restaurant_menu_highlight_show_featured",
				"label": "نمایش آیتم های ویژه",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "restaurant_menu_highlight_title",
			},
			{
				"fieldname": "restaurant_menu_highlight_featured_limit",
				"label": "تعداد آیتم ویژه",
				"fieldtype": "Int",
				"default": "10",
				"insert_after": "restaurant_menu_highlight_show_featured",
			},
			{
				"fieldname": "restaurant_menu_highlight_show_best_seller",
				"label": "نمایش آیتم های پرفروش",
				"fieldtype": "Check",
				"default": "1",
				"insert_after": "restaurant_menu_highlight_featured_limit",
			},
			{
				"fieldname": "restaurant_menu_highlight_best_seller_limit",
				"label": "تعداد آیتم پرفروش",
				"fieldtype": "Int",
				"default": "10",
				"insert_after": "restaurant_menu_highlight_show_best_seller",
			},
		]

		for field_def in settings_field_defs:
			try:
				if _has_doctype_field("Restaurant Web Settings", field_def["fieldname"]):
					existing_name = frappe.db.get_value(
						"Custom Field",
						{"dt": "Restaurant Web Settings", "fieldname": field_def["fieldname"]},
						"name",
					)
					if not existing_name:
						continue
					doc = frappe.get_doc("Custom Field", existing_name)
					changed = False
					for key, value in field_def.items():
						if doc.get(key) != value:
							doc.set(key, value)
							changed = True
					if changed:
						doc.save(ignore_permissions=True)
				else:
					payload = {
						"doctype": "Custom Field",
						"dt": "Restaurant Web Settings",
						**field_def,
					}
					frappe.get_doc(payload).insert(ignore_permissions=True)
			except Exception:
				pass

		try:
			frappe.clear_cache(doctype="Restaurant Web Settings")
		except Exception:
			pass

	if frappe.db.exists("DocType", "Item"):
		item_field_def = {
			"fieldname": "restaurant_is_best_seller",
			"label": "Restaurant Is Best Seller",
			"fieldtype": "Check",
			"default": "0",
			"insert_after": "restaurant_is_featured",
		}
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Item", "fieldname": item_field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Item",
			"module": "Restaurant",
			**item_field_def,
		}
		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			changed = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					changed = True
			if changed:
				doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(payload).insert(ignore_permissions=True)

		frappe.clear_cache(doctype="Item")


def _menu_highlight_settings():
	title = (
		_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_title", "ویژه و پرفروش")
		or "ویژه و پرفروش"
	).strip()
	if not title:
		title = "ویژه و پرفروش"

	enabled = (
		cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_enabled", 1)) == 1
	)
	show_featured = (
		cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_show_featured", 1))
		== 1
	)
	show_best_seller = (
		cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_show_best_seller", 1))
		== 1
	)

	featured_limit = max(
		min(
			cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_featured_limit", 10)
			),
			50,
		),
		0,
	)
	best_seller_limit = max(
		min(
			cint(
				_get_single_setting(
					"Restaurant Web Settings", "restaurant_menu_highlight_best_seller_limit", 10
				)
			),
			50,
		),
		0,
	)

	return {
		"enabled": enabled,
		"title": title,
		"show_featured": show_featured,
		"show_best_seller": show_best_seller,
		"featured_limit": featured_limit,
		"best_seller_limit": best_seller_limit,
	}


def _sort_menu_display_rows(rows):
	return sorted(
		rows or [],
		key=lambda row: (
			cint(row.get("restaurant_sort_order") or 0),
			_variant_item_sort_key(row.get("name") or ""),
			(row.get("item_name") or ""),
		),
	)


def _apply_menu_customization_flags(rows):
	item_names = []
	for row in rows or []:
		name = (row.get("name") or "").strip()
		if name and name not in item_names:
			item_names.append(name)
		variant_of = (row.get("variant_of") or "").strip()
		if variant_of and variant_of not in item_names:
			item_names.append(variant_of)

	flags = _menu_item_customization_flags(item_names)
	bom_item_map = _get_items_with_bom(item_names)
	out = []
	for row in rows or []:
		payload = frappe._dict(dict(row))
		item_name = (payload.get("name") or "").strip()
		variant_of = (payload.get("variant_of") or "").strip()
		payload["has_customization"] = (
			1 if (flags.get(item_name) or (variant_of and flags.get(variant_of))) else 0
		)
		payload["has_bom"] = (
			1 if (bom_item_map.get(item_name) or (variant_of and bom_item_map.get(variant_of))) else 0
		)
		builder_source_name = item_name
		if variant_of and not cint(payload.get("restaurant_is_customizable") or 0):
			builder_source_name = variant_of
		if builder_source_name:
			builder_flags = (
				frappe.db.get_value(
					"Item",
					builder_source_name,
					[
						"restaurant_is_customizable",
						"restaurant_builder_active",
						"restaurant_builder_template",
						"restaurant_customize_button_label",
						"restaurant_allow_direct_add",
					],
					as_dict=True,
				)
				or {}
			)
			payload["restaurant_is_customizable"] = cint(builder_flags.get("restaurant_is_customizable") or 0)
			payload["restaurant_builder_active"] = cint(builder_flags.get("restaurant_builder_active") or 0)
			payload["restaurant_builder_template"] = builder_flags.get("restaurant_builder_template") or ""
			payload["restaurant_customize_button_label"] = (
				builder_flags.get("restaurant_customize_button_label") or ""
			)
			payload["restaurant_allow_direct_add"] = cint(
				builder_flags.get("restaurant_allow_direct_add") or 0
			)
		out.append(payload)
	return out


def _get_core_menu_boot(branch=None):
	image_field = _core_item_image_field()
	category_meta_map = _get_core_category_meta_map()
	subcategory_meta_map = _get_core_subcategory_meta_map()
	nutrition_fields = _available_item_nutrition_fields()

	_ensure_item_group_homepage_field()
	_ensure_item_group_menu_icon_field()
	_ensure_item_tags_field()

	category_fields = [
		"name",
		"item_group_name as title",
		"restaurant_slug as slug",
		"restaurant_description as description",
		"image",
		"restaurant_sort_order as sort_order",
		"show_on_homepage",
	]
	if _has_column("Item Group", "restaurant_menu_icon"):
		category_fields.append("restaurant_menu_icon as menu_icon")

	categories = frappe.get_all(
		"Item Group",
		filters=_core_category_filters(is_subcategory=0),
		fields=category_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_group_name asc",
	)

	# Filter out categories that have show_on_homepage = 0
	if _has_column("Item Group", "show_on_homepage"):
		categories = [c for c in categories if c.get("show_on_homepage") != 0]

	category_item_fields = [
		"name",
		"item_code",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		f"{image_field} as image",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_sort_order",
		"restaurant_item_tags",
	]
	for fieldname in nutrition_fields:
		if fieldname not in category_item_fields:
			category_item_fields.append(fieldname)

	category_template_items = frappe.get_all(
		"Item",
		filters=_core_item_filters(branch),
		fields=category_item_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit_page_length=5000,
	)
	expanded_items = []
	for row in category_template_items:
		expanded_items.extend(_template_display_row_or_self(row, branch=branch))
	expanded_items = _apply_menu_customization_flags(expanded_items)

	category_count_map = defaultdict(int)
	subcategory_count_map = defaultdict(int)
	for row in expanded_items:
		category_count_map[row.get("restaurant_category") or ""] += 1
		subcategory_count_map[row.get("restaurant_subcategory") or ""] += 1

	for category in categories:
		category["item_count"] = cint(category_count_map.get(category.name) or 0)
		category["subcategories"] = []

	category_index = {row["name"]: row for row in categories}
	for sub_name, sub_meta in subcategory_meta_map.items():
		parent = category_index.get(sub_meta.get("category"))
		if not parent:
			continue
		sub_payload = {
			"name": sub_name,
			"title": sub_meta.get("title"),
			"slug": sub_meta.get("slug"),
			"sort_order": sub_meta.get("sort_order", 0),
			"item_count": cint(subcategory_count_map.get(sub_name) or 0),
		}
		parent["subcategories"].append(sub_payload)

	for category in categories:
		category["subcategories"] = sorted(
			category.get("subcategories") or [],
			key=lambda row: (cint(row.get("sort_order", 0)), row.get("title") or ""),
		)

	featured_item_fields = [
		"name",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		f"{image_field} as image",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_sort_order",
	]
	for fieldname in nutrition_fields:
		if fieldname not in featured_item_fields:
			featured_item_fields.append(fieldname)

	menu_highlight = _menu_highlight_settings()

	featured_template_items = frappe.get_all(
		"Item",
		filters={
			**_core_item_filters(branch),
			"restaurant_is_featured": 1,
		},
		fields=featured_item_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit_page_length=500,
	)
	featured_rows = []
	for row in featured_template_items:
		featured_rows.extend(_template_display_row_or_self(row, branch=branch))
	featured_rows = _apply_menu_customization_flags(featured_rows)
	featured_rows_sorted = _sort_menu_display_rows(featured_rows)
	featured_rows = featured_rows_sorted[:8]

	highlight_map = {}
	highlight_map_by_category = {}
	per_category_limit = 3

	def _resolve_highlight_category_slug(raw_row):
		category_name = (raw_row.get("restaurant_category") or "").strip()
		category_meta = category_meta_map.get(category_name, {})
		category_slug = _normalize_slug(category_meta.get("slug") or "")
		if category_slug:
			return category_slug

		category_title = (category_meta.get("title") or category_name).strip()
		return _normalize_slug(_public_menu_slugify(category_title))

	def _append_highlight_rows(raw_rows, tag):
		if not raw_rows:
			return

		for raw_row in raw_rows:
			category_slug = _resolve_highlight_category_slug(raw_row)
			if not category_slug:
				continue

			category_bucket = highlight_map_by_category.setdefault(category_slug, {})

			row_slug = (raw_row.get("restaurant_slug") or "").strip()
			row_name = (raw_row.get("name") or "").strip()
			row_key = row_slug or row_name
			if not row_key:
				continue

			payload = category_bucket.get(row_key)
			if not payload:
				if per_category_limit > 0 and len(category_bucket) >= per_category_limit:
					continue
				payload = _serialize_core_item(
					raw_row,
					category_meta_map=category_meta_map,
					subcategory_meta_map=subcategory_meta_map,
				)
				payload["menu_highlight_tags"] = []
				category_bucket[row_key] = payload
				highlight_map[row_key] = payload

			tags = payload.get("menu_highlight_tags") or []
			if tag and tag not in tags:
				tags.append(tag)
			payload["menu_highlight_tags"] = tags

	if menu_highlight.get("enabled"):
		if menu_highlight.get("show_featured"):
			_append_highlight_rows(
				featured_rows_sorted,
				"ویژه",
			)

		if menu_highlight.get("show_best_seller") and _has_column("Item", "restaurant_is_best_seller"):
			best_seller_template_items = frappe.get_all(
				"Item",
				filters={
					**_core_item_filters(branch),
					"restaurant_is_best_seller": 1,
				},
				fields=featured_item_fields,
				ignore_permissions=True,
				order_by="restaurant_sort_order asc, item_name asc",
				limit_page_length=500,
			)
			best_seller_rows = []
			for row in best_seller_template_items:
				best_seller_rows.extend(_template_display_row_or_self(row, branch=branch))
			best_seller_rows = _apply_menu_customization_flags(best_seller_rows)
			_append_highlight_rows(
				_sort_menu_display_rows(best_seller_rows),
				"پرفروش",
			)

	highlight_category_items = {}
	for category in categories:
		category_slug = _normalize_slug(category.get("slug") or "")
		if not category_slug:
			continue
		category_rows = highlight_map_by_category.get(category_slug, {})
		if category_rows:
			highlight_category_items[category_slug] = list(category_rows.values())

	for category_slug, rows_map in highlight_map_by_category.items():
		if category_slug in highlight_category_items:
			continue
		if rows_map:
			highlight_category_items[category_slug] = list(rows_map.values())

	return {
		"categories": categories,
		"subcategory_enabled": bool(subcategory_meta_map),
		"featured_items": [
			_serialize_core_item(
				row,
				category_meta_map=category_meta_map,
				subcategory_meta_map=subcategory_meta_map,
			)
			for row in featured_rows
		],
		"menu_highlight": {
			"enabled": 1 if menu_highlight.get("enabled") else 0,
			"title": menu_highlight.get("title") or "ویژه و پرفروش",
			"show_featured": 1 if menu_highlight.get("show_featured") else 0,
			"show_best_seller": 1 if menu_highlight.get("show_best_seller") else 0,
			"featured_limit": cint(menu_highlight.get("featured_limit") or 0),
			"best_seller_limit": cint(menu_highlight.get("best_seller_limit") or 0),
			"per_category_limit": per_category_limit,
			"category_items": highlight_category_items,
			"items": list(highlight_map.values()),
		},
		"hero_slides": _get_hero_slides(branch=branch),
		"about_us_sections": _get_about_us_sections(),
		"faq_items": _get_faq_items(),
		"currency": _get_currency(),
		"branding": _get_branding_payload(),
		"checkout_map": _get_checkout_map_settings(),
		"theme_settings": _load_management_theme_settings(),
		"loader_settings": _load_management_loader_settings(),
		"page_layout": _get_boot_page_layout_safe(branch),
		"user_roles": list(frappe.get_roles(frappe.session.user)) if frappe.session.user != "Guest" else [],
	}


def _get_boot_page_layout_safe(branch=None):
	"""Return per-company page layout map for boot. Never raises."""
	try:
		from restaurant.page_layout import get_boot_page_layout

		return get_boot_page_layout()
	except Exception:
		return {}


def _get_core_menu_items(
	category_slug=None, subcategory_slug=None, search=None, page=1, page_size=20, branch=None
):
	image_field = _core_item_image_field()
	nutrition_fields = _available_item_nutrition_fields()
	category_slug = _normalize_slug(category_slug)
	subcategory_slug = _normalize_slug(subcategory_slug)
	search = (search or "").strip()
	page = max(cint(page), 1)
	page_size = max(min(cint(page_size) or 20, MAX_PAGE_SIZE), 1)
	branch = (branch or "").strip()

	category_meta_map = _get_core_category_meta_map()
	subcategory_meta_map = _get_core_subcategory_meta_map()

	filters = _core_item_filters(branch)
	category_name = ""
	if category_slug:
		category_name = frappe.db.get_value(
			"Item Group",
			{
				"restaurant_slug": category_slug,
				**_core_category_filters(is_subcategory=0),
			},
			"name",
		)
		if not category_name:
			return {
				"items": [],
				"pagination": {
					"page": page,
					"page_size": page_size,
					"total": 0,
					"total_pages": 0,
				},
			}
		filters["restaurant_category"] = category_name

	if subcategory_slug:
		subcategory_filters = {
			"restaurant_slug": subcategory_slug,
			**_core_category_filters(is_subcategory=1),
		}
		if category_name:
			subcategory_filters["parent_item_group"] = category_name
		subcategory_name = frappe.db.get_value("Item Group", subcategory_filters, "name")
		if not subcategory_name:
			return {
				"items": [],
				"pagination": {
					"page": page,
					"page_size": page_size,
					"total": 0,
					"total_pages": 0,
				},
			}
		filters["restaurant_subcategory"] = subcategory_name

	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = [
			["item_name", "like", like],
			["restaurant_short_desc", "like", like],
			["restaurant_long_desc", "like", like],
		]

	start = (page - 1) * page_size

	item_fields = [
		"name",
		"item_code",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		f"{image_field} as image",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_sort_order",
	]
	for fieldname in nutrition_fields:
		if fieldname not in item_fields:
			item_fields.append(fieldname)
	if _has_column("Item", "restaurant_coming_soon"):
		item_fields.append("restaurant_coming_soon")

	template_rows = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=item_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit_page_length=5000,
	)

	expanded_rows = []
	for row in template_rows:
		expanded_rows.extend(_template_display_row_or_self(row, branch=branch))
	expanded_rows = _apply_menu_customization_flags(expanded_rows)

	if search:
		lowered = search.lower()
		filtered_rows = []
		for row in expanded_rows:
			haystack = " ".join(
				[
					str(row.get("item_name") or ""),
					str(row.get("restaurant_short_desc") or ""),
					str(row.get("restaurant_long_desc") or ""),
				]
			).lower()
			if lowered in haystack:
				filtered_rows.append(row)
		expanded_rows = filtered_rows

	expanded_rows = sorted(
		expanded_rows,
		key=lambda row: (
			cint(row.get("restaurant_sort_order") or 0),
			_variant_item_sort_key(row.get("name") or ""),
			(row.get("item_name") or ""),
		),
	)

	total = len(expanded_rows)
	paged_rows = expanded_rows[start : start + page_size]
	total_pages = (total + page_size - 1) // page_size if total else 0
	return {
		"items": [
			_serialize_core_item(
				row,
				category_meta_map=category_meta_map,
				subcategory_meta_map=subcategory_meta_map,
			)
			for row in paged_rows
		],
		"pagination": {
			"page": page,
			"page_size": page_size,
			"total": total,
			"total_pages": total_pages,
		},
	}


def _get_menu_items_public_fallback(
	category_slug=None, subcategory_slug=None, search=None, page=1, page_size=20, branch=None
):
	category_slug = _normalize_slug(category_slug)
	subcategory_slug = _normalize_slug(subcategory_slug)
	search = (search or "").strip().lower()
	page = max(cint(page), 1)
	page_size = max(min(cint(page_size) or 20, MAX_PAGE_SIZE), 1)
	branch = (branch or "").strip()

	has_restaurant_enabled = _has_column("Item", "restaurant_enabled")
	has_restaurant_branch = _has_column("Item", "restaurant_branch")
	has_restaurant_category = _has_column("Item", "restaurant_category")
	has_restaurant_subcategory = _has_column("Item", "restaurant_subcategory")
	has_restaurant_slug = _has_column("Item", "restaurant_slug")
	has_restaurant_sort_order = _has_column("Item", "restaurant_sort_order")
	has_restaurant_short_desc = _has_column("Item", "restaurant_short_desc")
	has_restaurant_long_desc = _has_column("Item", "restaurant_long_desc")
	has_restaurant_base_price = _has_column("Item", "restaurant_base_price")
	has_variant_of = _has_column("Item", "variant_of")
	has_image = _has_column("Item", "image")
	has_item_image = _has_column("Item", "item_image")

	category_by_name = {}
	subcategory_by_name = {}
	category_slug_to_name = {}
	subcategory_slug_to_name = {}

	try:
		group_fields = ["name", "item_group_name", "parent_item_group"]
		if _has_column("Item Group", "restaurant_slug"):
			group_fields.append("restaurant_slug")
		if _has_column("Item Group", "restaurant_is_menu_category"):
			group_fields.append("restaurant_is_menu_category")
		if _has_column("Item Group", "restaurant_is_subcategory"):
			group_fields.append("restaurant_is_subcategory")
		if _has_column("Item Group", "restaurant_sort_order"):
			group_fields.append("restaurant_sort_order")

		group_rows = frappe.get_all(
			"Item Group",
			fields=group_fields,
			ignore_permissions=True,
			limit_page_length=4000,
		)

		for row in group_rows or []:
			name = (row.get("name") or "").strip()
			if not name:
				continue
			title = (row.get("item_group_name") or name).strip()
			slug = (row.get("restaurant_slug") or "").strip()
			fallback_slug = _public_menu_slugify(title or name)
			slug = slug or fallback_slug

			is_sub = cint(row.get("restaurant_is_subcategory") or 0) == 1
			is_cat = cint(row.get("restaurant_is_menu_category") or 0) == 1

			if not is_sub and (is_cat or not row.get("parent_item_group")):
				category_by_name[name] = {"title": title, "slug": slug}
				if slug:
					category_slug_to_name[slug] = name
			if is_sub or row.get("parent_item_group"):
				subcategory_by_name[name] = {
					"title": title,
					"slug": slug,
					"parent": (row.get("parent_item_group") or "").strip(),
				}
				if slug:
					subcategory_slug_to_name[slug] = name
	except Exception:
		pass

	filters = {"disabled": 0}
	if has_restaurant_enabled:
		filters["restaurant_enabled"] = 1
	if _has_column("Item", "restaurant_out_of_stock"):
		filters["restaurant_out_of_stock"] = ["!=", 1]
	if has_restaurant_branch and branch:
		filters["restaurant_branch"] = ["in", [branch, ""]]
	if has_variant_of:
		filters["variant_of"] = ["in", ["", None]]

	resolved_category_name = category_slug_to_name.get(category_slug) if category_slug else ""
	if category_slug and has_restaurant_category:
		if resolved_category_name:
			filters["restaurant_category"] = resolved_category_name
		else:
			return {
				"items": [],
				"pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0},
			}

	resolved_subcategory_name = subcategory_slug_to_name.get(subcategory_slug) if subcategory_slug else ""
	if subcategory_slug and has_restaurant_subcategory:
		if resolved_subcategory_name:
			filters["restaurant_subcategory"] = resolved_subcategory_name
		else:
			return {
				"items": [],
				"pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0},
			}

	fields = ["name", "item_code", "item_name", "item_group", "standard_rate", "disabled"]
	if has_restaurant_slug:
		fields.append("restaurant_slug")
	if has_restaurant_short_desc:
		fields.append("restaurant_short_desc")
	if has_restaurant_long_desc:
		fields.append("restaurant_long_desc")
	if has_restaurant_base_price:
		fields.append("restaurant_base_price")
	if has_restaurant_category:
		fields.append("restaurant_category")
	if has_restaurant_subcategory:
		fields.append("restaurant_subcategory")
	if has_restaurant_sort_order:
		fields.append("restaurant_sort_order")
	if has_image:
		fields.append("image")
	if has_item_image:
		fields.append("item_image")
	for fieldname in _available_item_nutrition_fields():
		if fieldname not in fields:
			fields.append(fieldname)

	rows = frappe.get_all(
		"Item",
		filters=filters,
		fields=fields,
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=8000,
	)

	payload_rows = []
	for row in rows or []:
		item_name = (row.get("item_name") or row.get("name") or "").strip()
		if not item_name:
			continue

		category_name = (row.get("restaurant_category") or row.get("item_group") or "").strip()
		subcategory_name = (row.get("restaurant_subcategory") or "").strip()

		category_meta = category_by_name.get(category_name, {})
		subcategory_meta = subcategory_by_name.get(subcategory_name, {})

		slug = (row.get("restaurant_slug") or "").strip() if has_restaurant_slug else ""
		if not slug:
			slug = _public_menu_slugify(item_name) or _public_menu_slugify(
				row.get("item_code") or row.get("name") or ""
			)

		short_desc = (row.get("restaurant_short_desc") or "").strip() if has_restaurant_short_desc else ""
		long_desc = (row.get("restaurant_long_desc") or "").strip() if has_restaurant_long_desc else ""
		if search:
			haystack = " ".join([item_name, short_desc, long_desc, slug]).lower()
			if search not in haystack:
				continue

		category_title = (category_meta.get("title") or category_name).strip()
		subcategory_title = (subcategory_meta.get("title") or subcategory_name).strip()

		if category_slug:
			normalized_category_slug = _normalize_slug(
				category_meta.get("slug") or _public_menu_slugify(category_title)
			)
			if normalized_category_slug != category_slug:
				continue
		if subcategory_slug:
			normalized_subcategory_slug = _normalize_slug(
				subcategory_meta.get("slug") or _public_menu_slugify(subcategory_title)
			)
			if normalized_subcategory_slug != subcategory_slug:
				continue

		nutrition = _nutrition_payload(row)
		payload_rows.append(
			{
				"name": row.get("name"),
				"slug": slug,
				"title": item_name,
				"short_desc": short_desc,
				"base_price": _get_default_item_price_rate(row) if _get_default_item_price_rate(row) is not None else flt(row.get("restaurant_base_price") or row.get("standard_rate") or 0),
				"image": (row.get("item_image") or row.get("image") or "").strip(),
				"category": category_name,
				"category_title": category_title,
				"category_slug": (category_meta.get("slug") or _public_menu_slugify(category_title)),
				"subcategory": subcategory_name,
				"subcategory_title": subcategory_title,
				"subcategory_slug": (subcategory_meta.get("slug") or _public_menu_slugify(subcategory_title)),
				"nutrition": nutrition,
				"nutrition_kcal": nutrition.get("kcal"),
				"nutrition_protein_g": nutrition.get("protein_g"),
				"nutrition_carb_g": nutrition.get("carb_g"),
				"nutrition_sugar_g": nutrition.get("sugar_g"),
				"nutrition_fat_g": nutrition.get("fat_g"),
				"nutrition_protein_percent": nutrition.get("protein_percent"),
				"has_customization": 0,
				"show_in_website": 1,
				"show_in_print": 1,
				"restaurant_sort_order": cint(row.get("restaurant_sort_order") or 0)
				if has_restaurant_sort_order
				else 0,
			}
		)

	payload_rows = sorted(
		payload_rows,
		key=lambda row: (
			cint(row.get("restaurant_sort_order") or 0),
			(row.get("category_title") or ""),
			(row.get("subcategory_title") or ""),
			(row.get("title") or ""),
		),
	)

	total = len(payload_rows)
	start = (page - 1) * page_size
	paged_rows = payload_rows[start : start + page_size]
	total_pages = (total + page_size - 1) // page_size if total else 0
	return {
		"items": paged_rows,
		"pagination": {
			"page": page,
			"page_size": page_size,
			"total": total,
			"total_pages": total_pages,
		},
	}


def _get_core_item_detail(item_slug, branch=None):
	slug = _normalize_slug(item_slug)
	if not slug:
		frappe.throw(_("Item slug is required."))
	branch = (branch or "").strip()

	item_name = frappe.db.get_value(
		"Item",
		{
			"restaurant_slug": slug,
			**_core_item_filters(branch),
		},
		"name",
	)
	source_variant_name = ""
	if not item_name:
		item_name, source_variant_name = _resolve_variant_slug_to_context(slug=slug, branch=branch)
	if not item_name:
		frappe.throw(_("Menu item not found."), frappe.DoesNotExistError)

	template_doc = frappe.get_doc("Item", item_name)
	# A direct request for a variant must still retain the parent template
	# context. The selected variant supplies the BOM/price, while the parent
	# supplies the variant selector groups so POS can switch between single
	# and double without falling back to the first/default recipe.
	variant_parent = (template_doc.get("variant_of") or "").strip()
	if variant_parent:
		source_variant_name = template_doc.name
		template_doc = frappe.get_doc("Item", variant_parent)
	doc, fixed_attribute_values = _resolve_display_doc_for_item_detail(
		template_doc,
		source_variant_name=source_variant_name,
		branch=branch,
	)
	modifier_groups, _group_map, _title_map = _build_modifier_groups(doc)

	if template_doc.name != doc.name:
		template_variants = frappe.get_all(
			"Item",
			filters={"variant_of": template_doc.name, "disabled": 0, "restaurant_enabled": 1},
			fields=["name"],
			ignore_permissions=True,
			limit_page_length=1000,
		)
	else:
		template_variants = []

	variant_groups = _variant_selection_groups(
		template_doc.name,
		template_variants,
		fixed_attribute_values=fixed_attribute_values,
	)
	if variant_groups:
		modifier_groups = [*variant_groups, *modifier_groups]

	ingredient_rows = _get_bom_ingredient_rows(doc)
	ingredient_codes = sorted(
		{(row.get("ingredient_item") or "").strip() for row in ingredient_rows if row.get("ingredient_item")}
	)
	ingredient_item_map = {}
	ingredient_image_field = ""
	nutrition_fields = _available_item_nutrition_fields()

	if ingredient_codes:
		ingredient_image_field = (
			"item_image"
			if _has_column("Item", "item_image")
			else "image"
			if _has_column("Item", "image")
			else ""
		)
		item_fields = ["name"]
		if ingredient_image_field:
			item_fields.append(ingredient_image_field)
		for _img_field in ("website_image", "image", "item_image"):
			if _img_field not in item_fields and _has_column("Item", _img_field):
				item_fields.append(_img_field)
		for fieldname in nutrition_fields:
			if _has_column("Item", fieldname):
				item_fields.append(fieldname)

		for row in frappe.get_all(
			"Item",
			filters={"name": ["in", ingredient_codes]},
			fields=item_fields,
			ignore_permissions=True,
		):
			ingredient_item_map[row.name] = row

	ingredients = []
	estimated_nutrition = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}

	for row in ingredient_rows:
		show_on_website_raw = row.get("show_in_website")
		show_on_website = True if show_on_website_raw in (None, "") else bool(cint(show_on_website_raw))

		base_qty = flt(row.get("base_qty") or 0)
		if base_qty <= 0:
			base_qty = 1 if cint(row.is_included_by_default) else 0.5
		min_multiplier = flt(row.get("min_multiplier"))
		max_multiplier = flt(row.get("max_multiplier") or 3)
		step_multiplier = flt(row.get("step_multiplier") or 0.5)
		multiplier_qty = flt(row.get("multiplier_qty") or 0)
		if multiplier_qty > 0 and base_qty > 0:
			step_multiplier = multiplier_qty / base_qty
		required = cint(row.get("is_required")) or (
			cint(row.is_included_by_default) and not cint(row.can_remove)
		)
		editable = cint(row.get("is_editable_qty"))
		if editable not in (0, 1):
			editable = 1
		if required and min_multiplier < 1:
			min_multiplier = 1

		ingredient_item = (row.get("ingredient_item") or "").strip()
		ingredient_item_doc = ingredient_item_map.get(ingredient_item, {})
		ingredient_nutrition = _nutrition_per_unit_payload(ingredient_item_doc)
		ingredient_image = row.get("image") or ""
		if not ingredient_image:
			ingredient_image = (
				ingredient_item_doc.get(ingredient_image_field) if ingredient_image_field else ""
			)
		if not ingredient_image:
			for _img_field in ("item_image", "website_image", "image"):
				_val = ingredient_item_doc.get(_img_field) or ""
				if _val:
					ingredient_image = _val
					break
		uom_factor = _nutrition_factor_from_item_qty(ingredient_item, base_qty, row.get("qty_uom"))
		_add_nutrition_to_totals(estimated_nutrition, ingredient_nutrition, uom_factor)

		if show_on_website:
			alternative_options = row.get("alternative_options") or []
			ingredients.append(
				{
					"name": row.ingredient_name,
					"key": row.ingredient_name,
					"customer_label": row.get("customer_label") or row.ingredient_name,
					"ingredient_item": ingredient_item,
					"qty_uom": row.get("qty_uom") or doc.stock_uom or "",
					"base_qty": base_qty,
					"is_included_by_default": cint(row.is_included_by_default),
					"can_remove": cint(row.can_remove),
					"is_required": required,
					"is_editable_qty": editable,
					"min_multiplier": min_multiplier,
					"max_multiplier": max(max_multiplier, min_multiplier),
					"step_multiplier": step_multiplier if step_multiplier > 0 else 0.5,
					"multiplier_qty": multiplier_qty if multiplier_qty > 0 else 0,
					"extra_when_added": flt(row.extra_when_added),
					"is_replaceable": 1 if (cint(row.get("is_replaceable")) or alternative_options) else 0,
					"alternative_options": alternative_options,
					"price_status": row.get("price_status") or "",
					"price_list": row.get("price_list") or "",
					"price_source": row.get("price_source") or "",
					"price_item_code": row.get("price_item_code") or ingredient_item,
					"unit_rate": flt(row.get("unit_rate") or 0),
					"base_price": flt(row.get("base_price") or 0),
					"conversion_factor": flt(row.get("conversion_factor") or 0),
					"source_uom": row.get("source_uom") or row.get("qty_uom") or doc.stock_uom or "",
					"stock_uom": row.get("stock_uom") or row.get("qty_uom") or doc.stock_uom or "",
					"qty_in_stock_uom": flt(row.get("qty_in_stock_uom") or 0),
					"is_selectable": cint(row.get("is_selectable") or 0),
					"availability_status": row.get("availability_status") or "",
					"unavailable_reason": row.get("unavailable_reason") or "",
					"image": ingredient_image or "",
					"nutrition_kcal": ingredient_nutrition.get("kcal"),
					"nutrition_protein_g": ingredient_nutrition.get("protein_g"),
					"nutrition_carb_g": ingredient_nutrition.get("carb_g"),
					"nutrition_sugar_g": ingredient_nutrition.get("sugar_g"),
					"nutrition_fat_g": ingredient_nutrition.get("fat_g"),
				}
			)

	category_slug = frappe.db.get_value("Item Group", doc.restaurant_category, "restaurant_slug")
	subcategory_slug = frappe.db.get_value("Item Group", doc.restaurant_subcategory, "restaurant_slug")
	image_field = _core_item_image_field()

	item_nutrition = _nutrition_payload(doc)
	estimated_payload = _nutrition_payload_from_totals(estimated_nutrition)
	if not item_nutrition.get("kcal") and estimated_payload["kcal"] > 0:
		item_nutrition["kcal"] = estimated_payload["kcal"]
	if not item_nutrition.get("protein_g") and estimated_payload["protein_g"] > 0:
		item_nutrition["protein_g"] = estimated_payload["protein_g"]
	if not item_nutrition.get("carb_g") and estimated_payload["carb_g"] > 0:
		item_nutrition["carb_g"] = estimated_payload["carb_g"]
	if not item_nutrition.get("sugar_g") and estimated_payload["sugar_g"] > 0:
		item_nutrition["sugar_g"] = estimated_payload["sugar_g"]
	if not item_nutrition.get("fat_g") and estimated_payload["fat_g"] > 0:
		item_nutrition["fat_g"] = estimated_payload["fat_g"]
	if (
		item_nutrition.get("protein_percent") is None
		and item_nutrition.get("kcal")
		and item_nutrition.get("protein_g") is not None
	):
		item_nutrition["protein_percent"] = round(
			min((flt(item_nutrition["protein_g"]) * 4 * 100.0) / flt(item_nutrition["kcal"]), 100.0), 1
		)

	# Resolve price: default selling price list > restaurant_base_price > standard_rate
	_price_list_rate = None
	try:
		_price_list_rate = _get_default_item_price_rate(doc)
	except Exception:
		pass
	_base_price = (
		_price_list_rate
		if _price_list_rate is not None
		else flt(doc.restaurant_base_price or doc.standard_rate)
	)

	# Resolve image: try multiple fields
	_image = getattr(doc, image_field, "") or ""
	if not _image:
		for _img_field in ("item_image", "website_image", "image"):
			_val = getattr(doc, _img_field, "") or ""
			if _val:
				_image = _val
				break

	builder_source_doc = template_doc if template_doc.name != doc.name else doc

	item_payload = {
		"name": doc.name,
		"slug": doc.restaurant_slug,
		"title": _variant_display_title(
			template_doc,
			fixed_attribute_values=fixed_attribute_values,
			representative_item_name=doc.name,
		)
		if template_doc.name != doc.name
		else doc.item_name,
		"short_desc": doc.restaurant_short_desc,
		"long_desc": doc.restaurant_long_desc or doc.description,
		"base_price": _base_price,
		"image": _image,
		"category": doc.restaurant_category,
		"category_title": frappe.db.get_value("Item Group", doc.restaurant_category, "item_group_name")
		or doc.restaurant_category,
		"category_slug": category_slug,
		"subcategory": doc.restaurant_subcategory,
		"subcategory_title": frappe.db.get_value("Item Group", doc.restaurant_subcategory, "item_group_name")
		or doc.restaurant_subcategory,
		"subcategory_slug": subcategory_slug or "",
		"prep_time_mins": cint(doc.get("restaurant_prep_time_mins") or 0),
		"nutrition": item_nutrition,
		"nutrition_kcal": item_nutrition.get("kcal"),
		"nutrition_protein_g": item_nutrition.get("protein_g"),
		"nutrition_carb_g": item_nutrition.get("carb_g"),
		"nutrition_sugar_g": item_nutrition.get("sugar_g"),
		"nutrition_fat_g": item_nutrition.get("fat_g"),
		"nutrition_protein_percent": item_nutrition.get("protein_percent"),
		"variant_of": template_doc.name if template_doc.name != doc.name else "",
		"variant_fixed_attributes": fixed_attribute_values if fixed_attribute_values else {},
		"variant_attributes": _variant_attribute_public_payload(doc.name),
		"has_bom": 1
		if frappe.db.exists("BOM", {"item": doc.name, "is_active": 1, "docstatus": ["!=", 2]})
		else 0,
		"restaurant_is_customizable": cint(
			builder_source_doc.get("restaurant_is_customizable") or doc.get("restaurant_is_customizable") or 0
		),
		"restaurant_builder_active": cint(
			builder_source_doc.get("restaurant_builder_active") or doc.get("restaurant_builder_active") or 0
		),
		"restaurant_builder_template": builder_source_doc.get("restaurant_builder_template")
		or doc.get("restaurant_builder_template")
		or "",
		"restaurant_customize_button_label": builder_source_doc.get("restaurant_customize_button_label")
		or doc.get("restaurant_customize_button_label")
		or "سفارشی‌سازی",
		"restaurant_allow_direct_add": cint(
			builder_source_doc.get("restaurant_allow_direct_add")
			or doc.get("restaurant_allow_direct_add")
			or 0
		),
		"tags": _split_tags(getattr(doc, "restaurant_item_tags", None)),
	}

	
	variants_mapping = []
	if cint(template_doc.get("has_variants")):
		try:
			variants_mapping = _management_template_variants_payload(template_doc)
		except Exception:
			pass
			
	return {
		"item": item_payload,
		"ingredients": ingredients,
		"modifier_groups": modifier_groups,
		"allergens": _split_tags(doc.restaurant_allergen_tags),
		"currency": _get_currency(),
		"variants_mapping": variants_mapping,
	}


def _menu_doc_config(menu_doc):
	item_price = _get_default_item_price_rate(menu_doc)
	base_price = (
		item_price if item_price is not None else (flt(menu_doc.restaurant_base_price) or flt(menu_doc.standard_rate))
	)
	return {
		"title": menu_doc.item_name,
		"base_price": base_price,
		"slug": menu_doc.restaurant_slug,
		"short_desc": menu_doc.restaurant_short_desc,
		"long_desc": menu_doc.restaurant_long_desc or menu_doc.description,
		"menu_ref": menu_doc.name,
	}


def _core_order_status(sales_order_doc):
	explicit = (sales_order_doc.get("restaurant_status") or "").strip().lower()
	if explicit in ORDER_STATUSES:
		return explicit
	return CORE_ORDER_STATUS_MAP.get((sales_order_doc.status or "").strip().lower(), "new")



def _default_company():
	return frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
		"Company", {}, "name"
	)


def _resolve_order_company(order_context=None):
	ctx = order_context if isinstance(order_context, dict) else {}
	company = (ctx.get("branch") or ctx.get("company") or "").strip()
	if company and frappe.db.exists("Company", company):
		return company
	return _default_company()


def _ensure_default_selling_price_list_field():
	if not frappe.db.exists("DocType", "Price List"):
		return False

	fieldname = DEFAULT_SELLING_PRICE_LIST_FIELD
	existing = frappe.db.get_value("Custom Field", {"dt": "Price List", "fieldname": fieldname}, "name")
	payload = {
		"doctype": "Custom Field",
		"dt": "Price List",
		"fieldname": fieldname,
		"label": _("Default Selling Price List"),
		"fieldtype": "Check",
		"insert_after": "selling",
		"default": "0",
		"module": "Restaurant",
	}

	if existing:
		doc = frappe.get_doc("Custom Field", existing)
		changed = False
		for key, value in payload.items():
			if key == "doctype":
				continue
			if doc.get(key) != value:
				doc.set(key, value)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)
			frappe.clear_cache(doctype="Price List")
		return True

	doc = frappe.get_doc(payload)
	doc.insert(ignore_permissions=True)
	frappe.clear_cache(doctype="Price List")
	return True


def _selling_price_list_filters(currency=None):
	filters = {"selling": 1}
	if currency:
		filters["currency"] = currency
	if _has_column("Price List", "enabled"):
		filters["enabled"] = 1
	return filters


def _selling_settings_default_price_list(currency=None):
	if not frappe.db.exists("DocType", "Selling Settings"):
		return ""
	meta = frappe.get_meta("Selling Settings")
	if not meta.get_field("selling_price_list"):
		return ""

	price_list_name = (frappe.db.get_single_value("Selling Settings", "selling_price_list") or "").strip()
	if not price_list_name or not frappe.db.exists("Price List", price_list_name):
		return ""
	if not cint(frappe.db.get_value("Price List", price_list_name, "selling") or 0):
		return ""
	if _has_column("Price List", "enabled") and cint(frappe.db.get_value("Price List", price_list_name, "enabled") or 0) != 1:
		return ""
	if currency and _has_column("Price List", "currency"):
		row_currency = (frappe.db.get_value("Price List", price_list_name, "currency") or "").strip()
		if row_currency and row_currency != currency:
			return ""
	return price_list_name


def _get_default_selling_price_list_name(currency=None, set_fallback_default=False):
	_ensure_default_selling_price_list_field()
	filters = _selling_price_list_filters(currency=currency)

	from_selling_settings = _selling_settings_default_price_list(currency=currency)
	if from_selling_settings:
		return from_selling_settings

	if _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
		preferred = frappe.db.get_value(
			"Price List", {**filters, DEFAULT_SELLING_PRICE_LIST_FIELD: 1}, "name"
		)
		if preferred:
			return preferred

	fallback = frappe.db.get_value("Price List", filters, "name")
	if fallback and set_fallback_default and _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
		frappe.db.set_value("Price List", fallback, DEFAULT_SELLING_PRICE_LIST_FIELD, 1, update_modified=True)
	return fallback


def _default_selling_price_list(currency=None):
	name = _get_default_selling_price_list_name(currency=currency)
	if name:
		return name
	if currency:
		return _get_default_selling_price_list_name()
	return ""


def _default_uom():
	for name in ["Nos", "Unit", "واحد", "Box"]:
		if frappe.db.exists("UOM", name):
			return name
	return frappe.db.get_value("UOM", {}, "name") or "Nos"


def _item_requires_production(item_doc):
	if _has_column("Item", "restaurant_requires_bom"):
		return bool(cint(item_doc.get("restaurant_requires_bom")))
	return True


def _line_is_auto_added(so_item_row):
	if not _has_column("Sales Order Item", "restaurant_is_auto_added"):
		return False
	return bool(cint(so_item_row.get("restaurant_is_auto_added")))


def _line_requires_production(so_item_row, menu_doc):
	if _has_column("Sales Order Item", "restaurant_requires_production"):
		raw_value = so_item_row.get("restaurant_requires_production")
		if raw_value in ("", None):
			return _item_requires_production(menu_doc)
		return bool(cint(raw_value))
	return _item_requires_production(menu_doc)


def _set_sales_order_item_flags(row_payload, is_auto_added, requires_production):
	if _has_column("Sales Order Item", "restaurant_is_auto_added"):
		row_payload["restaurant_is_auto_added"] = cint(is_auto_added)
	if _has_column("Sales Order Item", "restaurant_requires_production"):
		row_payload["restaurant_requires_production"] = cint(requires_production)


def _get_auto_order_service_items(branches=None):
	if not _has_column("Item", "restaurant_auto_add_to_order"):
		return []

	filters = {
		"disabled": 0,
		"is_sales_item": 1,
		"restaurant_auto_add_to_order": 1,
	}
	if branches and _has_column("Item", "restaurant_branch"):
		normalized = sorted({(branch or "").strip() for branch in branches})
		if "" not in normalized:
			normalized.append("")
		filters["restaurant_branch"] = ["in", normalized]

	fields = [
		"name",
		"item_code",
		"item_name",
		"description",
		"stock_uom",
		"standard_rate",
	]
	if _has_column("Item", "restaurant_base_price"):
		fields.append("restaurant_base_price")
	if _has_column("Item", "restaurant_auto_add_qty"):
		fields.append("restaurant_auto_add_qty")
	if _has_column("Item", "restaurant_branch"):
		fields.append("restaurant_branch")
	if _has_column("Item", "restaurant_requires_bom"):
		fields.append("restaurant_requires_bom")

	return frappe.get_all(
		"Item",
		filters=filters,
		fields=fields,
		order_by="item_name asc",
		ignore_permissions=True,
	)


def _ensure_customer(customer_name, mobile):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	existing = _find_customer_by_mobile(mobile)
	if existing:
		if normalized_mobile and _has_column("Customer", "mobile_no"):
			current_mobile = frappe.db.get_value("Customer", existing, "mobile_no")
			if not current_mobile:
				frappe.db.set_value("Customer", existing, "mobile_no", normalized_mobile, update_modified=False)
		return existing

	if not normalized_mobile:
		existing_by_name = frappe.db.get_value("Customer", {"customer_name": customer_name, "disabled": 0}, "name")
		if existing_by_name:
			return existing_by_name

	customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or frappe.db.get_value(
		"Customer Group", {}, "name"
	)
	territory = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value(
		"Territory", {"is_group": 0}, "name"
	)
	if not territory:
		territory = frappe.db.get_value("Territory", {}, "name")

	if not customer_group or not territory:
		frappe.throw(_("Please configure Customer Group and Territory first."))

	doc = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": customer_name,
			"customer_type": "Individual",
			"customer_group": customer_group,
			"territory": territory,
			"mobile_no": normalized_mobile,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _normalize_order_context_payload(order_context=None, order_type="takeaway"):
	ctx = _parse_json(order_context, {})
	if not isinstance(ctx, dict):
		ctx = {}
	ctx_type = (ctx.get("order_type") or "").strip().lower()
	if ctx_type not in ORDER_CONTEXT_TYPES:
		ctx_type = (
			"delivery" if order_type == "delivery" else "dine_in" if order_type == "dine_in" else "pickup"
		)
	ctx["order_type"] = ctx_type
	ctx["delivery_fee"] = flt(ctx.get("delivery_fee") or 0)
	ctx["branch"] = (ctx.get("branch") or "").strip()
	ctx["branch_title"] = (ctx.get("branch_title") or ctx.get("branch") or "").strip()
	ctx["table"] = (ctx.get("table") or "").strip()
	ctx["customer_note"] = (ctx.get("customer_note") or "").strip()
	ctx["kitchen_note"] = (ctx.get("kitchen_note") or "").strip()
	ctx["courier_note"] = (ctx.get("courier_note") or "").strip()
	ctx["waiter"] = (ctx.get("waiter") or "").strip()
	ctx["waiter_name"] = (ctx.get("waiter_name") or "").strip()
	ctx["org_member"] = (ctx.get("org_member") or "").strip()
	ctx["org_access_code"] = (ctx.get("org_access_code") or "").strip()
	ctx["organization"] = (ctx.get("organization") or "").strip()
	return ctx


def _create_sales_order(
	customer_name,
	mobile,
	order_type,
	address,
	note,
	cart_items,
	include_service_items=True,
	delivery_address_name="",
	delivery_payload=None,
	coupon=None,
	order_context=None,
	financial_modifiers=None,
	totals=None,
	commit=True,
):
	order_context = _normalize_order_context_payload(order_context, order_type=order_type)
	company = _resolve_order_company(order_context)
	if not company:
		frappe.throw(_("Default company is not configured."))

	customer = _ensure_customer(customer_name, mobile)
	currency = frappe.db.get_value("Company", company, "default_currency") or _get_currency(company)
	selling_price_list = _default_selling_price_list(currency) or _default_selling_price_list()
	if not selling_price_list:
		frappe.throw(_("Please configure at least one selling price list."))
	uom_fallback = _default_uom()
	delivery_payload = delivery_payload if isinstance(delivery_payload, dict) else {}
	coupon = coupon if isinstance(coupon, dict) else {}
	_ensure_checkout_sales_order_fields()

	doc_payload = {
		"doctype": "Sales Order",
		"customer": customer,
		"company": company,
		"transaction_date": today(),
		"delivery_date": today(),
		"currency": currency,
		"selling_price_list": selling_price_list,
		"ignore_pricing_rule": 1,
		"items": [],
	}

	if _has_column("Sales Order", "restaurant_customer_mobile"):
		doc_payload["restaurant_customer_mobile"] = mobile
	if _has_column("Sales Order", "restaurant_order_type"):
		doc_payload["restaurant_order_type"] = order_type
	if _has_column("Sales Order", "restaurant_delivery_address"):
		doc_payload["restaurant_delivery_address"] = address
	if _has_column("Sales Order", "restaurant_note"):
		doc_payload["restaurant_note"] = note
	if _has_column("Sales Order", "restaurant_status"):
		doc_payload["restaurant_status"] = "new"
	if _has_column("Sales Order", "restaurant_include_service_items"):
		doc_payload["restaurant_include_service_items"] = cint(include_service_items)
	if _has_column("Sales Order", "restaurant_order_context_json"):
		doc_payload["restaurant_order_context_json"] = frappe.as_json(order_context)
	if _has_column("Sales Order", "restaurant_branch"):
		doc_payload["restaurant_branch"] = order_context.get("branch") or ""
	if _has_column("Sales Order", "restaurant_table"):
		doc_payload["restaurant_table"] = order_context.get("table") or ""
	if _has_column("Sales Order", "restaurant_delivery_fee"):
		doc_payload["restaurant_delivery_fee"] = flt(order_context.get("delivery_fee") or 0)
	if delivery_payload and _has_column("Sales Order", "restaurant_delivery_address_name"):
		doc_payload["restaurant_delivery_address_name"] = (
			delivery_address_name or delivery_payload.get("id") or ""
		)
	if delivery_payload and _has_column("Sales Order", "restaurant_delivery_lat"):
		doc_payload["restaurant_delivery_lat"] = flt(delivery_payload.get("lat") or 0)
	if delivery_payload and _has_column("Sales Order", "restaurant_delivery_lng"):
		doc_payload["restaurant_delivery_lng"] = flt(delivery_payload.get("lng") or 0)
	if delivery_payload and _has_column("Sales Order", "restaurant_delivery_details_json"):
		doc_payload["restaurant_delivery_details_json"] = frappe.as_json(delivery_payload)

	subtotal = 0.0
	payload_snapshot = []
	selected_branches = set()
	packaging_qty_map = {}

	for cart_line in cart_items:
		menu_doc = _get_item_doc_by_payload(cart_line)
		customization = _extract_customization(cart_line.get("customization") or cart_line.get("config"))

		variant_doc = _resolve_variant_item_for_customization(menu_doc, customization or {})
		if variant_doc:
			menu_doc = variant_doc

		if _has_column("Item", "restaurant_out_of_stock") and cint(
			menu_doc.get("restaurant_out_of_stock") or 0
		):
			frappe.throw(
				_("{0} is currently out of stock.").format(menu_doc.get("item_name") or menu_doc.get("name"))
			)
		packaging_qty_map[menu_doc.name] = packaging_qty_map.get(menu_doc.name, 0.0) + flt(
			cart_line.get("qty")
		)

		branch = (
			cart_line.get("branch")
			or order_context.get("branch")
			or menu_doc.get("restaurant_branch")
			or "DEFAULT"
		).strip() or "DEFAULT"
		selected_branches.add(branch)
		markup_percent = _get_branch_pricing_markup_percent(branch)
		line_calc = _recalculate_line(
			menu_doc, cart_line.get("qty"), customization, branch_markup_percent=markup_percent
		)
		cfg = _menu_doc_config(menu_doc)
		line_requires_production = _item_requires_production(menu_doc)

		description = cfg["long_desc"] or cfg["short_desc"] or menu_doc.description or ""
		line_note = str(cart_line.get("note") or "").strip()
		if line_note:
			description = f"{description}\n\nیادداشت: {line_note}".strip()
			
		row_payload = {
			"item_code": menu_doc.item_code,
			"item_name": cfg["title"],
			"description": description,
			"qty": line_calc["qty"],
			"uom": menu_doc.stock_uom or uom_fallback,
			"stock_uom": menu_doc.stock_uom or uom_fallback,
			"rate": line_calc["unit_price"],
			"amount": line_calc["line_total"],
		}
		if line_note and _has_column("Sales Order Item", "restaurant_note"):
			row_payload["restaurant_note"] = line_note
		if _has_column("Sales Order Item", "restaurant_menu_slug"):
			row_payload["restaurant_menu_slug"] = cfg["slug"]
		if _has_column("Sales Order Item", "restaurant_customization_json"):
			row_payload["restaurant_customization_json"] = frappe.as_json(
				line_calc["normalized_customization"]
			)
		builder_selection_payload = (
			line_calc.get("normalized_customization", {}).get("builder_selection") or {}
		)
		if builder_selection_payload and _has_column("Sales Order Item", "restaurant_builder_selection_json"):
			row_payload["restaurant_builder_selection_json"] = frappe.as_json(
				line_calc["normalized_customization"]
			)
		if builder_selection_payload and _has_column("Sales Order Item", "restaurant_builder_summary"):
			row_payload["restaurant_builder_summary"] = (
				line_calc.get("normalized_customization", {}).get("builder_summary") or ""
			)
		if builder_selection_payload and _has_column("Sales Order Item", "restaurant_builder_price_delta"):
			row_payload["restaurant_builder_price_delta"] = flt(
				line_calc.get("pricing_breakdown", {}).get("builder_total")
				or line_calc.get("pricing_breakdown", {}).get("options_total")
				or line_calc.get("extra_charge")
				or 0
			)
		if builder_selection_payload and _has_column(
			"Sales Order Item", "restaurant_builder_stock_consumption_json"
		):
			row_payload["restaurant_builder_stock_consumption_json"] = frappe.as_json(
				line_calc.get("ingredient_components") or []
			)
		if builder_selection_payload and _has_column("Sales Order Item", "restaurant_builder_nutrition_json"):
			row_payload["restaurant_builder_nutrition_json"] = frappe.as_json(
				line_calc.get("nutrition_totals") or {}
			)
		if _has_column("Sales Order Item", "restaurant_selection_summary"):
			row_payload["restaurant_selection_summary"] = frappe.as_json(line_calc["selections"])
		if _has_column("Sales Order Item", "restaurant_pricing_breakdown_json"):
			row_payload["restaurant_pricing_breakdown_json"] = frappe.as_json(line_calc["pricing_breakdown"])
		if _has_column("Sales Order Item", "restaurant_extra_charge"):
			row_payload["restaurant_extra_charge"] = flt(line_calc["extra_charge"])
		_set_sales_order_item_flags(
			row_payload,
			is_auto_added=False,
			requires_production=line_requires_production,
		)

		doc_payload["items"].append(row_payload)
		subtotal += line_calc["line_total"]
		payload_snapshot.append(
			{
				"item_code": menu_doc.item_code,
				"slug": cfg["slug"],
				"title": cfg["title"],
				"qty": line_calc["qty"],
				"unit_price": line_calc["unit_price"],
				"line_total": line_calc["line_total"],
				"branch": branch,
				"customization": line_calc["normalized_customization"],
				"selections": line_calc["selections"],
				"pricing_breakdown": line_calc["pricing_breakdown"],
				"is_auto_added": 0,
				"requires_production": cint(line_requires_production),
			}
		)

	if include_service_items:
		for service_item in _get_auto_order_service_items(branches=selected_branches):
			qty = flt(service_item.get("restaurant_auto_add_qty") or 1)
			if qty <= 0:
				continue

			service_code = service_item.get("item_code") or service_item.get("name")
			_service_item_price = _get_default_item_price_rate(service_item)
			unit_price = _service_item_price if _service_item_price is not None else flt(service_item.get("restaurant_base_price") or service_item.get("standard_rate") or 0)
			line_total = qty * unit_price
			line_requires_production = _item_requires_production(service_item)

			row_payload = {
				"item_code": service_code,
				"item_name": service_item.get("item_name") or service_code,
				"description": service_item.get("description")
				or service_item.get("item_name")
				or service_code,
				"qty": qty,
				"uom": service_item.get("stock_uom") or uom_fallback,
				"stock_uom": service_item.get("stock_uom") or uom_fallback,
				"rate": unit_price,
				"amount": line_total,
			}
			if _has_column("Sales Order Item", "restaurant_menu_slug"):
				row_payload["restaurant_menu_slug"] = ""
			if _has_column("Sales Order Item", "restaurant_customization_json"):
				row_payload["restaurant_customization_json"] = frappe.as_json({})
			if _has_column("Sales Order Item", "restaurant_selection_summary"):
				row_payload["restaurant_selection_summary"] = frappe.as_json([])
			if _has_column("Sales Order Item", "restaurant_pricing_breakdown_json"):
				row_payload["restaurant_pricing_breakdown_json"] = frappe.as_json(
					{
						"base_price": unit_price,
						"ingredient_delta_total": 0,
						"modifier_delta_total": 0,
						"extra_charge": 0,
						"unit_price": unit_price,
						"qty": qty,
						"line_total": line_total,
						"recipe_multiplier": 1,
						"branch_markup_percent": 0,
						"nutrition": {
							"kcal": 0,
							"protein_g": 0,
							"carb_g": 0,
							"sugar_g": 0,
							"fat_g": 0,
							"protein_percent": None,
						},
						"nutrition_totals": {
							"kcal": 0,
							"protein_g": 0,
							"carb_g": 0,
							"sugar_g": 0,
							"fat_g": 0,
						},
						"ingredients": [],
						"modifiers": [],
					}
				)
			if _has_column("Sales Order Item", "restaurant_extra_charge"):
				row_payload["restaurant_extra_charge"] = 0
			_set_sales_order_item_flags(
				row_payload,
				is_auto_added=True,
				requires_production=line_requires_production,
			)

			doc_payload["items"].append(row_payload)
			subtotal += line_total
			payload_snapshot.append(
				{
					"item_code": service_code,
					"slug": "",
					"title": service_item.get("item_name") or service_code,
					"qty": qty,
					"unit_price": unit_price,
					"line_total": line_total,
					"branch": service_item.get("restaurant_branch") or "",
					"customization": {},
					"selections": [],
					"pricing_breakdown": {
						"base_price": unit_price,
						"ingredient_delta_total": 0,
						"modifier_delta_total": 0,
						"extra_charge": 0,
						"unit_price": unit_price,
						"qty": qty,
						"line_total": line_total,
						"recipe_multiplier": 1,
						"branch_markup_percent": 0,
						"nutrition": {
							"kcal": 0,
							"protein_g": 0,
							"carb_g": 0,
							"sugar_g": 0,
							"fat_g": 0,
							"protein_percent": None,
						},
						"nutrition_totals": {
							"kcal": 0,
							"protein_g": 0,
							"carb_g": 0,
							"sugar_g": 0,
							"fat_g": 0,
						},
						"ingredients": [],
						"modifiers": [],
					},
					"is_auto_added": 1,
					"requires_production": cint(line_requires_production),
				}
			)

	financial_modifiers = financial_modifiers or {}
	totals_data = totals or {}
	
	frontend_discount_amount = flt(totals_data.get("discountAmount") or 0)
	applied_coupon_code = coupon.get("code") if coupon else financial_modifiers.get("coupon_code")
	
	if frontend_discount_amount > 0:
		doc_payload["apply_discount_on"] = "Grand Total"
		doc_payload["discount_amount"] = min(frontend_discount_amount, subtotal)
		
		if applied_coupon_code:
			coupon_note = _("Coupon {0}: {1}").format(applied_coupon_code, frontend_discount_amount)
			doc_payload["customer_note"] = (doc_payload.get("customer_note") or "") + coupon_note
			payload_snapshot.append({"coupon": applied_coupon_code, "discount_amount": frontend_discount_amount})
				
	# Apply Service Charge & Taxes & Tip
	doc_payload["taxes"] = []
	tax_acc = frappe.db.get_value("Account", {"account_type": "Tax", "company": company}, "name")
	if not tax_acc:
		tax_acc = frappe.db.get_value("Account", {"is_group": 0, "company": company}, "name")
		
	totals_data = totals or {}
	pos_tax = flt(totals_data.get("taxAmount") or financial_modifiers.get("tax_amount") or 0)
	if pos_tax > 0 and tax_acc:
		doc_payload["taxes"].append({
			"charge_type": "Actual",
			"account_head": tax_acc,
			"description": "Tax",
			"tax_amount": pos_tax,
		})
		
	pos_service = flt(totals_data.get("serviceAmount") or 0)
	if pos_service > 0 and tax_acc:
		doc_payload["taxes"].append({
			"charge_type": "Actual",
			"account_head": tax_acc,
			"description": "Service Charge",
			"tax_amount": pos_service,
		})
		
	pos_tip = flt(totals_data.get("tipAmount") or financial_modifiers.get("tip_amount") or 0)
	if pos_tip > 0 and tax_acc:
		doc_payload["taxes"].append({
			"charge_type": "Actual",
			"account_head": tax_acc,
			"description": "Tip",
			"tax_amount": pos_tip,
		})

	pos_packaging = flt(
		totals_data.get("packagingAmount") or financial_modifiers.get("packaging_amount") or 0
	)
	if pos_packaging <= 0 and _caller_has_management_access():
		# Auto-compute the packaging fee only for staff/POS orders. Web (guest)
		# checkouts must never get a fee they could not see before payment.
		try:
			pos_packaging = flt(fp_compute_order_packaging_fee(order_type, packaging_qty_map))
		except Exception:
			pos_packaging = 0.0
	if pos_packaging > 0 and tax_acc:
		doc_payload["taxes"].append({
			"charge_type": "Actual",
			"account_head": tax_acc,
			"description": _("Packaging Fee"),
			"tax_amount": pos_packaging,
		})
	if _has_column("Sales Order", "restaurant_packaging_fee"):
		doc_payload["restaurant_packaging_fee"] = flt(pos_packaging)

	# Organizational order validation (caps, allowed days/hours, addresses) +
	# waiter attribution — throws and rolls the order back on rule hits.
	estimated_total = (
		subtotal + pos_tax + pos_service + pos_tip + pos_packaging
		+ flt(order_context.get("delivery_fee") or 0) - flt(frontend_discount_amount or 0)
	)
	org_binding = org_validate_order(
		order_context,
		customer,
		estimated_total,
		delivery_address_name=delivery_address_name or (delivery_payload.get("id") or ""),
	)
	if org_binding:
		if _has_column("Sales Order", "restaurant_organization"):
			doc_payload["restaurant_organization"] = org_binding.get("organization") or ""
		if _has_column("Sales Order", "restaurant_org_member"):
			member_label = org_binding.get("org_member") or ""
			if org_binding.get("org_member_code"):
				member_label = (member_label + " (" + org_binding["org_member_code"] + ")").strip() if member_label else org_binding["org_member_code"]
			doc_payload["restaurant_org_member"] = member_label
		order_context["organization"] = org_binding.get("organization") or ""
		if _has_column("Sales Order", "restaurant_order_context_json"):
			doc_payload["restaurant_order_context_json"] = frappe.as_json(order_context)
	if order_context.get("waiter") or order_context.get("waiter_name"):
		waiter_user = (order_context.get("waiter") or "").strip()
		waiter_name = (order_context.get("waiter_name") or "").strip()
		if waiter_user and frappe.db.exists("User", waiter_user):
			if _has_column("Sales Order", "restaurant_waiter"):
				doc_payload["restaurant_waiter"] = waiter_user
			if not waiter_name:
				waiter_name = frappe.db.get_value("User", waiter_user, "full_name") or waiter_user
		if waiter_name and _has_column("Sales Order", "restaurant_waiter_name"):
			doc_payload["restaurant_waiter_name"] = waiter_name

	so_doc = frappe.get_doc(doc_payload)
	# Some custom ERPNext forks expect commission-related attributes even when
	# corresponding custom fields are missing from Sales Order meta.
	if not getattr(so_doc, "total_structure", None):
		setattr(so_doc, "total_structure", subtotal)
	if getattr(so_doc, "amount_eligible_for_commission", None) is None:
		setattr(so_doc, "amount_eligible_for_commission", subtotal)
	if getattr(so_doc, "commission_rate", None) is None:
		setattr(so_doc, "commission_rate", 0)
	if getattr(so_doc, "total_commission", None) is None:
		setattr(so_doc, "total_commission", 0)

	so_doc.insert(ignore_permissions=True)

	if _has_column("Sales Order", "restaurant_payload_json"):
		so_doc.db_set("restaurant_payload_json", frappe.as_json(payload_snapshot))

	if frontend_discount_amount > 0 and coupon.get("name"):
		_mark_coupon_used(coupon.get("name"))

	so_doc.submit()
	so_doc.db_set("customer_name", customer_name, update_modified=False)
	if _has_column("Sales Order", "restaurant_status"):
		so_doc.db_set("restaurant_status", "confirmed", update_modified=False)

	if commit:
		frappe.db.commit()

	return {
		"status": "success",
		"order_id": so_doc.name,
		"order_code": so_doc.name,
		"grand_total": flt(so_doc.grand_total or subtotal) + flt(order_context.get("delivery_fee") or 0),
		"pricing_breakdown": payload_snapshot,
	}


def _get_branch_production_settings(branch, company):
	if not frappe.db.exists("DocType", "Restaurant Branch Production Settings"):
		frappe.throw(_("Restaurant Branch Production Settings doctype is required for production flow."))

	branch = (branch or "").strip() or "DEFAULT"
	settings_name = frappe.db.get_value(
		"Restaurant Branch Production Settings",
		{"branch": branch, "is_active": 1},
		"name",
	)
	if not settings_name and branch != "DEFAULT":
		settings_name = frappe.db.get_value(
			"Restaurant Branch Production Settings",
			{"branch": "DEFAULT", "is_active": 1},
			"name",
		)

	if not settings_name:
		frappe.throw(_("Branch production settings not found for branch: {0}.").format(branch))

	settings = frappe.get_doc("Restaurant Branch Production Settings", settings_name)
	if settings.company != company:
		frappe.throw(_("Branch production settings company mismatch for branch {0}.").format(settings.branch))

	for key in ["raw_warehouse", "kitchen_wip_warehouse", "finished_goods_warehouse"]:
		if not settings.get(key):
			frappe.throw(_("Branch production settings is missing field: {0}.").format(key))

	return settings


def _resolve_bom_template(menu_doc):
	item_code = (menu_doc.get("item_code") or menu_doc.get("name") or "").strip()
	if not item_code:
		return ""

	submitted_default = frappe.get_all(
		"BOM",
		filters={
			"item": item_code,
			"is_default": 1,
			"is_active": 1,
			"docstatus": 1,
		},
		fields=["name"],
		order_by="modified desc",
		ignore_permissions=True,
		limit_page_length=1,
	)
	if submitted_default:
		return submitted_default[0].name

	# Fallback: if no submitted default exists, pick the most suitable active BOM.
	fallback_rows = frappe.get_all(
		"BOM",
		filters={
			"item": item_code,
			"is_active": 1,
			"docstatus": ["!=", 2],
		},
		fields=["name"],
		order_by="is_default desc, docstatus desc, modified desc",
		ignore_permissions=True,
		limit_page_length=1,
	)
	return fallback_rows[0].name if fallback_rows else ""


def clear_item_default_bom_links_for_bom(doc, method=None):
	bom_name = (getattr(doc, "name", "") or "").strip()
	if not bom_name or not frappe.db.has_column("Item", "default_bom"):
		return

	if not frappe.db.exists("Item", {"default_bom": bom_name}):
		return

	frappe.db.sql(
		"""
        UPDATE `tabItem`
        SET default_bom = ''
        WHERE default_bom = %s
        """,
		(bom_name,),
	)

	item_code = ((getattr(doc, "item", "") if doc else "") or "").strip()
	if item_code:
		_refresh_item_nutrition_from_bom(item_code)


def clear_item_default_bom_links_on_bom_trash(doc, method=None):
	# Backward-compatible alias for older hook references.
	clear_item_default_bom_links_for_bom(doc, method=method)


def refresh_item_nutrition_for_bom(doc, method=None):
	item_code = ((getattr(doc, "item", "") if doc else "") or "").strip()
	if not item_code:
		return
	_upsert_bom_nutrition_fields(doc)
	_refresh_item_nutrition_from_bom(item_code)


def _deactivate_item_if_possible(item_code):
	item_code = (item_code or "").strip()
	if not item_code or not frappe.db.exists("Item", item_code):
		return False

	if not frappe.db.has_column("Item", "disabled"):
		return False

	if cint(frappe.db.get_value("Item", item_code, "disabled")) == 1:
		return False

	item_doc = frappe.get_doc("Item", item_code)
	item_doc.disabled = 1
	item_doc.flags.ignore_validate = True
	item_doc.save(ignore_permissions=True)
	return True


def _build_ticket_components(menu_doc, bom_doc, line_calc, line_qty, recipe_multiplier, source_warehouse):
	components = []
	recipe_multiplier = flt(recipe_multiplier or 1)
	if recipe_multiplier <= 0:
		recipe_multiplier = 1

	bom_qty = flt(bom_doc.quantity or 1)
	if bom_qty <= 0:
		bom_qty = 1

	ingredient_by_base_item = {}
	for row in line_calc.get("ingredient_components") or []:
		if (row.get("source_type") or "bom_item") != "bom_item":
			continue
		base_item_code = (row.get("base_item_code") or row.get("item_code") or "").strip()
		if base_item_code:
			ingredient_by_base_item[base_item_code] = row

	qty_map = defaultdict(float)

	def _append_component_row(
		item_code,
		final_qty,
		source_type,
		ingredient_data,
		base_item_code="",
		selected_alternative_item="",
		base_qty=0,
		selected_base_qty=0,
		selected_multiplier=1,
		recipe_multiplier_value=1,
	):
		item_code = (item_code or "").strip()
		if not item_code or final_qty <= 1e-8:
			return

		item_name = frappe.db.get_value("Item", item_code, "item_name")
		stock_uom = (
			ingredient_data.get("stock_uom")
			if ingredient_data and ingredient_data.get("stock_uom")
			else frappe.db.get_value("Item", item_code, "stock_uom")
		)
		if _item_consumes_stock(item_code):
			qty_map[item_code] += final_qty
		components.append(
			{
				"item_code": item_code,
				"item_name": item_name,
				"base_item_code": (base_item_code or "").strip(),
				"selected_alternative_item": (selected_alternative_item or "").strip(),
				"ingredient_key": ingredient_data.get("ingredient_key") or item_code,
				"ingredient_label": ingredient_data.get("ingredient_label") or item_name or item_code,
				"stock_uom": stock_uom,
				"source_warehouse": source_warehouse,
				"base_qty": base_qty,
				"selected_base_qty": selected_base_qty,
				"base_multiplier": flt(ingredient_data.get("base_multiplier") or 0),
				"selected_multiplier": selected_multiplier,
				"recipe_multiplier": recipe_multiplier_value,
				"final_qty": final_qty,
				"is_required": cint(ingredient_data.get("is_required")),
				"is_included_by_default": cint(ingredient_data.get("is_included_by_default")),
				"pricing_rate": flt(ingredient_data.get("pricing_rate") or 0),
				"pricing_delta": flt(ingredient_data.get("pricing_delta") or 0),
				"source_type": source_type,
			}
		)

	def _get_item_bom_doc(item_code):
		item_code = (item_code or "").strip()
		if not item_code or not frappe.db.exists("Item", item_code):
			return None
		item_doc = frappe.get_cached_doc("Item", item_code)
		return _get_bom_doc(item_doc)

	for bom_row in bom_doc.items or []:
		base_per_serving = flt(bom_row.qty) / bom_qty
		ingredient_data = ingredient_by_base_item.get(bom_row.item_code)

		if ingredient_data:
			selected_multiplier = flt(ingredient_data.get("selected_multiplier") or 0)
			selected_base_qty = flt(
				ingredient_data.get("selected_base_qty")
				if ingredient_data.get("selected_base_qty") not in (None, "")
				else ingredient_data.get("base_qty") or base_per_serving
			)
			component_item_code = (ingredient_data.get("item_code") or bom_row.item_code or "").strip()
			component_item_name = ingredient_data.get("item_name") or frappe.db.get_value(
				"Item", component_item_code, "item_name"
			)
			component_stock_uom = (
				ingredient_data.get("stock_uom")
				or frappe.db.get_value("Item", component_item_code, "stock_uom")
				or bom_row.stock_uom
				or bom_row.uom
			)
		else:
			selected_multiplier = 1
			selected_base_qty = base_per_serving
			component_item_code = (bom_row.item_code or "").strip()
			component_item_name = bom_row.item_name or frappe.db.get_value(
				"Item", component_item_code, "item_name"
			)
			component_stock_uom = (
				bom_row.stock_uom
				or bom_row.uom
				or frappe.db.get_value("Item", component_item_code, "stock_uom")
			)

		if not component_item_code:
			continue

		final_qty = selected_base_qty * selected_multiplier * flt(line_qty) * recipe_multiplier
		if final_qty <= 1e-8:
			continue
		if _item_consumes_stock(component_item_code):
			qty_map[component_item_code] += final_qty

		payload = {
			"item_code": component_item_code,
			"item_name": component_item_name,
			"base_item_code": bom_row.item_code,
			"selected_alternative_item": component_item_code
			if component_item_code != bom_row.item_code
			else "",
			"ingredient_key": ingredient_data.get("ingredient_key") if ingredient_data else bom_row.item_code,
			"ingredient_label": ingredient_data.get("ingredient_label")
			if ingredient_data
			else bom_row.item_name,
			"stock_uom": component_stock_uom,
			"source_warehouse": source_warehouse,
			"base_qty": base_per_serving,
			"selected_base_qty": selected_base_qty,
			"base_multiplier": flt(ingredient_data.get("base_multiplier") if ingredient_data else 1),
			"selected_multiplier": selected_multiplier,
			"recipe_multiplier": recipe_multiplier,
			"final_qty": final_qty,
			"is_required": cint(ingredient_data.get("is_required")) if ingredient_data else 0,
			"is_included_by_default": cint(ingredient_data.get("is_included_by_default"))
			if ingredient_data
			else 1,
			"pricing_rate": flt(ingredient_data.get("pricing_rate")) if ingredient_data else 0,
			"pricing_delta": flt(ingredient_data.get("pricing_delta")) if ingredient_data else 0,
			"source_type": "bom_item",
		}
		components.append(payload)

	for ingredient_data in line_calc.get("ingredient_components") or []:
		if (ingredient_data.get("source_type") or "bom_item") == "bom_item":
			continue
		item_code = (ingredient_data.get("item_code") or "").strip()
		if not item_code:
			continue
		selected_multiplier = flt(ingredient_data.get("selected_multiplier") or 0)
		if selected_multiplier <= 0:
			continue

		base_qty = flt(
			ingredient_data.get("selected_base_qty")
			if ingredient_data.get("selected_base_qty") not in (None, "")
			else ingredient_data.get("base_qty") or 0
		)
		final_qty = base_qty * selected_multiplier * flt(line_qty) * recipe_multiplier
		if final_qty <= 1e-8:
			continue
		source_type = ingredient_data.get("source_type") or "modifier_add_on"
		if source_type in ("modifier_add_on", "builder_component"):
			modifier_bom_doc = _get_item_bom_doc(item_code)
			if modifier_bom_doc and (modifier_bom_doc.items or []):
				modifier_bom_qty = flt(modifier_bom_doc.quantity or 1)
				if modifier_bom_qty <= 0:
					modifier_bom_qty = 1
				for modifier_bom_row in modifier_bom_doc.items or []:
					child_item_code = (modifier_bom_row.item_code or "").strip()
					if not child_item_code:
						continue
					child_per_unit = flt(modifier_bom_row.qty or 0) / modifier_bom_qty
					child_final_qty = child_per_unit * final_qty
					_append_component_row(
						child_item_code,
						child_final_qty,
						"modifier_bom_item",
						ingredient_data,
						base_item_code=item_code,
						selected_alternative_item="",
						base_qty=child_per_unit,
						selected_base_qty=child_per_unit,
						selected_multiplier=final_qty,
						recipe_multiplier_value=recipe_multiplier,
					)
				continue

		_append_component_row(
			item_code,
			final_qty,
			source_type,
			ingredient_data,
			base_item_code=(ingredient_data.get("base_item_code") or "").strip(),
			selected_alternative_item=(ingredient_data.get("selected_alternative_item") or "").strip(),
			base_qty=base_qty,
			selected_base_qty=base_qty,
			selected_multiplier=selected_multiplier,
			recipe_multiplier_value=recipe_multiplier,
		)

	return components, qty_map


def _create_work_order_for_ticket(
	ticket_doc, sales_order_doc, so_item_row, menu_doc, settings, bom_name, qty_map
):
	wo_doc = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": menu_doc.item_code,
			"bom_no": bom_name,
			"company": sales_order_doc.company,
			"qty": flt(so_item_row.qty),
			"sales_order": sales_order_doc.name,
			"sales_order_item": so_item_row.name,
			"source_warehouse": settings.raw_warehouse,
			"wip_warehouse": settings.kitchen_wip_warehouse,
			"fg_warehouse": settings.finished_goods_warehouse,
			"use_multi_level_bom": 0,
			"skip_transfer": 1,
		}
	)
	wo_doc.insert(ignore_permissions=True)
	updates = {}
	if _has_column("Work Order", "restaurant_sales_order"):
		updates["restaurant_sales_order"] = sales_order_doc.name
	if _has_column("Work Order", "restaurant_sales_order_item"):
		updates["restaurant_sales_order_item"] = so_item_row.name
	# Use sales_order name as identifier
	if _has_column("Work Order", "restaurant_production_ticket"):
		updates["restaurant_production_ticket"] = ticket_doc.name
	if _has_column("Work Order", "restaurant_customization_json"):
		updates["restaurant_customization_json"] = ticket_doc.customization_json or ""
	if updates:
		frappe.db.set_value("Work Order", wo_doc.name, updates, update_modified=False)

	_sync_work_order_required_items(wo_doc.name, qty_map=qty_map, source_warehouse=settings.raw_warehouse)
	return wo_doc.name


def _sync_work_order_required_items(wo_name, qty_map, source_warehouse):
	wo_name = (wo_name or "").strip()
	if not wo_name or not frappe.db.exists("Work Order", wo_name):
		return

	normalized_rows = []
	for item_code, raw_qty in (qty_map or {}).items():
		code = (item_code or "").strip()
		qty = flt(raw_qty)
		if not code or qty <= 1e-8 or not _item_consumes_stock(code):
			continue
		normalized_rows.append((code, qty))

	normalized_rows.sort(key=lambda row: row[0])
	item_codes = [row[0] for row in normalized_rows]
	item_meta_map = {}
	if item_codes:
		for row in frappe.get_all(
			"Item",
			filters={"name": ["in", item_codes]},
			fields=["name", "item_name", "description", "stock_uom"],
			ignore_permissions=True,
		):
			item_meta_map[row.name] = row

	frappe.db.delete(
		"Work Order Item",
		{
			"parent": wo_name,
			"parenttype": "Work Order",
			"parentfield": "required_items",
		},
	)

	has_allow_alt = _has_column("Work Order Item", "allow_alternative_item")
	has_source_warehouse = _has_column("Work Order Item", "source_warehouse")
	for idx, (item_code, qty) in enumerate(normalized_rows, start=1):
		item_meta = item_meta_map.get(item_code) or {}
		row_payload = {
			"doctype": "Work Order Item",
			"parent": wo_name,
			"parenttype": "Work Order",
			"parentfield": "required_items",
			"idx": idx,
			"item_code": item_code,
			"item_name": item_meta.get("item_name") or frappe.db.get_value("Item", item_code, "item_name"),
			"description": item_meta.get("description") or "",
			"stock_uom": item_meta.get("stock_uom") or frappe.db.get_value("Item", item_code, "stock_uom"),
			"required_qty": qty,
		}
		if has_source_warehouse:
			row_payload["source_warehouse"] = source_warehouse
		if has_allow_alt:
			row_payload["allow_alternative_item"] = 1

		frappe.get_doc(row_payload).insert(ignore_permissions=True)


def _production_skip_payload(row, menu_doc, reason, message=None):
	return {
		"sales_order_item": row.name,
		"item_code": row.item_code,
		"item_name": (menu_doc.get("item_name") if menu_doc else "") or row.item_name,
		"reason": reason,
		"message": message or "",
	}


def _create_production_for_sales_order(so_doc):
	tickets = []
	work_orders = []
	skipped_items = []

	for row in so_doc.items or []:
		if not row.item_code:
			skipped_items.append(_production_skip_payload(row, None, "missing_item_code"))
			continue

		menu_doc = frappe.get_doc("Item", row.item_code)
		if _line_is_auto_added(row):
			skipped_items.append(_production_skip_payload(row, menu_doc, "auto_added_item"))
			continue
		if not _line_requires_production(row, menu_doc):
			skipped_items.append(_production_skip_payload(row, menu_doc, "production_not_required"))
			continue

		branch = (menu_doc.get("restaurant_branch") or "DEFAULT").strip() or "DEFAULT"
		try:
			settings = _get_branch_production_settings(branch, so_doc.company)
		except Exception as exc:
			skipped_items.append(
				_production_skip_payload(
					row,
					menu_doc,
					"missing_branch_settings",
					str(exc),
				)
			)
			continue

		bom_name = _resolve_bom_template(menu_doc)
		if not bom_name:
			skipped_items.append(
				_production_skip_payload(
					row,
					menu_doc,
					"missing_bom",
					_("No BOM template found for menu item: {0}").format(menu_doc.item_name),
				)
			)
			continue

		bom_doc = frappe.get_doc("BOM", bom_name)
		if cint(bom_doc.docstatus) != 1:
			skipped_items.append(
				_production_skip_payload(
					row,
					menu_doc,
					"bom_not_submitted",
					_("BOM template must be submitted: {0}").format(bom_name),
				)
			)
			continue

		customization = _parse_json(row.get("restaurant_customization_json"), {})
		pricing_breakdown = _parse_json(row.get("restaurant_pricing_breakdown_json"), {})
		line_calc = _recalculate_line(
			menu_doc,
			row.qty,
			customization,
			branch_markup_percent=flt(settings.pricing_markup_percent or 0),
		)

		selected_bom = (
			line_calc.get("pricing_breakdown", {}).get("selected_bom")
			or pricing_breakdown.get("selected_bom")
			or ""
		).strip()
		if selected_bom and frappe.db.exists("BOM", selected_bom):
			selected_bom_doc = frappe.get_doc("BOM", selected_bom)
			if (
				selected_bom_doc.item == menu_doc.item_code
				and cint(selected_bom_doc.docstatus) == 1
				and cint(selected_bom_doc.is_active)
			):
				bom_name = selected_bom_doc.name
				bom_doc = selected_bom_doc

		recipe_multiplier = flt(
			pricing_breakdown.get("recipe_multiplier") or line_calc.get("recipe_multiplier") or 1
		)
		component_rows, qty_map = _build_ticket_components(
			menu_doc,
			bom_doc,
			line_calc,
			row.qty,
			recipe_multiplier,
			settings.raw_warehouse,
		)

		ticket_doc = frappe.get_doc(
			{
				"doctype": "Restaurant Production Ticket",
				"sales_order": so_doc.name,
				"sales_order_item": row.name,
				"order_code": so_doc.name,
				"company": so_doc.company,
				"branch": settings.branch,
				"menu_item": menu_doc.name,
				"menu_item_name": menu_doc.item_name,
				"qty": flt(row.qty),
				"recipe_multiplier": recipe_multiplier,
				"status": "planned",
				"bom_template": bom_name,
				"source_warehouse": settings.raw_warehouse,
				"wip_warehouse": settings.kitchen_wip_warehouse,
				"fg_warehouse": settings.finished_goods_warehouse,
				"customization_json": frappe.as_json(line_calc["normalized_customization"]),
				"pricing_breakdown_json": frappe.as_json(line_calc["pricing_breakdown"]),
				"components": component_rows,
			}
		)
		ticket_doc.insert(ignore_permissions=True)

		if _has_column("Sales Order Item", "restaurant_production_ticket"):
			frappe.db.set_value(
				"Sales Order Item",
				row.name,
				"restaurant_production_ticket",
				ticket_doc.name,
				update_modified=False,
			)

		wo_name = _create_work_order_for_ticket(
			ticket_doc=ticket_doc,
			sales_order_doc=so_doc,
			so_item_row=row,
			menu_doc=menu_doc,
			settings=settings,
			bom_name=bom_name,
			qty_map=qty_map,
		)
		ticket_doc.db_set("work_order", wo_name, update_modified=False)

		tickets.append(ticket_doc.name)
		work_orders.append(wo_name)

	return {
		"production_tickets": tickets,
		"work_orders": work_orders,
		"skipped_items": skipped_items,
	}


def _status_timeline_for_order_type(status, order_type="takeaway"):
	if order_type == "dine_in":
		labels = DINE_IN_STATUS_FLOW
	elif order_type == "delivery":
		labels = DELIVERY_STATUS_FLOW
	else:
		labels = PICKUP_STATUS_FLOW
	current_index = labels.index(status) if status in labels else 0
	return [{"status": row, "done": index <= current_index} for index, row in enumerate(labels)]


def _get_sales_order_payload(so_name):
	doc = frappe.get_doc("Sales Order", so_name)
	status = _core_order_status(doc)
	delivery_details = (
		_parse_json(doc.get("restaurant_delivery_details_json"), {})
		if _has_column("Sales Order", "restaurant_delivery_details_json")
		else {}
	)
	order_context = (
		_parse_json(doc.get("restaurant_order_context_json"), {})
		if _has_column("Sales Order", "restaurant_order_context_json")
		else {}
	)
	if not isinstance(order_context, dict):
		order_context = {}

	items_payload = []
	for row in doc.items or []:
		parsed_config = _parse_json(row.get("restaurant_customization_json"), {})
		selection_rows = _parse_json(row.get("restaurant_selection_summary"), [])
		pricing_breakdown = _parse_json(row.get("restaurant_pricing_breakdown_json"), {})
		selections = selection_rows if isinstance(selection_rows, list) else []

		items_payload.append(
			{
				"menu_item": row.item_code,
				"title": row.item_name,
				"qty": flt(row.qty),
				"unit_price": flt(row.rate),
				"line_total": flt(row.amount),
				"customization": parsed_config,
				"selections": selections,
				"pricing_breakdown": pricing_breakdown,
				"nutrition": pricing_breakdown.get("nutrition")
				if isinstance(pricing_breakdown, dict)
				else {},
				"nutrition_totals": pricing_breakdown.get("nutrition_totals")
				if isinstance(pricing_breakdown, dict)
				else {},
				"extra_charge": flt(row.get("restaurant_extra_charge") or 0),
				"production_ticket": row.get("restaurant_production_ticket") or "",
				"is_auto_added": cint(row.get("restaurant_is_auto_added") or 0),
				"requires_production": cint(
					row.get("restaurant_requires_production")
					if row.get("restaurant_requires_production") not in ("", None)
					else 1
				)
				if _has_column("Sales Order Item", "restaurant_requires_production")
				else 1,
			}
		)

	resolved_order_type = doc.get("restaurant_order_type") or "takeaway"
	context_order_type = order_context.get("order_type") or (
		"pickup" if resolved_order_type == "takeaway" else resolved_order_type
	)
	order_context.setdefault("order_type", context_order_type)
	if _has_column("Sales Order", "restaurant_branch") and doc.get("restaurant_branch"):
		order_context.setdefault("branch", doc.get("restaurant_branch"))
	if _has_column("Sales Order", "restaurant_table") and doc.get("restaurant_table"):
		order_context.setdefault("table", doc.get("restaurant_table"))
	if _has_column("Sales Order", "restaurant_delivery_fee"):
		order_context.setdefault("delivery_fee", flt(doc.get("restaurant_delivery_fee") or 0))

	order_payload = {
		"name": doc.name,
		"order_code": doc.name,
		"customer_name": doc.customer_name,
		"mobile": doc.get("restaurant_customer_mobile") or "",
		"order_type": resolved_order_type,
		"order_context": order_context,
		"address": doc.get("restaurant_delivery_address") or "",
		"delivery_address_id": doc.get("restaurant_delivery_address_name") or "",
		"delivery_lat": flt(doc.get("restaurant_delivery_lat") or 0)
		if _has_column("Sales Order", "restaurant_delivery_lat")
		else None,
		"delivery_lng": flt(doc.get("restaurant_delivery_lng") or 0)
		if _has_column("Sales Order", "restaurant_delivery_lng")
		else None,
		"delivery_details": delivery_details if isinstance(delivery_details, dict) else {},
		"note": _clean_automatic_pos_note(doc.get("restaurant_note") or ""),
		"include_service_items": cint(doc.get("restaurant_include_service_items") or 1)
		if _has_column("Sales Order", "restaurant_include_service_items")
		else 1,
		"status": status,
		"placed_at": str(doc.creation or doc.transaction_date or now_datetime()),
		"subtotal": flt(doc.total or doc.net_total),
		"grand_total": flt(doc.grand_total or doc.total),
	}

	return {
		"order": order_payload,
		"items": items_payload,
		"status_timeline": _status_timeline_for_order_type(status, context_order_type),
	}


def _get_bom_doc(menu_item_doc):
	bom_name = _resolve_bom_template(menu_item_doc)
	if not bom_name or not frappe.db.exists("BOM", bom_name):
		return None
	return frappe.get_doc("BOM", bom_name)


def _get_modifier_source_bom_doc(menu_item_doc, primary_bom_doc=None):
	if menu_item_doc.doctype != "Item" or not frappe.db.exists("DocType", "Restaurant BOM Modifier"):
		return primary_bom_doc

	bom_doc = primary_bom_doc or _get_bom_doc(menu_item_doc)
	if (bom_doc.get("restaurant_modifier_rows") if bom_doc else None) or []:
		return bom_doc

	item_code = (menu_item_doc.get("item_code") or menu_item_doc.get("name") or "").strip()
	if not item_code:
		return bom_doc

	primary_bom_name = (bom_doc.name if bom_doc else "") or ""
	fallback_rows = frappe.db.sql(
		"""
		SELECT bom.name
		FROM `tabBOM` bom
		INNER JOIN `tabRestaurant BOM Modifier` modifier_row
			ON modifier_row.parent = bom.name
		WHERE bom.item = %s
			AND bom.docstatus = 1
			AND bom.name != %s
		GROUP BY bom.name, bom.is_active, bom.is_default, bom.modified
		ORDER BY bom.is_active DESC, bom.is_default DESC, bom.modified DESC
		LIMIT 1
		""",
		(item_code, primary_bom_name),
		as_dict=True,
	)
	if not fallback_rows:
		return bom_doc

	fallback_bom_name = (fallback_rows[0].get("name") or "").strip()
	if not fallback_bom_name or not frappe.db.exists("BOM", fallback_bom_name):
		return bom_doc

	return frappe.get_doc("BOM", fallback_bom_name)


def _get_item_alternative_options(
	base_item,
	allow_alternative_item=0,
	item_meta_cache=None,
	base_qty=0,
	base_uom="",
	price_list=None,
):
	item_meta_cache = item_meta_cache if item_meta_cache is not None else {}
	option_map = {}
	base_item = (base_item or "").strip()
	base_qty = flt(base_qty or 0)
	base_uom = (base_uom or "").strip()

	if (
		cint(allow_alternative_item)
		and base_item
		and frappe.db.exists("DocType", "Item Alternative")
	):
		alt_fieldname = ""
		if _has_column("Item Alternative", "alternative_item"):
			alt_fieldname = "alternative_item"
		elif _has_column("Item Alternative", "alternative_item_code"):
			alt_fieldname = "alternative_item_code"
		elif _has_column("Item Alternative", "item_code"):
			alt_fieldname = "item_code"

		filters = None
		if _has_column("Item Alternative", "item_code") and alt_fieldname != "item_code":
			filters = {"item_code": base_item}
		elif _has_column("Item Alternative", "parent") and _has_column("Item Alternative", "parenttype"):
			filters = {"parent": base_item, "parenttype": "Item"}
		elif _has_column("Item Alternative", "parent"):
			filters = {"parent": base_item}

		query_fields = [alt_fieldname] if alt_fieldname else []
		if _has_column("Item Alternative", "idx"):
			query_fields.append("idx")

		order_by = "idx asc" if _has_column("Item Alternative", "idx") else "creation asc"
		item_alternative_rows = []
		if filters and query_fields:
			item_alternative_rows = frappe.get_all(
				"Item Alternative",
				filters=filters,
				fields=query_fields,
				order_by=order_by,
				ignore_permissions=True,
			)

		for alt_row in item_alternative_rows:
			alternative_item = (
				alt_row.get(alt_fieldname)
				or alt_row.get("alternative_item")
				or alt_row.get("alternative_item_code")
				or ""
			).strip()
			if not alternative_item:
				continue
			option_map.setdefault(
				alternative_item,
				{
					"alternative_item": alternative_item,
					"qty_multiplier": 1,
					"qty_addition": 0,
					"price_delta": 0,
					"sort_order": cint(alt_row.get("idx") or 0),
					"uom": "",
				},
			)

	missing_codes = [code for code in option_map if code not in item_meta_cache]
	if missing_codes:
		nutrition_fields = [
			fieldname for fieldname in NUTRITION_KEY_FIELD_MAP.values() if _has_column("Item", fieldname)
		]
		item_fields = ["name", "item_name", "stock_uom", *nutrition_fields]
		if _has_column("Item", "disabled"):
			item_fields.append("disabled")
		for item_row in frappe.get_all(
			"Item",
			filters={"name": ["in", missing_codes]},
			fields=item_fields,
			ignore_permissions=True,
		):
			item_meta_cache[item_row.name] = item_row

	options = []
	for option in option_map.values():
		item_meta = item_meta_cache.get(option["alternative_item"], {})
		option["item_name"] = item_meta.get("item_name") or option["alternative_item"]
		option["stock_uom"] = item_meta.get("stock_uom") or option["uom"] or ""
		# ``uom`` is the unit shown to the cashier, while ``pricing_uom`` is
		# the unit in which the BOM quantity is authored. If the alternative
		# does not define its own source unit, price the same 10g/20g quantity
		# as the BOM row and let ERPNext convert it to the alternative stock UOM.
		option["pricing_uom"] = option.get("uom") or base_uom or option.get("stock_uom") or ""
		if not option["uom"]:
			option["uom"] = option["stock_uom"]
		option["item_disabled"] = 1 if cint(item_meta.get("disabled") or 0) == 1 else 0
		option["nutrition_kcal"] = flt(item_meta.get("restaurant_nutrition_kcal") or 0)
		option["nutrition_protein_g"] = flt(item_meta.get("restaurant_nutrition_protein_g") or 0)
		option["nutrition_carb_g"] = flt(item_meta.get("restaurant_nutrition_carb_g") or 0)
		option["nutrition_sugar_g"] = flt(item_meta.get("restaurant_nutrition_sugar_g") or 0)
		option["nutrition_fat_g"] = flt(item_meta.get("restaurant_nutrition_fat_g") or 0)
		option["price_status"] = "ok"
		option["price_source"] = "item_price"
		option["price_item_code"] = option["alternative_item"]
		option["price_list"] = (price_list or _default_selling_price_list() or "").strip()
		option["price_delta"] = 0.0
		option["resolved_price_delta"] = 0.0
		option["is_selectable"] = 1
		option["disabled"] = 0
		option["unavailable_reason"] = ""
		option["availability_status"] = "available"
		option["unit_rate"] = 0.0
		option["base_price"] = 0.0
		option["alternative_price"] = 0.0
		option["comparison_base_price"] = 0.0
		option["comparison_base_unit_rate"] = 0.0
		option["base_qty_in_stock_uom"] = 0.0
		option["alternative_qty_in_stock_uom"] = 0.0
		if base_item and base_qty > 0:
			qty_multiplier = flt(
				option.get("qty_multiplier") if option.get("qty_multiplier") not in (None, "") else 1
			)
			if qty_multiplier < 0:
				qty_multiplier = 0
			qty_addition = flt(option.get("qty_addition") or 0)
			alternative_qty = (base_qty * qty_multiplier) + qty_addition
			pricing_payload = _resolve_ingredient_alternative_pricing(
				base_item,
				base_qty,
				base_uom,
				option["alternative_item"],
				alternative_qty,
				alternative_uom=option.get("pricing_uom") or base_uom or option.get("stock_uom") or "",
				price_list=price_list,
			)
			option.update(pricing_payload)
		options.append(option)

	return sorted(
		options,
		key=lambda d: (cint(d.get("sort_order") or 0), d.get("item_name") or d.get("alternative_item") or ""),
	)


def _get_bom_row_alternative_options(bom_doc, bom_row, item_meta_cache=None):
	return _get_item_alternative_options(
		bom_row.get("item_code"),
		allow_alternative_item=bom_row.get("allow_alternative_item"),
		item_meta_cache=item_meta_cache,
		base_qty=bom_row.get("qty") or 0,
		base_uom=bom_row.get("uom") or bom_row.get("stock_uom") or "",
	)


def _get_bom_ingredient_rows(menu_item_doc):
	bom_doc = _get_bom_doc(menu_item_doc)
	if not bom_doc:
		return []

	rows = []
	item_meta_cache = {}
	for row in sorted(bom_doc.get("items") or [], key=lambda d: cint(d.idx or 0)):
		ingredient_item_code = (row.get("item_code") or "").strip()
		ingredient_image = ""
		if ingredient_item_code:
			ingredient_image = frappe.db.get_value("Item", ingredient_item_code, "image") or ""

		alternative_options = _get_bom_row_alternative_options(bom_doc, row, item_meta_cache=item_meta_cache)
		ingredient_pricing = (
			_resolve_default_selling_item_pricing(
				ingredient_item_code,
				row.get("qty") or 0,
				uom=row.get("uom") or row.get("stock_uom") or "",
			)
			if ingredient_item_code
			else {}
		)
		payload = {
			"ingredient_name": row.get("restaurant_customer_label")
			or row.get("item_name")
			or row.get("item_code"),
			"customer_label": row.get("restaurant_customer_label")
			or row.get("item_name")
			or row.get("item_code"),
			"ingredient_item": ingredient_item_code,
			"image": ingredient_image,
			"qty_uom": row.get("uom") or row.get("stock_uom"),
			"base_qty": flt(row.get("qty") or 0),
			"is_included_by_default": cint(row.get("restaurant_is_included_by_default")),
			"can_remove": cint(row.get("restaurant_can_remove")),
			"is_required": cint(row.get("restaurant_is_required")),
			"is_editable_qty": cint(row.get("restaurant_is_editable_qty"))
			if row.get("restaurant_is_editable_qty") is not None
			else 0,
			"min_multiplier": flt(row.get("restaurant_min_multiplier")),
			"max_multiplier": flt(row.get("restaurant_max_multiplier") or 3),
			"step_multiplier": flt(row.get("restaurant_step_multiplier") or 0.5),
			"multiplier_qty": flt(row.get("restaurant_multiplier_qty") or 0),
			"extra_when_added": flt(row.get("restaurant_extra_when_added")),
			"is_replaceable": cint(row.get("allow_alternative_item")),
			"alternative_options": alternative_options,
			"price_status": ingredient_pricing.get("price_status") or "",
			"price_list": ingredient_pricing.get("price_list") or "",
			"price_source": "item_price" if ingredient_item_code else "",
			"price_item_code": ingredient_pricing.get("item_code") or ingredient_item_code,
			"unit_rate": flt(ingredient_pricing.get("unit_rate") or 0),
			"base_price": flt(ingredient_pricing.get("total_price") or 0),
			"conversion_factor": flt(ingredient_pricing.get("conversion_factor") or 0),
			"source_uom": ingredient_pricing.get("source_uom") or row.get("uom") or row.get("stock_uom") or "",
			"stock_uom": ingredient_pricing.get("stock_uom") or row.get("stock_uom") or row.get("uom") or "",
			"qty_in_stock_uom": flt(ingredient_pricing.get("qty_in_stock_uom") or 0),
			"is_selectable": cint(ingredient_pricing.get("is_selectable") or 0) if ingredient_item_code else 0,
			"availability_status": ingredient_pricing.get("availability_status") or "",
			"unavailable_reason": ingredient_pricing.get("unavailable_reason") or "",
			"show_in_website": _bom_item_show_value(row, default=1),
			"sort_order": cint(row.get("idx") or 0),
		}
		rows.append(
			SimpleNamespace(
				**payload,
				get=lambda fieldname, default=None, _payload=payload: _payload.get(fieldname, default),
			)
		)
	return rows


def _build_modifier_groups(menu_item_doc):
	groups = []
	group_map = {}
	group_title_map = {}
	option_nutrition_cache = {}

	if menu_item_doc.doctype != "Item":
		return groups, group_map, group_title_map

	bom_doc = _get_modifier_source_bom_doc(menu_item_doc, primary_bom_doc=_get_bom_doc(menu_item_doc))
	modifier_rows = sorted(
		(bom_doc.get("restaurant_modifier_rows") if bom_doc else []) or [],
		key=lambda d: cint(d.get("idx") or 0),
	)

	def _normalize_group_meta(selection_mode, required, min_select, max_select):
		mode = (selection_mode or "single").strip().lower() or "single"
		if mode not in {"single", "multi"}:
			mode = "single"

		reqd = cint(required)
		min_count = cint(min_select)
		max_count = cint(max_select or 1)
		if mode == "single":
			min_count = 1 if reqd else 0
			max_count = 1
		else:
			min_count = max(min_count, 0)
			max_count = max(max_count, 1)

		return mode, reqd, min_count, max_count

	def _append_group_option(payload_group, option_row):
		option_name = (
			option_row.get("option_name")
			or option_row.get("option_key")
			or option_row.get("option_item")
			or option_row.get("alternative_bom")
			or option_row.get("option_label")
			or ""
		).strip()
		if not option_name:
			return

		action_type = (
			option_row.get("action_type") or option_row.get("modifier_type") or "add_on"
		).strip() or "add_on"
		if action_type not in {"add_on", "bom_variant"}:
			action_type = "add_on"

		option_item_code = (option_row.get("option_item") or "").strip()
		qty_rules = _normalize_modifier_option_quantity_rules(option_row)
		pricing_payload = _resolve_modifier_option_pricing(option_row)
		if cint(pricing_payload.get("item_disabled") or 0) == 1:
			return
		if action_type == "add_on" and pricing_payload.get("price_status") != "ok":
			return
		option_item_nutrition = option_nutrition_cache.get(option_item_code)
		if option_item_nutrition is None:
			option_item_nutrition = {}
			if option_item_code and frappe.db.exists("Item", option_item_code):
				option_item_doc = frappe.get_cached_doc("Item", option_item_code)
				nutrition_payload = _nutrition_per_unit_payload(option_item_doc)
				option_item_nutrition = {
					"nutrition_kcal": flt(nutrition_payload.get("kcal") or 0),
					"nutrition_protein_g": flt(nutrition_payload.get("protein_g") or 0),
					"nutrition_carb_g": flt(nutrition_payload.get("carb_g") or 0),
					"nutrition_sugar_g": flt(nutrition_payload.get("sugar_g") or 0),
					"nutrition_fat_g": flt(nutrition_payload.get("fat_g") or 0),
				}
			option_nutrition_cache[option_item_code] = option_item_nutrition

		option_payload = {
			"name": option_name,
			"label": (option_row.get("option_label") or option_name).strip(),
			"price_delta": flt(pricing_payload.get("price_delta") or 0),
			"is_default": cint(option_row.get("is_default")),
			"recipe_multiplier": flt(option_row.get("recipe_multiplier") or 1),
			"action_type": action_type,
			"modifier_type": action_type,
			"option_item": option_item_code,
			"option_uom": (option_row.get("option_uom") or "").strip(),
			"option_cost_rate": flt(option_row.get("option_cost_rate") or 0),
			"option_cost_amount": flt(option_row.get("option_cost_amount") or 0),
			"replacement_for_item": (option_row.get("replacement_for_item") or "").strip(),
			"alternative_bom": (option_row.get("alternative_bom") or "").strip(),
			"option_qty": flt(qty_rules.get("option_qty") or 1),
			"base_qty": flt(qty_rules.get("base_qty") or 1),
			"min_qty": flt(qty_rules.get("min_qty") or 0),
			"max_qty": flt(qty_rules.get("max_qty") or 0),
			"qty_step": flt(qty_rules.get("qty_step") or 1),
			"legacy_price_delta": flt(option_row.get("price_delta") or 0),
			**pricing_payload,
			**option_item_nutrition,
		}
		payload_group["options"].append(option_payload)

	group_doc_cache = {}
	grouped = {}
	for row in modifier_rows:
		linked_group = (row.get("modifier_group") or "").strip()
		if linked_group and frappe.db.exists("Restaurant Modifier Group", linked_group):
			if linked_group not in group_doc_cache:
				group_doc_cache[linked_group] = frappe.get_doc("Restaurant Modifier Group", linked_group)
			group_doc = group_doc_cache[linked_group]

			selection_mode, required, min_select, max_select = _normalize_group_meta(
				group_doc.get("selection_mode"),
				group_doc.get("required"),
				group_doc.get("min_select"),
				group_doc.get("max_select"),
			)

			payload_group = grouped.setdefault(
				linked_group,
				{
					"group_name": linked_group,
					"title": (group_doc.get("title") or linked_group).strip(),
					"selection_mode": selection_mode,
					"required": required,
					"min_select": min_select,
					"max_select": max_select,
					"sort_order": cint(group_doc.get("sort_order") or row.get("idx") or 0),
					"options": [],
				},
			)
			if payload_group["options"]:
				continue

			for option_row in sorted(
				group_doc.get("options") or [],
				key=lambda d: (cint(d.get("sort_order") or 0), cint(d.get("idx") or 0)),
			):
				if option_row.get("is_active") not in ("", None) and cint(option_row.get("is_active")) == 0:
					continue
				_append_group_option(payload_group, option_row)
			continue

		group_name = (row.get("group_key") or row.get("group_title") or "").strip()
		if not group_name:
			continue

		group_title = (row.get("group_title") or group_name).strip()
		selection_mode, required, min_select, max_select = _normalize_group_meta(
			row.get("selection_mode"),
			row.get("required"),
			row.get("min_select"),
			row.get("max_select"),
		)

		payload_group = grouped.setdefault(
			group_name,
			{
				"group_name": group_name,
				"title": group_title,
				"selection_mode": selection_mode,
				"required": required,
				"min_select": min_select,
				"max_select": max_select,
				"sort_order": cint(row.get("sort_order") or row.get("idx") or 0),
				"options": [],
			},
		)

		_append_group_option(payload_group, row)

	for payload_group in sorted(
		grouped.values(),
		key=lambda d: (cint(d.get("sort_order") or 0), d.get("title") or d.get("group_name") or ""),
	):
		if not payload_group["options"]:
			continue
		option_map = {opt["name"]: opt for opt in payload_group["options"] if opt.get("name")}
		groups.append(payload_group)
		group_map[payload_group["group_name"]] = {
			"meta": payload_group,
			"options": option_map,
		}
		group_title_map[payload_group["title"]] = payload_group["group_name"]
		group_title_map[payload_group["group_name"]] = payload_group["group_name"]

	return groups, group_map, group_title_map


@frappe.whitelist(allow_guest=True)
def get_menu_boot(branch=None):
	branch = (branch or "").strip()
	try:
		return _get_core_menu_boot(branch=branch)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.get_menu_boot")
		raise


@frappe.whitelist(allow_guest=True)
def get_menu_items(category_slug=None, subcategory_slug=None, search=None, page=1, page_size=20, branch=None):
	try:
		return _get_core_menu_items(
			category_slug=category_slug,
			subcategory_slug=subcategory_slug,
			search=search,
			page=page,
			page_size=page_size,
			branch=branch,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.get_menu_items")
		return _get_menu_items_public_fallback(
			category_slug=category_slug,
			subcategory_slug=subcategory_slug,
			search=search,
			page=page,
			page_size=page_size,
			branch=branch,
		)


@frappe.whitelist(allow_guest=True)
def get_item_detail(item_slug, branch=None):
	_ensure_item_tags_field()
	try:
		return _get_core_item_detail(item_slug=item_slug, branch=branch)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.get_item_detail")
		raise


@frappe.whitelist(allow_guest=True)
def get_related_items(item_slug, limit=6, branch=None):
	_ensure_item_tags_field()
	slug = _normalize_slug(item_slug)
	if not slug:
		return []

	limit = max(1, min(cint(limit) or 6, 24))
	branch = (branch or "").strip()

	item_name = frappe.db.get_value(
		"Item",
		{
			"restaurant_slug": slug,
			**_core_item_filters(branch),
		},
		"name",
	)
	source_variant_name = ""
	if not item_name:
		item_name, source_variant_name = _resolve_variant_slug_to_context(slug=slug, branch=branch)
	if not item_name:
		return []

	template_doc = frappe.get_doc("Item", item_name)
	display_doc, _fixed_attribute_values = _resolve_display_doc_for_item_detail(
		template_doc,
		source_variant_name=source_variant_name,
		branch=branch,
	)

	category_meta_map = _get_core_category_meta_map()
	subcategory_meta_map = _get_core_subcategory_meta_map()
	current_names = {name for name in {template_doc.name, display_doc.name, source_variant_name} if name}
	current_slug = _normalize_slug(display_doc.get("restaurant_slug") or template_doc.get("restaurant_slug") or slug)
	current_tags = {
		tag.lower()
		for tag in (
			_split_tags(getattr(template_doc, "restaurant_item_tags", None))
			or _get_item_tag_titles(template_doc.name)
		)
		if tag
	}

	image_field = _core_item_image_field()
	item_fields = [
		"name",
		"item_code",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		f"{image_field} as image",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_sort_order",
	]
	for fieldname in _available_item_nutrition_fields():
		if fieldname not in item_fields:
			item_fields.append(fieldname)
	if _has_column("Item", "restaurant_coming_soon"):
		item_fields.append("restaurant_coming_soon")

	template_rows = frappe.get_all(
		"Item",
		filters=_core_item_filters(branch),
		fields=item_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit_page_length=5000,
	)

	expanded_rows = []
	for row in template_rows:
		if row.get("name") in current_names:
			continue
		expanded_rows.extend(_template_display_row_or_self(row, branch=branch))
	expanded_rows = _apply_menu_customization_flags(expanded_rows)

	scored_rows = []
	for row in expanded_rows:
		row_name = (row.get("name") or "").strip()
		row_slug = _normalize_slug(row.get("restaurant_slug") or "")
		if row_name in current_names or (row_slug and row_slug == current_slug):
			continue

		score = 0
		if (row.get("restaurant_subcategory") or "").strip() == (display_doc.get("restaurant_subcategory") or "").strip():
			score += 40
		if (row.get("restaurant_category") or "").strip() == (display_doc.get("restaurant_category") or "").strip():
			score += 20

		row_tags = {
			tag.lower()
			for tag in (
				_split_tags(getattr(row, "restaurant_item_tags", None))
				or _get_item_tag_titles(row_name)
			)
			if tag
		}
		score += min(len(current_tags & row_tags), 3) * 5

		if score <= 0:
			continue
		scored_rows.append((score, row))

	scored_rows.sort(
		key=lambda entry: (
			-entry[0],
			cint(entry[1].get("restaurant_sort_order") or 0),
			_variant_item_sort_key(entry[1].get("name") or ""),
			(entry[1].get("item_name") or ""),
		)
	)

	items = []
	seen_slugs = set()
	for _score, row in scored_rows:
		payload = _serialize_core_item(
			row,
			category_meta_map=category_meta_map,
			subcategory_meta_map=subcategory_meta_map,
		)
		payload_slug = _normalize_slug(payload.get("slug") or "")
		seen_key = payload_slug or (payload.get("name") or "")
		if not seen_key or seen_key in seen_slugs:
			continue
		seen_slugs.add(seen_key)
		items.append(payload)
		if len(items) >= limit:
			break

	return items


@frappe.whitelist(allow_guest=True)
def test_item_tags():
	"""Test endpoint to verify item tags field exists and works"""
	_ensure_item_tags_field()
	has_field = frappe.db.has_column("Item", "restaurant_item_tags")
	items = frappe.get_all(
		"Item",
		fields=["name", "item_name", "restaurant_item_tags"],
		limit=5,
	)
	return {
		"field_exists": has_field,
		"sample_items": [
			{"name": i.name, "title": i.item_name, "tags": i.restaurant_item_tags or ""} for i in items
		],
	}


@frappe.whitelist(allow_guest=True)
def set_item_tags(item_name, tags):
	"""Set tags for an item. Tags should be comma-separated."""
	if not frappe.db.has_column("Item", "restaurant_item_tags"):
		_ensure_item_tags_field()
	frappe.db.set_value("Item", item_name, "restaurant_item_tags", tags or "")
	frappe.db.commit()
	return {"status": "ok", "item": item_name, "tags": tags}


@frappe.whitelist(allow_guest=True)
def find_items_for_salad():
	"""Find items needed for protein salad"""
	terms = [
		"فیله مرغ",
		"سینه مرغ",
		"تخم مرغ",
		"خیار",
		"کاهو",
		"پنیر فتا",
		"آفتابگردان",
		"بادام",
		"کاسه کرافت",
		"سالاد",
		"مرغ",
	]
	results = {}
	for term in terms:
		items = frappe.get_all(
			"Item",
			fields=[
				"name",
				"item_name",
				"item_group",
				"stock_uom",
				"restaurant_nutrition_kcal",
				"restaurant_nutrition_protein_g",
				"restaurant_nutrition_carb_g",
				"restaurant_nutrition_fat_g",
			],
			filters={"item_name": ["like", f"%{term}%"], "disabled": 0},
			limit=5,
		)
		if items:
			results[term] = items
	return results


@frappe.whitelist(allow_guest=True)
def create_protein_salad():
	"""Create protein salad product with BOM"""
	frappe.set_user("Administrator")

	# Step 1: Create missing items
	new_items = [
		{
			"item_code": "فیله مرغ",
			"item_name": "فیله مرغ",
			"item_group": "مواد اولیه",
			"stock_uom": "گرم",
			"is_stock_item": 1,
			"restaurant_nutrition_kcal": 1.65,
			"restaurant_nutrition_protein_g": 0.31,
			"restaurant_nutrition_carb_g": 0,
			"restaurant_nutrition_fat_g": 0.036,
		},
		{
			"item_code": "تخم مرغ خالص",
			"item_name": "تخم مرغ خالص",
			"item_group": "مواد اولیه",
			"stock_uom": "عدد",
			"is_stock_item": 1,
			"restaurant_nutrition_kcal": 155.0,
			"restaurant_nutrition_protein_g": 12.5,
			"restaurant_nutrition_carb_g": 1.1,
			"restaurant_nutrition_fat_g": 11.0,
		},
		{
			"item_code": "پنیر فتا",
			"item_name": "پنیر فتا",
			"item_group": "مواد اولیه",
			"stock_uom": "گرم",
			"is_stock_item": 1,
			"restaurant_nutrition_kcal": 2.64,
			"restaurant_nutrition_protein_g": 0.14,
			"restaurant_nutrition_carb_g": 0.04,
			"restaurant_nutrition_fat_g": 0.21,
		},
		{
			"item_code": "تخمه آفتابگردان",
			"item_name": "تخمه آفتابگردان",
			"item_group": "مواد اولیه",
			"stock_uom": "گرم",
			"is_stock_item": 1,
			"restaurant_nutrition_kcal": 5.84,
			"restaurant_nutrition_protein_g": 0.21,
			"restaurant_nutrition_carb_g": 0.2,
			"restaurant_nutrition_fat_g": 0.51,
		},
		{
			"item_code": "بادام درختی",
			"item_name": "بادام درختی",
			"item_group": "مواد اولیه",
			"stock_uom": "گرم",
			"is_stock_item": 1,
			"restaurant_nutrition_kcal": 5.79,
			"restaurant_nutrition_protein_g": 0.21,
			"restaurant_nutrition_carb_g": 0.22,
			"restaurant_nutrition_fat_g": 0.49,
		},
	]

	created_items = []
	for item_data in new_items:
		if not frappe.db.exists("Item", item_data["item_code"]):
			doc = frappe.new_doc("Item")
			for key, value in item_data.items():
				setattr(doc, key, value)
			doc.insert(ignore_permissions=True)
			created_items.append(item_data["item_code"])

	frappe.db.commit()

	# Step 2: Create the salad product
	salad_name = "سالاد فیله پروتئینی"
	if not frappe.db.exists("Item", salad_name):
		salad = frappe.new_doc("Item")
		salad.item_code = salad_name
		salad.item_name = salad_name
		salad.item_group = "محصولات"
		salad.stock_uom = "عدد"
		salad.is_stock_item = 1
		salad.is_sales_item = 1
		salad.restaurant_enabled = 1
		salad.restaurant_category = (
			frappe.db.get_value("Item Group", {"name": ["like", "%سالاد%"]}, "name") or "محصولات"
		)
		salad.restaurant_slug = "protein-fillet-salad"
		salad.restaurant_short_desc = "سالاد فیله مرغ پروتئینی با کاهو، خیار، تخم مرغ، پنیر فتا و تخمه‌ها"
		salad.restaurant_item_tags = "رژیمی, پروتئینی, سالاد"
		salad.restaurant_nutrition_kcal = 0  # Will be calculated from BOM
		salad.restaurant_nutrition_protein_g = 0
		salad.insert(ignore_permissions=True)
	else:
		salad = frappe.get_doc("Item", salad_name)

	frappe.db.commit()

	# Step 3: Create BOM
	bom_name = f"BOM-{salad_name}-001"
	if not frappe.db.exists("BOM", bom_name):
		bom = frappe.new_doc("BOM")
		bom.item = salad_name
		bom.bom_name = bom_name
		bom.quantity = 1
		bom.uom = "عدد"
		bom.is_active = 1
		bom.is_default = 1
		bom.with_operations = 0
		bom.rm_cost_as_per = "Valuation Rate"

		# BOM items - quantities for one serving
		bom_items = [
			{"item_code": "فیله مرغ", "qty": 150, "uom": "گرم"},  # 150g chicken fillet
			{"item_code": "کاهو فرانسوی", "qty": 80, "uom": "گرم"},  # 80g lettuce
			{"item_code": "خیار", "qty": 60, "uom": "گرم"},  # 60g cucumber
			{"item_code": "تخم مرغ خالص", "qty": 2, "uom": "عدد"},  # 2 eggs
			{"item_code": "پنیر فتا", "qty": 30, "uom": "گرم"},  # 30g feta
			{"item_code": "تخمه آفتابگردان", "qty": 10, "uom": "گرم"},  # 10g sunflower seeds
			{"item_code": "بادام درختی", "qty": 10, "uom": "گرم"},  # 10g almonds
			{"item_code": "کاسه کرافت بزرگ", "qty": 1, "uom": "عدد"},  # 1 kraft bowl
		]

		for bi in bom_items:
			bom.append(
				"items",
				{
					"item_code": bi["item_code"],
					"qty": bi["qty"],
					"uom": bi["uom"],
					"rate": 0,
					"include_item_in_manufacturing": 1,
				},
			)

		bom.insert(ignore_permissions=True)
		bom.submit()
	else:
		bom = frappe.get_doc("BOM", bom_name)

	frappe.db.commit()

	# Step 4: Calculate nutrition from BOM
	from restaurant.api import _refresh_item_nutrition_from_bom, _upsert_bom_nutrition_fields

	_upsert_bom_nutrition_fields(bom)
	_refresh_item_nutrition_from_bom(salad_name)
	frappe.db.commit()

	# Get final nutrition
	salad.reload()
	return {
		"status": "ok",
		"created_items": created_items,
		"salad": salad_name,
		"bom": bom_name,
		"nutrition_kcal": salad.restaurant_nutrition_kcal,
		"nutrition_protein_g": salad.restaurant_nutrition_protein_g,
		"nutrition_carb_g": salad.restaurant_nutrition_carb_g,
		"nutrition_fat_g": salad.restaurant_nutrition_fat_g,
		"tags": salad.restaurant_item_tags,
	}


@frappe.whitelist(allow_guest=True)
def debug_salad():
	"""Debug salad item"""
	item = frappe.get_doc("Item", "سالاد فیله پروتئینی")
	boms = frappe.get_all(
		"BOM", filters={"item": item.name}, fields=["name", "is_active", "is_default", "docstatus"]
	)
	return {
		"name": item.name,
		"restaurant_enabled": item.restaurant_enabled,
		"restaurant_slug": item.restaurant_slug,
		"restaurant_category": item.restaurant_category,
		"restaurant_subcategory": item.restaurant_subcategory,
		"disabled": item.disabled,
		"is_sales_item": item.is_sales_item,
		"item_group": item.item_group,
		"tags": item.restaurant_item_tags,
		"bom": boms,
	}
	if len(mobile) < 10:
		frappe.throw(_("A valid mobile number is required."))
	return mobile


def _ensure_order_type(order_type):
	ot = (order_type or "").strip().lower()
	if ot not in ORDER_TYPES:
		frappe.throw(_("Invalid order type."))
	return ot


def _ensure_delivery_mode(mode):
	raw_mode = (mode or "").strip().lower()
	if raw_mode not in DELIVERY_MODES:
		frappe.throw(_("Invalid delivery mode."))
	return raw_mode


def _resolve_order_type_and_delivery_mode(order_type=None, delivery_mode=None):
	raw_mode = (delivery_mode or "").strip().lower()
	raw_order_type = (order_type or "").strip().lower()

	if raw_mode:
		mode = _ensure_delivery_mode(raw_mode)
		return ("delivery" if mode == "delivery" else "takeaway"), mode

	if raw_order_type:
		normalized = _ensure_order_type(raw_order_type)
		mode = "delivery" if normalized == "delivery" else "pickup"
		return normalized, mode

	return "takeaway", "pickup"


def _ensure_mobile(mobile, allow_empty=True):
	mobile = re.sub(r"\D+", "", str(mobile or ""))
	if not mobile:
		if allow_empty:
			return ""
		frappe.throw(_("A valid mobile number is required."))
	if mobile.startswith("98") and len(mobile) == 12:
		mobile = "0" + mobile[2:]
	if len(mobile) == 10 and mobile.startswith("9"):
		mobile = "0" + mobile
	# Legacy cleanup: fake mobile used to be default in older versions
	if mobile == "09120000000" and allow_empty:
		return ""
	if len(mobile) < 10:
		frappe.throw(_("A valid mobile number is required."))
	return mobile


def _find_customer_by_mobile(mobile):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	if not normalized_mobile:
		return ""

	if _has_column("Customer", "mobile_no"):
		existing = frappe.db.get_value("Customer", {"mobile_no": normalized_mobile, "disabled": 0}, "name")
		if existing:
			return existing

	if _has_column("Customer", "customer_primary_mobile"):
		existing = frappe.db.get_value(
			"Customer",
			{"customer_primary_mobile": normalized_mobile, "disabled": 0},
			"name",
		)
		if existing:
			return existing

	return ""


def _ensure_checkout_address_fields():
	if not frappe.db.exists("DocType", "Address"):
		return

	field_defs = [
		{
			"fieldname": "restaurant_location_section",
			"label": "Restaurant Location",
			"fieldtype": "Section Break",
			"insert_after": "phone",
		},
		{
			"fieldname": "restaurant_location_title",
			"label": "Location Title",
			"fieldtype": "Data",
			"insert_after": "restaurant_location_section",
		},
		{
			"fieldname": "restaurant_plaque",
			"label": "Plaque",
			"fieldtype": "Data",
			"insert_after": "restaurant_location_title",
		},
		{
			"fieldname": "restaurant_unit",
			"label": "Unit",
			"fieldtype": "Data",
			"insert_after": "restaurant_plaque",
		},
		{
			"fieldname": "restaurant_floor",
			"label": "Floor",
			"fieldtype": "Data",
			"insert_after": "restaurant_unit",
		},
		{
			"fieldname": "restaurant_latitude",
			"label": "Latitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_floor",
		},
		{
			"fieldname": "restaurant_longitude",
			"label": "Longitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_latitude",
		},
		{
			"fieldname": "restaurant_guidance_video",
			"label": "Guidance Video URL",
			"fieldtype": "Data",
			"insert_after": "restaurant_longitude",
		},
	]

	changed = False
	for field_def in field_defs:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Address", "fieldname": field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Address",
			"module": "Restaurant",
			**field_def,
		}

		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			dirty = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					dirty = True
			if dirty:
				doc.save(ignore_permissions=True)
				changed = True
			continue

		frappe.get_doc(payload).insert(ignore_permissions=True)
		changed = True

	if changed:
		frappe.clear_cache(doctype="Address")


def _ensure_checkout_sales_order_fields():
	global _CHECKOUT_SALES_ORDER_FIELDS_READY_SITES
	site_key = getattr(getattr(frappe, "local", None), "site", "__default__") or "__default__"
	if site_key in _CHECKOUT_SALES_ORDER_FIELDS_READY_SITES:
		return
	if not frappe.db.exists("DocType", "Sales Order"):
		return

	field_defs = [
		{
			"fieldname": "restaurant_delivery_address_name",
			"label": "Delivery Address",
			"fieldtype": "Link",
			"options": "Address",
			"insert_after": "restaurant_delivery_address",
		},
		{
			"fieldname": "restaurant_delivery_lat",
			"label": "Delivery Latitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_delivery_address_name",
		},
		{
			"fieldname": "restaurant_delivery_lng",
			"label": "Delivery Longitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_delivery_lat",
		},
		{
			"fieldname": "restaurant_delivery_details_json",
			"label": "Delivery Details JSON",
			"fieldtype": "Long Text",
			"insert_after": "restaurant_delivery_lng",
		},
		{
			"fieldname": "restaurant_order_context_json",
			"label": "Order Context JSON",
			"fieldtype": "Long Text",
			"insert_after": "restaurant_delivery_details_json",
		},
		{
			"fieldname": "restaurant_branch",
			"label": "Restaurant Branch",
			"fieldtype": "Link",
			"options": "Company",
			"insert_after": "restaurant_order_context_json",
		},
		{
			"fieldname": "restaurant_table",
			"label": "Restaurant Table",
			"fieldtype": "Data",
			"insert_after": "restaurant_branch",
		},
		{
			"fieldname": "restaurant_delivery_fee",
			"label": "Delivery Fee",
			"fieldtype": "Currency",
			"insert_after": "restaurant_table",
		},
	]

	changed = False
	for field_def in field_defs:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Sales Order", "fieldname": field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Sales Order",
			"module": "Restaurant",
			**field_def,
		}

		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			dirty = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					dirty = True
			if dirty:
				doc.save(ignore_permissions=True)
				changed = True
			continue

		frappe.get_doc(payload).insert(ignore_permissions=True)
		changed = True

	if changed:
		frappe.clear_cache(doctype="Sales Order")
	_CHECKOUT_SALES_ORDER_FIELDS_READY_SITES.add(site_key)


def _normalize_delivery_geo(lat_value, lng_value, required=False):
	lat = _to_bounded_float(lat_value, minimum=-90, maximum=90)
	lng = _to_bounded_float(lng_value, minimum=-180, maximum=180)
	if required and (lat is None or lng is None):
		frappe.throw(_("Delivery location is required for delivery orders."))
	return lat, lng


def _delivery_extra_line(payload):
	chunks = []
	if payload.get("plaque"):
		chunks.append(_("Plaque: {0}").format(payload.get("plaque")))
	if payload.get("unit"):
		chunks.append(_("Unit: {0}").format(payload.get("unit")))
	if payload.get("floor"):
		chunks.append(_("Floor: {0}").format(payload.get("floor")))
	return " - ".join(chunks)


def _format_delivery_text(payload):
	address_line = (payload.get("address_line") or "").strip()
	extra_line = _delivery_extra_line(payload)
	if address_line and extra_line:
		return f"{address_line}\n{extra_line}"
	return address_line or extra_line


def _serialize_address_payload(row):
	address_line = (row.get("address_line1") or "").strip()
	address_line2 = (row.get("address_line2") or "").strip()
	if not address_line and address_line2:
		address_line = address_line2
	elif address_line and address_line2:
		address_line = f"{address_line} - {address_line2}"

	lat = _to_bounded_float(
		_first_non_empty(
			row.get("restaurant_latitude"),
			row.get("latitude"),
		),
		minimum=-90,
		maximum=90,
	)
	lng = _to_bounded_float(
		_first_non_empty(
			row.get("restaurant_longitude"),
			row.get("longitude"),
		),
		minimum=-180,
		maximum=180,
	)

	return {
		"id": row.get("name") or "",
		"title": (row.get("restaurant_location_title") or row.get("address_title") or "").strip(),
		"phone": (row.get("phone") or "").strip(),
		"address_line": address_line,
		"plaque": (row.get("restaurant_plaque") or "").strip(),
		"unit": (row.get("restaurant_unit") or "").strip(),
		"floor": (row.get("restaurant_floor") or "").strip(),
		"lat": lat,
		"lng": lng,
		"is_primary": cint(row.get("is_primary_address") or 0),
		"video_url": (row.get("restaurant_guidance_video") or "").strip(),
		"updated_at": _json_safe_datetime(row.get("modified")),
	}


def _customer_address_names(customer_name):
	if not customer_name or not frappe.db.exists("DocType", "Dynamic Link"):
		return []
	rows = frappe.get_all(
		"Dynamic Link",
		fields=["parent"],
		filters={
			"parenttype": "Address",
			"link_doctype": "Customer",
			"link_name": customer_name,
		},
		ignore_permissions=True,
	)
	return [row.parent for row in rows if row.get("parent")]


def _list_customer_delivery_addresses(customer_name):
	names = _customer_address_names(customer_name)
	if not names:
		return []

	_ensure_checkout_address_fields()
	fields = [
		"name",
		"address_title",
		"address_line1",
		"address_line2",
		"phone",
		"modified",
	]
	optional_fields = [
		"is_primary_address",
		"restaurant_location_title",
		"restaurant_plaque",
		"restaurant_unit",
		"restaurant_floor",
		"restaurant_latitude",
		"restaurant_longitude",
		"restaurant_guidance_video",
		"latitude",
		"longitude",
	]
	for fieldname in optional_fields:
		if _has_column("Address", fieldname):
			fields.append(fieldname)

	rows = frappe.get_all(
		"Address",
		fields=fields,
		filters={"name": ["in", names]},
		order_by="modified desc",
		ignore_permissions=True,
	)
	payload = [_serialize_address_payload(row) for row in rows]
	payload = sorted(
		payload,
		key=lambda row: (cint(row.get("is_primary") or 0), row.get("updated_at") or ""),
		reverse=True,
	)
	return payload


def _normalize_address_payload(address_info, customer_name, mobile):
	info = _parse_json(address_info, {})
	if not isinstance(info, dict):
		info = {}

	title = (info.get("title") or info.get("address_title") or "").strip()
	if not title:
		title = _("Address of {0}").format(customer_name)
	phone = _ensure_mobile(info.get("phone") or info.get("mobile") or mobile)
	address_line = (
		info.get("address_line") or info.get("address") or info.get("address_line1") or ""
	).strip()
	plaque = (info.get("plaque") or "").strip()
	unit = (info.get("unit") or "").strip()
	floor = (info.get("floor") or "").strip()
	lat, lng = _normalize_delivery_geo(
		_first_non_empty(info.get("lat"), info.get("latitude")),
		_first_non_empty(info.get("lng"), info.get("longitude")),
		required=True,
	)
	is_primary = cint(info.get("is_primary") or info.get("is_primary_address") or 0)
	video_url = _first_non_empty(info.get("video_url"), info.get("guidance_video"), info.get("video")) or ""
	video_url = str(video_url).strip()

	if not address_line:
		frappe.throw(_("Address line is required for delivery."))

	return {
		"id": (info.get("id") or info.get("name") or info.get("address_id") or "").strip(),
		"title": title,
		"phone": phone,
		"address_line": address_line,
		"plaque": plaque,
		"unit": unit,
		"floor": floor,
		"lat": lat,
		"lng": lng,
		"is_primary": is_primary,
		"video_url": video_url,
	}


def _upsert_customer_delivery_address(customer_name, normalized_info):
	_ensure_checkout_address_fields()
	address_name = (normalized_info.get("id") or "").strip()
	customer_addresses = set(_customer_address_names(customer_name))

	if address_name and address_name not in customer_addresses:
		frappe.throw(_("Selected address does not belong to this customer."))

	if address_name and frappe.db.exists("Address", address_name):
		doc = frappe.get_doc("Address", address_name)
	else:
		doc = frappe.get_doc({"doctype": "Address"})

	doc.address_title = normalized_info["title"]
	doc.address_type = "Shipping"
	doc.address_line1 = normalized_info["address_line"]
	doc.address_line2 = _delivery_extra_line(normalized_info)
	doc.phone = normalized_info["phone"]

	if _has_column("Address", "is_shipping_address"):
		doc.set("is_shipping_address", 1)
	if _has_column("Address", "is_primary_address"):
		doc.set("is_primary_address", cint(normalized_info.get("is_primary") or 0))

	if _has_column("Address", "restaurant_location_title"):
		doc.set("restaurant_location_title", normalized_info["title"])
	if _has_column("Address", "restaurant_plaque"):
		doc.set("restaurant_plaque", normalized_info["plaque"])
	if _has_column("Address", "restaurant_unit"):
		doc.set("restaurant_unit", normalized_info["unit"])
	if _has_column("Address", "restaurant_floor"):
		doc.set("restaurant_floor", normalized_info["floor"])
	if _has_column("Address", "restaurant_latitude"):
		doc.set("restaurant_latitude", normalized_info["lat"])
	if _has_column("Address", "restaurant_longitude"):
		doc.set("restaurant_longitude", normalized_info["lng"])
	if _has_column("Address", "latitude"):
		doc.set("latitude", normalized_info["lat"])
	if _has_column("Address", "longitude"):
		doc.set("longitude", normalized_info["lng"])
	if _has_column("Address", "restaurant_guidance_video"):
		doc.set("restaurant_guidance_video", normalized_info.get("video_url") or "")

	links = doc.get("links") or []
	has_customer_link = any(
		row.get("link_doctype") == "Customer" and row.get("link_name") == customer_name for row in links
	)
	if not has_customer_link:
		doc.append(
			"links",
			{
				"link_doctype": "Customer",
				"link_name": customer_name,
				"link_title": customer_name,
			},
		)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	if cint(normalized_info.get("is_primary") or 0) == 1 and _has_column("Address", "is_primary_address"):
		for sibling_name in customer_addresses:
			if sibling_name == doc.name:
				continue
			if frappe.db.exists("Address", sibling_name):
				frappe.db.set_value("Address", sibling_name, "is_primary_address", 0, update_modified=False)

	return _serialize_address_payload(doc.as_dict())


def _vehicle_doctype_ready():
	try:
		return bool(
			frappe.db.exists("DocType", "Restaurant Customer Vehicle")
			and frappe.db.sql("SHOW TABLES LIKE %s", "tabRestaurant Customer Vehicle")
		)
	except Exception:
		return False


def _serialize_customer_vehicle(row):
	return {
		"id": row.get("name") or "",
		"customer": row.get("customer") or "",
		"mobile": row.get("mobile") or "",
		"title": row.get("title") or "",
		"type": row.get("vehicle_type") or "",
		"color": row.get("color") or "",
		"plate": row.get("plate_number") or "",
		"is_primary": cint(row.get("is_primary") or 0),
		"is_active": cint(row.get("is_active") or 0),
		"last_used_at": row.get("last_used_at") or "",
		"updated_at": row.get("modified") or "",
		"notes": row.get("notes") or "",
	}


def _list_customer_vehicles(customer_name=None, mobile=None):
	if not _vehicle_doctype_ready():
		return []

	filters = {"is_active": 1}
	if customer_name:
		filters["customer"] = customer_name
	elif mobile:
		filters["mobile"] = _ensure_mobile(mobile)
	else:
		return []

	rows = frappe.get_all(
		"Restaurant Customer Vehicle",
		filters=filters,
		fields=[
			"name",
			"customer",
			"mobile",
			"title",
			"vehicle_type",
			"color",
			"plate_number",
			"is_primary",
			"is_active",
			"last_used_at",
			"modified",
			"notes",
		],
		order_by="is_primary desc, last_used_at desc, modified desc",
		ignore_permissions=True,
	)
	return [_serialize_customer_vehicle(row) for row in rows]


def _normalize_vehicle_payload(vehicle_info, customer_name, mobile):
	info = _parse_json(vehicle_info, {})
	if not isinstance(info, dict):
		info = {}

	vehicle_type = (info.get("type") or info.get("vehicle_type") or "").strip()
	color = (info.get("color") or "").strip()
	plate = (info.get("plate") or info.get("plate_number") or "").strip()
	title = (info.get("title") or "").strip()
	if not vehicle_type:
		frappe.throw(_("Vehicle type is required."))
	if not color:
		frappe.throw(_("Vehicle color is required."))
	if not plate:
		frappe.throw(_("Vehicle plate number is required."))
	if not title:
		title = f"{vehicle_type} - {plate}"

	return {
		"id": (info.get("id") or info.get("name") or info.get("vehicle_id") or "").strip(),
		"customer": customer_name,
		"mobile": _ensure_mobile(info.get("mobile") or mobile),
		"title": title,
		"vehicle_type": vehicle_type,
		"color": color,
		"plate_number": plate,
		"is_primary": cint(info.get("is_primary") or 0),
		"notes": (info.get("notes") or "").strip(),
	}


def _upsert_customer_vehicle(customer_name, normalized_info, mark_used=False):
	if not _vehicle_doctype_ready():
		frappe.throw(_("Vehicle storage is not installed. Please run migrate."))

	vehicle_name = (normalized_info.get("id") or "").strip()
	if vehicle_name:
		owner_customer = frappe.db.get_value("Restaurant Customer Vehicle", vehicle_name, "customer")
		if owner_customer and owner_customer != customer_name:
			frappe.throw(_("Selected vehicle does not belong to this customer."))

	if vehicle_name and frappe.db.exists("Restaurant Customer Vehicle", vehicle_name):
		doc = frappe.get_doc("Restaurant Customer Vehicle", vehicle_name)
	else:
		doc = frappe.new_doc("Restaurant Customer Vehicle")

	doc.customer = customer_name
	doc.mobile = normalized_info["mobile"]
	doc.title = normalized_info["title"]
	doc.vehicle_type = normalized_info["vehicle_type"]
	doc.color = normalized_info["color"]
	doc.plate_number = normalized_info["plate_number"]
	doc.is_primary = cint(normalized_info.get("is_primary") or 0)
	doc.is_active = 1
	doc.notes = normalized_info.get("notes") or ""
	if mark_used:
		doc.last_used_at = now_datetime()

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	if cint(doc.is_primary or 0) == 1:
		for sibling in frappe.get_all(
			"Restaurant Customer Vehicle",
			filters={"customer": customer_name, "name": ["!=", doc.name]},
			pluck="name",
			ignore_permissions=True,
		):
			frappe.db.set_value(
				"Restaurant Customer Vehicle", sibling, "is_primary", 0, update_modified=False
			)

	return _serialize_customer_vehicle(doc.as_dict())


def _resolve_customer_vehicle_for_order(customer_name, mobile, vehicle_id=None, vehicle_snapshot=None):
	if not _vehicle_doctype_ready():
		return {}

	vehicle_id = (vehicle_id or "").strip()
	snapshot = _parse_json(vehicle_snapshot, {})
	if not isinstance(snapshot, dict):
		snapshot = {}

	vehicle_payload = {}
	if vehicle_id:
		rows = [
			row for row in _list_customer_vehicles(customer_name=customer_name) if row.get("id") == vehicle_id
		]
		if not rows:
			frappe.throw(_("Pickup vehicle not found for this customer."))
		vehicle_payload = dict(rows[0])

	merged = {
		**vehicle_payload,
		"id": vehicle_id or snapshot.get("id") or vehicle_payload.get("id") or "",
		"title": _first_non_empty(snapshot.get("title"), vehicle_payload.get("title"), ""),
		"type": _first_non_empty(
			snapshot.get("type"), snapshot.get("vehicle_type"), vehicle_payload.get("type"), ""
		),
		"color": _first_non_empty(snapshot.get("color"), vehicle_payload.get("color"), ""),
		"plate": _first_non_empty(
			snapshot.get("plate"), snapshot.get("plate_number"), vehicle_payload.get("plate"), ""
		),
		"is_primary": snapshot.get("is_primary") or vehicle_payload.get("is_primary") or 0,
		"notes": _first_non_empty(snapshot.get("notes"), vehicle_payload.get("notes"), ""),
	}
	normalized = _normalize_vehicle_payload(merged, customer_name=customer_name, mobile=mobile)
	return _upsert_customer_vehicle(customer_name, normalized, mark_used=True)


def _resolve_delivery_address_for_order(
	customer_name,
	mobile,
	delivery_address_id="",
	delivery_snapshot=None,
	legacy_address="",
	customer_display_name="",
):
	snapshot_payload = _parse_json(delivery_snapshot, {})
	if not isinstance(snapshot_payload, dict):
		snapshot_payload = {}

	address_payload = {}
	if delivery_address_id:
		address_rows = [
			row
			for row in _list_customer_delivery_addresses(customer_name)
			if row.get("id") == delivery_address_id
		]
		if not address_rows:
			frappe.throw(_("Delivery address not found for this customer."))
		address_payload = dict(address_rows[0])

	merged_payload = {
		**address_payload,
		"title": _first_non_empty(snapshot_payload.get("title"), address_payload.get("title"), ""),
		"phone": _first_non_empty(
			snapshot_payload.get("phone"),
			snapshot_payload.get("mobile"),
			address_payload.get("phone"),
			mobile,
		),
		"address_line": _first_non_empty(
			snapshot_payload.get("address_line"),
			snapshot_payload.get("address"),
			address_payload.get("address_line"),
			legacy_address,
		),
		"plaque": _first_non_empty(snapshot_payload.get("plaque"), address_payload.get("plaque"), ""),
		"unit": _first_non_empty(snapshot_payload.get("unit"), address_payload.get("unit"), ""),
		"floor": _first_non_empty(snapshot_payload.get("floor"), address_payload.get("floor"), ""),
		"lat": _first_non_empty(
			snapshot_payload.get("lat"),
			snapshot_payload.get("latitude"),
			address_payload.get("lat"),
		),
		"lng": _first_non_empty(
			snapshot_payload.get("lng"),
			snapshot_payload.get("longitude"),
			address_payload.get("lng"),
		),
	}
	normalized = _normalize_address_payload(
		merged_payload,
		customer_name=customer_display_name or customer_name,
		mobile=mobile,
	)

	if not normalized.get("id") and delivery_address_id:
		normalized["id"] = delivery_address_id
	if not normalized.get("id"):
		saved = _upsert_customer_delivery_address(customer_name, normalized)
		return saved
	return normalized


def _normalize_cart_items(items):
	rows = _parse_json(items, [])
	if not isinstance(rows, list) or not rows:
		frappe.throw(_("At least one item is required."))
	return rows


def _get_item_doc_by_payload(item_payload):
	slug = _normalize_slug(
		item_payload.get("item_slug") or item_payload.get("menu_item_slug") or item_payload.get("slug")
	)
	if not slug:
		frappe.throw(_("Each cart line must contain item_slug."))

	item_name = frappe.db.get_value(
		"Item",
		{
			"restaurant_slug": slug,
			**_core_item_filters(),
		},
		"name",
	)
	if not item_name:
		branch = (item_payload.get("branch") or "").strip()
		parent_name, variant_name = _resolve_variant_slug_to_context(slug=slug, branch=branch)
		# For cart payload, we WANT the variant itself, not the parent!
		item_name = variant_name if variant_name else parent_name
	
	if not item_name:
		# Final fallback: Try to look it up by actual Name directly.
		if frappe.db.exists("Item", slug):
			item_name = slug
	
	if not item_name:
		frappe.throw(_("Menu item not found: {0}").format(slug), frappe.DoesNotExistError)
	return frappe.get_doc("Item", item_name)


def _item_variant_attribute_rows(item_name):
	item_name = (item_name or "").strip()
	if not item_name:
		return []
	try:
		rows = frappe.get_all(
			"Item Variant Attribute",
			filters={"parent": item_name, "parenttype": "Item"},
			fields=["attribute", "attribute_value", "idx"],
			ignore_permissions=True,
			order_by="idx asc",
		)
	except Exception:
		return []
	return rows or []


def _item_variant_attribute_map(item_name):
	mapping = {}
	for row in _item_variant_attribute_rows(item_name):
		attribute_name = (row.get("attribute") or "").strip()
		value_name = (row.get("attribute_value") or "").strip()
		if attribute_name and value_name:
			mapping[attribute_name] = value_name
	return mapping


def _item_attribute_flags(attribute_name):
	attribute_name = (attribute_name or "").strip()
	if not attribute_name:
		return {"show_in_website": 1, "selection_only": 0}

	show_on_website = 1
	selection_only = 0
	if _has_column("Item Attribute", "restaurant_show_in_website"):
		raw_show = frappe.db.get_value("Item Attribute", attribute_name, "restaurant_show_in_website")
		show_on_website = 1 if raw_show in ("", None) else cint(raw_show)
	if _has_column("Item Attribute", "restaurant_selection_only"):
		selection_only = cint(
			frappe.db.get_value("Item Attribute", attribute_name, "restaurant_selection_only") or 0
		)
	return {
		"show_in_website": show_on_website,
		"selection_only": selection_only,
	}


def _item_attribute_default_value(attribute_name, allowed_values=None):
	attribute_name = (attribute_name or "").strip()
	if not attribute_name:
		return ""

	normalized_allowed = None
	if allowed_values is not None:
		normalized_allowed = {
			str(value or "").strip() for value in allowed_values if str(value or "").strip()
		}
		if not normalized_allowed:
			return ""

	rows = frappe.get_all(
		"Item Attribute Value",
		filters={"parent": attribute_name},
		fields=["attribute_value", "idx"],
		ignore_permissions=True,
		order_by="idx asc",
	)
	first_candidate = ""
	for row in rows:
		value_name = (row.get("attribute_value") or "").strip()
		if not value_name:
			continue
		if normalized_allowed is not None and value_name not in normalized_allowed:
			continue
		if not first_candidate:
			first_candidate = value_name
		if _has_column("Item Attribute Value", "restaurant_is_default"):
			is_default = cint(
				frappe.db.get_value(
					"Item Attribute Value",
					{"parent": attribute_name, "attribute_value": value_name},
					"restaurant_is_default",
				)
				or 0
			)
			if is_default:
				return value_name
	return first_candidate


def _variant_attribute_value_sort_key(attribute_name, value_name):
	value_name = (value_name or "").strip()
	if not value_name:
		return (1, 0, "", 0)

	row = (
		frappe.db.get_value(
			"Item Attribute Value",
			{"parent": attribute_name, "attribute_value": value_name},
			["idx", "abbr"],
			as_dict=True,
		)
		or {}
	)
	return (1, cint(row.get("idx") or 0), value_name, 0)


def _variant_item_sort_key(item_name):
	rows = _item_variant_attribute_rows(item_name)
	order_chunks = []
	for row in rows:
		attribute_name = (row.get("attribute") or "").strip()
		value_name = (row.get("attribute_value") or "").strip()
		flags = _item_attribute_flags(attribute_name)
		show_on_website = cint(flags.get("show_in_website") or 0)
		selection_only = cint(flags.get("selection_only") or 0)
		if not show_on_website or selection_only:
			continue

		default_flag = 0
		if _has_column("Item Attribute Value", "restaurant_is_default"):
			default_flag = cint(
				frappe.db.get_value(
					"Item Attribute Value",
					{"parent": attribute_name, "attribute_value": value_name},
					"restaurant_is_default",
				)
				or 0
			)
		sort_key = _variant_attribute_value_sort_key(attribute_name, value_name)
		order_chunks.append((default_flag, sort_key))

	if not order_chunks:
		return (0, item_name)

	default_rank = 0 if all(cint(flag) == 1 for flag, _key in order_chunks) else 1
	values_rank = tuple(key for _flag, key in order_chunks)
	return (default_rank, values_rank, item_name)


def _variant_attribute_public_payload(item_name):
	rows = _item_variant_attribute_rows(item_name)
	payload = []
	for row in rows:
		attribute_name = (row.get("attribute") or "").strip()
		value_name = (row.get("attribute_value") or "").strip()
		if not attribute_name or not value_name:
			continue

		flags = _item_attribute_flags(attribute_name)
		show_on_website = cint(flags.get("show_in_website") or 0)
		selection_only = cint(flags.get("selection_only") or 0)
		if not show_on_website:
			continue

		value_doc = (
			frappe.db.get_value(
				"Item Attribute Value",
				{"parent": attribute_name, "attribute_value": value_name},
				["abbr", "idx"],
				as_dict=True,
			)
			or {}
		)
		is_default = 0
		if _has_column("Item Attribute Value", "restaurant_is_default"):
			is_default = cint(
				frappe.db.get_value(
					"Item Attribute Value",
					{"parent": attribute_name, "attribute_value": value_name},
					"restaurant_is_default",
				)
				or 0
			)

		payload.append(
			{
				"attribute": attribute_name,
				"value": value_name,
				"abbr": (value_doc.get("abbr") or "").strip(),
				"sort_order": cint(value_doc.get("idx") or 0),
				"is_default": is_default,
				"selection_only": selection_only,
				"show_in_website": show_on_website,
			}
		)
	return payload


def _variant_display_title(template_doc, fixed_attribute_values=None, representative_item_name=""):
	base_title = ((template_doc.get("item_name") if template_doc else "") or "").strip()

	fixed_map = {}
	if isinstance(fixed_attribute_values, dict):
		for key, value in fixed_attribute_values.items():
			attribute_name = str(key or "").strip()
			attribute_value = str(value or "").strip()
			if attribute_name and attribute_value:
				fixed_map[attribute_name] = attribute_value

	if not fixed_map:
		return base_title

	attribute_order = []
	representative_item_name = (representative_item_name or "").strip()
	if representative_item_name:
		for row in _item_variant_attribute_rows(representative_item_name):
			attribute_name = (row.get("attribute") or "").strip()
			if attribute_name and attribute_name in fixed_map and attribute_name not in attribute_order:
				attribute_order.append(attribute_name)
	if not attribute_order:
		attribute_order = sorted(fixed_map.keys())

	lowered_base_title = base_title.lower()
	title_chunks = []
	for attribute_name in attribute_order:
		attribute_value = (fixed_map.get(attribute_name) or "").strip()
		if not attribute_value:
			continue
		if lowered_base_title and attribute_value.lower() in lowered_base_title:
			continue
		title_chunks.append(attribute_value)

	suffix = " ".join(title_chunks).strip()
	if not suffix:
		return base_title
	if not base_title:
		return suffix
	return f"{base_title} {suffix}".strip()


def _variant_selection_groups(template_item_name, all_variant_rows, fixed_attribute_values=None):
	groups = []
	if not template_item_name:
		return groups

	if not all_variant_rows:
		return groups

	fixed_map = {}
	if isinstance(fixed_attribute_values, dict):
		for key, value in fixed_attribute_values.items():
			attr_name = str(key or "").strip()
			attr_value = str(value or "").strip()
			if attr_name and attr_value:
				fixed_map[attr_name] = attr_value

	has_default_value = _has_column("Item Attribute Value", "restaurant_is_default")

	candidate_variants = []
	attribute_names = set()
	for row in all_variant_rows:
		variant_name = (row.get("name") or "").strip()
		if not variant_name:
			continue
		attr_map = _item_variant_attribute_map(variant_name)
		if fixed_map and any((attr_map.get(key) or "") != value for key, value in fixed_map.items()):
			continue
		candidate_variants.append({"name": variant_name, "attr_map": attr_map})
		for attr_name in attr_map:
			attribute_names.add(attr_name)

	if not candidate_variants:
		return groups

	for attribute_name in sorted(attribute_names):
		flags = _item_attribute_flags(attribute_name)
		show_on_website = cint(flags.get("show_in_website") or 0)
		selection_only = cint(flags.get("selection_only") or 0)

		if not show_on_website or not selection_only:
			continue

		available_values = {
			(variant.get("attr_map") or {}).get(attribute_name, "") for variant in candidate_variants
		}
		available_values = {value for value in available_values if value}
		if not available_values:
			continue

		option_rows = []
		value_rows = frappe.get_all(
			"Item Attribute Value",
			filters={"parent": attribute_name},
			fields=["attribute_value", "abbr", "idx"],
			ignore_permissions=True,
			order_by="idx asc",
		)
		for value_row in value_rows:
			value_name = (value_row.get("attribute_value") or "").strip()
			if not value_name or value_name not in available_values:
				continue
			default_flag = 0
			if has_default_value:
				default_flag = cint(
					frappe.db.get_value(
						"Item Attribute Value",
						{"parent": attribute_name, "attribute_value": value_name},
						"restaurant_is_default",
					)
					or 0
				)
			option_rows.append(
				{
					"name": value_name,
					"label": value_name,
					"value": value_name,
					"is_default": default_flag,
					"sort_order": cint(value_row.get("idx") or 0),
					"abbr": (value_row.get("abbr") or "").strip(),
					"price_delta": 0,
					"action_type": "variant_selection",
					"modifier_type": "variant_selection",
					"min_qty": 1,
					"max_qty": 1,
					"qty_step": 1,
					"option_qty": 1,
				}
			)

		if not option_rows:
			continue

		groups.append(
			{
				"group_name": f"variant::{attribute_name}",
				"title": attribute_name,
				"selection_mode": "single",
				"required": 1,
				"min_select": 1,
				"max_select": 1,
				"sort_order": 9999,
				"is_variant_attribute_selector": 1,
				"attribute_name": attribute_name,
				"options": option_rows,
			}
		)

	return groups


def _resolve_variant_item_for_customization(menu_doc, customization):
	if menu_doc.doctype != "Item":
		return None
	if not _has_column("Item", "has_variants") or not _has_column("Item", "variant_of"):
		return None
	if not cint(menu_doc.get("has_variants")):
		return None

	fixed_map = {}
	raw_fixed = (customization or {}).get("variant_fixed_attributes")
	if isinstance(raw_fixed, dict):
		for key, value in raw_fixed.items():
			attr_name = str(key or "").strip()
			attr_value = str(value or "").strip()
			if attr_name and attr_value:
				fixed_map[attr_name] = attr_value

	normalized_modifiers = _normalize_selected_modifiers((customization or {}).get("selected_modifiers"))
	selected_by_attribute = {}
	for row in normalized_modifiers:
		group_name = (row.get("group") or "").strip()
		if not group_name.startswith("variant::"):
			continue
		attribute_name = group_name.split("variant::", 1)[1].strip()
		option_value = (row.get("option") or "").strip()
		if attribute_name and option_value:
			selected_by_attribute[attribute_name] = option_value

	variants = frappe.get_all(
		"Item",
		filters={
			"variant_of": menu_doc.name,
			"disabled": 0,
			"restaurant_enabled": 1,
		},
		fields=["name", "item_code", "item_name", "restaurant_slug"],
		ignore_permissions=True,
		limit_page_length=500,
		order_by="modified desc",
	)
	if not variants:
		return None

	selection_attributes = {}
	variant_maps = {}
	for variant in variants:
		variant_name = (variant.get("name") or "").strip()
		if not variant_name:
			continue
		attrs = _item_variant_attribute_map(variant_name)
		variant_maps[variant_name] = attrs
		for attr_name, attr_value in attrs.items():
			flags = _item_attribute_flags(attr_name)
			if not cint(flags.get("show_in_website") or 0):
				continue
			if not cint(flags.get("selection_only") or 0):
				continue
			selection_attributes.setdefault(attr_name, set()).add(attr_value)

	completed_selection = dict(selected_by_attribute)
	for attr_name, values in selection_attributes.items():
		if completed_selection.get(attr_name):
			continue
		default_value = _item_attribute_default_value(attr_name, allowed_values=values)
		if default_value:
			completed_selection[attr_name] = default_value

	target_attrs = {}
	target_attrs.update(fixed_map)
	target_attrs.update(completed_selection)

	for variant in variants:
		variant_name = (variant.get("name") or "").strip()
		attrs = variant_maps.get(variant_name) or {}
		if all((attrs.get(attr_name) or "") == attr_value for attr_name, attr_value in target_attrs.items()):
			return frappe.get_doc("Item", variant.name)

	if target_attrs:
		frappe.throw(_("No Item Variant matches selected attributes."))
	return None


def _resolve_menu_item_name_from_variant_slug(slug, branch=None):
	normalized = _normalize_slug(slug)
	if not normalized and not slug:
		return ""

	variant_name = frappe.db.get_value(
		"Item",
		{
			"restaurant_slug": normalized or slug,
			"disabled": 0,
			"restaurant_enabled": 1,
		},
		"name",
	)
	
	if not variant_name and slug:
		variant_name = frappe.db.get_value(
			"Item",
			{
				"name": slug,
				"disabled": 0,
				"restaurant_enabled": 1,
			},
			"name",
		)
		
	if not variant_name:
		return ""

	variant_of = (frappe.db.get_value("Item", variant_name, "variant_of") or "").strip()
	if not variant_of:
		return variant_name

	if branch and _has_column("Item", "restaurant_branch"):
		parent_branch = (frappe.db.get_value("Item", variant_of, "restaurant_branch") or "").strip()
		if parent_branch and parent_branch != branch:
			return ""
	return variant_of


def _resolve_variant_slug_to_context(slug, branch=None):
	normalized = _normalize_slug(slug)
	if not normalized and not slug:
		return ("", "")

	direct_name = frappe.db.get_value(
		"Item",
		{
			"restaurant_slug": normalized or slug,
			"disabled": 0,
			"restaurant_enabled": 1,
		},
		"name",
	)
	
	if not direct_name and slug:
		direct_name = frappe.db.get_value(
			"Item",
			{
				"name": slug,
				"disabled": 0,
				"restaurant_enabled": 1,
			},
			"name",
		)
		
	if not direct_name:
		return ("", "")

	variant_of = (frappe.db.get_value("Item", direct_name, "variant_of") or "").strip()
	if not variant_of:
		return (direct_name, "")

	if branch and _has_column("Item", "restaurant_branch"):
		parent_branch = (frappe.db.get_value("Item", variant_of, "restaurant_branch") or "").strip()
		if parent_branch and parent_branch != branch:
			return ("", "")
	return (variant_of, direct_name)


def _template_display_variants(template_doc, branch=None):
	if not template_doc:
		return []
	if not _has_column("Item", "variant_of"):
		return []
	if not cint(template_doc.get("has_variants") or 0):
		return []

	filters = {
		"variant_of": template_doc.name,
		"disabled": 0,
		"restaurant_enabled": 1,
	}
	branch = (branch or "").strip()
	if branch and _has_column("Item", "restaurant_branch"):
		filters["restaurant_branch"] = ["in", [branch, ""]]

	image_field = _core_item_image_field()
	variants = frappe.get_all(
		"Item",
		filters=filters,
		fields=[
			"name",
			"item_code",
			"item_name",
			"restaurant_slug",
			"restaurant_short_desc",
			"restaurant_base_price",
			"standard_rate",
			"restaurant_enabled",
			"disabled",
			"restaurant_category",
			"restaurant_subcategory",
			"restaurant_sort_order",
			f"{image_field} as image",
		],
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit_page_length=1000,
	)

	grouped = {}
	for variant in variants:
		attr_map = _item_variant_attribute_map(variant.get("name"))
		signature = []
		fixed_map = {}
		for attr_name, attr_value in attr_map.items():
			flags = _item_attribute_flags(attr_name)
			if not cint(flags.get("show_in_website") or 0):
				continue
			if cint(flags.get("selection_only") or 0):
				continue
			signature.append((attr_name, attr_value))
			fixed_map[attr_name] = attr_value

		signature_key = tuple(sorted(signature))
		bucket = grouped.setdefault(signature_key, {"fixed": fixed_map, "variants": []})
		bucket["variants"].append(variant)

	display_rows = []
	for bucket in grouped.values():
		reps = sorted(
			bucket["variants"],
			key=lambda row: _variant_item_sort_key(row.get("name")),
		)
		representative = reps[0] if reps else None
		if not representative:
			continue
		payload = dict(representative)
		display_title = _variant_display_title(
			template_doc,
			fixed_attribute_values=bucket.get("fixed") or {},
			representative_item_name=representative.get("name"),
		)
		if display_title:
			payload["item_name"] = display_title
		payload["variant_of"] = template_doc.name
		payload["variant_fixed_attributes"] = bucket.get("fixed") or {}
		payload["variant_attributes"] = _variant_attribute_public_payload(representative.get("name"))
		payload["variant_source_item"] = representative.get("name")
		display_rows.append(frappe._dict(payload))

	return display_rows


def _template_display_row_or_self(template_row, branch=None):
	if not template_row:
		return []

	template_name = (
		template_row.get("name") if hasattr(template_row, "get") else getattr(template_row, "name", "")
	) or ""
	if not template_name:
		return []

	template_doc = frappe.get_doc("Item", template_name)
	rows = _template_display_variants(template_doc, branch=branch)
	if rows:
		return rows

	payload = frappe._dict(dict(template_row))
	payload["variant_of"] = ""
	payload["variant_fixed_attributes"] = {}
	payload["variant_attributes"] = []
	payload["variant_source_item"] = payload.get("name") or ""
	if "restaurant_coming_soon" not in payload and template_row.get("restaurant_coming_soon") is not None:
		payload["restaurant_coming_soon"] = template_row.get("restaurant_coming_soon")
	return [payload]


def _resolve_display_doc_for_item_detail(item_doc, source_variant_name=None, branch=None):
	if not item_doc:
		return item_doc, {}
	if not _has_column("Item", "has_variants") or not _has_column("Item", "variant_of"):
		return item_doc, {}
	if not cint(item_doc.get("has_variants") or 0):
		return item_doc, {}

	variants = _template_display_variants(item_doc, branch=branch)
	if not variants:
		return item_doc, {}

	if source_variant_name:
		source_variant_name = (source_variant_name or "").strip()
		for row in variants:
			if (row.get("name") or "").strip() == source_variant_name:
				return frappe.get_doc("Item", source_variant_name), row.get("variant_fixed_attributes") or {}

	representatives = sorted(variants, key=lambda row: _variant_item_sort_key(row.get("name")))
	selected = representatives[0]
	return frappe.get_doc("Item", selected.get("name")), selected.get("variant_fixed_attributes") or {}


def _extract_customization(raw):
	payload = _parse_json(raw, {})
	if not isinstance(payload, dict):
		payload = {}
	payload.setdefault("ingredient_adjustments", [])
	payload.setdefault("selected_modifiers", [])
	payload.setdefault("selected_alternatives", [])
	payload.setdefault("removed_ingredients", [])
	payload.setdefault("added_ingredients", [])
	payload.setdefault("nutrition", {})
	payload.setdefault("nutrition_totals", {})
	payload.setdefault("variant_fixed_attributes", {})
	payload.setdefault("builder_selection", {})
	payload.setdefault("builder_summary", "")
	payload.setdefault("builder_pricing_breakdown", {})
	payload.setdefault("builder_portion_rows", [])
	payload.setdefault("builder_template", "")
	return payload


def _ingredient_base_multiplier(row):
	return 1.0 if cint(row.get("is_included_by_default")) else 0.0


def _ingredient_required(row):
	return cint(row.get("is_required")) or (
		cint(row.get("is_included_by_default")) and not cint(row.get("can_remove"))
	)


def _step_valid(value, minimum, step):
	if step <= 0:
		return True
	ratio = (flt(value) - flt(minimum)) / flt(step)
	return abs(ratio - round(ratio)) < 1e-8


def _valuation_rate_for_item(item_code):
	if not item_code:
		return 0.0
	rate = flt(frappe.db.get_value("Item", item_code, "valuation_rate") or 0)
	if rate:
		return rate
	return flt(frappe.db.get_value("Item", item_code, "standard_rate") or 0)


def _item_consumes_stock(item_code):
	item_code = (item_code or "").strip()
	if not item_code or not frappe.db.exists("Item", item_code):
		return False
	if not _has_column("Item", "is_stock_item"):
		return True
	return cint(frappe.db.get_value("Item", item_code, "is_stock_item") or 0) == 1


def _normalize_selected_modifiers(raw_modifiers):
	rows = []
	for selected in raw_modifiers or []:
		if not isinstance(selected, dict):
			continue
		group = (selected.get("group") or selected.get("group_name") or selected.get("title") or "").strip()
		option = (selected.get("option") or selected.get("option_name") or "").strip()
		if not group or not option:
			continue

		qty = flt(selected.get("qty") if selected.get("qty") not in (None, "") else 1)
		if qty <= 0:
			qty = 1

		rows.append(
			{
				"group": group,
				"option": option,
				"qty": qty,
			}
		)
	return rows


def _normalize_selected_alternatives(raw_alternatives):
	normalized = {}
	for row in raw_alternatives or []:
		if not isinstance(row, dict):
			continue

		ingredient_key = (
			row.get("ingredient_key") or row.get("key") or row.get("ingredient_name") or row.get("name") or ""
		).strip()
		if not ingredient_key:
			continue

		alternative_item = (row.get("alternative_item") or row.get("item_code") or "").strip()
		if not alternative_item:
			normalized.pop(ingredient_key, None)
			continue

		normalized[ingredient_key] = alternative_item

	return [{"ingredient_key": key, "alternative_item": value} for key, value in normalized.items()]


def _normalize_ingredient_adjustments(menu_doc, customization):
	ingredient_rows = _get_bom_ingredient_rows(menu_doc)
	normalized = {}

	explicit_rows = customization.get("ingredient_adjustments") or []
	explicit_mode = isinstance(explicit_rows, list) and bool(explicit_rows)
	if explicit_mode:
		for row in explicit_rows:
			if not isinstance(row, dict):
				continue
			key = (row.get("ingredient_key") or row.get("key") or row.get("name") or "").strip()
			if not key:
				continue
			normalized[key] = flt(
				row.get("multiplier") if row.get("multiplier") is not None else row.get("qty")
			)

	removed_set = {
		str(name or "").strip()
		for name in (customization.get("removed_ingredients") or [])
		if str(name or "").strip()
	}
	added_set = {
		str(name or "").strip()
		for name in (customization.get("added_ingredients") or [])
		if str(name or "").strip()
	}

	for row in ingredient_rows:
		key = (row.get("ingredient_name") or "").strip()
		if not key:
			continue
		if key in normalized:
			continue

		base_multiplier = _ingredient_base_multiplier(row)
		multiplier = base_multiplier
		if not explicit_mode:
			if key in removed_set:
				multiplier = 0
			elif key in added_set:
				multiplier = max(base_multiplier, 1)

		normalized[key] = multiplier

	return normalized


def _get_branch_pricing_markup_percent(branch):
	if not frappe.db.exists("DocType", "Restaurant Branch Production Settings"):
		return 0.0

	branch = (branch or "").strip() or "DEFAULT"
	settings_name = frappe.db.get_value(
		"Restaurant Branch Production Settings",
		{"branch": branch, "is_active": 1},
		"name",
	)
	if not settings_name and branch != "DEFAULT":
		settings_name = frappe.db.get_value(
			"Restaurant Branch Production Settings",
			{"branch": "DEFAULT", "is_active": 1},
			"name",
		)
	if not settings_name:
		return 0.0
	return flt(
		frappe.db.get_value("Restaurant Branch Production Settings", settings_name, "pricing_markup_percent")
		or 0
	)


def _bom_row_stock_qty(row, bom_qty):
	qty_consumed_per_unit = flt(row.get("qty_consumed_per_unit") or 0)
	if qty_consumed_per_unit > 0:
		return qty_consumed_per_unit * bom_qty

	stock_qty = flt(row.get("stock_qty") or 0)
	if stock_qty > 0:
		return stock_qty

	row_qty = flt(row.get("qty") or 0)
	row_uom = row.get("uom") or row.get("stock_uom") or ""
	item_code = (row.get("item_code") or "").strip()
	return _nutrition_factor_from_item_qty(item_code, row_qty, row_uom)


def _nutrition_totals_for_item_qty(item_code, qty, uom=None):
	totals = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	item_code = (item_code or "").strip()
	if not item_code:
		return totals

	factor = _nutrition_factor_from_item_qty(item_code, qty, uom)
	if factor <= 0:
		return totals

	item_doc = frappe.get_cached_doc("Item", item_code)
	payload = _nutrition_per_unit_payload(item_doc)
	_add_nutrition_to_totals(totals, payload, factor)
	return totals


def _assign_nutrition_fields_on_child_row(child_row, totals):
	if not child_row:
		return
	child_doctype = (
		(child_row.get("doctype") if hasattr(child_row, "get") else None)
		or getattr(child_row, "doctype", "")
		or ""
	).strip()
	if not child_doctype:
		return
	for key, fieldname in NUTRITION_KEY_FIELD_MAP.items():
		if not _has_column(child_doctype, fieldname):
			continue
		child_row.set(fieldname, round(flt((totals or {}).get(key) or 0), 4))


def _estimate_bom_nutrition_data(bom_doc):
	if not bom_doc:
		return {}

	bom_qty = flt(bom_doc.get("quantity") or 0)
	if bom_qty <= 0:
		bom_qty = 1.0

	source_rows = []
	if bom_doc.get("exploded_items"):
		source_rows = bom_doc.get("exploded_items") or []
	else:
		source_rows = bom_doc.get("items") or []

	totals_for_batch = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	row_payloads = []
	has_any = False

	for row in source_rows:
		if cint(row.get("include_item_in_manufacturing", 1)) == 0:
			continue

		item_code = (row.get("item_code") or "").strip()
		if not item_code:
			continue

		stock_qty = _bom_row_stock_qty(row, bom_qty)
		if stock_qty <= 0:
			continue

		item_doc = frappe.get_cached_doc("Item", item_code)
		per_stock = _nutrition_per_unit_payload(item_doc)
		if not any(flt(per_stock.get(key) or 0) for key in NUTRITION_KEY_FIELD_MAP):
			recursive_payload = _estimate_item_nutrition_from_default_bom(item_doc, visited=set())
			if recursive_payload:
				per_stock = recursive_payload

		line_totals = {key: flt(per_stock.get(key) or 0) * stock_qty for key in NUTRITION_KEY_FIELD_MAP}
		_add_nutrition_to_totals(totals_for_batch, per_stock, stock_qty)
		if any(flt(line_totals.get(key) or 0) > 0 for key in NUTRITION_KEY_FIELD_MAP):
			has_any = True

		row_payloads.append(
			{
				"item_code": item_code,
				"item_name": row.get("item_name") or item_doc.get("item_name") or item_code,
				"stock_uom": row.get("stock_uom") or item_doc.get("stock_uom") or "",
				"stock_qty": round(stock_qty, 6),
				"nutrition_kcal": round(flt(line_totals.get("kcal") or 0), 4),
				"nutrition_protein_g": round(flt(line_totals.get("protein_g") or 0), 4),
				"nutrition_carb_g": round(flt(line_totals.get("carb_g") or 0), 4),
				"nutrition_sugar_g": round(flt(line_totals.get("sugar_g") or 0), 4),
				"nutrition_fat_g": round(flt(line_totals.get("fat_g") or 0), 4),
			}
		)

	totals_per_unit = {
		key: _safe_div(flt(totals_for_batch.get(key) or 0), bom_qty) for key in NUTRITION_KEY_FIELD_MAP
	}

	return {
		"has_any": has_any,
		"bom_qty": bom_qty,
		"rows": row_payloads,
		"totals_for_batch": _normalize_nutrition_totals(totals_for_batch),
		"totals_per_unit": _normalize_nutrition_totals(totals_per_unit),
		"nutrition_per_unit": _nutrition_payload_from_totals(totals_per_unit),
	}


def _upsert_bom_nutrition_fields(bom_doc):
	if not bom_doc:
		return False
	if not getattr(bom_doc, "name", None):
		return False

	estimated = _estimate_bom_nutrition_data(bom_doc)
	per_unit = estimated.get("totals_per_unit") or {}
	bom_qty = flt(bom_doc.get("quantity") or 0)
	if bom_qty <= 0:
		bom_qty = 1.0
	changed = False
	for key, fieldname in NUTRITION_KEY_FIELD_MAP.items():
		if not _has_column("BOM", fieldname):
			continue
		next_value = round(flt(per_unit.get(key) or 0), 4)
		if abs(flt(bom_doc.get(fieldname) or 0) - next_value) > 1e-9:
			bom_doc.set(fieldname, next_value)
			changed = True

	if bom_doc.get("items"):
		for row in bom_doc.get("items") or []:
			row_item = (row.get("item_code") or "").strip()
			if not row_item:
				continue
			row_qty = flt(row.get("qty") or 0)
			row_uom = row.get("uom") or row.get("stock_uom") or ""
			row_totals = _nutrition_totals_for_item_qty(row_item, row_qty, row_uom)
			_assign_nutrition_fields_on_child_row(row, row_totals)

	if bom_doc.get("exploded_items"):
		for row in bom_doc.get("exploded_items") or []:
			row_item = (row.get("item_code") or "").strip()
			if not row_item:
				continue
			stock_qty = _bom_row_stock_qty(row, bom_qty=bom_qty)
			row_totals = _nutrition_totals_for_item_qty(row_item, stock_qty, row.get("stock_uom") or "")
			_assign_nutrition_fields_on_child_row(row, row_totals)

	return changed


def _estimate_item_nutrition_from_default_bom(item_doc, visited=None):
	if not item_doc:
		return None

	item_name = (item_doc.get("name") if hasattr(item_doc, "get") else getattr(item_doc, "name", "")) or ""
	if not item_name:
		return None

	visited = visited or set()
	if item_name in visited:
		return None
	visited.add(item_name)

	bom_name = _resolve_bom_template(item_doc)
	if not bom_name:
		return None

	try:
		bom_doc = frappe.get_cached_doc("BOM", bom_name)
	except Exception:
		return None

	direct_bom_nutrition = _nutrition_payload(bom_doc)
	if any(flt(direct_bom_nutrition.get(key) or 0) > 0 for key in NUTRITION_KEY_FIELD_MAP):
		return direct_bom_nutrition

	estimated_data = _estimate_bom_nutrition_data(bom_doc)
	if estimated_data.get("has_any"):
		return estimated_data.get("nutrition_per_unit")

	bom_qty = flt(bom_doc.get("quantity") or 0)
	if bom_qty <= 0:
		bom_qty = 1.0

	row_totals = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	has_any_value = False

	child_rows = []
	if bom_doc.get("exploded_items"):
		child_rows = bom_doc.get("exploded_items") or []
	else:
		child_rows = bom_doc.get("items") or []

	for row in child_rows:
		if cint(row.get("include_item_in_manufacturing", 1)) == 0:
			continue

		child_item_code = (row.get("item_code") or "").strip()
		if not child_item_code:
			continue

		qty_in_stock_uom = (
			flt(row.get("qty_consumed_per_unit") or 0)
			if row.get("qty_consumed_per_unit") not in (None, "")
			else flt(row.get("stock_qty") or 0)
		)
		if qty_in_stock_uom <= 0:
			stock_qty = flt(row.get("stock_qty") or 0)
			if stock_qty > 0:
				qty_in_stock_uom = stock_qty / bom_qty

		if qty_in_stock_uom <= 0:
			row_qty = flt(row.get("qty") or 0)
			row_uom = row.get("uom") or row.get("stock_uom") or ""
			qty_in_stock_uom = _nutrition_factor_from_item_qty(child_item_code, row_qty, row_uom) / bom_qty

		if qty_in_stock_uom <= 0:
			continue

		child_item_doc = frappe.get_cached_doc("Item", child_item_code)
		child_per_unit = _nutrition_per_unit_payload(child_item_doc)
		if not any(flt(child_per_unit.get(key) or 0) for key in NUTRITION_KEY_FIELD_MAP):
			recursive_payload = _estimate_item_nutrition_from_default_bom(child_item_doc, visited=visited)
			if recursive_payload:
				child_per_unit = recursive_payload

		before = dict(row_totals)
		_add_nutrition_to_totals(row_totals, child_per_unit, qty_in_stock_uom)
		if any(
			abs(flt(row_totals.get(key) or 0) - flt(before.get(key) or 0)) > 1e-9
			for key in NUTRITION_KEY_FIELD_MAP
		):
			has_any_value = True

	if not has_any_value:
		return None

	return _nutrition_payload_from_totals(row_totals)


def _upsert_item_nutrition_from_bom(item_code, nutrition_payload):
	item_code = (item_code or "").strip()
	if not item_code or not nutrition_payload:
		return False
	if not frappe.db.exists("Item", item_code):
		return False

	changed = False
	updates = {}
	for key, fieldname in NUTRITION_KEY_FIELD_MAP.items():
		if not _has_column("Item", fieldname):
			continue
		next_value = round(flt(nutrition_payload.get(key) or 0), 4)
		current_value = flt(frappe.db.get_value("Item", item_code, fieldname) or 0)
		if abs(current_value - next_value) > 1e-9:
			updates[fieldname] = next_value
			changed = True

	if changed:
		frappe.db.set_value("Item", item_code, updates, update_modified=False)

	return changed


def _refresh_item_nutrition_from_bom(item_code):
	item_code = (item_code or "").strip()
	if not item_code:
		return False
	if not frappe.db.exists("Item", item_code):
		return False

	item_doc = frappe.get_cached_doc("Item", item_code)
	estimated = _estimate_item_nutrition_from_default_bom(item_doc)
	if not estimated:
		return False
	return _upsert_item_nutrition_from_bom(item_code, estimated)


def _recalculate_line(menu_doc, quantity, customization, branch_markup_percent=0):
	variant_doc = _resolve_variant_item_for_customization(menu_doc, customization or {})
	if variant_doc:
		menu_doc = variant_doc

	builder_enabled = bool(
		cint(menu_doc.get("restaurant_is_customizable") or 0)
		and cint(menu_doc.get("restaurant_builder_active") or 0)
	)
	builder_payload = _extract_builder_selection_payload(customization or {})
	if builder_enabled and builder_payload.get("rows"):
		builder_calc = _compute_builder_selection_data(
			menu_doc.item_code,
			builder_payload.get("rows") or [],
			base_price=_menu_doc_config(menu_doc).get("base_price"),
			template_name=builder_payload.get("template") or menu_doc.get("restaurant_builder_template") or "",
			strict=True,
		)
		line_qty = max(flt(quantity or 1), 1)
		unit_price = flt(builder_calc["final_price"] or 0)
		line_total = unit_price * line_qty
		nutrition_totals = {
			key: round(flt(builder_calc["nutrition"].get(key) or 0) * line_qty, 4)
			for key in NUTRITION_KEY_FIELD_MAP
		}
		normalized_customization = dict(builder_calc["normalized_customization"] or {})
		normalized_customization["nutrition"] = _nutrition_payload_from_totals(nutrition_totals)
		normalized_customization["nutrition_totals"] = _normalize_nutrition_totals(nutrition_totals)
		pricing_breakdown = dict(builder_calc["pricing_breakdown"] or {})
		pricing_breakdown.update(
			{
				"unit_price": unit_price,
				"line_total": line_total,
				"qty": line_qty,
				"extra_charge": unit_price - flt(builder_calc["base_price"] or 0),
				"nutrition": builder_calc["nutrition"],
				"nutrition_totals": _normalize_nutrition_totals(nutrition_totals),
				"ingredients": builder_calc["ingredient_components"],
				"modifiers": [],
				"selected_alternatives": [],
			}
		)
		return {
			"qty": line_qty,
			"unit_price": unit_price,
			"line_total": line_total,
			"selections": builder_calc["selections_summary"],
			"extra_charge": unit_price - flt(builder_calc["base_price"] or 0),
			"normalized_customization": normalized_customization,
			"pricing_breakdown": pricing_breakdown,
			"ingredient_components": builder_calc["ingredient_components"],
			"recipe_multiplier": 1.0,
			"nutrition": builder_calc["nutrition"],
			"nutrition_totals": _normalize_nutrition_totals(nutrition_totals),
		}

	quantity = max(flt(quantity or 1), 1)
	cfg = _menu_doc_config(menu_doc)
	base_price = flt(cfg["base_price"])
	unit_price = base_price

	ingredient_rows = _get_bom_ingredient_rows(menu_doc)
	adjustments = _normalize_ingredient_adjustments(menu_doc, customization)
	ingredient_keys = {
		(row.get("ingredient_name") or "").strip()
		for row in ingredient_rows
		if (row.get("ingredient_name") or "").strip()
	}
	unknown_adjustments = set(adjustments.keys()) - ingredient_keys
	if unknown_adjustments:
		frappe.throw(_("Invalid ingredient key: {0}").format(", ".join(sorted(unknown_adjustments))))
	selected_alternative_rows = _normalize_selected_alternatives(customization.get("selected_alternatives"))
	selected_alternative_map = {
		(row.get("ingredient_key") or "").strip(): (row.get("alternative_item") or "").strip()
		for row in selected_alternative_rows
		if (row.get("ingredient_key") or "").strip() and (row.get("alternative_item") or "").strip()
	}
	unknown_alternative_rows = set(selected_alternative_map.keys()) - ingredient_keys
	if unknown_alternative_rows:
		frappe.throw(
			_("Invalid ingredient key for alternative selection: {0}").format(
				", ".join(sorted(unknown_alternative_rows))
			)
		)

	selections = []
	ingredient_delta_total = 0.0
	modifier_delta_total = 0.0
	ingredient_components = []
	normalized_adjustments = []
	normalized_selected_alternatives = []
	nutrition_totals = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	markup_factor = 1 + flt(branch_markup_percent) / 100.0

	for row in ingredient_rows:
		ingredient_name = (row.get("ingredient_name") or "").strip()
		if not ingredient_name:
			continue

		label = row.get("customer_label") or ingredient_name
		ingredient_item = row.get("ingredient_item") or ""
		base_qty = flt(row.get("base_qty") or (1 if cint(row.get("is_included_by_default")) else 0.5))
		if base_qty <= 0:
			base_qty = 1

		base_multiplier = _ingredient_base_multiplier(row)
		selected_multiplier = flt(adjustments.get(ingredient_name, base_multiplier))
		alternative_options = row.get("alternative_options") or []
		alternative_map = {
			(opt.get("alternative_item") or "").strip(): opt
			for opt in alternative_options
			if (opt.get("alternative_item") or "").strip()
		}
		selected_alternative_item = (selected_alternative_map.get(ingredient_name) or "").strip()
		selected_alternative = (
			alternative_map.get(selected_alternative_item) if selected_alternative_item else None
		)

		min_multiplier = flt(row.get("min_multiplier"))
		max_multiplier = flt(row.get("max_multiplier") or 3)
		step_multiplier = flt(row.get("step_multiplier") or 0.5)
		multiplier_qty = flt(row.get("multiplier_qty") or 0)
		if multiplier_qty > 0 and base_qty > 0:
			step_multiplier = multiplier_qty / base_qty
		is_required = _ingredient_required(row)
		can_remove = cint(row.get("can_remove"))
		is_editable = cint(row.get("is_editable_qty"))
		if is_editable not in (0, 1):
			is_editable = 1

		if is_required and min_multiplier < 1:
			min_multiplier = 1
		if min_multiplier < 0:
			min_multiplier = 0
		if max_multiplier < min_multiplier:
			max_multiplier = min_multiplier
		if step_multiplier <= 0:
			step_multiplier = 0.5

		if not is_editable and abs(selected_multiplier - base_multiplier) > 1e-8:
			frappe.throw(_("Ingredient quantity is locked and cannot be changed: {0}").format(label))

		if selected_multiplier < min_multiplier - 1e-8 or selected_multiplier > max_multiplier + 1e-8:
			frappe.throw(
				_("Ingredient multiplier for {0} must be between {1} and {2}.").format(
					label,
					min_multiplier,
					max_multiplier,
				)
			)

		if not _step_valid(selected_multiplier, min_multiplier, step_multiplier):
			frappe.throw(
				_("Ingredient multiplier for {0} must follow step {1}.").format(label, step_multiplier)
			)

		if not can_remove and base_multiplier > 0 and selected_multiplier < base_multiplier - 1e-8:
			frappe.throw(_("Ingredient cannot be reduced below base recipe: {0}").format(label))

		if selected_alternative_item and not selected_alternative:
			frappe.throw(
				_("Invalid alternative item selected for {0}: {1}").format(label, selected_alternative_item)
			)

		selected_item_code = ingredient_item
		selected_base_qty = base_qty
		selected_stock_uom = row.get("qty_uom") or ""
		selected_pricing_uom = row.get("qty_uom") or ""
		selected_item_name = (
			frappe.db.get_value("Item", ingredient_item, "item_name") if ingredient_item else label
		)

		if selected_alternative:
			selected_item_code = (selected_alternative.get("alternative_item") or "").strip()
			qty_multiplier = flt(
				selected_alternative.get("qty_multiplier")
				if selected_alternative.get("qty_multiplier") not in (None, "")
				else 1
			)
			if qty_multiplier < 0:
				qty_multiplier = 0
			qty_addition = flt(selected_alternative.get("qty_addition") or 0)
			selected_base_qty = (base_qty * qty_multiplier) + qty_addition
			if selected_base_qty < 0:
				frappe.throw(_("Alternative quantity for {0} cannot be negative.").format(label))
			if selected_multiplier > 0 and selected_base_qty <= 0:
				frappe.throw(_("Alternative quantity for {0} must be greater than zero.").format(label))

			selected_pricing_uom = (
				selected_alternative.get("pricing_uom")
				or row.get("qty_uom")
				or selected_alternative.get("uom")
				or selected_alternative.get("stock_uom")
				or ""
			)
			selected_stock_uom = (
				selected_alternative.get("stock_uom")
				or frappe.db.get_value("Item", selected_item_code, "stock_uom")
				or selected_alternative.get("uom")
				or selected_stock_uom
			)
			selected_item_name = (
				selected_alternative.get("item_name")
				or frappe.db.get_value("Item", selected_item_code, "item_name")
				or selected_item_code
			)
			normalized_selected_alternatives.append(
				{
					"ingredient_key": ingredient_name,
					"alternative_item": selected_item_code,
				}
			)

		delta_multiplier = selected_multiplier - base_multiplier
		base_component_qty = base_qty * base_multiplier
		selected_component_qty = selected_base_qty * selected_multiplier
		base_pricing = (
			_resolve_default_selling_item_pricing(
				ingredient_item,
				base_component_qty,
				uom=row.get("qty_uom") or "",
			)
			if ingredient_item
			else {}
		)
		selected_pricing = (
			_resolve_default_selling_item_pricing(
				selected_item_code,
				selected_component_qty,
				uom=selected_pricing_uom or selected_stock_uom or "",
			)
			if selected_item_code
			else {}
		)
		base_rate = _valuation_rate_for_item(ingredient_item)
		selected_rate = _valuation_rate_for_item(selected_item_code)
		base_item_price_ok = not ingredient_item or cint(base_pricing.get("is_selectable") or 0) == 1
		selected_item_price_ok = (
			not selected_item_code or cint(selected_pricing.get("is_selectable") or 0) == 1
		)
		if ingredient_item or selected_item_code:
			if base_item_price_ok and selected_item_price_ok:
				base_total_price = flt(base_pricing.get("total_price") or 0)
				selected_total_price = flt(selected_pricing.get("total_price") or 0)
				delta_price = selected_total_price - base_total_price
			elif selected_alternative and ingredient_item and selected_item_code:
				alternative_pricing = _resolve_ingredient_alternative_pricing(
					ingredient_item,
					base_component_qty,
					row.get("qty_uom") or "",
					selected_item_code,
					selected_component_qty,
					alternative_uom=selected_pricing_uom or selected_stock_uom,
				)
				if cint(alternative_pricing.get("is_selectable") or 0) != 1:
					frappe.throw(
						alternative_pricing.get("unavailable_reason")
						or _("Alternative item price could not be resolved for {0}.").format(label)
					)
				delta_price = flt(alternative_pricing.get("price_delta") or 0)
			elif flt(row.get("extra_when_added")):
				delta_price = delta_multiplier * flt(row.get("extra_when_added"))
			else:
				base_component_cost = base_component_qty * base_rate if ingredient_item else 0
				selected_component_cost = (
					selected_component_qty * selected_rate if selected_item_code else 0
				)
				delta_price = (selected_component_cost - base_component_cost) * markup_factor
		else:
			delta_price = delta_multiplier * flt(row.get("extra_when_added"))

		unit_price += delta_price
		ingredient_delta_total += delta_price
		normalized_adjustments.append({"ingredient_key": ingredient_name, "multiplier": selected_multiplier})

		if abs(delta_price) > 1e-8 or abs(delta_multiplier) > 1e-8 or selected_alternative:
			if selected_alternative:
				alt_label = selected_item_name or selected_item_code
				modifier_suffix = f" x{selected_multiplier:g}" if abs(selected_multiplier - 1) > 1e-8 else ""
				selection_label = f"{label} -> {alt_label}{modifier_suffix}"
				selection_kind = "ingredient_alternative"
			else:
				prefix = "+" if delta_multiplier > 0 else "-"
				selection_label = f"{prefix} {label} x{abs(delta_multiplier):g}"
				selection_kind = "ingredient"

			selections.append(
				{
					"kind": selection_kind,
					"label": selection_label,
					"delta_price": delta_price,
					"qty": 1,
				}
			)

		ingredient_components.append(
			{
				"ingredient_key": ingredient_name,
				"ingredient_label": label,
				"item_code": selected_item_code,
				"item_name": selected_item_name,
				"base_item_code": ingredient_item,
				"selected_alternative_item": selected_item_code if selected_alternative else "",
				"base_qty": base_qty,
				"selected_base_qty": selected_base_qty,
				"base_multiplier": base_multiplier,
				"selected_multiplier": selected_multiplier,
				"is_required": cint(is_required),
				"is_included_by_default": cint(row.get("is_included_by_default")),
				"can_remove": can_remove,
				"is_editable_qty": is_editable,
				"min_multiplier": min_multiplier,
				"max_multiplier": max_multiplier,
				"step_multiplier": step_multiplier,
				"multiplier_qty": multiplier_qty if multiplier_qty > 0 else 0,
				"pricing_rate": flt(selected_pricing.get("unit_rate") or selected_rate or 0),
				"pricing_delta": delta_price,
				"price_status": selected_pricing.get("price_status")
				or base_pricing.get("price_status")
				or "",
				"price_list": selected_pricing.get("price_list")
				or base_pricing.get("price_list")
				or "",
				"price_source": "item_price"
				if base_item_price_ok and selected_item_price_ok and (ingredient_item or selected_item_code)
				else "legacy",
				"stock_uom": selected_stock_uom or row.get("qty_uom") or "",
				"source_type": "bom_item",
			}
		)
		selected_item_doc = frappe.get_cached_doc("Item", selected_item_code) if selected_item_code else {}
		selected_item_nutrition = _nutrition_per_unit_payload(selected_item_doc)
		nutrition_factor = _nutrition_factor_from_item_qty(
			selected_item_code,
			selected_base_qty * selected_multiplier,
			selected_stock_uom or row.get("qty_uom") or "",
		)
		_add_nutrition_to_totals(nutrition_totals, selected_item_nutrition, nutrition_factor)

	modifier_groups, group_map, title_map = _build_modifier_groups(menu_doc)
	selected_raw_all = _normalize_selected_modifiers(customization.get("selected_modifiers"))
	variant_selected_rows = [
		row for row in selected_raw_all if (row.get("group") or "").startswith("variant::")
	]
	selected_raw = [row for row in selected_raw_all if not (row.get("group") or "").startswith("variant::")]
	selected_by_group = defaultdict(int)
	normalized_selected_modifiers = [
		{
			"group": (row.get("group") or "").strip(),
			"option": (row.get("option") or "").strip(),
			"qty": flt(row.get("qty") or 1),
			"type": "variant_selection",
			"item_code": "",
			"replacement_for_item": "",
			"alternative_bom": "",
		}
		for row in variant_selected_rows
		if (row.get("group") or "").strip() and (row.get("option") or "").strip()
	]
	line_recipe_multiplier = 1.0
	selected_bom = ""

	for selected in selected_raw:
		raw_group = (
			selected.get("group") or selected.get("group_name") or selected.get("title") or ""
		).strip()
		group_name = raw_group if raw_group in group_map else title_map.get(raw_group)
		if not group_name:
			frappe.throw(_("Invalid modifier group: {0}").format(raw_group))
		if cint(group_map[group_name]["meta"].get("is_variant_attribute_selector")):
			continue

		option_name = (selected.get("option") or selected.get("option_name") or "").strip()
		option_payload = group_map[group_name]["options"].get(option_name)
		if not option_payload:
			frappe.throw(_("Invalid modifier option: {0}").format(option_name))

		recipe_multiplier = flt(option_payload.get("recipe_multiplier") or 1)
		if recipe_multiplier <= 0:
			recipe_multiplier = 1

		modifier_type = (
			option_payload.get("action_type") or option_payload.get("modifier_type") or "add_on"
		).strip() or "add_on"
		option_label = (option_payload.get("label") or option_name).strip()
		option_item = (option_payload.get("option_item") or "").strip()
		replacement_for = (option_payload.get("replacement_for_item") or "").strip()
		alternative_bom = (option_payload.get("alternative_bom") or "").strip()
		option_qty = flt(option_payload.get("option_qty") or option_payload.get("base_qty") or 1)
		if option_qty <= 0:
			option_qty = 1

		option_min_qty = max(
			flt(option_payload.get("min_qty") if option_payload.get("min_qty") not in (None, "") else 0), 0
		)
		option_max_qty = max(
			flt(
				option_payload.get("max_qty")
				if option_payload.get("max_qty") not in (None, "")
				else max(option_qty, option_qty * 4)
			),
			option_min_qty,
			option_qty,
		)
		option_step = flt(option_payload.get("qty_step") or option_qty or 1)
		if option_step <= 0:
			option_step = option_qty if option_qty > 0 else 1

		qty = flt(
			selected.get("qty")
			if selected.get("qty") not in (None, "")
			else (option_qty if cint(option_payload.get("is_default")) else option_min_qty)
		)
		if qty <= 0:
			qty = option_qty if option_qty > 0 else option_step

		if qty < option_min_qty - 1e-8 or qty > option_max_qty + 1e-8:
			frappe.throw(
				_("Modifier qty for {0} must be between {1} and {2}.").format(
					option_label,
					option_min_qty,
					option_max_qty,
				)
			)

		if not _step_valid(qty, option_min_qty, option_step):
			frappe.throw(_("Modifier qty for {0} must follow step {1}.").format(option_label, option_step))

		if cint(option_payload.get("is_selectable") if option_payload.get("is_selectable") not in (None, "") else 1) != 1:
			raise_reason = (
				option_payload.get("unavailable_reason")
				or _("Modifier option {0} is not available for ordering.").format(option_label)
			)
			frappe.throw(raise_reason, frappe.ValidationError)

		conversion_factor = flt(option_payload.get("conversion_factor") or 1)
		selected_qty_in_stock_uom = qty * conversion_factor
		delta = flt(option_payload.get("unit_rate") or 0) * selected_qty_in_stock_uom
		qty_ratio = qty / option_qty if option_qty > 1e-8 else 1

		if modifier_type == "bom_variant" and alternative_bom:
			bom_meta = frappe.db.get_value(
				"BOM",
				alternative_bom,
				["item", "docstatus", "is_active"],
				as_dict=True,
			)
			if (
				not bom_meta
				or bom_meta.item != menu_doc.item_code
				or cint(bom_meta.docstatus) != 1
				or not cint(bom_meta.is_active)
			):
				frappe.throw(_("Invalid BOM variant for option: {0}").format(option_label))
			selected_bom = alternative_bom

		if modifier_type == "replacement":
			frappe.throw(
				_(
					"Replacement modifiers are deprecated. Configure alternatives in BOM Item instead: {0}"
				).format(option_label)
			)

		if modifier_type == "add_on" and option_item:
			option_stock_uom = frappe.db.get_value("Item", option_item, "stock_uom") or ""
			ingredient_components.append(
				{
					"ingredient_key": option_name,
					"ingredient_label": option_label,
					"item_code": option_item,
					"item_name": frappe.db.get_value("Item", option_item, "item_name") or option_label,
					"base_item_code": "",
					"selected_alternative_item": "",
					"base_qty": flt(option_payload.get("base_qty_in_stock_uom") or selected_qty_in_stock_uom),
					"selected_base_qty": selected_qty_in_stock_uom,
					"base_multiplier": 0,
					"selected_multiplier": 1,
					"is_required": 0,
					"is_included_by_default": 0,
					"can_remove": 1,
					"is_editable_qty": 1,
					"min_multiplier": option_min_qty * conversion_factor,
					"max_multiplier": option_max_qty * conversion_factor,
					"step_multiplier": option_step * conversion_factor,
					"pricing_rate": _valuation_rate_for_item(option_item),
					"pricing_delta": delta,
					"stock_uom": option_stock_uom,
					"authoring_uom": option_payload.get("option_uom") or "",
					"authoring_base_qty": option_qty,
					"selected_authoring_qty": qty,
					"source_type": "modifier_add_on",
				}
			)
			option_item_doc = frappe.get_cached_doc("Item", option_item)
			option_nutrition = _nutrition_per_unit_payload(option_item_doc)
			option_factor = _nutrition_factor_from_item_qty(
				option_item,
				qty,
				option_payload.get("option_uom") or option_stock_uom,
			)
			_add_nutrition_to_totals(nutrition_totals, option_nutrition, option_factor)

		unit_price += delta
		modifier_delta_total += delta
		selected_by_group[group_name] += 1
		line_recipe_multiplier *= math.pow(recipe_multiplier, qty_ratio)
		normalized_selected_modifiers.append(
			{
				"group": group_name,
				"option": option_name,
				"qty": qty,
				"type": modifier_type,
				"item_code": option_item,
				"replacement_for_item": replacement_for,
				"alternative_bom": alternative_bom,
			}
		)

		qty_label = f"{qty:g}"
		uom_label = (option_payload.get("option_uom") or "").strip()
		label_suffix = f" {qty_label} {uom_label}".rstrip() if qty > 0 else ""
		selections.append(
			{
				"kind": "modifier",
				"label": f"{group_map[group_name]['meta']['title']}: {option_label}{label_suffix}",
				"delta_price": delta,
				"qty": qty,
			}
		)

	for group in modifier_groups:
		if cint(group.get("is_variant_attribute_selector")):
			continue
		count = selected_by_group.get(group["group_name"], 0)
		if count < cint(group["min_select"]):
			default_option = next(
				(
					option
					for option in group.get("options", [])
					if cint(option.get("is_default"))
					and cint(option.get("is_selectable") if option.get("is_selectable") not in (None, "") else 1) == 1
					and not (option.get("option_item") or "").strip()
					and flt(option.get("unit_rate") or option.get("price_delta") or option.get("base_price") or 0) == 0
				),
				None,
			)
			if (
				count == 0
				and default_option
				and (group.get("selection_mode") or "single") == "single"
				and cint(group["min_select"]) <= 1
			):
				option_name = (default_option.get("name") or "").strip()
				option_qty = flt(
					default_option.get("option_qty")
					or default_option.get("base_qty")
					or default_option.get("qty_step")
					or 1
				)
				if option_name:
					selected_by_group[group["group_name"]] += 1
					count = selected_by_group[group["group_name"]]
					normalized_selected_modifiers.append(
						{
							"group": group["group_name"],
							"option": option_name,
							"qty": option_qty if option_qty > 0 else 1,
							"type": default_option.get("action_type") or default_option.get("modifier_type") or "add_on",
							"item_code": "",
							"replacement_for_item": "",
							"alternative_bom": "",
						}
					)
		if count < cint(group["min_select"]):
			frappe.throw(_("Please select more options for group: {0}").format(group["title"]))
		if count > cint(group["max_select"]):
			frappe.throw(_("Too many selected options for group: {0}").format(group["title"]))

	line_total = unit_price * quantity
	nutrition_unit = _nutrition_payload_from_totals(nutrition_totals)
	nutrition_line_totals = {
		key: round(flt(nutrition_unit.get(key) or 0) * quantity, 4) for key in NUTRITION_KEY_FIELD_MAP
	}
	nutrition_line_payload = _nutrition_payload_from_totals(nutrition_line_totals)
	normalized_customization = {
		"ingredient_adjustments": normalized_adjustments,
		"selected_modifiers": normalized_selected_modifiers,
		"selected_alternatives": normalized_selected_alternatives,
		"nutrition": nutrition_line_payload,
		"nutrition_totals": _normalize_nutrition_totals(nutrition_line_totals),
		"variant_fixed_attributes": (customization.get("variant_fixed_attributes") or {}),
	}
	pricing_breakdown = {
		"base_price": base_price,
		"ingredient_delta_total": ingredient_delta_total,
		"modifier_delta_total": modifier_delta_total,
		"extra_charge": unit_price - base_price,
		"unit_price": unit_price,
		"qty": quantity,
		"line_total": line_total,
		"recipe_multiplier": line_recipe_multiplier,
		"selected_bom": selected_bom,
		"branch_markup_percent": flt(branch_markup_percent),
		"nutrition": nutrition_unit,
		"nutrition_totals": _normalize_nutrition_totals(nutrition_line_totals),
		"ingredients": ingredient_components,
		"modifiers": normalized_selected_modifiers,
		"selected_alternatives": normalized_selected_alternatives,
	}

	return {
		"qty": quantity,
		"unit_price": unit_price,
		"line_total": line_total,
		"selections": selections,
		"extra_charge": unit_price - base_price,
		"normalized_customization": normalized_customization,
		"pricing_breakdown": pricing_breakdown,
		"ingredient_components": ingredient_components,
		"recipe_multiplier": line_recipe_multiplier,
		"nutrition": nutrition_unit,
		"nutrition_totals": _normalize_nutrition_totals(nutrition_line_totals),
	}


def _restaurant_doctype_exists(doctype):
	try:
		return bool(frappe.db.exists("DocType", doctype))
	except Exception:
		return False


def _estimate_cart_subtotal(cart_items):
	subtotal = 0.0
	for cart_line in _normalize_cart_items(cart_items):
		menu_doc = _get_item_doc_by_payload(cart_line)
		customization = _extract_customization(cart_line.get("customization") or cart_line.get("config"))
		branch = (
			cart_line.get("branch") or menu_doc.get("restaurant_branch") or "DEFAULT"
		).strip() or "DEFAULT"
		line_calc = _recalculate_line(
			menu_doc,
			cart_line.get("qty"),
			customization,
			branch_markup_percent=_get_branch_pricing_markup_percent(branch),
		)
		subtotal += flt(line_calc.get("line_total") or 0)
	return flt(subtotal)


def _find_coupon_doc(coupon_code):
	code = (coupon_code or "").strip()
	if not code or not _restaurant_doctype_exists("Restaurant Coupon"):
		return None

	coupon_name = frappe.db.get_value("Restaurant Coupon", {"coupon_code": code}, "name")
	if not coupon_name:
		rows = frappe.get_all(
			"Restaurant Coupon",
			fields=["name", "coupon_code"],
			limit_page_length=500,
			ignore_permissions=True,
		)
		code_lower = code.lower()
		coupon_name = next(
			(row.name for row in rows if (row.get("coupon_code") or "").strip().lower() == code_lower),
			None,
		)
	return frappe.get_doc("Restaurant Coupon", coupon_name) if coupon_name else None


def _build_coupon_result(coupon_doc, subtotal, mobile="", branch=""):
	today_date = getdate(today())
	code = (coupon_doc.get("coupon_code") or coupon_doc.name or "").strip()
	if not cint(coupon_doc.get("is_active")):
		frappe.throw(_("Coupon {0} is not active.").format(code))
	if coupon_doc.get("valid_from") and getdate(coupon_doc.get("valid_from")) > today_date:
		frappe.throw(_("Coupon {0} is not valid yet.").format(code))
	if coupon_doc.get("valid_to") and getdate(coupon_doc.get("valid_to")) < today_date:
		frappe.throw(_("Coupon {0} has expired.").format(code))
	if cint(coupon_doc.get("usage_limit")) and cint(coupon_doc.get("used_count")) >= cint(
		coupon_doc.get("usage_limit")
	):
		frappe.throw(_("Coupon {0} usage limit has been reached.").format(code))

	coupon_mobile = (coupon_doc.get("customer_mobile") or "").strip()
	if coupon_mobile:
		if not mobile or _ensure_mobile(coupon_mobile) != _ensure_mobile(mobile):
			frappe.throw(_("Coupon {0} is not valid for this customer.").format(code))

	coupon_branch = (coupon_doc.get("branch") or "").strip()
	if coupon_branch and branch and coupon_branch.lower() != (branch or "").strip().lower():
		frappe.throw(_("Coupon {0} is not valid for this branch.").format(code))

	subtotal = flt(subtotal)
	min_order = flt(coupon_doc.get("min_order_amount") or 0)
	if min_order and subtotal < min_order:
		frappe.throw(_("Minimum order amount for coupon {0} is {1}.").format(code, min_order))

	discount_value = flt(coupon_doc.get("discount_value") or 0)
	if discount_value <= 0:
		frappe.throw(_("Coupon discount value is invalid."))

	discount_type = (coupon_doc.get("discount_type") or "Percent").strip().lower()
	discount_amount = subtotal * discount_value / 100.0 if discount_type == "percent" else discount_value
	max_discount = flt(coupon_doc.get("max_discount_amount") or 0)
	if max_discount > 0:
		discount_amount = min(discount_amount, max_discount)
	discount_amount = flt(min(max(discount_amount, 0), subtotal))

	return {
		"valid": 1,
		"success": True,
		"name": coupon_doc.name,
		"code": code,
		"title": coupon_doc.get("title") or code,
		"discount_type": coupon_doc.get("discount_type") or "Percent",
		"discount_value": discount_value,
		"discount_amount": discount_amount,
		"subtotal": subtotal,
		"total_after_discount": flt(max(subtotal - discount_amount, 0)),
		"message": _("Coupon applied successfully."),
	}


def _validate_coupon_for_cart(coupon_code, cart_items, mobile="", branch=""):
	coupon_doc = _find_coupon_doc(coupon_code)
	if not coupon_doc:
		frappe.throw(_("Coupon not found."), frappe.DoesNotExistError)
	return _build_coupon_result(coupon_doc, _estimate_cart_subtotal(cart_items), mobile=mobile, branch=branch)


def _mark_coupon_used(coupon_name):
	if not coupon_name or not _restaurant_doctype_exists("Restaurant Coupon"):
		return
	current = cint(frappe.db.get_value("Restaurant Coupon", coupon_name, "used_count") or 0)
	frappe.db.set_value("Restaurant Coupon", coupon_name, "used_count", current + 1, update_modified=False)


@frappe.whitelist(allow_guest=True)
def validate_coupon(coupon_code, items=None, mobile=None, branch=None, subtotal=None):
	coupon_doc = _find_coupon_doc(coupon_code)
	if not coupon_doc:
		frappe.throw(_("Coupon not found."), frappe.DoesNotExistError)
	resolved_subtotal = flt(subtotal) if subtotal not in (None, "") else _estimate_cart_subtotal(items)
	return _build_coupon_result(coupon_doc, resolved_subtotal, mobile=mobile or "", branch=branch or "")


def _otp_cache_key(mobile):
	return "restaurant_customer_otp:{0}".format(_ensure_mobile(mobile))


@frappe.whitelist(allow_guest=True)
def send_otp(mobile, customer_name=None):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	if not normalized_mobile:
		return ""
	otp = "".join(random.choices(string.digits, k=6))
	frappe.cache().set_value(_otp_cache_key(normalized_mobile), otp, expires_in_sec=300)
	result = {"success": True, "sent": 1, "mobile": normalized_mobile, "expires_in": 300}
	if cint(frappe.conf.get("developer_mode")):
		result["debug_otp"] = otp
	return result


@frappe.whitelist(allow_guest=True)
def verify_otp(mobile, otp=None, code=None, customer_name=None):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	if not normalized_mobile:
		return ""
	provided = (otp or code or "").strip()
	cached = frappe.cache().get_value(_otp_cache_key(normalized_mobile))
	if isinstance(cached, bytes):
		cached = cached.decode()
	if not provided or str(cached or "") != provided:
		frappe.throw(_("Invalid or expired OTP."), frappe.PermissionError)

	resolved_name = (customer_name or "").strip()
	customer_docname = _find_customer_by_mobile(normalized_mobile)
	if not customer_docname:
		customer_docname = _ensure_customer(resolved_name or normalized_mobile, normalized_mobile)
	elif not resolved_name:
		resolved_name = frappe.db.get_value("Customer", customer_docname, "customer_name") or ""
	frappe.cache().delete_value(_otp_cache_key(normalized_mobile))
	return {
		"success": True,
		"verified": 1,
		"mobile": normalized_mobile,
		"customer": {
			"customer_id": customer_docname,
			"name": resolved_name or normalized_mobile,
			"mobile": normalized_mobile,
		},
	}


@frappe.whitelist(allow_guest=True)
def customer_send_otp(mobile, customer_name=None):
	return send_otp(mobile=mobile, customer_name=customer_name)


@frappe.whitelist(allow_guest=True)
def customer_verify_otp(mobile, code=None, otp=None, customer_name=None):
	return verify_otp(mobile=mobile, otp=otp, code=code, customer_name=customer_name)


def _ensure_company_branch_fields():
	if not frappe.db.exists("DocType", "Company"):
		return

	field_defs = [
		{
			"fieldname": "restaurant_is_branch",
			"label": "Restaurant Branch",
			"fieldtype": "Check",
			"insert_after": "abbr",
			"default": "1",
		},
		{
			"fieldname": "restaurant_branch_active",
			"label": "Restaurant Branch Active",
			"fieldtype": "Check",
			"insert_after": "restaurant_is_branch",
			"default": "1",
		},
		{
			"fieldname": "restaurant_public_title",
			"label": "Restaurant Public Title",
			"fieldtype": "Data",
			"insert_after": "restaurant_branch_active",
		},
		{
			"fieldname": "restaurant_branch_address",
			"label": "Restaurant Branch Address",
			"fieldtype": "Small Text",
			"insert_after": "restaurant_public_title",
		},
		{
			"fieldname": "restaurant_branch_phone",
			"label": "Restaurant Branch Phone",
			"fieldtype": "Data",
			"insert_after": "restaurant_branch_address",
		},
		{
			"fieldname": "restaurant_branch_lat",
			"label": "Restaurant Branch Latitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_branch_phone",
		},
		{
			"fieldname": "restaurant_branch_lng",
			"label": "Restaurant Branch Longitude",
			"fieldtype": "Float",
			"insert_after": "restaurant_branch_lat",
		},
		{
			"fieldname": "restaurant_branch_image",
			"label": "Restaurant Branch Image",
			"fieldtype": "Attach Image",
			"insert_after": "restaurant_branch_lng",
		},
		{
			"fieldname": "restaurant_branch_map_url",
			"label": "Restaurant Branch Map URL",
			"fieldtype": "Data",
			"insert_after": "restaurant_branch_image",
		},
		{
			"fieldname": "restaurant_prep_time_mins",
			"label": "Default Preparation Time (mins)",
			"fieldtype": "Int",
			"insert_after": "restaurant_branch_map_url",
			"default": "20",
		},
		{
			"fieldname": "restaurant_pickup_available",
			"label": "Pickup Available",
			"fieldtype": "Check",
			"insert_after": "restaurant_prep_time_mins",
			"default": "1",
		},
		{
			"fieldname": "restaurant_delivery_available",
			"label": "Delivery Available",
			"fieldtype": "Check",
			"insert_after": "restaurant_pickup_available",
			"default": "1",
		},
		{
			"fieldname": "restaurant_delivery_eta_min",
			"label": "Delivery ETA Min",
			"fieldtype": "Int",
			"insert_after": "restaurant_delivery_available",
			"default": "35",
		},
		{
			"fieldname": "restaurant_delivery_eta_max",
			"label": "Delivery ETA Max",
			"fieldtype": "Int",
			"insert_after": "restaurant_delivery_eta_min",
			"default": "45",
		},
		{
			"fieldname": "restaurant_delivery_fee",
			"label": "Delivery Fee",
			"fieldtype": "Currency",
			"insert_after": "restaurant_delivery_eta_max",
			"default": "0",
		},
		{
			"fieldname": "restaurant_delivery_radius_km",
			"label": "Delivery Radius (km)",
			"fieldtype": "Float",
			"insert_after": "restaurant_delivery_fee",
			"default": "0",
		},
		{
			"fieldname": "restaurant_pricing_markup_percent",
			"label": "Restaurant Pricing Markup Percent",
			"fieldtype": "Percent",
			"insert_after": "restaurant_delivery_radius_km",
			"default": "0",
		},
	]

	changed = False
	for field_def in field_defs:
		existing_name = frappe.db.get_value(
			"Custom Field",
			{"dt": "Company", "fieldname": field_def["fieldname"]},
			"name",
		)
		payload = {
			"doctype": "Custom Field",
			"dt": "Company",
			"module": "Restaurant",
			**field_def,
		}
		if existing_name:
			doc = frappe.get_doc("Custom Field", existing_name)
			dirty = False
			for key, value in payload.items():
				if key == "doctype":
					continue
				if doc.get(key) != value:
					doc.set(key, value)
					dirty = True
			if dirty:
				doc.save(ignore_permissions=True)
				changed = True
			continue
		frappe.get_doc(payload).insert(ignore_permissions=True)
		changed = True

	if changed:
		frappe.clear_cache(doctype="Company")


def _current_weekday_name():
	return now_datetime().strftime("%A")


def _time_to_label(value):
	if value in (None, ""):
		return ""
	try:
		return str(get_time(value))[:5]
	except Exception:
		return str(value).strip()[:5]


def _is_now_between(opening_time, closing_time):
	if not opening_time or not closing_time:
		return True
	try:
		now_time = now_datetime().time()
		open_time = get_time(opening_time)
		close_time = get_time(closing_time)
		if open_time <= close_time:
			return open_time <= now_time <= close_time
		return now_time >= open_time or now_time <= close_time
	except Exception:
		return True


def _branch_schedule_map():
	if not _restaurant_doctype_exists("Restaurant Branch Schedule"):
		return {}
	weekday = _current_weekday_name()
	rows = frappe.get_all(
		"Restaurant Branch Schedule",
		fields=[
			"branch",
			"day_of_week",
			"is_open",
			"opening_time",
			"closing_time",
			"prep_time_mins",
			"pickup_available",
			"delivery_available",
			"delivery_eta_min",
			"delivery_eta_max",
			"delivery_fee",
			"delivery_radius_km",
		],
		filters={"day_of_week": weekday},
		ignore_permissions=True,
		limit_page_length=500,
	)
	return {(row.get("branch") or "").strip(): row for row in rows if (row.get("branch") or "").strip()}


def _apply_branch_schedule(payload, schedule=None):
	schedule = schedule or {}
	opening = schedule.get("opening_time")
	closing = schedule.get("closing_time")
	base_active = cint(payload.get("is_active") if payload.get("is_active") not in (None, "") else 1) == 1
	schedule_open = cint(schedule.get("is_open") if schedule.get("is_open") not in (None, "") else 1) == 1
	is_open = base_active and schedule_open and _is_now_between(opening, closing)
	open_label = "باز"
	if opening or closing:
		open_label = (
			f"باز تا {_time_to_label(closing)}"
			if is_open and closing
			else f"ساعت کاری {_time_to_label(opening)} تا {_time_to_label(closing)}"
		)
	if not is_open:
		open_label = "بسته"

	payload.update(
		{
			"isOpen": bool(is_open),
			"open_label": open_label,
			"opening_time": _time_to_label(opening),
			"closing_time": _time_to_label(closing),
			"hours": open_label,
			"prepTime": cint(schedule.get("prep_time_mins") or payload.get("prepTime") or 20),
			"prep_time_mins": cint(
				schedule.get("prep_time_mins")
				or payload.get("prep_time_mins")
				or payload.get("prepTime")
				or 20
			),
			"pickup_available": base_active
			and cint(
				schedule.get("pickup_available")
				if schedule.get("pickup_available") not in (None, "")
				else payload.get("pickup_available", 1)
			)
			== 1,
			"delivery_available": base_active
			and cint(
				schedule.get("delivery_available")
				if schedule.get("delivery_available") not in (None, "")
				else payload.get("delivery_available", 1)
			)
			== 1,
			"delivery_eta_min": cint(
				schedule.get("delivery_eta_min") or payload.get("delivery_eta_min") or 35
			),
			"delivery_eta_max": cint(
				schedule.get("delivery_eta_max") or payload.get("delivery_eta_max") or 45
			),
			"delivery_fee": flt(schedule.get("delivery_fee") or payload.get("delivery_fee") or 0),
			"delivery_radius_km": flt(
				schedule.get("delivery_radius_km") or payload.get("delivery_radius_km") or 0
			),
		}
	)
	return payload


def _company_branch_rows():
	_ensure_company_branch_fields()
	fields = ["name", "company_name", "default_currency"]
	optional_fields = [
		"restaurant_is_branch",
		"restaurant_branch_active",
		"restaurant_public_title",
		"restaurant_branch_address",
		"restaurant_branch_phone",
		"restaurant_branch_lat",
		"restaurant_branch_lng",
		"restaurant_branch_image",
		"restaurant_branch_map_url",
		"restaurant_prep_time_mins",
		"restaurant_pickup_available",
		"restaurant_delivery_available",
		"restaurant_delivery_eta_min",
		"restaurant_delivery_eta_max",
		"restaurant_delivery_fee",
		"restaurant_delivery_radius_km",
		"restaurant_pricing_markup_percent",
	]
	for fieldname in optional_fields:
		if _has_column("Company", fieldname):
			fields.append(fieldname)

	filters = {"is_group": 0} if _has_column("Company", "is_group") else {}
	if _has_column("Company", "restaurant_is_branch"):
		filters["restaurant_is_branch"] = 1

	rows = frappe.get_all(
		"Company",
		fields=fields,
		filters=filters,
		order_by="company_name asc",
		ignore_permissions=True,
		limit_page_length=200,
	)
	return rows


@frappe.whitelist(allow_guest=True)
def get_branches():
	branches = {}
	schedules = _branch_schedule_map()

	for row in _company_branch_rows():
		branch_name = (row.get("name") or "").strip()
		if not branch_name:
			continue
		lat = _to_bounded_float(row.get("restaurant_branch_lat"), minimum=-90, maximum=90)
		lng = _to_bounded_float(row.get("restaurant_branch_lng"), minimum=-180, maximum=180)
		map_url = row.get("restaurant_branch_map_url") or ""
		if not map_url and lat is not None and lng is not None:
			map_url = f"https://maps.google.com/?q={lat},{lng}"
		branches[branch_name.lower()] = _apply_branch_schedule(
			{
				"id": branch_name,
				"name": branch_name,
				"title": row.get("restaurant_public_title") or row.get("company_name") or branch_name,
				"address": row.get("restaurant_branch_address") or "",
				"phone": row.get("restaurant_branch_phone") or "",
				"lat": lat,
				"lng": lng,
				"is_active": cint(
					row.get("restaurant_branch_active")
					if row.get("restaurant_branch_active") not in (None, "")
					else 1
				),
				"company": branch_name,
				"currency": row.get("default_currency") or _get_currency(branch_name),
				"pricing_markup_percent": flt(row.get("restaurant_pricing_markup_percent") or 0),
				"prepTime": cint(row.get("restaurant_prep_time_mins") or 20),
				"prep_time_mins": cint(row.get("restaurant_prep_time_mins") or 20),
				"pickup_available": cint(
					row.get("restaurant_pickup_available")
					if row.get("restaurant_pickup_available") not in (None, "")
					else 1
				)
				== 1,
				"delivery_available": cint(
					row.get("restaurant_delivery_available")
					if row.get("restaurant_delivery_available") not in (None, "")
					else 1
				)
				== 1,
				"delivery_eta_min": cint(row.get("restaurant_delivery_eta_min") or 35),
				"delivery_eta_max": cint(row.get("restaurant_delivery_eta_max") or 45),
				"delivery_fee": flt(row.get("restaurant_delivery_fee") or 0),
				"delivery_radius_km": flt(row.get("restaurant_delivery_radius_km") or 0),
				"mapUrl": map_url or "https://maps.google.com",
				"image": row.get("restaurant_branch_image")
				or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=70",
			},
			schedules.get(branch_name),
		)

	if _restaurant_doctype_exists("Restaurant Branch Production Settings"):
		for row in frappe.get_all(
			"Restaurant Branch Production Settings",
			fields=["name", "branch", "is_active", "company", "pricing_markup_percent"],
			order_by="branch asc",
			ignore_permissions=True,
		):
			branch_name = (row.get("branch") or row.get("name") or "").strip()
			if branch_name:
				base = branches.get(branch_name.lower(), {})
				base.update(
					{
						"id": branch_name,
						"name": branch_name,
						"title": base.get("title") or branch_name,
						"address": base.get("address") or "",
						"phone": base.get("phone") or "",
						"is_active": cint(
							row.get("is_active") if row.get("is_active") not in (None, "") else 1
						),
						"company": row.get("company") or base.get("company") or branch_name,
						"pricing_markup_percent": flt(row.get("pricing_markup_percent") or 0),
						"prepTime": base.get("prepTime") or 20,
						"mapUrl": base.get("mapUrl") or "https://maps.google.com",
						"image": base.get("image")
						or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=70",
					}
				)
				base["isOpen"] = cint(
					row.get("is_active") if row.get("is_active") not in (None, "") else 1
				) == 1 and bool(base.get("isOpen", True))
				branches[branch_name.lower()] = _apply_branch_schedule(base, schedules.get(branch_name))

	if _restaurant_doctype_exists("Restaurant Table"):
		for row in frappe.get_all(
			"Restaurant Table",
			filters={"is_active": 1},
			fields=["location"],
			limit_page_length=500,
			ignore_permissions=True,
		):
			location = (row.get("location") or "").strip()
			if location and location.lower() not in branches:
				branches[location.lower()] = _apply_branch_schedule(
					{
						"id": location,
						"name": location,
						"title": location,
						"address": "",
						"phone": "",
						"is_active": 1,
						"prepTime": 20,
						"mapUrl": "https://maps.google.com",
						"image": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=70",
					},
					schedules.get(location),
				)

	if not branches:
		branches["default"] = _apply_branch_schedule(
			{
				"id": "DEFAULT",
				"name": "شعبه اصلی",
				"title": "شعبه اصلی",
				"address": "",
				"phone": "",
				"is_active": 1,
				"prepTime": 20,
				"mapUrl": "https://maps.google.com",
				"image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&auto=format&fit=crop&q=70",
			},
			schedules.get("DEFAULT"),
		)
	return {"branches": list(branches.values())}


def _reservation_time_key(value):
	if value in (None, ""):
		return ""
	try:
		return str(get_time(value))[:5]
	except Exception:
		return str(value).strip()[:5]


@frappe.whitelist(allow_guest=True)
def get_available_tables(branch=None, reservation_date=None, reservation_time=None, guest_count=1):
	if not _restaurant_doctype_exists("Restaurant Table"):
		return {"tables": []}
	filters = {"is_active": 1}
	branch = (branch or "").strip()
	if branch:
		filters["location"] = branch

	reserved = set()
	if _restaurant_doctype_exists("Restaurant Table Reservation") and reservation_date and reservation_time:
		for row in frappe.get_all(
			"Restaurant Table Reservation",
			filters={
				"reservation_date": getdate(reservation_date),
				"status": ["in", ["pending", "confirmed"]],
			},
			fields=["table", "reservation_time"],
			limit_page_length=500,
			ignore_permissions=True,
		):
			if row.get("table") and _reservation_time_key(
				row.get("reservation_time")
			) == _reservation_time_key(reservation_time):
				reserved.add(row.get("table"))

	tables = []
	for row in frappe.get_all(
		"Restaurant Table",
		filters=filters,
		fields=["name", "table_number", "status", "location"],
		order_by="table_number asc",
		limit_page_length=500,
		ignore_permissions=True,
	):
		status = (row.get("status") or "empty").strip().lower()
		available = status in {"empty", "available"} and row.name not in reserved
		tables.append(
			{
				"id": row.name,
				"name": row.name,
				"label": row.get("table_number") or row.name,
				"table_number": row.get("table_number") or row.name,
				"branch": row.get("location") or "",
				"area": row.get("location") or "main",
				"capacity": max(cint(guest_count), 1),
				"status": "available" if available else ("reserved" if row.name in reserved else "occupied"),
				"is_available": 1 if available else 0,
				"shape": "rect",
			}
		)
	return {"tables": tables}


@frappe.whitelist(allow_guest=True)
def create_table_reservation(payload=None, **kwargs):
	if not _restaurant_doctype_exists("Restaurant Table Reservation"):
		frappe.throw(_("Restaurant Table Reservation doctype is not installed."))
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	customer_name = (data.get("customer_name") or data.get("name") or "").strip()
	if not customer_name:
		frappe.throw(_("Customer name is required."))
	mobile = _ensure_mobile(data.get("mobile") or data.get("phone"))
	reservation_date = data.get("reservation_date") or data.get("date")
	reservation_time = data.get("reservation_time") or data.get("time")
	if not reservation_date or not reservation_time:
		frappe.throw(_("Reservation date and time are required."))
	guest_count = max(cint(data.get("guest_count") or data.get("guests") or 1), 1)
	table_name = (data.get("table") or data.get("table_id") or "").strip()
	branch = (data.get("branch") or "").strip()

	if table_name:
		available = get_available_tables(
			branch=branch,
			reservation_date=reservation_date,
			reservation_time=reservation_time,
			guest_count=guest_count,
		).get("tables", [])
		if not any(t.get("id") == table_name and t.get("is_available") for t in available):
			frappe.throw(_("Selected table is not available for this date and time."))

	doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Reservation",
			"customer_name": customer_name,
			"mobile": mobile,
			"branch": branch,
			"table": table_name,
			"reservation_date": getdate(reservation_date),
			"reservation_time": reservation_time,
			"guest_count": guest_count,
			"status": data.get("status") or "pending",
			"note": data.get("note") or "",
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"reservation": {
			"name": doc.name,
			"customer_name": doc.customer_name,
			"mobile": doc.mobile,
			"branch": doc.branch,
			"table": doc.table,
			"reservation_date": str(doc.reservation_date),
			"reservation_time": str(doc.reservation_time),
			"guest_count": cint(doc.guest_count),
			"status": doc.status,
			"note": doc.note,
		},
	}


@frappe.whitelist()
def get_management_tables():
	_ensure_management_site_settings_access()

	tables = []
	if _restaurant_doctype_exists("Restaurant Table"):
		table_fields = ["name", "table_number", "status", "is_active", "location", "active_session", "notes"]
		table_rows = frappe.get_all(
			"Restaurant Table",
			fields=table_fields,
			order_by="table_number asc, modified desc",
			ignore_permissions=True,
			limit_page_length=500,
		)
		for row in table_rows:
			tables.append(
				{
					"name": row.get("name"),
					"table_number": row.get("table_number") or row.get("name"),
					"status": (row.get("status") or "empty").strip().lower() or "empty",
					"is_active": cint(row.get("is_active") or 0),
					"location": row.get("location") or "",
					"active_session": row.get("active_session") or "",
					"notes": row.get("notes") or "",
				}
			)

	reservations = []
	if _restaurant_doctype_exists("Restaurant Table Reservation"):
		reservation_rows = frappe.get_all(
			"Restaurant Table Reservation",
			fields=[
				"name",
				"customer_name",
				"mobile",
				"branch",
				"table",
				"reservation_date",
				"reservation_time",
				"guest_count",
				"status",
				"note",
			],
			order_by="reservation_date desc, reservation_time desc, modified desc",
			ignore_permissions=True,
			limit_page_length=500,
		)
		for row in reservation_rows:
			reservations.append(
				{
					"name": row.get("name"),
					"customer_name": row.get("customer_name") or "",
					"mobile": row.get("mobile") or "",
					"branch": row.get("branch") or "",
					"table": row.get("table") or "",
					"reservation_date": str(row.get("reservation_date") or ""),
					"reservation_time": str(row.get("reservation_time") or ""),
					"guest_count": cint(row.get("guest_count") or 0),
					"status": (row.get("status") or "pending").strip().lower() or "pending",
					"note": row.get("note") or "",
				}
			)

	sessions = []
	if _restaurant_doctype_exists("Restaurant Table Session"):
		session_rows = frappe.get_all(
			"Restaurant Table Session",
			fields=["name", "table", "status", "opened_at", "closed_at", "total_confirmed_amount", "note"],
			order_by="opened_at desc, modified desc",
			ignore_permissions=True,
			limit_page_length=500,
		)
		for row in session_rows:
			customer_payload = _sanitize_table_session_customer(_extract_table_session_meta(row.get("note")))
			sessions.append(
				{
					"name": row.get("name"),
					"table": row.get("table") or "",
					"status": (row.get("status") or "active").strip().lower() or "active",
					"opened_at": str(row.get("opened_at") or ""),
					"closed_at": str(row.get("closed_at") or ""),
					"total_confirmed_amount": flt(row.get("total_confirmed_amount") or 0),
					"note": row.get("note") or "",
					**customer_payload,
				}
			)

	return {"tables": tables, "reservations": reservations, "sessions": sessions}


@frappe.whitelist()
def create_management_table(payload=None, **kwargs):
	_ensure_management_site_settings_access()
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	table_number = (data.get("table_number") or data.get("name") or "").strip()
	if not table_number:
		frappe.throw(_("Table number or name is required."))
	if not _restaurant_doctype_exists("Restaurant Table"):
		frappe.throw(_("Restaurant Table doctype is not installed."))
	if frappe.db.exists("Restaurant Table", table_number):
		frappe.throw(_("A table with this name already exists."))
	if frappe.db.exists("Restaurant Table", {"table_number": table_number}):
		frappe.throw(_("A table with this number already exists."))

	doc = frappe.new_doc("Restaurant Table")
	# Keep the user-facing number as the document name when the doctype allows it;
	# otherwise Frappe will generate a safe name automatically.
	if doc.meta.autoname == "field:table_number":
		doc.table_number = table_number
	else:
		doc.table_number = table_number
	for fieldname in ("status", "location", "notes", "active_session"):
		if fieldname in data and _has_column("Restaurant Table", fieldname):
			doc.set(fieldname, data.get(fieldname) or "")
	if _has_column("Restaurant Table", "is_active"):
		doc.is_active = 1 if data.get("is_active", 1) else 0
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"table": {
			"name": doc.name,
			"table_number": doc.table_number or table_number,
			"status": doc.status or "empty",
			"is_active": cint(doc.is_active),
			"location": doc.location or "",
			"active_session": doc.active_session or "",
			"notes": doc.notes or "",
		},
	}


@frappe.whitelist()
def delete_management_table(name=None, **kwargs):
	_ensure_management_site_settings_access()
	table_name = (name or kwargs.get("name") or "").strip()
	if not table_name or not frappe.db.exists("Restaurant Table", table_name):
		frappe.throw(_("Table not found."))
	if _restaurant_doctype_exists("Restaurant Table Session") and frappe.db.exists(
		"Restaurant Table Session", {"table": table_name, "status": "active"}
	):
		frappe.throw(_("Close the active table session before deleting this table."))
	if _restaurant_doctype_exists("Restaurant Table Reservation") and frappe.db.exists(
		"Restaurant Table Reservation", {"table": table_name, "status": ["in", ["pending", "confirmed"]]}
	):
		frappe.throw(_("Cancel or complete the table reservations before deleting this table."))
	frappe.delete_doc("Restaurant Table", table_name, force=1, ignore_permissions=True)
	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def update_management_table(payload=None, **kwargs):
	_ensure_management_site_settings_access()
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	table_name = (data.get("name") or data.get("table") or "").strip()
	if not table_name or not frappe.db.exists("Restaurant Table", table_name):
		frappe.throw(_("Table not found."))

	doc = frappe.get_doc("Restaurant Table", table_name)
	if "table_number" in data:
		doc.table_number = (data.get("table_number") or "").strip() or doc.table_number
	if "status" in data:
		status = (data.get("status") or "").strip().lower() or "empty"
		if status not in {"empty", "occupied", "waiting"}:
			status = "empty"
		doc.status = status
	if "is_active" in data:
		doc.is_active = cint(data.get("is_active") or 0)
	if "location" in data:
		doc.location = (data.get("location") or "").strip()
	if "notes" in data:
		doc.notes = data.get("notes") or ""
	if "active_session" in data and _has_column("Restaurant Table", "active_session"):
		doc.active_session = (data.get("active_session") or "").strip()

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"table": {
			"name": doc.name,
			"table_number": doc.table_number,
			"status": doc.status,
			"is_active": cint(doc.is_active),
			"location": doc.location or "",
			"active_session": doc.active_session or "",
			"notes": doc.notes or "",
		},
	}


@frappe.whitelist()
def update_management_table_reservation(payload=None, **kwargs):
	_ensure_management_site_settings_access()
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	reservation_name = (data.get("name") or "").strip()
	if not reservation_name or not frappe.db.exists("Restaurant Table Reservation", reservation_name):
		frappe.throw(_("Reservation not found."))

	doc = frappe.get_doc("Restaurant Table Reservation", reservation_name)
	if "customer_name" in data:
		doc.customer_name = (data.get("customer_name") or "").strip()
	if "mobile" in data:
		doc.mobile = _ensure_mobile(data.get("mobile") or doc.mobile)
	if "branch" in data:
		doc.branch = (data.get("branch") or "").strip()
	if "table" in data:
		doc.table = (data.get("table") or "").strip()
	if "reservation_date" in data and data.get("reservation_date"):
		doc.reservation_date = getdate(data.get("reservation_date"))
	if "reservation_time" in data and data.get("reservation_time"):
		doc.reservation_time = data.get("reservation_time")
	if "guest_count" in data:
		doc.guest_count = max(cint(data.get("guest_count") or 1), 1)
	if "status" in data:
		status = (data.get("status") or "").strip().lower() or "pending"
		if status not in {"pending", "confirmed", "cancelled", "completed"}:
			status = "pending"
		doc.status = status
	if "note" in data:
		doc.note = data.get("note") or ""

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"reservation": {
			"name": doc.name,
			"customer_name": doc.customer_name,
			"mobile": doc.mobile,
			"branch": doc.branch or "",
			"table": doc.table or "",
			"reservation_date": str(doc.reservation_date or ""),
			"reservation_time": str(doc.reservation_time or ""),
			"guest_count": cint(doc.guest_count or 0),
			"status": doc.status or "pending",
			"note": doc.note or "",
		},
	}


@frappe.whitelist()
def update_management_table_session(payload=None, **kwargs):
	_ensure_management_site_settings_access()
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	session_name = (data.get("name") or "").strip()
	if not session_name or not frappe.db.exists("Restaurant Table Session", session_name):
		frappe.throw(_("Session not found."))

	doc = frappe.get_doc("Restaurant Table Session", session_name)
	if "status" in data:
		status = (data.get("status") or "").strip().lower() or "active"
		if status not in {"active", "closed"}:
			status = "active"
		doc.status = status
	if "note" in data:
		doc.note = data.get("note") or ""
	if "closed_at" in data and data.get("closed_at"):
		doc.closed_at = data.get("closed_at")
	if "opened_at" in data and data.get("opened_at"):
		doc.opened_at = data.get("opened_at")

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"session": {
			"name": doc.name,
			"table": doc.table or "",
			"status": doc.status or "active",
			"opened_at": str(doc.opened_at or ""),
			"closed_at": str(doc.closed_at or ""),
			"total_confirmed_amount": flt(doc.total_confirmed_amount or 0),
			"note": doc.note or "",
		},
	}


def _resolve_review_item(item_slug="", item=""):
	item = (item or "").strip()
	if item and frappe.db.exists("Item", item):
		return item
	slug = _normalize_slug(item_slug)
	if slug and _has_column("Item", "restaurant_slug"):
		return frappe.db.get_value("Item", {"restaurant_slug": slug}, "name") or ""
	return ""


@frappe.whitelist(allow_guest=True)
def submit_review(payload=None, **kwargs):
	if not _restaurant_doctype_exists("Restaurant Customer Review"):
		frappe.throw(_("Restaurant Customer Review doctype is not installed."))
	data = _parse_json(payload, {}) if payload is not None else {}
	if not isinstance(data, dict):
		data = {}
	data.update({k: v for k, v in kwargs.items() if v is not None})

	customer_name = (data.get("customer_name") or data.get("name") or "").strip()
	if not customer_name:
		frappe.throw(_("Customer name is required."))
	mobile = _ensure_mobile(data.get("mobile") or data.get("phone"))
	rating = flt(data.get("rating") or 0)
	if rating < 1 or rating > 5:
		frappe.throw(_("Rating must be between 1 and 5."))
	item_slug = _normalize_slug(data.get("item_slug") or data.get("slug") or "")
	item_name = _resolve_review_item(item_slug=item_slug, item=data.get("item"))
	order_code = (data.get("order_code") or "").strip()
	sales_order = _resolve_sales_order_name(order_code) if order_code else ""

	doc = frappe.get_doc(
		{
			"doctype": "Restaurant Customer Review",
			"customer_name": customer_name,
			"mobile": mobile,
			"item": item_name,
			"item_slug": item_slug,
			"sales_order": sales_order,
			"order_code": order_code,
			"rating": rating,
			"title": data.get("title") or "",
			"comment": data.get("comment") or "",
			"is_approved": cint(data.get("is_approved") if data.get("is_approved") not in (None, "") else 0),
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {
		"success": True,
		"review": {"name": doc.name, "rating": rating, "is_approved": cint(doc.is_approved)},
	}


@frappe.whitelist(allow_guest=True)
def get_item_reviews(item_slug=None, item=None, page=1, page_size=20):
	if not _restaurant_doctype_exists("Restaurant Customer Review"):
		return {"reviews": [], "average_rating": 0, "count": 0}
	filters = {"is_approved": 1}
	item_name = _resolve_review_item(item_slug=item_slug, item=item)
	if item_name:
		filters["item"] = item_name
	elif item_slug:
		filters["item_slug"] = _normalize_slug(item_slug)
	page = max(cint(page), 1)
	page_size = min(max(cint(page_size), 1), MAX_PAGE_SIZE)
	rows = frappe.get_all(
		"Restaurant Customer Review",
		filters=filters,
		fields=["name", "customer_name", "rating", "title", "comment", "creation"],
		order_by="creation desc",
		start=(page - 1) * page_size,
		limit_page_length=page_size,
		ignore_permissions=True,
	)
	all_ratings = frappe.get_all(
		"Restaurant Customer Review",
		filters=filters,
		fields=["rating"],
		limit_page_length=1000,
		ignore_permissions=True,
	)
	count = len(all_ratings)
	average = flt(sum(flt(r.get("rating") or 0) for r in all_ratings) / count) if count else 0
	return {
		"reviews": [
			{
				"name": row.name,
				"customer_name": row.customer_name,
				"rating": flt(row.rating),
				"title": row.title,
				"comment": row.comment,
				"created_at": str(row.creation),
			}
			for row in rows
		],
		"average_rating": average,
		"count": count,
	}


@frappe.whitelist(allow_guest=True)
def get_customer_orders(mobile, limit=50, start=0):
	mobile = _ensure_mobile(mobile)
	limit = min(max(cint(limit), 1), 100)
	start = max(cint(start), 0)
	filters = {}
	if _has_column("Sales Order", "restaurant_customer_mobile"):
		filters["restaurant_customer_mobile"] = mobile
	else:
		customer = _find_customer_by_mobile(mobile)
		if not customer:
			return {"orders": []}
		filters["customer"] = customer
	rows = frappe.get_all(
		"Sales Order",
		filters=filters,
		fields=["name", "creation"],
		order_by="creation desc",
		start=start,
		limit_page_length=limit,
		ignore_permissions=True,
	)
	orders = []
	for row in rows:
		try:
			orders.append(_get_sales_order_payload(row.name).get("order"))
		except Exception:
			continue
	return {"orders": [o for o in orders if o]}


@frappe.whitelist(allow_guest=True)
def get_customer_profile(mobile=None, customer_name=None):
	profile = get_customer_checkout_profile(mobile=mobile, customer_name=customer_name)
	profile["orders"] = get_customer_orders(mobile=mobile, limit=10).get("orders", []) if mobile else []
	try:
		customer_id = (profile.get("customer") or {}).get("customer_id") or ""
		profile["club"] = get_customer_club_summary(customer_id)
	except Exception:
		profile["club"] = {"wallet_balance": 0.0, "points_balance": 0, "loyalty_tier": "", "points_enabled": False}
	return profile


@frappe.whitelist(allow_guest=True)
def get_customer_checkout_profile(mobile, customer_name=None):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	if not normalized_mobile:
		return ""
	customer_docname = _find_customer_by_mobile(normalized_mobile)

	resolved_name = (customer_name or "").strip()
	addresses = []
	vehicles = []
	if customer_docname:
		if not resolved_name:
			resolved_name = frappe.db.get_value("Customer", customer_docname, "customer_name") or ""
		addresses = _list_customer_delivery_addresses(customer_docname)
		vehicles = _list_customer_vehicles(customer_name=customer_docname)

	return {
		"customer": {
			"name": resolved_name,
			"mobile": normalized_mobile,
			"customer_id": customer_docname or "",
		},
		"addresses": addresses,
		"vehicles": vehicles,
	}


@frappe.whitelist(allow_guest=True)
def save_customer_vehicle(customer_info, vehicle_info):
	customer_payload = _parse_json(customer_info, {})
	customer_name = (customer_payload.get("name") or customer_payload.get("customer_name") or "").strip()
	if not customer_name:
		frappe.throw(_("Customer name is required."))

	mobile = _ensure_mobile(customer_payload.get("mobile") or customer_payload.get("phone"))
	customer_docname = _ensure_customer(customer_name, mobile)

	normalized_vehicle = _normalize_vehicle_payload(
		vehicle_info, customer_name=customer_docname, mobile=mobile
	)
	saved_vehicle = _upsert_customer_vehicle(customer_docname, normalized_vehicle, mark_used=False)
	frappe.db.commit()

	return {
		"customer": {
			"name": customer_name,
			"mobile": mobile,
			"customer_id": customer_docname,
		},
		"vehicle": saved_vehicle,
		"vehicles": _list_customer_vehicles(customer_name=customer_docname),
	}


@frappe.whitelist(allow_guest=True)
def get_customer_vehicles(mobile, customer_name=None):
	normalized_mobile = _ensure_mobile(mobile, allow_empty=True)
	if not normalized_mobile:
		return ""
	customer_docname = _find_customer_by_mobile(normalized_mobile)
	if not customer_docname:
		return {
			"vehicles": [],
			"customer": {"name": customer_name or "", "mobile": normalized_mobile, "customer_id": ""},
		}
	return {
		"customer": {
			"name": frappe.db.get_value("Customer", customer_docname, "customer_name") or customer_name or "",
			"mobile": normalized_mobile,
			"customer_id": customer_docname,
		},
		"vehicles": _list_customer_vehicles(customer_name=customer_docname),
	}


@frappe.whitelist(allow_guest=True)
def save_customer_delivery_address(customer_info, address_info):
	customer_payload = _parse_json(customer_info, {})
	customer_name = (customer_payload.get("name") or customer_payload.get("customer_name") or "").strip()
	if not customer_name:
		frappe.throw(_("Customer name is required."))

	mobile = _ensure_mobile(customer_payload.get("mobile") or customer_payload.get("phone"))
	customer_docname = _ensure_customer(customer_name, mobile)

	normalized_address = _normalize_address_payload(address_info, customer_name=customer_name, mobile=mobile)
	saved_address = _upsert_customer_delivery_address(customer_docname, normalized_address)

	if _has_column("Customer", "mobile_no"):
		current_mobile = frappe.db.get_value("Customer", customer_docname, "mobile_no")
		if not current_mobile:
			frappe.db.set_value("Customer", customer_docname, "mobile_no", mobile, update_modified=False)

	frappe.db.commit()
	return {
		"customer": {
			"name": customer_name,
			"mobile": mobile,
			"customer_id": customer_docname,
		},
		"address": saved_address,
		"addresses": _list_customer_delivery_addresses(customer_docname),
	}


@frappe.whitelist(allow_guest=True)
def place_order(
	customer_info,
	order_type=None,
	items=None,
	address=None,
	note=None,
	include_service_items=1,
	delivery_mode=None,
	delivery_address_id=None,
	delivery_address_snapshot=None,
	pickup_method=None,
	pickup_vehicle_id=None,
	pickup_vehicle_snapshot=None,
	coupon_code=None,
	order_context=None,
	financial_modifiers=None,
	totals=None,
	commit=True,
):
	customer_info = _parse_json(customer_info, {})
	cart_items = _normalize_cart_items(items)
	order_type, resolved_delivery_mode = _resolve_order_type_and_delivery_mode(
		order_type=order_type,
		delivery_mode=delivery_mode,
	)

	customer_name = (customer_info.get("name") or customer_info.get("customer_name") or "").strip()
	if not customer_name:
		frappe.throw(_("Customer name is required."))

	mobile = _ensure_mobile(customer_info.get("mobile") or customer_info.get("phone"))
	note = (note or "").strip()
	include_service_items = cint(include_service_items)
	coupon_code = (coupon_code or "").strip()
	delivery_address_id = (delivery_address_id or "").strip()
	pickup_method = (pickup_method or "").strip().lower()
	pickup_vehicle_id = (pickup_vehicle_id or "").strip()
	legacy_address = (address or "").strip()
	snapshot_payload = _parse_json(delivery_address_snapshot, {})
	has_snapshot_payload = isinstance(snapshot_payload, dict) and bool(snapshot_payload)
	is_legacy_delivery = (
		order_type == "delivery"
		and not (delivery_mode or "").strip()
		and not delivery_address_id
		and not has_snapshot_payload
	)

	delivery_payload = {}
	delivery_text = ""
	if is_legacy_delivery:
		if not legacy_address:
			frappe.throw(_("Address is required for delivery."))
		delivery_text = legacy_address
	elif order_type == "delivery" or resolved_delivery_mode == "delivery":
		customer_docname = _ensure_customer(customer_name, mobile)
		delivery_payload = _resolve_delivery_address_for_order(
			customer_name=customer_docname,
			mobile=mobile,
			delivery_address_id=delivery_address_id,
			delivery_snapshot=delivery_address_snapshot,
			legacy_address=legacy_address,
			customer_display_name=customer_name,
		)
		delivery_address_id = delivery_payload.get("id") or delivery_address_id
		delivery_text = _format_delivery_text(delivery_payload)
		if not delivery_text:
			frappe.throw(_("Address is required for delivery."))

		delivery_lat, delivery_lng = _normalize_delivery_geo(
			delivery_payload.get("lat"),
			delivery_payload.get("lng"),
			required=True,
		)
		delivery_payload["lat"] = delivery_lat
		delivery_payload["lng"] = delivery_lng
	else:
		delivery_text = legacy_address if order_type == "dine_in" else ""

	pickup_vehicle_payload = {}
	if order_type == "takeaway" and resolved_delivery_mode == "pickup" and pickup_method == "car":
		customer_docname = _ensure_customer(customer_name, mobile)
		pickup_vehicle_payload = _resolve_customer_vehicle_for_order(
			customer_name=customer_docname,
			mobile=mobile,
			vehicle_id=pickup_vehicle_id,
			vehicle_snapshot=pickup_vehicle_snapshot,
		)

	financial_modifiers = financial_modifiers or {}
	# Direct parameter takes precedence, then financial_modifiers fallback
	resolved_coupon_code = (coupon_code or "").strip() or financial_modifiers.get("coupon_code") or ""
	coupon = _validate_coupon_for_cart(resolved_coupon_code, cart_items, mobile=mobile) if resolved_coupon_code else {}

	return _create_sales_order(
		customer_name=customer_name,
		mobile=mobile,
		order_type=order_type,
		address=delivery_text,
		note=note,
		cart_items=cart_items,
		include_service_items=bool(include_service_items),
		delivery_address_name=delivery_address_id,
		delivery_payload=delivery_payload,
		coupon=coupon,
		order_context=order_context,
		financial_modifiers=financial_modifiers,
		totals=totals,
		commit=commit,
	)


def _status_timeline(current_status):
	ordered = ["new", "confirmed", "preparing", "ready", "delivered"]
	if current_status == "cancelled":
		return [{"status": "cancelled", "done": True}]

	current_index = ordered.index(current_status) if current_status in ordered else 0
	timeline = []
	for idx, status in enumerate(ordered):
		timeline.append({"status": status, "done": idx <= current_index})
	return timeline


@frappe.whitelist(allow_guest=True)
def get_order(order_code, mobile):
	order_code = (order_code or "").strip()
	mobile = _ensure_mobile(mobile)
	if not order_code:
		frappe.throw(_("Order code is required."))

	so_name = frappe.db.get_value(
		"Sales Order",
		{

			"restaurant_customer_mobile": mobile,
		},
		"name",
	)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)
	return _get_sales_order_payload(so_name)


@frappe.whitelist(allow_guest=True)
def get_order_production_status(order_code, mobile):
	order_code = (order_code or "").strip()
	mobile = _ensure_mobile(mobile)
	if not order_code:
		frappe.throw(_("Order code is required."))

	so_name = frappe.db.get_value(
		"Sales Order",
		{

			"restaurant_customer_mobile": mobile,
		},
		"name",
	)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	tickets = []
	work_order_names = set()
	if frappe.db.exists("DocType", "Restaurant Production Ticket"):
		ticket_rows = frappe.get_all(
			"Restaurant Production Ticket",
			fields=[
				"name",
				"sales_order_item",
				"menu_item_name",
				"qty",
				"status",
				"work_order",
				"bom_template",
			],
			filters={"sales_order": so_name},
			order_by="creation asc",
			ignore_permissions=True,
		)
		for row in ticket_rows:
			tickets.append(
				{
					"name": row.name,
					"sales_order_item": row.sales_order_item,
					"menu_item_name": row.menu_item_name,
					"qty": flt(row.qty),
					"status": row.status,
					"work_order": row.work_order or "",
					"bom_template": row.bom_template or "",
				}
			)
			if row.work_order:
				work_order_names.add(row.work_order)

	work_orders = []
	if work_order_names:
		for wo in frappe.get_all(
			"Work Order",
			fields=["name", "status", "production_item", "qty", "produced_qty"],
			filters={"name": ["in", list(work_order_names)]},
			ignore_permissions=True,
		):
			work_orders.append(
				{
					"name": wo.name,
					"status": wo.status,
					"production_item": wo.production_item,
					"qty": flt(wo.qty),
					"produced_qty": flt(wo.produced_qty),
				}
			)

	return {
		"order_code": order_code,
		"sales_order": so_name,
		"production_tickets": tickets,
		"work_orders": work_orders,
	}


def _resolve_sales_order_name(order_name):
	so_name = (order_name or "").strip()
	if not so_name:
		return ""
	if frappe.db.exists("Sales Order", so_name):
		return so_name

		if mapped:
			return mapped
	return ""


def _extract_qty_map_from_ticket(ticket_doc, target_qty=None):
	qty_map = defaultdict(float)
	scale_factor = 1.0
	ticket_qty = flt(ticket_doc.get("qty") or 0)
	requested_qty = flt(target_qty or 0)
	if requested_qty > 1e-8 and ticket_qty > 1e-8:
		scale_factor = requested_qty / ticket_qty

	for row in ticket_doc.get("components") or []:
		item_code = (row.get("item_code") or "").strip()
		final_qty = flt(row.get("final_qty") or 0)
		if not item_code or final_qty <= 1e-8 or not _item_consumes_stock(item_code):
			continue
		qty_map[item_code] += final_qty * scale_factor
	return qty_map


def _resolve_ticket_for_work_order_doc(work_order_doc):
	if not frappe.db.exists("DocType", "Restaurant Production Ticket"):
		return None

	explicit_ticket = (
		(work_order_doc.get("restaurant_production_ticket") if hasattr(work_order_doc, "get") else None) or ""
	).strip()
	if explicit_ticket and frappe.db.exists("Restaurant Production Ticket", explicit_ticket):
		return frappe.get_doc("Restaurant Production Ticket", explicit_ticket)

	sales_order_item = (
		(work_order_doc.get("sales_order_item") if hasattr(work_order_doc, "get") else None)
		or (work_order_doc.get("restaurant_sales_order_item") if hasattr(work_order_doc, "get") else None)
		or ""
	).strip()
	if sales_order_item:
		linked_ticket = ""
		if _has_column("Sales Order Item", "restaurant_production_ticket"):
			linked_ticket = (
				frappe.db.get_value("Sales Order Item", sales_order_item, "restaurant_production_ticket")
				or ""
			).strip()
		if not linked_ticket and _has_column("Restaurant Production Ticket", "sales_order_item"):
			linked_ticket = (
				frappe.db.get_value(
					"Restaurant Production Ticket", {"sales_order_item": sales_order_item}, "name"
				)
				or ""
			).strip()
		if linked_ticket and frappe.db.exists("Restaurant Production Ticket", linked_ticket):
			return frappe.get_doc("Restaurant Production Ticket", linked_ticket)

	sales_order = (
		(work_order_doc.get("sales_order") if hasattr(work_order_doc, "get") else None) or ""
	).strip()
	production_item = (
		(work_order_doc.get("production_item") if hasattr(work_order_doc, "get") else None) or ""
	).strip()
	if sales_order:
		fallback_filters = {"sales_order": sales_order}
		if production_item and _has_column("Restaurant Production Ticket", "menu_item"):
			fallback_filters["menu_item"] = production_item
		candidates = frappe.get_all(
			"Restaurant Production Ticket",
			filters=fallback_filters,
			fields=["name"],
			order_by="creation desc",
			limit_page_length=1,
			ignore_permissions=True,
		)
		if candidates:
			return frappe.get_doc("Restaurant Production Ticket", candidates[0].name)

	return None


def sync_work_order_required_items_from_ticket(doc, method=None):
	if not doc or not getattr(doc, "name", None):
		return
	if cint(doc.get("docstatus") or 0) != 0:
		return

	ticket_doc = _resolve_ticket_for_work_order_doc(doc)
	if not ticket_doc:
		return

	qty_map = _extract_qty_map_from_ticket(ticket_doc, target_qty=flt(doc.get("qty") or 0))
	if not qty_map:
		return

	updates = {}
	if _has_column("Work Order", "restaurant_production_ticket"):
		current_ticket = (doc.get("restaurant_production_ticket") or "").strip()
		if current_ticket != ticket_doc.name:
			updates["restaurant_production_ticket"] = ticket_doc.name
	if (
		_has_column("Work Order", "restaurant_sales_order")
		and not (doc.get("restaurant_sales_order") or "").strip()
	):
		updates["restaurant_sales_order"] = (doc.get("sales_order") or "").strip()
	if (
		_has_column("Work Order", "restaurant_sales_order_item")
		and not (doc.get("restaurant_sales_order_item") or "").strip()
	):
		updates["restaurant_sales_order_item"] = (doc.get("sales_order_item") or "").strip()

	if updates:
		frappe.db.set_value("Work Order", doc.name, updates, update_modified=False)

	source_warehouse = (doc.get("source_warehouse") or "").strip() or (
		ticket_doc.get("source_warehouse") or ""
	).strip()
	_sync_work_order_required_items(doc.name, qty_map=qty_map, source_warehouse=source_warehouse)

	if _has_column("Restaurant Production Ticket", "work_order"):
		linked_wo = (ticket_doc.get("work_order") or "").strip()
		if not linked_wo:
			frappe.db.set_value(
				"Restaurant Production Ticket",
				ticket_doc.name,
				"work_order",
				doc.name,
				update_modified=False,
			)


@frappe.whitelist()
def sync_order_work_orders(order_name):
	_ensure_management_access()

	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	so_doc = frappe.get_doc("Sales Order", so_name)
	created_work_orders = []
	synced_work_orders = []
	skipped_tickets = []

	if not frappe.db.exists("DocType", "Restaurant Production Ticket"):
		production_payload = _create_production_for_sales_order(so_doc)
		frappe.db.commit()
		return {
			"status": "success",
			"sales_order": so_name,
			"created_work_orders": production_payload.get("work_orders") or [],
			"synced_work_orders": [],
			"skipped_tickets": production_payload.get("skipped_items") or [],
		}

	ticket_names = frappe.get_all(
		"Restaurant Production Ticket",
		filters={"sales_order": so_name},
		pluck="name",
		order_by="creation asc",
		ignore_permissions=True,
	)
	if not ticket_names:
		production_payload = _create_production_for_sales_order(so_doc)
		frappe.db.commit()
		return {
			"status": "success",
			"sales_order": so_name,
			"created_work_orders": production_payload.get("work_orders") or [],
			"synced_work_orders": [],
			"skipped_tickets": production_payload.get("skipped_items") or [],
		}

	so_item_map = {row.name: row for row in so_doc.items or []}
	for ticket_name in ticket_names:
		ticket_doc = frappe.get_doc("Restaurant Production Ticket", ticket_name)
		if ticket_doc.get("work_order") and frappe.db.exists("Work Order", ticket_doc.work_order):
			qty_map = _extract_qty_map_from_ticket(
				ticket_doc,
				target_qty=flt(frappe.db.get_value("Work Order", ticket_doc.work_order, "qty") or 0),
			)
			if not qty_map:
				skipped_tickets.append({"ticket": ticket_name, "reason": "empty_components"})
				continue
			source_warehouse = (
				(ticket_doc.get("source_warehouse") or "").strip()
				or frappe.db.get_value("Work Order", ticket_doc.get("work_order"), "source_warehouse")
				or ""
			)
			_sync_work_order_required_items(
				ticket_doc.work_order, qty_map=qty_map, source_warehouse=source_warehouse
			)
			synced_work_orders.append(ticket_doc.work_order)
			continue

		existing_wo = frappe.get_all(
			"Work Order",
			filters={
				"sales_order": so_name,
				"sales_order_item": ticket_doc.sales_order_item,
				"docstatus": ["!=", 2],
			},
			fields=["name", "qty", "source_warehouse"],
			order_by="creation desc",
			limit_page_length=1,
			ignore_permissions=True,
		)
		if existing_wo:
			existing_wo_row = existing_wo[0]
			qty_map = _extract_qty_map_from_ticket(ticket_doc, target_qty=flt(existing_wo_row.qty or 0))
			if not qty_map:
				skipped_tickets.append({"ticket": ticket_name, "reason": "empty_components"})
				continue

			source_warehouse = (existing_wo_row.source_warehouse or "").strip() or (
				ticket_doc.get("source_warehouse") or ""
			).strip()
			_sync_work_order_required_items(
				existing_wo_row.name, qty_map=qty_map, source_warehouse=source_warehouse
			)
			if _has_column("Work Order", "restaurant_production_ticket"):
				frappe.db.set_value(
					"Work Order",
					existing_wo_row.name,
					"restaurant_production_ticket",
					ticket_doc.name,
					update_modified=False,
				)
			ticket_doc.db_set("work_order", existing_wo_row.name, update_modified=False)
			synced_work_orders.append(existing_wo_row.name)
			continue

		so_item_row = so_item_map.get(ticket_doc.sales_order_item)
		if not so_item_row or not so_item_row.item_code:
			skipped_tickets.append({"ticket": ticket_name, "reason": "missing_sales_order_item"})
			continue

		menu_doc = frappe.get_doc("Item", so_item_row.item_code)
		branch = (
			ticket_doc.get("branch") or menu_doc.get("restaurant_branch") or "DEFAULT"
		).strip() or "DEFAULT"
		try:
			settings = _get_branch_production_settings(branch, so_doc.company)
		except Exception as exc:
			skipped_tickets.append(
				{"ticket": ticket_name, "reason": "missing_branch_settings", "message": str(exc)}
			)
			continue

		bom_name = (ticket_doc.get("bom_template") or _resolve_bom_template(menu_doc) or "").strip()
		if not bom_name or not frappe.db.exists("BOM", bom_name):
			skipped_tickets.append({"ticket": ticket_name, "reason": "missing_bom"})
			continue

		wo_name = _create_work_order_for_ticket(
			ticket_doc=ticket_doc,
			sales_order_doc=so_doc,
			so_item_row=so_item_row,
			menu_doc=menu_doc,
			settings=settings,
			bom_name=bom_name,
			qty_map=qty_map,
		)
		ticket_doc.db_set("work_order", wo_name, update_modified=False)
		created_work_orders.append(wo_name)

	frappe.db.commit()
	return {
		"status": "success",
		"sales_order": so_name,
		"created_work_orders": created_work_orders,
		"synced_work_orders": sorted(set(synced_work_orders)),
		"skipped_tickets": skipped_tickets,
	}


@frappe.whitelist()
def run_management_order_auto_flow(order_name, trigger="manual", payment_status=None, force=1):
	_ensure_management_access()
	result = _run_sales_order_auto_flow(
		order_name,
		trigger=trigger,
		payment_status=payment_status,
		force=bool(cint(force)),
	)
	frappe.db.commit()
	return result


@frappe.whitelist()
def get_management_production_auto_settings():
	_ensure_management_access()
	return _production_auto_settings()


@frappe.whitelist()
def set_management_production_auto_settings(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	_ensure_production_auto_setting_fields()
	bool_fields = [
		"restaurant_auto_flow_enabled",
		"restaurant_auto_flow_on_order_submit",
		"restaurant_auto_flow_on_payment",
		"restaurant_auto_flow_submit_work_order",
		"restaurant_auto_flow_material_transfer",
		"restaurant_auto_flow_manufacture",
		"restaurant_auto_flow_submit_stock_entries",
		"restaurant_auto_flow_mark_ready",
		"restaurant_auto_flow_mark_delivered_on_paid",
		"restaurant_auto_flow_create_delivery_note",
		"restaurant_auto_flow_submit_delivery_note",
	]

	updates = {}
	for fieldname in bool_fields:
		if fieldname not in data:
			continue
		updates[fieldname] = cint(data.get(fieldname))

	if updates:
		settings_doc = frappe.get_doc("Restaurant Web Settings", "Restaurant Web Settings")
		for fieldname, value in updates.items():
			if _has_column("Restaurant Web Settings", fieldname):
				settings_doc.set(fieldname, value)
		settings_doc.save(ignore_permissions=True)
		frappe.db.commit()

	return _production_auto_settings()


@frappe.whitelist()
def get_management_pos_shift_settings():
	_ensure_management_access()
	return _pos_shift_settings()


@frappe.whitelist()
def set_management_pos_shift_settings(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	_ensure_pos_shift_setting_fields()
	opening = data.get("opening") if isinstance(data.get("opening"), dict) else {}
	closing = data.get("closing") if isinstance(data.get("closing"), dict) else {}

	updates = {
		"restaurant_pos_opening_enabled": cint(opening.get("enabled")) if "enabled" in opening else None,
		"restaurant_pos_opening_time": (
			_normalize_time_string(opening.get("time"), "08:00:00") if "time" in opening else None
		),
		"restaurant_pos_opening_cash_float": (
			max(flt(opening.get("cash_float") or 0), 0) if "cash_float" in opening else None
		),
		"restaurant_pos_opening_checklist_required": (
			cint(opening.get("checklist_required")) if "checklist_required" in opening else None
		),
		"restaurant_pos_opening_note_template": (
			(opening.get("note_template") or "").strip() if "note_template" in opening else None
		),
		"restaurant_pos_closing_enabled": cint(closing.get("enabled")) if "enabled" in closing else None,
		"restaurant_pos_closing_time": (
			_normalize_time_string(closing.get("time"), "23:00:00") if "time" in closing else None
		),
		"restaurant_pos_closing_expected_cash": (
			max(flt(closing.get("expected_cash") or 0), 0) if "expected_cash" in closing else None
		),
		"restaurant_pos_closing_tolerance": (
			max(flt(closing.get("tolerance") or 0), 0) if "tolerance" in closing else None
		),
		"restaurant_pos_closing_checklist_required": (
			cint(closing.get("checklist_required")) if "checklist_required" in closing else None
		),
		"restaurant_pos_closing_note_template": (
			(closing.get("note_template") or "").strip() if "note_template" in closing else None
		),
	}

	normalized_updates = {key: value for key, value in updates.items() if value is not None}
	if normalized_updates:
		settings_doc = frappe.get_doc("Restaurant Web Settings", "Restaurant Web Settings")
		changed = False
		for fieldname, value in normalized_updates.items():
			if _has_column("Restaurant Web Settings", fieldname) and settings_doc.get(fieldname) != value:
				settings_doc.set(fieldname, value)
				changed = True
		if changed:
			settings_doc.save(ignore_permissions=True)
			frappe.db.commit()

	return _pos_shift_settings()


@frappe.whitelist()
def get_management_pos_profile(profile_name=None):
	_ensure_management_access()
	return _management_pos_profile_payload(profile_name=profile_name, include_profiles=True)


@frappe.whitelist()
def set_management_pos_profile(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	profile_name = (data.get("profile_name") or data.get("active_profile") or "").strip()
	if not profile_name:
		frappe.throw(_("POS Profile is required."))
	if not frappe.db.exists("DocType", "POS Profile") or not frappe.db.exists("POS Profile", profile_name):
		frappe.throw(_("POS Profile not found."))

	try:
		frappe.defaults.set_user_default("pos_profile", profile_name, user=frappe.session.user)
	except Exception:
		frappe.defaults.set_user_default("pos_profile", profile_name)

	try:
		frappe.defaults.set_user_default("POS Profile", profile_name, user=frappe.session.user)
	except Exception:
		pass

	frappe.db.commit()
	return _management_pos_profile_payload(profile_name=profile_name, include_profiles=True)


@frappe.whitelist()
def set_management_pos_profile_settings(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	profile_name = (data.get("profile_name") or data.get("active_profile") or "").strip()
	if not profile_name:
		frappe.throw(_("POS Profile is required."))
	if not frappe.db.exists("DocType", "POS Profile") or not frappe.db.exists("POS Profile", profile_name):
		frappe.throw(_("POS Profile not found."))

	doc = frappe.get_doc("POS Profile", profile_name)
	settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}
	payments = data.get("payments") if isinstance(data.get("payments"), list) else None
	users = data.get("users") if isinstance(data.get("users"), list) else None

	scalar_map = {
		"title": ("title", "pos_profile_name"),
		"company": ("company",),
		"warehouse": ("warehouse", "set_warehouse"),
		"selling_price_list": ("selling_price_list", "price_list"),
		"customer": ("customer",),
		"cost_center": ("cost_center",),
		"currency": ("currency",),
		"campaign": ("campaign",),
		"taxes_and_charges": ("taxes_and_charges", "taxes_and_charges_template"),
		"write_off_account": ("write_off_account",),
		"write_off_cost_center": ("write_off_cost_center",),
	}
	for key, candidates in scalar_map.items():
		if key not in settings:
			continue
		fieldname = _resolve_doc_fieldname(doc, candidates)
		if not fieldname:
			continue
		doc.set(fieldname, str(settings.get(key) or "").strip())

	bool_map = {
		"allow_rate_change": ("allow_rate_change", "allow_user_to_edit_rate"),
		"allow_discount_change": ("allow_discount_change", "allow_user_to_edit_discount"),
		"ignore_pricing_rule": ("ignore_pricing_rule",),
		"update_stock": ("update_stock",),
		"allow_negative_stock": ("allow_negative_stock",),
		"print_receipt_on_order_complete": ("print_receipt_on_order_complete",),
		"disabled": ("disabled",),
	}
	for key, candidates in bool_map.items():
		if key not in settings:
			continue
		fieldname = _resolve_doc_fieldname(doc, candidates)
		if not fieldname:
			continue
		doc.set(fieldname, cint(settings.get(key)))

	payment_table = _resolve_doc_fieldname(doc, ("payments", "modes_of_payment", "payment_methods"))
	if payment_table:
		_apply_pos_profile_payment_rows(doc, payment_table, payments)

	user_table = _resolve_doc_fieldname(doc, ("applicable_for_users", "users", "allowed_users"))
	if user_table:
		_apply_pos_profile_user_rows(doc, user_table, users)

	doc.save(ignore_permissions=True)

	if cint(data.get("set_default")):
		try:
			frappe.defaults.set_user_default("pos_profile", profile_name, user=frappe.session.user)
		except Exception:
			frappe.defaults.set_user_default("pos_profile", profile_name)
		try:
			frappe.defaults.set_user_default("POS Profile", profile_name, user=frappe.session.user)
		except Exception:
			pass

	frappe.db.commit()
	return _management_pos_profile_payload(profile_name=profile_name, include_profiles=True)


def unlink_work_order_from_restaurant_ticket(doc, method=None):
	wo_name = ((doc.get("name") if hasattr(doc, "get") else None) or getattr(doc, "name", "") or "").strip()
	if not wo_name:
		return

	if frappe.db.exists("DocType", "Restaurant Production Ticket") and _has_column(
		"Restaurant Production Ticket", "work_order"
	):
		frappe.db.sql(
			"""
            update `tabRestaurant Production Ticket`
            set work_order = ''
            where work_order = %s
            """,
			(wo_name,),
		)


def unlink_production_ticket_links(doc, method=None):
	ticket_name = (
		(doc.get("name") if hasattr(doc, "get") else None) or getattr(doc, "name", "") or ""
	).strip()
	if not ticket_name:
		return

	if _has_column("Sales Order Item", "restaurant_production_ticket"):
		frappe.db.sql(
			"""
            update `tabSales Order Item`
            set restaurant_production_ticket = ''
            where restaurant_production_ticket = %s
            """,
			(ticket_name,),
		)

	if _has_column("Work Order", "restaurant_production_ticket"):
		frappe.db.sql(
			"""
            update `tabWork Order`
            set restaurant_production_ticket = ''
            where restaurant_production_ticket = %s
            """,
			(ticket_name,),
		)


MANAGEMENT_ALLOWED_ROLES = {"System Manager", "Desk User", "Restaurant Manager", "Website Manager"}
MANAGEMENT_THEME_ALLOWED_ROLES = {"System Manager", "Desk User", "Restaurant Manager", "Website Manager"}
MANAGEMENT_SITE_SETTINGS_ALLOWED_ROLES = {
	"System Manager",
	"Desk User",
	"Restaurant Manager",
	"Website Manager",
}
MANAGEMENT_WEB_REVENUE_STATUSES = {"new", "confirmed", "preparing", "ready", "delivered"}
MANAGEMENT_TABLE_REVENUE_STATUSES = {"confirmed", "served", "paid"}


def _caller_has_management_access():
	"""Non-throwing variant of _ensure_management_access (for optional features)."""
	if frappe.session.user == "Guest":
		return False
	try:
		roles = set(frappe.get_roles(frappe.session.user))
	except Exception:
		return False
	return bool(roles.intersection(MANAGEMENT_ALLOWED_ROLES))


def _ensure_management_access():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access management pages."), frappe.PermissionError)

	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(MANAGEMENT_ALLOWED_ROLES):
		frappe.throw(_("You don't have permission to access management pages."), frappe.PermissionError)


def _ensure_management_theme_access():
	_ensure_management_access()
	if frappe.session.user == "Administrator":
		return
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(MANAGEMENT_THEME_ALLOWED_ROLES):
		frappe.throw(_("You don't have permission to change theme settings."), frappe.PermissionError)


def _ensure_management_site_settings_access():
	_ensure_management_access()
	if frappe.session.user == "Administrator":
		return
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(MANAGEMENT_SITE_SETTINGS_ALLOWED_ROLES):
		frappe.throw(
			_("You don't have permission to change website content settings."), frappe.PermissionError
		)


def _sanitize_management_loader_settings(payload=None):
	source = payload if isinstance(payload, dict) else {}
	mode = (source.get("loader_mode") or "").strip().lower()
	if mode not in {"preset", "custom"}:
		mode = MANAGEMENT_SITE_LOADER_DEFAULTS["loader_mode"]

	preset = (source.get("loader_preset") or "").strip().lower()
	legacy_alias_map = {
		"willow-tree": "steaming-bowl",
		"pulse-ring": "burger-stack",
		"wave-bars": "pizza-slice",
	}
	preset = legacy_alias_map.get(preset, preset)
	if preset not in MANAGEMENT_SITE_LOADER_PRESETS:
		preset = MANAGEMENT_SITE_LOADER_DEFAULTS["loader_preset"]

	title = (source.get("loader_title") or "").strip() or MANAGEMENT_SITE_LOADER_DEFAULTS["loader_title"]
	subtitle = (source.get("loader_subtitle") or "").strip() or MANAGEMENT_SITE_LOADER_DEFAULTS[
		"loader_subtitle"
	]
	overlay_color = _normalize_theme_hex(
		source.get("loader_overlay_color"),
		MANAGEMENT_SITE_LOADER_DEFAULTS["loader_overlay_color"],
	)
	accent_color = _normalize_theme_hex(
		source.get("loader_accent_color"),
		MANAGEMENT_SITE_LOADER_DEFAULTS["loader_accent_color"],
	)
	custom_code = str(source.get("loader_custom_code") or "")
	custom_code = custom_code[:20000]

	try:
		min_duration = cint(source.get("loader_min_duration_ms"))
	except Exception:
		min_duration = MANAGEMENT_SITE_LOADER_DEFAULTS["loader_min_duration_ms"]
	min_duration = max(0, min(min_duration, 8000))

	return {
		"loader_enabled": 1
		if cint(
			source.get("loader_enabled")
			if source.get("loader_enabled") not in (None, "")
			else MANAGEMENT_SITE_LOADER_DEFAULTS["loader_enabled"]
		)
		else 0,
		"loader_mode": mode,
		"loader_preset": preset,
		"loader_title": title,
		"loader_subtitle": subtitle,
		"loader_min_duration_ms": min_duration,
		"loader_overlay_color": overlay_color,
		"loader_accent_color": accent_color,
		"loader_custom_code": custom_code if mode == "custom" else str(custom_code or ""),
	}


def _load_management_loader_settings():
	try:
		raw = frappe.defaults.get_global_default(MANAGEMENT_SITE_LOADER_GLOBAL_DEFAULT_KEY)
		parsed = _parse_json(raw, {})
	except Exception:
		parsed = {}
	return _sanitize_management_loader_settings(parsed)


def _load_management_display_variant_settings():
	try:
		raw = frappe.defaults.get_global_default(MANAGEMENT_DISPLAY_VARIANT_KEY)
		parsed = _parse_json(raw, {})
		if not isinstance(parsed, dict):
			parsed = {}
		return {
			key: str(parsed.get(key) or default).strip() or default
			for key, default in MANAGEMENT_DISPLAY_VARIANT_DEFAULTS.items()
		}
	except Exception:
		return dict(MANAGEMENT_DISPLAY_VARIANT_DEFAULTS)


def _management_site_settings_payload():
	try:
		_ensure_menu_highlight_setting_fields()
	except Exception:
		pass
	loader_fallback = _load_management_loader_settings()
	display_variant = _load_management_display_variant_settings()

	def _to_int(value, default=0):
		try:
			return cint(value)
		except Exception:
			return default

	# — layer 1: hard-coded defaults —
	web_settings = {
		"brand_name": "",
		"brand_tagline": "",
		"default_currency": "IRR",
		"hero_title": "",
		"hero_subtitle": "",
		"hero_image": "",
		"primary_cta_label": "",
		"header_variant": "classic",
		"menu_search_variant": "search-card",
		"hero_section_variant": "off",
		"footer_variant": "full",
		"hero_section_enabled": 0,
		"footer_enabled": 1,
		"hero_section_title": "",
		"hero_section_description": "",
		"hero_section_cta": "",
		"footer_description": "",
		"footer_phone": "",
		"footer_email": "",
		"footer_address": "",
		"footer_instagram": "",
		"footer_telegram": "",
		"footer_copyright": "",
		"loader_enabled": 1,
		"loader_mode": "preset",
		"loader_preset": "steaming-bowl",
		"loader_title": "در حال آماده سازی سفارش",
		"loader_subtitle": "آشپزخانه مشغول آماده کردن سفارش شماست...",
		"loader_min_duration_ms": 1400,
		"loader_overlay_color": "#F6F4ED",
		"loader_accent_color": "#6A9A6B",
		"loader_custom_code": "",
		"restaurant_menu_highlight_enabled": 1,
		"restaurant_menu_highlight_title": "ویژه و پرفروش",
		"restaurant_menu_highlight_show_featured": 1,
		"restaurant_menu_highlight_featured_limit": 10,
		"restaurant_menu_highlight_show_best_seller": 1,
		"restaurant_menu_highlight_best_seller_limit": 10,
	}

	# — layer 2: primary storage — JSON blob from global defaults —
	try:
		raw_blob = frappe.defaults.get_global_default(MANAGEMENT_SITE_SETTINGS_BLOB_KEY)
		blob = _parse_json(raw_blob, {})
		if isinstance(blob, dict) and blob:
			web_settings.update(blob)
	except Exception:
		pass

	# — layer 3: DocType — wins only for basic fields that are known to exist there —
	_doctype_basic_fields = (
		"brand_name",
		"brand_tagline",
		"default_currency",
		"hero_title",
		"hero_subtitle",
		"hero_image",
		"primary_cta_label",
	)
	try:
		settings_doc = frappe.get_cached_doc("Restaurant Web Settings")
		for _f in _doctype_basic_fields:
			_v = settings_doc.get(_f)
			if _v not in (None, ""):
				web_settings[_f] = _v
		# also sync integer highlight fields from DocType if they exist there
		for _f, _default in (
			("restaurant_menu_highlight_enabled", 1),
			("restaurant_menu_highlight_show_featured", 1),
			("restaurant_menu_highlight_featured_limit", 10),
			("restaurant_menu_highlight_show_best_seller", 1),
			("restaurant_menu_highlight_best_seller_limit", 10),
		):
			_v = settings_doc.get(_f)
			if _v not in (None, ""):
				web_settings[_f] = cint(_v)
	except Exception:
		pass

	web_settings.update(_sanitize_management_loader_settings({**loader_fallback, **web_settings}))
	web_settings.update(display_variant)

	faq_items = []
	if frappe.db.exists("DocType", "Restaurant FAQ"):
		faq_fields = ["name"]
		for fieldname in ["question", "answer", "sort_order", "is_active"]:
			if _has_column("Restaurant FAQ", fieldname):
				faq_fields.append(fieldname)
		faq_order_by = (
			"sort_order asc, modified asc" if _has_column("Restaurant FAQ", "sort_order") else "modified asc"
		)
		faq_rows = frappe.get_all(
			"Restaurant FAQ",
			fields=faq_fields,
			ignore_permissions=True,
			order_by=faq_order_by,
		)
		faq_items = [
			{
				"name": row.get("name"),
				"question": row.get("question") or "",
				"answer": row.get("answer") or "",
				"sort_order": _to_int(row.get("sort_order")),
				"is_active": _to_int(row.get("is_active"), 1),
			}
			for row in faq_rows
		]

	about_sections = []
	if frappe.db.exists("DocType", "Restaurant About Section"):
		about_fields = ["name"]
		for fieldname in [
			"section_type",
			"title",
			"subtitle",
			"badge",
			"founded_year",
			"icon",
			"year_label",
			"highlight",
			"body_text",
			"image",
			"stat_label",
			"stat_value",
			"sort_order",
			"is_active",
		]:
			if _has_column("Restaurant About Section", fieldname):
				about_fields.append(fieldname)
		about_order_by = (
			"sort_order asc, modified asc"
			if _has_column("Restaurant About Section", "sort_order")
			else "modified asc"
		)
		about_rows = frappe.get_all(
			"Restaurant About Section",
			fields=about_fields,
			ignore_permissions=True,
			order_by=about_order_by,
		)
		about_sections = [
			{
				"name": row.get("name"),
				"section_type": row.get("section_type") or "story",
				"title": row.get("title") or "",
				"subtitle": row.get("subtitle") or "",
				"badge": row.get("badge") or "",
				"founded_year": row.get("founded_year") or "",
				"icon": row.get("icon") or "",
				"year_label": row.get("year_label") or "",
				"highlight": _to_int(row.get("highlight")),
				"body_text": row.get("body_text") or "",
				"image": row.get("image") or "",
				"stat_label": row.get("stat_label") or "",
				"stat_value": row.get("stat_value") or "",
				"sort_order": _to_int(row.get("sort_order")),
				"is_active": _to_int(row.get("is_active"), 1),
			}
			for row in about_rows
		]

	hero_slides = []
	if frappe.db.exists("DocType", "Restaurant Hero Slide"):
		slide_fields = [
			"name",
			"title",
			"subtitle",
			"image",
			"linked_item",
			"cta_label",
			"cta_url",
			"sort_order",
			"is_active",
		]
		if _has_column("Restaurant Hero Slide", "branch"):
			slide_fields.append("branch")
		slide_rows = frappe.get_all(
			"Restaurant Hero Slide",
			fields=slide_fields,
			ignore_permissions=True,
			order_by="sort_order asc, modified asc",
		)
		hero_slides = [
			{
				"name": row.get("name"),
				"title": row.get("title") or "",
				"subtitle": row.get("subtitle") or "",
				"image": row.get("image") or "",
				"linked_item": row.get("linked_item") or "",
				"cta_label": row.get("cta_label") or "",
				"cta_url": row.get("cta_url") or "",
				"branch": row.get("branch") or "",
				"sort_order": _to_int(row.get("sort_order")),
				"is_active": _to_int(row.get("is_active"), 1),
			}
			for row in slide_rows
		]

	return {
		"web_settings": web_settings,
		"hero_slides": hero_slides,
		"about_sections": about_sections,
		"faq_items": faq_items,
	}


def _sync_management_site_doctype_rows(doctype, rows, normalize_row):
	if not frappe.db.exists("DocType", doctype):
		return []

	incoming_rows = rows if isinstance(rows, list) else []
	existing_names = frappe.get_all(doctype, pluck="name", ignore_permissions=True)
	existing_set = set(existing_names or [])
	keep = []

	for index, row in enumerate(incoming_rows):
		source = row if isinstance(row, dict) else {}
		normalized = normalize_row(source, index)
		if not normalized:
			continue
		safe_payload = {}
		for key, value in normalized.items():
			if _has_column(doctype, key):
				safe_payload[key] = value
		if not safe_payload:
			continue
		name = (source.get("name") or "").strip()
		if name and name in existing_set:
			doc = frappe.get_doc(doctype, name)
			for key, value in safe_payload.items():
				doc.set(key, value)
			doc.save(ignore_permissions=True)
			keep.append(doc.name)
		else:
			payload = {"doctype": doctype, **safe_payload}
			doc = frappe.get_doc(payload)
			doc.insert(ignore_permissions=True)
			keep.append(doc.name)

	for name in existing_set.difference(set(keep)):
		try:
			frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
		except Exception:
			continue

	return keep


@frappe.whitelist(allow_guest=True)
def get_management_theme_settings():
	return _load_management_theme_settings()


@frappe.whitelist()
def set_management_theme_settings(payload=None):
	_ensure_management_theme_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	normalized = _sanitize_management_theme_settings(data)
	frappe.defaults.set_global_default(MANAGEMENT_THEME_GLOBAL_DEFAULT_KEY, json.dumps(normalized))
	frappe.db.commit()
	return normalized


@frappe.whitelist()
def get_management_site_settings():
	_ensure_management_site_settings_access()
	return _management_site_settings_payload()


@frappe.whitelist()
def set_management_site_settings(payload=None, **kwargs):
	_ensure_management_site_settings_access()
	try:
		_ensure_menu_highlight_setting_fields()
	except Exception:
		pass
	data = _parse_json(payload, {})
	if not data and kwargs:
		data = {key: value for key, value in kwargs.items() if key not in {"cmd", "method"}}
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	web_settings = data.get("web_settings") if isinstance(data.get("web_settings"), dict) else None
	loader_fields = tuple(MANAGEMENT_SITE_LOADER_DEFAULTS.keys())
	if web_settings and any(fieldname in web_settings for fieldname in loader_fields):
		normalized_loader = _sanitize_management_loader_settings(web_settings)
		for fieldname, value in normalized_loader.items():
			web_settings[fieldname] = value
		frappe.defaults.set_global_default(
			MANAGEMENT_SITE_LOADER_GLOBAL_DEFAULT_KEY,
			json.dumps(normalized_loader),
		)

	if web_settings:
		# — primary storage: save ALL web_settings as a JSON blob —
		try:
			existing_blob = {}
			try:
				raw = frappe.defaults.get_global_default(MANAGEMENT_SITE_SETTINGS_BLOB_KEY)
				existing_blob = _parse_json(raw, {})
				if not isinstance(existing_blob, dict):
					existing_blob = {}
			except Exception:
				pass
			existing_blob.update(web_settings)
			frappe.defaults.set_global_default(MANAGEMENT_SITE_SETTINGS_BLOB_KEY, json.dumps(existing_blob))
		except Exception:
			pass

		# — also persist display variant fields separately —
		display_variant_payload = {}
		try:
			raw = frappe.defaults.get_global_default(MANAGEMENT_DISPLAY_VARIANT_KEY)
			display_variant_payload = _parse_json(raw, {})
			if not isinstance(display_variant_payload, dict):
				display_variant_payload = {}
		except Exception:
			display_variant_payload = {}
		for key, default_val in MANAGEMENT_DISPLAY_VARIANT_DEFAULTS.items():
			if key in web_settings:
				display_variant_payload[key] = str(web_settings[key] or default_val).strip() or default_val
		try:
			frappe.defaults.set_global_default(
				MANAGEMENT_DISPLAY_VARIANT_KEY, json.dumps(display_variant_payload)
			)
		except Exception:
			pass

	if web_settings and frappe.db.exists("DocType", "Restaurant Web Settings"):
		scalar_fields = [
			"brand_name",
			"brand_tagline",
			"default_currency",
			"hero_title",
			"hero_subtitle",
			"hero_image",
			"primary_cta_label",
			"header_variant",
			"menu_search_variant",
			"hero_section_variant",
			"footer_variant",
			"hero_section_title",
			"hero_section_description",
			"hero_section_cta",
			"footer_description",
			"footer_phone",
			"footer_email",
			"footer_address",
			"footer_instagram",
			"footer_telegram",
			"footer_copyright",
			"loader_mode",
			"loader_preset",
			"loader_title",
			"loader_subtitle",
			"loader_overlay_color",
			"loader_accent_color",
			"loader_custom_code",
			"restaurant_menu_highlight_title",
		]
		int_fields = [
			"hero_section_enabled",
			"footer_enabled",
			"loader_enabled",
			"loader_min_duration_ms",
			"restaurant_menu_highlight_enabled",
			"restaurant_menu_highlight_show_featured",
			"restaurant_menu_highlight_featured_limit",
			"restaurant_menu_highlight_show_best_seller",
			"restaurant_menu_highlight_best_seller_limit",
		]
		existing_brand = ""
		try:
			existing_brand = (
				frappe.db.get_value("Restaurant Web Settings", "Restaurant Web Settings", "brand_name") or ""
			).strip()
		except Exception:
			pass
		for fieldname in scalar_fields:
			if fieldname not in web_settings or not _has_doctype_field("Restaurant Web Settings", fieldname):
				continue
			value = str(web_settings.get(fieldname) or "").strip()
			if fieldname == "header_variant":
				value = value if value in MANAGEMENT_HEADER_VARIANTS else "classic"
			if fieldname == "menu_search_variant":
				value = value if value in MANAGEMENT_MENU_SEARCH_VARIANTS else "search-card"
			if fieldname == "hero_section_variant":
				value = value if value in MANAGEMENT_HERO_SECTION_VARIANTS else "off"
			if fieldname == "footer_variant":
				value = value if value in MANAGEMENT_FOOTER_VARIANTS else "full"
			if fieldname == "brand_name" and not value:
				value = existing_brand or "Restaurant"
			try:
				frappe.db.set_value(
					"Restaurant Web Settings",
					"Restaurant Web Settings",
					fieldname,
					value,
					update_modified=False,
				)
			except Exception:
				pass
		for fieldname in int_fields:
			if fieldname not in web_settings or not _has_doctype_field("Restaurant Web Settings", fieldname):
				continue
			try:
				frappe.db.set_value(
					"Restaurant Web Settings",
					"Restaurant Web Settings",
					fieldname,
					cint(web_settings.get(fieldname) or 0),
					update_modified=False,
				)
			except Exception:
				pass
		try:
			frappe.db.set_value(
				"Restaurant Web Settings",
				"Restaurant Web Settings",
				"modified",
				frappe.utils.now(),
				update_modified=False,
			)
		except Exception:
			pass

	if "faq_items" in data:
		_sync_management_site_doctype_rows(
			"Restaurant FAQ",
			data.get("faq_items"),
			lambda row, index: (
				{
					"question": (row.get("question") or "").strip(),
					"answer": (row.get("answer") or "").strip(),
					"sort_order": cint(row.get("sort_order") or index),
					"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
				}
				if (row.get("question") or "").strip() and (row.get("answer") or "").strip()
				else None
			),
		)

	if "about_sections" in data:
		_sync_management_site_doctype_rows(
			"Restaurant About Section",
			data.get("about_sections"),
			lambda row, index: (
				{
					"section_type": ((row.get("section_type") or "story").strip() or "story"),
					"title": (row.get("title") or "").strip() or "بخش درباره ما",
					"subtitle": (row.get("subtitle") or "").strip(),
					"badge": (row.get("badge") or "").strip(),
					"founded_year": (row.get("founded_year") or "").strip(),
					"icon": (row.get("icon") or "").strip(),
					"year_label": (row.get("year_label") or "").strip(),
					"highlight": cint(row.get("highlight") if row.get("highlight") not in (None, "") else 0),
					"body_text": (row.get("body_text") or "").strip()
					or "توضیحات این بخش هنوز تکمیل نشده است.",
					"image": (row.get("image") or "").strip(),
					"stat_label": (row.get("stat_label") or "").strip(),
					"stat_value": (row.get("stat_value") or "").strip(),
					"sort_order": cint(row.get("sort_order") or index),
					"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
				}
				if (row.get("title") or "").strip()
				or (row.get("body_text") or "").strip()
				or (row.get("section_type") or "").strip()
				else None
			),
		)

	if "hero_slides" in data:
		has_branch = _has_column("Restaurant Hero Slide", "branch")

		def _normalize_slide_row(row, index):
			title = (row.get("title") or "").strip()
			if not title:
				return None
			out = {
				"title": title,
				"subtitle": (row.get("subtitle") or "").strip(),
				"image": (row.get("image") or "").strip(),
				"linked_item": (row.get("linked_item") or "").strip(),
				"cta_label": (row.get("cta_label") or "").strip() or "مشاهده محصول",
				"cta_url": (row.get("cta_url") or "").strip(),
				"sort_order": cint(row.get("sort_order") or index),
				"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
			}
			if has_branch:
				out["branch"] = (row.get("branch") or "").strip()
			return out

		_sync_management_site_doctype_rows(
			"Restaurant Hero Slide",
			data.get("hero_slides"),
			_normalize_slide_row,
		)

	frappe.clear_cache(doctype="Restaurant Web Settings")
	frappe.db.commit()
	result = _management_site_settings_payload()
	result["loader_settings"] = _load_management_loader_settings()
	return result


def _management_date_window(date_from=None, date_to=None, default_days=30):
	end_date = getdate(date_to) if date_to else getdate(nowdate())
	start_date = getdate(date_from) if date_from else add_days(end_date, -(cint(default_days) - 1))
	if start_date > end_date:
		start_date, end_date = end_date, start_date
	return str(start_date), str(end_date)


def _management_datetime_bounds(date_from=None, date_to=None, default_days=30):
	start_date, end_date = _management_date_window(
		date_from=date_from, date_to=date_to, default_days=default_days
	)
	return f"{start_date} 00:00:00", f"{end_date} 23:59:59"


def _management_business_datetime(date_value=None, fallback_datetime=None):
	date_part = None
	fallback_dt = None

	if date_value not in (None, ""):
		try:
			date_part = getdate(date_value)
		except Exception:
			date_part = None

	if fallback_datetime not in (None, ""):
		try:
			fallback_dt = get_datetime(fallback_datetime)
		except Exception:
			fallback_dt = None

	if date_part and fallback_dt:
		return get_datetime(f"{date_part} {fallback_dt.strftime('%H:%M:%S')}")
	if date_part:
		return get_datetime(f"{date_part} 00:00:00")
	return fallback_dt


def _management_fetch_web_orders(date_from=None, date_to=None, status=None, cashier=None):
	if not frappe.db.exists("DocType", "Sales Order"):
		return []

	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	has_transaction_date = _has_column("Sales Order", "transaction_date")
	filters = {"docstatus": ["<", 2]}
	if has_transaction_date:
		filters["transaction_date"] = ["between", [start_date, end_date]]
	else:
		filters["creation"] = ["between", [start_dt, end_dt]]
	if cashier:
		filters["owner"] = cashier

	has_mobile = _has_column("Sales Order", "restaurant_customer_mobile")
	has_order_type = _has_column("Sales Order", "restaurant_order_type")
	has_note = _has_column("Sales Order", "restaurant_note")
	has_payment_method = _has_column("Sales Order", "restaurant_payment_method")
	has_payment_status = _has_column("Sales Order", "restaurant_payment_status")
	has_payment_provider = _has_column("Sales Order", "restaurant_payment_provider")
	has_restaurant_table = _has_column("Sales Order", "restaurant_table")

	fields = [
		"name",
		"customer",
		"customer_name",
		"status",
		"docstatus",
		"total",
		"net_total",
		"grand_total",
		"creation",
		"owner",
	]
	if has_transaction_date:
		fields.append("transaction_date")
	if has_mobile:
		fields.append("restaurant_customer_mobile")
	if has_order_type:
		fields.append("restaurant_order_type")
	if has_note:
		fields.append("restaurant_note")
	if has_payment_method:
		fields.append("restaurant_payment_method")
	if has_payment_status:
		fields.append("restaurant_payment_status")
	if has_payment_provider:
		fields.append("restaurant_payment_provider")
	if has_restaurant_table:
		fields.append("restaurant_table")
	if _has_column("Sales Order", "restaurant_status"):
		fields.append("restaurant_status")

	order_by = "transaction_date desc, creation desc" if has_transaction_date else "creation desc"
	rows = frappe.get_all(
		"Sales Order",
		fields=fields,
		filters=filters,
		order_by=order_by,
		ignore_permissions=True,
	)

	mobile_by_customer = {}
	if not has_mobile:
		customer_names = {row.customer for row in rows if row.customer}
		if customer_names:
			customer_fields = ["name"]
			has_mobile_no = _has_column("Customer", "mobile_no")
			has_primary_mobile = _has_column("Customer", "customer_primary_mobile")
			if has_mobile_no:
				customer_fields.append("mobile_no")
			if has_primary_mobile:
				customer_fields.append("customer_primary_mobile")

			customer_rows = frappe.get_all(
				"Customer",
				fields=customer_fields,
				filters={"name": ["in", list(customer_names)]},
				ignore_permissions=True,
			)
			for row in customer_rows:
				mobile_by_customer[row.name] = (
					(row.get("mobile_no") if has_mobile_no else "")
					or (row.get("customer_primary_mobile") if has_primary_mobile else "")
					or ""
				)

	parent_names = [row.name for row in rows]
	items_by_parent = defaultdict(list)
	has_item_customization = _has_column("Sales Order Item", "restaurant_customization_json")
	has_item_pricing_breakdown = _has_column("Sales Order Item", "restaurant_pricing_breakdown_json")
	if parent_names and frappe.db.exists("DocType", "Sales Order Item"):
		item_fields = ["parent", "item_code", "item_name", "qty", "rate", "amount", "base_amount"]
		if has_item_customization:
			item_fields.append("restaurant_customization_json")
		if has_item_pricing_breakdown:
			item_fields.append("restaurant_pricing_breakdown_json")
		item_rows = frappe.get_all(
			"Sales Order Item",
			fields=item_fields,
			filters={"parent": ["in", parent_names]},
			order_by="parent asc, idx asc",
			ignore_permissions=True,
		)
		for item in item_rows:
			amount = item.get("amount")
			if amount in (None, ""):
				amount = item.get("base_amount")
			line_total = flt(amount if amount not in (None, "") else flt(item.rate) * flt(item.qty))
			pricing_breakdown = (
				_parse_json(item.restaurant_pricing_breakdown_json, {}) if has_item_pricing_breakdown else {}
			)
			items_by_parent[item.parent].append(
				{
					"item_code": item.item_code or "",
					"title": item.item_name or "",
					"qty": flt(item.qty),
					"unit_price": flt(item.rate),
					"line_total": line_total,
					"customization_json": item.restaurant_customization_json
					if has_item_customization
					else "",
					"pricing_breakdown": pricing_breakdown if isinstance(pricing_breakdown, dict) else {},
					"nutrition": pricing_breakdown.get("nutrition")
					if isinstance(pricing_breakdown, dict)
					else {},
					"nutrition_totals": pricing_breakdown.get("nutrition_totals")
					if isinstance(pricing_breakdown, dict)
					else {},
				}
			)

	normalized_status = (status or "").strip().lower()
	
	# Fetch outstanding amounts in bulk to avoid N+1
	outstanding_map = {}
	sales_invoice_map = {}
	if parent_names and frappe.db.exists("DocType", "Sales Invoice Item"):
		si_items = frappe.get_all("Sales Invoice Item", filters={"sales_order": ["in", parent_names], "docstatus": 1}, fields=["parent", "sales_order"], ignore_permissions=True)
		if si_items:
			si_names = list({si.parent for si in si_items})
			si_docs = frappe.get_all("Sales Invoice", filters={"name": ["in", si_names]}, fields=["name", "outstanding_amount"], ignore_permissions=True)
			si_outstanding = {doc.name: flt(doc.outstanding_amount) for doc in si_docs}
			for si_item in si_items:
				sales_invoice_map.setdefault(si_item.sales_order, set()).add(si_item.parent)
				if si_item.sales_order not in outstanding_map:
					outstanding_map[si_item.sales_order] = 0.0
				outstanding_map[si_item.sales_order] += si_outstanding.get(si_item.parent, 0.0)

	delivery_exists_map = {}
	if parent_names and frappe.db.exists("DocType", "Delivery Note Item"):
		dn_items = frappe.get_all(
			"Delivery Note Item",
			filters={"against_sales_order": ["in", parent_names], "docstatus": 1},
			fields=["against_sales_order"],
			ignore_permissions=True,
		)
		for dn_item in dn_items:
			if dn_item.against_sales_order:
				delivery_exists_map[dn_item.against_sales_order] = True

	payload = []
	for row in rows:
		order_status = _core_order_status(row)
		delivery_exists = bool(delivery_exists_map.get(row.name))
		if delivery_exists:
			order_status = "delivered"
		if normalized_status and order_status != normalized_status:
			continue

		created_at = (
			_management_business_datetime(
				date_value=row.get("transaction_date") if has_transaction_date else None,
				fallback_datetime=row.creation,
			)
			or row.creation
		)
		payload.append(
			{
				"source": "web",
				"doctype": "Sales Order",
				"name": row.name,
				"order_code": row.name,
				"customer_name": row.customer_name or "POS Customer",
				"mobile": (row.restaurant_customer_mobile if has_mobile else "")
				or mobile_by_customer.get(row.customer, ""),
				"channel": (row.restaurant_order_type if has_order_type else "") or "takeaway",
				"status": order_status,
				"subtotal": flt(row.total or row.net_total),
				"grand_total": flt(row.grand_total or row.total or row.net_total),
				"outstanding_amount": flt(outstanding_map.get(row.name, flt(row.grand_total or row.total or row.net_total))),
				"has_sales_invoice": bool(sales_invoice_map.get(row.name)),
				"sales_invoices": sorted(sales_invoice_map.get(row.name, [])),
				"delivery_exists": delivery_exists,
				"created_at": _json_safe_datetime(created_at),
				"cashier": row.owner or "",
				"note": _clean_automatic_pos_note(row.restaurant_note) if has_note else "",
				"payment_method": row.restaurant_payment_method if has_payment_method else "",
				"payment_status": row.restaurant_payment_status if has_payment_status else "",
				"payment_provider": row.restaurant_payment_provider if has_payment_provider else "",
				"table": (row.restaurant_table or "") if has_restaurant_table else "",
				"items": items_by_parent.get(row.name, []),
			}
		)
	return payload


def _management_fetch_table_orders(date_from=None, date_to=None, status=None, cashier=None):
	if not frappe.db.exists("DocType", "Restaurant Table Order"):
		return []

	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	has_created_at = _has_column("Restaurant Table Order", "created_at")
	filters = {"docstatus": ["<", 2]}
	if has_created_at:
		filters["created_at"] = ["between", [start_dt, end_dt]]
	else:
		filters["creation"] = ["between", [start_dt, end_dt]]
	if status:
		filters["status"] = status
	if cashier:
		filters["owner"] = cashier

	fields = [
		"name",
		"order_code",
		"table",
		"status",
		"subtotal",
		"grand_total",
		"creation",
		"owner",
	]
	if has_created_at:
		fields.append("created_at")

	order_by = "created_at desc, creation desc" if has_created_at else "creation desc"
	rows = frappe.get_all(
		"Restaurant Table Order",
		fields=fields,
		filters=filters,
		order_by=order_by,
		ignore_permissions=True,
	)

	table_names = {row.table for row in rows if row.table}
	table_label_map = {}
	if table_names and frappe.db.exists("DocType", "Restaurant Table"):
		table_rows = frappe.get_all(
			"Restaurant Table",
			fields=["name", "table_number"],
			filters={"name": ["in", list(table_names)]},
			ignore_permissions=True,
		)
		table_label_map = {row.name: row.table_number for row in table_rows}

	parent_names = [row.name for row in rows]
	item_rows = []
	if parent_names and frappe.db.exists("DocType", "Restaurant Table Order Item"):
		item_rows = frappe.get_all(
			"Restaurant Table Order Item",
			fields=["parent", "menu_item", "quantity", "line_total"],
			filters={"parent": ["in", parent_names]},
			order_by="idx asc",
			ignore_permissions=True,
		)

	menu_item_names = {row.menu_item for row in item_rows if row.menu_item}
	menu_title_map = {}
	menu_erp_item_map = {}
	if menu_item_names and frappe.db.exists("DocType", "Restaurant Table Menu Item"):
		menu_fields = ["name", "item_name"]
		has_menu_erp_item = _has_column("Restaurant Table Menu Item", "erpnext_item")
		if has_menu_erp_item:
			menu_fields.append("erpnext_item")
		menu_rows = frappe.get_all(
			"Restaurant Table Menu Item",
			fields=menu_fields,
			filters={"name": ["in", list(menu_item_names)]},
			ignore_permissions=True,
		)
		menu_title_map = {row.name: row.item_name for row in menu_rows}
		if has_menu_erp_item:
			menu_erp_item_map = {
				row.name: (row.get("erpnext_item") or "") for row in menu_rows if row.get("erpnext_item")
			}

	items_by_parent = defaultdict(list)
	for item in item_rows:
		items_by_parent[item.parent].append(
			{
				"title": menu_title_map.get(item.menu_item) or item.menu_item or "",
				"item_code": menu_erp_item_map.get(item.menu_item, ""),
				"qty": flt(item.quantity),
				"line_total": flt(item.line_total),
				"customization_json": "",
			}
		)

	payload = []
	for row in rows:
		table_label = table_label_map.get(row.table) or row.table or "Table"
		created_at = row.get("created_at") or row.creation
		payload.append(
			{
				"source": "table",
				"doctype": "Restaurant Table Order",
				"name": row.name,
				"order_code": row.order_code or row.name,
				"customer_name": f"Table {table_label}",
				"mobile": "",
				"channel": "dine_in",
				"table": row.table or "",
				"table_label": table_label,
				"status": row.status or "pending",
				"subtotal": flt(row.subtotal),
				"grand_total": flt(row.grand_total),
				"created_at": _json_safe_datetime(created_at),
				"cashier": row.owner or "",
				"items": items_by_parent.get(row.name, []),
			}
		)
	return payload


def _management_collect_orders(date_from=None, date_to=None, status=None, source="all", cashier=None):
	source = (source or "all").strip().lower()
	orders = []
	if source in {"all", "web", "restaurant"}:
		orders.extend(
			_management_fetch_web_orders(
				date_from=date_from,
				date_to=date_to,
				status=status,
				cashier=cashier,
			)
		)
	if source in {"all", "table"}:
		orders.extend(
			_management_fetch_table_orders(
				date_from=date_from,
				date_to=date_to,
				status=status,
				cashier=cashier,
			)
		)

	def _sort_key(order):
		try:
			return get_datetime(order.get("created_at"))
		except Exception:
			return now_datetime()

	return sorted(orders, key=_sort_key, reverse=True)


def _is_revenue_order(order):
	source = order.get("source")
	status = (order.get("status") or "").strip().lower()
	if source == "table":
		return status in MANAGEMENT_TABLE_REVENUE_STATUSES
	return status in MANAGEMENT_WEB_REVENUE_STATUSES


def _build_sales_summary(orders):
	revenue_orders = [row for row in orders if _is_revenue_order(row)]
	total_sales = sum(flt(row.get("grand_total")) for row in revenue_orders)
	total_orders = len(revenue_orders)
	avg_ticket = (total_sales / total_orders) if total_orders else 0
	total_items = 0
	for order in revenue_orders:
		total_items += sum(flt(item.get("qty")) for item in order.get("items") or [])

	return {
		"total_sales": total_sales,
		"total_orders": total_orders,
		"avg_ticket": avg_ticket,
		"total_items": total_items,
	}


def _build_top_products(orders, limit=10):
	grouped = {}
	for order in orders:
		if not _is_revenue_order(order):
			continue
		for item in order.get("items") or []:
			key = (item.get("title") or "").strip() or "بدون نام"
			bucket = grouped.setdefault(
				key,
				{
					"product_title": key,
					"qty": 0.0,
					"amount": 0.0,
				},
			)
			bucket["qty"] += flt(item.get("qty"))
			bucket["amount"] += flt(item.get("line_total"))

	rows = sorted(grouped.values(), key=lambda row: row["amount"], reverse=True)
	return rows[: max(cint(limit), 1)]


def _build_product_mix_associations(orders, limit=80, min_pair_orders=2, min_base_orders=2):
	revenue_orders = [row for row in (orders or []) if _is_revenue_order(row)]
	total_orders = len(revenue_orders)
	if total_orders <= 1:
		return []

	base_counts = defaultdict(int)
	pair_counts = defaultdict(int)

	for order in revenue_orders:
		raw_items = order.get("items") or []
		titles = []
		for item in raw_items:
			title = (item.get("title") or item.get("item_code") or "").strip()
			if title:
				titles.append(title)

		unique_titles = sorted(set(titles))
		if len(unique_titles) <= 1:
			continue

		for title in unique_titles:
			base_counts[title] += 1

		for left in unique_titles:
			for right in unique_titles:
				if left == right:
					continue
				pair_counts[(left, right)] += 1

	rules = []
	for pair_key, co_count in pair_counts.items():
		left, right = pair_key
		left_count = cint(base_counts.get(left) or 0)
		right_count = cint(base_counts.get(right) or 0)
		if left_count < cint(min_base_orders):
			continue
		if co_count < cint(min_pair_orders):
			continue

		confidence = round(_safe_div(co_count * 100.0, left_count), 2)
		support = round(_safe_div(co_count * 100.0, total_orders), 2)
		expected_support = (
			_safe_div((left_count * right_count), total_orders * total_orders) if total_orders else 0
		)
		actual_support = _safe_div(co_count, total_orders)
		lift = round(_safe_div(actual_support, expected_support), 3) if expected_support else 0

		rules.append(
			{
				"product_title": left,
				"paired_product_title": right,
				"base_order_count": left_count,
				"paired_order_count": right_count,
				"co_order_count": cint(co_count),
				"confidence_percent": confidence,
				"support_percent": support,
				"lift_score": lift,
			}
		)

	rules = sorted(
		rules,
		key=lambda row: (
			flt(row.get("confidence_percent")),
			cint(row.get("co_order_count")),
			flt(row.get("support_percent")),
		),
		reverse=True,
	)
	return rules[: max(cint(limit), 1)]


def _build_daily_trend(orders):
	grouped = defaultdict(float)
	for order in orders:
		if not _is_revenue_order(order):
			continue
		date_key = str(getdate(order.get("created_at")))
		grouped[date_key] += flt(order.get("grand_total"))

	return [{"date": date_key, "sales": grouped[date_key]} for date_key in sorted(grouped.keys())]


def _build_hourly_trend(orders):
	grouped = {hour: {"hour": hour, "orders": 0, "sales": 0.0} for hour in range(24)}
	for order in orders:
		if not _is_revenue_order(order):
			continue
		hour = get_datetime(order.get("created_at")).hour
		grouped[hour]["orders"] += 1
		grouped[hour]["sales"] += flt(order.get("grand_total"))
	return [grouped[idx] for idx in range(24)]


def _build_status_rows(orders):
	grouped = defaultdict(lambda: {"status": "", "orders": 0, "sales": 0.0})
	for order in orders:
		status = (order.get("status") or "").strip().lower() or "unknown"
		bucket = grouped[status]
		bucket["status"] = status
		bucket["orders"] += 1
		bucket["sales"] += flt(order.get("grand_total"))
	return sorted(grouped.values(), key=lambda row: row["orders"], reverse=True)


def _build_channel_rows(orders):
	grouped = defaultdict(lambda: {"channel": "", "orders": 0, "sales": 0.0})
	for order in orders:
		if not _is_revenue_order(order):
			continue
		channel = (order.get("channel") or "unknown").strip().lower()
		bucket = grouped[channel]
		bucket["channel"] = channel
		bucket["orders"] += 1
		bucket["sales"] += flt(order.get("grand_total"))
	return sorted(grouped.values(), key=lambda row: row["sales"], reverse=True)


def _build_cashier_rows(orders):
	grouped = defaultdict(lambda: {"cashier": "", "orders": 0, "sales": 0.0, "avg_ticket": 0.0})
	for order in orders:
		if not _is_revenue_order(order):
			continue
		cashier = (order.get("cashier") or "unknown").strip()
		bucket = grouped[cashier]
		bucket["cashier"] = cashier
		bucket["orders"] += 1
		bucket["sales"] += flt(order.get("grand_total"))

	rows = []
	for row in grouped.values():
		row["avg_ticket"] = row["sales"] / row["orders"] if row["orders"] else 0
		rows.append(row)
	return sorted(rows, key=lambda row: row["sales"], reverse=True)


def _build_cancellation_rows(orders):
	rows = []
	for order in orders:
		if (order.get("status") or "").strip().lower() != "cancelled":
			continue
		rows.append(
			{
				"order_code": order.get("order_code"),
				"source": order.get("source"),
				"channel": order.get("channel"),
				"cashier": order.get("cashier"),
				"amount": flt(order.get("grand_total")),
				"created_at": order.get("created_at"),
			}
		)
	return rows


def _build_modifier_usage_rows(web_orders):
	grouped = defaultdict(int)
	for order in web_orders:
		for item in order.get("items") or []:
			payload = _parse_json(item.get("customization_json"), {})
			selected = payload.get("selected_modifiers") or []
			for row in selected:
				group_name = (row.get("group") or row.get("group_name") or "").strip() or "Unknown"
				option_name = (row.get("option") or row.get("option_name") or "").strip() or "Unknown"
				qty = max(cint(row.get("qty") or 1), 1)
				grouped[f"{group_name} :: {option_name}"] += qty
	rows = []
	for key, count in grouped.items():
		group_name, option_name = key.split(" :: ", 1)
		rows.append(
			{
				"group": group_name,
				"option": option_name,
				"usage_count": count,
			}
		)
	return sorted(rows, key=lambda row: row["usage_count"], reverse=True)


def _management_previous_window(date_from=None, date_to=None):
	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
	days = max((getdate(end_date) - getdate(start_date)).days + 1, 1)
	prev_end = str(add_days(start_date, -1))
	prev_start = str(add_days(prev_end, -(days - 1)))
	return prev_start, prev_end


def _safe_div(numerator, denominator):
	denominator_value = flt(denominator)
	if not denominator_value:
		return 0.0
	return flt(numerator) / denominator_value


def _pct_change(current, previous):
	current_value = flt(current)
	previous_value = flt(previous)
	if not previous_value:
		return 100.0 if current_value else 0.0
	return round(((current_value - previous_value) * 100.0) / previous_value, 1)


def _trend_from_change(change_value):
	if flt(change_value) > 0:
		return "up"
	if flt(change_value) < 0:
		return "down"
	return "flat"


def _bi_kpi(key, label, value, unit, previous=0, action_url="", action_label=""):
	change_pct = _pct_change(value, previous)
	payload = {
		"key": key,
		"label": label,
		"value": flt(value) if unit in {"money", "percent", "minutes", "score"} else cint(value),
		"unit": unit,
		"change_pct": change_pct,
		"trend": _trend_from_change(change_pct),
		"change_label": _("Compared to previous window"),
	}
	if action_url:
		payload["action_url"] = action_url
	if action_label:
		payload["action_label"] = action_label
	return payload


def _table_columns_from_rows(rows):
	first_row = (rows or [{}])[0] if rows else {}
	columns = []
	for key in first_row.keys():
		normalized = str(key or "")
		col_type = "text"
		if any(
			token in normalized for token in ["sales", "amount", "spent", "total", "ticket", "line_total"]
		):
			col_type = "money"
		elif "percent" in normalized or normalized.endswith("_rate"):
			col_type = "percent"
		columns.append(
			{
				"key": normalized,
				"label": normalized.replace("_", " ").title(),
				"type": col_type,
			}
		)
	return columns


def _series_cumulative(values):
	running = 0.0
	payload = []
	for value in values:
		running += flt(value)
		payload.append(round(running, 2))
	return payload


def _group_daily_sales_and_orders(orders):
	grouped = defaultdict(lambda: {"sales": 0.0, "orders": 0})
	for row in orders:
		if not _is_revenue_order(row):
			continue
		date_key = str(getdate(row.get("created_at")))
		grouped[date_key]["sales"] += flt(row.get("grand_total"))
		grouped[date_key]["orders"] += 1
	keys = sorted(grouped.keys())
	return {
		"labels": keys,
		"sales_values": [round(grouped[key]["sales"], 2) for key in keys],
		"order_values": [cint(grouped[key]["orders"]) for key in keys],
	}


def _management_report_meta(date_from=None, date_to=None, compare_mode="previous_window"):
	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
	prev_start, prev_end = _management_previous_window(date_from=date_from, date_to=date_to)
	return {
		"date_from": start_date,
		"date_to": end_date,
		"previous_date_from": prev_start,
		"previous_date_to": prev_end,
		"compare_mode": (compare_mode or "previous_window").strip().lower() or "previous_window",
	}


def _build_management_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	report_key = (report_key or "").strip().lower()
	currency = _get_currency()
	kpis = []
	charts = []
	tables = []
	insights = []

	if report_key == "sales-summary":
		prev_summary = _build_sales_summary(previous_orders)
		daily = _group_daily_sales_and_orders(orders)
		kpis = [
			_bi_kpi(
				"total_sales",
				_("Total Sales"),
				summary.get("total_sales"),
				"money",
				prev_summary.get("total_sales"),
			),
			_bi_kpi(
				"total_orders",
				_("Total Orders"),
				summary.get("total_orders"),
				"count",
				prev_summary.get("total_orders"),
			),
			_bi_kpi(
				"avg_ticket",
				_("Average Ticket"),
				summary.get("avg_ticket"),
				"money",
				prev_summary.get("avg_ticket"),
			),
			_bi_kpi(
				"total_items",
				_("Items Sold"),
				summary.get("total_items"),
				"count",
				prev_summary.get("total_items"),
			),
		]
		charts = [
			{
				"key": "daily-sales-orders",
				"title": _("Daily Sales vs Orders"),
				"type": "line",
				"unit": "money",
				"labels": daily.get("labels"),
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#2f6f5c",
						"values": daily.get("sales_values"),
					},
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#3e8ed0",
						"values": daily.get("order_values"),
					},
				],
			}
		]
		table_rows = [
			{
				"date": label,
				"sales": daily.get("sales_values")[idx],
				"orders": daily.get("order_values")[idx],
				"avg_ticket": round(
					_safe_div(daily.get("sales_values")[idx], daily.get("order_values")[idx]), 2
				),
			}
			for idx, label in enumerate(daily.get("labels") or [])
		]
		tables = [
			{
				"key": "daily-table",
				"title": _("Daily Breakdown"),
				"columns": _table_columns_from_rows(table_rows),
				"rows": table_rows,
			}
		]
		if daily.get("sales_values"):
			peak_index = max(
				range(len(daily.get("sales_values"))), key=lambda idx: daily.get("sales_values")[idx]
			)
			insights.append(
				{
					"key": "peak-day",
					"severity": "info",
					"text": _("Peak sales day in this range: {0}.").format(daily.get("labels")[peak_index]),
				}
			)

	elif report_key == "sales-trend":
		prev_rows = _build_daily_trend(previous_orders)
		previous_total = sum(flt(row.get("sales")) for row in prev_rows)
		expected_daily = round(_safe_div(summary.get("total_sales"), max(cint(summary.get("days")), 1)), 2)
		labels = [row.get("date") for row in rows]
		sales_values = [flt(row.get("sales")) for row in rows]
		expected_values = [expected_daily for _ in rows]
		table_rows = []
		for idx, row in enumerate(rows):
			sales = flt(row.get("sales"))
			expected = expected_values[idx]
			delta_pct = round(_pct_change(sales, expected), 1)
			table_rows.append(
				{
					"date": row.get("date"),
					"sales": sales,
					"expected_sales": expected,
					"delta_percent": delta_pct,
				}
			)
		kpis = [
			_bi_kpi("total_sales", _("Total Sales"), summary.get("total_sales"), "money", previous_total),
			_bi_kpi("days", _("Days in Range"), summary.get("days"), "count", len(prev_rows)),
			_bi_kpi("expected_daily", _("Expected Daily Sales"), expected_daily, "money", expected_daily),
			_bi_kpi(
				"variance",
				_("Sales vs Expected"),
				summary.get("total_sales") - (expected_daily * max(cint(summary.get("days")), 1)),
				"money",
				0,
			),
		]
		charts = [
			{
				"key": "sales-vs-expected",
				"title": _("Sales vs Expected"),
				"type": "line",
				"unit": "money",
				"labels": labels,
				"series": [
					{"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": sales_values},
					{
						"key": "expected",
						"label": _("Expected"),
						"color": "#3e8ed0",
						"values": expected_values,
					},
				],
			},
			{
				"key": "cumulative-sales",
				"title": _("Cumulative Sales"),
				"type": "area",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "cumulative",
						"label": _("Cumulative"),
						"color": "#da8a2f",
						"values": _series_cumulative(sales_values),
					}
				],
			},
		]
		tables = [
			{
				"key": "trend-table",
				"title": _("Daily Trend"),
				"columns": _table_columns_from_rows(table_rows),
				"rows": table_rows,
			}
		]

	elif report_key == "sales-hourly":
		prev_rows = _build_hourly_trend(previous_orders)
		previous_sales = sum(flt(row.get("sales")) for row in prev_rows)
		previous_orders_count = sum(cint(row.get("orders")) for row in prev_rows)
		hour_rows = rows or []
		peak_row = max(
			hour_rows, key=lambda row: flt(row.get("sales")), default={"hour": 0, "sales": 0, "orders": 0}
		)
		labels = [str(row.get("hour")).zfill(2) for row in hour_rows]
		sales_values = [flt(row.get("sales")) for row in hour_rows]
		order_values = [cint(row.get("orders")) for row in hour_rows]
		avg_hourly = round(_safe_div(sum(sales_values), len(hour_rows) or 1), 2)
		kpis = [
			_bi_kpi("total_sales", _("Total Sales"), summary.get("total_sales"), "money", previous_sales),
			_bi_kpi(
				"total_orders", _("Total Orders"), summary.get("total_orders"), "count", previous_orders_count
			),
			_bi_kpi("peak_hour_sales", _("Peak Hour Sales"), peak_row.get("sales"), "money", 0),
			_bi_kpi("avg_hourly_sales", _("Average Hourly Sales"), avg_hourly, "money", avg_hourly),
		]
		charts = [
			{
				"key": "hourly-sales",
				"title": _("Hourly Sales"),
				"type": "line",
				"unit": "money",
				"labels": labels,
				"series": [{"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": sales_values}],
			},
			{
				"key": "hourly-orders",
				"title": _("Hourly Orders"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{"key": "orders", "label": _("Orders"), "color": "#3e8ed0", "values": order_values}
				],
			},
		]
		tables = [
			{
				"key": "hour-table",
				"title": _("Hourly Breakdown"),
				"columns": _table_columns_from_rows(hour_rows),
				"rows": hour_rows,
			}
		]
		insights = [
			{
				"key": "peak-hour-note",
				"severity": "info",
				"text": _("Peak traffic hour: {0}:00 with {1} orders.").format(
					str(peak_row.get("hour")).zfill(2), cint(peak_row.get("orders"))
				),
			}
		]

	elif report_key == "top-products":
		prev_rows = _build_top_products(previous_orders, limit=20)
		previous_total = sum(flt(row.get("amount")) for row in prev_rows)
		data_rows = rows or []
		total_sales = sum(flt(row.get("amount")) for row in data_rows)
		total_qty = sum(flt(row.get("qty")) for row in data_rows)
		top_item = data_rows[0] if data_rows else {}
		top5_share = round(
			_safe_div(sum(flt(row.get("amount")) for row in data_rows[:5]) * 100.0, total_sales or 1), 2
		)
		kpis = [
			_bi_kpi("total_sales", _("Total Sales"), total_sales, "money", previous_total),
			_bi_kpi("products_count", _("Products Count"), len(data_rows), "count", len(prev_rows)),
			_bi_kpi("top5_share", _("Top 5 Share"), top5_share, "percent", top5_share),
			_bi_kpi("top_product_sales", _("Top Product Sales"), top_item.get("amount") or 0, "money", 0),
		]
		labels = [row.get("product_title") for row in data_rows[:10]]
		charts = [
			{
				"key": "products-by-sales",
				"title": _("Top Products by Sales"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#2f6f5c",
						"values": [flt(row.get("amount")) for row in data_rows[:10]],
					}
				],
			},
			{
				"key": "products-by-qty",
				"title": _("Top Products by Quantity"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "qty",
						"label": _("Quantity"),
						"color": "#da8a2f",
						"values": [flt(row.get("qty")) for row in data_rows[:10]],
					}
				],
			},
		]
		normalized_rows = []
		for row in data_rows:
			share = row.get("share_percent")
			if share in (None, ""):
				share = round(_safe_div(flt(row.get("amount")) * 100.0, total_sales or 1), 2)
			normalized_rows.append(
				{
					**row,
					"share_percent": share,
					"avg_price": round(_safe_div(row.get("amount"), row.get("qty")), 2),
				}
			)
		tables = [
			{
				"key": "product-table",
				"title": _("Product Breakdown"),
				"columns": _table_columns_from_rows(normalized_rows),
				"rows": normalized_rows,
			}
		]
		insights = (
			[
				{
					"key": "top-product",
					"severity": "success",
					"text": _("Top product: {0} with sales {1}.").format(
						top_item.get("product_title") or "-",
						frappe.format_value(
							top_item.get("amount") or 0, {"fieldtype": "Currency", "options": currency}
						),
					),
				}
			]
			if top_item
			else []
		)

	elif report_key == "product-mix":
		prev_rows = _build_product_mix_associations(
			previous_orders, limit=80, min_pair_orders=2, min_base_orders=2
		)
		data_rows = rows or []
		avg_confidence = round(
			_safe_div(sum(flt(row.get("confidence_percent")) for row in data_rows), len(data_rows) or 1),
			2,
		)
		prev_avg_confidence = round(
			_safe_div(sum(flt(row.get("confidence_percent")) for row in prev_rows), len(prev_rows) or 1),
			2,
		)
		strong_rules = [row for row in data_rows if flt(row.get("confidence_percent")) >= 50]
		prev_strong_rules = [row for row in prev_rows if flt(row.get("confidence_percent")) >= 50]
		top_rule = data_rows[0] if data_rows else {}

		kpis = [
			_bi_kpi("rules_count", _("Association Rules"), len(data_rows), "count", len(prev_rows)),
			_bi_kpi(
				"avg_confidence", _("Average Confidence"), avg_confidence, "percent", prev_avg_confidence
			),
			_bi_kpi(
				"strong_rules",
				_("Rules >= 50% Confidence"),
				len(strong_rules),
				"count",
				len(prev_strong_rules),
			),
			_bi_kpi(
				"top_confidence", _("Top Confidence"), top_rule.get("confidence_percent") or 0, "percent", 0
			),
		]

		top_chart_rows = data_rows[:12]
		chart_labels = [
			_("{0} + {1}").format(row.get("product_title") or "-", row.get("paired_product_title") or "-")
			for row in top_chart_rows
		]
		charts = [
			{
				"key": "mix-confidence",
				"title": _("Most Frequent Product Combinations"),
				"subtitle": _("Confidence percent for each basket rule"),
				"type": "line",
				"unit": "count",
				"labels": chart_labels,
				"series": [
					{
						"key": "confidence",
						"label": _("Confidence %"),
						"color": "#2f6f5c",
						"values": [flt(row.get("confidence_percent")) for row in top_chart_rows],
					},
					{
						"key": "support",
						"label": _("Support %"),
						"color": "#da8a2f",
						"values": [flt(row.get("support_percent")) for row in top_chart_rows],
					},
				],
			}
		]

		tables = [
			{
				"key": "mix-rules",
				"title": _("Product Mix Rules"),
				"subtitle": _("Example: when customer buys A, how often they also buy B"),
				"columns": _table_columns_from_rows(data_rows),
				"rows": data_rows,
			}
		]

		best_by_product = {}
		for row in data_rows:
			product_title = row.get("product_title") or ""
			if not product_title or product_title in best_by_product:
				continue
			best_by_product[product_title] = row
		summary_rows = []
		for product_title, row in sorted(
			best_by_product.items(), key=lambda item: flt(item[1].get("confidence_percent")), reverse=True
		):
			summary_rows.append(
				{
					"product_title": product_title,
					"best_pair_title": row.get("paired_product_title") or "",
					"confidence_percent": flt(row.get("confidence_percent")),
					"support_percent": flt(row.get("support_percent")),
					"co_order_count": cint(row.get("co_order_count")),
				}
			)
		if summary_rows:
			tables.append(
				{
					"key": "mix-summary",
					"title": _("Best Cross-Sell Pair per Product"),
					"columns": _table_columns_from_rows(summary_rows),
					"rows": summary_rows[:20],
				}
			)

		if top_rule:
			insights.append(
				{
					"key": "top-mix",
					"severity": "success",
					"text": _("{0} customers also buy {1} in {2}% of orders.").format(
						top_rule.get("product_title") or "-",
						top_rule.get("paired_product_title") or "-",
						round(flt(top_rule.get("confidence_percent") or 0), 2),
					),
				}
			)

	elif report_key == "order-status":
		prev_rows = _build_status_rows(previous_orders)
		prev_total = sum(cint(row.get("orders")) for row in prev_rows)
		total_orders = sum(cint(row.get("orders")) for row in rows)
		by_status = {str(row.get("status") or "").lower(): row for row in rows}
		delivered = cint((by_status.get("delivered") or {}).get("orders"))
		cancelled = cint((by_status.get("cancelled") or {}).get("orders"))
		open_orders = total_orders - delivered - cancelled
		kpis = [
			_bi_kpi("total_orders", _("Total Orders"), total_orders, "count", prev_total),
			_bi_kpi(
				"delivered_rate",
				_("Delivered Rate"),
				round(_safe_div(delivered * 100.0, total_orders or 1), 2),
				"percent",
				0,
			),
			_bi_kpi(
				"cancelled_rate",
				_("Cancelled Rate"),
				round(_safe_div(cancelled * 100.0, total_orders or 1), 2),
				"percent",
				0,
			),
			_bi_kpi("open_orders", _("Open Orders"), open_orders, "count", 0),
		]
		labels = [row.get("status") for row in rows]
		charts = [
			{
				"key": "orders-by-status",
				"title": _("Orders by Status"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#2f6f5c",
						"values": [cint(row.get("orders")) for row in rows],
					}
				],
			},
			{
				"key": "sales-by-status",
				"title": _("Sales by Status"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#3e8ed0",
						"values": [flt(row.get("sales")) for row in rows],
					}
				],
			},
		]
		tables = [
			{
				"key": "status-table",
				"title": _("Status Breakdown"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]

	elif report_key == "channel-split":
		prev_rows = _build_channel_rows(previous_orders)
		prev_total_sales = sum(flt(row.get("sales")) for row in prev_rows)
		total_sales = sum(flt(row.get("sales")) for row in rows)
		by_channel = {str(row.get("channel") or "").lower(): row for row in rows}
		dine_sales = flt((by_channel.get("dine_in") or {}).get("sales"))
		takeaway_sales = flt((by_channel.get("takeaway") or {}).get("sales"))
		delivery_sales = flt((by_channel.get("delivery") or {}).get("sales"))
		kpis = [
			_bi_kpi("total_sales", _("Total Sales"), total_sales, "money", prev_total_sales),
			_bi_kpi(
				"dine_in_share",
				_("Dine-In Share"),
				round(_safe_div(dine_sales * 100.0, total_sales or 1), 2),
				"percent",
				0,
			),
			_bi_kpi(
				"takeaway_share",
				_("Takeaway Share"),
				round(_safe_div(takeaway_sales * 100.0, total_sales or 1), 2),
				"percent",
				0,
			),
			_bi_kpi(
				"delivery_share",
				_("Delivery Share"),
				round(_safe_div(delivery_sales * 100.0, total_sales or 1), 2),
				"percent",
				0,
			),
		]
		labels = [row.get("channel") for row in rows]
		charts = [
			{
				"key": "channel-sales",
				"title": _("Sales by Channel"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#2f6f5c",
						"values": [flt(row.get("sales")) for row in rows],
					}
				],
			},
			{
				"key": "channel-orders",
				"title": _("Orders by Channel"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#da8a2f",
						"values": [cint(row.get("orders")) for row in rows],
					}
				],
			},
		]
		tables = [
			{
				"key": "channel-table",
				"title": _("Channel Breakdown"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]

	elif report_key == "cashier-performance":
		prev_rows = _build_cashier_rows(previous_orders)
		prev_total_sales = sum(flt(row.get("sales")) for row in prev_rows)
		total_sales = sum(flt(row.get("sales")) for row in rows)
		top_cashier = rows[0] if rows else {}
		avg_ticket_all = round(_safe_div(total_sales, sum(cint(row.get("orders")) for row in rows) or 1), 2)
		kpis = [
			_bi_kpi("total_sales", _("Total Sales"), total_sales, "money", prev_total_sales),
			_bi_kpi("cashiers", _("Cashiers"), len(rows), "count", len(prev_rows)),
			_bi_kpi("top_cashier_sales", _("Top Cashier Sales"), top_cashier.get("sales") or 0, "money", 0),
			_bi_kpi("avg_ticket", _("Average Ticket"), avg_ticket_all, "money", avg_ticket_all),
		]
		labels = [row.get("cashier") for row in rows[:10]]
		charts = [
			{
				"key": "cashier-sales",
				"title": _("Sales by Cashier"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#2f6f5c",
						"values": [flt(row.get("sales")) for row in rows[:10]],
					}
				],
			},
			{
				"key": "cashier-orders",
				"title": _("Orders by Cashier"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#3e8ed0",
						"values": [cint(row.get("orders")) for row in rows[:10]],
					}
				],
			},
		]
		tables = [
			{
				"key": "cashier-table",
				"title": _("Cashier Performance"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]

	elif report_key == "cancellations":
		prev_rows = _build_cancellation_rows(previous_orders)
		total_orders = len([order for order in orders if _is_revenue_order(order)])
		cancelled_amount = sum(flt(row.get("amount")) for row in rows)
		prev_cancelled_amount = sum(flt(row.get("amount")) for row in prev_rows)
		by_date = defaultdict(lambda: {"count": 0, "amount": 0.0})
		for row in rows:
			date_key = str(getdate(row.get("created_at")))
			by_date[date_key]["count"] += 1
			by_date[date_key]["amount"] += flt(row.get("amount"))
		labels = sorted(by_date.keys())
		kpis = [
			_bi_kpi("cancelled_orders", _("Cancelled Orders"), len(rows), "count", len(prev_rows)),
			_bi_kpi(
				"cancelled_amount", _("Cancelled Amount"), cancelled_amount, "money", prev_cancelled_amount
			),
			_bi_kpi(
				"cancel_rate",
				_("Cancel Rate"),
				round(_safe_div(len(rows) * 100.0, total_orders or 1), 2),
				"percent",
				0,
			),
			_bi_kpi("lost_amount", _("Lost Revenue"), cancelled_amount, "money", prev_cancelled_amount),
		]
		charts = [
			{
				"key": "cancelled-count-trend",
				"title": _("Cancellation Count Trend"),
				"type": "line",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "count",
						"label": _("Cancelled Orders"),
						"color": "#b84f4f",
						"values": [by_date[key]["count"] for key in labels],
					}
				],
			},
			{
				"key": "cancelled-amount-trend",
				"title": _("Cancellation Amount Trend"),
				"type": "bar",
				"unit": "money",
				"labels": labels,
				"series": [
					{
						"key": "amount",
						"label": _("Cancelled Amount"),
						"color": "#da8a2f",
						"values": [round(by_date[key]["amount"], 2) for key in labels],
					}
				],
			},
		]
		tables = [
			{
				"key": "cancellation-table",
				"title": _("Cancellation Orders"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]
		if cancelled_amount > 0:
			insights.append(
				{
					"key": "cancel-risk",
					"severity": "warn",
					"text": _("There is a measurable cancellation impact in this window."),
				}
			)

	elif report_key == "modifier-usage":
		prev_rows = _build_modifier_usage_rows(previous_orders)
		prev_total_usage = sum(cint(row.get("usage_count")) for row in prev_rows)
		total_usage = sum(cint(row.get("usage_count")) for row in rows)
		top_modifier = rows[0] if rows else {}
		group_rows = defaultdict(int)
		for row in rows:
			group_rows[row.get("group") or "Unknown"] += cint(row.get("usage_count"))
		labels = [row.get("option") for row in rows[:10]]
		usage_per_order = round(_safe_div(total_usage, len(orders) or 1), 2)
		kpis = [
			_bi_kpi("modifiers", _("Unique Modifiers"), len(rows), "count", len(prev_rows)),
			_bi_kpi("total_usage", _("Total Usage"), total_usage, "count", prev_total_usage),
			_bi_kpi(
				"top_modifier_usage",
				_("Top Modifier Usage"),
				top_modifier.get("usage_count") or 0,
				"count",
				0,
			),
			_bi_kpi("usage_per_order", _("Usage per Order"), usage_per_order, "count", usage_per_order),
		]
		charts = [
			{
				"key": "top-modifier-usage",
				"title": _("Top Modifier Usage"),
				"type": "bar",
				"unit": "count",
				"labels": labels,
				"series": [
					{
						"key": "usage",
						"label": _("Usage"),
						"color": "#2f6f5c",
						"values": [cint(row.get("usage_count")) for row in rows[:10]],
					}
				],
			},
			{
				"key": "group-modifier-usage",
				"title": _("Usage by Group"),
				"type": "bar",
				"unit": "count",
				"labels": list(group_rows.keys()),
				"series": [
					{
						"key": "group_usage",
						"label": _("Usage"),
						"color": "#3e8ed0",
						"values": [cint(value) for value in group_rows.values()],
					}
				],
			},
		]
		tables = [
			{
				"key": "modifier-table",
				"title": _("Modifier Usage"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]

	elif report_key in MANAGEMENT_FEATURE_PACK_REPORTS:
		# Feature-pack reports (category/table/payment-method/product/shift sales).
		fp_bi = fp_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(fp_bi, dict):
			kpis = fp_bi.get("kpis") or []
			charts = fp_bi.get("charts") or []
			tables = fp_bi.get("tables") or []
			insights = fp_bi.get("insights") or []

	elif report_key in MANAGEMENT_INVENTORY_REPORTS:
		# Inventory reports (valuation/movements/waste & losses).
		inv_bi = inv_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(inv_bi, dict):
			kpis = inv_bi.get("kpis") or []
			charts = inv_bi.get("charts") or []
			tables = inv_bi.get("tables") or []
			insights = inv_bi.get("insights") or []

	elif report_key in CLUB_REPORT_KEYS:
		# Customer-club reports (RFM, campaigns, wallet, surveys).
		club_bi = club_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(club_bi, dict):
			kpis = club_bi.get("kpis") or []
			charts = club_bi.get("charts") or []
			tables = club_bi.get("tables") or []
			insights = club_bi.get("insights") or []

	elif report_key in OPS_REPORT_KEYS:
		# Ops/finance reports (couriers, kitchen, P&L, break-even).
		ops_bi = ops_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(ops_bi, dict):
			kpis = ops_bi.get("kpis") or []
			charts = ops_bi.get("charts") or []
			tables = ops_bi.get("tables") or []
			insights = ops_bi.get("insights") or []

	elif report_key in MENUENG_REPORT_KEYS:
		menueng_bi = menueng_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(menueng_bi, dict):
			kpis = menueng_bi.get("kpis") or []
			charts = menueng_bi.get("charts") or []
			tables = menueng_bi.get("tables") or []
			insights = menueng_bi.get("insights") or []

	elif report_key in TAX_REPORT_KEYS:
		tax_bi = tax_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(tax_bi, dict):
			kpis = tax_bi.get("kpis") or []
			charts = tax_bi.get("charts") or []
			tables = tax_bi.get("tables") or []
			insights = tax_bi.get("insights") or []

	elif report_key in BRANCH_REPORT_KEYS:
		branch_bi = branch_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(branch_bi, dict):
			kpis = branch_bi.get("kpis") or []
			charts = branch_bi.get("charts") or []
			tables = branch_bi.get("tables") or []
			insights = branch_bi.get("insights") or []

	elif report_key in KIOSK_REPORT_KEYS:
		kiosk_bi = kiosk_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(kiosk_bi, dict):
			kpis = kiosk_bi.get("kpis") or []
			charts = kiosk_bi.get("charts") or []
			tables = kiosk_bi.get("tables") or []
			insights = kiosk_bi.get("insights") or []

	elif report_key in ACC_REPORT_KEYS:
		acc_bi = acc_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta)
		if isinstance(acc_bi, dict):
			kpis = acc_bi.get("kpis") or []
			charts = acc_bi.get("charts") or []
			tables = acc_bi.get("tables") or []
			insights = acc_bi.get("insights") or []

	if not tables and rows:
		tables = [
			{
				"key": "report-table",
				"title": _("Report Table"),
				"columns": _table_columns_from_rows(rows),
				"rows": rows,
			}
		]

	return {
		"meta": meta,
		"kpis": kpis,
		"charts": charts,
		"tables": tables,
		"insights": insights,
		"currency": currency,
	}


def _compose_management_report(
	report_key, title, summary, rows, date_from=None, date_to=None, source="all", orders=None
):
	current_orders = (
		orders
		if orders is not None
		else _management_collect_orders(date_from=date_from, date_to=date_to, source=source)
	)
	prev_start, prev_end = _management_previous_window(date_from=date_from, date_to=date_to)
	previous_orders = _management_collect_orders(date_from=prev_start, date_to=prev_end, source=source)
	meta = _management_report_meta(date_from=date_from, date_to=date_to, compare_mode="previous_window")
	bi_payload = _build_management_report_bi(
		report_key=report_key,
		title=title,
		summary=summary or {},
		rows=rows or [],
		orders=current_orders or [],
		previous_orders=previous_orders or [],
		meta=meta,
	)
	return _management_report_payload(
		report_key=report_key,
		title=title,
		summary=summary,
		rows=rows,
		currency=bi_payload.get("currency") or _get_currency(),
		meta=bi_payload.get("meta"),
		kpis=bi_payload.get("kpis") or [],
		charts=bi_payload.get("charts") or [],
		tables=bi_payload.get("tables") or [],
		insights=bi_payload.get("insights") or [],
	)


def _management_report_payload(
	report_key,
	title,
	summary,
	rows,
	currency=None,
	meta=None,
	kpis=None,
	charts=None,
	tables=None,
	insights=None,
):
	return {
		"report_key": report_key,
		"title": title,
		"summary": summary or {},
		"rows": rows or [],
		"currency": currency or _get_currency(),
		"meta": meta or {},
		"kpis": kpis or [],
		"charts": charts or [],
		"tables": tables or [],
		"insights": insights or [],
	}


def _management_hardware_summary(date_from=None, date_to=None):
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	summary = {
		"node": {
			"connected": False,
			"message": _("Local node is not checked."),
			"latency_ms": 0,
		},
		"payments": {
			"total": 0,
			"paid": 0,
			"failed": 0,
			"pending": 0,
			"success_rate": 0,
		},
		"events": {
			"error_count": 0,
			"warn_count": 0,
			"invalid_scale_scan_count": 0,
			"recent_errors": [],
		},
	}

	try:
		health = get_management_pos_hardware_status()
		summary["node"] = {
			"connected": bool(health.get("connected")),
			"message": health.get("message") or "",
			"latency_ms": cint(health.get("latency_ms") or 0),
			"provider": health.get("provider") or "",
		}
	except Exception:
		summary["node"] = {
			"connected": False,
			"message": _("Health check failed."),
			"latency_ms": 0,
		}

	if frappe.db.exists("DocType", "Restaurant POS Payment Log"):
		payment_rows = frappe.get_all(
			"Restaurant POS Payment Log",
			fields=["status"],
			filters={"creation": ["between", [start_dt, end_dt]]},
			ignore_permissions=True,
			limit_page_length=1000,
		)
		for row in payment_rows:
			status = (row.get("status") or "").strip().lower()
			summary["payments"]["total"] += 1
			if status == "paid":
				summary["payments"]["paid"] += 1
			elif status == "pending":
				summary["payments"]["pending"] += 1
			else:
				summary["payments"]["failed"] += 1

		total = summary["payments"]["total"]
		if total:
			summary["payments"]["success_rate"] = round((summary["payments"]["paid"] * 100.0) / total, 1)

	if frappe.db.exists("DocType", "Restaurant POS Hardware Event"):
		event_rows = frappe.get_all(
			"Restaurant POS Hardware Event",
			fields=["severity", "event_type", "message", "creation", "payload_json"],
			filters={"creation": ["between", [start_dt, end_dt]]},
			order_by="creation desc",
			ignore_permissions=True,
			limit_page_length=200,
		)

		recent_errors = []
		for row in event_rows:
			severity = (row.get("severity") or "").strip().lower()
			event_type = (row.get("event_type") or "").strip().lower()
			if severity == "error":
				summary["events"]["error_count"] += 1
				if len(recent_errors) < 10:
					recent_errors.append(
						{
							"event_type": event_type,
							"message": row.get("message") or "",
							"created_at": _json_safe_datetime(row.get("creation")),
						}
					)
			if severity == "warn":
				summary["events"]["warn_count"] += 1
			if event_type == "scale" and severity in {"warn", "error"}:
				payload = _parse_json(row.get("payload_json"), {})
				if payload.get("reason") == "invalid_barcode":
					summary["events"]["invalid_scale_scan_count"] += 1

		summary["events"]["recent_errors"] = recent_errors

	return summary


def _management_operational_metrics(date_from=None, date_to=None):
	metrics = {
		"satisfaction_avg": None,
		"satisfaction_count": 0,
		"avg_delivery_mins": None,
		"max_delivery_mins": None,
		"max_delivery_order": "",
	}

	if not frappe.db.exists("DocType", "Sales Order"):
		return metrics

	rating_candidates = [
		"restaurant_customer_rating",
		"restaurant_rating",
		"customer_rating",
	]
	delivery_candidates = [
		"restaurant_delivery_mins",
		"restaurant_delivery_minutes",
		"delivery_minutes",
	]
	rating_field = next((field for field in rating_candidates if _has_column("Sales Order", field)), "")
	delivery_field = next((field for field in delivery_candidates if _has_column("Sales Order", field)), "")
	if not rating_field and not delivery_field:
		return metrics

	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	has_transaction_date = _has_column("Sales Order", "transaction_date")
	fields = ["name"]
	if has_transaction_date:
		fields.append("transaction_date")
	if rating_field:
		fields.append(rating_field)
	if delivery_field:
		fields.append(delivery_field)

	filters = {}
	if has_transaction_date:
		filters["transaction_date"] = ["between", [start_date, end_date]]
	else:
		filters["creation"] = ["between", [start_dt, end_dt]]

	rows = frappe.get_all(
		"Sales Order",
		fields=fields,
		filters=filters,
		ignore_permissions=True,
		limit_page_length=2000,
	)

	ratings = []
	delivery_values = []
	max_delivery_order = ""
	max_delivery_value = -1

	for row in rows:
		if rating_field:
			rating_value = flt(row.get(rating_field))
			if rating_value > 0:
				ratings.append(rating_value)

		if delivery_field:
			delivery_value = flt(row.get(delivery_field))
			if delivery_value > 0:
				delivery_values.append(delivery_value)
				if delivery_value > max_delivery_value:
					max_delivery_value = delivery_value
					max_delivery_order = (
						row.name
					) or row.get("name")

	if ratings:
		metrics["satisfaction_avg"] = round(sum(ratings) / len(ratings), 2)
		metrics["satisfaction_count"] = len(ratings)
	if delivery_values:
		metrics["avg_delivery_mins"] = round(sum(delivery_values) / len(delivery_values), 2)
		metrics["max_delivery_mins"] = round(max(delivery_values), 2)
		metrics["max_delivery_order"] = max_delivery_order

	return metrics


def _management_item_lookup_tokens(item_doc):
	tokens = set()
	if not item_doc:
		return tokens

	for fieldname in ("name", "item_code", "item_name"):
		value = (
			item_doc.get(fieldname) if hasattr(item_doc, "get") else getattr(item_doc, fieldname, "")
		) or ""
		token = str(value).strip().lower()
		if token:
			tokens.add(token)
	return tokens


def _management_top_product_nutrition(rows, token_map):
	totals = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	for row in rows or []:
		title_key = str(row.get("product_title") or "").strip().lower()
		item_doc = token_map.get(title_key)
		if not item_doc:
			continue

		qty = flt(row.get("qty") or 0)
		if qty <= 0:
			continue

		per_unit = _nutrition_per_unit_payload(item_doc)
		_add_nutrition_to_totals(totals, per_unit, qty)

	return _nutrition_payload_from_totals(totals)


def _management_dashboard_nutrition_snapshot(orders):
	top_products = _build_top_products(orders, limit=8)
	if not top_products:
		return {"nutrition": {}, "top_products": []}

	product_titles = {
		str(row.get("product_title") or "").strip().lower()
		for row in top_products
		if str(row.get("product_title") or "").strip()
	}
	if not product_titles:
		return {"nutrition": {}, "top_products": top_products}

	item_rows = frappe.get_all(
		"Item",
		fields=["name", "item_code", "item_name"],
		ignore_permissions=True,
		limit_page_length=5000,
	)
	token_map = {}
	for row in item_rows:
		item_doc = frappe.get_cached_doc("Item", row.name)
		for token in _management_item_lookup_tokens(item_doc):
			if token in product_titles:
				token_map[token] = item_doc

	for row in top_products:
		token = str(row.get("product_title") or "").strip().lower()
		item_doc = token_map.get(token)
		if not item_doc:
			continue
		qty = flt(row.get("qty") or 0)
		per_unit = _nutrition_per_unit_payload(item_doc)
		per_item = {key: round(flt(per_unit.get(key) or 0), 2) for key in NUTRITION_KEY_FIELD_MAP}
		totals = {key: round(flt(per_item.get(key) or 0) * qty, 2) for key in NUTRITION_KEY_FIELD_MAP}
		row["nutrition_per_item"] = per_item
		row["nutrition_totals"] = totals
		row["nutrition_per_item_payload"] = _nutrition_payload_from_totals(per_item)
		row["nutrition_totals_payload"] = _nutrition_payload_from_totals(totals)

	return {
		"nutrition": _management_top_product_nutrition(top_products, token_map),
		"top_products": top_products,
	}


@frappe.whitelist()
def get_management_dashboard(date_from=None, date_to=None, branch=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	summary = _build_sales_summary(orders)
	nutrition_snapshot = _management_dashboard_nutrition_snapshot(orders)
	return {
		"date_from": _management_date_window(date_from=date_from, date_to=date_to)[0],
		"date_to": _management_date_window(date_from=date_from, date_to=date_to)[1],
		"currency": _get_currency(),
		"kpis": summary,
		"top_products": nutrition_snapshot.get("top_products") or _build_top_products(orders, limit=6),
		"nutrition": nutrition_snapshot.get("nutrition") or {},
		"status_breakdown": _build_status_rows(orders),
		"channel_breakdown": _build_channel_rows(orders),
		"sales_trend": _build_daily_trend(orders),
		"recent_orders": orders[:10],
		"hardware": _management_hardware_summary(date_from=date_from, date_to=date_to),
		"operational": _management_operational_metrics(date_from=date_from, date_to=date_to),
		"courier_fleet": _management_courier_summary(),
	}


@frappe.whitelist()
def get_management_pos_hardware_status():
	_ensure_management_access()
	settings = _get_pos_payment_settings()

	response = {
		"connected": False,
		"provider": settings.get("provider") or "manual",
		"message": _("Hardware provider is manual mode."),
		"latency_ms": 0,
		"terminal_id": settings.get("terminal_id") or "",
		"scale": settings.get("scale") or {},
	}

	if (settings.get("provider") or "") != "local_node":
		return response

	start = now_datetime()
	health = _call_local_hardware_node("/v1/device/health", payload={}, settings=settings, method="GET")
	end = now_datetime()
	latency_ms = max(cint((end - start).total_seconds() * 1000), 0)
	payload = health.get("response") or {}
	response.update(
		{
			"connected": bool(health.get("ok")),
			"latency_ms": latency_ms,
			"message": payload.get("message")
			or (
				_("Local node is connected.")
				if health.get("ok")
				else (health.get("error") or _("Local node is offline."))
			),
			"driver": payload.get("driver") or payload.get("payment_driver") or "",
			"devices": payload.get("devices") or {},
		}
	)

	return response


@frappe.whitelist()
def list_management_pos_payment_logs(date_from=None, date_to=None, status=None, limit=50):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant POS Payment Log"):
		return {"logs": []}

	start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
	filters = {"creation": ["between", [start_dt, end_dt]]}
	normalized_status = (status or "").strip().lower()
	if normalized_status:
		filters["status"] = normalized_status

	rows = frappe.get_all(
		"Restaurant POS Payment Log",
		fields=[
			"name",
			"request_id",
			"sales_order",
			"order_code",
			"amount",
			"currency",
			"provider",
			"payment_method",
			"status",
			"rrn",
			"trace_no",
			"latency_ms",
			"error_text",
			"creation",
		],
		filters=filters,
		order_by="creation desc",
		ignore_permissions=True,
		limit_page_length=max(cint(limit), 1),
	)

	return {
		"logs": [
			{
				**row,
				"created_at": _json_safe_datetime(row.get("creation")),
			}
			for row in rows
		]
	}


@frappe.whitelist()
def report_management_pos_hardware_event(
	event_type, severity, message, payload=None, related_order=None, source="pos"
):
	_ensure_management_access()
	parsed_payload = _parse_json(payload, {})
	_insert_management_hardware_event(
		event_type=event_type,
		severity=severity,
		message=message,
		payload=parsed_payload,
		related_order=related_order,
		source=source,
	)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def get_management_pos_config():
	"""Get POS default configuration (order mode defaults, place presets)."""
	_ensure_management_access()
	raw = frappe.defaults.get_global_default("restaurant_pos_defaults") or "{}"
	if isinstance(raw, str):
		raw = raw.strip()
		if not raw:
			raw = "{}"
	try:
		config = json.loads(raw) if isinstance(raw, str) else raw
	except (json.JSONDecodeError, TypeError):
		config = {}

	delivery_couriers = _list_management_courier_options(active_only=True)
	default_delivery_courier = (config.get("default_delivery_courier") or "").strip()
	if not default_delivery_courier and delivery_couriers:
		default_delivery_courier = delivery_couriers[0].get("label") or ""

	payment_profile = _management_pos_profile_summary()
	payment_options = payment_profile.get("payments") or []
	if not payment_options and frappe.db.exists("DocType", "Mode of Payment"):
		payment_options = [
			{"mode_of_payment": row.get("name"), "type": row.get("type") or ""}
			for row in frappe.get_all(
				"Mode of Payment",
				fields=["name", "type"],
				filters={"enabled": 1} if _has_column("Mode of Payment", "enabled") else {},
				order_by="name asc",
				limit_page_length=200,
			)
		]
	defaults = {
		"default_order_mode": config.get("default_order_mode", "dine_in"),
		"default_customers": config.get(
			"default_customers",
			{
				"dine_in": {"name": "POS Customer", "mobile": ""},
				"takeaway": {"name": "POS Customer", "mobile": ""},
				"delivery": {"name": "POS Customer", "mobile": ""},
			},
		),
		"takeaway_places": config.get("takeaway_places", ["بیرون بر حضوری", "تحویل کنار سالن"]),
		"default_takeaway_place": config.get("default_takeaway_place", "بیرون بر حضوری"),
		"delivery_places": config.get("delivery_places", ["پیک 1", "پیک 2", "پیک 3", "ارسال اکسپرس"]),
		"default_delivery_place": config.get("default_delivery_place", "پیک 1"),
		"default_delivery_courier": default_delivery_courier,
		"default_payment_option": (config.get("default_payment_option") or "").strip(),
		"default_payment_method": _normalize_payment_method(config.get("default_payment_method") or "cash"),
		"payment_options": payment_options,
		"delivery_couriers": delivery_couriers,
	}
	return defaults


@frappe.whitelist()
def set_management_pos_config(payload=None):
	"""Save POS default configuration for the current user/operator."""
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))

	raw = frappe.defaults.get_global_default("restaurant_pos_defaults") or "{}"
	if isinstance(raw, str):
		raw = raw.strip()
		if not raw:
			raw = "{}"
	try:
		current = json.loads(raw) if isinstance(raw, str) else raw
	except (json.JSONDecodeError, TypeError):
		current = {}

	for key in (
		"default_order_mode",
		"default_customers",
		"takeaway_places",
		"default_takeaway_place",
		"delivery_places",
		"default_delivery_place",
		"default_delivery_courier",
		"default_payment_option",
		"default_payment_method",
	):
		if key in data:
			current[key] = data[key]

	frappe.defaults.set_global_default("restaurant_pos_defaults", json.dumps(current, ensure_ascii=False))
	frappe.db.commit()
	return {"status": "success", "config": get_management_pos_config()}



@frappe.whitelist()
def get_management_pos_boot(branch=None):
	_ensure_management_access()
	branch = (branch or "").strip()
	image_field = _core_item_image_field()
	category_meta_map = _get_core_category_meta_map()
	subcategory_meta_map = _get_core_subcategory_meta_map()
	boot_item_fields = [
		"name",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		f"{image_field} as image",
		"restaurant_category",
		"restaurant_subcategory",
	]
	if _has_column("Item", "restaurant_out_of_stock"):
		boot_item_fields.append("restaurant_out_of_stock")
	if _has_column("Item", "restaurant_packaging_price"):
		boot_item_fields.append("restaurant_packaging_price")
	rows = frappe.get_all(
		"Item",
		filters=_core_item_filters(branch),
		fields=boot_item_fields,
		ignore_permissions=True,
		order_by="restaurant_sort_order asc, item_name asc",
		limit=300,
	)

	# Fallback: for items with no image, get first attachment
	item_names = [r["name"] for r in rows if not (r.get("image") or "").strip()]
	attachment_map = {}
	if item_names and frappe.db.exists("DocType", "File"):
		attached = frappe.get_all(
			"File",
			fields=["attached_to_name", "file_url"],
			filters={
				"attached_to_doctype": "Item",
				"attached_to_name": ["in", item_names],
				"is_folder": 0,
				"is_private": 0,
			},
			order_by="creation asc",
			ignore_permissions=True,
		)
		for att in attached:
			name = att.get("attached_to_name")
			if name and name not in attachment_map:
				attachment_map[name] = att.get("file_url", "")

	for r in rows:
		if not (r.get("image") or "").strip() and r["name"] in attachment_map:
			r["image"] = attachment_map[r["name"]]

	items = []
	for row in rows:
		serialized = _serialize_core_item(
			row,
			category_meta_map=category_meta_map,
			subcategory_meta_map=subcategory_meta_map,
		)
		serialized["out_of_stock"] = cint(row.get("restaurant_out_of_stock") or 0)
		serialized["packaging_price"] = flt(row.get("restaurant_packaging_price") or 0)
		items.append(serialized)
	categories = [
		{
			"name": key,
			"title": value.get("title"),
			"slug": value.get("slug"),
		}
		for key, value in category_meta_map.items()
	]
	config = get_management_pos_config()
	print_brand_settings = _management_get_print_brand_settings()
	return {
		"currency": _get_currency(),
		"items": items,
		"categories": sorted(categories, key=lambda row: row.get("title") or ""),
		"payment": _management_pos_payment_boot(),
		"pos_profile": _management_pos_profile_summary(),
		"pos_config": config,
		"packaging": {
			"enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_packaging_enabled", 0))
			== 1,
			"flat_fee": flt(_get_single_setting("Restaurant Web Settings", "restaurant_packaging_flat_fee", 0)),
			"per_item": cint(
				_get_single_setting("Restaurant Web Settings", "restaurant_packaging_per_item", 1)
			)
			== 1,
			"apply_modes": [
				mode
				for mode, fieldname in (
					("takeaway", "restaurant_packaging_takeaway"),
					("delivery", "restaurant_packaging_delivery"),
					("dine_in", "restaurant_packaging_dine_in"),
				)
				if cint(_get_single_setting("Restaurant Web Settings", fieldname, 0)) == 1
			],
			"label": _get_single_setting("Restaurant Web Settings", "restaurant_packaging_label", "")
			or _("Packaging Fee"),
		},
		"print_font": {
			"font_family": print_brand_settings.get("print_font_family") or "Peyda",
			"font_size": min(max(cint(print_brand_settings.get("print_font_size") or 11), 8), 24),
			"receipt_font_scale": print_brand_settings.get("print_receipt_font_scale") or "متوسط",
		},
	}


def _create_pos_order_payload(payload, commit=True):
    """Create the POS Sales Order and optionally leave the transaction open.

    Combined POS actions used to call the public create endpoint first, which
    committed the Sales Order, and then start a second transaction for the
    Sales Invoice.  Keeping both writes in one request/transaction removes a
    full commit round-trip while preserving the same public API behavior.
    """
    payload = _parse_json(payload, {})
    if not isinstance(payload, dict):
        payload = {}
    customer_name = (payload.get("customer_name") or "POS Customer").strip()
    mobile = (payload.get("mobile") or "").strip()
    order_type = (payload.get("order_type") or "takeaway").strip()
    address = (payload.get("address") or "").strip()
    note = (payload.get("note") or "").strip()
    items = payload.get("items") or []
    financial_modifiers = payload.get("financial_modifiers", {})
    totals_payload = payload.get("totals", {})
    # waiter / table / org context for dine-in attribution
    order_context = _parse_json(payload.get("order_context"), {})
    if not isinstance(order_context, dict):
        order_context = {}
    waiter = (payload.get("waiter") or "").strip()
    waiter_name = (payload.get("waiter_name") or "").strip()
    if waiter and not order_context.get("waiter"):
        order_context["waiter"] = waiter
    if waiter_name and not order_context.get("waiter_name"):
        order_context["waiter_name"] = waiter_name
    table = (payload.get("table") or "").strip()
    place = (payload.get("place") or "").strip()
    guest_count = max(cint(payload.get("guest_count") or 1), 1)
    if table and not order_context.get("table"):
        order_context["table"] = table
    if place and not order_context.get("place"):
        order_context["place"] = place
    if place and order_type == "dine_in" and not order_context.get("table"):
        order_context["table"] = place
    order_context["guest_count"] = guest_count

    result = place_order(
        customer_info={"name": customer_name, "mobile": mobile},
        order_type=order_type, items=items,
        address=address, note=note,
        include_service_items=1,
        order_context=order_context,
        financial_modifiers=financial_modifiers,
        totals=totals_payload,
        # The wrapper owns the commit so combined POS actions can include the
        # Sales Invoice in the same transaction.
        commit=False,
    )
    so_name = _resolve_sales_order_name(result.get("order_id") or result.get("name") or "")
    _set_restaurant_order_status(so_name, "confirmed", force=True)
    _append_sales_order_note(so_name, "[ORDER] Order created.")
    if commit:
        frappe.db.commit()
    return {
        "status": "success",
        "order_id": so_name,
        "order_code": result.get("order_code") or "",
    }


@frappe.whitelist()
def create_pos_order(payload):
    # ثبت سفارش: فقط SO بساز (بدون تولید، بدون پرداخت)
    _ensure_management_access()
    return _create_pos_order_payload(payload, commit=True)


@frappe.whitelist()
def produce_pos_order(order_name):
    # شروع تولید: Auto Flow (WO + SE) برا کالاهای BOM دار
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)
    try:
        auto_result = _run_sales_order_auto_flow(so_name, trigger="order_submit", force=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ProducePOS AutoFlow")
        frappe.throw(_("Production auto flow failed."))
    _set_restaurant_order_status(so_name, "preparing", force=True)
    _append_sales_order_note(so_name, "[PRODUCE] Production started.")
    frappe.db.commit()
    return {
        "status": "success",
        "order_id": so_name,
        "automation": auto_result if isinstance(auto_result, dict) else {},
    }

@frappe.whitelist()
def create_and_pay_pos_order(payload):
    """ثبت + تسویه: SO ساخته میشه بعد SI + Payment یکجا (بدون تولید)"""
    _ensure_management_access()
    payload = _parse_json(payload, {})
    if not isinstance(payload, dict):
        payload = {}
    
    # Build the SO and invoice in one request/transaction.  The old path
    # committed once in create_pos_order and again in settle_pos_order.
    order_result = _create_pos_order_payload(payload, commit=False)
    so_name = order_result.get("order_id", "")

    payment_info = _parse_json(payload.get("payment"), {})
    settle_result = settle_pos_order(
        order_name=so_name,
        payment=payment_info,
        commit=False,
    )
    frappe.db.commit()

    return {
        "order_id": so_name,
        "order_code": order_result.get("order_code", ""),
        "status": "success",
        "sales_invoice": settle_result.get("sales_invoice", ""),
    }

@frappe.whitelist()
def create_management_order_proforma(order_name):
    """ساخت پیش‌فاکتور (Quotation) از روی سفارش — برای گارسون/صندوق."""
    _ensure_management_access()
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("سفارش یافت نشد: {0}").format(order_name or "-"))
    if not frappe.db.exists("DocType", "Quotation"):
        frappe.throw(_("ماژول پیش‌فاکتور (Quotation) در دسترس نیست."))

    so = frappe.get_doc("Sales Order", so_name)
    quotation = frappe.new_doc("Quotation")
    quotation.quotation_to = "Customer"
    quotation.party_name = so.customer
    quotation.customer_name = so.get("customer_name") or so.customer
    quotation.company = so.company
    quotation.transaction_date = today()
    quotation.currency = so.get("currency") or _get_currency(so.company)
    if so.get("selling_price_list"):
        quotation.selling_price_list = so.get("selling_price_list")
    for item in so.get("items") or []:
        line = {
            "item_code": item.get("item_code"),
            "item_name": item.get("item_name") or item.get("item_code"),
            "description": item.get("description") or item.get("item_name") or item.get("item_code"),
            "qty": flt(item.get("qty")),
            "uom": item.get("uom") or item.get("stock_uom") or "Nos",
            "rate": flt(item.get("rate")),
        }
        if item.get("income_account"):
            line["income_account"] = item.get("income_account")
        quotation.append("items", line)
    quotation.remarks = _("پیش‌فاکتور سفارش {0}").format(so_name)
    quotation.flags.ignore_permissions = True
    quotation.insert(ignore_permissions=True)
    frappe.db.commit()
    return {
        "status": "success",
        "quotation": quotation.name,
        "order": so_name,
        "grand_total": flt(quotation.grand_total),
        "print_url": "/printview?doctype=Quotation&name={}&trigger_print=1".format(quotation.name),
    }


def _resolve_pos_mode_of_payment(method):
    """Get mode of payment from DB that has a default account"""
    if not frappe.db.exists("DocType", "Mode of Payment"):
        return method
    all_modes = frappe.get_all("Mode of Payment", fields=["name", "type"], ignore_permissions=True)
    # Filter to only modes that have an account configured
    valid_modes = []
    for m in all_modes:
        accts = frappe.get_all("Mode of Payment Account",
            filters={"parent": m.name},
            fields=["default_account"],
            ignore_permissions=True, limit=1)
        if accts and accts[0].get("default_account"):
            valid_modes.append(m)
    if not valid_modes:
        valid_modes = all_modes
    # Try exact match first
    for m in valid_modes:
        if m.name.lower() == method.lower():
            return m.name
    # Try type match
    mode_type_map = {"cash": "Cash", "card": "Bank", "credit": "Credit", "bank": "Bank"}
    expected_type = mode_type_map.get(method)
    if expected_type:
        for m in valid_modes:
            if (m.type or "").strip() == expected_type:
                return m.name
    # First available
    if valid_modes:
        return valid_modes[0].name
    if all_modes:
        return all_modes[0].name
    return method


def _set_sales_order_payment_method(so_name, method):
    if _has_column("Sales Order", "restaurant_payment_method"):
        frappe.db.set_value(
            "Sales Order",
            so_name,
            "restaurant_payment_method",
            _normalize_payment_method(method),
            update_modified=False,
        )

@frappe.whitelist()
def settle_pos_order(order_name, payment=None, reference_no=None, rrn=None, commit=True):
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)
        
    # Check if order is already invoiced
    si = frappe.db.get_value("Sales Invoice Item", {"sales_order": so_name}, "parent")
    si_doc = None
    if si:
        si_doc = frappe.get_doc("Sales Invoice", si)
        if si_doc.docstatus == 1:
            if flt(si_doc.outstanding_amount) <= 0.1:
                return {
                    "sales_order": so_name,
                    "sales_invoice": si,
                    "status": "success",
                    "message": "Order is already fully paid."
                }
            
    payment = _parse_json(payment, {})
    method = _normalize_payment_method(payment.get("method") or "cash")
    splits = payment.get("splits") or []
    
    # If no splits provided but we have a method, create a single split
    if not splits:
        splits = [{
            "method": method,
            "mode_of_payment": payment.get("mode_of_payment") or _resolve_pos_mode_of_payment(method),
            "amount": 0, # Will be set to grand_total below
            "reference_no": (reference_no or payment.get("reference_no") or "").strip()
        }]
    for split in splits:
        split["method"] = _normalize_payment_method(split.get("method") or method)
    primary_method = splits[0].get("method") if splits else method
    credit_only = bool(splits) and all((split.get("method") or "") == "credit" for split in splits)

    result = {"sales_order": so_name}
    
    try:
        if not si_doc:
            make_si = frappe.get_attr("erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice")
            si_doc = make_si(so_name)
            if hasattr(si_doc, "as_dict"):
                si_doc.is_pos = 0 if credit_only else 1
                si_doc.update_stock = 0
            elif isinstance(si_doc, dict):
                si_doc["is_pos"] = 0 if credit_only else 1
                si_doc["update_stock"] = 0
                si_doc = frappe.get_doc(si_doc)
            else:
                si_doc = frappe.get_doc({"doctype": "Sales Invoice"})
                si_doc.is_pos = 0 if credit_only else 1
    
            grand_total = flt(getattr(si_doc, "grand_total", 0) or getattr(si_doc, "total", 0) or 0)
    
            # Fix amounts in splits if empty
            total_split = sum(flt(s.get("amount") or 0) for s in splits)
            if total_split <= 0:
                splits[0]["amount"] = grand_total
    
            # Validate splits total
            total_split = sum(flt(s.get("amount") or 0) for s in splits)
            if abs(total_split - grand_total) > 0.5: # Allow small rounding
                frappe.throw(f"Payment splits total ({total_split}) does not match invoice total ({grand_total})")
    
            # Add payments to SI
            if hasattr(si_doc, "payments"):
                si_doc.payments = []
            for s in splits:
                mop = s.get("mode_of_payment") or _resolve_pos_mode_of_payment(s.get("method") or "cash")
                if s.get("method") != "credit": # Don't add credit to SI payments table usually
                    si_doc.append("payments", {
                        "mode_of_payment": mop,
                        "amount": flt(s.get("amount")),
                    })
    
            si_doc.flags.ignore_permissions = True
            si_doc.insert()
            si_doc.submit()
            
        result["sales_invoice"] = si_doc.name

        # Create Payment Entries
        if si_doc.docstatus == 1:
            # Re-fetch outstanding amount
            si_outstanding = flt(frappe.db.get_value("Sales Invoice", si_doc.name, "outstanding_amount"))
            
            # In POS, Sales Invoice automatically creates Payment Entries for payments added to `si_doc.payments` during submit.
            # So if `si_doc.payments` had the full amount, `outstanding_amount` will be 0 right after submit().
            # If outstanding is 0, we don't need to create more Payment Entries, nor do we want to throw an error.
            if si_outstanding <= 0.5:
                # Already paid via SI submit
                splits = []
                total_split = 0
            else:
                # If we are processing a partial payment retry, validate the split total against current outstanding
                total_split = sum(flt(s.get("amount") or 0) for s in splits)
                
                if total_split <= 0 and si_outstanding > 0:
                    # Fallback to outstanding
                    splits = [{
                        "method": method,
                        "mode_of_payment": payment.get("mode_of_payment") or _resolve_pos_mode_of_payment(method),
                        "amount": si_outstanding,
                        "reference_no": (reference_no or payment.get("reference_no") or "").strip()
                    }]
                    total_split = si_outstanding
                    
                if total_split > si_outstanding + 0.5:
                    frappe.throw(f"Payment splits total ({total_split}) exceeds outstanding amount ({si_outstanding})")
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            payment_entries = []
            
            # Check existing Payment Entries to avoid duplicate on retry
            existing_pes = frappe.get_all("Payment Entry Reference",
                filters={"reference_name": si_doc.name, "docstatus": 1},
                fields=["parent", "allocated_amount"], ignore_permissions=True)
            
            existing_pe_docs = []
            if existing_pes:
                existing_pe_names = list({r.parent for r in existing_pes})
                existing_pe_docs = frappe.get_all("Payment Entry",
                    filters={"name": ["in", existing_pe_names], "docstatus": 1},
                    fields=["name", "mode_of_payment", "reference_no", "paid_amount"],
                    ignore_permissions=True)
                    
            for s in splits:
                if s.get("method") == "credit":
                    continue
                    
                mop = s.get("mode_of_payment") or _resolve_pos_mode_of_payment(s.get("method") or "cash")
                amt = flt(s.get("amount"))
                ref = str(s.get("reference_no") or si_doc.name)
                
                # Verify if this exact payment (mode + ref + amount) was already submitted
                is_duplicate = False
                for ex_pe in existing_pe_docs:
                    if (ex_pe.mode_of_payment == mop and 
                        (not ref or ex_pe.reference_no == ref or ex_pe.reference_no == si_doc.name) and 
                        abs(flt(ex_pe.paid_amount) - amt) < 0.1):
                        is_duplicate = True
                        payment_entries.append(ex_pe.name)
                        break
                        
                if is_duplicate:
                    continue
                
                pe = get_payment_entry("Sales Invoice", si_doc.name)
                pe.reference_no = ref
                pe.reference_date = today()
                pe.mode_of_payment = mop
                pe.paid_amount = amt
                pe.received_amount = amt
                # Clear references except this SI and adjust amount
                for r in pe.references:
                    if r.reference_name == si_doc.name:
                        r.allocated_amount = amt
                pe.flags.ignore_permissions = True
                pe.insert()
                pe.submit()
                payment_entries.append(pe.name)
                
            if payment_entries:
                result["payment_entries"] = payment_entries
                
            si_outstanding = flt(frappe.db.get_value("Sales Invoice", si_doc.name, "outstanding_amount"))
            if si_outstanding <= 0.1:
                frappe.db.set_value("Sales Invoice", si_doc.name, "status", "Paid", update_modified=False)
                current_restaurant_status = (
                    frappe.db.get_value("Sales Order", so_name, "restaurant_status")
                    if _has_column("Sales Order", "restaurant_status")
                    else ""
                ) or ""
                if current_restaurant_status.strip().lower() != "delivered":
                    _set_restaurant_order_status(so_name, "paid", force=True)
                _append_sales_order_note(so_name, "[SETTLE] Invoice created and payment recorded.")
            else:
                _append_sales_order_note(so_name, f"[SETTLE] Partially paid. Outstanding: {si_outstanding}")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Settle POS SI")
        frappe.throw(str(e))
        
    _set_sales_order_payment_method(so_name, primary_method)
    _save_management_pos_payment(
        so_name,
        {
            "method": primary_method,
            "provider": (payment.get("provider") or "manual").strip().lower() or "manual",
            "status": "paid" if flt(getattr(si_doc, "outstanding_amount", 0) or 0) <= 0.1 else "pending",
            "reference_no": (reference_no or payment.get("reference_no") or "").strip(),
            "rrn": (rrn or payment.get("rrn") or "").strip(),
            "provider_payload": payment.get("provider_payload") or {},
        },
        run_auto_flow=False,
    )

    # Customer club effects: wallet debit + cashback credit (idempotent).
    try:
        club_apply_settle_effects(so_name, splits, result.get("payment_breakdown") or result.get("payments"))
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Settle POS Club Effects")

    if commit:
        frappe.db.commit()
    return result


@frappe.whitelist()
def deliver_invoice_only(order_name):
    """فقط رسید تحویل بزن بدون تغییر وضعیت (فاکتور باز میمونه)"""
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)
    
    result = {"sales_order": so_name}
    try:
        auto_flow = _run_sales_order_auto_flow(
            so_name,
            trigger="manual",
            force=True,
            allow_negative_stock=True,
        )
        result["auto_flow"] = auto_flow
        dn_name = _create_delivery_note_for_sales_order(
            so_name,
            fg_warehouse_map=auto_flow.get("fg_warehouse_map") or {},
            submit_doc=True,
            allow_negative_stock=True,
        )
        if dn_name:
            result["delivery_note"] = dn_name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "DeliverInvoiceOnly DN")
        frappe.throw(_("Delivery Note creation failed."))
    
    _set_restaurant_order_status(so_name, "delivered", force=True)
    _append_sales_order_note(so_name, "[DELIVER_ONLY] Delivery Note created. Invoice remains open.")
    frappe.db.commit()
    return result

def _background_deliver_pos_order(so_name):
    frappe.db.commit()
    try:
        so_doc = frappe.get_doc("Sales Order", so_name)
        ticket_names = []
        if frappe.db.exists("DocType", "Restaurant Production Ticket"):
            ticket_names = frappe.get_all(
                "Restaurant Production Ticket",
                filters={"sales_order": so_name},
                pluck="name", ignore_permissions=True, order_by="creation asc"
            )
        if not ticket_names:
            cp = _create_production_for_sales_order(so_doc)
            ticket_names = cp.get("production_tickets") or []

        for ticket_name in ticket_names:
            if not frappe.db.exists("Restaurant Production Ticket", ticket_name):
                continue
            ticket = frappe.get_doc("Restaurant Production Ticket", ticket_name)
            wo_name = ticket.get("work_order") or ""
            if not wo_name or not frappe.db.exists("Work Order", wo_name):
                continue

            wo = frappe.get_doc("Work Order", wo_name)
            if wo.docstatus == 0:
                wo.flags.ignore_permissions = True
                wo.submit()
                wo = frappe.get_doc("Work Order", wo.name)

            if wo.docstatus != 1:
                continue

            pending_transfer = max(flt(wo.qty) - flt(wo.material_transferred_for_manufacturing), 0)
            if pending_transfer > 1e-8 and not cint(wo.skip_transfer):
                _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=True, allow_negative_stock=True)

            wo = frappe.get_doc("Work Order", wo.name)
            pending_manufacture = max(flt(wo.qty) - flt(wo.produced_qty), 0)
            if pending_manufacture > 1e-8:
                _create_work_order_stock_entry(wo.name, "Manufacture", pending_manufacture, submit_doc=True, allow_negative_stock=True)

            wo = frappe.get_doc("Work Order", wo.name)
            if hasattr(wo, "update_work_order_qty"):
                try: wo.update_work_order_qty()
                except: pass
            if hasattr(wo, "update_status"):
                try: wo.update_status()
                except: pass
            if flt(wo.produced_qty) >= flt(wo.qty) - 1e-8:
                if ticket.get("status") != "completed":
                    ticket.db_set("status", "completed", update_modified=False)

        try:
            _create_delivery_note_for_sales_order(so_name, submit_doc=True, allow_negative_stock=True)
        except Exception:
            pass

        _set_restaurant_order_status(so_name, "delivered", force=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Background Deliver POS Order Error")
        _append_sales_order_note(so_name, f"[ERROR] Delivery failed: {str(e)[:100]}")
        frappe.db.commit()

@frappe.whitelist()
def deliver_pos_order(order_name):
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)

    status = _core_order_status(frappe.get_doc("Sales Order", so_name))
    if status == "delivered":
        dn = frappe.db.get_value("Delivery Note Item", {"against_sales_order": so_name}, "parent")
        return {
            "sales_order": so_name,
            "status": "success",
            "delivery_note": dn or "",
            "message": "Order is already delivered."
        }

    result = {
        "sales_order": so_name,
        "status": "success",
        "delivery_note": "در حال صدور...",
    }
    
    # Set foreground status to preparing before background execution
    _set_restaurant_order_status(so_name, "preparing", force=True)
    frappe.db.commit()

    try:
        from frappe.utils.background_jobs import enqueue
        enqueue(
            "restaurant.api._background_deliver_pos_order",
            queue="short",
            so_name=so_name,
            now=frappe.flags.in_test
        )
    except Exception:
        _background_deliver_pos_order(so_name)

    return result

@frappe.whitelist()
def produce_and_deliver_pos_order(order_name):
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)

    status = _core_order_status(frappe.get_doc("Sales Order", so_name))
    if status == "delivered":
        dn = frappe.db.get_value("Delivery Note Item", {"against_sales_order": so_name}, "parent")
        return {
            "sales_order": so_name,
            "status": "success",
            "delivery_note": dn or "",
            "message": "Order is already delivered."
        }

    result = {
        "sales_order": so_name,
        "status": "success",
        "delivery_note": "در حال صدور...",
    }
    
    # Set foreground status to preparing before background execution
    _set_restaurant_order_status(so_name, "preparing", force=True)
    frappe.db.commit()

    try:
        from frappe.utils.background_jobs import enqueue
        enqueue(
            "restaurant.api._background_deliver_pos_order",
            queue="short",
            so_name=so_name,
            now=frappe.flags.in_test
        )
    except Exception:
        _background_deliver_pos_order(so_name)

    return result

@frappe.whitelist()

def _background_production_and_delivery(so_name):
    frappe.db.commit()
    try:
        so_doc = frappe.get_doc("Sales Order", so_name)
        # 1. Delivery Note
        dn_name = None
        try:
            dn_name = _create_delivery_note_for_sales_order(so_name, submit_doc=True, allow_negative_stock=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "CreateAndSettle DN Error Background")

        # 2. Production
        ticket_names = []
        if frappe.db.exists("DocType", "Restaurant Production Ticket"):
            ticket_names = frappe.get_all(
                "Restaurant Production Ticket", filters={"sales_order": so_name},
                pluck="name", ignore_permissions=True, order_by="creation asc"
            )
        if not ticket_names:
            cp = _create_production_for_sales_order(so_doc)
            ticket_names = cp.get("production_tickets") or []
            
        for ticket_name in ticket_names:
            if not frappe.db.exists("Restaurant Production Ticket", ticket_name):
                continue
            ticket = frappe.get_doc("Restaurant Production Ticket", ticket_name)
            wo_name = ticket.get("work_order") or ""
            if not wo_name or not frappe.db.exists("Work Order", wo_name):
                continue
            wo = frappe.get_doc("Work Order", wo_name)
            if wo.docstatus == 0:
                wo.flags.ignore_permissions = True
                wo.submit()
                wo = frappe.get_doc("Work Order", wo.name)
            if wo.docstatus != 1:
                continue
            pending_transfer = max(flt(wo.qty) - flt(wo.material_transferred_for_manufacturing), 0)
            if pending_transfer > 1e-8 and not cint(wo.skip_transfer):
                _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=True, allow_negative_stock=True)
            wo = frappe.get_doc("Work Order", wo.name)
            pending_mfg = max(flt(wo.qty) - flt(wo.produced_qty), 0)
            if pending_mfg > 1e-8:
                _create_work_order_stock_entry(wo.name, "Manufacture", pending_mfg, submit_doc=True, allow_negative_stock=True)
            wo = frappe.get_doc("Work Order", wo.name)
            if hasattr(wo, "update_work_order_qty"):
                try: wo.update_work_order_qty()
                except: pass
            if hasattr(wo, "update_status"):
                try: wo.update_status()
                except: pass
                
        # 3. Retry Delivery Note if it failed earlier
        if not dn_name:
            try:
                _create_delivery_note_for_sales_order(so_name, submit_doc=True, allow_negative_stock=True)
            except Exception:
                pass
                
        _set_restaurant_order_status(so_name, "delivered", force=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CreateAndSettle Background Production Error")
        _append_sales_order_note(so_name, f"[ERROR] Production failed: {str(e)[:100]}")
        frappe.db.commit()

@frappe.whitelist()
def create_and_settle_pos_order(payload):
    # تسویه و تحویل: SO + SI + Payment (Sync) -> Production + DN (Background)
    _ensure_management_access()
    payload = _parse_json(payload, {})
    if not isinstance(payload, dict):
        payload = {}

    # Keep the Sales Order and Sales Invoice in one transaction.  Production
    # and delivery remain outside the cashier's critical path below.
    order_result = _create_pos_order_payload(payload, commit=False)
    so_name = order_result.get("order_id", "")

    payment = payload.get("payment", {})
    settle_result = settle_pos_order(order_name=so_name, payment=payment, commit=False)

    # 3. Production + Delivery Note (Background)
    _set_restaurant_order_status(so_name, "preparing", force=True)
    frappe.db.commit()

    try:
        from frappe.utils.background_jobs import enqueue
        enqueue(
            "restaurant.api._background_production_and_delivery",
            queue="short",
            so_name=so_name,
            now=frappe.flags.in_test
        )
    except Exception:
        # Fallback to sync if enqueue fails
        _background_production_and_delivery(so_name)

    return {
        "status": "success",
        "order_id": so_name,
        "order_code": order_result.get("order_code", ""),
        "sales_invoice": settle_result.get("sales_invoice", ""),
        "delivery_note": "در حال صدور...",
    }

@frappe.whitelist()
def create_management_pos_order(payload):
	_ensure_management_access()
	payload = _parse_json(payload, {})
	if not isinstance(payload, dict):
		payload = {}

	customer_name = (payload.get("customer_name") or "POS Customer").strip()
	mobile = (payload.get("mobile") or "").strip()
	order_type = (payload.get("order_type") or "takeaway").strip()
	address = (payload.get("address") or "").strip()
	note = (payload.get("note") or "").strip()
	items = payload.get("items") or []
	payment = _parse_json(payload.get("payment"), {})

	result = place_order(
		customer_info={"name": customer_name, "mobile": mobile},
		order_type=order_type,
		items=items,
		address=address,
		note=note,
		include_service_items=1,
	)

	try:
		result["payment"] = _process_management_pos_payment(result, payment)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Management POS Payment Error")
		result["payment"] = {
			"method": _normalize_payment_method((payment or {}).get("method")),
			"provider": ((payment or {}).get("provider") or "manual").strip().lower() or "manual",
			"status": "failed",
			"reference_no": "",
			"rrn": "",
			"message": _("Order was created, but payment integration failed."),
			"provider_payload": {},
		}
@frappe.whitelist()
def confirm_management_pos_payment(
	order_name, status="paid", reference_no=None, rrn=None, provider_payload=None
):
	_ensure_management_access()

	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	existing_method = "card"
	if _has_column("Sales Order", "restaurant_payment_method"):
		existing_method = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_method") or "card"

	existing_provider = "manual"
	if _has_column("Sales Order", "restaurant_payment_provider"):
		existing_provider = (
			frappe.db.get_value("Sales Order", so_name, "restaurant_payment_provider") or "manual"
		)

	payment_result = {
		"method": _normalize_payment_method(existing_method),
		"provider": (existing_provider or "manual").strip().lower() or "manual",
		"status": _normalize_payment_status(status),
		"reference_no": (reference_no or "").strip(),
		"rrn": (rrn or "").strip(),
		"message": _("Payment status updated manually."),
		"provider_payload": _parse_json(provider_payload, {}),
	}

	automation_payload = _save_management_pos_payment(so_name, payment_result)
	_append_sales_order_note(so_name, f"[PAYMENT] {payment_result['message']} ({payment_result['status']})")

	frappe.db.commit()
	return {
		"status": "success",
		"order_name": so_name,
		"order_code": so_name,
		"payment": payment_result,
		"automation": automation_payload or {},
	}


def _manual_management_payment_result(
	so_name, status="paid", reference_no=None, rrn=None, provider_payload=None,
	payment_method=None, mode_of_payment=None,
):
	existing_method = "card"
	if _has_column("Sales Order", "restaurant_payment_method"):
		existing_method = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_method") or "card"

	existing_provider = "manual"
	if _has_column("Sales Order", "restaurant_payment_provider"):
		existing_provider = (
			frappe.db.get_value("Sales Order", so_name, "restaurant_payment_provider") or "manual"
		)

	method = _normalize_payment_method(payment_method or existing_method)
	selected_mode = str(mode_of_payment or _resolve_pos_mode_of_payment(method) or "").strip()
	return {
		"method": method,
		"mode_of_payment": selected_mode,
		"splits": [{
			"method": method,
			"mode_of_payment": selected_mode,
			"amount": 0,
			"reference_no": (reference_no or "").strip(),
		}],
		"provider": (existing_provider or "manual").strip().lower() or "manual",
		"status": _normalize_payment_status(status),
		"reference_no": (reference_no or "").strip(),
		"rrn": (rrn or "").strip(),
		"message": _("Payment status updated manually."),
		"provider_payload": _parse_json(provider_payload, {}),
	}


@frappe.whitelist()
def mark_management_order_paid(
	order_name, reference_no=None, rrn=None, provider_payload=None,
	payment_method=None, mode_of_payment=None,
):
	_ensure_management_access()

	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	payment_result = _manual_management_payment_result(
		so_name=so_name,
		status="paid",
		reference_no=reference_no,
		rrn=rrn,
		provider_payload=provider_payload,
		payment_method=payment_method,
		mode_of_payment=mode_of_payment,
	)
	settle_result = settle_pos_order(order_name=so_name, payment=payment_result)
	_append_sales_order_note(so_name, "[PAYMENT] پرداخت سفارش ثبت شد (paid)")

	frappe.db.commit()
	return {
		"status": "success",
		"order_name": so_name,
		"order_code": so_name,
		"sales_invoice": settle_result.get("sales_invoice", ""),
		"payment_entries": settle_result.get("payment_entries", []),
		"payment": payment_result,
		"restaurant_status": _core_order_status(frappe.get_doc("Sales Order", so_name)),
	}


@frappe.whitelist()
def complete_management_order(order_name, reference_no=None, rrn=None, provider_payload=None):
	_ensure_management_access()

	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	payment_result = _manual_management_payment_result(
		so_name=so_name,
		status="paid",
		reference_no=reference_no,
		rrn=rrn,
		provider_payload=provider_payload,
	)
	_save_management_pos_payment(so_name, payment_result, run_auto_flow=False)

	# Completing an order from management means paid + delivered regardless of workflow flags.
	_set_restaurant_order_status(so_name, "delivered", force=True)
	_append_sales_order_note(so_name, "[ORDER] سفارش تکمیل شد (paid + delivered)")

	frappe.db.commit()
	return {
		"status": "success",
		"order_name": so_name,
		"order_code": so_name,
		"payment": payment_result,
		"restaurant_status": _core_order_status(frappe.get_doc("Sales Order", so_name)),
	}


@frappe.whitelist()

@frappe.whitelist()
def purge_management_pos_order(order_name):
	_ensure_management_access()
	if not order_name:
		frappe.throw(_("Order name is required."))

	so_name = _resolve_sales_order_name(order_name)
	if not so_name or not frappe.db.exists("Sales Order", so_name):
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	summary = {
		"cleaned_records": {},
		"errors": []
	}

	def _cancel_and_delete(doctype, names):
		if not names:
			return
		if doctype not in summary["cleaned_records"]:
			summary["cleaned_records"][doctype] = []
		
		for name in set(names):
			if not frappe.db.exists(doctype, name):
				continue
			try:
				doc = frappe.get_doc(doctype, name)
				if doc.docstatus == 1:
					doc.flags.ignore_permissions = True
					doc.cancel()
				
				# Only delete if it's draft, or if it's a custom log (like POS Log / Ticket)
				# For core ERPNext documents, safe to delete draft, but CANCEL only if submitted.
				if doc.docstatus == 0 or doctype in ["Restaurant Production Ticket", "Restaurant POS Payment Log"]:
					frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
					summary["cleaned_records"][doctype].append(f"{name} (Deleted)")
				else:
					summary["cleaned_records"][doctype].append(f"{name} (Cancelled)")
			except Exception as e:
				summary["errors"].append(f"Failed to clean {doctype} {name}: {str(e)}")

	# 1. Gather dependent docs
	tickets = frappe.get_all("Restaurant Production Ticket", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Restaurant Production Ticket") else []
	
	wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Work Order") else []
	
	ses = []
	if wos and frappe.db.exists("DocType", "Stock Entry"):
		ses = frappe.get_all("Stock Entry", filters={"work_order": ["in", wos]}, pluck="name", ignore_permissions=True)
		
	dns = []
	if frappe.db.exists("DocType", "Delivery Note Item"):
		dn_items = frappe.get_all("Delivery Note Item", filters={"against_sales_order": so_name}, pluck="parent", ignore_permissions=True)
		dns = list(set(dn_items))
		
	sis = []
	if frappe.db.exists("DocType", "Sales Invoice Item"):
		si_items = frappe.get_all("Sales Invoice Item", filters={"sales_order": so_name}, pluck="parent", ignore_permissions=True)
		sis = list(set(si_items))
		
	pes = []
	if frappe.db.exists("DocType", "Payment Entry Reference"):
		refs = [{"reference_doctype": "Sales Order", "reference_name": so_name}]
		for si in sis:
			refs.append({"reference_doctype": "Sales Invoice", "reference_name": si})
			
		for ref in refs:
			pe_refs = frappe.get_all("Payment Entry Reference", filters=ref, pluck="parent", ignore_permissions=True)
			pes.extend(pe_refs)
		pes = list(set(pes))
		
	pos_logs = frappe.get_all("Restaurant POS Payment Log", filters={"sales_order": so_name}, pluck="name", ignore_permissions=True) if frappe.db.exists("DocType", "Restaurant POS Payment Log") else []

	# Cancel & Delete in dependency order
	_cancel_and_delete("Payment Entry", pes)
	_cancel_and_delete("Sales Invoice", sis)
	_cancel_and_delete("Delivery Note", dns)
	_cancel_and_delete("Stock Entry", ses)
	_cancel_and_delete("Work Order", wos)
	_cancel_and_delete("Restaurant Production Ticket", tickets)
	_cancel_and_delete("Restaurant POS Payment Log", pos_logs)

	if _has_column("Sales Order", "restaurant_status") and frappe.db.exists("Sales Order", so_name):
		frappe.db.set_value("Sales Order", so_name, "restaurant_status", "cancelled", update_modified=False)
	
	# Finally Sales Order
	_cancel_and_delete("Sales Order", [so_name])

	frappe.db.commit()
	if summary["errors"]:
		return {
			"status": "partial_success",
			"order_name": so_name,
			"summary": summary
		}

	return {
		"status": "success",
		"order_name": so_name,
		"summary": summary
	}


@frappe.whitelist()
def void_management_pos_order(order_name, reason=None):
	_ensure_management_access()
	if not order_name:
		frappe.throw(_("Order name is required."))

	so_name = order_name

	if not so_name or not frappe.db.exists("Sales Order", so_name):
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	has_status = _has_column("Sales Order", "restaurant_status")
	has_note = _has_column("Sales Order", "restaurant_note")
	doc = frappe.get_doc("Sales Order", so_name)
	if _core_order_status(doc) == "delivered":
		frappe.throw(_("Delivered orders cannot be voided."))

	reason_text = (reason or "").strip()
	if reason_text and has_note:
		existing_note = (doc.get("restaurant_note") or "").strip()
		doc.db_set("restaurant_note", f"{existing_note}\n[VOID] {reason_text}".strip(), update_modified=False)

	if doc.docstatus == 1:
		doc.flags.ignore_permissions = True
		doc.cancel()
	if has_status:
		frappe.db.set_value("Sales Order", doc.name, "restaurant_status", "cancelled", update_modified=False)

	frappe.db.commit()
	return {
		"status": "success",
		"order_name": doc.name,
		"order_code": doc.name,
		"state": "cancelled",
	}


@frappe.whitelist()
def list_management_pos_orders(date_from=None, date_to=None, status=None, cashier=None):
	_ensure_management_access()
	orders = _management_collect_orders(
		date_from=date_from,
		date_to=date_to,
		status=status,
		source="web",
		cashier=cashier,
	)
	return {"orders": orders}


@frappe.whitelist()
def list_management_orders(date_from=None, date_to=None, status=None, source=None, cashier=None):
	_ensure_management_access()
	orders = _management_collect_orders(
		date_from=date_from,
		date_to=date_to,
		status=status,
		source=source or "all",
		cashier=cashier,
	)
	return {"orders": orders}


@frappe.whitelist()
def get_management_order_detail(order_name, source=None):
	_ensure_management_access()
	if not order_name:
		frappe.throw(_("Order name is required."))

	source = (source or "").strip().lower()
	if source in {"", "web", "restaurant"}:
		so_name = None
		if frappe.db.exists("Sales Order", order_name):
			so_name = order_name


		if so_name:
			doc = frappe.get_doc("Sales Order", so_name)
			has_item_customization = _has_column("Sales Order Item", "restaurant_customization_json")
			sales_invoice_names = []
			outstanding_amount = flt(doc.grand_total or doc.total or doc.net_total)
			if frappe.db.exists("DocType", "Sales Invoice Item"):
				si_items = frappe.get_all(
					"Sales Invoice Item",
					filters={"sales_order": so_name, "docstatus": 1},
					fields=["parent"],
					ignore_permissions=True,
				)
				sales_invoice_names = sorted({row.parent for row in si_items if row.parent})
				if sales_invoice_names:
					si_docs = frappe.get_all(
						"Sales Invoice",
						filters={"name": ["in", sales_invoice_names]},
						fields=["name", "outstanding_amount"],
						ignore_permissions=True,
					)
					outstanding_amount = sum(flt(row.outstanding_amount) for row in si_docs)
			delivery_exists = False
			if frappe.db.exists("DocType", "Delivery Note Item"):
				delivery_exists = bool(
					frappe.db.exists(
						"Delivery Note Item",
						{"against_sales_order": so_name, "docstatus": 1},
					)
				)
			order_status = _core_order_status(doc)
			if delivery_exists:
				order_status = "delivered"
			order_context = _parse_json(doc.get("restaurant_order_context_json"), {})
			if not isinstance(order_context, dict):
				order_context = {}
			place_label = (
				order_context.get("place")
				or order_context.get("table")
				or doc.get("restaurant_table")
				or ""
			)
			items = []
			for row in doc.items or []:
				amount = row.get("amount")
				if amount in (None, ""):
					amount = row.get("base_amount")
				items.append(
					{
						"item_code": row.item_code or "",
						"title": row.item_name,
						"qty": flt(row.qty),
						"unit_price": flt(row.rate),
						"line_total": flt(
							amount if amount not in (None, "") else flt(row.rate) * flt(row.qty)
						),
						"customization_json": row.get("restaurant_customization_json")
						if has_item_customization
						else "",
						"note": row.get("restaurant_note") or "",
					}
				)

			return {
				"order": {
					"source": "web",
					"doctype": "Sales Order",
					"name": doc.name,
					"order_code": doc.name,
					"customer_name": doc.customer_name,
					"mobile": doc.get("restaurant_customer_mobile") or "",
					"channel": doc.get("restaurant_order_type") or "takeaway",
					"place": place_label,
					"order_context": order_context,
					"status": order_status,
					"subtotal": flt(doc.total or doc.net_total),
					"grand_total": flt(doc.grand_total or doc.total or doc.net_total),
					"outstanding_amount": flt(outstanding_amount),
					"has_sales_invoice": bool(sales_invoice_names),
					"sales_invoices": sales_invoice_names,
					"delivery_exists": delivery_exists,
					"discount_amount": flt(doc.get("discount_amount") or doc.get("additional_discount_amount") or 0),
					"tax_amount": sum([flt(t.tax_amount) for t in getattr(doc, "taxes", []) if "Tax" in t.description or "مالیات" in t.description]),
					"service_amount": sum([flt(t.tax_amount) for t in getattr(doc, "taxes", []) if "Service" in t.description or "سرویس" in t.description]),
					"tip_amount": sum([flt(t.tax_amount) for t in getattr(doc, "taxes", []) if "Tip" in t.description or "انعام" in t.description]),
					"created_at": _json_safe_datetime(
						_management_business_datetime(doc.get("transaction_date"), doc.creation)
						or doc.creation
					),
					"cashier": doc.owner,
					"note": _clean_automatic_pos_note(doc.get("restaurant_note") or ""),
					"payment_method": doc.get("restaurant_payment_method") or "",
					"payment_status": doc.get("restaurant_payment_status") or "",
					"payment_provider": doc.get("restaurant_payment_provider") or "",
					"payment_reference": doc.get("restaurant_payment_reference") or "",
					"courier": doc.get("restaurant_courier") or "",
					"payment_rrn": doc.get("restaurant_payment_rrn") or "",
					"items": items,
				}
			}

	if source in {"", "web", "restaurant"} and frappe.db.exists("Restaurant Order", order_name):
		doc = frappe.get_doc("Restaurant Order", order_name)
		items = [
			{
				"title": row.title_snapshot,
				"qty": flt(row.qty),
				"line_total": flt(row.line_total),
				"customization_json": row.customization_json or "",
			}
			for row in (doc.items or [])
		]
		return {
			"order": {
				"source": "web",
				"doctype": "Restaurant Order",
				"name": doc.name,
				"order_code": doc.order_code,
				"customer_name": doc.customer_name,
				"mobile": doc.mobile,
				"channel": doc.order_type,
				"status": doc.status,
				"subtotal": flt(doc.subtotal),
				"grand_total": flt(doc.grand_total),
				"created_at": _json_safe_datetime(doc.placed_at or doc.creation),
				"cashier": doc.owner,
				"note": doc.note or "",
				"items": items,
			}
		}

	if source in {"", "table"} and frappe.db.exists("Restaurant Table Order", order_name):
		doc = frappe.get_doc("Restaurant Table Order", order_name)
		menu_item_names = {row.menu_item for row in (doc.items or []) if row.menu_item}
		name_map = {}
		if menu_item_names and frappe.db.exists("DocType", "Restaurant Table Menu Item"):
			rows = frappe.get_all(
				"Restaurant Table Menu Item",
				fields=["name", "item_name"],
				filters={"name": ["in", list(menu_item_names)]},
				ignore_permissions=True,
			)
			name_map = {row.name: row.item_name for row in rows}
		items = [
			{
				"title": name_map.get(row.menu_item) or row.menu_item or "",
				"qty": flt(row.quantity),
				"line_total": flt(row.line_total),
				"customization_json": "",
			}
			for row in (doc.items or [])
		]
		table_number = frappe.db.get_value("Restaurant Table", doc.table, "table_number") or doc.table
		return {
			"order": {
				"source": "table",
				"doctype": "Restaurant Table Order",
				"name": doc.name,
				"order_code": doc.order_code,
				"customer_name": f"Table {table_number}",
				"mobile": "",
				"channel": "dine_in",
				"status": doc.status,
				"subtotal": flt(doc.subtotal),
				"grand_total": flt(doc.grand_total),
				"created_at": _json_safe_datetime(doc.created_at or doc.creation),
				"cashier": doc.owner,
				"note": doc.note or "",
				"items": items,
			}
		}

	frappe.throw(_("Order not found."), frappe.DoesNotExistError)


@frappe.whitelist()
def update_management_order(order_name, payment_method=None, note=None, customer_name=None, mobile=None):
	_ensure_management_access()
	if not order_name:
		frappe.throw(_("Order name is required."))

	so_name = _resolve_sales_order_name(order_name)
	if not so_name:
		frappe.throw(_("Order not found."), frappe.DoesNotExistError)

	updates = {}
	if payment_method is not None:
		normalized = _normalize_payment_method(payment_method)
		if _has_column("Sales Order", "restaurant_payment_method"):
			updates["restaurant_payment_method"] = normalized

	if note is not None:
		if _has_column("Sales Order", "restaurant_note"):
			updates["restaurant_note"] = (note or "").strip()

	if customer_name is not None:
		customer_text = (customer_name or "").strip()
		if customer_text:
			updates["customer_name"] = customer_text

	if mobile is not None:
		mobile_text = (mobile or "").strip()
		if _has_column("Sales Order", "restaurant_customer_mobile"):
			updates["restaurant_customer_mobile"] = mobile_text

	for field, value in updates.items():
		frappe.db.set_value("Sales Order", so_name, field, value, update_modified=False)

	_append_sales_order_note(so_name, "[EDIT] اطلاعات سفارش ویرایش شد")
	frappe.db.commit()

	return {
		"status": "success",
		"order_name": so_name,
		"order_code": so_name,
	}


@frappe.whitelist()
def create_management_return_order(order_name, reason=None):
    """ساخت فاکتور برگشتی کامل: SI برگشتی + DN برگشتی + کنسل WO (بدون SO جدید)"""
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))

    so_name = _resolve_sales_order_name(order_name)
    if not so_name:
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)

    doc = frappe.get_doc("Sales Order", so_name)
    status = _core_order_status(doc)

    if status not in ("paid", "delivered", "completed", "cancelled"):
        frappe.throw(_("فقط سفارش‌های پرداخت‌شده یا تحویل‌شده قابل برگشت هستند."))

    reason_text = (reason or "درخواست مشتری").strip()
    original_code = doc.name
    
    result = {
        "original_order_name": so_name,
        "original_order_code": original_code,
    }

    # 1. ساخت SI برگشتی از روی فاکتور فروش اصلی
    try:
        si_name = _existing_si_for_so(so_name)
        if si_name:
            return_si = _create_return_si(si_name, reason_text)
            if return_si:
                result["return_si"] = return_si
        else:
            result["return_si"] = "no_si_found"
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Return SI Creation")
        result["return_si_error"] = "SI creation failed"

    # 2. ساخت DN برگشتی از روی رسید تحویل اصلی
    try:
        dn_name = _existing_delivery_note_for_sales_order(so_name)
        if dn_name:
            return_dn = _create_return_dn(dn_name, reason_text)
            if return_dn:
                result["return_dn"] = return_dn
        else:
            result["return_dn"] = "no_dn_found"
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Return DN Creation")
        result["return_dn_error"] = "DN creation failed"

    # 3. کنسل کردن دستور کارهای فعال
    try:
        if frappe.db.exists("DocType", "Work Order"):
            wo_names = frappe.get_all("Work Order",
                filters={"sales_order": so_name, "docstatus": 1},
                pluck="name", ignore_permissions=True)
            for wo_name in wo_names:
                wo = frappe.get_doc("Work Order", wo_name)
                se_names = frappe.get_all("Stock Entry",
                    filters={"work_order": wo_name, "docstatus": 1},
                    pluck="name", ignore_permissions=True)
                for se_name in se_names:
                    se = frappe.get_doc("Stock Entry", se_name)
                    se.flags.ignore_permissions = True
                    se.cancel()
                wo.flags.ignore_permissions = True
                wo.cancel()
            result["cancelled_work_orders"] = wo_names
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Return Cancel WO")
        result["wo_cancel_error"] = "Work Order cancellation failed"

    # 4. کنسل کردن سفارش فروش اصلی
    if doc.docstatus == 1:
        try:
            doc.flags.ignore_permissions = True
            doc.cancel()
            result["cancelled_so"] = so_name
        except Exception:
            frappe.log_error(frappe.get_traceback(), "Return Cancel SO")
            result["so_cancel_error"] = "SO cancellation failed"

    if _has_column("Sales Order", "restaurant_status"):
        frappe.db.set_value("Sales Order", so_name, "restaurant_status", "cancelled", update_modified=False)

    _append_sales_order_note(so_name, f"[RETURN] برگشت کامل انجام شد. {reason_text}")
    frappe.db.commit()

    result.update({
        "status": "success",
        "customer_name": doc.customer_name,
        "grand_total": flt(doc.grand_total or doc.total or 0),
    })
    return result

def _management_resolve_item_name(item_name):
	raw_value = (item_name or "").strip()
	if not raw_value:
		frappe.throw(_("Item name is required."))

	if frappe.db.exists("Item", raw_value):
		return raw_value

	by_code = frappe.db.get_value("Item", {"item_code": raw_value}, "name")
	if by_code:
		return by_code

	by_title = frappe.db.get_value("Item", {"item_name": raw_value}, "name")
	if by_title:
		return by_title

	if _has_column("Item", "restaurant_slug"):
		slug_match = frappe.db.get_value("Item", {"restaurant_slug": _normalize_slug(raw_value)}, "name")
		if slug_match:
			return slug_match

	frappe.throw(_("Item not found."), frappe.DoesNotExistError)


def _management_collect_item_media(item_doc, image_field):
	urls = []
	seed_urls = [
		getattr(item_doc, image_field, ""),
		item_doc.get("website_image"),
		item_doc.get("image"),
	]
	for url in seed_urls:
		normalized = (url or "").strip()
		if normalized:
			urls.append(normalized)

	if frappe.db.exists("DocType", "File"):
		attached = frappe.get_all(
			"File",
			fields=["file_url", "is_private", "creation"],
			filters={
				"attached_to_doctype": "Item",
				"attached_to_name": item_doc.name,
				"is_folder": 0,
			},
			order_by="creation asc",
			ignore_permissions=True,
		)
		for row in attached:
			file_url = (row.get("file_url") or "").strip()
			if not file_url:
				continue
			if row.get("is_private"):
				continue
			urls.append(file_url)

	seen = set()
	deduplicated = []
	for url in urls:
		if url in seen:
			continue
		seen.add(url)
		deduplicated.append(url)

	return {
		"main_image": deduplicated[0] if deduplicated else "",
		"gallery": deduplicated,
	}


def _management_product_field_options():
	options = {
		"uoms": [],
		"item_groups": [],
		"categories": [],
		"subcategories": [],
		"branches": [],
		"item_attributes": [],
		"kitchen_print_modes": [
			{"value": "parent_only", "label": _("Only parent item")},
			{"value": "parent_with_components", "label": _("Parent with selected components")},
			{"value": "components_grouped_by_step", "label": _("Components grouped by builder step")},
		],
		"stock_consumption_modes": [
			{"value": "no_stock_deduction", "label": _("No stock deduction")},
			{"value": "consume_selected_components", "label": _("Consume selected components")},
			{"value": "create_dynamic_bom", "label": _("Create dynamic BOM preview")},
			{
				"value": "use_sales_order_exploded_components",
				"label": _("Use sales order exploded components"),
			},
			{"value": "manual_kitchen_consumption", "label": _("Manual kitchen consumption")},
		],
	}

	if frappe.db.exists("DocType", "UOM"):
		uom_rows = frappe.get_all(
			"UOM",
			fields=["name", "uom_name"],
			order_by="uom_name asc",
			ignore_permissions=True,
		)
		options["uoms"] = [
			{
				"value": row.name,
				"label": row.uom_name or row.name,
			}
			for row in uom_rows
		]

	if frappe.db.exists("DocType", "Item Group"):
		group_filters = {}
		if _has_column("Item Group", "is_group"):
			group_filters["is_group"] = 0
		group_rows = frappe.get_all(
			"Item Group",
			fields=["name", "item_group_name"],
			filters=group_filters,
			order_by="item_group_name asc",
			ignore_permissions=True,
		)
		options["item_groups"] = [
			{
				"value": row.name,
				"label": row.item_group_name or row.name,
			}
			for row in group_rows
		]

		category_rows = frappe.get_all(
			"Item Group",
			fields=["name", "item_group_name", "restaurant_slug", "restaurant_sort_order"],
			filters=_core_category_filters(is_subcategory=0),
			order_by="restaurant_sort_order asc, item_group_name asc",
			ignore_permissions=True,
		)
		options["categories"] = [
			{
				"value": row.name,
				"label": row.item_group_name or row.name,
				"slug": row.restaurant_slug or "",
			}
			for row in category_rows
		]

		category_name_set = {row.name for row in category_rows}
		subcategory_fields = [
			"name",
			"item_group_name",
			"restaurant_slug",
			"parent_item_group",
			"restaurant_sort_order",
			"is_group",
		]
		has_subcategory_flag = _has_column("Item Group", "restaurant_is_subcategory")
		if has_subcategory_flag:
			subcategory_fields.append("restaurant_is_subcategory")
		if _has_column("Item Group", "restaurant_is_menu_category"):
			subcategory_fields.append("restaurant_is_menu_category")

		subcategory_filters = {}
		if _has_column("Item Group", "restaurant_active"):
			subcategory_filters["restaurant_active"] = 1
		if _has_column("Item Group", "is_group"):
			subcategory_filters["is_group"] = 0

		subcategory_rows = frappe.get_all(
			"Item Group",
			fields=subcategory_fields,
			filters=subcategory_filters,
			order_by="restaurant_sort_order asc, item_group_name asc",
			ignore_permissions=True,
		)
		options["subcategories"] = [
			{
				"value": row.name,
				"label": row.item_group_name or row.name,
				"slug": row.restaurant_slug or "",
				"category": row.parent_item_group or "",
			}
			for row in subcategory_rows
			if (cint(row.get("restaurant_is_subcategory") or 0) == 1 if has_subcategory_flag else False)
			or ((row.parent_item_group or "") in category_name_set and cint(row.get("is_group") or 0) != 1)
		]

	if _has_column("Item", "restaurant_branch"):
		branch_rows = frappe.db.sql(
			"""
            select distinct restaurant_branch
            from `tabItem`
            where ifnull(restaurant_branch, '') != ''
            order by restaurant_branch asc
            """,
			as_dict=True,
		)
		options["branches"] = [
			{
				"value": row.get("restaurant_branch"),
				"label": row.get("restaurant_branch"),
			}
			for row in branch_rows
			if row.get("restaurant_branch")
		]

	if frappe.db.exists("DocType", "Item Attribute"):
		attribute_fields = [
			"name",
			"attribute_name",
			"numeric_values",
			"disabled",
			"from_range",
			"to_range",
			"increment",
		]
		if _has_column("Item Attribute", "restaurant_show_in_website"):
			attribute_fields.append("restaurant_show_in_website")
		if _has_column("Item Attribute", "restaurant_selection_only"):
			attribute_fields.append("restaurant_selection_only")

		attribute_rows = frappe.get_all(
			"Item Attribute",
			fields=attribute_fields,
			order_by="attribute_name asc",
			ignore_permissions=True,
			limit_page_length=1000,
		)

		value_has_default = _has_column("Item Attribute Value", "restaurant_is_default")
		for attribute_row in attribute_rows:
			attribute_name = (attribute_row.get("name") or "").strip()
			if not attribute_name:
				continue

			value_fields = ["attribute_value", "abbr", "idx"]
			if value_has_default:
				value_fields.append("restaurant_is_default")
			value_rows = frappe.get_all(
				"Item Attribute Value",
				filters={"parent": attribute_name},
				fields=value_fields,
				order_by="idx asc",
				ignore_permissions=True,
				limit_page_length=1000,
			)
			values_payload = []
			for value_row in value_rows:
				value_name = (value_row.get("attribute_value") or "").strip()
				if not value_name:
					continue
				is_default = cint(value_row.get("restaurant_is_default") or 0) if value_has_default else 0
				values_payload.append(
					{
						"value": value_name,
						"abbr": (value_row.get("abbr") or "").strip(),
						"sort_order": cint(value_row.get("idx") or 0),
						"is_default": is_default,
					}
				)

			options["item_attributes"].append(
				{
					"name": attribute_name,
					"label": (attribute_row.get("attribute_name") or attribute_name).strip(),
					"numeric_values": cint(attribute_row.get("numeric_values") or 0),
					"disabled": cint(attribute_row.get("disabled") or 0),
					"from_range": flt(attribute_row.get("from_range") or 0),
					"to_range": flt(attribute_row.get("to_range") or 0),
					"increment": flt(attribute_row.get("increment") or 0),
					"show_in_website": 1
					if attribute_row.get("restaurant_show_in_website") in ("", None)
					else cint(attribute_row.get("restaurant_show_in_website") or 0),
					"selection_only": cint(attribute_row.get("restaurant_selection_only") or 0),
					"values": values_payload,
				}
			)

	return options


def _normalize_management_select_value(
	value,
	*,
	valid_options,
	alias_map=None,
	default="",
	fallback_to_default=False,
):
	raw_value = (value or "").strip()
	if not raw_value:
		return default if fallback_to_default else ""

	canonical = raw_value.lower()
	if alias_map and canonical in alias_map:
		return alias_map[canonical]

	if raw_value in valid_options:
		return raw_value

	return default if fallback_to_default else raw_value


def _normalize_management_kitchen_print_mode(value, fallback_to_default=False):
	return _normalize_management_select_value(
		value,
		valid_options=MANAGEMENT_KITCHEN_PRINT_MODES,
		alias_map=MANAGEMENT_KITCHEN_PRINT_MODE_ALIASES,
		default=MANAGEMENT_KITCHEN_PRINT_MODE_DEFAULT,
		fallback_to_default=fallback_to_default,
	)


def _normalize_management_stock_consumption_mode(value, fallback_to_default=False):
	return _normalize_management_select_value(
		value,
		valid_options=MANAGEMENT_STOCK_CONSUMPTION_MODES,
		alias_map=MANAGEMENT_STOCK_CONSUMPTION_MODE_ALIASES,
		default=MANAGEMENT_STOCK_CONSUMPTION_MODE_DEFAULT,
		fallback_to_default=fallback_to_default,
	)


def normalize_item_builder_modes(doc, method=None):
	if not doc or getattr(doc, "doctype", "") != "Item":
		return

	if _has_column("Item", "restaurant_kitchen_print_mode"):
		doc.restaurant_kitchen_print_mode = _normalize_management_kitchen_print_mode(
			doc.get("restaurant_kitchen_print_mode"),
			fallback_to_default=True,
		)

	if _has_column("Item", "restaurant_stock_consumption_mode"):
		doc.restaurant_stock_consumption_mode = _normalize_management_stock_consumption_mode(
			doc.get("restaurant_stock_consumption_mode"),
			fallback_to_default=True,
		)


def _management_item_attribute_payload(attribute_doc, include_values=True):
	has_show = _has_column("Item Attribute", "restaurant_show_in_website")
	has_selection_only = _has_column("Item Attribute", "restaurant_selection_only")
	has_default = _has_column("Item Attribute Value", "restaurant_is_default")

	payload = {
		"name": (attribute_doc.get("name") or "").strip(),
		"label": (attribute_doc.get("attribute_name") or attribute_doc.get("name") or "").strip(),
		"numeric_values": cint(attribute_doc.get("numeric_values") or 0),
		"disabled": cint(attribute_doc.get("disabled") or 0),
		"from_range": flt(attribute_doc.get("from_range") or 0),
		"to_range": flt(attribute_doc.get("to_range") or 0),
		"increment": flt(attribute_doc.get("increment") or 0),
		"show_in_website": 1
		if not has_show or attribute_doc.get("restaurant_show_in_website") in ("", None)
		else cint(attribute_doc.get("restaurant_show_in_website") or 0),
		"selection_only": 0
		if not has_selection_only
		else cint(attribute_doc.get("restaurant_selection_only") or 0),
		"value_count": 0,
		"values": [],
	}

	if not include_values:
		payload["value_count"] = cint(
			frappe.db.count(
				"Item Attribute Value",
				{"parent": payload["name"]},
			)
			or 0
		)
		return payload

	rows = attribute_doc.get("item_attribute_values") or []
	values = []
	for row in rows:
		value_name = (row.get("attribute_value") or "").strip()
		if not value_name:
			continue
		values.append(
			{
				"value": value_name,
				"abbr": (row.get("abbr") or "").strip(),
				"sort_order": cint(row.get("idx") or 0),
				"is_default": cint(row.get("restaurant_is_default") or 0) if has_default else 0,
			}
		)

	payload["values"] = values
	payload["value_count"] = len(values)
	return payload


@frappe.whitelist()
def list_management_item_attributes(search=None, include_values=0):
	_ensure_management_access()
	include_values = cint(include_values or 0)
	normalized_search = str(search or "").strip()

	if not frappe.db.exists("DocType", "Item Attribute"):
		return {"rows": []}

	filters = {}
	or_filters = None
	if normalized_search:
		like_pattern = f"%{normalized_search}%"
		or_filters = [["name", "like", like_pattern], ["attribute_name", "like", like_pattern]]

	rows = frappe.get_all(
		"Item Attribute",
		fields=["name"],
		filters=filters,
		or_filters=or_filters,
		order_by="attribute_name asc",
		ignore_permissions=True,
		limit_page_length=1000,
	)

	payload_rows = []
	for row in rows:
		attribute_name = (row.get("name") or "").strip()
		if not attribute_name:
			continue
		payload_rows.append(
			_management_item_attribute_payload(
				frappe.get_doc("Item Attribute", attribute_name),
				include_values=bool(include_values),
			)
		)

	return {"rows": payload_rows}


@frappe.whitelist()
def get_management_item_attribute(attribute_name=None):
	_ensure_management_access()
	normalized_name = str(attribute_name or "").strip()
	if not normalized_name:
		frappe.throw(_("Item Attribute is required."))
	if not frappe.db.exists("Item Attribute", normalized_name):
		frappe.throw(_("Item Attribute not found: {0}").format(normalized_name), frappe.DoesNotExistError)
	return _management_item_attribute_payload(
		frappe.get_doc("Item Attribute", normalized_name),
		include_values=True,
	)


@frappe.whitelist()
def save_management_item_attribute(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	attribute_name = str(parsed_payload.get("name") or "").strip()
	if not attribute_name:
		frappe.throw(_("Item Attribute is required."))
	if not frappe.db.exists("Item Attribute", attribute_name):
		frappe.throw(_("Item Attribute not found: {0}").format(attribute_name), frappe.DoesNotExistError)

	attribute_doc = frappe.get_doc("Item Attribute", attribute_name)

	numeric_values = cint(parsed_payload.get("numeric_values") or 0)
	attribute_doc.set("numeric_values", numeric_values)
	attribute_doc.set("disabled", cint(parsed_payload.get("disabled") or 0))
	attribute_doc.set("from_range", flt(parsed_payload.get("from_range") or 0))
	attribute_doc.set("to_range", flt(parsed_payload.get("to_range") or 0))
	attribute_doc.set("increment", flt(parsed_payload.get("increment") or 0))

	if _has_column("Item Attribute", "restaurant_show_in_website") and "show_in_website" in parsed_payload:
		attribute_doc.set("restaurant_show_in_website", cint(parsed_payload.get("show_in_website") or 0))
	if _has_column("Item Attribute", "restaurant_selection_only") and "selection_only" in parsed_payload:
		attribute_doc.set("restaurant_selection_only", cint(parsed_payload.get("selection_only") or 0))

	has_default = _has_column("Item Attribute Value", "restaurant_is_default")
	normalized_values = []
	seen_values = set()
	default_value = ""
	for row in parsed_payload.get("values") or []:
		value_name = str((row or {}).get("value") or "").strip()
		if not value_name or value_name in seen_values:
			continue
		seen_values.add(value_name)

		abbr_value = str((row or {}).get("abbr") or "").strip() or value_name
		is_default = cint((row or {}).get("is_default") or 0)
		if is_default and not default_value:
			default_value = value_name
		normalized_values.append(
			{
				"attribute_value": value_name,
				"abbr": abbr_value,
			}
		)

	if not numeric_values and not normalized_values:
		frappe.throw(_("At least one value is required for non-numeric Item Attribute."))

	if numeric_values:
		attribute_doc.set("item_attribute_values", [])
	else:
		attribute_doc.set("item_attribute_values", [])
		for row in normalized_values:
			attribute_doc.append("item_attribute_values", row)

	attribute_doc.save(ignore_permissions=True)

	if has_default and not numeric_values:
		for child in attribute_doc.get("item_attribute_values") or []:
			is_default = (
				1 if default_value and (child.get("attribute_value") or "").strip() == default_value else 0
			)
			frappe.db.set_value(
				"Item Attribute Value",
				child.name,
				"restaurant_is_default",
				is_default,
				update_modified=False,
			)

	frappe.db.commit()
	return _management_item_attribute_payload(attribute_doc, include_values=True)


def _management_slugify_value(value):
	raw = str(value or "").strip().lower()
	if not raw:
		return ""
	raw = re.sub(r"\s+", "-", raw)
	raw = re.sub(r"[^0-9a-z\u0600-\u06FF-]+", "-", raw)
	raw = re.sub(r"-{2,}", "-", raw)
	return raw.strip("-")


def _management_unique_item_slug(base_slug, item_name=""):
	normalized = _management_slugify_value(base_slug)
	if not normalized:
		return ""

	item_name = (item_name or "").strip()
	candidate = normalized
	index = 2
	while True:
		existing = frappe.db.get_value("Item", {"restaurant_slug": candidate}, "name")
		if not existing or (item_name and existing == item_name):
			return candidate
		candidate = f"{normalized}-{index}"
		index += 1


def _management_resolve_template_doc(item_name):
	resolved_name = _management_resolve_item_name(item_name)
	item_doc = frappe.get_doc("Item", resolved_name)
	variant_of = (item_doc.get("variant_of") or "").strip()
	if variant_of:
		return frappe.get_doc("Item", variant_of)
	return item_doc


def _management_template_attribute_names(template_doc):
	return [
		(row.get("attribute") or "").strip()
		for row in (template_doc.get("attributes") or [])
		if (row.get("attribute") or "").strip()
	]


def _management_template_variants_payload(template_doc):
	if not _has_column("Item", "variant_of"):
		return []

	has_restaurant_slug = _has_column("Item", "restaurant_slug")
	has_restaurant_enabled = _has_column("Item", "restaurant_enabled")
	has_show_in_website = _has_column("Item", "show_in_website")
	has_restaurant_base_price = _has_column("Item", "restaurant_base_price")

	fields = ["name", "item_code", "item_name", "disabled", "standard_rate"]
	if has_restaurant_slug:
		fields.append("restaurant_slug")
	if has_restaurant_enabled:
		fields.append("restaurant_enabled")
	if has_show_in_website:
		fields.append("show_in_website")
	if has_restaurant_base_price:
		fields.append("restaurant_base_price")

	rows = frappe.get_all(
		"Item",
		filters={"variant_of": template_doc.name},
		fields=fields,
		order_by="item_name asc",
		ignore_permissions=True,
		limit_page_length=1000,
	)

	payload = []
	for row in rows:
		variant_name = (row.get("name") or "").strip()
		attribute_rows = []
		for attr_row in _item_variant_attribute_rows(variant_name):
			attribute_name = (attr_row.get("attribute") or "").strip()
			attribute_value = (attr_row.get("attribute_value") or "").strip()
			if attribute_name and attribute_value:
				attribute_rows.append({"attribute": attribute_name, "value": attribute_value})
		payload.append(
			{
				"name": variant_name,
				"item_code": row.get("item_code") or variant_name,
				"item_name": row.get("item_name") or variant_name,
				"slug": row.get("restaurant_slug") or "",
				"is_active": cint(row.get("restaurant_enabled") or 0)
				if has_restaurant_enabled
				else (0 if cint(row.get("disabled") or 0) else 1),
				"is_disabled": cint(row.get("disabled") or 0),
				"show_in_website": cint(row.get("show_in_website") or 0) if has_show_in_website else 1,
				"base_price": _get_default_item_price_rate(row) if _get_default_item_price_rate(row) is not None else (flt(row.get("restaurant_base_price") or row.get("standard_rate") or 0) if has_restaurant_base_price else flt(row.get("standard_rate") or 0)),
				"attributes": attribute_rows,
			}
		)
	return payload


def _management_template_display_summary(template_doc):
	rows = _template_display_variants(template_doc)
	payload = []
	for row in rows:
		payload.append(
			{
				"name": row.get("name"),
				"title": row.get("item_name"),
				"slug": row.get("restaurant_slug"),
				"fixed_attributes": row.get("variant_fixed_attributes") or {},
			}
		)

	if payload:
		return payload

	return [
		{
			"name": template_doc.name,
			"title": template_doc.item_name or template_doc.name,
			"slug": template_doc.get("restaurant_slug") or "",
			"fixed_attributes": {},
		}
	]


@frappe.whitelist()
def get_management_product_variant_builder(item_name=None):
	_ensure_management_access()
	normalized_item_name = (item_name or "").strip()
	if not normalized_item_name:
		frappe.throw(_("Item is required."))

	template_doc = _management_resolve_template_doc(normalized_item_name)
	if (
		cint(template_doc.get("has_variants") or 0)
		and (template_doc.get("variant_based_on") or "") != "Item Attribute"
	):
		frappe.throw(_("Only Item Attribute based variants are supported here."))

	field_options = _management_product_field_options()
	available_attributes = field_options.get("item_attributes") or []
	selected_attribute_names = set(_management_template_attribute_names(template_doc))

	attributes_payload = []
	for row in available_attributes:
		attr_name = (row.get("name") or "").strip()
		if not attr_name:
			continue
		payload = dict(row)
		payload["selected_on_template"] = 1 if attr_name in selected_attribute_names else 0
		attributes_payload.append(payload)

	attributes_payload = sorted(
		attributes_payload,
		key=lambda row: (
			0 if cint(row.get("selected_on_template") or 0) else 1,
			cint(row.get("disabled") or 0),
			(row.get("label") or row.get("name") or ""),
		),
	)

	return {
		"template": {
			"name": template_doc.name,
			"item_code": template_doc.item_code,
			"item_name": template_doc.item_name,
			"has_variants": cint(template_doc.get("has_variants") or 0),
			"variant_based_on": template_doc.get("variant_based_on") or "",
			"restaurant_slug": template_doc.get("restaurant_slug") or "",
		},
		"attributes": attributes_payload,
		"template_attributes": list(selected_attribute_names),
		"variants": _management_template_variants_payload(template_doc),
		"menu_display": _management_template_display_summary(template_doc),
	}


def _management_apply_template_attributes(template_doc, selected_attribute_names):
	normalized = []
	seen = set()
	for attr_name in selected_attribute_names or []:
		key = str(attr_name or "").strip()
		if not key or key in seen:
			continue
		if not frappe.db.exists("Item Attribute", key):
			frappe.throw(_("Item Attribute not found: {0}").format(key), frappe.DoesNotExistError)
		seen.add(key)
		normalized.append(key)

	if not normalized:
		frappe.throw(_("At least one Item Attribute must be selected for variants."))

	existing_rows = {
		str(row.get("attribute") or "").strip(): row for row in (template_doc.get("attributes") or [])
	}

	replacement_rows = []
	for attr_name in normalized:
		existing = existing_rows.get(attr_name)
		numeric_values = cint(frappe.db.get_value("Item Attribute", attr_name, "numeric_values") or 0)
		disabled = cint(frappe.db.get_value("Item Attribute", attr_name, "disabled") or 0)
		replacement_rows.append(
			{
				"attribute": attr_name,
				"attribute_value": ""
				if numeric_values
				else (existing.get("attribute_value") if existing else ""),
				"numeric_values": numeric_values,
				"from_range": flt(existing.get("from_range") if existing else 0),
				"to_range": flt(existing.get("to_range") if existing else 0),
				"increment": flt(existing.get("increment") if existing else 0),
				"disabled": disabled,
			}
		)

	template_doc.set("has_variants", 1)
	template_doc.set("variant_based_on", "Item Attribute")
	template_doc.set("attributes", replacement_rows)
	return normalized


def _management_apply_attribute_settings(attribute_settings):
	if not isinstance(attribute_settings, list):
		return

	has_show = _has_column("Item Attribute", "restaurant_show_in_website")
	has_selection_only = _has_column("Item Attribute", "restaurant_selection_only")
	has_default = _has_column("Item Attribute Value", "restaurant_is_default")

	for row in attribute_settings:
		attribute_name = str((row or {}).get("name") or "").strip()
		if not attribute_name or not frappe.db.exists("Item Attribute", attribute_name):
			continue

		updates = {}
		if has_show and "show_in_website" in row:
			updates["restaurant_show_in_website"] = cint(row.get("show_in_website"))
		if has_selection_only and "selection_only" in row:
			updates["restaurant_selection_only"] = cint(row.get("selection_only"))
		if updates:
			frappe.db.set_value("Item Attribute", attribute_name, updates, update_modified=True)

		value_settings = row.get("values")
		if not isinstance(value_settings, list):
			continue

		default_value = ""
		for value_row in value_settings:
			value_name = str((value_row or {}).get("value") or "").strip()
			if not value_name:
				continue
			if cint((value_row or {}).get("is_default") or 0):
				default_value = value_name
				break

		attribute_doc = frappe.get_doc("Item Attribute", attribute_name)
		value_map = {
			(child.get("attribute_value") or "").strip(): child
			for child in (attribute_doc.get("item_attribute_values") or [])
		}
		changed = False
		for value_row in value_settings:
			value_name = str((value_row or {}).get("value") or "").strip()
			if not value_name:
				continue
			abbr_value = str((value_row or {}).get("abbr") or "").strip()

			child = value_map.get(value_name)
			if not child:
				child = attribute_doc.append(
					"item_attribute_values",
					{"attribute_value": value_name, "abbr": abbr_value or value_name},
				)
				value_map[value_name] = child
				changed = True
			elif abbr_value and (child.get("abbr") or "").strip() != abbr_value:
				child.set("abbr", abbr_value)
				changed = True

		if changed:
			attribute_doc.save(ignore_permissions=True)

		if has_default:
			for value_name in value_map.keys():
				is_default = 1 if default_value and value_name == default_value else 0
				frappe.db.set_value(
					"Item Attribute Value",
					{"parent": attribute_name, "attribute_value": value_name},
					"restaurant_is_default",
					is_default,
					update_modified=False,
				)


@frappe.whitelist()
def save_management_product_variant_builder(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	template_doc = _management_resolve_template_doc(
		parsed_payload.get("item_name") or parsed_payload.get("template_name")
	)
	selected_attributes = parsed_payload.get("selected_attributes") or []
	_management_apply_template_attributes(template_doc, selected_attributes)
	_management_apply_attribute_settings(parsed_payload.get("attribute_settings"))

	template_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_management_product_variant_builder(template_doc.name)


@frappe.whitelist()
def generate_management_product_variants(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	template_doc = _management_resolve_template_doc(
		parsed_payload.get("item_name") or parsed_payload.get("template_name")
	)
	selected_attributes = parsed_payload.get("selected_attributes") or _management_template_attribute_names(
		template_doc
	)
	normalized_attributes = _management_apply_template_attributes(template_doc, selected_attributes)

	selected_values = parsed_payload.get("selected_values_by_attribute") or {}
	if not isinstance(selected_values, dict):
		selected_values = {}

	values_by_attribute = {}
	for attribute_name in normalized_attributes:
		raw_values = selected_values.get(attribute_name) or []
		if isinstance(raw_values, str):
			raw_values = [raw_values]
		elif not isinstance(raw_values, (list, tuple, set)):
			raw_values = [raw_values]

		normalized_values = []
		seen_values = set()
		missing_values = []
		for value in raw_values:
			value_name = str(value or "").strip()
			if not value_name or value_name in seen_values:
				continue
			if not frappe.db.exists(
				"Item Attribute Value", {"parent": attribute_name, "attribute_value": value_name}
			):
				missing_values.append(value_name)
			normalized_values.append(value_name)
			seen_values.add(value_name)

		if missing_values:
			attribute_doc = frappe.get_doc("Item Attribute", attribute_name)
			value_map = {
				(child.get("attribute_value") or "").strip(): child
				for child in (attribute_doc.get("item_attribute_values") or [])
			}
			changed = False
			for value_name in missing_values:
				if value_name in value_map:
					continue
				attribute_doc.append(
					"item_attribute_values",
					{"attribute_value": value_name, "abbr": value_name},
				)
				changed = True
			if changed:
				attribute_doc.save(ignore_permissions=True)

		if not normalized_values:
			rows = frappe.get_all(
				"Item Attribute Value",
				filters={"parent": attribute_name},
				fields=["attribute_value", "idx"],
				order_by="idx asc",
				ignore_permissions=True,
				limit_page_length=500,
			)
			normalized_values = [
				(row.get("attribute_value") or "").strip()
				for row in rows
				if (row.get("attribute_value") or "").strip()
			]

		if not normalized_values:
			frappe.throw(_("No values selected for Item Attribute: {0}").format(attribute_name))

		values_by_attribute[attribute_name] = normalized_values

	value_lists = [values_by_attribute.get(attr_name) or [] for attr_name in normalized_attributes]
	combinations = list(product(*value_lists))
	if not combinations:
		frappe.throw(_("No variant combinations found."))
	if len(combinations) > 600:
		frappe.throw(_("Too many combinations. Please select fewer values (max 600 variants per run)."))

	from erpnext.controllers.item_variant import create_variant, get_variant

	created = []
	existed = []
	template_slug = (
		template_doc.get("restaurant_slug") or template_doc.item_name or template_doc.item_code or ""
	).strip()
	for combination in combinations:
		args = {
			attribute_name: combination[index] for index, attribute_name in enumerate(normalized_attributes)
		}
		existing_name = get_variant(template_doc.name, args=args)
		if existing_name:
			existed.append(existing_name)
			continue

		variant_doc = create_variant(template_doc.name, args, use_template_image=True)
		variant_doc.flags.ignore_mandatory = True
		variant_doc.save(ignore_permissions=True)

		if _has_column("Item", "restaurant_slug") and not (variant_doc.get("restaurant_slug") or "").strip():
			suffix_parts = [
				_management_slugify_value(args.get(attr_name)) for attr_name in normalized_attributes
			]
			suffix = "-".join([part for part in suffix_parts if part])
			target_slug = _management_unique_item_slug(
				f"{template_slug}-{suffix}" if suffix else template_slug,
				item_name=variant_doc.name,
			)
			if target_slug:
				frappe.db.set_value(
					"Item", variant_doc.name, "restaurant_slug", target_slug, update_modified=False
				)

		created.append(variant_doc.name)

	template_doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"created_count": len(created),
		"existing_count": len(existed),
		"created_items": created,
		"existing_items": existed,
		"builder": get_management_product_variant_builder(template_doc.name),
	}


def _management_list_selling_price_lists(currency=None):
	_ensure_default_selling_price_list_field()
	filters = _selling_price_list_filters(currency=currency)

	fields = ["name", "price_list_name", "currency", "selling", "modified"]
	if _has_column("Price List", "enabled"):
		fields.append("enabled")
	if _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
		fields.append(DEFAULT_SELLING_PRICE_LIST_FIELD)

	order_by = "modified desc"
	if _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
		order_by = f"{DEFAULT_SELLING_PRICE_LIST_FIELD} desc, modified desc"

	rows = frappe.get_all(
		"Price List",
		fields=fields,
		filters=filters,
		order_by=order_by,
		ignore_permissions=True,
	)
	default_name = _get_default_selling_price_list_name(currency=currency, set_fallback_default=True)

	payload = []
	for row in rows:
		payload.append(
			{
				"name": row.name,
				"title": row.price_list_name or row.name,
				"currency": row.currency or "",
				"enabled": cint(row.get("enabled") if "enabled" in row else 1),
				"selling": cint(row.get("selling") if "selling" in row else 1),
				"is_default": 1 if row.name == default_name else 0,
			}
		)
	payload.sort(key=lambda row: (0 if row.get("is_default") else 1, row.get("title") or row.get("name") or ""))
	return payload, default_name


def _normalize_management_modifier_group_option(row=None, idx=0):
	row = row or {}
	action_type = (row.get("action_type") or row.get("modifier_type") or "add_on").strip() or "add_on"
	if action_type not in {"add_on", "bom_variant"}:
		action_type = "add_on"

	option_name = (
		row.get("option_name")
		or row.get("option_label")
		or row.get("option_key")
		or row.get("name")
		or row.get("option_item")
		or row.get("alternative_bom")
		or ""
	).strip()
	if not option_name:
		return None

	option_item = (row.get("option_item") or "").strip()
	qty_rules = _normalize_modifier_option_quantity_rules(row)
	option_qty = flt(qty_rules.get("option_qty") or 1) or 1
	option_cost_rate = 0
	option_uom = (row.get("option_uom") or "").strip()
	if action_type == "add_on" and option_item and frappe.db.exists("Item", option_item):
		option_cost_rate = flt(frappe.db.get_value("Item", option_item, "valuation_rate") or 0)
		option_uom = option_uom or (frappe.db.get_value("Item", option_item, "stock_uom") or "")

	return {
		"option_name": option_name,
		"action_type": action_type,
		"option_item": option_item,
		"option_uom": option_uom,
		"option_qty": option_qty,
		"option_cost_rate": option_cost_rate,
		"option_cost_amount": flt(option_cost_rate * option_qty),
		"price_delta": flt(row.get("price_delta") or 0),
		"min_qty": flt(qty_rules.get("min_qty") or 0),
		"max_qty": flt(qty_rules.get("max_qty") or 0),
		"qty_step": flt(qty_rules.get("qty_step") or 1),
		"alternative_bom": (row.get("alternative_bom") or "").strip(),
		"recipe_multiplier": flt(row.get("recipe_multiplier") or 1) or 1,
		"is_default": cint(row.get("is_default")),
		"sort_order": cint(row.get("sort_order") or idx or 0),
		"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
	}


def _serialize_management_modifier_group(group_doc, price_list=None):
	if isinstance(group_doc, str):
		group_doc = frappe.get_doc("Restaurant Modifier Group", group_doc)

	default_price_list = (price_list or _default_selling_price_list() or "").strip()
	options = []
	unresolved_count = 0
	active_options_count = 0

	for idx, option_row in enumerate(
		sorted(group_doc.get("options") or [], key=lambda d: (cint(d.get("sort_order") or 0), cint(d.get("idx") or 0))),
		start=1,
	):
		normalized_option = _normalize_management_modifier_group_option(option_row, idx=idx)
		if not normalized_option:
			continue
		pricing = _resolve_modifier_option_pricing(normalized_option, price_list=default_price_list)
		option_item = normalized_option.get("option_item") or ""
		if cint(normalized_option.get("is_active") if normalized_option.get("is_active") not in (None, "") else 1):
			active_options_count += 1
			if pricing.get("price_status") not in {"ok"}:
				unresolved_count += 1

		options.append(
			{
				"name": option_row.get("name") or "",
				"option_name": normalized_option.get("option_name"),
				"action_type": normalized_option.get("action_type"),
				"option_item": option_item,
				"option_item_name": frappe.db.get_value("Item", option_item, "item_name") if option_item else "",
				"option_uom": normalized_option.get("option_uom") or "",
				"option_qty": flt(normalized_option.get("option_qty") or 1),
				"base_qty": flt(normalized_option.get("option_qty") or 1),
				"option_cost_rate": flt(normalized_option.get("option_cost_rate") or 0),
				"option_cost_amount": flt(normalized_option.get("option_cost_amount") or 0),
				"legacy_price_delta": flt(normalized_option.get("price_delta") or 0),
				"min_qty": flt(normalized_option.get("min_qty") or 0),
				"max_qty": flt(normalized_option.get("max_qty") or 0),
				"qty_step": flt(normalized_option.get("qty_step") or 1),
				"alternative_bom": normalized_option.get("alternative_bom") or "",
				"recipe_multiplier": flt(normalized_option.get("recipe_multiplier") or 1),
				"is_default": cint(normalized_option.get("is_default")),
				"sort_order": cint(normalized_option.get("sort_order") or 0),
				"is_active": cint(normalized_option.get("is_active") if normalized_option.get("is_active") not in (None, "") else 1),
				**pricing,
			}
		)

	return {
		"name": group_doc.name,
		"title": group_doc.get("title") or group_doc.name,
		"selection_mode": group_doc.get("selection_mode") or "single",
		"required": cint(group_doc.get("required")),
		"min_select": cint(group_doc.get("min_select") or 0),
		"max_select": cint(group_doc.get("max_select") or 1),
		"description": group_doc.get("description") or "",
		"sort_order": cint(group_doc.get("sort_order") or 0),
		"is_active": cint(group_doc.get("is_active") if group_doc.get("is_active") not in (None, "") else 1),
		"default_price_list": default_price_list,
		"options": options,
		"options_count": len(options),
		"active_options_count": active_options_count,
		"unresolved_options_count": unresolved_count,
		"has_pricing_issues": 1 if unresolved_count > 0 else 0,
	}


def _validate_management_modifier_group_options(is_group_active, options=None, price_list=None):
	options = options or []
	default_price_list = (price_list or _default_selling_price_list() or "").strip()
	issues = []
	for idx, row in enumerate(options, start=1):
		normalized = _normalize_management_modifier_group_option(row, idx=idx)
		if not normalized:
			continue
		if not cint(normalized.get("is_active") if normalized.get("is_active") not in (None, "") else 1):
			continue
		pricing = _resolve_modifier_option_pricing(normalized, price_list=default_price_list)
		if is_group_active and pricing.get("price_status") not in {"ok"}:
			issues.append(
				{
					"option_name": normalized.get("option_name") or _("Option #{0}").format(idx),
					"reason": pricing.get("unavailable_reason")
					or _("Modifier option pricing could not be resolved."),
				}
			)
	return issues


def _management_get_item_price_history(item_code, limit=30):
	if not item_code or not frappe.db.exists("DocType", "Item Price"):
		return []

	price_lists, _default_name = _management_list_selling_price_lists()
	selling_names = [row.get("name") for row in price_lists if row.get("name")]
	if not selling_names:
		return []

	rows = frappe.get_all(
		"Item Price",
		fields=["name", "price_list", "price_list_rate", "currency", "valid_from", "modified", "uom"],
		filters={
			"item_code": item_code,
			"price_list": ["in", selling_names],
		},
		order_by="modified desc",
		ignore_permissions=True,
		limit_page_length=max(cint(limit), 1),
	)

	payload = []
	for row in rows:
		payload.append(
			{
				"name": row.name,
				"price_list": row.price_list,
				"price_list_rate": flt(row.price_list_rate),
				"currency": row.currency or "",
				"uom": row.uom or "",
				"valid_from": str(row.valid_from) if row.valid_from else "",
				"modified": _json_safe_datetime(row.modified),
				"effective_at": str(row.valid_from) if row.valid_from else _json_safe_datetime(row.modified),
			}
		)
	return payload


def _management_collect_product_lines(item_doc, orders):
	lookup = {
		(item_doc.name or "").strip().lower(),
		(item_doc.item_code or "").strip().lower(),
		(item_doc.item_name or "").strip().lower(),
	}
	lookup = {token for token in lookup if token}

	lines = []
	for order in orders or []:
		order_lines = order.get("items") or []
		for line in order_lines:
			line_code = (line.get("item_code") or "").strip().lower()
			line_title = (line.get("title") or "").strip().lower()
			if line_code and line_code in lookup:
				matches = True
			else:
				matches = bool(line_title and line_title in lookup)
			if not matches:
				continue

			lines.append(
				{
					"order_name": order.get("name"),
					"order_code": order.get("order_code") or order.get("name"),
					"source": order.get("source") or "web",
					"channel": order.get("channel") or "",
					"status": order.get("status") or "",
					"created_at": order.get("created_at"),
					"customer_name": order.get("customer_name") or "",
					"mobile": order.get("mobile") or "",
					"cashier": order.get("cashier") or "",
					"qty": flt(line.get("qty")),
					"line_total": flt(line.get("line_total")),
					"is_revenue": 1 if _is_revenue_order(order) else 0,
				}
			)
	return lines


def _management_product_line_metrics(lines):
	revenue_lines = [line for line in lines if cint(line.get("is_revenue")) == 1]
	order_names = {line.get("order_name") for line in revenue_lines if line.get("order_name")}
	customers = {
		f"{(line.get('mobile') or '').strip()}::{(line.get('customer_name') or '').strip()}"
		for line in revenue_lines
	}
	customers = {row for row in customers if row != "::"}

	total_sales = sum(flt(line.get("line_total")) for line in revenue_lines)
	total_qty = sum(flt(line.get("qty")) for line in revenue_lines)
	total_orders = len(order_names)
	total_customers = len(customers)

	cancelled_lines = [line for line in lines if str(line.get("status") or "").strip().lower() == "cancelled"]
	cancelled_sales = sum(flt(line.get("line_total")) for line in cancelled_lines)
	cancelled_qty = sum(flt(line.get("qty")) for line in cancelled_lines)

	return {
		"revenue_lines": revenue_lines,
		"total_sales": total_sales,
		"total_qty": total_qty,
		"orders_count": total_orders,
		"customers_count": total_customers,
		"avg_order_value": round(_safe_div(total_sales, total_orders), 2),
		"avg_qty_per_order": round(_safe_div(total_qty, total_orders), 2),
		"cancelled_sales": cancelled_sales,
		"cancelled_qty": cancelled_qty,
	}


def _management_product_daily_series(lines, date_from, date_to):
	start_date = getdate(date_from)
	end_date = getdate(date_to)
	dates = []
	cursor = start_date
	while cursor <= end_date:
		dates.append(str(cursor))
		cursor = getdate(add_days(cursor, 1))

	sales_by_date = defaultdict(float)
	qty_by_date = defaultdict(float)
	for line in lines:
		created_at = line.get("created_at")
		try:
			date_key = str(getdate(created_at))
		except Exception:
			continue
		sales_by_date[date_key] += flt(line.get("line_total"))
		qty_by_date[date_key] += flt(line.get("qty"))

	return {
		"labels": dates,
		"sales_values": [round(sales_by_date.get(date_key, 0), 2) for date_key in dates],
		"qty_values": [round(qty_by_date.get(date_key, 0), 3) for date_key in dates],
	}


def _management_product_hourly_series(lines):
	hourly_sales = [0.0 for _ in range(24)]
	hourly_qty = [0.0 for _ in range(24)]
	for line in lines:
		try:
			hour = get_datetime(line.get("created_at")).hour
		except Exception:
			continue
		hourly_sales[hour] += flt(line.get("line_total"))
		hourly_qty[hour] += flt(line.get("qty"))

	labels = [str(hour).zfill(2) for hour in range(24)]
	return {
		"labels": labels,
		"sales_values": [round(value, 2) for value in hourly_sales],
		"qty_values": [round(value, 3) for value in hourly_qty],
	}


def _management_build_product_analytics(item_doc, date_from=None, date_to=None):
	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to, default_days=30)
	prev_start, prev_end = _management_previous_window(date_from=start_date, date_to=end_date)

	current_orders = _management_collect_orders(date_from=start_date, date_to=end_date, source="all")
	previous_orders = _management_collect_orders(date_from=prev_start, date_to=prev_end, source="all")

	current_lines = _management_collect_product_lines(item_doc, current_orders)
	previous_lines = _management_collect_product_lines(item_doc, previous_orders)
	current_metrics = _management_product_line_metrics(current_lines)
	previous_metrics = _management_product_line_metrics(previous_lines)

	total_sales_window = sum(
		flt(order.get("grand_total")) for order in current_orders if _is_revenue_order(order)
	)
	prev_sales_window = sum(
		flt(order.get("grand_total")) for order in previous_orders if _is_revenue_order(order)
	)
	contribution_pct = round(_safe_div(current_metrics["total_sales"] * 100.0, total_sales_window or 1), 2)
	prev_contribution_pct = round(
		_safe_div(previous_metrics["total_sales"] * 100.0, prev_sales_window or 1), 2
	)

	daily_series = _management_product_daily_series(current_metrics["revenue_lines"], start_date, end_date)
	hourly_series = _management_product_hourly_series(current_metrics["revenue_lines"])

	recent_rows = sorted(
		current_lines,
		key=lambda row: _json_safe_datetime(row.get("created_at")) or "",
		reverse=True,
	)[:20]
	table_rows = [
		{
			"created_at": row.get("created_at"),
			"order_code": row.get("order_code"),
			"customer_name": row.get("customer_name"),
			"channel": row.get("channel"),
			"status": row.get("status"),
			"qty": flt(row.get("qty")),
			"line_total": flt(row.get("line_total")),
		}
		for row in recent_rows
	]

	customer_groups = defaultdict(lambda: {"customer_name": "", "sales": 0.0, "qty": 0.0, "orders": set()})
	for row in current_metrics["revenue_lines"]:
		key = f"{(row.get('mobile') or '').strip()}::{(row.get('customer_name') or '').strip()}"
		bucket = customer_groups[key]
		bucket["customer_name"] = (
			(row.get("customer_name") or "").strip() or (row.get("mobile") or "").strip() or "-"
		)
		bucket["sales"] += flt(row.get("line_total"))
		bucket["qty"] += flt(row.get("qty"))
		if row.get("order_name"):
			bucket["orders"].add(row.get("order_name"))

	customer_rows = sorted(customer_groups.values(), key=lambda row: row.get("sales") or 0, reverse=True)[:8]
	customer_table = [
		{
			"customer_name": row.get("customer_name"),
			"sales": round(flt(row.get("sales")), 2),
			"qty": round(flt(row.get("qty")), 3),
			"orders": len(row.get("orders") or []),
		}
		for row in customer_rows
	]

	peak_sales = max(daily_series["sales_values"] or [0])
	peak_index = daily_series["sales_values"].index(peak_sales) if daily_series["sales_values"] else 0
	peak_day = (daily_series["labels"] or [""])[peak_index] if daily_series["labels"] else ""

	return {
		"meta": {
			"date_from": start_date,
			"date_to": end_date,
			"previous_date_from": prev_start,
			"previous_date_to": prev_end,
			"compare_mode": "previous_window",
		},
		"kpis": [
			_bi_kpi(
				"product_sales",
				_("Product Sales"),
				current_metrics["total_sales"],
				"money",
				previous_metrics["total_sales"],
			),
			_bi_kpi(
				"product_qty",
				_("Sold Quantity"),
				current_metrics["total_qty"],
				"count",
				previous_metrics["total_qty"],
			),
			_bi_kpi(
				"orders_count",
				_("Orders with Product"),
				current_metrics["orders_count"],
				"count",
				previous_metrics["orders_count"],
			),
			_bi_kpi(
				"customers_count",
				_("Unique Customers"),
				current_metrics["customers_count"],
				"count",
				previous_metrics["customers_count"],
			),
			_bi_kpi(
				"avg_order_value",
				_("Average Order Value"),
				current_metrics["avg_order_value"],
				"money",
				previous_metrics["avg_order_value"],
			),
			_bi_kpi(
				"contribution_pct",
				_("Sales Contribution"),
				contribution_pct,
				"percent",
				prev_contribution_pct,
			),
		],
		"charts": [
			{
				"key": "daily-sales",
				"title": _("Daily Sales"),
				"type": "line",
				"unit": "money",
				"labels": daily_series["labels"],
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#2f6f5c",
						"values": daily_series["sales_values"],
					}
				],
			},
			{
				"key": "daily-qty",
				"title": _("Daily Quantity"),
				"type": "line",
				"unit": "count",
				"labels": daily_series["labels"],
				"series": [
					{
						"key": "qty",
						"label": _("Quantity"),
						"color": "#da8a2f",
						"values": daily_series["qty_values"],
					}
				],
			},
			{
				"key": "hourly-sales",
				"title": _("Hourly Sales Trend"),
				"type": "line",
				"unit": "money",
				"labels": hourly_series["labels"],
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#3e8ed0",
						"values": hourly_series["sales_values"],
					}
				],
			},
		],
		"tables": [
			{
				"key": "recent-orders",
				"title": _("Recent Orders"),
				"columns": _table_columns_from_rows(table_rows),
				"rows": table_rows,
			},
			{
				"key": "top-customers",
				"title": _("Top Customers"),
				"columns": _table_columns_from_rows(customer_table),
				"rows": customer_table,
			},
		],
		"insights": [
			{
				"key": "peak-day",
				"severity": "info",
				"text": _("Peak day for this item: {0}.").format(peak_day or "-"),
			},
			{
				"key": "cancelled-impact",
				"severity": "warn" if current_metrics["cancelled_sales"] > 0 else "info",
				"text": _("Cancelled value in window: {0}.").format(
					frappe.format_value(
						current_metrics["cancelled_sales"],
						{"fieldtype": "Currency", "options": _get_currency()},
					)
				),
			},
		],
		"currency": _get_currency(),
	}


@frappe.whitelist()
def get_management_modifier_groups_context():
	_ensure_management_access()
	price_lists, default_price_list = _management_list_selling_price_lists()
	item_filters = {"disabled": 0} if _has_column("Item", "disabled") else {}
	bom_filters = {"is_active": 1} if _has_column("BOM", "is_active") else {}
	return {
		"default_price_list": default_price_list or "",
		"price_lists": price_lists,
		"item_options": _named_doc_options("Item", label_fields=("item_name",), filters=item_filters, limit=1000),
		"bom_options": _named_doc_options("BOM", label_fields=("item",), filters=bom_filters, limit=1000),
		"uom_options": _named_doc_options("UOM", label_fields=("uom_name",), limit=500),
		"action_type_options": [
			{"value": "add_on", "label": _("Add-on")},
			{"value": "bom_variant", "label": _("BOM Variant")},
		],
	}


@frappe.whitelist()
def list_management_modifier_groups(search=None, include_inactive=1):
	_ensure_management_access()
	search = (search or "").strip()
	include_inactive = cint(include_inactive)
	filters = {}
	if not include_inactive and _has_column("Restaurant Modifier Group", "is_active"):
		filters["is_active"] = 1

	rows = frappe.get_all(
		"Restaurant Modifier Group",
		fields=[
			"name",
			"title",
			"selection_mode",
			"required",
			"min_select",
			"max_select",
			"description",
			"sort_order",
			"is_active",
			"modified",
		],
		filters=filters,
		or_filters=(
			[
				["name", "like", f"%{search}%"],
				["title", "like", f"%{search}%"],
			]
			if search
			else None
		),
		order_by="sort_order asc, modified desc",
		ignore_permissions=True,
		limit_page_length=500,
	)
	default_price_list = _default_selling_price_list()
	payload = []
	for row in rows:
		serialized = _serialize_management_modifier_group(row.name, price_list=default_price_list)
		payload.append(
			{
				"name": serialized.get("name"),
				"title": serialized.get("title"),
				"selection_mode": serialized.get("selection_mode"),
				"required": serialized.get("required"),
				"min_select": serialized.get("min_select"),
				"max_select": serialized.get("max_select"),
				"description": serialized.get("description"),
				"sort_order": serialized.get("sort_order"),
				"is_active": serialized.get("is_active"),
				"modified": row.get("modified"),
				"options_count": serialized.get("options_count"),
				"active_options_count": serialized.get("active_options_count"),
				"unresolved_options_count": serialized.get("unresolved_options_count"),
				"has_pricing_issues": serialized.get("has_pricing_issues"),
				"default_price_list": serialized.get("default_price_list") or "",
			}
		)
	return {
		"groups": payload,
		"default_price_list": default_price_list or "",
	}


@frappe.whitelist()
def get_management_modifier_group_detail(group_name):
	_ensure_management_access()
	group_name = (group_name or "").strip()
	if not group_name:
		frappe.throw(_("Modifier Group name is required."))
	if not frappe.db.exists("Restaurant Modifier Group", group_name):
		frappe.throw(_("Modifier Group not found."), frappe.DoesNotExistError)
	return _serialize_management_modifier_group(group_name)


@frappe.whitelist()
def save_management_modifier_group(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	group_name = (parsed_payload.get("name") or parsed_payload.get("group_name") or "").strip()
	title = (parsed_payload.get("title") or "").strip()
	if not title:
		frappe.throw(_("Modifier Group title is required."))

	if group_name:
		if not frappe.db.exists("Restaurant Modifier Group", group_name):
			frappe.throw(_("Modifier Group not found."), frappe.DoesNotExistError)
		group_doc = frappe.get_doc("Restaurant Modifier Group", group_name)
	else:
		group_doc = frappe.new_doc("Restaurant Modifier Group")

	group_doc.title = title
	group_doc.selection_mode = (parsed_payload.get("selection_mode") or "single").strip() or "single"
	group_doc.required = cint(parsed_payload.get("required"))
	group_doc.min_select = cint(parsed_payload.get("min_select") or 0)
	group_doc.max_select = max(cint(parsed_payload.get("max_select") or 1), 1)
	group_doc.description = (parsed_payload.get("description") or "").strip()
	group_doc.sort_order = cint(parsed_payload.get("sort_order") or 0)
	group_doc.is_active = cint(parsed_payload.get("is_active") if parsed_payload.get("is_active") not in (None, "") else 1)

	raw_options = parsed_payload.get("options") if isinstance(parsed_payload.get("options"), list) else []
	normalized_options = []
	for idx, row in enumerate(raw_options, start=1):
		normalized = _normalize_management_modifier_group_option(row, idx=idx)
		if normalized:
			normalized_options.append(normalized)
	if not normalized_options:
		frappe.throw(_("At least one modifier option is required."))

	issues = _validate_management_modifier_group_options(group_doc.is_active, normalized_options)
	if issues:
		first_issue = issues[0]
		frappe.throw(
			_("Cannot save active modifier group because option {0} is unresolved: {1}").format(
				first_issue.get("option_name"),
				first_issue.get("reason"),
			),
			frappe.ValidationError,
		)

	group_doc.set("options", [])
	for idx, row in enumerate(normalized_options, start=1):
		row["idx"] = idx
		group_doc.append("options", row)

	if group_doc.is_new():
		group_doc.insert(ignore_permissions=True)
	else:
		group_doc.save(ignore_permissions=True)

	for child_row, source_row in zip(group_doc.get("options") or [], normalized_options):
		option_uom = (source_row.get("option_uom") or "").strip()
		if child_row.name and child_row.get("option_uom") != option_uom:
			frappe.db.set_value(
				"Restaurant Modifier Option",
				child_row.name,
				"option_uom",
				option_uom,
				update_modified=False,
			)

	frappe.db.commit()
	frappe.clear_cache(doctype="Restaurant Modifier Group")
	return _serialize_management_modifier_group(group_doc.name)


@frappe.whitelist()
def list_management_price_lists(currency=None):
	_ensure_management_access()
	rows, default_name = _management_list_selling_price_lists(currency=(currency or "").strip() or None)
	return {
		"price_lists": rows,
		"default_price_list": default_name or "",
	}


@frappe.whitelist()
def set_management_default_price_list(price_list_name):
	_ensure_management_access()
	price_list_name = (price_list_name or "").strip()
	if not price_list_name:
		frappe.throw(_("Price List name is required."))
	if not frappe.db.exists("Price List", price_list_name):
		frappe.throw(_("Price List not found."), frappe.DoesNotExistError)

	_ensure_default_selling_price_list_field()
	if not _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
		frappe.throw(_("Could not prepare default price list field."))

	is_selling = cint(frappe.db.get_value("Price List", price_list_name, "selling"))
	if not is_selling:
		frappe.throw(_("Selected price list must be a selling price list."))

	if frappe.db.exists("DocType", "Selling Settings"):
		selling_settings_meta = frappe.get_meta("Selling Settings")
		if selling_settings_meta.get_field("selling_price_list"):
			frappe.db.set_single_value("Selling Settings", "selling_price_list", price_list_name)

	fieldname = DEFAULT_SELLING_PRICE_LIST_FIELD
	frappe.db.sql(
		f"""
        update `tabPrice List`
        set `{fieldname}` = 0
        where selling = 1 and name != %s
        """,
		(price_list_name,),
	)
	frappe.db.set_value("Price List", price_list_name, fieldname, 1, update_modified=True)
	frappe.db.commit()

	rows, default_name = _management_list_selling_price_lists()
	return {
		"status": "success",
		"default_price_list": default_name or price_list_name,
		"price_lists": rows,
	}


def _serialize_management_builder_template(template):
	steps_data = []
	for step in sorted(template.steps or [], key=lambda s: s.sort_order or 0):
		options_data = []
		for opt in _get_builder_step_options(step.name):
			item_name = frappe.db.get_value("Item", opt.item, "item_name") if opt.item else ""
			options_data.append(
				{
					"name": opt.name,
					"option_label": opt.option_label,
					"option_key": opt.option_key,
					"option_description": opt.option_description or "",
					"sort_order": opt.sort_order or 0,
					"item": opt.item or "",
					"item_name": item_name or "",
					"base_price_delta": opt.base_price_delta or 0,
					"price_type": opt.price_type or "fixed",
					"price_percentage": opt.price_percentage or 0,
					"is_default": bool(opt.is_default),
					"is_available": opt.is_available != 0,
					"max_qty": opt.max_qty or 1,
					"image": opt.image or "",
					"color_code": opt.color_code or "",
					"nutrition_json": opt.nutrition_json or "",
					"allergen_tags": opt.allergen_tags or "",
					"stock_impact_json": opt.stock_impact_json or "",
					"linked_step_key": opt.linked_step_key or "",
					"disable_if": opt.disable_if or "",
				}
			)

		steps_data.append(
			{
				"name": step.name,
				"step_title": step.step_title,
				"step_key": step.step_key,
				"step_description": step.step_description or "",
				"sort_order": step.sort_order or 0,
				"selection_mode": step.selection_mode or "single",
				"min_select": step.min_select or 0,
				"max_select": step.max_select or 1,
				"is_required": bool(step.is_required),
				"show_step_price": step.show_step_price != 0,
				"step_icon": step.step_icon or "",
				"conditional_logic": step.conditional_logic or {},
				"options": options_data,
			}
		)

	return {
		"name": template.name,
		"title": template.title,
		"slug": template.slug,
		"description": template.description or "",
		"is_active": bool(template.is_active),
		"layout_mode": template.layout_mode,
		"show_summary_panel": template.show_summary_panel != 0,
		"show_price_live": template.show_price_live != 0,
		"primary_color": template.primary_color or "#1a73e8",
		"background_image": template.background_image or "",
		"allow_skip_steps": bool(template.allow_skip_steps),
		"allow_go_back": template.allow_go_back != 0,
		"require_all_required": template.require_all_required != 0,
		"max_total_selections": template.max_total_selections or 0,
		"steps": steps_data,
	}


def _management_builder_templates_summary():
	templates = frappe.get_all(
		"Product Builder Template",
		fields=["name", "title", "slug", "description", "is_active", "layout_mode", "modified"],
		order_by="modified desc",
	)
	for template in templates:
		template["steps_count"] = frappe.db.count(
			"Product Builder Step", {"parent": template.name, "parenttype": "Product Builder Template"}
		)
	return templates


def _normalize_builder_template_payload(payload=None):
	source = frappe.parse_json(payload) if isinstance(payload, str) else payload
	if not isinstance(source, dict):
		return {}
	normalized = copy.deepcopy(source)
	for step in normalized.get("steps") or []:
		if not isinstance(step, dict):
			continue
		step["conditional_logic"] = _parse_json(step.get("conditional_logic"), {})
		for fieldname in ("is_required", "show_step_price"):
			if fieldname in step:
				step[fieldname] = bool(cint(step.get(fieldname)))
		for option in step.get("options") or []:
			if not isinstance(option, dict):
				continue
			for fieldname in ("is_default", "is_available"):
				if fieldname in option:
					option[fieldname] = bool(cint(option.get(fieldname)))
			option["nutrition_json"] = _normalize_json_text_field(
				option.get("nutrition_json", option.get("nutrition")),
				{},
			)
			option["stock_impact_json"] = _normalize_json_text_field(
				option.get("stock_impact_json", option.get("stock_impact")),
				{},
			)
			option["disable_if"] = _normalize_json_text_field(
				option.get("disable_if", option.get("disabled_if")),
				[],
			)
			option.pop("nutrition", None)
			option.pop("stock_impact", None)
			option.pop("disabled_if", None)
	return normalized


def _builder_payload_signature(payload=None):
	normalized = _normalize_builder_template_payload(payload)
	return _stable_json_dumps(normalized)


def _merge_builder_payload_defaults(incoming=None, existing=None):
	incoming_payload = _normalize_builder_template_payload(incoming)
	existing_payload = _normalize_builder_template_payload(existing)
	if not existing_payload:
		return incoming_payload
	if not incoming_payload:
		return existing_payload

	merged = copy.deepcopy(existing_payload)
	for key, value in incoming_payload.items():
		if key == "steps":
			continue
		merged[key] = value

	existing_steps = existing_payload.get("steps") or []
	incoming_steps = incoming_payload.get("steps") or []
	step_map = {
		StringKey: step
		for StringKey, step in [
			(
				str((step or {}).get("step_key") or index),
				copy.deepcopy(step or {}),
			)
			for index, step in enumerate(existing_steps)
			if isinstance(step, dict)
		]
	}
	merged_steps = []
	for index, step in enumerate(incoming_steps):
		if not isinstance(step, dict):
			continue
		step_key = str(step.get("step_key") or index)
		base_step = copy.deepcopy(step_map.get(step_key) or {})
		for key, value in step.items():
			if key == "options":
				continue
			base_step[key] = value

		existing_options = (step_map.get(step_key) or {}).get("options") or []
		option_map = {
			str((opt or {}).get("option_key") or opt_index): copy.deepcopy(opt or {})
			for opt_index, opt in enumerate(existing_options)
			if isinstance(opt, dict)
		}
		merged_options = []
		for opt_index, option in enumerate(step.get("options") or []):
			if not isinstance(option, dict):
				continue
			option_key = str(option.get("option_key") or opt_index)
			base_option = copy.deepcopy(option_map.get(option_key) or {})
			base_option.update(option)
			merged_options.append(base_option)
		base_step["options"] = merged_options
		merged_steps.append(base_step)

	merged["steps"] = merged_steps
	return merged


def _build_item_specific_builder_template(item_doc, builder_payload, selected_template_name=None):
	payload = _normalize_builder_template_payload(builder_payload)
	if not isinstance(payload, dict):
		frappe.throw(_("Invalid product builder config."))

	title = (payload.get("title") or item_doc.get("item_name") or item_doc.name or "").strip()
	if not title:
		frappe.throw(_("Builder title is required."))

	base_slug = (payload.get("slug") or "").strip()
	if not base_slug:
		base_slug = frappe.scrub(item_doc.get("item_code") or item_doc.name or title) + "-builder"
	if not base_slug:
		base_slug = "item-builder"

	target_name = (item_doc.get("restaurant_builder_template") or "").strip()
	shared_name = (selected_template_name or "").strip()
	use_existing = False
	if target_name and frappe.db.exists("Product Builder Template", target_name):
		# If the user is applying/editing a shared selected template, create an item-specific copy.
		# If the item is already linked to its own generated template, update that existing one.
		if not shared_name:
			use_existing = True
		elif target_name != shared_name:
			use_existing = True

	if use_existing:
		template_name = target_name
	else:
		template_name = ""
		candidate_slug = base_slug
		counter = 1
		while frappe.db.exists("Product Builder Template", {"slug": candidate_slug}):
			candidate_slug = f"{base_slug}-{counter}"
			counter += 1
		payload["slug"] = candidate_slug
		payload["name"] = ""
		payload["title"] = title
		payload["description"] = (
			payload.get("description")
			or f"Item-specific builder for {item_doc.get('item_name') or item_doc.name}"
		).strip()
		result = save_builder_template(template_data=frappe.as_json(payload))
		if (result or {}).get("status") != "success":
			error = (result or {}).get("error") or {}
			frappe.throw(error.get("message") or _("Failed to create item-specific builder template."))
		data = (result or {}).get("data") or {}
		template_name = data.get("name")
		if not template_name:
			frappe.throw(_("Failed to create item-specific builder template."))
		return template_name

	payload["name"] = template_name
	payload["title"] = title
	result = save_builder_template(template_data=frappe.as_json(payload))
	if (result or {}).get("status") != "success":
		error = (result or {}).get("error") or {}
		frappe.throw(error.get("message") or _("Failed to update item-specific builder template."))
	data = (result or {}).get("data") or {}
	return data.get("name") or template_name


@frappe.whitelist()
def get_management_product_detail(item_name, date_from=None, date_to=None):
	_ensure_management_access()
	item_name = _management_resolve_item_name(item_name)
	item_doc = frappe.get_doc("Item", item_name)
	image_field = _core_item_image_field()
	refreshed_nutrition = _refresh_item_nutrition_from_bom(item_doc.name)
	if refreshed_nutrition:
		item_doc = frappe.get_doc("Item", item_name)
	media = _management_collect_item_media(item_doc, image_field=image_field)

	price_lists, default_price_list = _management_list_selling_price_lists()
	history = _management_get_item_price_history(item_doc.item_code, limit=40)
	latest_price_row = history[0] if history else None

	current_row = None
	if default_price_list and frappe.db.exists("DocType", "Item Price"):
		current_row = frappe.db.get_value(
			"Item Price",
			{"item_code": item_doc.item_code, "price_list": default_price_list},
			["name", "price_list_rate", "currency", "valid_from", "modified", "uom"],
			as_dict=True,
		)

	category_slug = ""
	subcategory_slug = ""
	if item_doc.get("restaurant_category"):
		category_slug = (
			frappe.db.get_value("Item Group", item_doc.get("restaurant_category"), "restaurant_slug") or ""
		)
	if item_doc.get("restaurant_subcategory"):
		subcategory_slug = (
			frappe.db.get_value("Item Group", item_doc.get("restaurant_subcategory"), "restaurant_slug") or ""
		)

	analytics = _management_build_product_analytics(item_doc, date_from=date_from, date_to=date_to)
	price_history_table = {
		"key": "price-history",
		"title": _("Price History"),
		"columns": _table_columns_from_rows(history),
		"rows": history,
	}
	analytics["tables"] = [price_history_table, *(analytics.get("tables") or [])]

	variant_of_name = (item_doc.get("variant_of") or "").strip() if _has_column("Item", "variant_of") else ""
	variant_of_item_name = ""
	if variant_of_name:
		variant_of_item_name = frappe.db.get_value("Item", variant_of_name, "item_name") or variant_of_name

	builder_templates = (
		_management_builder_templates_summary()
		if frappe.db.exists("DocType", "Product Builder Template")
		else []
	)
	builder_config = None
	builder_template_name = item_doc.get("restaurant_builder_template") or ""
	if builder_template_name and frappe.db.exists("Product Builder Template", builder_template_name):
		try:
			builder_template_doc = frappe.get_doc("Product Builder Template", builder_template_name)
			builder_config = _serialize_management_builder_template(builder_template_doc)
		except Exception:
			builder_config = None

	return {
		"item": {
			"name": item_doc.name,
			"item_code": item_doc.item_code,
			"item_name": item_doc.item_name,
			"variant_of": variant_of_name,
			"variant_of_item_name": variant_of_item_name,
			"has_variants": cint(item_doc.get("has_variants") or 0),
			"variant_based_on": item_doc.get("variant_based_on") or "",
			"custom_snapp_code": item_doc.get("custom_snapp_code")
			if _has_column("Item", "custom_snapp_code")
			else "",
			"item_group": item_doc.item_group,
			"stock_uom": item_doc.stock_uom,
			"disabled": cint(item_doc.disabled),
			"is_sales_item": cint(item_doc.get("is_sales_item") or 0),
			"show_in_website": cint(item_doc.get("show_in_website") or 0),
			"description": item_doc.description or "",
			"short_description": item_doc.get("restaurant_short_desc") or "",
			"long_description": item_doc.get("restaurant_long_desc") or item_doc.description or "",
			"image": media.get("main_image") or getattr(item_doc, image_field, "") or "",
			"website_image": item_doc.get("website_image") or "",
			"restaurant_slug": item_doc.get("restaurant_slug") or "",
			"restaurant_enabled": cint(item_doc.get("restaurant_enabled") or 0),
			"restaurant_out_of_stock": cint(item_doc.get("restaurant_out_of_stock") or 0)
			if _has_column("Item", "restaurant_out_of_stock")
			else 0,
			"restaurant_packaging_price": flt(item_doc.get("restaurant_packaging_price") or 0)
			if _has_column("Item", "restaurant_packaging_price")
			else 0,
			"barcodes": [
				(barcode_row.get("barcode") or "").strip()
				for barcode_row in (item_doc.get("barcodes") or [])
				if (barcode_row.get("barcode") or "").strip()
			]
			if frappe.db.exists("DocType", "Item Barcode")
			else [],
			"restaurant_is_featured": cint(item_doc.get("restaurant_is_featured") or 0),
			"restaurant_is_best_seller": cint(item_doc.get("restaurant_is_best_seller") or 0),
			"restaurant_sort_order": cint(item_doc.get("restaurant_sort_order") or 0),
			"restaurant_prep_time_mins": cint(item_doc.get("restaurant_prep_time_mins") or 0),
			"restaurant_branch": item_doc.get("restaurant_branch") or "",
			"restaurant_category": item_doc.get("restaurant_category") or "",
			"restaurant_category_slug": category_slug,
			"restaurant_subcategory": item_doc.get("restaurant_subcategory") or "",
			"restaurant_subcategory_slug": subcategory_slug,
			"restaurant_requires_bom": cint(item_doc.get("restaurant_requires_bom") or 0),
			"restaurant_auto_add_to_order": cint(item_doc.get("restaurant_auto_add_to_order") or 0),
			"restaurant_coming_soon": cint(item_doc.get("restaurant_coming_soon") or 0),
			"restaurant_auto_add_qty": flt(item_doc.get("restaurant_auto_add_qty") or 0),
			"restaurant_is_customizable": cint(item_doc.get("restaurant_is_customizable") or 0),
			"restaurant_customize_button_label": item_doc.get("restaurant_customize_button_label") or "",
			"restaurant_custom_product_type": item_doc.get("restaurant_custom_product_type") or "",
			"restaurant_builder_template": item_doc.get("restaurant_builder_template") or "",
			"restaurant_builder_active": cint(item_doc.get("restaurant_builder_active") or 0),
			"restaurant_allow_direct_add": cint(item_doc.get("restaurant_allow_direct_add") or 0),
			"restaurant_show_nutrition_summary": cint(item_doc.get("restaurant_show_nutrition_summary") or 0),
			"restaurant_show_allergen_warnings": cint(item_doc.get("restaurant_show_allergen_warnings") or 0),
			"restaurant_kitchen_print_mode": _normalize_management_kitchen_print_mode(
				item_doc.get("restaurant_kitchen_print_mode"),
				fallback_to_default=True,
			),
			"restaurant_stock_consumption_mode": _normalize_management_stock_consumption_mode(
				item_doc.get("restaurant_stock_consumption_mode"),
				fallback_to_default=True,
			),
			"restaurant_item_tags": item_doc.get("restaurant_item_tags") or "",
			"restaurant_nutrition_kcal": flt(item_doc.get("restaurant_nutrition_kcal") or 0),
			"restaurant_nutrition_protein_g": flt(item_doc.get("restaurant_nutrition_protein_g") or 0),
			"restaurant_nutrition_carb_g": flt(item_doc.get("restaurant_nutrition_carb_g") or 0),
			"restaurant_nutrition_sugar_g": flt(item_doc.get("restaurant_nutrition_sugar_g") or 0),
			"restaurant_nutrition_fat_g": flt(item_doc.get("restaurant_nutrition_fat_g") or 0),
			"nutrition": _nutrition_payload(item_doc),
		},
		"media": media,
		"field_options": _management_product_field_options(),
		"builder_templates": builder_templates,
		"builder": {
			"template_name": builder_template_name,
			"builder_templates": builder_templates,
			"product_builder_config": builder_config,
		},
		"pricing": {
			"default_price_list": default_price_list or "",
			"price_lists": price_lists,
			"current_price": {
				"name": current_row.get("name") if current_row else "",
				"price_list": default_price_list or "",
				"price_list_rate": flt(current_row.get("price_list_rate")) if current_row else 0,
				"currency": (current_row.get("currency") if current_row else "") or _get_currency(),
				"uom": (current_row.get("uom") if current_row else "") or item_doc.stock_uom,
				"valid_from": str(current_row.get("valid_from"))
				if current_row and current_row.get("valid_from")
				else "",
				"modified": _json_safe_datetime(current_row.get("modified")) if current_row else "",
			},
			"latest_price": {
				"price_list": latest_price_row.get("price_list") if latest_price_row else "",
				"price_list_rate": flt(latest_price_row.get("price_list_rate")) if latest_price_row else 0,
				"currency": (latest_price_row.get("currency") if latest_price_row else "") or _get_currency(),
				"effective_at": latest_price_row.get("effective_at") if latest_price_row else "",
			},
			"history": history,
		},
		"report": analytics,
	}


@frappe.whitelist()
def update_management_product_settings(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	item_name = _management_resolve_item_name(parsed_payload.get("item_name") or parsed_payload.get("name"))
	item_doc = frappe.get_doc("Item", item_name)
	if "restaurant_coming_soon" in parsed_payload:
		_ensure_coming_soon_field()
		item_doc = frappe.get_doc("Item", item_doc.name)

	data_fields = {
		"item_name",
		"item_group",
		"stock_uom",
		"custom_snapp_code",
		"description",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_long_desc",
		"restaurant_branch",
		"restaurant_category",
		"restaurant_subcategory",
		"website_image",
		"image",
		"item_image",
		"restaurant_customize_button_label",
		"restaurant_custom_product_type",
		"restaurant_builder_template",
		"restaurant_kitchen_print_mode",
		"restaurant_stock_consumption_mode",
	}
	int_fields = {
		"disabled",
		"show_in_website",
		"restaurant_enabled",
		"restaurant_is_featured",
		"restaurant_is_best_seller",
		"restaurant_sort_order",
		"restaurant_prep_time_mins",
		"restaurant_requires_bom",
		"restaurant_auto_add_to_order",
		"restaurant_coming_soon",
		"restaurant_is_customizable",
		"restaurant_builder_active",
		"restaurant_allow_direct_add",
		"restaurant_show_nutrition_summary",
		"restaurant_show_allergen_warnings",
		"restaurant_out_of_stock",
	}
	float_fields = {"restaurant_auto_add_qty", "restaurant_packaging_price"}
	nutrition_fields = set(NUTRITION_KEY_FIELD_MAP.values())

	changed = False

	if "item_code" in parsed_payload and _has_column("Item", "item_code"):
		requested_item_code = (parsed_payload.get("item_code") or "").strip()
		if not requested_item_code:
			frappe.throw(_("Item code cannot be empty."))

		current_item_code = (item_doc.get("item_code") or "").strip()
		if requested_item_code != current_item_code:
			existing_docname = frappe.db.get_value("Item", {"item_code": requested_item_code}, "name")
			if existing_docname and existing_docname != item_doc.name:
				frappe.throw(_("Item code already exists."))

			if item_doc.name != requested_item_code:
				renamed_docname = rename_doc(
					"Item",
					item_doc.name,
					requested_item_code,
					force=True,
					merge=False,
					ignore_permissions=True,
				)
				item_doc = frappe.get_doc("Item", renamed_docname)

			if (item_doc.get("item_code") or "").strip() != requested_item_code:
				item_doc.set("item_code", requested_item_code)
			changed = True
	for fieldname in data_fields:
		if fieldname not in parsed_payload:
			continue
		if not _has_column("Item", fieldname):
			continue
		next_value = parsed_payload.get(fieldname)
		next_value = (next_value or "").strip() if isinstance(next_value, str) else (next_value or "")
		if fieldname == "restaurant_kitchen_print_mode":
			next_value = _normalize_management_kitchen_print_mode(next_value)
		elif fieldname == "restaurant_stock_consumption_mode":
			next_value = _normalize_management_stock_consumption_mode(next_value)
		if item_doc.get(fieldname) != next_value:
			item_doc.set(fieldname, next_value)
			changed = True

	for fieldname in int_fields:
		if fieldname not in parsed_payload:
			continue
		if not _has_column("Item", fieldname):
			continue
		next_value = cint(parsed_payload.get(fieldname))
		if item_doc.get(fieldname) != next_value:
			item_doc.set(fieldname, next_value)
			changed = True

	for fieldname in float_fields:
		if fieldname not in parsed_payload:
			continue
		if not _has_column("Item", fieldname):
			continue
		next_value = flt(parsed_payload.get(fieldname))
		if flt(item_doc.get(fieldname) or 0) != next_value:
			item_doc.set(fieldname, next_value)
			changed = True

	for fieldname in nutrition_fields:
		if fieldname not in parsed_payload:
			continue
		if not _has_column("Item", fieldname):
			continue
		next_value = flt(parsed_payload.get(fieldname) or 0)
		if flt(item_doc.get(fieldname) or 0) != next_value:
			item_doc.set(fieldname, next_value)
			changed = True

	# Handle tag table (child table) only after its optional custom doctypes are installed.
	tag_table_field = "restaurant_item_tag_table"
	if (
		tag_table_field in parsed_payload
		and _item_tag_tables_ready()
		and _has_column("Item", tag_table_field)
	):
		tag_links = parsed_payload.get(tag_table_field) or []
		if isinstance(tag_links, list):
			item_doc.set(tag_table_field, [])
			for link in tag_links:
				tag_name = link.get("tag") or link.get("_tag_title") or ""
				if tag_name:
					tag_docname = frappe.db.get_value("Restaurant Item Tag", {"title": tag_name}, "name")
					if not tag_docname:
						td = frappe.new_doc("Restaurant Item Tag")
						td.title = tag_name
						td.insert(ignore_permissions=True)
						tag_docname = td.name
					item_doc.append(tag_table_field, {"tag": tag_docname})
			changed = True

	builder_config_payload = parsed_payload.get("product_builder_config")
	selected_builder_template = (parsed_payload.get("restaurant_builder_template") or "").strip()
	if builder_config_payload and cint(
		parsed_payload.get("restaurant_is_customizable") or item_doc.get("restaurant_is_customizable") or 0
	):
		current_template_name = (item_doc.get("restaurant_builder_template") or "").strip()
		current_builder_config = None
		if current_template_name and frappe.db.exists("Product Builder Template", current_template_name):
			try:
				current_builder_config = _serialize_management_builder_template(
					frappe.get_doc("Product Builder Template", current_template_name)
				)
			except Exception:
				current_builder_config = None
		merged_builder_config = _merge_builder_payload_defaults(
			builder_config_payload,
			current_builder_config,
		)
		incoming_signature = _builder_payload_signature(merged_builder_config)
		current_signature = _builder_payload_signature(current_builder_config)
		if incoming_signature and incoming_signature != current_signature:
			template_name = _build_item_specific_builder_template(
				item_doc,
				merged_builder_config,
				selected_template_name=selected_builder_template,
			)
			if (
				_has_column("Item", "restaurant_builder_template")
				and (item_doc.get("restaurant_builder_template") or "") != template_name
			):
				item_doc.set("restaurant_builder_template", template_name)
				changed = True

	default_price_list = (parsed_payload.get("default_price_list") or "").strip()
	if default_price_list:
		set_management_default_price_list(default_price_list)

	if changed:
		item_doc.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache(doctype="Item")
		try:
			frappe.clear_website_cache()
		except Exception:
			pass

	return get_management_product_detail(item_doc.name)


@frappe.whitelist()
def set_management_product_price(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	item_name = _management_resolve_item_name(parsed_payload.get("item_name") or parsed_payload.get("name"))
	item_doc = frappe.get_doc("Item", item_name)
	rate = flt(parsed_payload.get("price_list_rate"))
	price_list_name = (
		parsed_payload.get("price_list") or parsed_payload.get("price_list_name") or ""
	).strip()
	valid_from = parsed_payload.get("valid_from")

	if not price_list_name:
		price_list_name = _get_default_selling_price_list_name(set_fallback_default=True) or ""
	if not price_list_name:
		frappe.throw(_("Please configure at least one selling price list."))
	if not frappe.db.exists("Price List", price_list_name):
		frappe.throw(_("Price List not found."), frappe.DoesNotExistError)
	if not cint(frappe.db.get_value("Price List", price_list_name, "selling")):
		frappe.throw(_("Price List must be a selling list."))

	currency = (
		parsed_payload.get("currency") or frappe.db.get_value("Price List", price_list_name, "currency") or ""
	).strip()
	if not currency:
		currency = _get_currency()

	filters = {"item_code": item_doc.item_code, "price_list": price_list_name}
	existing_name = frappe.db.get_value("Item Price", filters, "name")

	if existing_name:
		price_doc = frappe.get_doc("Item Price", existing_name)
		price_doc.price_list_rate = rate
		if _has_column("Item Price", "currency"):
			price_doc.currency = currency
		if valid_from and _has_column("Item Price", "valid_from"):
			price_doc.valid_from = getdate(valid_from)
		if _has_column("Item Price", "uom") and not price_doc.get("uom"):
			price_doc.uom = item_doc.stock_uom
		price_doc.save(ignore_permissions=True)
	else:
		payload_doc = {
			"doctype": "Item Price",
			"item_code": item_doc.item_code,
			"price_list": price_list_name,
			"price_list_rate": rate,
		}
		if _has_column("Item Price", "currency"):
			payload_doc["currency"] = currency
		if valid_from and _has_column("Item Price", "valid_from"):
			payload_doc["valid_from"] = getdate(valid_from)
		if _has_column("Item Price", "uom"):
			payload_doc["uom"] = item_doc.stock_uom
		frappe.get_doc(payload_doc).insert(ignore_permissions=True)

	# Keep standard rate and restaurant base price aligned with the active selling price.
	frappe.db.set_value("Item", item_doc.name, "standard_rate", rate, update_modified=True)
	if _has_column("Item", "restaurant_base_price"):
		frappe.db.set_value("Item", item_doc.name, "restaurant_base_price", rate, update_modified=False)

	frappe.db.commit()
	return get_management_product_detail(item_doc.name)


@frappe.whitelist()
def get_management_bom_context():
	_ensure_management_access()
	default_company = (frappe.db.get_single_value("Global Defaults", "default_company") or "").strip()
	company_filters = {}
	if _has_column("Company", "disabled"):
		company_filters["disabled"] = 0
	companies = frappe.get_all(
		"Company",
		filters=company_filters,
		fields=["name", "default_currency", "abbr"],
		ignore_permissions=True,
		order_by="name asc",
		limit_page_length=200,
	)
	default_row = None
	for row in companies or []:
		if (row.get("name") or "").strip() == default_company:
			default_row = row
			break
	if not default_row and companies:
		default_row = companies[0]
	return {
		"companies": companies or [],
		"default_company": (default_row or {}).get("name") or default_company or "",
		"default_currency": (default_row or {}).get("default_currency") or "",
	}


@frappe.whitelist()
def list_management_bom_items(search="", limit=200):
	_ensure_management_access()
	query = (search or "").strip()
	filters = {"disabled": 0}
	or_filters = None
	if query:
		like = f"%{query}%"
		or_filters = [["item_code", "like", like], ["item_name", "like", like], ["name", "like", like]]
	return frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "item_code", "item_name", "stock_uom"],
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=max(1, min(cint(limit or 200), 500)),
	)


@frappe.whitelist()
def list_management_boms(item_code="", search="", limit=50):
	_ensure_management_access()
	query = (search or "").strip()
	item_code = (item_code or "").strip()
	filters = [["docstatus", "in", [0, 1]]]
	if item_code:
		filters.append(["item", "=", item_code])
	or_filters = None
	if query:
		like = f"%{query}%"
		or_filters = [["name", "like", like], ["item", "like", like], ["item_name", "like", like]]
	return frappe.get_all(
		"BOM",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "item", "item_name", "quantity", "is_active", "is_default", "docstatus", "modified"],
		ignore_permissions=True,
		order_by="modified desc",
		limit_page_length=max(1, min(cint(limit or 50), 300)),
	)


@frappe.whitelist()
def get_management_bom_doc(bom_name=""):
	_ensure_management_access()
	bom_name = (bom_name or "").strip()
	if not bom_name:
		frappe.throw(_("BOM name is required."))
	if not frappe.db.exists("BOM", bom_name):
		frappe.throw(_("BOM not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("BOM", bom_name).as_dict()
	item_meta_cache = {}
	for item_row in doc.get("items") or []:
		if not isinstance(item_row, dict):
			continue
		alternatives = _get_item_alternative_options(
			item_row.get("item_code"),
			allow_alternative_item=item_row.get("allow_alternative_item"),
			item_meta_cache=item_meta_cache,
		)
		item_row["alternatives_count"] = len(alternatives)
		item_row["alternatives"] = [
			{
				"alternative_item": option.get("alternative_item") or "",
				"item_name": option.get("item_name") or option.get("alternative_item") or "",
				"stock_uom": option.get("stock_uom") or option.get("uom") or "",
			}
			for option in alternatives
		]
	return doc


@frappe.whitelist()
def save_management_bom(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	bom_name = (parsed_payload.get("name") or parsed_payload.get("bom_name") or "").strip()
	if not bom_name:
		frappe.throw(_("BOM name is required."))
	if not frappe.db.exists("BOM", bom_name):
		frappe.throw(_("BOM not found."), frappe.DoesNotExistError)

	bom_doc = frappe.get_doc("BOM", bom_name)
	if cint(bom_doc.docstatus) == 2:
		frappe.throw(_("Cancelled BOM cannot be edited."))

	for fieldname in ("item", "company", "currency", "rm_cost_as_per", "restaurant_recipe_instruction"):
		if fieldname not in parsed_payload or not _has_column("BOM", fieldname):
			continue
		next_value = parsed_payload.get(fieldname)
		next_value = (next_value or "").strip() if isinstance(next_value, str) else (next_value or "")
		bom_doc.set(fieldname, next_value)

	for fieldname in ("quantity", *NUTRITION_KEY_FIELD_MAP.values()):
		if fieldname not in parsed_payload or not _has_column("BOM", fieldname):
			continue
		bom_doc.set(fieldname, flt(parsed_payload.get(fieldname) or 0))

	for fieldname in ("is_active", "is_default"):
		if fieldname not in parsed_payload or not _has_column("BOM", fieldname):
			continue
		bom_doc.set(fieldname, cint(parsed_payload.get(fieldname)))

	if "items" in parsed_payload:
		raw_rows = parsed_payload.get("items") if isinstance(parsed_payload.get("items"), list) else []
		normalized_items = []
		for row in raw_rows:
			if not isinstance(row, dict):
				continue
			item_code = (row.get("item_code") or "").strip()
			uom = (row.get("uom") or "").strip()
			qty = flt(row.get("qty") or 0)
			if not item_code or not uom or qty <= 0:
				continue

			item_row = {
				"item_code": item_code,
				"qty": qty,
				"uom": uom,
				"conversion_factor": flt(row.get("conversion_factor") or 1) or 1,
			}

			float_fields = {
				"stock_qty",
				"rate",
				"base_rate",
				"amount",
				"base_amount",
				"scrap",
				"restaurant_min_multiplier",
				"restaurant_max_multiplier",
				"restaurant_step_multiplier",
				"restaurant_multiplier_qty",
				"restaurant_extra_when_added",
				*NUTRITION_KEY_FIELD_MAP.values(),
			}
			int_fields = {
				"include_item_in_manufacturing",
				"allow_alternative_item",
				"restaurant_is_included_by_default",
				"restaurant_can_edit_qty",
				"restaurant_can_remove",
				"restaurant_is_required",
				"restaurant_is_editable_qty",
			}
			text_fields = {"description", "source_warehouse", "operation", "restaurant_qty_mode"}
			bom_item_show_field = _bom_item_show_fieldname()

			for fieldname in float_fields:
				if fieldname in row and _has_column("BOM Item", fieldname):
					item_row[fieldname] = flt(row.get(fieldname) or 0)
			for fieldname in int_fields:
				if fieldname in row and _has_column("BOM Item", fieldname):
					item_row[fieldname] = cint(row.get(fieldname))
			if bom_item_show_field:
				show_value = row.get("show_in_website")
				if show_value in (None, ""):
					show_value = row.get("show_in_print")
				if show_value not in (None, ""):
					item_row[bom_item_show_field] = cint(show_value)
			for fieldname in text_fields:
				if fieldname in row and _has_column("BOM Item", fieldname):
					item_row[fieldname] = (row.get(fieldname) or "").strip()

			normalized_items.append(item_row)

		if not normalized_items:
			frappe.throw(_("At least one BOM Item row is required."))

		bom_doc.set("items", [])
		for idx, item_row in enumerate(normalized_items, start=1):
			item_row["idx"] = idx
			bom_doc.append("items", item_row)

	if (
		"restaurant_modifier_rows" in parsed_payload
		and bom_doc.meta.has_field("restaurant_modifier_rows")
		and frappe.db.exists("DocType", "Restaurant BOM Modifier")
	):
		raw_rows = (
			parsed_payload.get("restaurant_modifier_rows")
			if isinstance(parsed_payload.get("restaurant_modifier_rows"), list)
			else []
		)
		normalized_modifier_rows = []
		for row in raw_rows:
			if not isinstance(row, dict):
				continue
			modifier_group = (row.get("modifier_group") or "").strip()
			if not modifier_group:
				continue

			modifier_row = {
				"modifier_group": modifier_group,
				"group_key": (row.get("group_key") or row.get("modifier_group") or "").strip(),
				"group_title": (row.get("group_title") or "").strip(),
				"selection_mode": (row.get("selection_mode") or "single").strip() or "single",
				"modifier_type": (row.get("modifier_type") or "add_on").strip() or "add_on",
				"option_key": (row.get("option_key") or "").strip(),
				"option_label": (row.get("option_label") or "").strip(),
				"option_item": (row.get("option_item") or "").strip(),
				"replacement_for_item": (row.get("replacement_for_item") or "").strip(),
				"alternative_bom": (row.get("alternative_bom") or "").strip(),
				"min_select": cint(row.get("min_select") or 0),
				"max_select": cint(row.get("max_select") or 1),
				"option_qty": flt(row.get("option_qty") or 1) or 1,
				"price_delta": flt(row.get("price_delta") or 0),
				"recipe_multiplier": flt(row.get("recipe_multiplier") or 1) or 1,
				"required": cint(row.get("required")),
				"is_default": cint(row.get("is_default")),
				"is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
			}
			if _has_column("Restaurant BOM Modifier", "sort_order"):
				modifier_row["sort_order"] = cint(row.get("sort_order") or 0)
			normalized_modifier_rows.append(modifier_row)

		bom_doc.set("restaurant_modifier_rows", [])
		for idx, row in enumerate(normalized_modifier_rows, start=1):
			row["idx"] = idx
			bom_doc.append("restaurant_modifier_rows", row)

	# Allow direct save on submitted BOMs instead of forcing draft duplication.
	bom_doc.flags.ignore_validate_update_after_submit = True
	bom_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return frappe.get_doc("BOM", bom_doc.name).as_dict()


@frappe.whitelist()
def update_management_bom_cost(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	bom_name = (parsed_payload.get("bom_name") or parsed_payload.get("name") or "").strip()
	if not bom_name:
		frappe.throw(_("BOM name is required."))
	if not frappe.db.exists("BOM", bom_name):
		frappe.throw(_("BOM not found."), frappe.DoesNotExistError)

	bom_doc = frappe.get_doc("BOM", bom_name)
	if cint(bom_doc.docstatus) == 2:
		frappe.throw(_("Cancelled BOM cannot be updated."))

	if "rm_cost_as_per" in parsed_payload and _has_column("BOM", "rm_cost_as_per"):
		bom_doc.rm_cost_as_per = (parsed_payload.get("rm_cost_as_per") or "").strip() or "Valuation Rate"

	bom_doc.update_cost()

	# Recalculate and sync nutrition data after cost update
	try:
		_upsert_bom_nutrition_fields(bom_doc)
		item_code = (getattr(bom_doc, "item", "") or "").strip()
		if item_code:
			_refresh_item_nutrition_from_bom(item_code)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "restaurant.api.update_management_bom_cost_nutrition_sync")

	frappe.db.commit()
	return frappe.get_doc("BOM", bom_doc.name).as_dict()


@frappe.whitelist()
def list_management_products(search=None, category=None, active_only=0, branch=None, tag=None):
	_ensure_management_access()
	branch = (branch or "").strip()
	search = (search or "").strip()
	category = (category or "").strip()
	tag = (tag or "").strip()
	active_only = cint(active_only)

	image_field = _core_item_image_field()
	category_meta_map = _get_core_category_meta_map()
	subcategory_meta_map = _get_core_subcategory_meta_map()

	filters = {}
	if _has_column("Item", "restaurant_enabled") and active_only:
		filters["restaurant_enabled"] = 1
	if branch and _has_column("Item", "restaurant_branch"):
		filters["restaurant_branch"] = ["in", [branch, ""]]

	if category:
		category_name = frappe.db.get_value(
			"Item Group",
			{
				"restaurant_slug": category,
				**_core_category_filters(is_subcategory=0),
			},
			"name",
		)
		if category_name:
			filters["restaurant_category"] = category_name
		else:
			return {"products": []}

	or_filters = None
	if search:
		like = f"%{search}%"
		or_filters = [["item_name", "like", like], ["restaurant_slug", "like", like]]

	# Tag filter via child table and legacy comma-separated Item field.
	if tag:
		tagged_name_set = set()
		if _item_tag_tables_ready():
			try:
				tagged_items = frappe.db.sql(
					"""
                SELECT DISTINCT parent FROM `tabRestaurant Item Tag Link`
                WHERE tag = %s
            """,
					tag,
					as_dict=True,
				)
				tagged_name_set.update(
					(r.parent or "").strip() for r in tagged_items if (r.parent or "").strip()
				)
			except Exception:
				pass
		if _has_column("Item", "restaurant_item_tags"):
			legacy_rows = frappe.get_all(
				"Item",
				filters={"restaurant_item_tags": ["like", f"%{tag}%"]},
				fields=["name"],
				ignore_permissions=True,
				limit_page_length=1000,
			)
			tagged_name_set.update(
				(row.name or "").strip() for row in legacy_rows if (row.name or "").strip()
			)
		if tagged_name_set:
			filters["name"] = ["in", sorted(tagged_name_set)]
		else:
			return {"products": []}

	item_fields = [
		"name",
		"item_code",
		"item_name",
		"restaurant_slug",
		"restaurant_short_desc",
		"restaurant_base_price",
		"standard_rate",
		"restaurant_enabled",
		"disabled",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_sort_order",
		f"{image_field} as image",
	]
	if _has_column("Item", "custom_snapp_code"):
		item_fields.append("custom_snapp_code")
	if _has_column("Item", "restaurant_item_tags"):
		item_fields.append("restaurant_item_tags")
	if _has_column("Item", "restaurant_coming_soon"):
		item_fields.append("restaurant_coming_soon")
	if _has_column("Item", "restaurant_out_of_stock"):
		item_fields.append("restaurant_out_of_stock")
	if _has_column("Item", "restaurant_packaging_price"):
		item_fields.append("restaurant_packaging_price")

	template_rows = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=item_fields,
		order_by="modified desc",
		ignore_permissions=True,
		limit=500,
	)

	rows = []
	for template_row in template_rows:
		rows.extend(_template_display_row_or_self(template_row, branch=branch))

	stock_by_item = {}
	item_names = [row.get("name") for row in rows if row.get("name")]
	if item_names and frappe.db.exists("DocType", "Bin"):
		bin_rows = frappe.get_all(
			"Bin",
			fields=["item_code", "actual_qty"],
			filters={"item_code": ["in", item_names]},
			ignore_permissions=True,
			limit_page_length=2000,
		)
		for bin_row in bin_rows:
			item_code = bin_row.get("item_code")
			stock_by_item[item_code] = flt(stock_by_item.get(item_code) or 0) + flt(bin_row.get("actual_qty"))

	payload = []
	for row in rows:
		item = _serialize_core_item(
			row,
			category_meta_map=category_meta_map,
			subcategory_meta_map=subcategory_meta_map,
		)
		payload.append(
			{
				**item,
				"name": row.name,
				"item_code": row.item_code or row.name,
				"custom_snapp_code": row.get("custom_snapp_code") or "",
				"is_active": cint(row.restaurant_enabled),
				"is_disabled": cint(row.disabled),
				"out_of_stock": cint(row.get("restaurant_out_of_stock") or 0),
				"packaging_price": flt(row.get("restaurant_packaging_price") or 0),
				"stock_qty": flt(stock_by_item.get(row.name) or 0),
			}
		)
	return {
		"products": payload,
		"stock": {
			"low_threshold": max(
				cint(_get_single_setting("Restaurant Web Settings", "restaurant_low_stock_threshold", 5)), 1
			),
		},
	}


@frappe.whitelist()
def set_management_product_active(item_name, active):
	_ensure_management_access()
	if not item_name:
		frappe.throw(_("Item name is required."))
	if not frappe.db.exists("Item", item_name):
		frappe.throw(_("Item not found."), frappe.DoesNotExistError)
	if not _has_column("Item", "restaurant_enabled"):
		frappe.throw(_("Restaurant enabled field is missing on Item."))

	active = cint(active)
	frappe.db.set_value("Item", item_name, "restaurant_enabled", active, update_modified=True)
	return {
		"status": "success",
		"item_name": item_name,
		"restaurant_enabled": active,
	}


@frappe.whitelist()
def delete_management_product(item_name=None, allow_archive_on_link=1, force_delete=0):
	_ensure_management_access()
	target_item_name = _management_resolve_item_name(item_name)
	if not frappe.db.exists("Item", target_item_name):
		frappe.throw(_("Item not found."), frappe.DoesNotExistError)

	item_doc = frappe.get_doc("Item", target_item_name)
	item_code = (item_doc.get("item_code") or item_doc.name or "").strip()
	item_label = (item_doc.get("item_name") or item_code or target_item_name).strip()

	force_delete = cint(force_delete)
	allow_archive_on_link = cint(allow_archive_on_link)

	try:
		frappe.delete_doc(
			"Item",
			target_item_name,
			ignore_permissions=True,
			force=bool(force_delete),
		)
		frappe.db.commit()
		return {
			"status": "deleted",
			"item_name": target_item_name,
			"item_code": item_code,
			"item_label": item_label,
			"force_delete": force_delete,
		}
	except frappe.LinkExistsError:
		if not allow_archive_on_link:
			frappe.throw(
				_(
					"This item is linked to other documents and cannot be deleted. You can disable it instead."
				),
				frappe.LinkExistsError,
			)

		updates = {"disabled": 1}
		if _has_column("Item", "restaurant_enabled"):
			updates["restaurant_enabled"] = 0
		if _has_column("Item", "show_in_website"):
			updates["show_in_website"] = 0

		frappe.db.set_value("Item", target_item_name, updates, update_modified=True)
		frappe.db.commit()
		return {
			"status": "archived",
			"item_name": target_item_name,
			"item_code": item_code,
			"item_label": item_label,
			"message": _("Item has linked documents and was archived instead of deleted."),
		}


@frappe.whitelist()
def list_management_customers(search=None, date_from=None, date_to=None):
	_ensure_management_access()
	search_text = (search or "").strip().lower()
	
	# Fetch all ERPNext Customers
	fields = ["name", "customer_name"]
	if _has_column("Customer", "mobile_no"):
		fields.append("mobile_no")
	if _has_column("Customer", "customer_primary_mobile"):
		fields.append("customer_primary_mobile")
		
	filters = {"disabled": 0}
	or_filters = {}
	if search_text:
		or_filters = {
			"customer_name": ["like", f"%{search_text}%"],
			"name": ["like", f"%{search_text}%"]
		}
		if _has_column("Customer", "mobile_no"):
			or_filters["mobile_no"] = ["like", f"%{search_text}%"]
		if _has_column("Customer", "customer_primary_mobile"):
			or_filters["customer_primary_mobile"] = ["like", f"%{search_text}%"]

	get_all_kwargs = {
		"doctype": "Customer",
		"fields": fields,
		"filters": filters,
		"ignore_permissions": True,
		"limit_page_length": 5000
	}
	if or_filters:
		get_all_kwargs["or_filters"] = or_filters
	customer_docs = frappe.get_all(**get_all_kwargs)
	
	grouped = {}
	for doc in customer_docs:
		customer_name = (doc.get("customer_name") or doc.get("name") or "").strip()
		mobile = (doc.get("mobile_no") or doc.get("customer_primary_mobile") or "").strip()
		if search_text and search_text not in f"{customer_name} {mobile}".lower():
			continue
		key = f"{customer_name}::{mobile}"
		grouped[key] = {
			"customer_name": customer_name,
			"mobile": mobile,
			"orders_count": 0,
			"total_spent": 0.0,
			"last_order_at": None,
		}

	# Fetch orders for stats
	orders = _management_fetch_web_orders(date_from=date_from, date_to=date_to)
	for order in orders:
		if not _is_revenue_order(order):
			continue

		customer_name = (order.get("customer_name") or "").strip() or "POS Customer"
		mobile = (order.get("mobile") or "").strip()
		if search_text and search_text not in f"{customer_name} {mobile}".lower():
			continue

		key = f"{customer_name}::{mobile}"
		bucket = grouped.setdefault(
			key,
			{
				"customer_name": customer_name,
				"mobile": mobile,
				"orders_count": 0,
				"total_spent": 0.0,
				"last_order_at": None,
			},
		)
		bucket["orders_count"] += 1
		bucket["total_spent"] += flt(order.get("grand_total"))

		created_at = order.get("created_at")
		if created_at:
			try:
				created_dt = get_datetime(created_at)
			except Exception:
				created_dt = None
			previous = bucket.get("last_order_at")
			if created_dt and (not previous or created_dt > previous):
				bucket["last_order_at"] = created_dt

	rows = sorted(
		grouped.values(),
		key=lambda row: (flt(row.get("total_spent")), cint(row.get("orders_count"))),
		reverse=True,
	)
	return {
		"customers": [
			{
				"customer_name": row.get("customer_name") or "",
				"mobile": row.get("mobile") or "",
				"orders_count": cint(row.get("orders_count")),
				"total_spent": flt(row.get("total_spent")),
				"last_order_at": _json_safe_datetime(row.get("last_order_at")),
			}
			for row in rows
		]
	}


def _serialize_management_courier(row, vehicle_count_map=None):
	vehicle_count_map = vehicle_count_map or {}
	return {
		"name": row.get("name") or "",
		"courier_name": (row.get("courier_name") or "").strip(),
		"courier_code": (row.get("courier_code") or "").strip(),
		"mobile": (row.get("mobile") or "").strip(),
		"access_code": (row.get("access_code") or "").strip(),
		"vehicle_type": (row.get("vehicle_type") or "").strip(),
		"plate_number": (row.get("plate_number") or "").strip(),
		"zone": (row.get("zone") or "").strip(),
		"assignment_priority": cint(row.get("assignment_priority") or 0),
		"is_active": cint(row.get("is_active") or 0),
		"notes": (row.get("notes") or "").strip(),
		"vehicle_count": cint(vehicle_count_map.get(row.get("name")) or 0),
		"modified": _json_safe_datetime(row.get("modified")),
	}


def _serialize_management_courier_vehicle(row, courier_map=None):
	courier_map = courier_map or {}
	courier_name = (row.get("courier") or "").strip()
	courier_row = courier_map.get(courier_name) or {}
	return {
		"name": row.get("name") or "",
		"title": (row.get("title") or "").strip(),
		"courier": courier_name,
		"courier_label": (courier_row.get("courier_name") or courier_name).strip(),
		"vehicle_type": (row.get("vehicle_type") or "").strip(),
		"plate_number": (row.get("plate_number") or "").strip(),
		"is_primary": cint(row.get("is_primary") or 0),
		"is_active": cint(row.get("is_active") or 0),
		"notes": (row.get("notes") or "").strip(),
		"modified": _json_safe_datetime(row.get("modified")),
	}


def _management_courier_vehicle_count_map():
	if not frappe.db.exists("DocType", "Restaurant Courier Vehicle"):
		return {}
	rows = frappe.get_all(
		"Restaurant Courier Vehicle",
		fields=["courier"],
		filters={},
		ignore_permissions=True,
		limit_page_length=1000,
	)
	counts = {}
	for row in rows:
		courier_name = (row.get("courier") or "").strip()
		if courier_name:
			counts[courier_name] = cint(counts.get(courier_name) or 0) + 1
	return counts


def _management_courier_summary():
	summary = {
		"courier_count": 0,
		"active_courier_count": 0,
		"vehicle_count": 0,
		"active_vehicle_count": 0,
	}
	if frappe.db.exists("DocType", "Restaurant Courier"):
		summary["courier_count"] = cint(frappe.db.count("Restaurant Courier"))
		summary["active_courier_count"] = cint(frappe.db.count("Restaurant Courier", {"is_active": 1}))
	if frappe.db.exists("DocType", "Restaurant Courier Vehicle"):
		summary["vehicle_count"] = cint(frappe.db.count("Restaurant Courier Vehicle"))
		summary["active_vehicle_count"] = cint(
			frappe.db.count("Restaurant Courier Vehicle", {"is_active": 1})
		)
	return summary


def _list_management_courier_options(active_only=True):
	if not frappe.db.exists("DocType", "Restaurant Courier"):
		return []
	filters = {}
	if active_only:
		filters["is_active"] = 1
	rows = frappe.get_all(
		"Restaurant Courier",
		fields=["name", "courier_name", "courier_code", "mobile", "zone", "assignment_priority"],
		filters=filters,
		order_by="assignment_priority asc, courier_name asc",
		ignore_permissions=True,
		limit_page_length=1000,
	)
	return [
		{
			"name": row.get("name") or "",
			"label": (row.get("courier_name") or "").strip(),
			"courier_code": (row.get("courier_code") or "").strip(),
			"mobile": (row.get("mobile") or "").strip(),
			"zone": (row.get("zone") or "").strip(),
		}
		for row in rows
	]


@frappe.whitelist()
def list_management_couriers(search=None, active_only=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant Courier"):
		return {"couriers": [], "summary": _management_courier_summary()}
	search_text = (search or "").strip().lower()
	filters = {}
	if cint(active_only):
		filters["is_active"] = 1
	fields = [
		"name",
		"courier_name",
		"courier_code",
		"mobile",
		"vehicle_type",
		"plate_number",
		"zone",
		"assignment_priority",
		"is_active",
		"notes",
		"modified",
	]
	if _has_column("Restaurant Courier", "access_code"):
		fields.insert(4, "access_code")
	or_filters = None
	if search_text:
		or_filters = {
			"courier_name": ["like", f"%{search_text}%"],
			"courier_code": ["like", f"%{search_text}%"],
			"mobile": ["like", f"%{search_text}%"],
			"plate_number": ["like", f"%{search_text}%"],
			"zone": ["like", f"%{search_text}%"],
		}
	rows = frappe.get_all(
		"Restaurant Courier",
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by="assignment_priority asc, courier_name asc",
		ignore_permissions=True,
		limit_page_length=1000,
	)
	vehicle_count_map = _management_courier_vehicle_count_map()
	return {
		"couriers": [_serialize_management_courier(row, vehicle_count_map) for row in rows],
		"summary": _management_courier_summary(),
	}


@frappe.whitelist()
def save_management_courier(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))
	docname = (data.get("name") or "").strip()
	if docname and frappe.db.exists("Restaurant Courier", docname):
		doc = frappe.get_doc("Restaurant Courier", docname)
	else:
		doc = frappe.new_doc("Restaurant Courier")
	for fieldname in (
		"courier_name",
		"courier_code",
		"mobile",
		"access_code",
		"vehicle_type",
		"plate_number",
		"zone",
		"assignment_priority",
		"is_active",
		"notes",
	):
		if fieldname in data and (fieldname != "access_code" or hasattr(doc, "access_code")):
			doc.set(fieldname, data.get(fieldname))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success", "courier": _serialize_management_courier(doc.as_dict())}


@frappe.whitelist()
def delete_management_courier(name):
	_ensure_management_access()
	docname = (name or "").strip()
	if not docname or not frappe.db.exists("Restaurant Courier", docname):
		frappe.throw(_("Courier not found."))
	linked_vehicle_count = 0
	if frappe.db.exists("DocType", "Restaurant Courier Vehicle"):
		linked_vehicle_count = cint(
			frappe.db.count("Restaurant Courier Vehicle", {"courier": docname})
		)
	if linked_vehicle_count:
		frappe.throw(_("Delete courier vehicles first."))
	frappe.delete_doc("Restaurant Courier", docname, force=1, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


@frappe.whitelist()
def list_management_courier_vehicles(search=None, courier=None, active_only=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Restaurant Courier Vehicle"):
		return {"vehicles": [], "summary": _management_courier_summary()}
	search_text = (search or "").strip().lower()
	courier_name = (courier or "").strip()
	filters = {}
	if courier_name:
		filters["courier"] = courier_name
	if cint(active_only):
		filters["is_active"] = 1
	or_filters = None
	if search_text:
		or_filters = {
			"title": ["like", f"%{search_text}%"],
			"plate_number": ["like", f"%{search_text}%"],
			"vehicle_type": ["like", f"%{search_text}%"],
		}
	rows = frappe.get_all(
		"Restaurant Courier Vehicle",
		fields=[
			"name",
			"title",
			"courier",
			"vehicle_type",
			"plate_number",
			"is_primary",
			"is_active",
			"notes",
			"modified",
		],
		filters=filters,
		or_filters=or_filters,
		order_by="is_primary desc, modified desc",
		ignore_permissions=True,
		limit_page_length=1000,
	)
	courier_rows = frappe.get_all(
		"Restaurant Courier",
		fields=["name", "courier_name"],
		ignore_permissions=True,
		limit_page_length=1000,
	)
	courier_map = {(row.get("name") or "").strip(): row for row in courier_rows}
	return {
		"vehicles": [_serialize_management_courier_vehicle(row, courier_map) for row in rows],
		"summary": _management_courier_summary(),
	}


@frappe.whitelist()
def save_management_courier_vehicle(payload=None):
	_ensure_management_access()
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid payload format."))
	docname = (data.get("name") or "").strip()
	if docname and frappe.db.exists("Restaurant Courier Vehicle", docname):
		doc = frappe.get_doc("Restaurant Courier Vehicle", docname)
	else:
		doc = frappe.new_doc("Restaurant Courier Vehicle")
	for fieldname in ("courier", "title", "vehicle_type", "plate_number", "is_primary", "is_active", "notes"):
		if fieldname in data:
			doc.set(fieldname, data.get(fieldname))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"status": "success",
		"vehicle": _serialize_management_courier_vehicle(doc.as_dict()),
	}


@frappe.whitelist()
def delete_management_courier_vehicle(name):
	_ensure_management_access()
	docname = (name or "").strip()
	if not docname or not frappe.db.exists("Restaurant Courier Vehicle", docname):
		frappe.throw(_("Courier vehicle not found."))
	frappe.delete_doc("Restaurant Courier Vehicle", docname, force=1, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}


def _management_customer_match(order, mobile="", customer_name=""):
	normalized_mobile = (mobile or "").strip()
	normalized_name = (customer_name or "").strip().lower()
	order_mobile = (order.get("mobile") or "").strip()
	order_name = ((order.get("customer_name") or "").strip() or "POS Customer").lower()

	if normalized_mobile and order_mobile != normalized_mobile:
		return False
	if normalized_name and order_name != normalized_name and not normalized_mobile:
		return False
	return bool(normalized_mobile or normalized_name)


def _management_filter_customer_orders(orders, mobile="", customer_name=""):
	return [
		row
		for row in (orders or [])
		if _management_customer_match(row, mobile=mobile, customer_name=customer_name)
	]


def _management_customer_report_payload(orders, previous_orders, date_from="", date_to=""):
	total_spent = sum(flt(row.get("grand_total")) for row in orders)
	previous_total_spent = sum(flt(row.get("grand_total")) for row in previous_orders)
	orders_count = len(orders)
	previous_orders_count = len(previous_orders)
	avg_ticket = _safe_div(total_spent, orders_count)
	previous_avg_ticket = _safe_div(previous_total_spent, previous_orders_count)

	paid_orders_count = sum(
		1 for row in orders if str(row.get("payment_status") or "").strip().lower() == "paid"
	)
	unpaid_orders_count = max(orders_count - paid_orders_count, 0)
	paid_rate = round(_safe_div(paid_orders_count * 100.0, orders_count or 1), 2)
	previous_paid_orders_count = sum(
		1 for row in previous_orders if str(row.get("payment_status") or "").strip().lower() == "paid"
	)
	previous_paid_rate = round(_safe_div(previous_paid_orders_count * 100.0, previous_orders_count or 1), 2)

	monthly_grouped = defaultdict(lambda: {"sales": 0.0, "orders": 0})
	for row in orders:
		created_at = row.get("created_at")
		try:
			month_key = str(getdate(created_at))[:7]
		except Exception:
			continue
		monthly_grouped[month_key]["sales"] += flt(row.get("grand_total") or 0)
		monthly_grouped[month_key]["orders"] += 1

	month_keys = sorted(monthly_grouped.keys())
	monthly_labels = month_keys
	monthly_sales = [round(flt(monthly_grouped[key]["sales"]), 2) for key in month_keys]
	monthly_orders = [cint(monthly_grouped[key]["orders"]) for key in month_keys]

	channel_grouped = defaultdict(lambda: {"sales": 0.0, "orders": 0})
	payment_grouped = defaultdict(int)
	product_grouped = defaultdict(lambda: {"qty": 0.0, "amount": 0.0})
	for row in orders:
		channel = (row.get("channel") or "unknown").strip() or "unknown"
		payment_status = (row.get("payment_status") or "unknown").strip() or "unknown"
		channel_grouped[channel]["sales"] += flt(row.get("grand_total") or 0)
		channel_grouped[channel]["orders"] += 1
		payment_grouped[payment_status] += 1

		for item in row.get("items") or []:
			product_title = (item.get("title") or "").strip() or "بدون نام"
			product_grouped[product_title]["qty"] += flt(item.get("qty") or 0)
			product_grouped[product_title]["amount"] += flt(item.get("line_total") or 0)

	channel_rows = sorted(
		[
			{
				"channel": channel,
				"orders": cint(values.get("orders") or 0),
				"sales": round(flt(values.get("sales") or 0), 2),
			}
			for channel, values in channel_grouped.items()
		],
		key=lambda row: row.get("sales") or 0,
		reverse=True,
	)

	payment_rows = sorted(
		[
			{"payment_status": key or "unknown", "orders": cint(value or 0)}
			for key, value in payment_grouped.items()
		],
		key=lambda row: row.get("orders") or 0,
		reverse=True,
	)

	product_rows = sorted(
		[
			{
				"product_title": title,
				"qty": round(flt(values.get("qty") or 0), 3),
				"amount": round(flt(values.get("amount") or 0), 2),
			}
			for title, values in product_grouped.items()
		],
		key=lambda row: row.get("amount") or 0,
		reverse=True,
	)[:20]

	recent_orders_rows = [
		{
			"order_code": row.get("order_code") or row.get("name") or "",
			"status": row.get("status") or "",
			"payment_status": row.get("payment_status") or "",
			"channel": row.get("channel") or "",
			"grand_total": flt(row.get("grand_total") or 0),
			"created_at": row.get("created_at") or "",
		}
		for row in orders[:40]
	]

	charts = []
	if monthly_labels:
		charts.append(
			{
				"key": "monthly-sales",
				"title": _("Monthly Purchase Trend"),
				"subtitle": _("Customer monthly sales and order count"),
				"type": "line",
				"unit": "money",
				"labels": monthly_labels,
				"series": [
					{
						"key": "sales",
						"label": _("Sales"),
						"color": "#0D9488",
						"values": monthly_sales,
					},
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#2563EB",
						"values": monthly_orders,
					},
				],
			}
		)
	if payment_rows:
		charts.append(
			{
				"key": "payment-status",
				"title": _("Payment Status Distribution"),
				"subtitle": _("How many orders are paid or unpaid"),
				"type": "bar",
				"unit": "count",
				"labels": [row.get("payment_status") or "" for row in payment_rows],
				"series": [
					{
						"key": "orders",
						"label": _("Orders"),
						"color": "#334155",
						"values": [cint(row.get("orders") or 0) for row in payment_rows],
					}
				],
			}
		)

	return {
		"meta": {
			"date_from": date_from,
			"date_to": date_to,
			"compare_mode": "previous_window",
		},
		"kpis": [
			_bi_kpi("customer_sales", _("Total Purchase"), total_spent, "money", previous_total_spent),
			_bi_kpi("customer_orders", _("Orders Count"), orders_count, "count", previous_orders_count),
			_bi_kpi("customer_avg_ticket", _("Average Ticket"), avg_ticket, "money", previous_avg_ticket),
			_bi_kpi("customer_paid_rate", _("Paid Orders Rate"), paid_rate, "percent", previous_paid_rate),
		],
		"charts": charts,
		"tables": [
			{
				"key": "recent-orders",
				"title": _("Recent Orders"),
				"columns": _table_columns_from_rows(recent_orders_rows),
				"rows": recent_orders_rows,
			},
			{
				"key": "top-products",
				"title": _("Top Purchased Products"),
				"columns": _table_columns_from_rows(product_rows),
				"rows": product_rows,
			},
			{
				"key": "channels",
				"title": _("Channels Summary"),
				"columns": _table_columns_from_rows(channel_rows),
				"rows": channel_rows,
			},
		],
		"insights": [
			{
				"type": "info",
				"text": _("Paid orders: {0} | Unpaid orders: {1}").format(
					cint(paid_orders_count), cint(unpaid_orders_count)
				),
			},
			{
				"type": "info",
				"text": _("Date window: {0} to {1}").format(date_from or "-", date_to or "-"),
			},
		],
	}


@frappe.whitelist()
def get_management_customer_detail(mobile=None, customer_name=None, date_from=None, date_to=None):
	_ensure_management_access()
	normalized_mobile = (mobile or "").strip()
	normalized_customer_name = (customer_name or "").strip()
	if not normalized_mobile and not normalized_customer_name:
		frappe.throw(_("Customer mobile or customer name is required."))

	orders = _management_filter_customer_orders(
		_management_fetch_web_orders(date_from=date_from, date_to=date_to),
		mobile=normalized_mobile,
		customer_name=normalized_customer_name,
	)
	orders = [row for row in orders if _is_revenue_order(row)]

	start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
	prev_start, prev_end = _management_previous_window(start_date, end_date)
	previous_orders = _management_filter_customer_orders(
		_management_fetch_web_orders(date_from=prev_start, date_to=prev_end),
		mobile=normalized_mobile,
		customer_name=normalized_customer_name,
	)
	previous_orders = [row for row in previous_orders if _is_revenue_order(row)]

	sorted_orders = sorted(
		orders,
		key=lambda row: _json_safe_datetime(row.get("created_at")) or "",
		reverse=True,
	)

	resolved_customer_name = (
		normalized_customer_name
		or (sorted_orders[0].get("customer_name") if sorted_orders else "")
		or "مشتری"
	)
	resolved_mobile = normalized_mobile or (sorted_orders[0].get("mobile") if sorted_orders else "") or ""

	first_order_at = ""
	last_order_at = ""
	if sorted_orders:
		last_order_at = sorted_orders[0].get("created_at") or ""
		first_order_at = sorted_orders[-1].get("created_at") or ""

	total_spent = sum(flt(row.get("grand_total") or 0) for row in sorted_orders)
	orders_count = len(sorted_orders)
	avg_ticket = round(_safe_div(total_spent, orders_count), 2)
	paid_orders_count = sum(
		1 for row in sorted_orders if str(row.get("payment_status") or "").strip().lower() == "paid"
	)
	unpaid_orders_count = max(orders_count - paid_orders_count, 0)
	days_since_last_order = 0
	if last_order_at:
		try:
			days_since_last_order = cint((now_datetime().date() - getdate(last_order_at)).days)
		except Exception:
			days_since_last_order = 0

	report_payload = _management_customer_report_payload(
		sorted_orders,
		previous_orders,
		date_from=start_date,
		date_to=end_date,
	)

	return {
		"customer": {
			"customer_name": resolved_customer_name,
			"mobile": resolved_mobile,
			"orders_count": orders_count,
			"total_spent": flt(total_spent),
			"avg_ticket": flt(avg_ticket),
			"paid_orders_count": cint(paid_orders_count),
			"unpaid_orders_count": cint(unpaid_orders_count),
			"first_order_at": first_order_at,
			"last_order_at": last_order_at,
			"days_since_last_order": cint(days_since_last_order),
		},
		"orders": sorted_orders,
		"report": report_payload,
	}


@frappe.whitelist()
def get_management_report_sales_summary(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	summary = _build_sales_summary(orders)
	rows = [
		{"metric": "Total Sales", "value": summary["total_sales"]},
		{"metric": "Total Orders", "value": summary["total_orders"]},
		{"metric": "Average Ticket", "value": summary["avg_ticket"]},
		{"metric": "Items Sold", "value": summary["total_items"]},
	]
	return _compose_management_report(
		"sales-summary",
		"Sales Summary",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_sales_trend(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_daily_trend(orders)
	summary = {"days": len(rows), "total_sales": sum(flt(row["sales"]) for row in rows)}
	return _compose_management_report(
		"sales-trend",
		"Sales Trend",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_sales_hourly(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_hourly_trend(orders)
	summary = {
		"total_sales": sum(flt(row["sales"]) for row in rows),
		"total_orders": sum(cint(row["orders"]) for row in rows),
	}
	return _compose_management_report(
		"sales-hourly",
		"Hourly Sales",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_top_products(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_top_products(orders, limit=20)
	summary = {
		"products_count": len(rows),
		"total_sales": sum(flt(row["amount"]) for row in rows),
	}
	return _compose_management_report(
		"top-products",
		"Top Products",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_product_mix(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	payload = _build_product_mix_associations(orders, limit=80, min_pair_orders=2, min_base_orders=2)
	summary = {
		"rules_count": len(payload),
		"unique_products": len({row.get("product_title") for row in payload if row.get("product_title")}),
		"avg_confidence_percent": round(
			_safe_div(sum(flt(row.get("confidence_percent")) for row in payload), len(payload) or 1),
			2,
		),
	}
	return _compose_management_report(
		"product-mix",
		"Product Mix",
		summary,
		payload,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_order_status(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_status_rows(orders)
	summary = {"total_orders": sum(cint(row["orders"]) for row in rows)}
	return _compose_management_report(
		"order-status",
		"Order Status",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_channel_split(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_channel_rows(orders)
	summary = {"channels": len(rows), "total_sales": sum(flt(row["sales"]) for row in rows)}
	return _compose_management_report(
		"channel-split",
		"Channel Split",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_cashier_performance(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_cashier_rows(orders)
	summary = {"cashiers": len(rows), "total_sales": sum(flt(row["sales"]) for row in rows)}
	return _compose_management_report(
		"cashier-performance",
		"Cashier Performance",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_cancellations(date_from=None, date_to=None):
	_ensure_management_access()
	orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="all")
	rows = _build_cancellation_rows(orders)
	summary = {
		"cancelled_orders": len(rows),
		"cancelled_amount": sum(flt(row["amount"]) for row in rows),
	}
	return _compose_management_report(
		"cancellations",
		"Cancellations",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="all",
		orders=orders,
	)


@frappe.whitelist()
def get_management_report_modifier_usage(date_from=None, date_to=None):
	_ensure_management_access()
	web_orders = _management_collect_orders(date_from=date_from, date_to=date_to, source="web")
	rows = _build_modifier_usage_rows(web_orders)
	summary = {"modifiers": len(rows), "total_usage": sum(cint(row["usage_count"]) for row in rows)}
	return _compose_management_report(
		"modifier-usage",
		"Modifier Usage",
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		source="web",
		orders=web_orders,
	)


@frappe.whitelist()
def get_management_bi_report(report_key, date_from=None, date_to=None, compare_mode="previous_window"):
	_ensure_management_access()
	normalized_key = (report_key or "").strip().lower()
	if not normalized_key:
		frappe.throw(_("Report key is required."))

	dispatch = {
		"sales-summary": get_management_report_sales_summary,
		"sales-trend": get_management_report_sales_trend,
		"sales-hourly": get_management_report_sales_hourly,
		"top-products": get_management_report_top_products,
		"product-mix": get_management_report_product_mix,
		"order-status": get_management_report_order_status,
		"channel-split": get_management_report_channel_split,
		"cashier-performance": get_management_report_cashier_performance,
		"cancellations": get_management_report_cancellations,
		"modifier-usage": get_management_report_modifier_usage,
		"category-sales": get_management_report_category_sales,
		"table-sales": get_management_report_table_sales,
		"payment-methods": get_management_report_payment_methods,
		"product-sales": get_management_report_product_sales,
		"shift-sales": get_management_report_shift_sales,
		"inventory-valuation": get_management_report_inventory_valuation,
		"stock-movements": get_management_report_stock_movements,
		"inventory-waste": get_management_report_inventory_waste,
		"customer-analytics": get_management_report_customer_analytics,
		"campaign-performance": get_management_report_campaign_performance,
		"wallet-summary": get_management_report_wallet_summary,
		"credit-transactions": get_management_report_credit_transactions,
		"care-feedback": get_management_report_care_feedback,
		"survey-analytics": get_management_report_survey_analytics,
		"courier-performance": get_management_report_courier_performance,
		"waiter-performance": get_management_report_waiter_performance,
		"kitchen-performance": get_management_report_kitchen_performance,
		"profit-loss": get_management_report_profit_loss,
		"breakeven": get_management_report_breakeven,
		"menu-engineering": get_management_report_menu_engineering,
		"tax-reconciliation": get_management_report_tax_reconciliation,
		"branch-performance": get_management_report_branch_performance,
		"vendor-sales": get_management_report_vendor_sales,
		"receipt-payment-balance": get_management_report_receipt_payment_balance,
	}
	fn = dispatch.get(normalized_key)
	if not fn:
		frappe.throw(_("Invalid report key: {0}").format(normalized_key))
	payload = fn(date_from=date_from, date_to=date_to)
	if isinstance(payload, dict):
		payload.setdefault("meta", {})
		payload["meta"]["compare_mode"] = (
			compare_mode or "previous_window"
		).strip().lower() or "previous_window"
	return payload


TABLE_REQUEST_TYPES = {"waiter", "sauce", "drink", "other"}
TABLE_ORDER_ACTIVE_STATUSES = {"pending", "confirmed", "served"}
TABLE_ORDER_BILLING_STATUSES = {"confirmed", "served", "paid"}
TABLE_SESSION_META_PREFIX = "__table_session_meta__:"


def _ensure_table_service_ready():
	required = [
		"Restaurant Table",
		"Restaurant Table Session",
		"Restaurant Table Menu Item",
		"Restaurant Table Order",
		"Restaurant Table Order Item",
		"Restaurant Table Request",
	]
	missing = [doctype for doctype in required if not frappe.db.exists("DocType", doctype)]
	if missing:
		frappe.throw(_("Missing DocTypes: {0}").format(", ".join(missing)))


def _get_table_by_token(qr_token):
	token = (qr_token or "").strip()
	if not token:
		frappe.throw(_("QR token is required."))

	table_name = frappe.db.get_value(
		"Restaurant Table",
		{
			"qr_code_token": token,
			"is_active": 1,
		},
		"name",
	)
	if not table_name:
		frappe.throw(_("Table not found for this QR token."), frappe.DoesNotExistError)
	return frappe.get_doc("Restaurant Table", table_name)


def _get_or_create_active_table_session(table_name):
	active_session = frappe.db.get_value(
		"Restaurant Table Session",
		{"table": table_name, "status": "active"},
		"name",
	)
	if active_session:
		return frappe.get_doc("Restaurant Table Session", active_session)

	doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Session",
			"table": table_name,
			"status": "active",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def _resolve_active_table_session_name(table_name, preferred_session=None):
	candidate = (preferred_session or "").strip()
	if candidate:
		candidate_row = frappe.db.get_value(
			"Restaurant Table Session",
			candidate,
			["name", "status", "table"],
			as_dict=True,
		)
		if (
			candidate_row
			and candidate_row.get("status") == "active"
			and candidate_row.get("table") == table_name
		):
			return candidate_row.get("name")

	return frappe.db.get_value(
		"Restaurant Table Session",
		{"table": table_name, "status": "active"},
		"name",
	)


def _extract_table_session_meta(note_value):
	raw_note = (note_value or "").strip()
	if not raw_note:
		return {}

	if raw_note.startswith(TABLE_SESSION_META_PREFIX):
		raw_note = raw_note[len(TABLE_SESSION_META_PREFIX) :].strip()

	parsed = _parse_json(raw_note, {})
	if not isinstance(parsed, dict):
		return {}

	return parsed


def _sanitize_table_session_customer(meta):
	payload = meta or {}
	customer_name = (payload.get("customer_name") or "").strip()
	customer_mobile = (payload.get("customer_mobile") or payload.get("mobile") or "").strip()
	customer_type = (payload.get("customer_type") or "").strip().lower()
	guest_count = max(cint(payload.get("guest_count") or 0), 0)

	return {
		"customer_name": customer_name,
		"customer_mobile": customer_mobile,
		"customer_type": customer_type,
		"guest_count": guest_count,
	}


def _encode_table_session_meta(meta):
	payload = _sanitize_table_session_customer(meta)
	serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
	return f"{TABLE_SESSION_META_PREFIX}{serialized}"


def _serialize_table(table_doc):
	return {
		"name": table_doc.name,
		"table_number": table_doc.table_number,
		"status": table_doc.status,
		"location": table_doc.location or "",
		"qr_code_token": table_doc.qr_code_token,
	}


def _serialize_table_menu_items():
	rows = frappe.get_all(
		"Restaurant Table Menu Item",
		filters={"is_available": 1},
		fields=[
			"name",
			"item_name",
			"category",
			"price",
			"image",
			"description",
			"prep_time_mins",
			"sort_order",
		],
		order_by="category asc, sort_order asc, item_name asc",
		ignore_permissions=True,
	)

	categories = {}
	for row in rows:
		category = (row.category or _("General")).strip() or _("General")
		if category not in categories:
			categories[category] = []
		categories[category].append(
			{
				"name": row.name,
				"title": row.item_name,
				"category": category,
				"price": flt(row.price),
				"image": row.image or "",
				"description": row.description or "",
				"prep_time_mins": cint(row.prep_time_mins or 0),
			}
		)

	return {
		"categories": [
			{"name": name, "items": items} for name, items in sorted(categories.items(), key=lambda d: d[0])
		],
		"items": rows,
	}


def _serialize_table_session(session_doc):
	customer_payload = _sanitize_table_session_customer(_extract_table_session_meta(session_doc.note))
	return {
		"name": session_doc.name,
		"table": session_doc.table,
		"status": session_doc.status,
		"opened_at": _json_safe_datetime(session_doc.opened_at),
		"closed_at": _json_safe_datetime(session_doc.closed_at),
		"total_confirmed_amount": flt(session_doc.total_confirmed_amount),
		**customer_payload,
	}


def _menu_item_titles(item_codes):
	if not item_codes:
		return {}
	rows = frappe.get_all(
		"Restaurant Table Menu Item",
		filters={"name": ["in", list(item_codes)]},
		fields=["name", "item_name"],
		ignore_permissions=True,
	)
	return {row.name: row.item_name for row in rows}


def _serialize_table_order(order_doc, title_map=None):
	title_map = title_map or {}
	item_codes = {row.menu_item for row in (order_doc.items or []) if row.menu_item}
	if item_codes and not title_map:
		title_map = _menu_item_titles(item_codes)

	return {
		"name": order_doc.name,
		"order_code": order_doc.order_code,
		"session": order_doc.session,
		"table": order_doc.table,
		"status": order_doc.status,
		"created_at": _json_safe_datetime(order_doc.created_at),
		"confirmed_at": _json_safe_datetime(order_doc.confirmed_at),
		"served_at": _json_safe_datetime(order_doc.served_at),
		"paid_at": _json_safe_datetime(order_doc.paid_at),
		"subtotal": flt(order_doc.subtotal),
		"grand_total": flt(order_doc.grand_total),
		"note": order_doc.note or "",
		"is_editable": order_doc.status == "pending",
		"items": [
			{
				"row_name": row.name,
				"menu_item": row.menu_item,
				"menu_item_title": title_map.get(row.menu_item) or row.menu_item,
				"quantity": flt(row.quantity),
				"price_at_time": flt(row.price_at_time),
				"line_total": flt(row.line_total),
				"note": row.note or "",
			}
			for row in (order_doc.items or [])
		],
	}


def _serialize_table_request(request_doc):
	return {
		"name": request_doc.name,
		"session": request_doc.session,
		"table": request_doc.table,
		"request_type": request_doc.request_type,
		"description": request_doc.description or "",
		"status": request_doc.status,
		"created_at": _json_safe_datetime(request_doc.created_at),
		"resolved_at": _json_safe_datetime(request_doc.resolved_at),
		"handled_by": request_doc.handled_by or "",
	}


def _get_session_order_docs(session_name):
	rows = frappe.get_all(
		"Restaurant Table Order",
		fields=["name"],
		filters={"session": session_name},
		order_by="creation asc",
		ignore_permissions=True,
	)
	return [frappe.get_doc("Restaurant Table Order", row.name) for row in rows]


def _get_session_request_docs(session_name):
	rows = frappe.get_all(
		"Restaurant Table Request",
		fields=["name"],
		filters={"session": session_name},
		order_by="creation asc",
		ignore_permissions=True,
	)
	return [frappe.get_doc("Restaurant Table Request", row.name) for row in rows]


def _refresh_session_total_confirmed_amount(session_name):
	rows = frappe.get_all(
		"Restaurant Table Order",
		fields=["grand_total"],
		filters={
			"session": session_name,
			"status": ["in", list(TABLE_ORDER_BILLING_STATUSES)],
		},
		ignore_permissions=True,
	)
	total = sum(flt(row.get("grand_total") or 0) for row in (rows or []))
	frappe.db.set_value(
		"Restaurant Table Session",
		session_name,
		"total_confirmed_amount",
		total,
		update_modified=False,
	)
	return total


def _table_session_state_payload(session_doc):
	orders = _get_session_order_docs(session_doc.name)
	requests = _get_session_request_docs(session_doc.name)
	item_codes = {row.menu_item for order in orders for row in (order.items or []) if row.menu_item}
	title_map = _menu_item_titles(item_codes)

	return {
		"session": _serialize_table_session(session_doc),
		"orders": [_serialize_table_order(doc, title_map=title_map) for doc in orders],
		"requests": [_serialize_table_request(doc) for doc in requests],
		"counts": {
			"pending_orders": sum(1 for doc in orders if doc.status == "pending"),
			"confirmed_orders": sum(1 for doc in orders if doc.status == "confirmed"),
			"served_orders": sum(1 for doc in orders if doc.status == "served"),
			"paid_orders": sum(1 for doc in orders if doc.status == "paid"),
			"pending_requests": sum(1 for doc in requests if doc.status == "pending"),
		},
		"totals": {
			"session_grand_total": sum(flt(doc.grand_total) for doc in orders if doc.status != "cancelled"),
			"session_confirmed_total": _refresh_session_total_confirmed_amount(session_doc.name),
		},
	}


def _resolve_menu_item_ref(raw_ref):
	ref = (raw_ref or "").strip()
	if not ref:
		return None

	if frappe.db.exists("Restaurant Table Menu Item", ref):
		return ref

	return frappe.db.get_value(
		"Restaurant Table Menu Item",
		{"item_name": ref},
		"name",
	)


def _normalize_table_selector(value):
	text = (value or "").strip().lower()
	text = text.replace(" ", "")
	text = text.replace("میز", "")
	text = text.replace("table", "")
	return text


def _resolve_table_name(table_name):
	raw = (table_name or "").strip()
	if not raw:
		return ""

	if frappe.db.exists("Restaurant Table", raw):
		return raw

	by_number = frappe.db.get_value(
		"Restaurant Table",
		{"table_number": raw, "is_active": 1},
		"name",
	)
	if by_number:
		return by_number

	normalized = _normalize_table_selector(raw)
	if not normalized:
		return ""

	rows = frappe.get_all(
		"Restaurant Table",
		fields=["name", "table_number"],
		filters={"is_active": 1},
		ignore_permissions=True,
	)
	for row in rows:
		table_number = (row.table_number or "").strip()
		if _normalize_table_selector(table_number) == normalized:
			return row.name
	return ""


def _resolve_or_create_table_menu_item_from_pos(raw_item):
	raw_item = raw_item or {}

	direct_ref = (raw_item.get("menu_item") or "").strip()
	if direct_ref and frappe.db.exists("Restaurant Table Menu Item", direct_ref):
		return frappe.get_doc("Restaurant Table Menu Item", direct_ref)

	item_code = (raw_item.get("item_code") or raw_item.get("erpnext_item") or "").strip()
	if item_code:
		by_erp_item = frappe.db.get_value(
			"Restaurant Table Menu Item",
			{"erpnext_item": item_code},
			"name",
		)
		if by_erp_item:
			return frappe.get_doc("Restaurant Table Menu Item", by_erp_item)

	title = (
		raw_item.get("title")
		or raw_item.get("item_name")
		or raw_item.get("menu_item_title")
		or item_code
		or _("POS Item")
	)
	title = (title or "").strip() or _("POS Item")

	by_title = frappe.db.get_value(
		"Restaurant Table Menu Item",
		{"item_name": title},
		"name",
	)
	if by_title:
		return frappe.get_doc("Restaurant Table Menu Item", by_title)

	category = (raw_item.get("category") or _("POS")).strip() or _("POS")
	unit_price = max(flt(raw_item.get("unit_price") or raw_item.get("price") or 0), 0)

	menu_doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Menu Item",
			"item_name": title,
			"category": category,
			"price": unit_price,
			"is_available": 1,
			"prep_time_mins": 10,
		}
	)

	if item_code and frappe.db.exists("Item", item_code):
		menu_doc.erpnext_item = item_code

	menu_doc.insert(ignore_permissions=True)
	return menu_doc


def _normalize_qr_svg_content(qr_svg):
	if isinstance(qr_svg, str):
		raw = qr_svg.encode("utf-8")
	else:
		raw = bytes(qr_svg)

	stripped = raw.strip()
	if stripped.startswith(b"<"):
		return stripped

	try:
		decoded = b64decode(stripped, validate=True)
		if decoded.strip().startswith(b"<"):
			return decoded.strip()
	except Exception:
		pass

	return stripped


@frappe.whitelist(allow_guest=True)
def table_boot(qr_token):
	_ensure_table_service_ready()
	table_doc = _get_table_by_token(qr_token)
	session_doc = _get_or_create_active_table_session(table_doc.name)

	return {
		"table": _serialize_table(table_doc),
		"menu": _serialize_table_menu_items(),
		**_table_session_state_payload(session_doc),
	}


@frappe.whitelist(allow_guest=True)
def get_table_qr_svg(table=None, qr_token=None):
	_ensure_table_service_ready()

	table_doc = None
	if table:
		table_name = (table or "").strip()
		if not frappe.db.exists("Restaurant Table", table_name):
			frappe.throw(_("Table not found."), frappe.DoesNotExistError)
		table_doc = frappe.get_doc("Restaurant Table", table_name)
	else:
		table_doc = _get_table_by_token(qr_token)

	target_url = table_doc.qr_target_url or frappe.utils.get_url(f"/table/{table_doc.qr_code_token}")
	qr_svg = get_qr_svg_code(target_url)
	content = _normalize_qr_svg_content(qr_svg)

	frappe.response["type"] = "binary"
	frappe.response["filecontent"] = content
	frappe.response["filename"] = f"restaurant-table-{table_doc.table_number}-qr.svg"
	frappe.response["display_content_as"] = "inline"


@frappe.whitelist(allow_guest=True)
def get_table_menu(qr_token):
	_ensure_table_service_ready()
	table_doc = _get_table_by_token(qr_token)
	session_doc = _get_or_create_active_table_session(table_doc.name)
	return {
		"table": _serialize_table(table_doc),
		"session": _serialize_table_session(session_doc),
		"menu": _serialize_table_menu_items(),
	}


@frappe.whitelist(allow_guest=True)
def place_table_order(qr_token, items, note=None):
	_ensure_table_service_ready()
	table_doc = _get_table_by_token(qr_token)
	session_doc = _get_or_create_active_table_session(table_doc.name)

	rows = _parse_json(items, [])
	if not isinstance(rows, list) or not rows:
		frappe.throw(_("At least one menu item is required."))

	order_doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Order",
			"session": session_doc.name,
			"table": table_doc.name,
			"status": "pending",
			"note": (note or "").strip(),
			"items": [],
		}
	)

	for raw in rows:
		if not isinstance(raw, dict):
			continue

		menu_item_ref = _resolve_menu_item_ref(
			raw.get("menu_item") or raw.get("menu_item_id") or raw.get("name")
		)
		if not menu_item_ref:
			frappe.throw(_("Invalid menu item: {0}").format(raw.get("menu_item") or raw.get("name") or "?"))

		menu_doc = frappe.get_doc("Restaurant Table Menu Item", menu_item_ref)
		if not cint(menu_doc.is_available):
			frappe.throw(_("Menu item is not available: {0}").format(menu_doc.item_name))

		qty = max(flt(raw.get("quantity") or raw.get("qty") or 1), 1)
		price = flt(menu_doc.price or 0)
		order_doc.append(
			"items",
			{
				"menu_item": menu_doc.name,
				"quantity": qty,
				"price_at_time": price,
				"note": (raw.get("note") or "").strip(),
			},
		)

	if not order_doc.items:
		frappe.throw(_("No valid menu item was provided."))

	order_doc.insert(ignore_permissions=True)
	state = _table_session_state_payload(session_doc)
	return {
		"status": "success",
		"order": _serialize_table_order(order_doc),
		**state,
	}


@frappe.whitelist()
def create_management_table_order_from_pos(table_name, items, note=None):
	_ensure_management_access()
	_ensure_table_service_ready()

	resolved_table_name = _resolve_table_name(table_name)
	if not resolved_table_name:
		frappe.throw(_("Table not found."), frappe.DoesNotExistError)

	table_doc = frappe.get_doc("Restaurant Table", resolved_table_name)
	if not cint(table_doc.is_active):
		frappe.throw(_("Selected table is not active."))

	session_doc = _get_or_create_active_table_session(table_doc.name)

	rows = _parse_json(items, [])
	if not isinstance(rows, list) or not rows:
		frappe.throw(_("At least one table item is required."))

	order_doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Order",
			"session": session_doc.name,
			"table": table_doc.name,
			"status": "confirmed",
			"note": (note or "").strip(),
			"items": [],
		}
	)

	for raw in rows:
		if not isinstance(raw, dict):
			continue

		menu_doc = _resolve_or_create_table_menu_item_from_pos(raw)
		qty = max(flt(raw.get("qty") or raw.get("quantity") or 1), 1)
		unit_price = max(flt(raw.get("unit_price") or menu_doc.price or 0), 0)
		item_note = (raw.get("note") or "").strip()

		order_doc.append(
			"items",
			{
				"menu_item": menu_doc.name,
				"quantity": qty,
				"price_at_time": unit_price,
				"note": item_note,
			},
		)

	if not order_doc.items:
		frappe.throw(_("No valid table item was provided."))

	order_doc.insert(ignore_permissions=True)
	state = _table_session_state_payload(session_doc)
	return {
		"status": "success",
		"table": _serialize_table(table_doc),
		"order": _serialize_table_order(order_doc),
		**state,
	}


@frappe.whitelist(allow_guest=True)
def create_table_request(qr_token, request_type, description=None):
	_ensure_table_service_ready()
	table_doc = _get_table_by_token(qr_token)
	session_doc = _get_or_create_active_table_session(table_doc.name)

	req_type = (request_type or "").strip().lower()
	if req_type not in TABLE_REQUEST_TYPES:
		frappe.throw(_("Invalid request type."))

	request_doc = frappe.get_doc(
		{
			"doctype": "Restaurant Table Request",
			"session": session_doc.name,
			"table": table_doc.name,
			"request_type": req_type,
			"description": (description or "").strip(),
			"status": "pending",
		}
	)
	request_doc.insert(ignore_permissions=True)

	return {
		"status": "success",
		"request": _serialize_table_request(request_doc),
		"session": _serialize_table_session(session_doc),
	}


@frappe.whitelist(allow_guest=True)
def get_table_session_state(qr_token):
	_ensure_table_service_ready()
	table_doc = _get_table_by_token(qr_token)
	session_doc = _get_or_create_active_table_session(table_doc.name)
	return {
		"table": _serialize_table(table_doc),
		**_table_session_state_payload(session_doc),
	}


@frappe.whitelist()
def get_table_overview():
	_ensure_table_service_ready()
	tables = frappe.get_all(
		"Restaurant Table",
		fields=["name", "table_number", "status", "location", "active_session", "is_active"],
		filters={"is_active": 1},
		order_by="table_number asc",
		ignore_permissions=True,
	)

	payload = []
	for table in tables:
		active_session = _resolve_active_table_session_name(table.name, table.active_session)
		pending_orders = 0
		pending_requests = 0
		confirmed_total = 0.0
		active_since = None
		occupied_minutes = 0
		session_customer = _sanitize_table_session_customer({})
		if active_session:
			pending_orders = frappe.db.count(
				"Restaurant Table Order",
				filters={"session": active_session, "status": "pending"},
			)
			pending_requests = frappe.db.count(
				"Restaurant Table Request",
				filters={"session": active_session, "status": "pending"},
			)
			confirmed_total = flt(
				frappe.db.get_value("Restaurant Table Session", active_session, "total_confirmed_amount") or 0
			)
			session_opened_at = frappe.db.get_value("Restaurant Table Session", active_session, "opened_at")
			session_note = frappe.db.get_value("Restaurant Table Session", active_session, "note") or ""
			session_customer = _sanitize_table_session_customer(_extract_table_session_meta(session_note))
			first_order_created_at = frappe.db.sql(
				"""
                select min(created_at)
                from `tabRestaurant Table Order`
                where `session`=%s
                """,
				(active_session,),
			)
			first_order_at = first_order_created_at[0][0] if first_order_created_at else None
			active_since = first_order_at or session_opened_at
			if active_since:
				try:
					elapsed = now_datetime() - get_datetime(active_since)
					occupied_minutes = max(int(elapsed.total_seconds() // 60), 0)
				except Exception:
					occupied_minutes = 0

		base_status = "occupied" if active_session else "empty"
		has_attention = bool(pending_orders or pending_requests)
		display_status = "waiting" if (base_status == "occupied" and has_attention) else base_status

		# Keep table status/session in sync with real active sessions to avoid stale "occupied" tables.
		desired_status_for_doc = "occupied" if active_session else "empty"
		desired_active_session = active_session or ""
		if (table.status or "").strip().lower() != desired_status_for_doc or (
			table.active_session or ""
		) != desired_active_session:
			frappe.db.set_value(
				"Restaurant Table",
				table.name,
				{
					"status": desired_status_for_doc,
					"active_session": desired_active_session,
				},
				update_modified=False,
			)

		payload.append(
			{
				"name": table.name,
				"table_number": table.table_number,
				"status": display_status,
				"location": table.location or "",
				"active_session": active_session or "",
				"pending_orders": pending_orders,
				"pending_requests": pending_requests,
				"confirmed_total": confirmed_total,
				"active_since": _json_safe_datetime(active_since),
				"occupied_minutes": occupied_minutes,
				"has_attention": has_attention,
				**session_customer,
			}
		)
	return {"tables": payload}


@frappe.whitelist()
def get_table_detail(table_name):
	_ensure_table_service_ready()
	if not table_name:
		frappe.throw(_("Table name is required."))

	resolved_table_name = _resolve_table_name(table_name)
	if not resolved_table_name:
		frappe.throw(_("Table not found."), frappe.DoesNotExistError)

	table_doc = frappe.get_doc("Restaurant Table", resolved_table_name)
	session_name = _resolve_active_table_session_name(table_doc.name, table_doc.active_session)

	if not session_name:
		return {
			"table": _serialize_table(table_doc),
			"session": None,
			"orders": [],
			"requests": [],
			"counts": {
				"pending_orders": 0,
				"confirmed_orders": 0,
				"served_orders": 0,
				"paid_orders": 0,
				"pending_requests": 0,
			},
			"totals": {
				"session_grand_total": 0,
				"session_confirmed_total": 0,
			},
		}

	session_doc = frappe.get_doc("Restaurant Table Session", session_name)
	return {
		"table": _serialize_table(table_doc),
		**_table_session_state_payload(session_doc),
	}


@frappe.whitelist()
def assign_table_session_customer(
	table_name, customer_name=None, mobile=None, customer_type=None, guest_count=None
):
	_ensure_management_access()
	_ensure_table_service_ready()

	resolved_table_name = _resolve_table_name(table_name)
	if not resolved_table_name:
		frappe.throw(_("Table not found."), frappe.DoesNotExistError)

	session_doc = _get_or_create_active_table_session(resolved_table_name)
	payload = {
		"customer_name": customer_name,
		"customer_mobile": mobile,
		"customer_type": customer_type,
		"guest_count": guest_count,
	}
	customer_profile = _sanitize_table_session_customer(payload)
	session_doc.note = _encode_table_session_meta(customer_profile)
	session_doc.save(ignore_permissions=True)

	table_doc = frappe.get_doc("Restaurant Table", resolved_table_name)
	return {
		"status": "success",
		"table": _serialize_table(table_doc),
		**_table_session_state_payload(session_doc),
	}


def _set_table_order_status(order_name, target_status, allowed_from):
	if not order_name:
		frappe.throw(_("Order name is required."))
	if target_status not in {"confirmed", "served", "paid"}:
		frappe.throw(_("Invalid target order status."))

	order_doc = frappe.get_doc("Restaurant Table Order", order_name)
	if order_doc.status == target_status:
		return order_doc

	if order_doc.status not in allowed_from:
		frappe.throw(
			_("Order status transition is invalid: {0} -> {1}").format(order_doc.status, target_status)
		)

	order_doc.status = target_status
	order_doc.save(ignore_permissions=True)
	_refresh_session_total_confirmed_amount(order_doc.session)
	return order_doc


@frappe.whitelist()
def confirm_table_order(order_name):
	order_doc = _set_table_order_status(order_name, "confirmed", {"pending"})
	return {
		"status": "success",
		"order": _serialize_table_order(order_doc),
	}


@frappe.whitelist()
def serve_table_order(order_name):
	order_doc = _set_table_order_status(order_name, "served", {"confirmed"})
	return {
		"status": "success",
		"order": _serialize_table_order(order_doc),
	}


@frappe.whitelist()
def pay_table_order(order_name):
	order_doc = _set_table_order_status(order_name, "paid", {"confirmed", "served"})
	return {
		"status": "success",
		"order": _serialize_table_order(order_doc),
	}


def _find_table_order_item(order_doc, row_name=None, menu_item=None):
	for row in order_doc.items or []:
		if row_name and row.name == row_name:
			return row

	if menu_item:
		normalized_menu_item = _resolve_menu_item_ref(menu_item) or menu_item
		for row in order_doc.items or []:
			if row.menu_item == normalized_menu_item:
				return row
	return None


@frappe.whitelist()
def update_table_order_item(
	order_name, row_name=None, menu_item=None, quantity=None, quantity_delta=None, note=None
):
	_ensure_management_access()
	_ensure_table_service_ready()
	if not order_name:
		frappe.throw(_("Order name is required."))

	order_doc = frappe.get_doc("Restaurant Table Order", order_name)
	if order_doc.status not in {"pending", "confirmed"}:
		frappe.throw(_("Only pending/confirmed orders can be edited."))

	qty = None if quantity in (None, "") else flt(quantity)
	delta = None if quantity_delta in (None, "") else flt(quantity_delta)
	if qty is None and delta is None and note in (None, ""):
		frappe.throw(_("At least one update field is required."))

	item_row = _find_table_order_item(order_doc, row_name=row_name, menu_item=menu_item)

	if not item_row and (qty in (None, 0) and (delta is None or delta <= 0)):
		frappe.throw(_("Cannot decrease a line that does not exist."))

	if not item_row:
		menu_item_ref = _resolve_menu_item_ref(menu_item)
		if not menu_item_ref:
			frappe.throw(_("Menu item is required for new order line."))
		menu_doc = frappe.get_doc("Restaurant Table Menu Item", menu_item_ref)
		if not cint(menu_doc.is_available):
			frappe.throw(_("Menu item is not available: {0}").format(menu_doc.item_name))
		item_row = order_doc.append(
			"items",
			{
				"menu_item": menu_doc.name,
				"quantity": 0,
				"price_at_time": flt(menu_doc.price),
				"note": "",
			},
		)

	base_qty = flt(item_row.quantity)
	target_qty = qty if qty is not None else (base_qty + (delta or 0))
	target_qty = flt(target_qty)

	if note is not None:
		item_row.note = (note or "").strip()

	if target_qty <= 0:
		for idx, row in enumerate(order_doc.items or []):
			if row.name == item_row.name:
				order_doc.items.pop(idx)
				break
	else:
		item_row.quantity = target_qty

	session_name = order_doc.session
	table_name = order_doc.table

	if not (order_doc.items or []):
		order_doc.delete(ignore_permissions=True)
		_refresh_session_total_confirmed_amount(session_name)
		session_doc = frappe.get_doc("Restaurant Table Session", session_name)
		return {
			"status": "success",
			"order_deleted": 1,
			"order_name": order_name,
			"table": table_name,
			**_table_session_state_payload(session_doc),
		}

	order_doc.save(ignore_permissions=True)
	_refresh_session_total_confirmed_amount(session_name)
	session_doc = frappe.get_doc("Restaurant Table Session", session_name)
	return {
		"status": "success",
		"order_deleted": 0,
		"order": _serialize_table_order(order_doc),
		**_table_session_state_payload(session_doc),
	}


@frappe.whitelist()
def move_table_session(session_name, target_table):
	_ensure_management_access()
	_ensure_table_service_ready()
	if not session_name:
		frappe.throw(_("Session name is required."))

	resolved_target_table = _resolve_table_name(target_table)
	if not resolved_target_table:
		frappe.throw(_("Target table was not found."), frappe.DoesNotExistError)

	session_doc = frappe.get_doc("Restaurant Table Session", session_name)
	if session_doc.status != "active":
		frappe.throw(_("Only active sessions can be moved to another table."))

	source_table = session_doc.table
	if source_table == resolved_target_table:
		frappe.throw(_("Source and target tables are the same."))

	target_table_doc = frappe.get_doc("Restaurant Table", resolved_target_table)
	if not cint(target_table_doc.is_active):
		frappe.throw(_("Target table is not active."))

	existing_active_target = frappe.db.get_value(
		"Restaurant Table Session",
		{"table": resolved_target_table, "status": "active"},
		"name",
	)
	if existing_active_target and existing_active_target != session_doc.name:
		frappe.throw(_("Target table already has an active session."))

	session_doc.table = resolved_target_table
	session_doc.save(ignore_permissions=True)

	frappe.db.sql(
		"""
        update `tabRestaurant Table Order`
        set `table`=%s
        where `session`=%s
        """,
		(resolved_target_table, session_doc.name),
	)
	frappe.db.sql(
		"""
        update `tabRestaurant Table Request`
        set `table`=%s
        where `session`=%s
        """,
		(resolved_target_table, session_doc.name),
	)

	active_source_session = frappe.db.get_value(
		"Restaurant Table Session",
		{"table": source_table, "status": "active"},
		"name",
	)
	if active_source_session:
		frappe.db.set_value(
			"Restaurant Table",
			source_table,
			{"status": "occupied", "active_session": active_source_session},
			update_modified=False,
		)
	else:
		frappe.db.set_value(
			"Restaurant Table",
			source_table,
			{"status": "empty", "active_session": ""},
			update_modified=False,
		)

	frappe.db.set_value(
		"Restaurant Table",
		resolved_target_table,
		{"status": "occupied", "active_session": session_doc.name},
		update_modified=False,
	)

	refreshed_session = frappe.get_doc("Restaurant Table Session", session_doc.name)
	return {
		"status": "success",
		"source_table": source_table,
		"target_table": resolved_target_table,
		"table": _serialize_table(target_table_doc),
		**_table_session_state_payload(refreshed_session),
	}


@frappe.whitelist()
def merge_table_sessions(source_session, target_table):
	"""Move all orders/requests from source_session into the active session of target_table."""
	_ensure_management_access()
	_ensure_table_service_ready()

	if not source_session or not target_table:
		frappe.throw(_("Source session and target table are required."))

	resolved_target = _resolve_table_name(target_table)
	if not resolved_target:
		frappe.throw(_("Target table was not found."), frappe.DoesNotExistError)

	source_doc = frappe.get_doc("Restaurant Table Session", source_session)
	if source_doc.status != "active":
		frappe.throw(_("Only active sessions can be merged."))

	source_table = source_doc.table
	if source_table == resolved_target:
		frappe.throw(_("Source and target tables cannot be the same."))

	target_session_name = frappe.db.get_value(
		"Restaurant Table Session",
		{"table": resolved_target, "status": "active"},
		"name",
	)
	if not target_session_name:
		frappe.throw(_("Target table has no active session. Use 'Move' instead of 'Merge'."))

	frappe.db.sql(
		"""
        update `tabRestaurant Table Order`
        set `session`=%s, `table`=%s
        where `session`=%s
        """,
		(target_session_name, resolved_target, source_session),
	)
	frappe.db.sql(
		"""
        update `tabRestaurant Table Request`
        set `session`=%s, `table`=%s
        where `session`=%s
        """,
		(target_session_name, resolved_target, source_session),
	)

	source_doc.status = "closed"
	source_doc.save(ignore_permissions=True)

	frappe.db.set_value(
		"Restaurant Table",
		source_table,
		{"status": "empty", "active_session": ""},
		update_modified=False,
	)

	refreshed_target = frappe.get_doc("Restaurant Table Session", target_session_name)
	return {
		"status": "success",
		"merged_from_table": source_table,
		"merged_into_session": target_session_name,
		**_table_session_state_payload(refreshed_target),
	}


@frappe.whitelist()
def resolve_table_request(request_name):
	if not request_name:
		frappe.throw(_("Request name is required."))

	doc = frappe.get_doc("Restaurant Table Request", request_name)
	doc.status = "done"
	doc.handled_by = frappe.session.user
	doc.save(ignore_permissions=True)
	return {
		"status": "success",
		"request": _serialize_table_request(doc),
	}


@frappe.whitelist()
def close_table_session(session_name):
	_ensure_table_service_ready()
	if not session_name:
		frappe.throw(_("Session name is required."))

	doc = frappe.get_doc("Restaurant Table Session", session_name)
	if doc.status == "closed":
		return {
			"status": "success",
			"session": _serialize_table_session(doc),
		}

	open_order_count = frappe.db.count(
		"Restaurant Table Order",
		filters={
			"session": session_name,
			"status": ["in", list(TABLE_ORDER_ACTIVE_STATUSES)],
		},
	)
	if open_order_count:
		frappe.throw(_("Cannot close session while there are active orders."))

	_refresh_session_total_confirmed_amount(session_name)
	doc.status = "closed"
	doc.save(ignore_permissions=True)

	return {
		"status": "success",
		"session": _serialize_table_session(doc),
	}


def seed_demo_menu():
	from restaurant.patches.v0_0.seed_restaurant_demo_data import execute
	from restaurant.patches.v0_1.sync_restaurant_to_core_doctypes import execute as sync_execute
	from restaurant.patches.v0_2.ensure_restaurant_production_custom_fields import execute as fields_execute
	from restaurant.patches.v0_2.seed_veederakht_production_data import execute as veederakht_seed_execute

	execute()
	sync_execute()
	fields_execute()
	veederakht_seed_execute()

	core_item_count = 0
	core_category_count = 0
	core_subcategory_count = 0
	if _has_column("Item", "restaurant_enabled"):
		core_item_count = frappe.db.count("Item", filters={"restaurant_enabled": 1, "disabled": 0})
	if _has_column("Item Group", "restaurant_is_menu_category"):
		core_category_count = frappe.db.count(
			"Item Group",
			filters={"restaurant_is_menu_category": 1, "restaurant_is_subcategory": 0},
		)
		core_subcategory_count = frappe.db.count(
			"Item Group",
			filters={"restaurant_is_menu_category": 1, "restaurant_is_subcategory": 1},
		)

	return {
		"categories": core_category_count,
		"items": core_item_count,
		"subcategories": core_subcategory_count,
		"core_item_groups": core_category_count + core_subcategory_count,
		"core_items": core_item_count,
		"salads_category": frappe.db.exists(
			"Item Group",
			{
				"restaurant_slug": "salads",
				"restaurant_is_menu_category": 1,
				"restaurant_is_subcategory": 0,
			},
		)
		if _has_column("Item Group", "restaurant_slug")
		else False,
		"web_settings": frappe.db.exists("DocType", "Restaurant Web Settings"),
	}


@frappe.whitelist()
def sync_menu_to_system_doctypes():
	from restaurant.patches.v0_1.sync_restaurant_to_core_doctypes import execute as sync_execute

	sync_execute()
	return {
		"status": "success",
		"item_groups": frappe.db.count("Item Group", filters={"restaurant_is_menu_category": 1})
		if _has_column("Item Group", "restaurant_is_menu_category")
		else 0,
		"items": frappe.db.count("Item", filters={"restaurant_enabled": 1, "disabled": 0})
		if _has_column("Item", "restaurant_enabled")
		else 0,
	}


@frappe.whitelist()
def get_doctype_cleanup_audit():
	legacy_core_replaced = [
		"Restaurant Menu Category",
		"Restaurant Menu Subcategory",
		"Restaurant Menu Item",
		"Restaurant Order",
		"Restaurant Order Item",
		"Restaurant Order Item Selection",
	]
	required_for_current_flow = [
		"Restaurant BOM Modifier",
		"Restaurant Branch Production Settings",
		"Restaurant Production Ticket",
		"Restaurant Production Component",
		"Restaurant Web Settings",
		"Restaurant Hero Slide",
		"Restaurant About Section",
		"Restaurant FAQ",
	]

	legacy_payload = []
	for doctype_name in legacy_core_replaced:
		exists = bool(frappe.db.exists("DocType", doctype_name))
		rows = 0
		if exists:
			try:
				rows = frappe.db.count(doctype_name)
			except Exception:
				rows = 0

		legacy_payload.append(
			{
				"doctype": doctype_name,
				"exists": exists,
				"rows": rows,
				"safe_to_delete_when_rows_zero": True,
			}
		)

	required_payload = []
	for doctype_name in required_for_current_flow:
		required_payload.append(
			{
				"doctype": doctype_name,
				"exists": bool(frappe.db.exists("DocType", doctype_name)),
			}
		)

	return {
		"legacy_core_replaced": legacy_payload,
		"required_for_current_flow": required_payload,
	}


@frappe.whitelist()
def run_snapp_sync_now(from_datetime=None, to_datetime=None, only_new=1):
	from restaurant.snapp_sync import sync_snapp_orders

	return sync_snapp_orders(
		trigger="manual",
		from_datetime=from_datetime,
		to_datetime=to_datetime,
		only_new=only_new,
	)


@frappe.whitelist()
def get_snapp_sync_status():
	from restaurant.snapp_sync import get_sync_status

	return get_sync_status()


@frappe.whitelist()
def organize_catalog_items(enable_for_menu=1):
	from restaurant.catalog_organizer import organize_imported_items

	return organize_imported_items(enable_for_menu=enable_for_menu)


@frappe.whitelist()
def run_snapp_backfill(start_date, end_date=None, chunk_days=7, only_new=1):
	from restaurant.snapp_sync import sync_snapp_orders_backfill

	return sync_snapp_orders_backfill(
		start_date=start_date,
		end_date=end_date,
		chunk_days=chunk_days,
		only_new=only_new,
	)


@frappe.whitelist()
def run_snapp_repair_orders(amount_multiplier=None, batch_size=200):
	from restaurant.snapp_sync import repair_existing_snapp_orders

	return repair_existing_snapp_orders(
		amount_multiplier=amount_multiplier,
		batch_size=batch_size,
	)


def _management_is_blank_format_name(format_name):
	normalized = (format_name or "").strip().lower()
	return any(token in normalized for token in ["blank", "خالی", "افتتاح", "اختتام", "opening", "closing"])


def _management_doc_type_label(doctype_name):
	mapping = {
		"BOM": "فرمول ساخت",
		"Delivery Note": "حواله تحویل",
		"Material Request": "درخواست مواد",
		"Stock Entry": "سند انتقال مواد",
		"Employee Advance": "درخواست مساعده",
		"Leave Application": "درخواست مرخصی",
		"Payment Entry": "سند ثبت تنخواه",
		"Restaurant POS Payment Log": "گزارش صندوق پوز",
		"Restaurant Register Closing": "اختتامیه صندوق",
		"Sales Invoice": "فاکتور فروش",
		"Sales Order": "سفارش فروش",
		"Purchase Order": "سفارش خرید",
		"Quotation": "پیش فاکتور",
	}
	if doctype_name in mapping:
		return mapping[doctype_name]
	translated = _(doctype_name) if doctype_name else ""
	return translated or doctype_name or "سایر"


def _management_print_format_title(format_name):
	mapping = {
		"Restaurant Blank BOM": "فرم خالی فرمول ساخت رستوران",
		"Restaurant Blank Delivery Note": "فرم خالی حواله تحویل",
		"Restaurant Blank Material Request": "فرم خالی درخواست مواد",
		"Restaurant Blank Material Transfer": "فرم خالی سند انتقال مواد",
		"Restaurant Blank Employee Advance Request": "فرم خالی درخواست مساعده",
		"Restaurant Blank Leave Request": "فرم خالی درخواست مرخصی",
		"Restaurant Blank Petty Cash Register": "فرم خالی سند ثبت تنخواه",
		"Restaurant Blank POS Opening Report": "فرم خالی افتتاحیه صندوق پوز",
		"Restaurant Blank POS Closing Report": "فرم خالی اختتامیه صندوق پوز",
		"Persian Blank BOM": "فرم خالی فرمول ساخت فارسی",
		"Persian Blank Delivery Note": "فرم خالی حواله تحویل فارسی",
		"Persian Blank Material Request": "فرم خالی درخواست مواد فارسی",
	}
	return mapping.get(format_name, format_name or "فرمت چاپ")


def _management_get_print_brand_settings():
	defaults = {
		"brand_name": "رستوران نمونه دن فلو",
		"brand_subtitle": "سامانه مدیریت رستوران",
		"logo": "",
		"header_background_color": "#4A2522",
		"header_text_color": "#FFFFFF",
		"accent_color": "#C08A2A",
		"table_header_background_color": "#F7F2E3",
		"border_color": "#D8C8B3",
		"footer_text": "این نسخه برای چاپ داخلی مجموعه است.",
		"print_font_family": "Peyda",
		"print_font_size": 11,
		"print_receipt_font_scale": "متوسط",
	}
	if not frappe.db.exists("DocType", "Restaurant Print Brand Settings"):
		return defaults

	settings = dict(defaults)
	for fieldname in defaults.keys():
		value = frappe.db.get_single_value("Restaurant Print Brand Settings", fieldname)
		if value not in (None, ""):
			settings[fieldname] = value
	return settings


def _management_print_format_search_roots(app_name):
	roots = []
	if not app_name:
		return roots

	for path_builder in [
		lambda: frappe.get_app_path(app_name, app_name, "print_format"),
		lambda: frappe.get_app_path(app_name, "print_format"),
		lambda: frappe.get_app_path(app_name, app_name, app_name, "print_format"),
	]:
		try:
			root = path_builder()
		except Exception:
			root = ""

		if not root or not os.path.isdir(root) or root in roots:
			continue
		roots.append(root)

	return roots


def _management_collect_local_print_formats(app_name=None):
	local_rows = {}

	if app_name:
		apps = [app_name]
	else:
		try:
			apps = frappe.get_installed_apps() or []
		except Exception:
			apps = []

	for app in apps:
		for root in _management_print_format_search_roots(app):
			try:
				format_slugs = os.listdir(root)
			except Exception:
				format_slugs = []

			for slug in format_slugs:
				folder_path = os.path.join(root, slug)
				if not os.path.isdir(folder_path):
					continue

				json_path = os.path.join(folder_path, f"{slug}.json")
				if not os.path.exists(json_path):
					continue

				try:
					with open(json_path, "r", encoding="utf-8") as file_obj:
						payload = json.load(file_obj) or {}
				except Exception:
					continue

				if (payload.get("doctype") or "").strip() != "Print Format":
					continue

				format_name = (payload.get("name") or "").strip()
				if not format_name:
					continue

				local_rows[format_name] = {
					"name": format_name,
					"doc_type": (payload.get("doc_type") or "").strip(),
					"module": (payload.get("module") or "").strip(),
					"custom_format": cint(payload.get("custom_format") or 0),
					"print_format_type": (payload.get("print_format_type") or "Jinja").strip() or "Jinja",
					"standard": (payload.get("standard") or "Yes").strip() or "Yes",
					"disabled": cint(payload.get("disabled") or 0),
					"_app_name": app,
				}

	return list(local_rows.values())


def _management_get_local_print_format(format_name):
	target_name = (format_name or "").strip()
	if not target_name:
		return None

	for row in _management_collect_local_print_formats():
		if (row.get("name") or "").strip() == target_name:
			return row

	return None


def _management_load_standard_print_format_html(print_format_doc):
	format_name = (print_format_doc.get("name") or "").strip()
	if not format_name:
		return ""

	module_name = (print_format_doc.get("module") or "").strip()
	app_name = (print_format_doc.get("_app_name") or "").strip()

	if not app_name:
		try:
			module_app_map = getattr(frappe.local, "module_app", {}) or {}
			app_name = module_app_map.get(module_name) or ""
		except Exception:
			app_name = ""

	format_slug = frappe.scrub(format_name)
	candidate_paths = []
	if app_name:
		candidate_paths.extend(
			[
				frappe.get_app_path(app_name, app_name, "print_format", format_slug, f"{format_slug}.html"),
				frappe.get_app_path(
					app_name, app_name, app_name, "print_format", format_slug, f"{format_slug}.html"
				),
				frappe.get_app_path(app_name, "print_format", format_slug, f"{format_slug}.html"),
			]
		)

	# Final fallback: search every installed app for a matching standard print-format file.
	# This covers formats coming from other apps (for example iran_utilities) when module mapping is incomplete.
	for installed_app in frappe.get_installed_apps() or []:
		for root in _management_print_format_search_roots(installed_app):
			candidate_paths.append(os.path.join(root, format_slug, f"{format_slug}.html"))

	for path in candidate_paths:
		if not path or not os.path.exists(path):
			continue
		try:
			with open(path, "r", encoding="utf-8") as file_obj:
				return (file_obj.read() or "").strip()
		except Exception:
			continue

	alias_formats = {
		"Persian Blank BOM": "Restaurant Blank BOM",
		"Persian Blank Delivery Note": "Restaurant Blank Delivery Note",
		"Persian Blank Material Request": "Restaurant Blank Material Request",
	}
	alias_name = alias_formats.get(format_name)
	if alias_name:
		return _management_load_standard_print_format_html(
			{
				"name": alias_name,
				"module": "Restaurant",
				"_app_name": "restaurant",
			}
		)

	return ""


def _management_fallback_bom_html(print_format_name):
	brand = _management_get_print_brand_settings()
	brand_name = html_escape(str(brand.get("brand_name") or "رستوران نمونه دن فلو"))
	brand_subtitle = html_escape(str(brand.get("brand_subtitle") or "سامانه مدیریت رستوران"))
	header_bg = html_escape(str(brand.get("header_background_color") or "#4A2522"))
	header_text = html_escape(str(brand.get("header_text_color") or "#FFFFFF"))
	accent_color = html_escape(str(brand.get("accent_color") or "#C08A2A"))
	table_header_bg = html_escape(str(brand.get("table_header_background_color") or "#F7F2E3"))
	border_color = html_escape(str(brand.get("border_color") or "#D8C8B3"))
	footer_text = html_escape(str(brand.get("footer_text") or "این نسخه برای چاپ داخلی مجموعه است."))
	brand_logo = html_escape(str(brand.get("logo") or ""))
	title = html_escape(_management_print_format_title(print_format_name))
	print_font_family = html_escape(str(brand.get("print_font_family") or "Peyda"))
	print_font_size = min(max(cint(brand.get("print_font_size") or 11), 8), 24)

	material_rows = "".join(
		f"<tr><td>{index}</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"
		for index in range(1, 13)
	)
	step_rows = "".join(
		f"<tr><td>{index}</td><td></td><td></td><td></td><td></td><td></td></tr>" for index in range(1, 9)
	)
	package_rows = "".join(
		f"<tr><td>{index}</td><td></td><td></td><td></td><td></td></tr>" for index in range(1, 5)
	)
	logo_html = (
		f'<img class="logo" src="{brand_logo}" alt="لوگو" />' if brand_logo else '<div class="logo"></div>'
	)

	return f"""
    <style>
      body {{ margin: 0; direction: rtl; color: #2f3c36; font-family: {print_font_family}, Peyda, Tahoma, sans-serif; font-size: {print_font_size}px; }}
      .sheet {{ border: 1px solid {border_color}; border-radius: 12px; overflow: hidden; }}
      .header {{ background: {header_bg}; color: {header_text}; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }}
      .logo {{ width: 52px; height: 52px; border-radius: 10px; object-fit: cover; background: #fff; border: 1px solid {border_color}; }}
      .brand h1 {{ margin: 0; font-size: 18px; }}
      .brand p {{ margin: 2px 0 0; font-size: 11px; }}
      .title-box {{ text-align: left; }}
      .title-box strong {{ display: block; font-size: 16px; }}
      .title-box small {{ font-size: 11px; }}
      .meta-grid {{ padding: 10px 12px 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
      .meta-cell {{ border: 1px dashed {border_color}; border-radius: 10px; min-height: 52px; padding: 7px; font-size: 11px; }}
      .meta-cell strong {{ color: {accent_color}; display: block; margin-bottom: 3px; }}
      .section {{ padding: 8px 12px 0; }}
      .section-title {{ margin: 0 0 6px; border-right: 4px solid {accent_color}; padding: 4px 8px; background: #fbf8f1; font-size: 13px; }}
      table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
      th, td {{ border: 1px solid {border_color}; text-align: center; padding: 6px 4px; min-height: 24px; }}
      th {{ background: {table_header_bg}; color: #2b332f; }}
      .sign-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding: 14px 12px; }}
      .sign-cell {{ border-top: 1px solid {border_color}; text-align: center; min-height: 48px; padding-top: 8px; font-size: 11px; }}
      .footer {{ border-top: 1px dashed {border_color}; padding: 8px 12px 10px; font-size: 10px; color: #5b6b63; text-align: center; }}
    </style>
    <section class="sheet">
      <header class="header">
        <div class="brand">
          <h1>{brand_name}</h1>
          <p>{brand_subtitle}</p>
        </div>
        <div class="title-box">
          <strong>{title}</strong>
          <small>فرم کامل ثبت مواد اولیه، مراحل آماده سازی و کنترل کیفیت محصول</small>
        </div>
        {logo_html}
      </header>
      <section class="meta-grid">
        <div class="meta-cell"><strong>نام محصول</strong></div>
        <div class="meta-cell"><strong>کد محصول</strong></div>
        <div class="meta-cell"><strong>تاریخ ثبت</strong></div>
        <div class="meta-cell"><strong>نسخه فرمول</strong></div>
        <div class="meta-cell"><strong>تعداد مبنا</strong></div>
        <div class="meta-cell"><strong>واحد تولید</strong></div>
        <div class="meta-cell"><strong>ایستگاه تولید</strong></div>
        <div class="meta-cell"><strong>مسئول شیفت</strong></div>
      </section>
      <section class="section">
        <h3 class="section-title">۱) مواد اولیه و اقلام مصرفی</h3>
        <table>
          <thead>
            <tr>
              <th style="width: 44px;">ردیف</th>
              <th>نام ماده اولیه</th>
              <th>کد ماده</th>
              <th>مقدار استاندارد</th>
              <th>واحد</th>
              <th>درصد ضایعات</th>
              <th>توضیحات</th>
            </tr>
          </thead>
          <tbody>{material_rows}</tbody>
        </table>
      </section>
      <section class="section">
        <h3 class="section-title">۲) مراحل آماده سازی و پخت</h3>
        <table>
          <thead>
            <tr>
              <th style="width: 44px;">مرحله</th>
              <th>شرح عملیات</th>
              <th>ایستگاه کاری</th>
              <th>زمان (دقیقه)</th>
              <th>مسئول</th>
              <th>کنترل کیفیت</th>
            </tr>
          </thead>
          <tbody>{step_rows}</tbody>
        </table>
      </section>
      <section class="section">
        <h3 class="section-title">۳) بسته بندی و تحویل</h3>
        <table>
          <thead>
            <tr>
              <th style="width: 44px;">ردیف</th>
              <th>نوع بسته بندی</th>
              <th>تعداد</th>
              <th>واحد</th>
              <th>توضیحات تحویل</th>
            </tr>
          </thead>
          <tbody>{package_rows}</tbody>
        </table>
      </section>
      <section class="sign-grid">
        <div class="sign-cell">تدوین کننده فرمول</div>
        <div class="sign-cell">سرآشپز / مسئول تولید</div>
        <div class="sign-cell">کنترل کیفیت</div>
        <div class="sign-cell">تایید نهایی مدیریت</div>
      </section>
      <footer class="footer">{footer_text}</footer>
    </section>
    """


def _management_build_blank_doc(doctype_name):
	if not doctype_name:
		frappe.throw(_("برای ساخت پیش نمایش باید نوع داکیومنت مشخص باشد."))

	if not frappe.db.exists("DocType", doctype_name):
		frappe.throw(_("داکیومنت {0} پیدا نشد.").format(doctype_name))

	meta = frappe.get_meta(doctype_name)
	doc = frappe.new_doc(doctype_name)

	for field in meta.fields:
		fieldname = (field.fieldname or "").strip()
		if not fieldname:
			continue

		fieldtype = (field.fieldtype or "").strip()
		if fieldtype in {"Section Break", "Column Break", "Tab Break", "HTML", "Button", "Fold", "Heading"}:
			continue

		if fieldtype in {"Table", "Table MultiSelect"}:
			doc.set(fieldname, [])
			continue

		if fieldtype == "Check":
			doc.set(fieldname, 0)
			continue

		if fieldtype in {"Currency", "Float", "Percent", "Int", "Long Int", "Date", "Datetime", "Time"}:
			doc.set(fieldname, None)
			continue

		doc.set(fieldname, "")

	return doc


def _management_apply_print_color_fix(html_content):
	if not html_content:
		return html_content

	marker = "restaurant-print-color-fix"
	if marker in html_content:
		return html_content

	color_fix_style = """
    <style id="restaurant-print-color-fix">
      @media print {
        html,
        body,
        * {
          -webkit-print-color-adjust: exact !important;
          print-color-adjust: exact !important;
        }
      }
    </style>
    """

	return f"{color_fix_style}{html_content}"


def _management_fallback_print_html(print_format_name, doctype_name, error_message=""):
	if (doctype_name or "").strip() == "BOM":
		return _management_fallback_bom_html(print_format_name)

	error_note = ""
	if error_message:
		error_note = (
			f"<p style='color:#b84f4f;font-size:12px;margin-top:10px'>"
			f"خطا در رندر کامل قالب: {html_escape(str(error_message))}</p>"
		)

	brand_settings = _management_get_print_brand_settings()
	print_font_family = html_escape(str(brand_settings.get("print_font_family") or "Peyda"))
	print_font_size = min(max(cint(brand_settings.get("print_font_size") or 11), 8), 24)

	return f"""
    <style>
      body {{ direction: rtl; font-family: {print_font_family}, Peyda, Tahoma, sans-serif; font-size: {print_font_size}px; margin: 18px; color: #1f3b32; }}
      .sheet {{ border: 1px solid #d9d9d9; border-radius: 12px; padding: 16px; }}
      h1 {{ margin: 0 0 10px; font-size: 18px; }}
      .line {{ border-bottom: 1px dashed #bcc7c1; min-height: 18px; margin-bottom: 8px; }}
      p {{ margin: 0 0 12px; font-size: 12px; color: #4b6b61; }}
      .note {{ margin-top: 14px; border-top: 1px dashed #d2d2d2; padding-top: 10px; color: #666; font-size: 11px; }}
    </style>
    <section class="sheet">
      <h1>{html_escape(_management_print_format_title(print_format_name))}</h1>
      <p>داکیومنت: {html_escape(_management_doc_type_label(doctype_name))}</p>
      <div class="line"></div>
      <div class="line"></div>
      <div class="line"></div>
      <div class="line"></div>
      <div class="note">این پیش نمایش به صورت خالی ساخته شده است.</div>
      {error_note}
    </section>
    """


@frappe.whitelist()
def list_management_print_formats(search=None, doc_type=None, blank_only=0):
	_ensure_management_access()

	filters = {"disabled": 0}
	normalized_doc_type = (doc_type or "").strip()
	if normalized_doc_type:
		filters["doc_type"] = normalized_doc_type

	rows = frappe.get_all(
		"Print Format",
		fields=[
			"name",
			"doc_type",
			"module",
			"custom_format",
			"print_format_type",
			"standard",
			"modified",
		],
		filters=filters,
		order_by="doc_type asc, name asc",
		ignore_permissions=True,
		limit_page_length=600,
	)

	known_names = {(row.get("name") or "").strip() for row in rows if row.get("name")}
	for local_row in _management_collect_local_print_formats(app_name="restaurant"):
		local_name = (local_row.get("name") or "").strip()
		if not local_name or local_name in known_names:
			continue
		if normalized_doc_type and (local_row.get("doc_type") or "").strip() != normalized_doc_type:
			continue
		if cint(local_row.get("disabled") or 0) == 1:
			continue

		rows.append(local_row)
		known_names.add(local_name)

	needle = (search or "").strip().lower()
	only_blank = cint(blank_only) == 1

	payload = []
	grouped_counts = {}
	for row in rows:
		format_name = (row.get("name") or "").strip()
		doctype_name = (row.get("doc_type") or "").strip() or "سایر"
		module_name = (row.get("module") or "").strip()
		is_blank = _management_is_blank_format_name(format_name)
		display_title = _management_print_format_title(format_name)
		doctype_label = _management_doc_type_label(doctype_name)

		haystack = f"{format_name} {display_title} {doctype_name} {doctype_label} {module_name}".lower()
		if needle and needle not in haystack:
			continue
		if only_blank and not is_blank:
			continue

		payload.append(
			{
				"name": format_name,
				"title": display_title,
				"doc_type": doctype_name,
				"doc_type_label": doctype_label,
				"module": module_name,
				"is_blank": is_blank,
				"is_custom": cint(row.get("custom_format") or 0) == 1,
				"is_standard": str(row.get("standard") or "").lower() == "yes",
				"print_format_type": row.get("print_format_type") or "Jinja",
				"modified": _json_safe_datetime(row.get("modified")),
			}
		)

		stats = grouped_counts.setdefault(
			doctype_name, {"count": 0, "blank_count": 0, "label": doctype_label}
		)
		stats["count"] += 1
		if is_blank:
			stats["blank_count"] += 1

	doc_types = [
		{
			"doc_type": doctype_name,
			"doc_type_label": values["label"],
			"count": values["count"],
			"blank_count": values["blank_count"],
		}
		for doctype_name, values in grouped_counts.items()
	]
	doc_types = sorted(doc_types, key=lambda row: row.get("doc_type_label") or "")

	return {
		"total": len(payload),
		"formats": payload,
		"doc_types": doc_types,
	}


@frappe.whitelist()
def get_management_print_format_preview(print_format_name, doc_type=None):
	_ensure_management_access()

	format_name = (print_format_name or "").strip()
	if not format_name:
		frappe.throw(_("نام فرمت چاپ الزامی است."))

	print_format_doc = None
	if frappe.db.exists("Print Format", format_name):
		print_format_doc = frappe.get_doc("Print Format", format_name)
	else:
		print_format_doc = _management_get_local_print_format(format_name)

	if not print_format_doc:
		frappe.throw(_("فرمت چاپ {0} پیدا نشد.").format(format_name))

	target_doctype = (doc_type or "").strip() or (print_format_doc.get("doc_type") or "").strip()
	if not target_doctype:
		frappe.throw(_("برای پیش نمایش باید نوع داکیومنت مشخص باشد."))

	doc = _management_build_blank_doc(target_doctype)

	template_html = (print_format_doc.get("html") or "").strip()
	if not template_html:
		template_html = _management_load_standard_print_format_html(print_format_doc)
	if not template_html:
		template_html = _management_fallback_print_html(
			print_format_name=format_name,
			doctype_name=target_doctype,
		)

	context = {
		"doc": doc,
		"meta": frappe.get_meta(target_doctype),
		"frappe": frappe,
		"no_letterhead": 1,
		"brand_settings": _management_get_print_brand_settings(),
	}

	rendered_html = ""
	render_error = ""
	try:
		rendered_html = frappe.render_template(template_html, context)
	except Exception as err:
		render_error = str(err)

	if not rendered_html:
		rendered_html = _management_fallback_print_html(
			print_format_name=format_name,
			doctype_name=target_doctype,
			error_message=render_error,
		)

	rendered_html = _management_apply_print_color_fix(rendered_html)

	return {
		"name": format_name,
		"title": _management_print_format_title(format_name),
		"doc_type": target_doctype,
		"doc_type_label": _management_doc_type_label(target_doctype),
		"is_blank": _management_is_blank_format_name(format_name),
		"html": rendered_html,
	}


@frappe.whitelist()
def reorder_management_menu_groups(items=None):
	_ensure_management_access()
	if isinstance(items, str):
		items = frappe.parse_json(items)
	items = items or []
	for item in items:
		name = (item.get("name") or "").strip()
		sort_order = cint(item.get("sort_order") or 0)
		if name and frappe.db.exists("Item Group", name):
			frappe.db.set_value("Item Group", name, "restaurant_sort_order", sort_order)
	frappe.db.commit()
	frappe.clear_cache(doctype="Item Group")
	try:
		frappe.clear_website_cache()
	except Exception:
		pass
	return {"ok": True, "count": len(items)}


@frappe.whitelist()
def list_management_menu_groups(search=None):
	_ensure_management_access()
	_ensure_item_group_homepage_field()
	_ensure_item_group_menu_icon_field()
	query = (search or "").strip()
	filters = None
	or_filters = None
	if query:
		like = f"%{query}%"
		or_filters = [["name", "like", like], ["item_group_name", "like", like]]
	fields = [
		"name",
		"item_group_name",
		"parent_item_group",
		"is_group",
		"restaurant_is_menu_category",
		"restaurant_is_subcategory",
		"restaurant_active",
		"restaurant_slug",
		"restaurant_sort_order",
		"restaurant_description",
		"show_on_homepage",
		"image",
		"modified",
	]
	if _has_column("Item Group", "restaurant_menu_icon"):
		fields.append("restaurant_menu_icon")
	rows = frappe.get_all(
		"Item Group",
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		order_by="restaurant_sort_order asc, item_group_name asc",
		limit_page_length=2000,
		ignore_permissions=True,
	)
	return rows


@frappe.whitelist()
def list_management_item_group_parents(search=None):
	_ensure_management_access()
	query = (search or "").strip()
	filters = {"is_group": 1}
	or_filters = None
	if query:
		like = f"%{query}%"
		or_filters = [["name", "like", like], ["item_group_name", "like", like]]
	return frappe.get_all(
		"Item Group",
		fields=["name", "item_group_name", "parent_item_group", "is_group"],
		filters=filters,
		or_filters=or_filters,
		order_by="item_group_name asc",
		limit_page_length=2000,
		ignore_permissions=True,
	)


@frappe.whitelist()
def save_management_menu_design(payload=None):
	_ensure_management_access()
	parsed_payload = payload
	if isinstance(parsed_payload, str):
		parsed_payload = _parse_json(parsed_payload, {})
	if not isinstance(parsed_payload, dict):
		frappe.throw(_("Invalid payload format."))

	groups = parsed_payload.get("groups") or []
	products = parsed_payload.get("products") or []
	if isinstance(groups, str):
		groups = _parse_json(groups, [])
	if isinstance(products, str):
		products = _parse_json(products, [])
	if not isinstance(groups, list):
		groups = []
	if not isinstance(products, list):
		products = []

	saved_groups = []
	group_fields = {"restaurant_sort_order"}
	for fieldname in ("item_group_name", "restaurant_description", "restaurant_active"):
		if _has_column("Item Group", fieldname):
			group_fields.add(fieldname)

	for row in groups:
		if not isinstance(row, dict):
			continue
		name = (row.get("name") or "").strip()
		if not name or not frappe.db.exists("Item Group", name):
			continue
		updates = {}
		if "sort_order" in row or "restaurant_sort_order" in row:
			updates["restaurant_sort_order"] = cint(
				row.get("sort_order", row.get("restaurant_sort_order")) or 0
			)
		if "item_group_name" in row and "item_group_name" in group_fields:
			updates["item_group_name"] = (row.get("item_group_name") or "").strip()
		if "restaurant_description" in row and "restaurant_description" in group_fields:
			updates["restaurant_description"] = (row.get("restaurant_description") or "").strip()
		if "restaurant_active" in row and "restaurant_active" in group_fields:
			updates["restaurant_active"] = cint(row.get("restaurant_active") or 0)
		if updates:
			frappe.db.set_value("Item Group", name, updates, update_modified=True)
			saved_groups.append({"name": name, **updates})

	saved_products = []
	product_fields = {"item_name", "restaurant_sort_order"}
	for fieldname in (
		"restaurant_short_desc",
		"restaurant_category",
		"restaurant_subcategory",
		"restaurant_enabled",
	):
		if _has_column("Item", fieldname):
			product_fields.add(fieldname)

	for row in products:
		if not isinstance(row, dict):
			continue
		requested_name = row.get("name") or row.get("item_name") or row.get("item_code")
		try:
			item_name = _management_resolve_item_name(requested_name)
		except Exception:
			continue
		updates = {}
		if "item_name" in row and "item_name" in product_fields:
			updates["item_name"] = (row.get("item_name") or "").strip()
		if "restaurant_short_desc" in row and "restaurant_short_desc" in product_fields:
			updates["restaurant_short_desc"] = (row.get("restaurant_short_desc") or "").strip()
		if "restaurant_category" in row and "restaurant_category" in product_fields:
			updates["restaurant_category"] = (row.get("restaurant_category") or "").strip()
		if "restaurant_subcategory" in row and "restaurant_subcategory" in product_fields:
			updates["restaurant_subcategory"] = (row.get("restaurant_subcategory") or "").strip()
		if "restaurant_sort_order" in row:
			updates["restaurant_sort_order"] = cint(row.get("restaurant_sort_order") or 0)
		if "restaurant_enabled" in row and "restaurant_enabled" in product_fields:
			updates["restaurant_enabled"] = cint(row.get("restaurant_enabled") or 0)
		if updates:
			frappe.db.set_value("Item", item_name, updates, update_modified=True)
			saved_products.append({"name": item_name, **updates})

	frappe.db.commit()
	frappe.clear_cache(doctype="Item Group")
	frappe.clear_cache(doctype="Item")
	try:
		frappe.clear_website_cache()
	except Exception:
		pass

	return {
		"ok": True,
		"groups_count": len(saved_groups),
		"products_count": len(saved_products),
		"groups": saved_groups,
		"products": saved_products,
	}


@frappe.whitelist()
def setup_coming_soon_field():
	"""Add restaurant_coming_soon checkbox to Item doctype"""
	existing = frappe.db.get_value(
		"Custom Field", {"dt": "Item", "fieldname": "restaurant_coming_soon"}, "name"
	)
	if existing:
		return f"Field already exists: {existing}"
	from frappe.custom.doctype.custom_field.custom_field import create_custom_field

	try:
		doc = create_custom_field(
			"Item",
			frappe._dict(
				{
					"fieldname": "restaurant_coming_soon",
					"label": "\u0628\u0647\u200c\u0632\u0648\u062f\u06cc",
					"fieldtype": "Check",
					"insert_after": "restaurant_item_tag_table",
					"default": 0,
					"description": "\u0627\u06af\u0631 \u0641\u0639\u0627\u0644 \u0628\u0627\u0634\u062f \u0628\u0647 \u062c\u0627\u06cc \u0642\u06cc\u0645\u062a \u0646\u0648\u0634\u062a\u0647 \u00ab\u0628\u0647\u200c\u0632\u0648\u062f\u06cc\u00bb \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f",
				}
			),
		)
		frappe.db.commit()
		return f"Created: {doc}"
	except Exception as e:
		return f"Error: {e}"


# =============================================================================
# Product Builder API Endpoints
# =============================================================================


def _get_builder_step_options(step_name):
	if not step_name:
		return []
	return frappe.get_all(
		"Product Builder Option",
		filters={"parent": step_name, "parenttype": "Product Builder Step", "parentfield": "options"},
		fields=[
			"name",
			"option_label",
			"option_key",
			"option_description",
			"sort_order",
			"item",
			"portion_qty",
			"portion_uom",
			"min_portions",
			"max_portions",
			"portion_step",
			"base_price_delta",
			"price_type",
			"price_percentage",
			"is_default",
			"is_available",
			"max_qty",
			"image",
			"color_code",
			"nutrition_json",
			"allergen_tags",
			"stock_impact_json",
			"linked_step_key",
			"disable_if",
		],
		order_by="sort_order asc, idx asc",
		ignore_permissions=True,
	)


def _builder_template_for_item(item_code):
	item_code = (item_code or "").strip()
	if not item_code:
		return "", None
	item = frappe.db.get_value(
		"Item",
		{"name": item_code},
		["name", "restaurant_builder_template", "restaurant_builder_active", "restaurant_is_customizable"],
		as_dict=True,
	)
	if not item:
		return "", None
	return (item.get("restaurant_builder_template") or "").strip(), item


def _resolve_builder_base_price(item_code, item_doc=None):
	item_doc = item_doc or (frappe.get_doc("Item", item_code) if item_code and frappe.db.exists("Item", item_code) else None)
	if item_doc:
		cfg = _menu_doc_config(item_doc)
		if flt(cfg.get("base_price") or 0) > 0:
			return flt(cfg.get("base_price") or 0)
	item_pricing = _resolve_default_selling_item_pricing(
		item_code,
		1,
		uom=(item_doc.get("stock_uom") if item_doc else "") or "",
	)
	if cint(item_pricing.get("is_selectable") or 0) == 1 and flt(item_pricing.get("total_price") or 0) > 0:
		return flt(item_pricing.get("total_price") or 0)
	if item_doc:
		return flt(item_doc.get("standard_rate") or 0)
	return flt(frappe.db.get_value("Item", item_code, "standard_rate") or 0)


def _builder_option_portion_meta(option_row):
	option_item = (option_row.get("item") or "").strip()
	item_name = frappe.db.get_value("Item", option_item, "item_name") if option_item else ""
	stock_uom = frappe.db.get_value("Item", option_item, "stock_uom") if option_item else ""
	portion_qty = flt(
		option_row.get("portion_qty")
		if option_row.get("portion_qty") not in (None, "")
		else option_row.get("option_qty") or 1
	)
	if portion_qty <= 0:
		portion_qty = 1
	portion_uom = (
		(option_row.get("portion_uom") or "").strip()
		or (option_row.get("option_uom") or "").strip()
		or (stock_uom or "").strip()
	)
	min_portions = max(
		flt(
			option_row.get("min_portions")
			if option_row.get("min_portions") not in (None, "")
			else 0
		),
		0,
	)
	max_portions = flt(
		option_row.get("max_portions")
		if option_row.get("max_portions") not in (None, "")
		else option_row.get("max_qty") or 1
	)
	if max_portions <= 0:
		max_portions = 1
	if max_portions < min_portions:
		max_portions = min_portions
	portion_step = flt(
		option_row.get("portion_step")
		if option_row.get("portion_step") not in (None, "")
		else 1
	)
	if portion_step <= 0:
		portion_step = 1
	return {
		"item": option_item,
		"item_name": item_name or option_item,
		"stock_uom": stock_uom or "",
		"portion_qty": portion_qty,
		"portion_uom": portion_uom,
		"min_portions": min_portions,
		"max_portions": max_portions,
		"portion_step": portion_step,
	}


def _serialize_builder_option(option_row, include_unavailable=False):
	import json

	meta = _builder_option_portion_meta(option_row)
	price_payload = None
	price_delta = flt(option_row.get("base_price_delta") or 0)
	price_source = "legacy_manual"
	price_status = "ok"
	availability_status = "available"
	unavailable_reason = ""
	unit_rate = 0.0
	conversion_factor = 1.0
	resolved_stock_qty = 0.0
	price_list = ""
	is_available = cint(option_row.get("is_available") if option_row.get("is_available") not in (None, "") else 1) == 1

	if meta["item"]:
		price_payload = _resolve_default_selling_item_pricing(
			meta["item"],
			meta["portion_qty"],
			uom=meta["portion_uom"],
		)
		price_delta = flt(price_payload.get("total_price") or 0)
		price_source = "item_price"
		price_status = (price_payload.get("price_status") or "").strip() or "ok"
		availability_status = (price_payload.get("availability_status") or "").strip() or "available"
		unavailable_reason = (price_payload.get("unavailable_reason") or "").strip()
		unit_rate = flt(price_payload.get("unit_rate") or 0)
		conversion_factor = flt(price_payload.get("conversion_factor") or 1)
		resolved_stock_qty = flt(price_payload.get("qty_in_stock_uom") or 0)
		price_list = (price_payload.get("price_list") or "").strip()
		if cint(price_payload.get("is_selectable") or 0) != 1:
			is_available = False

	if not is_available and not include_unavailable:
		return None

	return {
		"option_key": option_row.get("option_key"),
		"option_label": option_row.get("option_label"),
		"option_description": option_row.get("option_description") or "",
		"sort_order": cint(option_row.get("sort_order") or 0),
		"item": meta["item"],
		"item_name": meta["item_name"] or "",
		"stock_uom": meta["stock_uom"] or "",
		"portion_qty": meta["portion_qty"],
		"portion_uom": meta["portion_uom"] or "",
		"min_portions": meta["min_portions"],
		"max_portions": meta["max_portions"],
		"portion_step": meta["portion_step"],
		"price_delta": price_delta,
		"resolved_price_delta": price_delta,
		"base_price_delta": flt(option_row.get("base_price_delta") or 0),
		"price_type": option_row.get("price_type") or "fixed",
		"price_percentage": flt(option_row.get("price_percentage") or 0),
		"is_default": cint(option_row.get("is_default") or 0),
		"is_available": bool(is_available),
		"image": option_row.get("image") or "",
		"color_code": option_row.get("color_code") or "",
		"nutrition": json.loads(option_row.get("nutrition_json")) if option_row.get("nutrition_json") else {},
		"allergens": [a.strip() for a in (option_row.get("allergen_tags") or "").split(",") if a.strip()],
		"max_qty": cint(option_row.get("max_qty") or 1),
		"portion_count_default": 1 if cint(option_row.get("is_default") or 0) else 0,
		"conversion_factor": conversion_factor,
		"resolved_stock_qty": resolved_stock_qty,
		"unit_rate": unit_rate,
		"price_status": price_status,
		"price_list": price_list,
		"price_source": price_source,
		"availability_status": availability_status,
		"unavailable_reason": unavailable_reason,
	}


def _normalize_builder_selection_rows(raw_rows):
	rows = []
	if isinstance(raw_rows, dict):
		for step_key, step_rows in (raw_rows or {}).items():
			for row in step_rows or []:
				if not isinstance(row, dict):
					continue
				payload = dict(row)
				payload.setdefault("step_key", (row.get("step_key") or step_key or "").strip())
				rows.extend(_normalize_builder_selection_rows([payload]))
		return rows
	for row in raw_rows or []:
		if not isinstance(row, dict):
			continue
		step_key = (row.get("step_key") or row.get("step") or "").strip()
		option_key = (row.get("option_key") or row.get("option") or "").strip()
		if not step_key or not option_key:
			continue
		qty = flt(
			row.get("qty")
			if row.get("qty") not in (None, "")
			else row.get("portion_count") or row.get("count") or 0
		)
		if qty <= 0:
			continue
		rows.append(
			{
				"step_key": step_key,
				"step_title": (row.get("step_title") or "").strip(),
				"option_key": option_key,
				"option_label": (row.get("option_label") or "").strip(),
				"qty": qty,
			}
		)
	return rows


def _extract_builder_selection_payload(customization):
	if not isinstance(customization, dict):
		return {}
	builder_selection = customization.get("builder_selection") or {}
	if not isinstance(builder_selection, dict):
		builder_selection = {}
	rows = _normalize_builder_selection_rows(
		builder_selection.get("selections")
		or customization.get("builder_portion_rows")
		or []
	)
	return {
		"template": (builder_selection.get("template") or customization.get("builder_template") or "").strip(),
		"rows": rows,
		"summary": (customization.get("builder_summary") or builder_selection.get("summary") or "").strip(),
	}


def _build_builder_template_catalog(template_name):
	template_doc = frappe.get_doc("Product Builder Template", template_name)
	steps = []
	step_map = {}
	option_map = {}
	for step in sorted(template_doc.steps or [], key=lambda row: row.sort_order or 0):
		options = []
		for option_row in _get_builder_step_options(step.name):
			serialized = _serialize_builder_option(option_row, include_unavailable=True)
			if not serialized:
				continue
			options.append(serialized)
			option_map[(step.step_key, serialized["option_key"])] = serialized
		step_payload = {
			"step_key": step.step_key,
			"step_title": step.step_title,
			"selection_mode": step.selection_mode or "multiple",
			"min_select": flt(step.min_select or 0),
			"max_select": flt(step.max_select or 0),
			"is_required": cint(step.is_required or 0),
			"options": options,
		}
		steps.append(step_payload)
		step_map[step.step_key] = step_payload
	return template_doc, steps, step_map, option_map


def _compute_builder_selection_data(item_code, selections, base_price=None, template_name=None, strict=True):
	template_name = (template_name or "").strip()
	if not template_name:
		template_name, _item_meta = _builder_template_for_item(item_code)
	if not template_name:
		frappe.throw(_("No active builder template found for this item."))

	item_doc = frappe.get_doc("Item", item_code)
	template_doc, steps, step_map, option_map = _build_builder_template_catalog(template_name)
	base_price_value = flt(base_price if base_price not in (None, "") else _resolve_builder_base_price(item_code, item_doc))
	rows = _normalize_builder_selection_rows(selections)
	if strict and not rows:
		frappe.throw(_("At least one builder selection is required."))

	step_totals = defaultdict(float)
	breakdown = []
	selection_items = []
	ingredient_components = []
	selections_summary = []
	nutrition_totals = {key: 0.0 for key in NUTRITION_KEY_FIELD_MAP}
	options_total = 0.0

	for row in rows:
		step_key = row["step_key"]
		option_key = row["option_key"]
		step_payload = step_map.get(step_key)
		option_payload = option_map.get((step_key, option_key))
		if not step_payload or not option_payload:
			frappe.throw(_("Invalid builder selection: {0} / {1}").format(step_key, option_key))
		if not option_payload.get("is_available"):
			frappe.throw(
				option_payload.get("unavailable_reason")
				or _("Builder option {0} is not available.").format(option_payload.get("option_label"))
			)

		qty = flt(row.get("qty") or 0)
		min_portions = flt(option_payload.get("min_portions") or 0)
		max_portions = flt(option_payload.get("max_portions") or 0)
		portion_step = flt(option_payload.get("portion_step") or 1)
		if qty < min_portions - 1e-8 or (max_portions > 0 and qty > max_portions + 1e-8):
			frappe.throw(
				_("Portion count for {0} must be between {1} and {2}.").format(
					option_payload.get("option_label"),
					min_portions,
					max_portions,
				)
			)
		if not _step_valid(qty, min_portions, portion_step):
			frappe.throw(
				_("Portion count for {0} must follow step {1}.").format(
					option_payload.get("option_label"),
					portion_step,
				)
			)

		step_totals[step_key] += qty
		portion_qty = flt(option_payload.get("portion_qty") or 1)
		portion_uom = option_payload.get("portion_uom") or option_payload.get("stock_uom") or ""
		pricing = None
		total_price = 0.0
		unit_rate = 0.0
		conversion_factor = 1.0
		resolved_stock_qty = 0.0
		price_status = option_payload.get("price_status") or "ok"
		price_list = option_payload.get("price_list") or ""
		price_source = option_payload.get("price_source") or "legacy_manual"

		if option_payload.get("item"):
			requested_qty = qty * portion_qty
			pricing = _resolve_default_selling_item_pricing(
				option_payload.get("item"),
				requested_qty,
				uom=portion_uom,
			)
			if cint(pricing.get("is_selectable") or 0) != 1:
				frappe.throw(
					pricing.get("unavailable_reason")
					or _("Builder option {0} is not selectable.").format(option_payload.get("option_label"))
				)
			total_price = flt(pricing.get("total_price") or 0)
			unit_rate = flt(pricing.get("unit_rate") or 0)
			conversion_factor = flt(pricing.get("conversion_factor") or 1)
			resolved_stock_qty = flt(pricing.get("qty_in_stock_uom") or 0)
			price_status = pricing.get("price_status") or price_status
			price_list = pricing.get("price_list") or price_list
			price_source = "item_price"
			ingredient_components.append(
				{
					"ingredient_key": option_key,
					"ingredient_label": option_payload.get("option_label") or option_key,
					"item_code": option_payload.get("item"),
					"item_name": option_payload.get("item_name")
					or frappe.db.get_value("Item", option_payload.get("item"), "item_name")
					or option_payload.get("item"),
					"base_item_code": "",
					"selected_alternative_item": "",
					"base_qty": resolved_stock_qty,
					"selected_base_qty": resolved_stock_qty,
					"base_multiplier": 0,
					"selected_multiplier": 1,
					"is_required": 0,
					"is_included_by_default": 0,
					"can_remove": 1,
					"is_editable_qty": 1,
					"min_multiplier": 0,
					"max_multiplier": max_portions,
					"step_multiplier": portion_step,
					"pricing_rate": unit_rate,
					"pricing_delta": total_price,
					"stock_uom": pricing.get("stock_uom") or option_payload.get("stock_uom") or "",
					"authoring_uom": portion_uom,
					"authoring_base_qty": portion_qty,
					"selected_authoring_qty": qty * portion_qty,
					"source_type": "builder_component",
				}
			)
			option_item_doc = frappe.get_cached_doc("Item", option_payload.get("item"))
			option_nutrition = _nutrition_per_unit_payload(option_item_doc)
			option_factor = _nutrition_factor_from_item_qty(
				option_payload.get("item"),
				qty * portion_qty,
				portion_uom,
			)
			_add_nutrition_to_totals(nutrition_totals, option_nutrition, option_factor)
		else:
			total_price = flt(option_payload.get("base_price_delta") or option_payload.get("price_delta") or 0) * qty

		options_total += total_price
		breakdown.append(
			{
				"step_key": step_key,
				"step_title": step_payload.get("step_title") or step_key,
				"option_key": option_key,
				"option_label": option_payload.get("option_label") or option_key,
				"portion_count": qty,
				"portion_qty": portion_qty,
				"portion_uom": portion_uom,
				"resolved_stock_qty": resolved_stock_qty,
				"stock_uom": (pricing or {}).get("stock_uom") or option_payload.get("stock_uom") or "",
				"conversion_factor": conversion_factor,
				"unit_rate": unit_rate,
				"delta": total_price,
				"total_price": total_price,
				"price_status": price_status,
				"price_list": price_list,
				"price_source": price_source,
				"item": option_payload.get("item") or "",
				"item_name": option_payload.get("item_name") or "",
			}
		)
		selection_items.append(
			{
				"step_key": step_key,
				"step_title": step_payload.get("step_title") or step_key,
				"option_key": option_key,
				"option_label": option_payload.get("option_label") or option_key,
				"qty": qty,
				"portion_count": qty,
				"portion_qty": portion_qty,
				"portion_uom": portion_uom,
				"resolved_stock_qty": resolved_stock_qty,
				"stock_uom": (pricing or {}).get("stock_uom") or option_payload.get("stock_uom") or "",
				"conversion_factor": conversion_factor,
				"unit_rate": unit_rate,
				"price_delta": total_price,
				"total_price": total_price,
				"price_status": price_status,
				"price_list": price_list,
				"price_source": price_source,
				"item": option_payload.get("item") or "",
				"sort_order": cint(option_payload.get("sort_order") or 0),
			}
		)
		selections_summary.append(
			{
				"kind": "builder_component",
				"label": _("{0}: {1} × {2:g}").format(
					step_payload.get("step_title") or step_key,
					option_payload.get("option_label") or option_key,
					qty,
				),
				"delta_price": total_price,
				"qty": qty,
			}
		)

	for step_payload in steps:
		total = flt(step_totals.get(step_payload["step_key"]) or 0)
		min_required = flt(step_payload.get("min_select") or 0)
		max_allowed = flt(step_payload.get("max_select") or 0)
		if cint(step_payload.get("is_required") or 0) and total < max(min_required, 1) - 1e-8:
			frappe.throw(
				_("Builder step {0} requires at least {1:g} portion(s).").format(
					step_payload.get("step_title") or step_payload["step_key"],
					max(min_required, 1),
				)
			)
		if total < min_required - 1e-8:
			frappe.throw(
				_("Builder step {0} requires at least {1:g} portion(s).").format(
					step_payload.get("step_title") or step_payload["step_key"],
					min_required,
				)
			)
		if max_allowed > 0 and total > max_allowed + 1e-8:
			frappe.throw(
				_("Builder step {0} exceeds the maximum of {1:g} portions.").format(
					step_payload.get("step_title") or step_payload["step_key"],
					max_allowed,
				)
			)

	final_price = base_price_value + options_total
	nutrition_unit = _nutrition_payload_from_totals(nutrition_totals)
	pricing_breakdown = {
		"base_price": base_price_value,
		"builder_total": options_total,
		"options_total": options_total,
		"unit_price": final_price,
		"line_total": final_price,
		"qty": 1,
		"builder_portion_rows": breakdown,
		"nutrition": nutrition_unit,
		"nutrition_totals": _normalize_nutrition_totals(nutrition_totals),
	}
	builder_summary = "، ".join(
		[
			"{0}: {1} × {2:g}".format(row["step_title"], row["option_label"], row["portion_count"])
			for row in breakdown
		]
	)
	return {
		"template": template_doc,
		"base_price": base_price_value,
		"options_total": options_total,
		"final_price": final_price,
		"breakdown": breakdown,
		"selection_items": selection_items,
		"normalized_customization": {
			"ingredient_adjustments": [],
			"selected_modifiers": [],
			"selected_alternatives": [],
			"removed_ingredients": [],
			"added_ingredients": [],
			"nutrition": nutrition_unit,
			"nutrition_totals": _normalize_nutrition_totals(nutrition_totals),
			"variant_fixed_attributes": {},
			"builder_selection": {
				"template": template_doc.name,
				"selections": [
					{"step_key": row["step_key"], "option_key": row["option_key"], "qty": row["portion_count"]}
					for row in breakdown
				],
				"summary": builder_summary,
			},
			"builder_summary": builder_summary,
			"builder_pricing_breakdown": pricing_breakdown,
			"builder_portion_rows": breakdown,
			"builder_template": template_doc.name,
		},
		"pricing_breakdown": pricing_breakdown,
		"ingredient_components": ingredient_components,
		"selections_summary": selections_summary,
		"builder_summary": builder_summary,
		"nutrition": nutrition_unit,
		"nutrition_totals": _normalize_nutrition_totals(nutrition_totals),
	}


@frappe.whitelist(allow_guest=True)
def get_builder_template(item_code=None, template_slug=None):
	"""
	Get the Product Builder Template for a given item or slug.
	Customer-facing API (guest-accessible).
	Only returns active templates.
	"""
	import json

	if not item_code and not template_slug:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "item_code or template_slug is required.",
				"code": "MISSING_PARAM",
			},
		}

	try:
		template_name = None

		if item_code:
			# Verify item exists and is customizable
			item = frappe.db.get_value(
				"Item",
				{"name": item_code, "restaurant_is_customizable": 1, "restaurant_builder_active": 1},
				["name", "restaurant_builder_template"],
				as_dict=True,
			)
			if not item:
				return {
					"status": "error",
					"error": {
						"type": "NotFoundError",
						"message": "No active builder template found for this item.",
						"code": "TEMPLATE_NOT_FOUND",
					},
				}
			template_name = item.get("restaurant_builder_template")

		if not template_name and template_slug:
			template_name = frappe.db.get_value(
				"Product Builder Template",
				{"slug": template_slug, "is_active": 1},
				"name",
			)

		if not template_name:
			return {
				"status": "error",
				"error": {
					"type": "NotFoundError",
					"message": "No active builder template found.",
					"code": "TEMPLATE_NOT_FOUND",
				},
			}

		template = frappe.get_doc("Product Builder Template", template_name)

		if not template.is_active:
			return {
				"status": "error",
				"error": {
					"type": "NotFoundError",
					"message": "Builder template is not active.",
					"code": "TEMPLATE_INACTIVE",
				},
			}

		item_doc = frappe.get_doc("Item", item_code) if item_code and frappe.db.exists("Item", item_code) else None
		base_price = _resolve_builder_base_price(item_code, item_doc=item_doc) if item_doc else 0

		# Build steps with options
		steps_data = []
		for step in sorted(template.steps, key=lambda s: s.sort_order or 0):
			options_data = []
			for opt in _get_builder_step_options(step.name):
				serialized = _serialize_builder_option(opt, include_unavailable=False)
				if not serialized:
					continue
				options_data.append(serialized)

			steps_data.append(
				{
					"step_key": step.step_key,
					"step_title": step.step_title,
					"step_description": step.step_description or "",
					"selection_mode": step.selection_mode,
					"min_select": step.min_select or 0,
					"max_select": step.max_select or 0,
					"is_required": step.is_required,
					"show_step_price": step.show_step_price,
					"step_icon": step.step_icon or "",
					"options": options_data,
				}
			)

		return {
			"status": "success",
			"data": {
				"template": {
					"name": template.name,
					"title": template.title,
					"slug": template.slug,
					"layout_mode": template.layout_mode,
					"show_summary_panel": template.show_summary_panel,
					"show_price_live": template.show_price_live,
					"primary_color": template.primary_color or "#1a73e8",
					"allow_skip_steps": template.allow_skip_steps,
					"allow_go_back": template.allow_go_back,
					"require_all_required": template.require_all_required,
					"max_total_selections": template.max_total_selections or 0,
					"base_price": base_price,
					"steps": steps_data,
				}
			},
		}

	except frappe.exceptions.AuthenticationError:
		raise
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_builder_template API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist(allow_guest=True)
def compute_builder_price(item_code, selections):
	"""
	Compute the final price for a set of builder selections.
	Server-side pricing to prevent tampering.
	"""
	import json

	if isinstance(selections, str):
		selections = json.loads(selections)

	if not item_code or not selections:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "item_code and selections are required.",
				"code": "MISSING_PARAM",
			},
		}

	try:
		computed = _compute_builder_selection_data(item_code, selections, strict=True)
		currency = frappe.db.get_default("currency") or "IRR"

		return {
			"status": "success",
			"data": {
				"base_price": computed["base_price"],
				"options_total": computed["options_total"],
				"final_price": computed["final_price"],
				"currency": currency,
				"breakdown": computed["breakdown"],
				"builder_summary": computed["builder_summary"],
				"builder_portion_rows": computed["breakdown"],
				"builder_pricing_breakdown": computed["pricing_breakdown"],
			},
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "compute_builder_price API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist(allow_guest=True)
def save_builder_selection(
	template, item, base_price, selections, selection_json=None, created_via="customer_menu", session_id=None
):
	"""
	Save a completed builder selection.
	Prices are recomputed server-side to prevent tampering.
	"""
	import json

	if isinstance(selections, str):
		selections = json.loads(selections)
	if isinstance(selection_json, str):
		selection_json = json.loads(selection_json)

	if not template or not item or not selections:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "template, item, and selections are required.",
				"code": "MISSING_PARAM",
			},
		}

	try:
		# Verify template is active
		tpl = frappe.get_doc("Product Builder Template", template)
		if not tpl.is_active:
			return {
				"status": "error",
				"error": {
					"type": "ValidationError",
					"message": "Builder template is not active.",
					"code": "TEMPLATE_INACTIVE",
				},
			}

		# Verify item is customizable
		item_doc = frappe.db.get_value(
			"Item", item, ["restaurant_is_customizable", "restaurant_builder_active"], as_dict=True
		)
		if not item_doc or not item_doc.get("restaurant_is_customizable"):
			return {
				"status": "error",
				"error": {
					"type": "ValidationError",
					"message": "Item is not customizable.",
					"code": "ITEM_NOT_CUSTOMIZABLE",
				},
			}

		computed = _compute_builder_selection_data(
			item,
			selections,
			base_price=base_price,
			template_name=template,
			strict=True,
		)
		item_price = computed["base_price"]
		selection_items = computed["selection_items"]
		options_total = computed["options_total"]
		final_price = computed["final_price"]

		# Build selection JSON if not provided
		if not selection_json:
			selection_json = computed["normalized_customization"].get("builder_selection") or {}

		# Create the selection document
		sel_doc = frappe.get_doc(
			{
				"doctype": "Product Builder Selection",
				"template": template,
				"template_title": tpl.title,
				"item": item,
				"item_name": frappe.db.get_value("Item", item, "item_name"),
				"base_price": item_price,
				"options_total": options_total,
				"final_price": final_price,
				"currency": frappe.db.get_default("currency") or "IRR",
				"selection_json": json.dumps(selection_json),
				"created_by_session": session_id,
				"created_via": created_via,
				"selections": selection_items,
			}
		)
		sel_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		return {
			"status": "success",
			"data": {
				"selection_id": sel_doc.name,
				"final_price": final_price,
				"summary": sel_doc.summary_text,
				"builder_summary": computed["builder_summary"],
				"builder_portion_rows": computed["breakdown"],
				"builder_pricing_breakdown": computed["pricing_breakdown"],
			},
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "save_builder_selection API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist(allow_guest=True)
def get_builder_selection(selection_id):
	"""
	Get a saved builder selection by ID.
	"""
	if not selection_id:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "selection_id is required.",
				"code": "MISSING_PARAM",
			},
		}

	try:
		sel = frappe.get_doc("Product Builder Selection", selection_id)
		return {
			"status": "success",
			"data": {
				"selection": {
					"name": sel.name,
					"template": sel.template,
					"template_title": sel.template_title,
					"item": sel.item,
					"item_name": sel.item_name,
					"base_price": sel.base_price,
					"options_total": sel.options_total,
					"final_price": sel.final_price,
					"selections": [
						{
							"step_key": s.step_key,
							"step_title": s.step_title,
							"option_key": s.option_key,
							"option_label": s.option_label,
							"qty": s.qty,
							"portion_count": s.get("portion_count") or s.qty,
							"portion_qty": s.get("portion_qty") or 0,
							"portion_uom": s.get("portion_uom") or "",
							"resolved_stock_qty": s.get("resolved_stock_qty") or 0,
							"stock_uom": s.get("stock_uom") or "",
							"conversion_factor": s.get("conversion_factor") or 1,
							"unit_rate": s.get("unit_rate") or 0,
							"price_delta": s.price_delta,
							"total_price": s.get("total_price") or s.price_delta,
							"price_status": s.get("price_status") or "",
							"price_list": s.get("price_list") or "",
							"price_source": s.get("price_source") or "",
						}
						for s in sel.selections
					],
					"selection_json": sel.selection_json,
					"summary_text": sel.summary_text,
				}
			},
		}
	except frappe.exceptions.DoesNotExistError:
		return {
			"status": "error",
			"error": {"type": "NotFoundError", "message": "Selection not found.", "code": "NOT_FOUND"},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_builder_selection API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist()
def list_builder_templates(search=None, filters=None, limit=20, offset=0):
	"""
	List builder templates (management API).
	Requires Accounts Manager or System Manager role.
	"""
	import json

	if isinstance(filters, str):
		filters = json.loads(filters)

	if not filters:
		filters = {}

	# Only allow management roles
	if not frappe.has_permission("Product Builder Template", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	try:
		or_filters = None
		if search:
			needle = f"%{search}%"
			or_filters = [
				["title", "like", needle],
				["slug", "like", needle],
				["description", "like", needle],
			]

		templates = frappe.get_all(
			"Product Builder Template",
			filters=filters,
			or_filters=or_filters,
			fields=["name", "title", "slug", "description", "is_active", "layout_mode", "modified"],
			limit_page_length=cint(limit),
			limit_start=cint(offset),
			order_by="modified desc",
		)
		total_count = frappe.db.count("Product Builder Template", filters=filters)
		for template in templates:
			template["steps_count"] = frappe.db.count(
				"Product Builder Step", {"parent": template.name, "parenttype": "Product Builder Template"}
			)

		return {
			"status": "success",
			"data": {
				"templates": templates,
				"total_count": total_count,
			},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "list_builder_templates API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist()
def get_builder_template_detail(name):
	"""Get a full builder template for the management editor."""
	if not name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "name is required.", "code": "MISSING_PARAM"},
		}

	if not frappe.has_permission("Product Builder Template", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	try:
		template = frappe.get_doc("Product Builder Template", name)
		steps_data = []
		for step in sorted(template.steps or [], key=lambda s: s.sort_order or 0):
			options_data = []
			for opt in _get_builder_step_options(step.name):
				serialized = _serialize_builder_option(opt, include_unavailable=True) or {}
				options_data.append(
					{
						"name": opt.name,
						"option_label": opt.option_label,
						"option_key": opt.option_key,
						"option_description": opt.option_description or "",
						"sort_order": opt.sort_order or 0,
						"item": opt.item or "",
						"item_name": serialized.get("item_name") or "",
						"stock_uom": serialized.get("stock_uom") or "",
						"portion_qty": serialized.get("portion_qty") or 1,
						"portion_uom": serialized.get("portion_uom") or "",
						"min_portions": serialized.get("min_portions") or 0,
						"max_portions": serialized.get("max_portions") or 1,
						"portion_step": serialized.get("portion_step") or 1,
						"resolved_price_delta": serialized.get("resolved_price_delta") or 0,
						"unit_rate": serialized.get("unit_rate") or 0,
						"conversion_factor": serialized.get("conversion_factor") or 1,
						"price_status": serialized.get("price_status") or "",
						"availability_status": serialized.get("availability_status") or "",
						"unavailable_reason": serialized.get("unavailable_reason") or "",
						"price_list": serialized.get("price_list") or "",
						"price_source": serialized.get("price_source") or "",
						"base_price_delta": opt.base_price_delta or 0,
						"price_type": opt.price_type or "fixed",
						"price_percentage": opt.price_percentage or 0,
						"is_default": bool(opt.is_default),
						"is_available": opt.is_available != 0,
						"max_qty": opt.max_qty or 1,
						"image": opt.image or "",
						"color_code": opt.color_code or "",
						"nutrition_json": opt.nutrition_json or "",
						"allergen_tags": opt.allergen_tags or "",
						"stock_impact_json": opt.stock_impact_json or "",
						"linked_step_key": opt.linked_step_key or "",
						"disable_if": opt.disable_if or "",
					}
				)

			steps_data.append(
				{
					"name": step.name,
					"step_title": step.step_title,
					"step_key": step.step_key,
					"step_description": step.step_description or "",
					"sort_order": step.sort_order or 0,
					"selection_mode": step.selection_mode or "single",
					"min_select": step.min_select or 0,
					"max_select": step.max_select or 1,
					"is_required": bool(step.is_required),
					"show_step_price": step.show_step_price != 0,
					"step_icon": step.step_icon or "",
					"conditional_logic": step.conditional_logic or {},
					"options": options_data,
				}
			)

		return {
			"status": "success",
			"data": {
				"template": {
					"name": template.name,
					"title": template.title,
					"slug": template.slug,
					"description": template.description or "",
					"is_active": bool(template.is_active),
					"layout_mode": template.layout_mode,
					"show_summary_panel": template.show_summary_panel != 0,
					"show_price_live": template.show_price_live != 0,
					"primary_color": template.primary_color or "#1a73e8",
					"background_image": template.background_image or "",
					"allow_skip_steps": bool(template.allow_skip_steps),
					"allow_go_back": template.allow_go_back != 0,
					"require_all_required": template.require_all_required != 0,
					"max_total_selections": template.max_total_selections or 0,
					"steps": steps_data,
				},
			},
		}
	except frappe.exceptions.DoesNotExistError:
		return {
			"status": "error",
			"error": {"type": "NotFoundError", "message": "Template not found.", "code": "NOT_FOUND"},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "get_builder_template_detail API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist()
def list_builder_option_items(search=None, limit=50):
	"""List active Item records for builder option pickers."""
	if not frappe.has_permission("Product Builder Template", "read"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	try:
		filters = {"disabled": 0} if _has_column("Item", "disabled") else {}
		or_filters = None
		if search:
			needle = f"%{search}%"
			or_filters = [
				["name", "like", needle],
				["item_name", "like", needle],
				["item_code", "like", needle],
			]

		fields = ["name", "item_code", "item_name", "stock_uom", "standard_rate", "item_group"]
		for image_field in ("restaurant_image", "website_image", "item_image", "image"):
			if _has_column("Item", image_field) and image_field not in fields:
				fields.append(image_field)
		if _has_column("Item", "restaurant_base_price"):
			fields.append("restaurant_base_price")

		items = frappe.get_all(
			"Item",
			filters=filters,
			or_filters=or_filters,
			fields=fields,
			limit_page_length=max(1, min(cint(limit) or 50, 500)),
			order_by="item_name asc, name asc",
			ignore_permissions=True,
		)

		rows = []
		for item in items:
			image = ""
			for image_field in ("restaurant_image", "website_image", "item_image", "image"):
				if item.get(image_field):
					image = item.get(image_field)
					break
			stock_uom = item.get("stock_uom") or ""
			pricing = _resolve_default_selling_item_pricing(
				item.get("name"),
				1,
				uom=stock_uom,
			)
			default_price = (
				pricing.get("unit_rate")
				if pricing.get("price_status") == "ok"
				else (
					item.get("restaurant_base_price")
					if item.get("restaurant_base_price") is not None
					else item.get("standard_rate")
				)
			)
			label = item.get("item_name") or item.get("item_code") or item.get("name")
			rows.append(
				{
					"value": item.get("name"),
					"label": label,
					"name": item.get("name"),
					"item_code": item.get("item_code") or item.get("name"),
					"item_name": item.get("item_name") or label,
					"stock_uom": stock_uom,
					"standard_rate": default_price or 0,
					"price_list": pricing.get("price_list") or "",
					"price_status": pricing.get("price_status") or "",
					"is_selectable": cint(pricing.get("is_selectable") or 0),
					"unavailable_reason": pricing.get("unavailable_reason") or "",
					"item_group": item.get("item_group") or "",
					"image": image or "",
				}
			)

		return {"status": "success", "data": {"items": rows}}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "list_builder_option_items API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist()
def save_builder_template(template_data=None, template=None):
	"""
	Create or update a builder template (management API).
	Requires Accounts Manager or System Manager role.
	"""
	import json

	payload = template_data if template_data is not None else template
	if isinstance(payload, str):
		payload = json.loads(payload)
	if not payload:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "template_data is required.",
				"code": "MISSING_PARAM",
			},
		}

	if not frappe.has_permission("Product Builder Template", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	try:
		steps = payload.pop("steps", None)
		step_options_by_key = {}
		if payload.get("name"):
			# Update existing
			doc = frappe.get_doc("Product Builder Template", payload["name"])
			doc.update(payload)
		else:
			# Create new
			doc = frappe.get_doc({"doctype": "Product Builder Template", **payload})

		if steps is not None:
			doc.set("steps", [])
			for step_index, step in enumerate(steps):
				step = dict(step or {})
				options = step.pop("options", []) or []
				step_payload = {k: v for k, v in step.items() if k not in ("name", "idx")}
				step_payload["sort_order"] = step_index
				if "conditional_logic" in step_payload:
					step_payload["conditional_logic"] = _normalize_json_text_field(
						step_payload.get("conditional_logic"),
						{},
					)
				step_key = step_payload.get("step_key") or f"step-{frappe.generate_hash(length=8)}"
				step_payload["step_key"] = step_key
				step_options_by_key[step_key] = options
				doc.append("steps", step_payload)

		if steps is not None:
			doc.flags.skip_builder_options_validation = True
		doc.save()

		if steps is not None:
			step_names = {step.step_key: step.name for step in doc.steps or []}
			for step_name in step_names.values():
				frappe.db.delete(
					"Product Builder Option",
					{"parent": step_name, "parenttype": "Product Builder Step", "parentfield": "options"},
				)
			for step_key, options in step_options_by_key.items():
				step_name = step_names.get(step_key)
				if not step_name:
					continue
				if not options:
					frappe.throw(_("Each builder step must have at least one option."))
				option_keys = [
					option.get("option_key") for option in options or [] if isinstance(option, dict)
				]
				if len(option_keys) != len(set(option_keys)):
					frappe.throw(_("Option keys must be unique within each builder step."))
				for option_index, option in enumerate(options or []):
					option_payload = {k: v for k, v in dict(option or {}).items() if k not in ("name", "idx")}
					option_payload["nutrition_json"] = _normalize_json_text_field(
						option_payload.get("nutrition_json"),
						{},
					)
					option_payload["stock_impact_json"] = _normalize_json_text_field(
						option_payload.get("stock_impact_json"),
						{},
					)
					option_payload["disable_if"] = _normalize_json_text_field(
						option_payload.get("disable_if"),
						[],
					)
					option_payload.update(
						{
							"doctype": "Product Builder Option",
							"parent": step_name,
							"parenttype": "Product Builder Step",
							"parentfield": "options",
							"idx": option_index + 1,
							"sort_order": option_index,
						}
					)
					frappe.get_doc(option_payload).db_insert()

		frappe.db.commit()

		return {
			"status": "success",
			"data": {
				"name": doc.name,
				"title": doc.title,
				"slug": doc.slug,
			},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "save_builder_template API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


@frappe.whitelist()
def duplicate_builder_template(name):
	"""
	Duplicate an existing builder template (management API).
	Requires Accounts Manager or System Manager role.
	"""
	import json

	if not frappe.has_permission("Product Builder Template", "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	try:
		source = frappe.get_doc("Product Builder Template", name)
		new_doc = frappe.get_doc(
			{
				"doctype": "Product Builder Template",
				"title": f"{source.title} (کپی)",
				"slug": f"{source.slug}-copy-{frappe.generate_hash(length=6)}",
				"description": source.description,
				"is_active": False,
				"layout_mode": source.layout_mode,
				"show_summary_panel": source.show_summary_panel,
				"show_price_live": source.show_price_live,
				"primary_color": source.primary_color,
				"background_image": source.background_image,
				"allow_skip_steps": source.allow_skip_steps,
				"allow_go_back": source.allow_go_back,
				"require_all_required": source.require_all_required,
				"max_total_selections": source.max_total_selections,
			}
		)

		copied_options = {}
		for step in sorted(source.steps, key=lambda s: s.sort_order or 0):
			new_step_key = f"step-{frappe.generate_hash(length=8)}"
			new_step = {
				"step_key": new_step_key,
				"step_title": step.step_title,
				"step_description": step.step_description,
				"selection_mode": step.selection_mode,
				"min_select": step.min_select,
				"max_select": step.max_select,
				"is_required": step.is_required,
				"show_step_price": step.show_step_price,
				"step_icon": step.step_icon,
			}
			new_doc.append("steps", new_step)
			copied_options[new_step_key] = _get_builder_step_options(step.name)

		new_doc.flags.skip_builder_options_validation = True
		new_doc.insert()
		step_names = {step.step_key: step.name for step in new_doc.steps or []}
		for step_key, options in copied_options.items():
			step_name = step_names.get(step_key)
			if not step_name:
				continue
			for option_index, opt in enumerate(options):
				frappe.get_doc(
					{
						"doctype": "Product Builder Option",
						"parent": step_name,
						"parenttype": "Product Builder Step",
						"parentfield": "options",
						"idx": option_index + 1,
						"sort_order": option_index,
						"option_key": f"opt-{frappe.generate_hash(length=8)}",
						"option_label": opt.option_label,
						"option_description": opt.option_description,
						"item": opt.item,
						"portion_qty": opt.get("portion_qty") if hasattr(opt, "get") else getattr(opt, "portion_qty", 1),
						"portion_uom": opt.get("portion_uom") if hasattr(opt, "get") else getattr(opt, "portion_uom", ""),
						"min_portions": opt.get("min_portions") if hasattr(opt, "get") else getattr(opt, "min_portions", 0),
						"max_portions": opt.get("max_portions") if hasattr(opt, "get") else getattr(opt, "max_portions", 1),
						"portion_step": opt.get("portion_step") if hasattr(opt, "get") else getattr(opt, "portion_step", 1),
						"base_price_delta": opt.base_price_delta,
						"price_type": opt.price_type,
						"price_percentage": opt.price_percentage,
						"is_default": False,
						"is_available": opt.is_available,
						"allergen_tags": opt.allergen_tags,
						"image": opt.image,
						"color_code": opt.color_code,
						"max_qty": opt.max_qty,
					}
				).db_insert()

		frappe.db.commit()

		return {
			"status": "success",
			"data": {
				"name": new_doc.name,
				"title": new_doc.title,
			},
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "duplicate_builder_template API error")
		return {
			"status": "error",
			"error": {"type": "ServerError", "message": str(e), "code": "SERVER_ERROR"},
		}


def cint(val):
	"""Cast to int safely."""
	try:
		return int(val)
	except (TypeError, ValueError):
		return 0


# -------------------------------------------------------------------
# Builder Integration Layer — ERPNext integration for custom orders
# -------------------------------------------------------------------


@frappe.whitelist()
def builder_kitchen_ticket(sales_order_name, sales_order_item_name=None):
	"""
	Build kitchen ticket context for a Sales Order.
	Requires management access.
	"""
	from restaurant.restaurant.builder_integration import build_kitchen_ticket_context

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	try:
		context = build_kitchen_ticket_context(sales_order_name, sales_order_item_name)
		return {"status": "success", "data": context}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_kitchen_ticket API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_render_kitchen_lines(sales_order_name, sales_order_item_name=None):
	"""
	Render kitchen ticket lines for printing, respecting each item's kitchen_print_mode.
	Returns structured lines ready for print template rendering.
	"""
	from restaurant.restaurant.builder_integration import (
		build_kitchen_ticket_context,
		render_kitchen_ticket_lines,
	)

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	try:
		context = build_kitchen_ticket_context(sales_order_name, sales_order_item_name)
		rendered_items = []
		for item_ctx in context.get("items", []):
			mode = item_ctx.get("print_mode", "parent_with_components")
			lines = render_kitchen_ticket_lines(item_ctx, mode)
			rendered_items.append(
				{
					"item_code": item_ctx["item_code"],
					"item_name": item_ctx["item_name"],
					"qty": item_ctx["qty"],
					"print_mode": mode,
					"lines": lines,
				}
			)
		return {"status": "success", "data": {"items": rendered_items}}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_render_kitchen_lines API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_resolve_stock(sales_order_name, sales_order_item_name=None):
	"""
	Resolve builder selections into stock deduction items.
	Respects each item's stock_consumption_mode.
	"""
	from restaurant.restaurant.builder_integration import resolve_builder_stock_deductions

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	try:
		results = resolve_builder_stock_deductions(sales_order_name, sales_order_item_name)
		return {"status": "success", "data": results}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_resolve_stock API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_dry_run(sales_order_name):
	"""
	Dry-run preview of ERPNext records that would be created.
	NO live records are created.
	"""
	from restaurant.restaurant.builder_integration import dry_run_erpnext_records

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	try:
		result = dry_run_erpnext_records(sales_order_name)
		return result
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_dry_run API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_validate_before_write(sales_order_name, operation="stock_entry"):
	"""
	Triple-check safety gate before ERPNext writes.
	Returns dry-run + duplicate check results. Requires human approval to proceed.
	"""
	from restaurant.restaurant.builder_integration import validate_before_erpnext_write

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	try:
		result = validate_before_erpnext_write(sales_order_name, operation)
		return {"status": "success", "data": result}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_validate_before_write API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_execute_records(sales_order_name, approval_token=None):
	"""
	Execute ERPNext record creation after human approval.
	Requires a valid approval_token from builder_validate_before_write().
	"""
	from restaurant.restaurant.builder_integration import execute_erpnext_records

	_ensure_management_access()

	if not sales_order_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_name is required."},
		}

	if not approval_token:
		return {
			"status": "error",
			"error": {"type": "ApprovalRequired", "message": "approval_token is required."},
		}

	try:
		result = execute_erpnext_records(sales_order_name, approval_token)
		return result
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_execute_records API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_attach_selection(sales_order_item_name, selection_name):
	"""
	Attach a builder selection to a Sales Order Item.
	Copies the selection reference + JSON for redundancy.
	"""
	from restaurant.restaurant.builder_integration import attach_builder_selection_to_so_item

	_ensure_management_access()

	if not sales_order_item_name or not selection_name:
		return {
			"status": "error",
			"error": {
				"type": "ValidationError",
				"message": "Both sales_order_item_name and selection_name are required.",
			},
		}

	try:
		attach_builder_selection_to_so_item(sales_order_item_name, selection_name)
		return {"status": "success", "message": "Builder selection attached successfully."}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_attach_selection API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def builder_get_selection_for_item(sales_order_item_name):
	"""
	Get the builder selection linked to a Sales Order Item.
	"""
	from restaurant.restaurant.builder_integration import get_builder_selection_for_so_item

	_ensure_management_access()

	if not sales_order_item_name:
		return {
			"status": "error",
			"error": {"type": "ValidationError", "message": "sales_order_item_name is required."},
		}

	try:
		result = get_builder_selection_for_so_item(sales_order_item_name)
		if not result:
			return {
				"status": "error",
				"error": {"type": "NotFoundError", "message": "Sales Order Item not found."},
			}
		return {"status": "success", "data": result}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "builder_get_selection_for_item API error")
		return {"status": "error", "error": {"type": "ServerError", "message": str(e)}}


@frappe.whitelist()
def get_bom_preview(item_code=None):
	"""
	Return the full BOM tree for a menu item.
	Accepts either an ERPNext item_code or a restaurant slug (resolved to item_code).
	Only staff/employee users can view BOM — customers see a permission error.
	Response shape matches frontend BomPreviewPage expectations.
	"""
	if frappe.session.user == "Guest":
		frappe.throw(_("Please login to access this resource."), frappe.PermissionError)

	if not _is_restaurant_staff() and not frappe.db.get_value(
		"Employee", {"user_id": frappe.session.user}, "name"
	):
		frappe.throw(
			_("You do not have permission to view BOM data. Staff access required."), frappe.PermissionError
		)

	item_code = (item_code or "").strip() if item_code else ""
	if not item_code:
		return {"status": "error", "error": {"type": "ValidationError", "message": "item_code is required."}}

	# Try direct item_code first, then resolve from slug
	item_name = frappe.db.get_value(
		"Item",
		{
			"item_code": item_code,
			"disabled": 0,
			"restaurant_enabled": 1,
		},
		"name",
	)

	if not item_name:
		# Resolve from restaurant_slug
		slug = _normalize_slug(item_code)
		if slug:
			item_name = frappe.db.get_value(
				"Item",
				{
					"restaurant_slug": slug,
					"disabled": 0,
					"restaurant_enabled": 1,
				},
				"name",
			)

	if not item_name:
		# Try variant resolution
		item_name = _resolve_menu_item_name_from_variant_slug(slug=item_code)

	if not item_name:
		return {
			"status": "error",
			"error": {"type": "NotFoundError", "message": _("Item not found: {0}").format(item_code)},
		}

	item_doc = frappe.get_doc("Item", item_name)

	# Resolve the default/active BOM
	bom_name = _resolve_bom_template(item_doc)

	if not bom_name:
		# Return product info without BOM
		product_data = _build_product_data(item_doc, has_bom=False)
		return {
			"status": "success",
			"data": {
				"product": product_data,
				"bom_tree": [],
				"gramezh": [],
				"prep_notes": "",
			},
		}

	bom_doc = frappe.get_doc("BOM", bom_name)

	# Build response in frontend-expected format.
	# Quantities are scaled recursively: if a parent uses 50g of a sub-BOM,
	# the sub-BOM children are calculated for that 50g, not for the sub-BOM's full batch size.
	product_data = _build_product_data(item_doc, has_bom=True)
	root_qty = flt(bom_doc.get("quantity") or 1) or 1
	bom_tree = _build_bom_tree_nodes(bom_doc, required_qty=root_qty)
	gramezh = _build_gramezh_rows(bom_doc, required_qty=root_qty)
	prep_notes = (bom_doc.get("prep_notes") or "").strip() if bom_doc.meta.has_field("prep_notes") else ""
	operations = _build_bom_operations(bom_doc)

	# BOM-level QC notes (from BOM.doctype custom field)
	bom_qc_notes = ""
	if bom_doc.meta.has_field("quality_inspection"):
		bom_qc_notes = (bom_doc.get("quality_inspection") or "").strip()

	return {
		"status": "success",
		"data": {
			"product": product_data,
			"bom_tree": bom_tree,
			"gramezh": gramezh,
			"prep_notes": prep_notes,
			"operations": operations,
			"bom_qc_notes": bom_qc_notes,
		},
	}


def _get_item_image_value(item_code):
	"""Safely return an Item image URL without querying missing columns."""
	item_code = (item_code or "").strip()
	if not item_code:
		return ""
	seen = set()
	for fieldname in (_core_item_image_field(), "item_image", "website_image", "image"):
		fieldname = (fieldname or "").strip()
		if not fieldname or fieldname in seen or not _has_column("Item", fieldname):
			continue
		seen.add(fieldname)
		value = frappe.db.get_value("Item", item_code, fieldname) or ""
		if value:
			return value
	return ""


def _build_product_data(item_doc, has_bom=False):
	"""Build the product object expected by BomPreviewPage."""
	image_field = _core_item_image_field()
	image = item_doc.get(image_field) if image_field else ""
	if not image:
		image = item_doc.get("item_image") or item_doc.get("website_image") or item_doc.get("image") or ""

	nutrition = {}
	if _has_column("Item", "restaurant_nutrition_kcal"):
		nutrition["kcal"] = item_doc.get("restaurant_nutrition_kcal")
	if _has_column("Item", "restaurant_nutrition_protein"):
		nutrition["protein_g"] = item_doc.get("restaurant_nutrition_protein")
	if _has_column("Item", "restaurant_nutrition_carb"):
		nutrition["carb_g"] = item_doc.get("restaurant_nutrition_carb")
	if _has_column("Item", "restaurant_nutrition_fat"):
		nutrition["fat_g"] = item_doc.get("restaurant_nutrition_fat")

	category = ""
	if item_doc.get("restaurant_category"):
		category = frappe.db.get_value("Item Group", item_doc.restaurant_category, "item_group_name") or ""

	# Quality control notes from Item custom field
	qc_notes = ""
	if item_doc.get("restaurant_qc_notes"):
		qc_notes = item_doc.get("restaurant_qc_notes") or ""

	return {
		"item_name": item_doc.item_name,
		"slug": item_doc.get("restaurant_slug") or "",
		"base_price": item_doc.get("restaurant_base_price") or item_doc.get("standard_rate") or 0,
		"category": category,
		"prep_time_mins": item_doc.get("restaurant_prep_time") or item_doc.get("prep_time_mins") or 0,
		"description": item_doc.get("restaurant_short_desc") or item_doc.get("description") or "",
		"nutrition": nutrition,
		"formula_description": item_doc.get("restaurant_formula_description") or "",
		"has_bom": has_bom,
		"image": image,
		"qc_notes": qc_notes,
	}


def _bom_effective_output(bom_doc):
	"""Return the most realistic output quantity for scaling a BOM batch.

	Restaurant BOMs are sometimes authored with BOM.quantity as the menu serving
	amount, while the rows describe the production batch. Prefer a dominant/same
	UOM row total when it is meaningfully larger than the declared quantity.
	"""
	declared_qty = flt(bom_doc.get("quantity") or 1)
	if declared_qty <= 0:
		declared_qty = 1.0
	bom_uom = (bom_doc.get("uom") or "").strip()

	totals_by_uom = {}
	positive_rows = 0
	for row in bom_doc.get("items") or []:
		qty = flt(row.get("qty") or 0)
		if qty <= 0:
			continue
		positive_rows += 1
		uom = (row.get("uom") or row.get("stock_uom") or "").strip()
		if not uom:
			continue
		totals_by_uom[uom] = totals_by_uom.get(uom, 0.0) + qty

	if not totals_by_uom:
		return declared_qty, bom_uom, declared_qty, "declared"

	candidate_uom = bom_uom if bom_uom in totals_by_uom else max(totals_by_uom, key=totals_by_uom.get)
	candidate_total = flt(totals_by_uom.get(candidate_uom) or 0)
	if candidate_total > declared_qty * 1.05:
		return candidate_total, candidate_uom, declared_qty, "uom_total"
	return declared_qty, bom_uom or candidate_uom, declared_qty, "declared"


def _build_bom_tree_nodes(bom_doc, depth=0, visited=None, required_qty=None):
	"""
	Build BOM tree for the frontend BomTree component.
	Quantities are normalized to required_qty. This is important for nested BOMs:
	if the parent needs 50g of a sub-assembly whose effective batch is 1000g,
	child rows are scaled by 50/1000.
	"""
	if visited is None:
		visited = set()

	bom_name = (bom_doc.name or "").strip()
	if bom_name in visited:
		return {"title": bom_name, "item_code": "", "qty": 0, "uom": "", "children": [], "_recursive": True}
	visited.add(bom_name)

	bom_qty, bom_uom, declared_qty, output_source = _bom_effective_output(bom_doc)
	required_qty = flt(required_qty if required_qty not in (None, "") else bom_qty)
	if required_qty <= 0:
		required_qty = bom_qty
	scale = required_qty / bom_qty if bom_qty else 1

	children = []
	for row in bom_doc.get("items") or []:
		item_code = (row.get("item_code") or "").strip()
		if not item_code:
			continue

		item_image = _get_item_image_value(item_code)
		raw_qty = flt(row.get("qty") or 0)
		scaled_qty = raw_qty * scale
		rate = flt(row.get("rate") or row.get("price_list_rate") or 0)
		node = {
			"title": row.get("item_name") or item_code,
			"item_code": item_code,
			"item_name": row.get("item_name") or item_code,
			"image": item_image,
			"qty": scaled_qty,
			"uom": row.get("uom") or row.get("stock_uom") or "",
			"rate": rate,
			"amount": flt(scaled_qty * rate),
			"is_sub_assembly": False,
			"children": [],
		}

		# Recursively resolve sub-BOMs
		sub_bom_name = frappe.get_all(
			"BOM",
			filters={
				"item": item_code,
				"is_active": 1,
				"docstatus": 1,
			},
			fields=["name"],
			order_by="is_default desc, modified desc",
			ignore_permissions=True,
			limit_page_length=1,
		)
		if sub_bom_name:
			try:
				sub_bom_doc = frappe.get_doc("BOM", sub_bom_name[0].name)
				if frappe.has_permission("BOM", "read", sub_bom_doc):
					sub_tree = _build_bom_tree_nodes(
						sub_bom_doc,
						depth=depth + 1,
						visited=visited.copy(),
						required_qty=scaled_qty,
					)
					node["is_sub_assembly"] = True
					node["children"] = sub_tree["children"]
					node["bom_batch_qty"] = sub_tree.get("batch_qty")
					node["bom_batch_uom"] = sub_tree.get("batch_uom")
					node["bom_declared_qty"] = sub_tree.get("declared_qty")
					node["bom_required_qty"] = scaled_qty
					node["bom_scale"] = sub_tree.get("scale")
					node["bom_output_source"] = sub_tree.get("output_source")
			except Exception:
				pass

		children.append(node)

	return {
		"title": bom_doc.get("item_name") or bom_doc.get("item") or bom_name,
		"item_code": bom_doc.get("item") or "",
		"qty": required_qty,
		"uom": bom_uom or bom_doc.get("uom") or "",
		"batch_qty": bom_qty,
		"batch_uom": bom_uom,
		"declared_qty": declared_qty,
		"scale": scale,
		"output_source": output_source,
		"children": children,
	}


def _build_gramezh_rows(bom_doc, required_qty=None):
	"""
	Build top-level material quantity rows.
	Rows are scaled to required_qty for consistency with the BOM tree.
	"""
	rows = []
	bom_qty, bom_uom, declared_qty, output_source = _bom_effective_output(bom_doc)
	required_qty = flt(required_qty if required_qty not in (None, "") else bom_qty)
	if required_qty <= 0:
		required_qty = bom_qty
	scale = required_qty / bom_qty if bom_qty else 1

	for row in bom_doc.get("items") or []:
		item_code = (row.get("item_code") or "").strip()
		if not item_code:
			continue

		qty = flt(row.get("qty") or 0) * scale
		rate = flt(row.get("rate") or row.get("price_list_rate") or 0)

		rows.append(
			{
				"item_code": item_code,
				"item_name": row.get("item_name") or item_code,
				"qty": qty,
				"uom": row.get("uom") or row.get("stock_uom") or "",
				"rate": rate,
				"amount": flt(qty * rate),
			}
		)

	return rows


def _build_bom_operations(bom_doc):
	"""
	Fetch BOM Operation child table for display as preparation steps.
	Returns list of {operation, description, time_in_mins, workstation}.
	"""
	operations = []
	if not bom_doc.meta.has_field("operations"):
		return operations

	for row in bom_doc.get("operations") or []:
		op_name = (row.get("operation") or "").strip()
		if not op_name:
			continue
		operations.append(
			{
				"operation": op_name,
				"description": (row.get("description") or "").strip(),
				"time_in_mins": row.get("time_in_mins") or 0,
				"workstation": (row.get("workstation") or "").strip(),
			}
		)
	return operations


# ─── Role / Permission helpers ───────────────────────────────────

_RESTAURANT_STAFF_ROLES = frozenset(
	[
		"Employee",
		"Chef",
		"Item Manager",
		"Stock Manager",
		"Manufacturing User",
		"Manufacturing Manager",
		"System Manager",
		"Stock User",
	]
)

_RESTAURANT_ADMIN_ROLES = frozenset(
	[
		"System Manager",
		"Administrator",
	]
)


def _user_roles(user=None):
	"""Return set of role names for the given user (default: current session)."""
	if not user:
		user = frappe.session.user
	if not user or user == "Guest":
		return set()
	return {r.role for r in frappe.get_all("Has Role", filters={"parent": user}, fields=["role"])}


def _is_restaurant_staff(user=None):
	"""True if user has at least one staff-role in the restaurant app."""
	return bool(_user_roles(user) & _RESTAURANT_STAFF_ROLES)


def _is_restaurant_admin(user=None):
	"""True if user has admin-level role."""
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	return bool(_user_roles(user) & _RESTAURANT_ADMIN_ROLES)


@frappe.whitelist()
def list_management_users(search=None):
	if not _is_restaurant_admin():
		frappe.throw(_("Only administrators can manage users."), frappe.PermissionError)
	search_text = (search or "").strip().lower()
	filters = {}
	rows = frappe.get_all(
		"User",
		fields=["name", "full_name", "email", "enabled", "user_type", "mobile_no", "last_login"],
		filters=filters,
		order_by="enabled desc, full_name asc",
		ignore_permissions=True,
		limit_page_length=1000,
	)
	role_map = {}
	for row in rows:
		role_map[row.name] = [r.role for r in frappe.get_all("Has Role", filters={"parent": row.name}, fields=["role"], ignore_permissions=True)]
	result = []
	for row in rows:
		if search_text and search_text not in " ".join(str(row.get(k) or "").lower() for k in ("name", "full_name", "email", "mobile_no")):
			continue
		result.append({**row, "roles": sorted(role_map.get(row.name, []))})
	roles = frappe.get_all("Role", filters={"disabled": 0}, pluck="name", order_by="name asc", ignore_permissions=True)
	return {"users": result, "roles": roles}


@frappe.whitelist()
def save_management_user(payload=None):
	if not _is_restaurant_admin():
		frappe.throw(_("Only administrators can manage users."), frappe.PermissionError)
	data = _parse_json(payload, {})
	if not isinstance(data, dict):
		frappe.throw(_("Invalid user payload."))
	user_name = (data.get("name") or data.get("email") or "").strip()
	if user_name and frappe.db.exists("User", user_name):
		doc = frappe.get_doc("User", user_name)
		if doc.name == frappe.session.user and not cint(data.get("enabled", 1)):
			frappe.throw(_("You cannot disable your own account."))
	else:
		email = (data.get("email") or "").strip().lower()
		if not email:
			frappe.throw(_("Email is required."))
		doc = frappe.new_doc("User")
		doc.email = email
		doc.user_type = "System User"
	for fieldname in ("email", "full_name", "mobile_no", "user_type"):
		if fieldname in data and data.get(fieldname) is not None:
			doc.set(fieldname, str(data.get(fieldname)).strip())
	doc.enabled = 1 if data.get("enabled", 1) else 0
	password = str(data.get("new_password") or "")
	if password:
		doc.new_password = password
	requested_roles = data.get("roles") if isinstance(data.get("roles"), list) else []
	allowed_roles = set(frappe.get_all("Role", filters={"disabled": 0}, pluck="name", ignore_permissions=True))
	requested_roles = [str(role).strip() for role in requested_roles if str(role).strip() in allowed_roles]
	if not requested_roles:
		requested_roles = ["Desk User"] if "Desk User" in allowed_roles else []
	doc.set("roles", [])
	for role in requested_roles:
		doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success": True, "user": {"name": doc.name, "email": doc.email, "full_name": doc.full_name, "enabled": cint(doc.enabled), "roles": requested_roles}}


@frappe.whitelist()
def delete_management_user(name=None):
	if not _is_restaurant_admin():
		frappe.throw(_("Only administrators can manage users."), frappe.PermissionError)
	user_name = (name or "").strip()
	if not user_name or user_name in {"Administrator", frappe.session.user} or not frappe.db.exists("User", user_name):
		frappe.throw(_("This user cannot be deleted."))
	frappe.delete_doc("User", user_name, force=1, ignore_permissions=True)
	frappe.db.commit()
	return {"success": True}


@frappe.whitelist()
def get_session_roles():
	"""
	Return role information for the currently logged-in user.

	Used by the frontend to gate BOM / formula visibility.
	Response: { user, roles: [...], is_staff, is_admin }
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please login to access this resource."), frappe.PermissionError)

	roles = sorted(_user_roles(user))

	# Also check if user is linked to an Employee record
	has_employee = bool(frappe.db.get_value("Employee", {"user_id": user}, "name"))

	return {
		"user": user,
		"roles": roles,
		"is_staff": _is_restaurant_staff(user) or has_employee,
		"is_admin": _is_restaurant_admin(user),
		"has_employee_record": has_employee,
	}


def _resolve_canonical_kitchen_status(so_name, has_restaurant_status=True):
    # 1. Check Delivery Note
    dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
    if dn_exists:
        return "closed"
    
    per_delivered = frappe.db.get_value("Sales Order", so_name, "per_delivered") or 0
    if per_delivered >= 100:
        return "closed"

    manual_status = "new"
    if has_restaurant_status:
        manual_status = frappe.db.get_value("Sales Order", so_name, "restaurant_status") or "new"

    # 2. Check Work Orders
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name}, fields=["status", "docstatus", "produced_qty", "qty"])
        if wos:
            all_draft = True
            all_completed = True
            any_in_progress = False
            
            for wo in wos:
                if wo.docstatus == 1:
                    all_draft = False
                    if wo.status == "Completed" or float(wo.produced_qty or 0) >= float(wo.qty or 0):
                        pass
                    else:
                        all_completed = False
                        any_in_progress = True
                else:
                    all_completed = False
                    
            if not all_draft:
                if all_completed:
                    return "ready"
                if any_in_progress:
                    return "preparing"
            
            # If all WOs are draft, rely on manual KDS status (operator intent)
            if manual_status in ["preparing", "ready"]:
                return manual_status
            return "new"
            
    # 3. Direct fulfillment (No BOM / No Work Order)
    if manual_status in ["preparing", "ready"]:
        return manual_status
        
    return "new"



def _start_kitchen_production(so_name):
    # 1. Create tickets and Work Orders if they don't exist
    so_doc = frappe.get_doc("Sales Order", so_name)
    has_tickets = False
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        has_tickets = bool(frappe.db.exists("Restaurant Production Ticket", {"sales_order": so_name}))
        
    if not has_tickets:
        _create_production_for_sales_order(so_doc)

    # 2. Submit Work Orders and do Material Transfer
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name})
        settings = _production_auto_settings()
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            # Submit if draft
            if settings.get("submit_work_order") and wo_doc.docstatus == 0:
                wo_doc.flags.ignore_permissions = True
                wo_doc.submit()
            
            # Material Transfer (Start production)
            wo_doc = frappe.get_doc("Work Order", wo.name)
            if wo_doc.docstatus == 1:
                pending_transfer = max(float(wo_doc.qty or 0) - float(wo_doc.material_transferred_for_manufacturing or 0), 0)
                if settings.get("material_transfer") and pending_transfer > 0 and not int(wo_doc.skip_transfer or 0):
                    _create_work_order_stock_entry(wo.name, "Material Transfer for Manufacture", pending_transfer, submit_doc=settings.get("submit_stock_entries"))
                
                # Mark ticket in_progress
                if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                    tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                    for t in tickets:
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "in_progress", update_modified=False)
    try:
        ops_kitchen_mark(so_name, "preparing")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kitchen Mark Preparing")

def _complete_kitchen_production(so_name):
    settings = _production_auto_settings()
    if frappe.db.exists("DocType", "Work Order"):
        wos = frappe.get_all("Work Order", filters={"sales_order": so_name, "docstatus": 1})
        for wo in wos:
            wo_doc = frappe.get_doc("Work Order", wo.name)
            pending_manufacture = max(float(wo_doc.qty or 0) - float(wo_doc.produced_qty or 0), 0)
            if settings.get("manufacture") and pending_manufacture > 0:
                _create_work_order_stock_entry(wo.name, "Manufacture", pending_manufacture, submit_doc=settings.get("submit_stock_entries"))
            
            # Mark ticket completed
            if frappe.db.exists("DocType", "Restaurant Production Ticket"):
                    tickets = frappe.get_all("Restaurant Production Ticket", filters={"work_order": wo.name})
                    for t in tickets:
                        frappe.db.set_value("Restaurant Production Ticket", t.name, "status", "completed", update_modified=False)
    try:
        ops_kitchen_mark(so_name, "ready")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Kitchen Mark Ready")


@frappe.whitelist()
def get_kitchen_display_orders(limit=50, date=None):
    """Get production-ready orders for kitchen display"""
    _ensure_management_access()
    limit = cint(limit) or 100
    orders = []
    
    if not frappe.db.exists("DocType", "Sales Order"):
        return {"orders": []}
    
    has_restaurant_status = _has_column("Sales Order", "restaurant_status")
    has_restaurant_note = _has_column("Sales Order Item", "restaurant_note")
    has_order_type = _has_column("Sales Order", "restaurant_order_type")
    has_prod_ticket = frappe.db.exists("DocType", "Restaurant Production Ticket")
    
    # Canonical filter: no pre-filtering on restaurant_status
    filters = {"docstatus": 1, "status": ["!=", "Cancelled"]}
    
    if date:
        filters["transaction_date"] = date
    else:
        filters["transaction_date"] = frappe.utils.today()
    
    so_fields = ["name", "customer_name", "customer", "transaction_date", "creation"]
    if has_order_type:
        so_fields.append("restaurant_order_type")
    has_kitchen_timestamps = _has_column("Sales Order", "restaurant_kitchen_started_at") and _has_column("Sales Order", "restaurant_kitchen_ready_at")
    if has_kitchen_timestamps:
        so_fields.extend(["restaurant_kitchen_started_at", "restaurant_kitchen_ready_at"])
    
    rows = frappe.get_all("Sales Order",
        fields=so_fields,
        filters=filters,
        order_by="creation desc",
        limit=limit,
        ignore_permissions=True,
    )
    
    so_item_fields = ["item_code", "item_name", "qty", "rate", "description"]
    if has_restaurant_note:
        so_item_fields.append("restaurant_note")
    
    for so in rows:
        so_name = so.name
        items = []
        tickets = []
        
        so_items = frappe.get_all("Sales Order Item",
            fields=so_item_fields,
            filters={"parent": so_name},
            order_by="idx asc",
            ignore_permissions=True
        )
        item_codes = [i.item_code for i in so_items if i.item_code]
        item_meta = {}
        if item_codes:
            has_item_image = _has_column("Item", "image")
            has_prep_time = _has_column("Item", "restaurant_prep_time_mins")
            has_vendor = _has_column("Item", "restaurant_vendor")
            meta_fields = ["name"]
            if has_item_image:
                meta_fields.append("image")
            if has_prep_time:
                meta_fields.append("restaurant_prep_time_mins")
            if has_vendor:
                meta_fields.append("restaurant_vendor")
            try:
                for meta_row in frappe.get_all("Item", fields=meta_fields, filters={"name": ["in", item_codes]}, ignore_permissions=True):
                    item_meta[meta_row["name"]] = meta_row
            except Exception:
                item_meta = {}
        for item in so_items:
            meta = item_meta.get(item.item_code) or {}
            items.append({
                "item_code": item.item_code,
                "title": item.item_name,
                "description": item.description or "",
                "qty": flt(item.qty),
                "rate": flt(item.rate),
                "note": item.restaurant_note if has_restaurant_note else "",
                "image": meta.get("image") or "",
                "prep_time_mins": cint(meta.get("restaurant_prep_time_mins") or 0),
                "vendor": meta.get("restaurant_vendor") or "",
            })
        
        if has_prod_ticket:
            tickets = frappe.get_all("Restaurant Production Ticket",
                fields=["name", "menu_item", "qty", "status", "work_order"],
                filters={"sales_order": so_name},
                ignore_permissions=True
            )
        
        status = _resolve_canonical_kitchen_status(so_name, has_restaurant_status)
        
        channel = so.restaurant_order_type if has_order_type else ""
        order_code = so_name
        
        orders.append({
            "name": so_name,
            "order_code": order_code,
            "customer_name": so.customer_name or "POS Customer",
            "status": status,
            "channel": channel or "حضوری",
            "items": items,
            "production_tickets": tickets,
            "creation": str(so.creation or ""),
            "created_at": str(so.transaction_date or so.creation or ""),
            "kitchen_started_at": str(so.get("restaurant_kitchen_started_at") or "") if has_kitchen_timestamps else "",
            "kitchen_ready_at": str(so.get("restaurant_kitchen_ready_at") or "") if has_kitchen_timestamps else "",
        })

    return {"orders": orders}


@frappe.whitelist()
def update_kitchen_order_status(order_name, status):
    """Update kitchen order status"""
    _ensure_management_access()
    if not order_name or not status:
        frappe.throw(_("Order name and status are required."))
    
    so_name = _resolve_sales_order_name(order_name)
    if not so_name or not frappe.db.exists("Sales Order", so_name):
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)
    
    # 1. Execute strictly stage-separated canonical backend action flows FIRST.
    # If any underlying document creation/submission fails, it raises an exception 
    # which bubbles up and stops the UI from advancing incorrectly.
    if status == "preparing":
        _start_kitchen_production(so_name)
    elif status == "ready":
        _complete_kitchen_production(so_name)
    elif status == "delivered":
        if frappe.db.exists("DocType", "Delivery Note"):
            dn_exists = frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name, "docstatus": 1})
            if not dn_exists:
                _create_delivery_note_for_sales_order(so_name, submit_doc=True)

    # 2. Only if the canonical documents succeeded (or no documents apply for this item),
    # update the manual text statuses for operator visibility.
    if _has_column("Sales Order", "restaurant_status"):
        _set_restaurant_order_status(so_name, status, force=True)
    
    if frappe.db.exists("DocType", "Restaurant Production Ticket"):
        tickets = frappe.get_all("Restaurant Production Ticket",
            filters={"sales_order": so_name},
            pluck="name",
            ignore_permissions=True
        )
        for ticket_name in tickets:
            ticket = frappe.get_doc("Restaurant Production Ticket", ticket_name)
            if status == "ready":
                ticket.db_set("status", "completed", update_modified=False)
            elif status == "preparing":
                ticket.db_set("status", "in_progress", update_modified=False)
    
    _append_sales_order_note(so_name, f"[KITCHEN] Status changed to: {status}")
    frappe.db.commit()
        
    return {"status": "success"}

# Triggering a direct push for E2E verification as requested

@frappe.whitelist(allow_guest=True)
def get_csrf_token():
    return frappe.sessions.get_csrf_token()

@frappe.whitelist(allow_guest=True)
def get_management_csrf_token():
    return frappe.sessions.get_csrf_token()


# ---------------------------------------------------------------------------
# POS feature pack: bulk product ops, Excel import/export, barcode lookup,
# combos, packaging fees, work shifts, register closing, extra sales reports,
# printer fonts and dashboard layout. Endpoints are re-exported here so they
# are reachable as /api/method/restaurant.api.<endpoint>.
# ---------------------------------------------------------------------------
from restaurant.api_feature_pack import *  # noqa: F401,F403,E402
from restaurant.api_inventory import *  # noqa: F401,F403,E402
from restaurant.api_club import *  # noqa: F401,F403,E402
from restaurant.api_ops import *  # noqa: F401,F403,E402
from restaurant.api_menueng import *  # noqa: F401,F403,E402
from restaurant.api_reserve import *  # noqa: F401,F403,E402
from restaurant.api_tax import *  # noqa: F401,F403,E402
from restaurant.api_branch import *  # noqa: F401,F403,E402
from restaurant.api_callcenter import *  # noqa: F401,F403,E402
from restaurant.api_kiosk import *  # noqa: F401,F403,E402
from restaurant.api_accounting import *  # noqa: F401,F403,E402
from restaurant.api_org import *  # noqa: F401,F403,E402
