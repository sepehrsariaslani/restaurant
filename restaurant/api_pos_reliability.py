"""Reliability-focused management POS endpoints."""

import copy
import json
import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

CLIENT_ORDER_KEY_FIELD = "restaurant_pos_client_order_key"


def _legacy_api():
    from restaurant import api as legacy

    return legacy


def _parse_payload(payload):
    if isinstance(payload, dict):
        return dict(payload)
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except Exception:
            parsed = {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _normalize_client_order_key(value):
    raw = str(value or "").strip()
    if not raw:
        return ""
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "-", raw)
    return normalized.strip("-._:")[:140]


def _normalize_atomic_quick_edit_payload(payload):
    data = _parse_payload(payload)
    item_name = str(data.get("item_name") or data.get("name") or "").strip()
    out_of_stock = cint(data.get("restaurant_out_of_stock") or 0)
    return {
        "item_name": item_name,
        "price_list_rate": flt(data.get("price_list_rate") or 0),
        "restaurant_short_desc": str(data.get("restaurant_short_desc") or "").strip(),
        "restaurant_long_desc": str(data.get("restaurant_long_desc") or "").strip(),
        "item_group": str(data.get("item_group") or "").strip(),
        "restaurant_out_of_stock": 1 if out_of_stock else 0,
        "restaurant_out_of_stock_until": (
            str(data.get("restaurant_out_of_stock_until") or "").strip() if out_of_stock else ""
        ),
    }


def _extract_order_id(result):
    if not isinstance(result, dict):
        return ""
    return str(result.get("order_id") or result.get("name") or "").strip()


def _merge_pos_items(base_items, extra_items):
    merged = []
    index_by_name = {}
    for row in list(base_items or []):
        item = dict(row or {})
        name = str(item.get("name") or item.get("item_code") or item.get("slug") or "").strip()
        if name:
            index_by_name[name] = len(merged)
        merged.append(item)
    for row in list(extra_items or []):
        item = dict(row or {})
        name = str(item.get("name") or item.get("item_code") or item.get("slug") or "").strip()
        if name and name in index_by_name:
            merged[index_by_name[name]] = item
        else:
            if name:
                index_by_name[name] = len(merged)
            merged.append(item)
    return merged


def _should_clear_expired_out_of_stock(flag, until_value, today_value):
    if not cint(flag or 0) or not until_value or not today_value:
        return False
    try:
        return getdate(until_value) < getdate(today_value)
    except Exception:
        return False


def _clear_expired_out_of_stock():
    legacy = _legacy_api()
    if not legacy._has_column("Item", "restaurant_out_of_stock"):
        return 0
    if not legacy._has_column("Item", "restaurant_out_of_stock_until"):
        return 0

    today_value = getdate()
    rows = frappe.get_all(
        "Item",
        filters={
            "restaurant_out_of_stock": 1,
            "restaurant_out_of_stock_until": ["is", "set"],
        },
        fields=["name", "restaurant_out_of_stock", "restaurant_out_of_stock_until"],
        ignore_permissions=True,
        limit=1000,
    )
    cleared = 0
    for row in rows:
        if _should_clear_expired_out_of_stock(
            row.get("restaurant_out_of_stock"),
            row.get("restaurant_out_of_stock_until"),
            today_value,
        ):
            frappe.db.set_value(
                "Item",
                row.get("name"),
                {"restaurant_out_of_stock": 0, "restaurant_out_of_stock_until": None},
                update_modified=False,
            )
            cleared += 1
    return cleared


def _client_key_field_ready():
    legacy = _legacy_api()
    return bool(legacy._has_column("Sales Order", CLIENT_ORDER_KEY_FIELD))


def _find_order_by_client_key(client_order_key):
    key = _normalize_client_order_key(client_order_key)
    if not key or not _client_key_field_ready():
        return ""
    return str(
        frappe.db.get_value("Sales Order", {CLIENT_ORDER_KEY_FIELD: key}, "name") or ""
    ).strip()


