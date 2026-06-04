import json
import os
import re
from html import escape as html_escape
import math
import random
import string
from base64 import b64decode
from collections import defaultdict
from itertools import product
from types import SimpleNamespace
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc
from frappe.twofactor import get_qr_svg_code
from frappe.utils import add_days, cint, flt, get_datetime, get_datetime_str, get_time, getdate, now_datetime, nowdate, today


MAX_PAGE_SIZE = 50
ORDER_STATUSES = ["new", "confirmed", "preparing", "ready", "delivered", "cancelled"]
ORDER_TYPES = {"dine_in", "takeaway", "delivery"}
DELIVERY_MODES = {"pickup", "delivery"}
POS_PAYMENT_METHODS = {"cash", "card"}
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
    if not raw_value:
        return []
    parts = []
    for chunk in str(raw_value).replace("\n", ",").split(","):
        tag = (chunk or "").strip()
        if tag:
            parts.append(tag)
    return parts


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
    item_code = (item_code or "").strip()
    source_uom = (source_uom or "").strip()
    if not item_code:
        return 1.0

    stock_uom = (frappe.db.get_value("Item", item_code, "stock_uom") or "").strip()
    if not source_uom or not stock_uom or source_uom == stock_uom:
        return 1.0

    conversion_factor = frappe.db.get_value(
        "UOM Conversion Detail",
        {"parent": item_code, "uom": source_uom},
        "conversion_factor",
    )
    if conversion_factor not in (None, ""):
        return max(flt(conversion_factor), 0)

    try:
        from erpnext.stock.doctype.item.item import get_uom_conv_factor

        fallback = get_uom_conv_factor(source_uom, stock_uom)
        if fallback not in (None, ""):
            return max(flt(fallback), 0)
    except Exception:
        pass

    return 1.0


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


def _get_currency():
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
    provider = (_get_single_setting("Restaurant Web Settings", "restaurant_checkout_map_provider", "neshan") or "neshan").strip().lower()
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
        "enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_pos_payment_enabled", 0)) == 1,
        "provider": (
            _get_single_setting("Restaurant Web Settings", "restaurant_pos_payment_provider", "manual") or "manual"
        ).strip().lower(),
        "default_method": _normalize_payment_method(
            _get_single_setting("Restaurant Web Settings", "restaurant_pos_default_payment_method", "cash")
        ),
        "terminal_id": (_get_single_setting("Restaurant Web Settings", "restaurant_pos_terminal_id", "") or "").strip(),
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
        defaults["default_method"] = _normalize_payment_method(settings_doc.get("default_payment_method") or "cash")
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

    node_result = _call_local_hardware_node("/v1/payment/sale", payload=request_payload, settings=settings, method="POST")
    response_payload = node_result.get("response") or {}

    node_status = (
        response_payload.get("status")
        or response_payload.get("result")
        or response_payload.get("payment_status")
        or ""
    ).strip().lower()

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
        for token in _split_tags(_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_success_values", ""))
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
        "webhook_url": (_get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_url", "") or "").strip(),
        "webhook_api_key": (
            _get_single_setting("Restaurant Web Settings", "restaurant_pos_webhook_api_key", "") or ""
        ).strip(),
        "webhook_timeout_seconds": timeout_seconds,
        "success_tokens": success_tokens,
    }


def _management_pos_payment_boot():
    settings = _get_pos_payment_settings()
    return {
        "enabled": settings["enabled"],
        "provider": settings["provider"],
        "default_method": settings["default_method"],
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
        "opened_at": _json_safe_datetime(row.get("period_start_date") or row.get("creation") or row.get("posting_date")),
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
    allow_discount_change = _pick_profile_bool(payload, ("allow_discount_change", "allow_user_to_edit_discount"))
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
    for fieldname in ("company", "warehouse", "set_warehouse", "currency", "disabled", "title", "pos_profile_name"):
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

    mode_field = _resolve_meta_fieldname(child_meta, ("mode_of_payment", "payment_method", "default_mode_of_payment"))
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
        message = _("POS payment processed.") if status == "paid" else _("POS payment is pending confirmation.")

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
        frappe.db.set_value("Sales Order", order_name, "restaurant_status", normalized_next, update_modified=False)
        return normalized_next

    if current == normalized_next:
        return current

    flow_rank = {value: idx for idx, value in enumerate(RESTAURANT_STATUS_FLOW)}
    current_rank = flow_rank.get(current, -1)
    next_rank = flow_rank.get(normalized_next, -1)
    if next_rank < current_rank:
        return current

    frappe.db.set_value("Sales Order", order_name, "restaurant_status", normalized_next, update_modified=False)
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
        "enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_enabled", 1)) == 1,
        "on_order_submit": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_on_order_submit", 1))
        == 1,
        "on_payment": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_on_payment", 1)) == 1,
        "submit_work_order": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_submit_work_order", 1))
        == 1,
        "material_transfer": cint(
            _get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_material_transfer", 0)
        )
        == 1,
        "manufacture": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_manufacture", 1)) == 1,
        "mark_ready": cint(_get_single_setting("Restaurant Web Settings", "restaurant_auto_flow_mark_ready", 1)) == 1,
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
            "enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_enabled", 1)) == 1,
            "time": (
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_time", "08:00:00") or "08:00:00"
            ),
            "cash_float": flt(_get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_cash_float", 0)),
            "checklist_required": cint(
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_checklist_required", 1)
            )
            == 1,
            "note_template": (
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_opening_note_template", "") or ""
            ).strip(),
        },
        "closing": {
            "enabled": cint(_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_enabled", 1)) == 1,
            "time": (
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_time", "23:00:00") or "23:00:00"
            ),
            "expected_cash": flt(
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_expected_cash", 0)
            ),
            "tolerance": flt(_get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_tolerance", 0)),
            "checklist_required": cint(
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_checklist_required", 1)
            )
            == 1,
            "note_template": (
                _get_single_setting("Restaurant Web Settings", "restaurant_pos_closing_note_template", "") or ""
            ).strip(),
        },
    }


def _create_work_order_stock_entry(work_order_name, purpose, qty, submit_doc=True):
    make_stock_entry = frappe.get_attr("erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry")
    payload = make_stock_entry(work_order_name, purpose, qty=qty)
    if hasattr(payload, "as_dict"):
        payload = payload.as_dict()
    if not isinstance(payload, dict):
        frappe.throw(_("Could not create stock entry payload for work order {0}.").format(work_order_name))

    stock_entry_doc = frappe.get_doc(payload)
    stock_entry_doc.insert(ignore_permissions=True)
    if submit_doc:
        stock_entry_doc.submit()
    return stock_entry_doc.name


def _existing_delivery_note_for_sales_order(so_name, submitted_only=False):
    if not so_name or not frappe.db.exists("DocType", "Delivery Note Item"):
        return ""

    filters = {"against_sales_order": so_name}
    if submitted_only:
        filters["docstatus"] = 1
    row = frappe.get_all(
        "Delivery Note Item",
        filters=filters,
        fields=["parent"],
        order_by="creation desc",
        limit_page_length=1,
        ignore_permissions=True,
    )
    return (row[0].parent if row else "") or ""


def _create_delivery_note_for_sales_order(so_name, fg_warehouse_map=None, submit_doc=True):
    existing = _existing_delivery_note_for_sales_order(so_name, submitted_only=submit_doc)
    if existing:
        return existing

    make_delivery_note = frappe.get_attr("erpnext.selling.doctype.sales_order.sales_order.make_delivery_note")
    payload = make_delivery_note(so_name)
    if hasattr(payload, "as_dict"):
        payload = payload.as_dict()
    if not isinstance(payload, dict):
        payload = {"doctype": "Delivery Note", **(payload or {})}

    delivery_doc = frappe.get_doc(payload)
    fg_warehouse_map = fg_warehouse_map or {}
    for row in delivery_doc.items or []:
        if row.get("warehouse"):
            continue
        mapped_warehouse = fg_warehouse_map.get(row.get("item_code"))
        if mapped_warehouse:
            row.warehouse = mapped_warehouse

    delivery_doc.insert(ignore_permissions=True)
    if submit_doc:
        delivery_doc.submit()
    return delivery_doc.name


def _run_sales_order_auto_flow(order_name, trigger="manual", payment_status=None, force=False):
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
            summary["errors"].append(
                _("Work Order missing for ticket {0}.").format(ticket_doc.name)
            )
            continue

        wo_doc = frappe.get_doc("Work Order", work_order_name)
        if settings.get("submit_work_order") and cint(wo_doc.docstatus) == 0:
            try:
                wo_doc.flags.ignore_permissions = True
                wo_doc.submit()
                summary["submitted_work_orders"].append(wo_doc.name)
                wo_doc = frappe.get_doc("Work Order", wo_doc.name)
            except Exception:
                summary["errors"].append(
                    _("Could not submit Work Order {0}.").format(wo_doc.name)
                )
                frappe.log_error(frappe.get_traceback(), f"Restaurant Auto Flow WO Submit ({wo_doc.name})")
                continue

        if cint(wo_doc.docstatus) != 1:
            continue

        any_started = True
        if (ticket_doc.get("status") or "").strip().lower() == "planned":
            ticket_doc.db_set("status", "in_progress", update_modified=False)

        pending_transfer = max(flt(wo_doc.qty) - flt(wo_doc.material_transferred_for_manufacturing), 0)
        if settings.get("material_transfer") and pending_transfer > 1e-8:
            try:
                se_name = _create_work_order_stock_entry(
                    wo_doc.name,
                    "Material Transfer for Manufacture",
                    pending_transfer,
                    submit_doc=settings.get("submit_stock_entries"),
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
    all_completed = has_production and completed_tickets == len(ticket_docs)
    if any_started:
        _set_restaurant_order_status(so_name, "preparing")
    if settings.get("mark_ready") and (all_completed or not has_production):
        _set_restaurant_order_status(so_name, "ready")

    effective_payment_status = (payment_status or _get_sales_order_payment_status(so_name) or "").strip().lower()
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
        updates["restaurant_payment_payload_json"] = frappe.as_json(payment_result.get("provider_payload") or {})

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


def _insert_management_hardware_event(event_type, severity, message, payload=None, related_order=None, source="pos"):
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


def _append_sales_order_note(order_name, note_line):
    if not note_line or not order_name or not _has_column("Sales Order", "restaurant_note"):
        return

    existing_note = frappe.db.get_value("Sales Order", order_name, "restaurant_note") or ""
    merged_note = f"{existing_note}\n{note_line}".strip() if existing_note else note_line
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
        "provider": provider,
        "status": "paid" if method == "cash" else "pending",
        "reference_no": "",
        "rrn": "",
        "message": _("Cash payment recorded.") if method == "cash" else _("Card payment is pending."),
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

    if manual_reference:
        payment_result["reference_no"] = manual_reference
    if manual_rrn:
        payment_result["rrn"] = manual_rrn

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
    try:
        settings = frappe.get_cached_doc("Restaurant Web Settings")
    except Exception:
        settings = None

    if not settings:
        return {
            "name": "Restaurant",
            "tagline": "منوی آنلاین تازه، سریع و شفاف",
            "hero_title": "سالادهای تازه و غذای سالم روز",
            "hero_subtitle": "با انتخاب کامل مواد داخل هر غذا، سفارش مهمان را سریع ثبت کنید.",
            "hero_image": "",
            "primary_cta_label": "ورود به منو",
        }

    return {
        "name": settings.brand_name or "Restaurant",
        "tagline": settings.brand_tagline or "منوی آنلاین تازه، سریع و شفاف",
        "hero_title": settings.hero_title or "سالادهای تازه و غذای سالم روز",
        "hero_subtitle": settings.hero_subtitle or "با انتخاب کامل مواد داخل هر غذا، سفارش مهمان را سریع ثبت کنید.",
        "hero_image": settings.hero_image or "",
        "primary_cta_label": settings.primary_cta_label or "ورود به منو",
    }


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
            item_data = frappe.db.get_value(
                "Item",
                row.linked_item,
                ["restaurant_slug", f"{image_field} as image", "item_name"],
                as_dict=True,
            ) or {}
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


def _core_item_image_field():
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


def _serialize_core_item(row, category_meta_map=None, subcategory_meta_map=None):
    category_meta_map = category_meta_map or {}
    subcategory_meta_map = subcategory_meta_map or {}
    category_meta = category_meta_map.get(row.restaurant_category, {})
    subcategory_meta = subcategory_meta_map.get(row.restaurant_subcategory, {})
    default_price_list = _get_default_selling_price_list_name()
    item_price = None
    if default_price_list:
        item_price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": row.item_code,
                "price_list": default_price_list,
                "selling": 1
            },
            "price_list_rate"
        )
    base_price = (
        flt(item_price)
        or flt(row.restaurant_base_price)
        or flt(row.standard_rate)
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
        "nutrition": nutrition,
        "nutrition_kcal": nutrition.get("kcal"),
        "nutrition_protein_g": nutrition.get("protein_g"),
        "nutrition_carb_g": nutrition.get("carb_g"),
        "nutrition_sugar_g": nutrition.get("sugar_g"),
        "nutrition_fat_g": nutrition.get("fat_g"),
        "nutrition_protein_percent": nutrition.get("protein_percent"),
        "has_customization": cint(row.get("has_customization") or 0),
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
        flags[item_name] = 1 if (bom_has_modifier_map.get(bom_name) or bom_has_visible_ingredient_map.get(bom_name)) else 0
    return flags


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
            else:
                frappe.get_doc(payload).insert(ignore_permissions=True)

        frappe.clear_cache(doctype="Restaurant Web Settings")

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

    enabled = cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_enabled", 1)) == 1
    show_featured = cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_show_featured", 1)) == 1
    show_best_seller = (
        cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_show_best_seller", 1)) == 1
    )

    featured_limit = max(min(cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_featured_limit", 10)), 50), 0)
    best_seller_limit = max(
        min(cint(_get_single_setting("Restaurant Web Settings", "restaurant_menu_highlight_best_seller_limit", 10)), 50),
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
    out = []
    for row in rows or []:
        payload = frappe._dict(dict(row))
        item_name = (payload.get("name") or "").strip()
        variant_of = (payload.get("variant_of") or "").strip()
        payload["has_customization"] = 1 if (flags.get(item_name) or (variant_of and flags.get(variant_of))) else 0
        out.append(payload)
    return out


def _get_core_menu_boot(branch=None):
    image_field = _core_item_image_field()
    category_meta_map = _get_core_category_meta_map()
    subcategory_meta_map = _get_core_subcategory_meta_map()
    nutrition_fields = _available_item_nutrition_fields()

    categories = frappe.get_all(
        "Item Group",
        filters=_core_category_filters(is_subcategory=0),
        fields=[
            "name",
            "item_group_name as title",
            "restaurant_slug as slug",
            "restaurant_description as description",
            "image",
            "restaurant_sort_order as sort_order",
        ],
        ignore_permissions=True,
        order_by="restaurant_sort_order asc, item_group_name asc",
    )

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
    }


def _get_core_menu_items(category_slug=None, subcategory_slug=None, search=None, page=1, page_size=20, branch=None):
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
    ]
    for fieldname in nutrition_fields:
        if fieldname not in item_fields:
            item_fields.append(fieldname)

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


def _get_menu_items_public_fallback(category_slug=None, subcategory_slug=None, search=None, page=1, page_size=20, branch=None):
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
    if has_restaurant_branch and branch:
        filters["restaurant_branch"] = ["in", [branch, ""]]
    if has_variant_of:
        filters["variant_of"] = ["in", ["", None]]

    resolved_category_name = category_slug_to_name.get(category_slug) if category_slug else ""
    if category_slug and has_restaurant_category:
        if resolved_category_name:
            filters["restaurant_category"] = resolved_category_name
        else:
            return {"items": [], "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0}}

    resolved_subcategory_name = subcategory_slug_to_name.get(subcategory_slug) if subcategory_slug else ""
    if subcategory_slug and has_restaurant_subcategory:
        if resolved_subcategory_name:
            filters["restaurant_subcategory"] = resolved_subcategory_name
        else:
            return {"items": [], "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0}}

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
            slug = _public_menu_slugify(item_name) or _public_menu_slugify(row.get("item_code") or row.get("name") or "")

        short_desc = (row.get("restaurant_short_desc") or "").strip() if has_restaurant_short_desc else ""
        long_desc = (row.get("restaurant_long_desc") or "").strip() if has_restaurant_long_desc else ""
        if search:
            haystack = " ".join([item_name, short_desc, long_desc, slug]).lower()
            if search not in haystack:
                continue

        category_title = (category_meta.get("title") or category_name).strip()
        subcategory_title = (subcategory_meta.get("title") or subcategory_name).strip()

        if category_slug:
            normalized_category_slug = _normalize_slug(category_meta.get("slug") or _public_menu_slugify(category_title))
            if normalized_category_slug != category_slug:
                continue
        if subcategory_slug:
            normalized_subcategory_slug = _normalize_slug(subcategory_meta.get("slug") or _public_menu_slugify(subcategory_title))
            if normalized_subcategory_slug != subcategory_slug:
                continue

        nutrition = _nutrition_payload(row)
        payload_rows.append(
            {
                "name": row.get("name"),
                "slug": slug,
                "title": item_name,
                "short_desc": short_desc,
                "base_price": flt(row.get("restaurant_base_price") or row.get("standard_rate") or 0),
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
                "restaurant_sort_order": cint(row.get("restaurant_sort_order") or 0) if has_restaurant_sort_order else 0,
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
    ingredient_codes = sorted({(row.get("ingredient_item") or "").strip() for row in ingredient_rows if row.get("ingredient_item")})
    ingredient_item_map = {}
    ingredient_image_field = ""
    nutrition_fields = _available_item_nutrition_fields()

    if ingredient_codes:
        ingredient_image_field = "item_image" if _has_column("Item", "item_image") else "image" if _has_column("Item", "image") else ""
        item_fields = ["name"]
        if ingredient_image_field:
            item_fields.append(ingredient_image_field)
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
        required = cint(row.get("is_required")) or (cint(row.is_included_by_default) and not cint(row.can_remove))
        editable = cint(row.get("is_editable_qty"))
        if editable not in (0, 1):
            editable = 1
        if required and min_multiplier < 1:
            min_multiplier = 1

        ingredient_item = (row.get("ingredient_item") or "").strip()
        ingredient_item_doc = ingredient_item_map.get(ingredient_item, {})
        ingredient_nutrition = _nutrition_per_unit_payload(ingredient_item_doc)
        ingredient_image = ingredient_item_doc.get(ingredient_image_field) if ingredient_image_field else ""
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
        "base_price": flt(doc.restaurant_base_price or doc.standard_rate),
        "image": getattr(doc, image_field, ""),
        "category": doc.restaurant_category,
        "category_slug": category_slug,
        "subcategory": doc.restaurant_subcategory,
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
    }

    return {
        "item": item_payload,
        "ingredients": ingredients,
        "modifier_groups": modifier_groups,
        "allergens": _split_tags(doc.restaurant_allergen_tags),
        "currency": _get_currency(),
    }


def _menu_doc_config(menu_doc):
    return {
        "title": menu_doc.item_name,
        "base_price": flt(menu_doc.restaurant_base_price or menu_doc.standard_rate),
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


def _generate_order_code():
    while True:
        code = "R" + "".join(random.choices(string.digits, k=7))
        in_sales = False
        if _has_column("Sales Order", "restaurant_order_code"):
            in_sales = frappe.db.exists("Sales Order", {"restaurant_order_code": code})
        if not in_sales:
            return code


def _default_company():
    return frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value(
        "Company", {}, "name"
    )


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


def _get_default_selling_price_list_name(currency=None, set_fallback_default=False):
    _ensure_default_selling_price_list_field()
    filters = _selling_price_list_filters(currency=currency)

    if _has_column("Price List", DEFAULT_SELLING_PRICE_LIST_FIELD):
        preferred = frappe.db.get_value("Price List", {**filters, DEFAULT_SELLING_PRICE_LIST_FIELD: 1}, "name")
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
    existing = _find_customer_by_mobile(mobile)
    if existing:
        if _has_column("Customer", "mobile_no"):
            current_mobile = frappe.db.get_value("Customer", existing, "mobile_no")
            if not current_mobile:
                frappe.db.set_value("Customer", existing, "mobile_no", mobile, update_modified=False)
        return existing

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
            "mobile_no": mobile,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


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
):
    company = _default_company()
    if not company:
        frappe.throw(_("Default company is not configured."))

    customer = _ensure_customer(customer_name, mobile)
    currency = frappe.db.get_value("Company", company, "default_currency") or _get_currency()
    selling_price_list = _default_selling_price_list(currency) or _default_selling_price_list()
    if not selling_price_list:
        frappe.throw(_("Please configure at least one selling price list."))
    uom_fallback = _default_uom()
    order_code = _generate_order_code()

    delivery_payload = delivery_payload if isinstance(delivery_payload, dict) else {}
    if delivery_payload:
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
    if _has_column("Sales Order", "restaurant_order_code"):
        doc_payload["restaurant_order_code"] = order_code
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
    if delivery_payload and _has_column("Sales Order", "restaurant_delivery_address_name"):
        doc_payload["restaurant_delivery_address_name"] = delivery_address_name or delivery_payload.get("id") or ""
    if delivery_payload and _has_column("Sales Order", "restaurant_delivery_lat"):
        doc_payload["restaurant_delivery_lat"] = flt(delivery_payload.get("lat") or 0)
    if delivery_payload and _has_column("Sales Order", "restaurant_delivery_lng"):
        doc_payload["restaurant_delivery_lng"] = flt(delivery_payload.get("lng") or 0)
    if delivery_payload and _has_column("Sales Order", "restaurant_delivery_details_json"):
        doc_payload["restaurant_delivery_details_json"] = frappe.as_json(delivery_payload)

    subtotal = 0.0
    payload_snapshot = []
    selected_branches = set()

    for cart_line in cart_items:
        menu_doc = _get_item_doc_by_payload(cart_line)
        customization = _extract_customization(cart_line.get("customization") or cart_line.get("config"))
        branch = (cart_line.get("branch") or menu_doc.get("restaurant_branch") or "DEFAULT").strip() or "DEFAULT"
        selected_branches.add(branch)
        markup_percent = _get_branch_pricing_markup_percent(branch)
        line_calc = _recalculate_line(menu_doc, cart_line.get("qty"), customization, branch_markup_percent=markup_percent)
        cfg = _menu_doc_config(menu_doc)
        line_requires_production = _item_requires_production(menu_doc)

        row_payload = {
            "item_code": menu_doc.item_code,
            "item_name": cfg["title"],
            "description": cfg["long_desc"] or cfg["short_desc"] or menu_doc.description,
            "qty": line_calc["qty"],
            "uom": menu_doc.stock_uom or uom_fallback,
            "stock_uom": menu_doc.stock_uom or uom_fallback,
            "rate": line_calc["unit_price"],
            "amount": line_calc["line_total"],
        }
        if _has_column("Sales Order Item", "restaurant_menu_slug"):
            row_payload["restaurant_menu_slug"] = cfg["slug"]
        if _has_column("Sales Order Item", "restaurant_customization_json"):
            row_payload["restaurant_customization_json"] = frappe.as_json(line_calc["normalized_customization"])
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
            unit_price = flt(service_item.get("restaurant_base_price") or service_item.get("standard_rate"))
            line_total = qty * unit_price
            line_requires_production = _item_requires_production(service_item)

            row_payload = {
                "item_code": service_code,
                "item_name": service_item.get("item_name") or service_code,
                "description": service_item.get("description") or service_item.get("item_name") or service_code,
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

    so_doc.submit()
    if _has_column("Sales Order", "restaurant_status"):
        so_doc.db_set("restaurant_status", "confirmed", update_modified=False)

    production_payload = _create_production_for_sales_order(so_doc)
    automation_payload = _run_sales_order_auto_flow(
        so_doc.name,
        trigger="order_submit",
        payment_status="",
    )
    frappe.db.commit()

    return {
        "status": "success",
        "order_id": so_doc.name,
        "order_code": so_doc.get("restaurant_order_code") or order_code,
        "grand_total": flt(so_doc.grand_total or subtotal),
        "pricing_breakdown": payload_snapshot,
        "production_tickets": production_payload["production_tickets"],
        "work_orders": production_payload["work_orders"],
        "production_skipped_items": production_payload.get("skipped_items") or [],
        "automation": automation_payload or {},
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
        frappe.throw(
            _("Branch production settings company mismatch for branch {0}.").format(settings.branch)
        )

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
            component_item_name = ingredient_data.get("item_name") or frappe.db.get_value("Item", component_item_code, "item_name")
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
            component_item_name = bom_row.item_name or frappe.db.get_value("Item", component_item_code, "item_name")
            component_stock_uom = bom_row.stock_uom or bom_row.uom or frappe.db.get_value("Item", component_item_code, "stock_uom")

        if not component_item_code:
            continue

        final_qty = selected_base_qty * selected_multiplier * flt(line_qty) * recipe_multiplier
        if final_qty <= 1e-8:
            continue
        qty_map[component_item_code] += final_qty

        payload = {
            "item_code": component_item_code,
            "item_name": component_item_name,
            "base_item_code": bom_row.item_code,
            "selected_alternative_item": component_item_code if component_item_code != bom_row.item_code else "",
            "ingredient_key": ingredient_data.get("ingredient_key") if ingredient_data else bom_row.item_code,
            "ingredient_label": ingredient_data.get("ingredient_label") if ingredient_data else bom_row.item_name,
            "stock_uom": component_stock_uom,
            "source_warehouse": source_warehouse,
            "base_qty": base_per_serving,
            "selected_base_qty": selected_base_qty,
            "base_multiplier": flt(ingredient_data.get("base_multiplier") if ingredient_data else 1),
            "selected_multiplier": selected_multiplier,
            "recipe_multiplier": recipe_multiplier,
            "final_qty": final_qty,
            "is_required": cint(ingredient_data.get("is_required")) if ingredient_data else 0,
            "is_included_by_default": cint(ingredient_data.get("is_included_by_default")) if ingredient_data else 1,
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
            else ingredient_data.get("base_qty")
            or 0
        )
        final_qty = base_qty * selected_multiplier * flt(line_qty) * recipe_multiplier
        if final_qty <= 1e-8:
            continue
        qty_map[item_code] += final_qty
        components.append(
            {
                "item_code": item_code,
                "item_name": frappe.db.get_value("Item", item_code, "item_name"),
                "base_item_code": (ingredient_data.get("base_item_code") or "").strip(),
                "selected_alternative_item": (ingredient_data.get("selected_alternative_item") or "").strip(),
                "ingredient_key": ingredient_data.get("ingredient_key") or item_code,
                "ingredient_label": ingredient_data.get("ingredient_label") or item_code,
                "stock_uom": ingredient_data.get("stock_uom") or frappe.db.get_value("Item", item_code, "stock_uom"),
                "source_warehouse": source_warehouse,
                "base_qty": base_qty,
                "selected_base_qty": base_qty,
                "base_multiplier": flt(ingredient_data.get("base_multiplier") or 0),
                "selected_multiplier": selected_multiplier,
                "recipe_multiplier": recipe_multiplier,
                "final_qty": final_qty,
                "is_required": cint(ingredient_data.get("is_required")),
                "is_included_by_default": cint(ingredient_data.get("is_included_by_default")),
                "pricing_rate": flt(ingredient_data.get("pricing_rate") or 0),
                "pricing_delta": flt(ingredient_data.get("pricing_delta") or 0),
                "source_type": ingredient_data.get("source_type") or "modifier_add_on",
            }
        )

    return components, qty_map


def _create_work_order_for_ticket(ticket_doc, sales_order_doc, so_item_row, menu_doc, settings, bom_name, qty_map):
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
    if _has_column("Work Order", "restaurant_order_code"):
        updates["restaurant_order_code"] = sales_order_doc.get("restaurant_order_code") or sales_order_doc.name
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
        if not code or qty <= 1e-8:
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

        recipe_multiplier = flt(pricing_breakdown.get("recipe_multiplier") or line_calc.get("recipe_multiplier") or 1)
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
                "order_code": so_doc.get("restaurant_order_code") or so_doc.name,
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


def _get_sales_order_payload(so_name):
    doc = frappe.get_doc("Sales Order", so_name)
    status = _core_order_status(doc)
    delivery_details = (
        _parse_json(doc.get("restaurant_delivery_details_json"), {})
        if _has_column("Sales Order", "restaurant_delivery_details_json")
        else {}
    )

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
                "nutrition": pricing_breakdown.get("nutrition") if isinstance(pricing_breakdown, dict) else {},
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

    order_payload = {
        "name": doc.name,
        "order_code": doc.get("restaurant_order_code") or doc.name,
        "customer_name": doc.customer_name,
        "mobile": doc.get("restaurant_customer_mobile") or "",
        "order_type": doc.get("restaurant_order_type") or "takeaway",
        "address": doc.get("restaurant_delivery_address") or "",
        "delivery_address_id": doc.get("restaurant_delivery_address_name") or "",
        "delivery_lat": flt(doc.get("restaurant_delivery_lat") or 0)
        if _has_column("Sales Order", "restaurant_delivery_lat")
        else None,
        "delivery_lng": flt(doc.get("restaurant_delivery_lng") or 0)
        if _has_column("Sales Order", "restaurant_delivery_lng")
        else None,
        "delivery_details": delivery_details if isinstance(delivery_details, dict) else {},
        "note": doc.get("restaurant_note") or "",
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
        "status_timeline": _status_timeline(status),
    }


def _get_bom_doc(menu_item_doc):
    bom_name = _resolve_bom_template(menu_item_doc)
    if not bom_name or not frappe.db.exists("BOM", bom_name):
        return None
    return frappe.get_doc("BOM", bom_name)


def _get_bom_row_alternative_options(bom_doc, bom_row, item_meta_cache=None):
    item_meta_cache = item_meta_cache if item_meta_cache is not None else {}
    option_map = {}

    base_item = (bom_row.get("item_code") or "").strip()
    if (
        cint(bom_row.get("allow_alternative_item"))
        and base_item
        and frappe.db.exists("DocType", "Item Alternative")
    ):
        alt_fieldname = ""
        if _has_column("Item Alternative", "alternative_item"):
            alt_fieldname = "alternative_item"
        elif _has_column("Item Alternative", "alternative_item_code"):
            alt_fieldname = "alternative_item_code"
        elif _has_column("Item Alternative", "item_code"):
            # Legacy/custom variants may store alternative item as item_code.
            alt_fieldname = "item_code"

        filters = None
        if _has_column("Item Alternative", "item_code") and alt_fieldname != "item_code":
            # ERPNext standard Item Alternative doctype.
            filters = {"item_code": base_item}
        elif _has_column("Item Alternative", "parent") and _has_column("Item Alternative", "parenttype"):
            # Legacy child-table style Item Alternative rows under Item.
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
        nutrition_fields = [fieldname for fieldname in NUTRITION_KEY_FIELD_MAP.values() if _has_column("Item", fieldname)]
        item_fields = ["name", "item_name", "stock_uom", *nutrition_fields]
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
        if not option["uom"]:
            option["uom"] = option["stock_uom"]
        option["nutrition_kcal"] = flt(item_meta.get("restaurant_nutrition_kcal") or 0)
        option["nutrition_protein_g"] = flt(item_meta.get("restaurant_nutrition_protein_g") or 0)
        option["nutrition_carb_g"] = flt(item_meta.get("restaurant_nutrition_carb_g") or 0)
        option["nutrition_sugar_g"] = flt(item_meta.get("restaurant_nutrition_sugar_g") or 0)
        option["nutrition_fat_g"] = flt(item_meta.get("restaurant_nutrition_fat_g") or 0)
        options.append(option)

    return sorted(
        options,
        key=lambda d: (cint(d.get("sort_order") or 0), d.get("item_name") or d.get("alternative_item") or ""),
    )


def _get_bom_ingredient_rows(menu_item_doc):
    bom_doc = _get_bom_doc(menu_item_doc)
    if not bom_doc:
        return []

    rows = []
    item_meta_cache = {}
    for row in sorted(bom_doc.get("items") or [], key=lambda d: cint(d.idx or 0)):
        alternative_options = _get_bom_row_alternative_options(bom_doc, row, item_meta_cache=item_meta_cache)
        payload = {
            "ingredient_name": row.get("restaurant_customer_label") or row.get("item_name") or row.get("item_code"),
            "customer_label": row.get("restaurant_customer_label") or row.get("item_name") or row.get("item_code"),
            "ingredient_item": (row.get("item_code") or "").strip(),
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

    bom_doc = _get_bom_doc(menu_item_doc)
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

        action_type = (option_row.get("action_type") or option_row.get("modifier_type") or "add_on").strip() or "add_on"
        if action_type not in {"add_on", "bom_variant"}:
            action_type = "add_on"

        option_item_code = (option_row.get("option_item") or "").strip()
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
            "price_delta": flt(option_row.get("price_delta")),
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
            "option_qty": flt(option_row.get("option_qty") or 1),
            "min_qty": flt(option_row.get("min_qty") if option_row.get("min_qty") not in (None, "") else 1),
            "max_qty": flt(option_row.get("max_qty") if option_row.get("max_qty") not in (None, "") else 9),
            "qty_step": flt(option_row.get("qty_step") or 1),
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
    try:
        return _get_core_item_detail(item_slug=item_slug, branch=branch)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "restaurant.api.get_item_detail")
        raise


def _ensure_mobile(value):
    mobile = "".join(ch for ch in str(value or "") if ch.isdigit())
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


def _find_customer_by_mobile(mobile):
    normalized_mobile = _ensure_mobile(mobile)

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
        info.get("address_line")
        or info.get("address")
        or info.get("address_line1")
        or ""
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

    links = doc.get("links") or []
    has_customer_link = any(
        row.get("link_doctype") == "Customer" and row.get("link_name") == customer_name
        for row in links
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
            row for row in _list_customer_delivery_addresses(customer_name)
            if row.get("id") == delivery_address_id
        ]
        if not address_rows:
            frappe.throw(_("Delivery address not found for this customer."))
        address_payload = dict(address_rows[0])

    merged_payload = {
        **address_payload,
        "title": _first_non_empty(snapshot_payload.get("title"), address_payload.get("title"), ""),
        "phone": _first_non_empty(snapshot_payload.get("phone"), snapshot_payload.get("mobile"), address_payload.get("phone"), mobile),
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
        item_payload.get("item_slug")
        or item_payload.get("menu_item_slug")
        or item_payload.get("slug")
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
        item_name = _resolve_menu_item_name_from_variant_slug(slug=slug, branch=branch)
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
        selection_only = cint(frappe.db.get_value("Item Attribute", attribute_name, "restaurant_selection_only") or 0)
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
        normalized_allowed = {str(value or "").strip() for value in allowed_values if str(value or "").strip()}
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

    row = frappe.db.get_value(
        "Item Attribute Value",
        {"parent": attribute_name, "attribute_value": value_name},
        ["idx", "abbr"],
        as_dict=True,
    ) or {}
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

        value_doc = frappe.db.get_value(
            "Item Attribute Value",
            {"parent": attribute_name, "attribute_value": value_name},
            ["abbr", "idx"],
            as_dict=True,
        ) or {}
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
            (variant.get("attr_map") or {}).get(attribute_name, "")
            for variant in candidate_variants
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
    slug = _normalize_slug(slug)
    if not slug:
        return ""

    variant_name = frappe.db.get_value(
        "Item",
        {
            "restaurant_slug": slug,
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
    slug = _normalize_slug(slug)
    if not slug:
        return ("", "")

    direct_name = frappe.db.get_value(
        "Item",
        {
            "restaurant_slug": slug,
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

    template_name = (template_row.get("name") if hasattr(template_row, "get") else getattr(template_row, "name", "")) or ""
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
    return payload


def _ingredient_base_multiplier(row):
    return 1.0 if cint(row.get("is_included_by_default")) else 0.0


def _ingredient_required(row):
    return cint(row.get("is_required")) or (cint(row.get("is_included_by_default")) and not cint(row.get("can_remove")))


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
            row.get("ingredient_key")
            or row.get("key")
            or row.get("ingredient_name")
            or row.get("name")
            or ""
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
            normalized[key] = flt(row.get("multiplier") if row.get("multiplier") is not None else row.get("qty"))

    removed_set = {str(name or "").strip() for name in (customization.get("removed_ingredients") or []) if str(name or "").strip()}
    added_set = {str(name or "").strip() for name in (customization.get("added_ingredients") or []) if str(name or "").strip()}

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
    return flt(frappe.db.get_value("Restaurant Branch Production Settings", settings_name, "pricing_markup_percent") or 0)


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
    child_doctype = ((child_row.get("doctype") if hasattr(child_row, "get") else None) or getattr(child_row, "doctype", "") or "").strip()
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
        key: _safe_div(flt(totals_for_batch.get(key) or 0), bom_qty)
        for key in NUTRITION_KEY_FIELD_MAP
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
        if any(abs(flt(row_totals.get(key) or 0) - flt(before.get(key) or 0)) > 1e-9 for key in NUTRITION_KEY_FIELD_MAP):
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

    quantity = max(flt(quantity or 1), 1)
    cfg = _menu_doc_config(menu_doc)
    base_price = flt(cfg["base_price"])
    unit_price = base_price

    ingredient_rows = _get_bom_ingredient_rows(menu_doc)
    adjustments = _normalize_ingredient_adjustments(menu_doc, customization)
    ingredient_keys = {(row.get("ingredient_name") or "").strip() for row in ingredient_rows if (row.get("ingredient_name") or "").strip()}
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
        frappe.throw(_("Invalid ingredient key for alternative selection: {0}").format(", ".join(sorted(unknown_alternative_rows))))

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
        selected_alternative = alternative_map.get(selected_alternative_item) if selected_alternative_item else None

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
            frappe.throw(_("Invalid alternative item selected for {0}: {1}").format(label, selected_alternative_item))

        selected_item_code = ingredient_item
        selected_base_qty = base_qty
        selected_stock_uom = row.get("qty_uom") or ""
        selected_item_name = frappe.db.get_value("Item", ingredient_item, "item_name") if ingredient_item else label
        extra_alternative_price = 0.0

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

            selected_stock_uom = (
                selected_alternative.get("uom")
                or selected_alternative.get("stock_uom")
                or frappe.db.get_value("Item", selected_item_code, "stock_uom")
                or selected_stock_uom
            )
            selected_item_name = (
                selected_alternative.get("item_name")
                or frappe.db.get_value("Item", selected_item_code, "item_name")
                or selected_item_code
            )
            extra_alternative_price = flt(selected_alternative.get("price_delta") or 0)
            normalized_selected_alternatives.append(
                {
                    "ingredient_key": ingredient_name,
                    "alternative_item": selected_item_code,
                }
            )

        base_rate = _valuation_rate_for_item(ingredient_item)
        selected_rate = _valuation_rate_for_item(selected_item_code)
        delta_multiplier = selected_multiplier - base_multiplier
        if ingredient_item or selected_item_code:
            base_component_qty = base_qty * base_multiplier
            selected_component_qty = selected_base_qty * selected_multiplier
            base_component_cost = base_component_qty * base_rate if ingredient_item else 0
            selected_component_cost = selected_component_qty * selected_rate if selected_item_code else 0
            delta_price = (selected_component_cost - base_component_cost) * markup_factor
            if selected_alternative:
                delta_price += extra_alternative_price * selected_multiplier
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
                "pricing_rate": selected_rate,
                "pricing_delta": delta_price,
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
    variant_selected_rows = [row for row in selected_raw_all if (row.get("group") or "").startswith("variant::")]
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
        raw_group = (selected.get("group") or selected.get("group_name") or selected.get("title") or "").strip()
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

        modifier_type = (option_payload.get("action_type") or option_payload.get("modifier_type") or "add_on").strip() or "add_on"
        option_label = (option_payload.get("label") or option_name).strip()
        option_item = (option_payload.get("option_item") or "").strip()
        replacement_for = (option_payload.get("replacement_for_item") or "").strip()
        alternative_bom = (option_payload.get("alternative_bom") or "").strip()
        option_qty = flt(option_payload.get("option_qty") or 1)
        if option_qty <= 0:
            option_qty = 1

        option_min_qty = max(flt(option_payload.get("min_qty") if option_payload.get("min_qty") not in (None, "") else 1), 0)
        option_max_qty = max(
            flt(option_payload.get("max_qty") if option_payload.get("max_qty") not in (None, "") else 9),
            option_min_qty,
        )
        option_step = flt(option_payload.get("qty_step") or 1)
        if option_step <= 0:
            option_step = 1

        qty = flt(selected.get("qty") if selected.get("qty") not in (None, "") else option_min_qty or 1)
        if qty <= 0:
            qty = option_min_qty if option_min_qty > 0 else option_step

        if qty < option_min_qty - 1e-8 or qty > option_max_qty + 1e-8:
            frappe.throw(
                _("Modifier qty for {0} must be between {1} and {2}.").format(
                    option_label,
                    option_min_qty,
                    option_max_qty,
                )
            )

        if not _step_valid(qty, option_min_qty, option_step):
            frappe.throw(
                _("Modifier qty for {0} must follow step {1}.").format(option_label, option_step)
            )

        delta = flt(option_payload.get("price_delta")) * qty

        if modifier_type == "bom_variant" and alternative_bom:
            bom_meta = frappe.db.get_value(
                "BOM",
                alternative_bom,
                ["item", "docstatus", "is_active"],
                as_dict=True,
            )
            if not bom_meta or bom_meta.item != menu_doc.item_code or cint(bom_meta.docstatus) != 1 or not cint(bom_meta.is_active):
                frappe.throw(_("Invalid BOM variant for option: {0}").format(option_label))
            selected_bom = alternative_bom

        if modifier_type == "replacement":
            frappe.throw(
                _("Replacement modifiers are deprecated. Configure alternatives in BOM Item instead: {0}").format(option_label)
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
                    "base_qty": option_qty,
                    "selected_base_qty": option_qty,
                    "base_multiplier": 0,
                    "selected_multiplier": qty,
                    "is_required": 0,
                    "is_included_by_default": 0,
                    "can_remove": 1,
                    "is_editable_qty": 1,
                    "min_multiplier": option_min_qty,
                    "max_multiplier": option_max_qty,
                    "step_multiplier": option_step,
                    "pricing_rate": _valuation_rate_for_item(option_item),
                    "pricing_delta": delta,
                    "stock_uom": option_stock_uom,
                    "source_type": "modifier_add_on",
                }
            )
            option_item_doc = frappe.get_cached_doc("Item", option_item)
            option_nutrition = _nutrition_per_unit_payload(option_item_doc)
            option_factor = _nutrition_factor_from_item_qty(option_item, option_qty * qty, option_stock_uom)
            _add_nutrition_to_totals(nutrition_totals, option_nutrition, option_factor)

        unit_price += delta
        modifier_delta_total += delta
        selected_by_group[group_name] += 1
        line_recipe_multiplier *= math.pow(recipe_multiplier, qty)
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

        label_suffix = f" x{qty:g}" if abs(flt(qty) - 1) > 1e-8 else ""
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
            frappe.throw(_("Please select more options for group: {0}").format(group["title"]))
        if count > cint(group["max_select"]):
            frappe.throw(_("Too many selected options for group: {0}").format(group["title"]))

    line_total = unit_price * quantity
    nutrition_unit = _nutrition_payload_from_totals(nutrition_totals)
    nutrition_line_totals = {key: round(flt(nutrition_unit.get(key) or 0) * quantity, 4) for key in NUTRITION_KEY_FIELD_MAP}
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


@frappe.whitelist(allow_guest=True)
def get_customer_checkout_profile(mobile, customer_name=None):
    normalized_mobile = _ensure_mobile(mobile)
    customer_docname = _find_customer_by_mobile(normalized_mobile)

    resolved_name = (customer_name or "").strip()
    addresses = []
    if customer_docname:
        if not resolved_name:
            resolved_name = frappe.db.get_value("Customer", customer_docname, "customer_name") or ""
        addresses = _list_customer_delivery_addresses(customer_docname)

    return {
        "customer": {
            "name": resolved_name,
            "mobile": normalized_mobile,
            "customer_id": customer_docname or "",
            "exists": 1 if customer_docname else 0,
        },
        "addresses": addresses,
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
    delivery_address_id = (delivery_address_id or "").strip()
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
            "restaurant_order_code": order_code,
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
            "restaurant_order_code": order_code,
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
    if _has_column("Sales Order", "restaurant_order_code"):
        mapped = frappe.db.get_value("Sales Order", {"restaurant_order_code": so_name}, "name")
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
        if not item_code or final_qty <= 1e-8:
            continue
        qty_map[item_code] += final_qty * scale_factor
    return qty_map


def _resolve_ticket_for_work_order_doc(work_order_doc):
    if not frappe.db.exists("DocType", "Restaurant Production Ticket"):
        return None

    explicit_ticket = (
        (work_order_doc.get("restaurant_production_ticket") if hasattr(work_order_doc, "get") else None)
        or ""
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
                frappe.db.get_value("Sales Order Item", sales_order_item, "restaurant_production_ticket") or ""
            ).strip()
        if not linked_ticket and _has_column("Restaurant Production Ticket", "sales_order_item"):
            linked_ticket = (
                frappe.db.get_value("Restaurant Production Ticket", {"sales_order_item": sales_order_item}, "name")
                or ""
            ).strip()
        if linked_ticket and frappe.db.exists("Restaurant Production Ticket", linked_ticket):
            return frappe.get_doc("Restaurant Production Ticket", linked_ticket)

    sales_order = ((work_order_doc.get("sales_order") if hasattr(work_order_doc, "get") else None) or "").strip()
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
    if _has_column("Work Order", "restaurant_sales_order") and not (doc.get("restaurant_sales_order") or "").strip():
        updates["restaurant_sales_order"] = (doc.get("sales_order") or "").strip()
    if _has_column("Work Order", "restaurant_sales_order_item") and not (
        doc.get("restaurant_sales_order_item") or ""
    ).strip():
        updates["restaurant_sales_order_item"] = (doc.get("sales_order_item") or "").strip()
    if _has_column("Work Order", "restaurant_order_code") and not (doc.get("restaurant_order_code") or "").strip():
        order_code = (
            frappe.db.get_value("Sales Order", doc.get("sales_order"), "restaurant_order_code")
            if doc.get("sales_order")
            else ""
        ) or ""
        updates["restaurant_order_code"] = order_code or (doc.get("sales_order") or "")
    if updates:
        frappe.db.set_value("Work Order", doc.name, updates, update_modified=False)

    source_warehouse = (
        (doc.get("source_warehouse") or "").strip() or (ticket_doc.get("source_warehouse") or "").strip()
    )
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
            _sync_work_order_required_items(ticket_doc.work_order, qty_map=qty_map, source_warehouse=source_warehouse)
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

            source_warehouse = (
                (existing_wo_row.source_warehouse or "").strip() or (ticket_doc.get("source_warehouse") or "").strip()
            )
            _sync_work_order_required_items(existing_wo_row.name, qty_map=qty_map, source_warehouse=source_warehouse)
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
        branch = (ticket_doc.get("branch") or menu_doc.get("restaurant_branch") or "DEFAULT").strip() or "DEFAULT"
        try:
            settings = _get_branch_production_settings(branch, so_doc.company)
        except Exception as exc:
            skipped_tickets.append({"ticket": ticket_name, "reason": "missing_branch_settings", "message": str(exc)})
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
    ticket_name = ((doc.get("name") if hasattr(doc, "get") else None) or getattr(doc, "name", "") or "").strip()
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
MANAGEMENT_SITE_SETTINGS_ALLOWED_ROLES = {"System Manager", "Desk User", "Restaurant Manager", "Website Manager"}
MANAGEMENT_WEB_REVENUE_STATUSES = {"new", "confirmed", "preparing", "ready", "delivered"}
MANAGEMENT_TABLE_REVENUE_STATUSES = {"confirmed", "served", "paid"}


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
        frappe.throw(_("You don't have permission to change website content settings."), frappe.PermissionError)


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
    subtitle = (source.get("loader_subtitle") or "").strip() or MANAGEMENT_SITE_LOADER_DEFAULTS["loader_subtitle"]
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


def _management_site_settings_payload():
    _ensure_menu_highlight_setting_fields()
    loader_fallback = _load_management_loader_settings()

    def _to_int(value, default=0):
        try:
            return cint(value)
        except Exception:
            return default

    web_settings = {}
    try:
        settings_doc = frappe.get_cached_doc("Restaurant Web Settings")
        web_settings = {
            "brand_name": settings_doc.get("brand_name") or "",
            "brand_tagline": settings_doc.get("brand_tagline") or "",
            "default_currency": settings_doc.get("default_currency") or "IRR",
            "hero_title": settings_doc.get("hero_title") or "",
            "hero_subtitle": settings_doc.get("hero_subtitle") or "",
            "hero_image": settings_doc.get("hero_image") or "",
            "primary_cta_label": settings_doc.get("primary_cta_label") or "",
            "loader_enabled": cint(
                settings_doc.get("loader_enabled")
                if settings_doc.get("loader_enabled") not in (None, "")
                else 1
            ),
            "loader_mode": settings_doc.get("loader_mode") or "preset",
            "loader_preset": settings_doc.get("loader_preset") or "steaming-bowl",
            "loader_title": settings_doc.get("loader_title") or "در حال آماده سازی سفارش",
            "loader_subtitle": settings_doc.get("loader_subtitle") or "آشپزخانه مشغول آماده کردن سفارش شماست...",
            "loader_min_duration_ms": cint(
                settings_doc.get("loader_min_duration_ms")
                if settings_doc.get("loader_min_duration_ms") not in (None, "")
                else 1400
            ),
            "loader_overlay_color": settings_doc.get("loader_overlay_color") or "#F6F4ED",
            "loader_accent_color": settings_doc.get("loader_accent_color") or "#6A9A6B",
            "loader_custom_code": settings_doc.get("loader_custom_code") or "",
            "restaurant_menu_highlight_enabled": cint(
                settings_doc.get("restaurant_menu_highlight_enabled")
                if settings_doc.get("restaurant_menu_highlight_enabled") not in (None, "")
                else 1
            ),
            "restaurant_menu_highlight_title": settings_doc.get("restaurant_menu_highlight_title") or "ویژه و پرفروش",
            "restaurant_menu_highlight_show_featured": cint(
                settings_doc.get("restaurant_menu_highlight_show_featured")
                if settings_doc.get("restaurant_menu_highlight_show_featured") not in (None, "")
                else 1
            ),
            "restaurant_menu_highlight_featured_limit": cint(
                settings_doc.get("restaurant_menu_highlight_featured_limit")
                if settings_doc.get("restaurant_menu_highlight_featured_limit") not in (None, "")
                else 10
            ),
            "restaurant_menu_highlight_show_best_seller": cint(
                settings_doc.get("restaurant_menu_highlight_show_best_seller")
                if settings_doc.get("restaurant_menu_highlight_show_best_seller") not in (None, "")
                else 1
            ),
            "restaurant_menu_highlight_best_seller_limit": cint(
                settings_doc.get("restaurant_menu_highlight_best_seller_limit")
                if settings_doc.get("restaurant_menu_highlight_best_seller_limit") not in (None, "")
                else 10
            ),
        }
    except Exception:
        web_settings = {
            "brand_name": "",
            "brand_tagline": "",
            "default_currency": "IRR",
            "hero_title": "",
            "hero_subtitle": "",
            "hero_image": "",
            "primary_cta_label": "",
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

    web_settings.update(_sanitize_management_loader_settings({**loader_fallback, **web_settings}))

    faq_items = []
    if frappe.db.exists("DocType", "Restaurant FAQ"):
        faq_fields = ["name"]
        for fieldname in ["question", "answer", "sort_order", "is_active"]:
            if _has_column("Restaurant FAQ", fieldname):
                faq_fields.append(fieldname)
        faq_order_by = "sort_order asc, modified asc" if _has_column("Restaurant FAQ", "sort_order") else "modified asc"
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
            "sort_order asc, modified asc" if _has_column("Restaurant About Section", "sort_order") else "modified asc"
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
def set_management_site_settings(payload=None):
    _ensure_management_site_settings_access()
    data = _parse_json(payload, {})
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

    if web_settings and frappe.db.exists("DocType", "Restaurant Web Settings"):
        settings_doc = frappe.get_doc("Restaurant Web Settings", "Restaurant Web Settings")
        scalar_fields = [
            "brand_name",
            "brand_tagline",
            "default_currency",
            "hero_title",
            "hero_subtitle",
            "hero_image",
            "primary_cta_label",
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
            "loader_enabled",
            "loader_min_duration_ms",
            "restaurant_menu_highlight_enabled",
            "restaurant_menu_highlight_show_featured",
            "restaurant_menu_highlight_featured_limit",
            "restaurant_menu_highlight_show_best_seller",
            "restaurant_menu_highlight_best_seller_limit",
        ]
        for fieldname in scalar_fields:
            if fieldname not in web_settings or not _has_column("Restaurant Web Settings", fieldname):
                continue
            value = (web_settings.get(fieldname) or "").strip()
            if fieldname == "brand_name" and not value:
                value = (settings_doc.get("brand_name") or "").strip() or "Restaurant"
            settings_doc.set(fieldname, value)
        for fieldname in int_fields:
            if fieldname not in web_settings or not _has_column("Restaurant Web Settings", fieldname):
                continue
            settings_doc.set(fieldname, cint(web_settings.get(fieldname) or 0))
        settings_doc.save(ignore_permissions=True)

    if "faq_items" in data:
        _sync_management_site_doctype_rows(
            "Restaurant FAQ",
            data.get("faq_items"),
            lambda row, index: {
                "question": (row.get("question") or "").strip(),
                "answer": (row.get("answer") or "").strip(),
                "sort_order": cint(row.get("sort_order") or index),
                "is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
            }
            if (row.get("question") or "").strip() and (row.get("answer") or "").strip()
            else None,
        )

    if "about_sections" in data:
        _sync_management_site_doctype_rows(
            "Restaurant About Section",
            data.get("about_sections"),
            lambda row, index: {
                "section_type": ((row.get("section_type") or "story").strip() or "story"),
                "title": (row.get("title") or "").strip() or "بخش درباره ما",
                "subtitle": (row.get("subtitle") or "").strip(),
                "badge": (row.get("badge") or "").strip(),
                "founded_year": (row.get("founded_year") or "").strip(),
                "icon": (row.get("icon") or "").strip(),
                "year_label": (row.get("year_label") or "").strip(),
                "highlight": cint(row.get("highlight") if row.get("highlight") not in (None, "") else 0),
                "body_text": (row.get("body_text") or "").strip() or "توضیحات این بخش هنوز تکمیل نشده است.",
                "image": (row.get("image") or "").strip(),
                "stat_label": (row.get("stat_label") or "").strip(),
                "stat_value": (row.get("stat_value") or "").strip(),
                "sort_order": cint(row.get("sort_order") or index),
                "is_active": cint(row.get("is_active") if row.get("is_active") not in (None, "") else 1),
            }
            if (row.get("title") or "").strip() or (row.get("body_text") or "").strip() or (row.get("section_type") or "").strip()
            else None,
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
    return _management_site_settings_payload()


def _management_date_window(date_from=None, date_to=None, default_days=30):
    end_date = getdate(date_to) if date_to else getdate(nowdate())
    start_date = getdate(date_from) if date_from else add_days(end_date, -(cint(default_days) - 1))
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    return str(start_date), str(end_date)


def _management_datetime_bounds(date_from=None, date_to=None, default_days=30):
    start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to, default_days=default_days)
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
    filters = {}
    if has_transaction_date:
        filters["transaction_date"] = ["between", [start_date, end_date]]
    else:
        filters["creation"] = ["between", [start_dt, end_dt]]
    if cashier:
        filters["owner"] = cashier

    has_order_code = _has_column("Sales Order", "restaurant_order_code")
    has_mobile = _has_column("Sales Order", "restaurant_customer_mobile")
    has_order_type = _has_column("Sales Order", "restaurant_order_type")
    has_note = _has_column("Sales Order", "restaurant_note")
    has_payment_method = _has_column("Sales Order", "restaurant_payment_method")
    has_payment_status = _has_column("Sales Order", "restaurant_payment_status")
    has_payment_provider = _has_column("Sales Order", "restaurant_payment_provider")

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
    if has_order_code:
        fields.append("restaurant_order_code")
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
                    "line_total": line_total,
                    "customization_json": item.restaurant_customization_json if has_item_customization else "",
                    "pricing_breakdown": pricing_breakdown if isinstance(pricing_breakdown, dict) else {},
                    "nutrition": pricing_breakdown.get("nutrition") if isinstance(pricing_breakdown, dict) else {},
                    "nutrition_totals": pricing_breakdown.get("nutrition_totals")
                    if isinstance(pricing_breakdown, dict)
                    else {},
                }
            )

    normalized_status = (status or "").strip().lower()
    payload = []
    for row in rows:
        order_status = _core_order_status(row)
        if normalized_status and order_status != normalized_status:
            continue

        created_at = _management_business_datetime(
            date_value=row.get("transaction_date") if has_transaction_date else None,
            fallback_datetime=row.creation,
        ) or row.creation
        payload.append(
            {
                "source": "web",
                "doctype": "Sales Order",
                "name": row.name,
                "order_code": (row.restaurant_order_code if has_order_code else "") or row.name,
                "customer_name": row.customer_name or "POS Customer",
                "mobile": (row.restaurant_customer_mobile if has_mobile else "") or mobile_by_customer.get(row.customer, ""),
                "channel": (row.restaurant_order_type if has_order_type else "") or "takeaway",
                "status": order_status,
                "subtotal": flt(row.total or row.net_total),
                "grand_total": flt(row.grand_total or row.total or row.net_total),
                "created_at": _json_safe_datetime(created_at),
                "cashier": row.owner or "",
                "note": row.restaurant_note if has_note else "",
                "payment_method": row.restaurant_payment_method if has_payment_method else "",
                "payment_status": row.restaurant_payment_status if has_payment_status else "",
                "payment_provider": row.restaurant_payment_provider if has_payment_provider else "",
                "items": items_by_parent.get(row.name, []),
            }
        )
    return payload


def _management_fetch_table_orders(date_from=None, date_to=None, status=None, cashier=None):
    if not frappe.db.exists("DocType", "Restaurant Table Order"):
        return []

    start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
    has_created_at = _has_column("Restaurant Table Order", "created_at")
    filters = {}
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
    if menu_item_names and frappe.db.exists("DocType", "Restaurant Table Menu Item"):
        menu_rows = frappe.get_all(
            "Restaurant Table Menu Item",
            fields=["name", "item_name"],
            filters={"name": ["in", list(menu_item_names)]},
            ignore_permissions=True,
        )
        menu_title_map = {row.name: row.item_name for row in menu_rows}

    items_by_parent = defaultdict(list)
    for item in item_rows:
        items_by_parent[item.parent].append(
            {
                "title": menu_title_map.get(item.menu_item) or item.menu_item or "",
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
        expected_support = _safe_div((left_count * right_count), total_orders * total_orders) if total_orders else 0
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

    return [
        {"date": date_key, "sales": grouped[date_key]}
        for date_key in sorted(grouped.keys())
    ]


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
        if any(token in normalized for token in ["sales", "amount", "spent", "total", "ticket", "line_total"]):
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
            _bi_kpi("total_sales", _("Total Sales"), summary.get("total_sales"), "money", prev_summary.get("total_sales")),
            _bi_kpi("total_orders", _("Total Orders"), summary.get("total_orders"), "count", prev_summary.get("total_orders")),
            _bi_kpi("avg_ticket", _("Average Ticket"), summary.get("avg_ticket"), "money", prev_summary.get("avg_ticket")),
            _bi_kpi("total_items", _("Items Sold"), summary.get("total_items"), "count", prev_summary.get("total_items")),
        ]
        charts = [
            {
                "key": "daily-sales-orders",
                "title": _("Daily Sales vs Orders"),
                "type": "line",
                "unit": "money",
                "labels": daily.get("labels"),
                "series": [
                    {"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": daily.get("sales_values")},
                    {"key": "orders", "label": _("Orders"), "color": "#3e8ed0", "values": daily.get("order_values")},
                ],
            }
        ]
        table_rows = [
            {
                "date": label,
                "sales": daily.get("sales_values")[idx],
                "orders": daily.get("order_values")[idx],
                "avg_ticket": round(_safe_div(daily.get("sales_values")[idx], daily.get("order_values")[idx]), 2),
            }
            for idx, label in enumerate(daily.get("labels") or [])
        ]
        tables = [{"key": "daily-table", "title": _("Daily Breakdown"), "columns": _table_columns_from_rows(table_rows), "rows": table_rows}]
        if daily.get("sales_values"):
            peak_index = max(range(len(daily.get("sales_values"))), key=lambda idx: daily.get("sales_values")[idx])
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
            table_rows.append({"date": row.get("date"), "sales": sales, "expected_sales": expected, "delta_percent": delta_pct})
        kpis = [
            _bi_kpi("total_sales", _("Total Sales"), summary.get("total_sales"), "money", previous_total),
            _bi_kpi("days", _("Days in Range"), summary.get("days"), "count", len(prev_rows)),
            _bi_kpi("expected_daily", _("Expected Daily Sales"), expected_daily, "money", expected_daily),
            _bi_kpi("variance", _("Sales vs Expected"), summary.get("total_sales") - (expected_daily * max(cint(summary.get("days")), 1)), "money", 0),
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
                    {"key": "expected", "label": _("Expected"), "color": "#3e8ed0", "values": expected_values},
                ],
            },
            {
                "key": "cumulative-sales",
                "title": _("Cumulative Sales"),
                "type": "area",
                "unit": "money",
                "labels": labels,
                "series": [{"key": "cumulative", "label": _("Cumulative"), "color": "#da8a2f", "values": _series_cumulative(sales_values)}],
            },
        ]
        tables = [{"key": "trend-table", "title": _("Daily Trend"), "columns": _table_columns_from_rows(table_rows), "rows": table_rows}]

    elif report_key == "sales-hourly":
        prev_rows = _build_hourly_trend(previous_orders)
        previous_sales = sum(flt(row.get("sales")) for row in prev_rows)
        previous_orders_count = sum(cint(row.get("orders")) for row in prev_rows)
        hour_rows = rows or []
        peak_row = max(hour_rows, key=lambda row: flt(row.get("sales")), default={"hour": 0, "sales": 0, "orders": 0})
        labels = [str(row.get("hour")).zfill(2) for row in hour_rows]
        sales_values = [flt(row.get("sales")) for row in hour_rows]
        order_values = [cint(row.get("orders")) for row in hour_rows]
        avg_hourly = round(_safe_div(sum(sales_values), len(hour_rows) or 1), 2)
        kpis = [
            _bi_kpi("total_sales", _("Total Sales"), summary.get("total_sales"), "money", previous_sales),
            _bi_kpi("total_orders", _("Total Orders"), summary.get("total_orders"), "count", previous_orders_count),
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
                "series": [{"key": "orders", "label": _("Orders"), "color": "#3e8ed0", "values": order_values}],
            },
        ]
        tables = [{"key": "hour-table", "title": _("Hourly Breakdown"), "columns": _table_columns_from_rows(hour_rows), "rows": hour_rows}]
        insights = [
            {
                "key": "peak-hour-note",
                "severity": "info",
                "text": _("Peak traffic hour: {0}:00 with {1} orders.").format(str(peak_row.get("hour")).zfill(2), cint(peak_row.get("orders"))),
            }
        ]

    elif report_key == "top-products":
        prev_rows = _build_top_products(previous_orders, limit=20)
        previous_total = sum(flt(row.get("amount")) for row in prev_rows)
        data_rows = rows or []
        total_sales = sum(flt(row.get("amount")) for row in data_rows)
        total_qty = sum(flt(row.get("qty")) for row in data_rows)
        top_item = data_rows[0] if data_rows else {}
        top5_share = round(_safe_div(sum(flt(row.get("amount")) for row in data_rows[:5]) * 100.0, total_sales or 1), 2)
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
                    {"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": [flt(row.get("amount")) for row in data_rows[:10]]}
                ],
            },
            {
                "key": "products-by-qty",
                "title": _("Top Products by Quantity"),
                "type": "bar",
                "unit": "count",
                "labels": labels,
                "series": [
                    {"key": "qty", "label": _("Quantity"), "color": "#da8a2f", "values": [flt(row.get("qty")) for row in data_rows[:10]]}
                ],
            },
        ]
        normalized_rows = []
        for row in data_rows:
            share = row.get("share_percent")
            if share in (None, ""):
                share = round(_safe_div(flt(row.get("amount")) * 100.0, total_sales or 1), 2)
            normalized_rows.append({**row, "share_percent": share, "avg_price": round(_safe_div(row.get("amount"), row.get("qty")), 2)})
        tables = [{"key": "product-table", "title": _("Product Breakdown"), "columns": _table_columns_from_rows(normalized_rows), "rows": normalized_rows}]
        insights = [
            {
                "key": "top-product",
                "severity": "success",
                "text": _("Top product: {0} with sales {1}.").format(top_item.get("product_title") or "-", frappe.format_value(top_item.get("amount") or 0, {"fieldtype": "Currency", "options": currency})),
            }
        ] if top_item else []

    elif report_key == "product-mix":
        prev_rows = _build_product_mix_associations(previous_orders, limit=80, min_pair_orders=2, min_base_orders=2)
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
            _bi_kpi("avg_confidence", _("Average Confidence"), avg_confidence, "percent", prev_avg_confidence),
            _bi_kpi("strong_rules", _("Rules >= 50% Confidence"), len(strong_rules), "count", len(prev_strong_rules)),
            _bi_kpi("top_confidence", _("Top Confidence"), top_rule.get("confidence_percent") or 0, "percent", 0),
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
        for product_title, row in sorted(best_by_product.items(), key=lambda item: flt(item[1].get("confidence_percent")), reverse=True):
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
            _bi_kpi("delivered_rate", _("Delivered Rate"), round(_safe_div(delivered * 100.0, total_orders or 1), 2), "percent", 0),
            _bi_kpi("cancelled_rate", _("Cancelled Rate"), round(_safe_div(cancelled * 100.0, total_orders or 1), 2), "percent", 0),
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
                "series": [{"key": "orders", "label": _("Orders"), "color": "#2f6f5c", "values": [cint(row.get("orders")) for row in rows]}],
            },
            {
                "key": "sales-by-status",
                "title": _("Sales by Status"),
                "type": "bar",
                "unit": "money",
                "labels": labels,
                "series": [{"key": "sales", "label": _("Sales"), "color": "#3e8ed0", "values": [flt(row.get("sales")) for row in rows]}],
            },
        ]
        tables = [{"key": "status-table", "title": _("Status Breakdown"), "columns": _table_columns_from_rows(rows), "rows": rows}]

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
            _bi_kpi("dine_in_share", _("Dine-In Share"), round(_safe_div(dine_sales * 100.0, total_sales or 1), 2), "percent", 0),
            _bi_kpi("takeaway_share", _("Takeaway Share"), round(_safe_div(takeaway_sales * 100.0, total_sales or 1), 2), "percent", 0),
            _bi_kpi("delivery_share", _("Delivery Share"), round(_safe_div(delivery_sales * 100.0, total_sales or 1), 2), "percent", 0),
        ]
        labels = [row.get("channel") for row in rows]
        charts = [
            {
                "key": "channel-sales",
                "title": _("Sales by Channel"),
                "type": "bar",
                "unit": "money",
                "labels": labels,
                "series": [{"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": [flt(row.get("sales")) for row in rows]}],
            },
            {
                "key": "channel-orders",
                "title": _("Orders by Channel"),
                "type": "bar",
                "unit": "count",
                "labels": labels,
                "series": [{"key": "orders", "label": _("Orders"), "color": "#da8a2f", "values": [cint(row.get("orders")) for row in rows]}],
            },
        ]
        tables = [{"key": "channel-table", "title": _("Channel Breakdown"), "columns": _table_columns_from_rows(rows), "rows": rows}]

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
                "series": [{"key": "sales", "label": _("Sales"), "color": "#2f6f5c", "values": [flt(row.get("sales")) for row in rows[:10]]}],
            },
            {
                "key": "cashier-orders",
                "title": _("Orders by Cashier"),
                "type": "bar",
                "unit": "count",
                "labels": labels,
                "series": [{"key": "orders", "label": _("Orders"), "color": "#3e8ed0", "values": [cint(row.get("orders")) for row in rows[:10]]}],
            },
        ]
        tables = [{"key": "cashier-table", "title": _("Cashier Performance"), "columns": _table_columns_from_rows(rows), "rows": rows}]

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
            _bi_kpi("cancelled_amount", _("Cancelled Amount"), cancelled_amount, "money", prev_cancelled_amount),
            _bi_kpi("cancel_rate", _("Cancel Rate"), round(_safe_div(len(rows) * 100.0, total_orders or 1), 2), "percent", 0),
            _bi_kpi("lost_amount", _("Lost Revenue"), cancelled_amount, "money", prev_cancelled_amount),
        ]
        charts = [
            {
                "key": "cancelled-count-trend",
                "title": _("Cancellation Count Trend"),
                "type": "line",
                "unit": "count",
                "labels": labels,
                "series": [{"key": "count", "label": _("Cancelled Orders"), "color": "#b84f4f", "values": [by_date[key]["count"] for key in labels]}],
            },
            {
                "key": "cancelled-amount-trend",
                "title": _("Cancellation Amount Trend"),
                "type": "bar",
                "unit": "money",
                "labels": labels,
                "series": [{"key": "amount", "label": _("Cancelled Amount"), "color": "#da8a2f", "values": [round(by_date[key]["amount"], 2) for key in labels]}],
            },
        ]
        tables = [{"key": "cancellation-table", "title": _("Cancellation Orders"), "columns": _table_columns_from_rows(rows), "rows": rows}]
        if cancelled_amount > 0:
            insights.append({"key": "cancel-risk", "severity": "warn", "text": _("There is a measurable cancellation impact in this window.")})

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
            _bi_kpi("top_modifier_usage", _("Top Modifier Usage"), top_modifier.get("usage_count") or 0, "count", 0),
            _bi_kpi("usage_per_order", _("Usage per Order"), usage_per_order, "count", usage_per_order),
        ]
        charts = [
            {
                "key": "top-modifier-usage",
                "title": _("Top Modifier Usage"),
                "type": "bar",
                "unit": "count",
                "labels": labels,
                "series": [{"key": "usage", "label": _("Usage"), "color": "#2f6f5c", "values": [cint(row.get("usage_count")) for row in rows[:10]]}],
            },
            {
                "key": "group-modifier-usage",
                "title": _("Usage by Group"),
                "type": "bar",
                "unit": "count",
                "labels": list(group_rows.keys()),
                "series": [{"key": "group_usage", "label": _("Usage"), "color": "#3e8ed0", "values": [cint(value) for value in group_rows.values()]}],
            },
        ]
        tables = [{"key": "modifier-table", "title": _("Modifier Usage"), "columns": _table_columns_from_rows(rows), "rows": rows}]

    if not tables and rows:
        tables = [{"key": "report-table", "title": _("Report Table"), "columns": _table_columns_from_rows(rows), "rows": rows}]

    return {
        "meta": meta,
        "kpis": kpis,
        "charts": charts,
        "tables": tables,
        "insights": insights,
        "currency": currency,
    }