def _management_unavailable_items(branch=""):
    legacy = _legacy_api()
    if not legacy._has_column("Item", "restaurant_out_of_stock"):
        return []

    image_field = legacy._core_item_image_field()
    fields = [
        "name",
        "item_name",
        "restaurant_slug",
        "restaurant_short_desc",
        "restaurant_base_price",
        "standard_rate",
        f"{image_field} as image",
        "restaurant_category",
        "restaurant_subcategory",
        "restaurant_out_of_stock",
    ]
    if legacy._has_column("Item", "restaurant_out_of_stock_until"):
        fields.append("restaurant_out_of_stock_until")
    if legacy._has_column("Item", "restaurant_packaging_price"):
        fields.append("restaurant_packaging_price")

    filters = copy.deepcopy(legacy._core_item_filters((branch or "").strip()))
    filters.pop("restaurant_out_of_stock", None)
    filters["restaurant_out_of_stock"] = 1

    order_by = "item_name asc"
    if legacy._has_column("Item", "restaurant_sort_order"):
        order_by = "restaurant_sort_order asc, item_name asc"

    rows = frappe.get_all(
        "Item",
        filters=filters,
        fields=fields,
        ignore_permissions=True,
        order_by=order_by,
        limit=1000,
    )
    category_meta_map = legacy._get_core_category_meta_map()
    subcategory_meta_map = legacy._get_core_subcategory_meta_map()
    payload = []
    for row in rows:
        serialized = legacy._serialize_core_item(
            row,
            category_meta_map=category_meta_map,
            subcategory_meta_map=subcategory_meta_map,
        )
        serialized["out_of_stock"] = cint(row.get("restaurant_out_of_stock") or 0)
        if "restaurant_out_of_stock_until" in fields:
            serialized["out_of_stock_until"] = legacy._date_value_to_iso(
                row.get("restaurant_out_of_stock_until")
            )
        if "restaurant_packaging_price" in fields:
            serialized["packaging_price"] = flt(row.get("restaurant_packaging_price") or 0)
        payload.append(serialized)
    return payload


@frappe.whitelist()
def get_management_pos_boot_reliable(branch=None):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    normalized_branch = (branch or "").strip()
    _clear_expired_out_of_stock()
    payload = legacy.get_management_pos_boot(normalized_branch)
    if not isinstance(payload, dict):
        payload = {}
    result = dict(payload)
    result["items"] = _merge_pos_items(
        payload.get("items") or [],
        _management_unavailable_items(normalized_branch),
    )
    return result


@frappe.whitelist()
def replay_offline_pos_order(payload=None):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    data = _parse_payload(payload)
    client_order_key = _normalize_client_order_key(data.get("client_order_key"))
    if not client_order_key:
        frappe.throw(_("Client order key is required for offline POS replay."))
    if not _client_key_field_ready():
        frappe.throw(_("POS reliability fields are not installed. Run bench migrate first."))

    existing = _find_order_by_client_key(client_order_key)
    if existing:
        return {
            "status": "existing",
            "order_id": existing,
            "client_order_key": client_order_key,
        }

    data["client_order_key"] = client_order_key
    try:
        result = legacy._create_pos_order_payload(data, commit=False)
        order_id = _extract_order_id(result)
        if not order_id:
            frappe.throw(_("POS order was created without an order id."))
        frappe.db.set_value(
            "Sales Order",
            order_id,
            CLIENT_ORDER_KEY_FIELD,
            client_order_key,
            update_modified=False,
        )
        frappe.db.commit()
        return {
            "status": "created",
            "order_id": order_id,
            "result": result,
            "client_order_key": client_order_key,
        }
    except Exception:
        frappe.db.rollback()
        existing = _find_order_by_client_key(client_order_key)
        if existing:
            return {
                "status": "existing",
                "order_id": existing,
                "client_order_key": client_order_key,
            }
        raise


def _set_item_field_if_available(legacy, item_doc, fieldname, value):
    if legacy._has_column("Item", fieldname):
        item_doc.set(fieldname, value)


def _resolve_price_context(legacy):
    price_list_name = legacy._get_default_selling_price_list_name(set_fallback_default=True) or ""
    if not price_list_name:
        frappe.throw(_("Please configure at least one selling price list."))
    if not frappe.db.exists("Price List", price_list_name):
        frappe.throw(_("Price List not found."))
    if not cint(frappe.db.get_value("Price List", price_list_name, "selling")):
        frappe.throw(_("Selected price list is not a selling price list."))
    currency = (
        frappe.db.get_value("Price List", price_list_name, "currency")
        or legacy._get_currency()
        or ""
    )
    return price_list_name, currency