def _compose_management_report(report_key, title, summary, rows, date_from=None, date_to=None, source="all", orders=None):
    current_orders = orders if orders is not None else _management_collect_orders(date_from=date_from, date_to=date_to, source=source)
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
    has_order_code = _has_column("Sales Order", "restaurant_order_code")
    if not rating_field and not delivery_field:
        return metrics

    start_date, end_date = _management_date_window(date_from=date_from, date_to=date_to)
    start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
    has_transaction_date = _has_column("Sales Order", "transaction_date")
    fields = ["name"]
    if has_order_code:
        fields.append("restaurant_order_code")
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
                    max_delivery_order = (row.get("restaurant_order_code") if has_order_code else "") or row.get("name")

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
        value = (item_doc.get(fieldname) if hasattr(item_doc, "get") else getattr(item_doc, fieldname, "")) or ""
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
            or (_("Local node is connected.") if health.get("ok") else (health.get("error") or _("Local node is offline."))),
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
def report_management_pos_hardware_event(event_type, severity, message, payload=None, related_order=None, source="pos"):
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
def get_management_pos_boot(branch=None):
    _ensure_management_access()
    branch = (branch or "").strip()
    image_field = _core_item_image_field()
    category_meta_map = _get_core_category_meta_map()
    subcategory_meta_map = _get_core_subcategory_meta_map()
    rows = frappe.get_all(
        "Item",
        filters=_core_item_filters(branch),
        fields=[
            "name",
            "item_name",
            "restaurant_slug",
            "restaurant_short_desc",
            "restaurant_base_price",
            "standard_rate",
            f"{image_field} as image",
            "restaurant_category",
            "restaurant_subcategory",
        ],
        ignore_permissions=True,
        order_by="restaurant_sort_order asc, item_name asc",
        limit=300,
    )
    items = [
        _serialize_core_item(
            row,
            category_meta_map=category_meta_map,
            subcategory_meta_map=subcategory_meta_map,
        )
        for row in rows
    ]
    categories = [
        {
            "name": key,
            "title": value.get("title"),
            "slug": value.get("slug"),
        }
        for key, value in category_meta_map.items()
    ]
    return {
        "currency": _get_currency(),
        "items": items,
        "categories": sorted(categories, key=lambda row: row.get("title") or ""),
        "payment": _management_pos_payment_boot(),
        "pos_profile": _management_pos_profile_summary(),
    }


@frappe.whitelist()
def create_management_pos_order(payload):
    _ensure_management_access()
    payload = _parse_json(payload, {})
    if not isinstance(payload, dict):
        payload = {}

    customer_name = (payload.get("customer_name") or "POS Customer").strip()
    mobile = (payload.get("mobile") or "09120000000").strip()
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

    frappe.db.commit()
    return result


@frappe.whitelist()
def confirm_management_pos_payment(order_name, status="paid", reference_no=None, rrn=None, provider_payload=None):
    _ensure_management_access()

    so_name = _resolve_sales_order_name(order_name)
    if not so_name:
        frappe.throw(_("Order not found."), frappe.DoesNotExistError)

    existing_method = "card"
    if _has_column("Sales Order", "restaurant_payment_method"):
        existing_method = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_method") or "card"

    existing_provider = "manual"
    if _has_column("Sales Order", "restaurant_payment_provider"):
        existing_provider = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_provider") or "manual"

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
        "order_code": frappe.db.get_value("Sales Order", so_name, "restaurant_order_code") or so_name,
        "payment": payment_result,
        "automation": automation_payload or {},
    }


def _manual_management_payment_result(so_name, status="paid", reference_no=None, rrn=None, provider_payload=None):
    existing_method = "card"
    if _has_column("Sales Order", "restaurant_payment_method"):
        existing_method = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_method") or "card"

    existing_provider = "manual"
    if _has_column("Sales Order", "restaurant_payment_provider"):
        existing_provider = frappe.db.get_value("Sales Order", so_name, "restaurant_payment_provider") or "manual"

    return {
        "method": _normalize_payment_method(existing_method),
        "provider": (existing_provider or "manual").strip().lower() or "manual",
        "status": _normalize_payment_status(status),
        "reference_no": (reference_no or "").strip(),
        "rrn": (rrn or "").strip(),
        "message": _("Payment status updated manually."),
        "provider_payload": _parse_json(provider_payload, {}),
    }