def _upsert_item_price(legacy, item_code, stock_uom, price_list_name, currency, rate):
    filters = {"item_code": item_code, "price_list": price_list_name}
    existing_name = frappe.db.get_value("Item Price", filters, "name")
    if existing_name:
        price_doc = frappe.get_doc("Item Price", existing_name)
        price_doc.price_list_rate = rate
        if legacy._has_column("Item Price", "currency"):
            price_doc.currency = currency
        if legacy._has_column("Item Price", "uom") and not price_doc.get("uom"):
            price_doc.uom = stock_uom
        price_doc.save(ignore_permissions=True)
        return price_doc.name

    values = {
        "doctype": "Item Price",
        "item_code": item_code,
        "price_list": price_list_name,
        "price_list_rate": rate,
    }
    if legacy._has_column("Item Price", "currency"):
        values["currency"] = currency
    if legacy._has_column("Item Price", "uom"):
        values["uom"] = stock_uom
    return frappe.get_doc(values).insert(ignore_permissions=True).name


def _sync_item_price_state(legacy, item_doc, rate):
    price_list_name, currency = _resolve_price_context(legacy)
    _upsert_item_price(
        legacy,
        item_doc.item_code,
        item_doc.stock_uom,
        price_list_name,
        currency,
        rate,
    )
    frappe.db.set_value("Item", item_doc.name, "standard_rate", rate, update_modified=True)
    if legacy._has_column("Item", "restaurant_base_price"):
        frappe.db.set_value(
            "Item",
            item_doc.name,
            "restaurant_base_price",
            rate,
            update_modified=False,
        )

    sync_names = []
    if cint(item_doc.get("has_variants") or 0) and legacy._has_column("Item", "variant_of"):
        variants = frappe.get_all(
            "Item",
            filters={"variant_of": item_doc.name, "disabled": 0},
            fields=["name"],
            ignore_permissions=True,
            limit_page_length=500,
        )
        sync_names = [row.name for row in variants]
    elif (item_doc.get("variant_of") or "").strip():
        parent_name = frappe.db.get_value("Item", item_doc.variant_of, "name")
        if parent_name:
            sync_names = [parent_name]

    for sync_name in sync_names:
        if sync_name == item_doc.name:
            continue
        frappe.db.set_value("Item", sync_name, "standard_rate", rate, update_modified=True)
        if legacy._has_column("Item", "restaurant_base_price"):
            frappe.db.set_value(
                "Item",
                sync_name,
                "restaurant_base_price",
                rate,
                update_modified=False,
            )
        sync_is_parent = cint(frappe.db.get_value("Item", sync_name, "has_variants") or 0)
        if sync_is_parent:
            continue
        sync_uom = frappe.db.get_value("Item", sync_name, "stock_uom") or item_doc.stock_uom
        _upsert_item_price(
            legacy,
            sync_name,
            sync_uom,
            price_list_name,
            currency,
            rate,
        )


@frappe.whitelist()
def update_pos_product_atomic(payload=None):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    raw_data = _parse_payload(payload)
    data = _normalize_atomic_quick_edit_payload(raw_data)
    if not data.get("item_name"):
        frappe.throw(_("Invalid payload format."))
    if data["price_list_rate"] < 0:
        frappe.throw(_("Price cannot be negative."))

    if "restaurant_out_of_stock_until" in raw_data:
        try:
            legacy._ensure_out_of_stock_until_field()
        except Exception:
            pass

    item_name = legacy._management_resolve_item_name(data["item_name"])
    item_doc = frappe.get_doc("Item", item_name)
    item_group = data["item_group"] or str(item_doc.item_group or "").strip()
    if item_group and not frappe.db.exists("Item Group", item_group):
        frappe.throw(_("Item Group not found."))

    out_of_stock = data["restaurant_out_of_stock"]
    out_until_raw = data["restaurant_out_of_stock_until"]
    out_until = getdate(out_until_raw) if out_of_stock and out_until_raw else None

    try:
        if item_group:
            item_doc.item_group = item_group
        _set_item_field_if_available(
            legacy,
            item_doc,
            "restaurant_short_desc",
            data["restaurant_short_desc"],
        )
        _set_item_field_if_available(
            legacy,
            item_doc,
            "restaurant_long_desc",
            data["restaurant_long_desc"],
        )
        _set_item_field_if_available(
            legacy,
            item_doc,
            "restaurant_out_of_stock",
            out_of_stock,
        )
        _set_item_field_if_available(
            legacy,
            item_doc,
            "restaurant_out_of_stock_until",
            out_until,
        )
        item_doc.save(ignore_permissions=True)
        _sync_item_price_state(legacy, item_doc, data["price_list_rate"])
        detail = legacy.get_management_product_detail(item_doc.name)
        frappe.db.commit()
        try:
            frappe.clear_cache(doctype="Item")
            frappe.clear_website_cache()
        except Exception:
            pass
        return {
            "status": "success",
            "item": item_doc.name,
            "detail": detail,
        }
    except Exception:
        frappe.db.rollback()
        raise