@frappe.whitelist()
def mark_management_order_paid(order_name, reference_no=None, rrn=None, provider_payload=None):
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
    _append_sales_order_note(so_name, "[PAYMENT] پرداخت سفارش ثبت شد (paid)")

    frappe.db.commit()
    return {
        "status": "success",
        "order_name": so_name,
        "order_code": frappe.db.get_value("Sales Order", so_name, "restaurant_order_code") or so_name,
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
        "order_code": frappe.db.get_value("Sales Order", so_name, "restaurant_order_code") or so_name,
        "payment": payment_result,
        "restaurant_status": _core_order_status(frappe.get_doc("Sales Order", so_name)),
    }


@frappe.whitelist()
def void_management_pos_order(order_name, reason=None):
    _ensure_management_access()
    if not order_name:
        frappe.throw(_("Order name is required."))

    so_name = order_name
    if not frappe.db.exists("Sales Order", so_name) and _has_column("Sales Order", "restaurant_order_code"):
        so_name = frappe.db.get_value("Sales Order", {"restaurant_order_code": order_name}, "name")
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
        "order_code": doc.get("restaurant_order_code") or doc.name,
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
        elif _has_column("Sales Order", "restaurant_order_code"):
            so_name = frappe.db.get_value("Sales Order", {"restaurant_order_code": order_name}, "name")

        if so_name:
            doc = frappe.get_doc("Sales Order", so_name)
            has_item_customization = _has_column("Sales Order Item", "restaurant_customization_json")
            items = []
            for row in (doc.items or []):
                amount = row.get("amount")
                if amount in (None, ""):
                    amount = row.get("base_amount")
                items.append(
                    {
                        "title": row.item_name,
                        "qty": flt(row.qty),
                        "line_total": flt(amount if amount not in (None, "") else flt(row.rate) * flt(row.qty)),
                        "customization_json": row.get("restaurant_customization_json") if has_item_customization else "",
                    }
                )

            return {
                "order": {
                    "source": "web",
                    "doctype": "Sales Order",
                    "name": doc.name,
                    "order_code": doc.get("restaurant_order_code") or doc.name,
                    "customer_name": doc.customer_name,
                    "mobile": doc.get("restaurant_customer_mobile") or "",
                    "channel": doc.get("restaurant_order_type") or "takeaway",
                    "status": _core_order_status(doc),
                    "subtotal": flt(doc.total or doc.net_total),
                    "grand_total": flt(doc.grand_total or doc.total or doc.net_total),
                    "created_at": _json_safe_datetime(
                        _management_business_datetime(doc.get("transaction_date"), doc.creation) or doc.creation
                    ),
                    "cashier": doc.owner,
                    "note": doc.get("restaurant_note") or "",
                    "payment_method": doc.get("restaurant_payment_method") or "",
                    "payment_status": doc.get("restaurant_payment_status") or "",
                    "payment_provider": doc.get("restaurant_payment_provider") or "",
                    "payment_reference": doc.get("restaurant_payment_reference") or "",
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
            if (
                cint(row.get("restaurant_is_subcategory") or 0) == 1
                if has_subcategory_flag
                else False
            )
            or (
                (row.parent_item_group or "") in category_name_set
                and cint(row.get("is_group") or 0) != 1
            )
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
            is_default = 1 if default_value and (child.get("attribute_value") or "").strip() == default_value else 0
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
                "is_active": cint(row.get("restaurant_enabled") or 0) if has_restaurant_enabled else (0 if cint(row.get("disabled") or 0) else 1),
                "is_disabled": cint(row.get("disabled") or 0),
                "show_in_website": cint(row.get("show_in_website") or 0) if has_show_in_website else 1,
                "base_price": flt(row.get("restaurant_base_price") or row.get("standard_rate") or 0)
                if has_restaurant_base_price
                else flt(row.get("standard_rate") or 0),
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
    if cint(template_doc.get("has_variants") or 0) and (template_doc.get("variant_based_on") or "") != "Item Attribute":
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

    existing_rows = {str(row.get("attribute") or "").strip(): row for row in (template_doc.get("attributes") or [])}

    replacement_rows = []
    for attr_name in normalized:
        existing = existing_rows.get(attr_name)
        numeric_values = cint(frappe.db.get_value("Item Attribute", attr_name, "numeric_values") or 0)
        disabled = cint(frappe.db.get_value("Item Attribute", attr_name, "disabled") or 0)
        replacement_rows.append(
            {
                "attribute": attr_name,
                "attribute_value": "" if numeric_values else (existing.get("attribute_value") if existing else ""),
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
            (child.get("attribute_value") or "").strip(): child for child in (attribute_doc.get("item_attribute_values") or [])
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

    template_doc = _management_resolve_template_doc(parsed_payload.get("item_name") or parsed_payload.get("template_name"))
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

    template_doc = _management_resolve_template_doc(parsed_payload.get("item_name") or parsed_payload.get("template_name"))
    selected_attributes = parsed_payload.get("selected_attributes") or _management_template_attribute_names(template_doc)
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
            if not frappe.db.exists("Item Attribute Value", {"parent": attribute_name, "attribute_value": value_name}):
                missing_values.append(value_name)
            normalized_values.append(value_name)
            seen_values.add(value_name)

        if missing_values:
            attribute_doc = frappe.get_doc("Item Attribute", attribute_name)
            value_map = {
                (child.get("attribute_value") or "").strip(): child for child in (attribute_doc.get("item_attribute_values") or [])
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
            normalized_values = [(row.get("attribute_value") or "").strip() for row in rows if (row.get("attribute_value") or "").strip()]

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
    template_slug = (template_doc.get("restaurant_slug") or template_doc.item_name or template_doc.item_code or "").strip()
    for combination in combinations:
        args = {attribute_name: combination[index] for index, attribute_name in enumerate(normalized_attributes)}
        existing_name = get_variant(template_doc.name, args=args)
        if existing_name:
            existed.append(existing_name)
            continue

        variant_doc = create_variant(template_doc.name, args, use_template_image=True)
        variant_doc.flags.ignore_mandatory = True
        variant_doc.save(ignore_permissions=True)

        if _has_column("Item", "restaurant_slug") and not (variant_doc.get("restaurant_slug") or "").strip():
            suffix_parts = [_management_slugify_value(args.get(attr_name)) for attr_name in normalized_attributes]
            suffix = "-".join([part for part in suffix_parts if part])
            target_slug = _management_unique_item_slug(
                f"{template_slug}-{suffix}" if suffix else template_slug,
                item_name=variant_doc.name,
            )
            if target_slug:
                frappe.db.set_value("Item", variant_doc.name, "restaurant_slug", target_slug, update_modified=False)

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
    return payload, default_name


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

    total_sales_window = sum(flt(order.get("grand_total")) for order in current_orders if _is_revenue_order(order))
    prev_sales_window = sum(flt(order.get("grand_total")) for order in previous_orders if _is_revenue_order(order))
    contribution_pct = round(_safe_div(current_metrics["total_sales"] * 100.0, total_sales_window or 1), 2)
    prev_contribution_pct = round(_safe_div(previous_metrics["total_sales"] * 100.0, prev_sales_window or 1), 2)

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
        bucket["customer_name"] = (row.get("customer_name") or "").strip() or (row.get("mobile") or "").strip() or "-"
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
        category_slug = frappe.db.get_value("Item Group", item_doc.get("restaurant_category"), "restaurant_slug") or ""
    if item_doc.get("restaurant_subcategory"):
        subcategory_slug = frappe.db.get_value("Item Group", item_doc.get("restaurant_subcategory"), "restaurant_slug") or ""

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

    return {
        "item": {
            "name": item_doc.name,
            "item_code": item_doc.item_code,
            "item_name": item_doc.item_name,
            "variant_of": variant_of_name,
            "variant_of_item_name": variant_of_item_name,
            "has_variants": cint(item_doc.get("has_variants") or 0),
            "variant_based_on": item_doc.get("variant_based_on") or "",
            "custom_snapp_code": item_doc.get("custom_snapp_code") if _has_column("Item", "custom_snapp_code") else "",
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
            "restaurant_auto_add_qty": flt(item_doc.get("restaurant_auto_add_qty") or 0),
            "restaurant_nutrition_kcal": flt(item_doc.get("restaurant_nutrition_kcal") or 0),
            "restaurant_nutrition_protein_g": flt(item_doc.get("restaurant_nutrition_protein_g") or 0),
            "restaurant_nutrition_carb_g": flt(item_doc.get("restaurant_nutrition_carb_g") or 0),
            "restaurant_nutrition_sugar_g": flt(item_doc.get("restaurant_nutrition_sugar_g") or 0),
            "restaurant_nutrition_fat_g": flt(item_doc.get("restaurant_nutrition_fat_g") or 0),
            "nutrition": _nutrition_payload(item_doc),
        },
        "media": media,
        "field_options": _management_product_field_options(),
        "pricing": {
            "default_price_list": default_price_list or "",
            "price_lists": price_lists,
            "current_price": {
                "name": current_row.get("name") if current_row else "",
                "price_list": default_price_list or "",
                "price_list_rate": flt(current_row.get("price_list_rate")) if current_row else 0,
                "currency": (current_row.get("currency") if current_row else "") or _get_currency(),
                "uom": (current_row.get("uom") if current_row else "") or item_doc.stock_uom,
                "valid_from": str(current_row.get("valid_from")) if current_row and current_row.get("valid_from") else "",
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
    }
    float_fields = {"restaurant_auto_add_qty"}
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

    default_price_list = (parsed_payload.get("default_price_list") or "").strip()
    if default_price_list:
        set_management_default_price_list(default_price_list)

    if changed:
        item_doc.save(ignore_permissions=True)
        frappe.db.commit()

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
    price_list_name = (parsed_payload.get("price_list") or parsed_payload.get("price_list_name") or "").strip()
    valid_from = parsed_payload.get("valid_from")

    if not price_list_name:
        price_list_name = _get_default_selling_price_list_name(set_fallback_default=True) or ""
    if not price_list_name:
        frappe.throw(_("Please configure at least one selling price list."))
    if not frappe.db.exists("Price List", price_list_name):
        frappe.throw(_("Price List not found."), frappe.DoesNotExistError)
    if not cint(frappe.db.get_value("Price List", price_list_name, "selling")):
        frappe.throw(_("Price List must be a selling list."))

    currency = (parsed_payload.get("currency") or frappe.db.get_value("Price List", price_list_name, "currency") or "").strip()
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

    for fieldname in ("item", "company", "currency", "rm_cost_as_per"):
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
    frappe.db.commit()
    return frappe.get_doc("BOM", bom_doc.name).as_dict()


@frappe.whitelist()
def list_management_products(search=None, category=None, active_only=0, branch=None):
    _ensure_management_access()
    branch = (branch or "").strip()
    search = (search or "").strip()
    category = (category or "").strip()
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
        f"{image_field} as image",
    ]
    if _has_column("Item", "custom_snapp_code"):
        item_fields.append("custom_snapp_code")

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
                "stock_qty": flt(stock_by_item.get(row.name) or 0),
            }
        )
    return {
        "products": payload,
        "stock": {
            "low_threshold": max(cint(_get_single_setting("Restaurant Web Settings", "restaurant_low_stock_threshold", 5)), 1),
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
                _("This item is linked to other documents and cannot be deleted. You can disable it instead."),
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
    orders = _management_fetch_web_orders(date_from=date_from, date_to=date_to)

    grouped = {}
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
    return [row for row in (orders or []) if _management_customer_match(row, mobile=mobile, customer_name=customer_name)]


def _management_customer_report_payload(orders, previous_orders, date_from="", date_to=""):
    total_spent = sum(flt(row.get("grand_total")) for row in orders)
    previous_total_spent = sum(flt(row.get("grand_total")) for row in previous_orders)
    orders_count = len(orders)
    previous_orders_count = len(previous_orders)
    avg_ticket = _safe_div(total_spent, orders_count)
    previous_avg_ticket = _safe_div(previous_total_spent, previous_orders_count)

    paid_orders_count = sum(1 for row in orders if str(row.get("payment_status") or "").strip().lower() == "paid")
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
        [{"payment_status": key or "unknown", "orders": cint(value or 0)} for key, value in payment_grouped.items()],
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
                "text": _("Paid orders: {0} | Unpaid orders: {1}").format(cint(paid_orders_count), cint(unpaid_orders_count)),
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

    resolved_customer_name = normalized_customer_name or (sorted_orders[0].get("customer_name") if sorted_orders else "") or "مشتری"
    resolved_mobile = normalized_mobile or (sorted_orders[0].get("mobile") if sorted_orders else "") or ""

    first_order_at = ""
    last_order_at = ""
    if sorted_orders:
        last_order_at = sorted_orders[0].get("created_at") or ""
        first_order_at = sorted_orders[-1].get("created_at") or ""

    total_spent = sum(flt(row.get("grand_total") or 0) for row in sorted_orders)
    orders_count = len(sorted_orders)
    avg_ticket = round(_safe_div(total_spent, orders_count), 2)
    paid_orders_count = sum(1 for row in sorted_orders if str(row.get("payment_status") or "").strip().lower() == "paid")
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
    }
    fn = dispatch.get(normalized_key)
    if not fn:
        frappe.throw(_("Invalid report key: {0}").format(normalized_key))
    payload = fn(date_from=date_from, date_to=date_to)
    if isinstance(payload, dict):
        payload.setdefault("meta", {})
        payload["meta"]["compare_mode"] = (compare_mode or "previous_window").strip().lower() or "previous_window"
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
        "categories": [{"name": name, "items": items} for name, items in sorted(categories.items(), key=lambda d: d[0])],
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
        fields=["sum(grand_total) as total"],
        filters={
            "session": session_name,
            "status": ["in", list(TABLE_ORDER_BILLING_STATUSES)],
        },
        limit_page_length=1,
        ignore_permissions=True,
    )
    total = flt((rows[0].get("total") if rows else 0) or 0)
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

        menu_item_ref = _resolve_menu_item_ref(raw.get("menu_item") or raw.get("menu_item_id") or raw.get("name"))
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
        if (
            (table.status or "").strip().lower() != desired_status_for_doc
            or (table.active_session or "") != desired_active_session
        ):
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
def assign_table_session_customer(table_name, customer_name=None, mobile=None, customer_type=None, guest_count=None):
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
    for row in (order_doc.items or []):
        if row_name and row.name == row_name:
            return row

    if menu_item:
        normalized_menu_item = _resolve_menu_item_ref(menu_item) or menu_item
        for row in (order_doc.items or []):
            if row.menu_item == normalized_menu_item:
                return row
    return None


@frappe.whitelist()
def update_table_order_item(order_name, row_name=None, menu_item=None, quantity=None, quantity_delta=None, note=None):
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
                frappe.get_app_path(app_name, app_name, app_name, "print_format", format_slug, f"{format_slug}.html"),
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

    material_rows = "".join(
        f"<tr><td>{index}</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"
        for index in range(1, 13)
    )
    step_rows = "".join(
        f"<tr><td>{index}</td><td></td><td></td><td></td><td></td><td></td></tr>"
        for index in range(1, 9)
    )
    package_rows = "".join(
        f"<tr><td>{index}</td><td></td><td></td><td></td><td></td></tr>"
        for index in range(1, 5)
    )
    logo_html = f'<img class="logo" src="{brand_logo}" alt="لوگو" />' if brand_logo else '<div class="logo"></div>'

    return f"""
    <style>
      body {{ margin: 0; direction: rtl; color: #2f3c36; font-family: Peyda, Tahoma, sans-serif; }}
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

    return f"""
    <style>
      body {{ direction: rtl; font-family: Peyda, Tahoma, sans-serif; margin: 18px; color: #1f3b32; }}
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

        stats = grouped_counts.setdefault(doctype_name, {"count": 0, "blank_count": 0, "label": doctype_label})
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
