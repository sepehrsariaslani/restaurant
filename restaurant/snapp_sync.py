import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frappe
import requests
from frappe.utils import cint, cstr, flt, get_datetime, get_datetime_str, now_datetime, today


SNAPP_SOURCE = "snapp_food"
DEFAULT_API_BASE_URL = "https://api.prod.snapp-store.com"
DEFAULT_ORIGIN_URL = ""
DEFAULT_HOST_DOMAIN = ""
DEFAULT_PAGE_SIZE = 50
DEFAULT_LOOKBACK_MINUTES = 180
DEFAULT_AMOUNT_MULTIPLIER = 10
MAX_PAGE_SIZE = 100
MAX_PAGES = 300
IMPORT_ITEM_GROUP = "Snapp Imported Items"
FALLBACK_GUEST_NAME = "Snapp Guest"

SNAPP_ORDER_TYPE_MAP = {
    "SALON": "dine_in",
    "DINE_IN": "dine_in",
    "PICKUP": "takeaway",
    "TAKEAWAY": "takeaway",
    "DELIVERY": "delivery",
}

SNAPP_STATE_MAP = {
    0: "new",
    1: "new",
    2: "confirmed",
    3: "preparing",
    4: "ready",
    5: "delivered",
    6: "cancelled",
}


def _has_column(doctype, fieldname):
    try:
        return frappe.db.has_column(doctype, fieldname)
    except Exception:
        return False


def _has_field(doctype, fieldname):
    try:
        return bool(frappe.get_meta(doctype).has_field(fieldname))
    except Exception:
        return False


def _set_single_if_exists(doctype, fieldname, value):
    if not _has_field(doctype, fieldname):
        return
    frappe.db.set_single_value(doctype, fieldname, value)


def _scale_amount(value, multiplier):
    return flt(value or 0) * flt(multiplier or 1)


def _set_if_column(payload, doctype, fieldname, value):
    if _has_column(doctype, fieldname):
        payload[fieldname] = value


def _normalize_mobile(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _slugify(value):
    text = re.sub(r"\s+", "-", str(value or "").strip().lower())
    return re.sub(r"[^a-z0-9\-]+", "", text).strip("-")


def _to_snapp_dt(value):
    dt_value = get_datetime(value) if value else now_datetime()
    if dt_value.tzinfo is None:
        dt_value = dt_value.replace(tzinfo=timezone.utc)
    else:
        dt_value = dt_value.astimezone(timezone.utc)
    return dt_value.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _extract_orders(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []

    possible_containers = [payload]
    for key in ("data", "result"):
        value = payload.get(key)
        if isinstance(value, dict):
            possible_containers.append(value)
        elif isinstance(value, list):
            return value

    for container in possible_containers:
        for key in ("items", "orders", "data", "result"):
            value = container.get(key)
            if isinstance(value, list):
                return value
    return []


def _extract_total_pages(payload):
    if not isinstance(payload, dict):
        return None

    possible_containers = [payload]
    for key in ("data", "result"):
        value = payload.get(key)
        if isinstance(value, dict):
            possible_containers.append(value)

    for container in possible_containers:
        for key in ("totalPages", "TotalPages", "pageCount", "PageCount"):
            value = container.get(key)
            if isinstance(value, int) and value > 0:
                return value
    return None


def _get_settings():
    if not frappe.db.exists("DocType", "Restaurant Web Settings"):
        return {
            "enabled": False,
            "reason": "Restaurant Web Settings doctype is missing.",
        }

    try:
        settings_doc = frappe.get_cached_doc("Restaurant Web Settings")
    except Exception:
        settings_doc = frappe.get_doc("Restaurant Web Settings")
    token = ""
    if _has_field("Restaurant Web Settings", "snapp_bearer_token"):
        token = (settings_doc.get_password("snapp_bearer_token", raise_exception=False) or "").strip()

    enabled = cint(settings_doc.get("snapp_sync_enabled")) if _has_field("Restaurant Web Settings", "snapp_sync_enabled") else 0
    return {
        "enabled": bool(enabled),
        "api_base_url": (settings_doc.get("snapp_api_base_url") or DEFAULT_API_BASE_URL).strip().rstrip("/"),
        "origin_url": (settings_doc.get("snapp_origin_url") or DEFAULT_ORIGIN_URL).strip(),
        "host_domain": (settings_doc.get("snapp_hostdomain") or DEFAULT_HOST_DOMAIN).strip(),
        "token": token,
        "page_size": max(1, min(cint(settings_doc.get("snapp_page_size") or DEFAULT_PAGE_SIZE), MAX_PAGE_SIZE)),
        "lookback_minutes": max(5, cint(settings_doc.get("snapp_lookback_minutes") or DEFAULT_LOOKBACK_MINUTES)),
        "amount_multiplier": flt(settings_doc.get("snapp_amount_multiplier") or DEFAULT_AMOUNT_MULTIPLIER),
        "write_debug_json": bool(cint(settings_doc.get("snapp_write_debug_json") or 0)),
    }


def get_sync_status():
    settings = _get_settings()
    if settings.get("reason"):
        return settings

    return {
        "enabled": settings["enabled"],
        "has_token": bool(settings["token"]),
        "api_base_url": settings["api_base_url"],
        "host_domain": settings["host_domain"],
        "page_size": settings["page_size"],
        "lookback_minutes": settings["lookback_minutes"],
        "amount_multiplier": settings["amount_multiplier"],
        "last_success_at": frappe.db.get_single_value("Restaurant Web Settings", "snapp_last_success_at")
        if _has_field("Restaurant Web Settings", "snapp_last_success_at")
        else None,
        "last_error_at": frappe.db.get_single_value("Restaurant Web Settings", "snapp_last_error_at")
        if _has_field("Restaurant Web Settings", "snapp_last_error_at")
        else None,
        "last_error_message": frappe.db.get_single_value("Restaurant Web Settings", "snapp_last_error_message")
        if _has_field("Restaurant Web Settings", "snapp_last_error_message")
        else None,
    }


def fetch_snapp_orders(from_datetime=None, to_datetime=None, page_size=None, max_pages=MAX_PAGES, settings=None):
    cfg = settings or _get_settings()
    if not cfg.get("token"):
        raise frappe.ValidationError("Snapp bearer token is not configured.")

    end_dt = get_datetime(to_datetime) if to_datetime else now_datetime()
    start_dt = get_datetime(from_datetime) if from_datetime else end_dt - timedelta(minutes=cfg["lookback_minutes"])
    page_size = max(1, min(cint(page_size or cfg["page_size"]), MAX_PAGE_SIZE))

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {cfg['token']}",
        "user-agent": "Mozilla/5.0",
    }
    if cfg.get("host_domain"):
        headers["hostdomain"] = cfg["host_domain"]
    if cfg.get("origin_url"):
        headers["origin"] = cfg["origin_url"]
        headers["referer"] = f"{cfg['origin_url'].rstrip('/')}/"

    all_orders = []
    page_number = 1
    pages_fetched = 0
    total_pages = None

    while page_number <= max_pages:
        params = {
            "FromDate": _to_snapp_dt(start_dt),
            "ToDate": _to_snapp_dt(end_dt),
            "Search": "",
            "FullName": "",
            "DeliveryType": "",
            "OrderType": "",
            "PaymentMethod": "",
            "OrderState": "",
            "PageSize": page_size,
            "PageNumber": page_number,
        }
        response = requests.get(
            f"{cfg['api_base_url']}/api/orders",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        pages_fetched += 1

        payload = response.json()
        page_orders = _extract_orders(payload)
        if not page_orders:
            break

        all_orders.extend(page_orders)

        if total_pages is None:
            total_pages = _extract_total_pages(payload)
        if total_pages and page_number >= total_pages:
            break
        if not total_pages and len(page_orders) < page_size:
            break
        page_number += 1

    return {
        "from_date": _to_snapp_dt(start_dt),
        "to_date": _to_snapp_dt(end_dt),
        "page_size": page_size,
        "pages_fetched": pages_fetched,
        "orders_count": len(all_orders),
        "orders": all_orders,
    }


def _map_order_type(order_type, delivery_type):
    candidates = [str(order_type or "").strip().upper(), str(delivery_type or "").strip().upper()]
    for candidate in candidates:
        if candidate in SNAPP_ORDER_TYPE_MAP:
            return SNAPP_ORDER_TYPE_MAP[candidate]
    return "takeaway"


def _map_status(history_state, last_state):
    text = str(history_state or "").strip().lower()
    if "cancel" in text or "reject" in text:
        return "cancelled"
    if "deliver" in text:
        return "delivered"
    if "ready" in text:
        return "ready"
    if "prepar" in text or "cook" in text:
        return "preparing"
    if "confirm" in text or "accept" in text:
        return "confirmed"
    if "new" in text or "pending" in text:
        return "new"
    if cint(last_state) in SNAPP_STATE_MAP:
        return SNAPP_STATE_MAP[cint(last_state)]
    return "confirmed"


def normalize_snapp_order(raw_order, amount_multiplier=1):
    order_id = str(raw_order.get("id") or "").strip()
    if not order_id:
        raise frappe.ValidationError("Missing Snapp order id.")

    full_name = (raw_order.get("fullName") or "").strip()
    if not full_name:
        full_name = " ".join(
            part for part in [(raw_order.get("firstName") or "").strip(), (raw_order.get("lastName") or "").strip()] if part
        ).strip()
    if not full_name:
        full_name = FALLBACK_GUEST_NAME

    items = []
    for row in raw_order.get("orderItems") or []:
        qty = max(flt(row.get("count") or row.get("newCount") or 1), 1)
        items.append(
            {
                "line_id": str(row.get("id") or "").strip(),
                "menu_item_id": str(row.get("menuItemId") or "").strip(),
                "title": (row.get("title") or row.get("menuItemTitle") or "").strip() or "Snapp Item",
                "qty": qty,
                "unit_price": _scale_amount(row.get("price"), amount_multiplier),
                "discount": _scale_amount(row.get("discount"), amount_multiplier),
                "packaging_cost": _scale_amount(row.get("packagingCost"), amount_multiplier),
                "with_tax": cint(row.get("withTax") or 0),
                "toppings": row.get("toppings") or [],
            }
        )

    return {
        "order_id": order_id,
        "bill_number": str(raw_order.get("billNumber") or "").strip(),
        "offline_bill_number": str(raw_order.get("offlineBillNumber") or "").strip(),
        "external_state": str(raw_order.get("orderHistoryState") or "").strip(),
        "last_state": cint(raw_order.get("lastState") or 0),
        "status": _map_status(raw_order.get("orderHistoryState"), raw_order.get("lastState")),
        "order_type": _map_order_type(raw_order.get("orderType"), raw_order.get("deliveryType")),
        "delivery_type": str(raw_order.get("deliveryType") or "").strip(),
        "payment_method": str(raw_order.get("paymentMethod") or "").strip(),
        "factor_number": cstr(raw_order.get("factorNumber") or "").strip(),
        "customer_name": full_name,
        "mobile": _normalize_mobile(raw_order.get("phoneNumber")),
        "external_customer_id": str(raw_order.get("customerId") or "").strip(),
        "created_at": get_datetime(raw_order.get("createdAt")) if raw_order.get("createdAt") else now_datetime(),
        "preparation_time": get_datetime(raw_order.get("preparationTime")) if raw_order.get("preparationTime") else None,
        "print_time": get_datetime(raw_order.get("printTime")) if raw_order.get("printTime") else None,
        "address": (raw_order.get("addressDescription") or "").strip(),
        "note": (raw_order.get("note") or raw_order.get("description") or "").strip(),
        "discount_code": cstr(raw_order.get("discountCode") or "").strip(),
        "discount_type": cstr(raw_order.get("discountType") or "").strip(),
        "vendor_name": cstr(raw_order.get("vendorName") or "").strip(),
        "vendor_subdomain": cstr(raw_order.get("vendorSubdomain") or "").strip(),
        "items": items,
        "final_amount": _scale_amount(raw_order.get("finalAmount") or raw_order.get("finalPrice"), amount_multiplier),
        "final_price": _scale_amount(raw_order.get("finalPrice"), amount_multiplier),
        "discount": _scale_amount(raw_order.get("discount"), amount_multiplier),
        "discount_amount": flt(raw_order.get("discountAmount") or 0),
        "packaging_cost": _scale_amount(raw_order.get("packagingCost"), amount_multiplier),
        "delivery_cost": _scale_amount(raw_order.get("deliveryCost"), amount_multiplier),
        "tax": _scale_amount(raw_order.get("tax"), amount_multiplier),
        "service_cost": _scale_amount(raw_order.get("serviceCost"), amount_multiplier),
        "service_fee": _scale_amount(raw_order.get("serviceFee"), amount_multiplier),
        "tip": _scale_amount(raw_order.get("tip"), amount_multiplier),
        "refund_amount": _scale_amount(raw_order.get("refundAmount"), amount_multiplier),
        "raw": raw_order,
    }


def _default_company():
    return frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")


def _default_selling_price_list(currency=None):
    selling = frappe.db.get_single_value("Selling Settings", "selling_price_list")
    if selling:
        return selling

    filters = {"selling": 1}
    if _has_column("Price List", "enabled"):
        filters["enabled"] = 1
    if currency and _has_column("Price List", "currency"):
        specific = frappe.db.get_value("Price List", {**filters, "currency": currency}, "name")
        if specific:
            return specific
    return frappe.db.get_value("Price List", filters, "name")


def _default_uom():
    if _has_column("UOM", "enabled"):
        return frappe.db.get_value("UOM", {"enabled": 1}, "name") or frappe.db.get_value("UOM", {}, "name") or "Nos"
    return frappe.db.get_value("UOM", {}, "name") or "Nos"


def _ensure_customer(customer_name, mobile, external_customer_id):
    if mobile:
        existing = frappe.db.get_value("Customer", {"mobile_no": mobile, "disabled": 0}, "name")
        if existing:
            return existing

    if not mobile:
        customer_key = external_customer_id or _slugify(customer_name) or "guest"
        candidate_name = f"{FALLBACK_GUEST_NAME} {customer_key[:12]}".strip()
        existing = frappe.db.get_value("Customer", {"customer_name": candidate_name, "disabled": 0}, "name")
        if existing:
            return existing
        customer_name = candidate_name

    customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or frappe.db.get_value(
        "Customer Group", {}, "name"
    )
    territory = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value(
        "Territory", {"is_group": 0}, "name"
    )
    if not territory:
        territory = frappe.db.get_value("Territory", {}, "name")
    if not customer_group or not territory:
        raise frappe.ValidationError("Please configure Customer Group and Territory first.")

    customer_doc = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "customer_group": customer_group,
            "territory": territory,
            "mobile_no": mobile,
        }
    )
    customer_doc.insert(ignore_permissions=True)
    return customer_doc.name


def _ensure_import_item_group():
    group = frappe.db.get_value("Item Group", {"item_group_name": IMPORT_ITEM_GROUP}, "name")
    if group:
        return group

    parent = frappe.db.get_value("Item Group", {"parent_item_group": ""}, "name") or frappe.db.get_value("Item Group", {}, "name")
    if not parent:
        raise frappe.ValidationError("No Item Group found for imported Snapp items.")

    group_doc = frappe.get_doc(
        {
            "doctype": "Item Group",
            "item_group_name": IMPORT_ITEM_GROUP,
            "parent_item_group": parent,
            "is_group": 0,
        }
    )
    group_doc.insert(ignore_permissions=True)
    return group_doc.name


def _build_item_code(line):
    source = line.get("menu_item_id") or line.get("title") or frappe.generate_hash(length=8)
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10].upper()
    return f"SNP-{digest}"


def _build_item_code_from_title(title, fallback_code):
    preferred = re.sub(r"\s+", " ", str(title or "").strip())
    preferred = preferred.replace("/", "-").replace("\\", "-")
    preferred = preferred[:120].strip()
    return preferred or fallback_code


def _unique_item_code(preferred):
    candidate = (preferred or "").strip()[:120]
    if not candidate:
        candidate = f"SNP-ITEM-{frappe.generate_hash(length=6).upper()}"
    if not frappe.db.exists("Item", candidate):
        return candidate

    counter = 1
    while True:
        suffix = f"-{counter}"
        attempt = f"{candidate[: 120 - len(suffix)]}{suffix}"
        if not frappe.db.exists("Item", attempt):
            return attempt
        counter += 1


def _resolve_item_code(line):
    external_menu_item_id = (line.get("menu_item_id") or "").strip()
    title = (line.get("title") or "").strip() or "Snapp Item"
    snapp_code = _build_item_code(line)

    if _has_column("Item", "custom_snapp_code"):
        by_snapp_code = frappe.db.get_value("Item", {"custom_snapp_code": snapp_code}, "name")
        if by_snapp_code:
            if external_menu_item_id and _has_column("Item", "restaurant_external_menu_item_id"):
                frappe.db.set_value(
                    "Item",
                    by_snapp_code,
                    "restaurant_external_menu_item_id",
                    external_menu_item_id,
                    update_modified=False,
                )
            return by_snapp_code

    if external_menu_item_id and _has_column("Item", "restaurant_external_menu_item_id"):
        by_external = frappe.db.get_value("Item", {"restaurant_external_menu_item_id": external_menu_item_id}, "name")
        if by_external:
            if _has_column("Item", "custom_snapp_code"):
                current_snapp_code = frappe.db.get_value("Item", by_external, "custom_snapp_code")
                if not (current_snapp_code or "").strip():
                    frappe.db.set_value("Item", by_external, "custom_snapp_code", snapp_code, update_modified=False)
            return by_external

    by_title = frappe.db.get_value("Item", {"item_name": title}, "name")
    if by_title:
        if external_menu_item_id and _has_column("Item", "restaurant_external_menu_item_id"):
            frappe.db.set_value("Item", by_title, "restaurant_external_menu_item_id", external_menu_item_id, update_modified=False)
        if _has_column("Item", "custom_snapp_code"):
            current_snapp_code = frappe.db.get_value("Item", by_title, "custom_snapp_code")
            if not (current_snapp_code or "").strip():
                frappe.db.set_value("Item", by_title, "custom_snapp_code", snapp_code, update_modified=False)
        return by_title

    item_group = _ensure_import_item_group()
    item_code = _unique_item_code(_build_item_code_from_title(title, snapp_code))

    item_doc = frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_code,
            "item_name": title,
            "item_group": item_group,
            "stock_uom": _default_uom(),
            "is_stock_item": 0,
            "is_sales_item": 1,
            "is_purchase_item": 0,
            "standard_rate": flt(line.get("unit_price") or 0),
            "description": title,
        }
    )
    if _has_column("Item", "restaurant_enabled"):
        item_doc.set("restaurant_enabled", 0)
    if _has_column("Item", "restaurant_external_menu_item_id"):
        item_doc.set("restaurant_external_menu_item_id", external_menu_item_id)
    if _has_column("Item", "custom_snapp_code"):
        item_doc.set("custom_snapp_code", snapp_code)
    item_doc.insert(ignore_permissions=True)
    return item_doc.name


def _unique_restaurant_order_code(preferred):
    cleaned = re.sub(r"[^A-Za-z0-9\-]", "", str(preferred or "").strip()) or f"SNP-{frappe.generate_hash(length=8).upper()}"
    candidate = cleaned[:120]
    if not _has_column("Sales Order", "restaurant_order_code"):
        return candidate

    if not frappe.db.exists("Sales Order", {"restaurant_order_code": candidate}):
        return candidate

    counter = 1
    while True:
        suffix = f"-{counter}"
        attempt = f"{candidate[: 120 - len(suffix)]}{suffix}"
        if not frappe.db.exists("Sales Order", {"restaurant_order_code": attempt}):
            return attempt
        counter += 1


def _build_sales_order_items(order_payload):
    rows = []
    for line in order_payload["items"]:
        item_code = _resolve_item_code(line)
        qty = max(flt(line.get("qty") or 1), 1)
        rate = flt(line.get("unit_price") or 0)
        line_payload = {
            "item_code": item_code,
            "qty": qty,
            "rate": rate,
            "amount": rate * qty,
            "description": line.get("title") or item_code,
            "uom": _default_uom(),
            "stock_uom": _default_uom(),
        }
        if _has_column("Sales Order Item", "restaurant_external_line_id"):
            line_payload["restaurant_external_line_id"] = line.get("line_id") or ""
        if _has_column("Sales Order Item", "restaurant_external_menu_item_id"):
            line_payload["restaurant_external_menu_item_id"] = line.get("menu_item_id") or ""
        if _has_column("Sales Order Item", "restaurant_external_item_title"):
            line_payload["restaurant_external_item_title"] = line.get("title") or ""
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_discount", flt(line.get("discount") or 0))
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_packaging_cost", flt(line.get("packaging_cost") or 0))
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_with_tax", cint(line.get("with_tax") or 0))
        _set_if_column(
            line_payload,
            "Sales Order Item",
            "restaurant_external_toppings_json",
            json.dumps(line.get("toppings") or [], ensure_ascii=False),
        )
        rows.append(line_payload)
    return rows


def _apply_sales_order_external_fields(target_payload, order_payload):
    _set_if_column(target_payload, "Sales Order", "restaurant_external_source", SNAPP_SOURCE)
    _set_if_column(target_payload, "Sales Order", "restaurant_external_order_id", order_payload["order_id"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_bill_number", order_payload["bill_number"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_state", order_payload["external_state"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_delivery_type", order_payload["delivery_type"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_payment_method", order_payload["payment_method"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_factor_number", order_payload["factor_number"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_discount", flt(order_payload["discount"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_delivery_cost", flt(order_payload["delivery_cost"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_packaging_cost", flt(order_payload["packaging_cost"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_tax", flt(order_payload["tax"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_service_cost", flt(order_payload["service_cost"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_service_fee", flt(order_payload["service_fee"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_tip", flt(order_payload["tip"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_refund_amount", flt(order_payload["refund_amount"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_final_price", flt(order_payload["final_price"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_discount_amount", flt(order_payload["discount_amount"]))
    _set_if_column(target_payload, "Sales Order", "restaurant_external_discount_code", order_payload["discount_code"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_discount_type", order_payload["discount_type"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_vendor_name", order_payload["vendor_name"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_vendor_subdomain", order_payload["vendor_subdomain"])
    _set_if_column(target_payload, "Sales Order", "restaurant_external_payload_json", json.dumps(order_payload["raw"], ensure_ascii=False))


def _update_existing_sales_order_lines(sales_order_name, order_payload):
    item_rows = frappe.get_all(
        "Sales Order Item",
        filters={"parent": sales_order_name},
        fields=["name", "qty", "restaurant_external_line_id", "restaurant_external_menu_item_id", "item_name"],
        limit_page_length=500,
        ignore_permissions=True,
    )

    by_line_id = {}
    by_menu_title = {}
    for line in order_payload["items"]:
        if line.get("line_id"):
            by_line_id[line["line_id"]] = line
        key = f"{line.get('menu_item_id') or ''}|{(line.get('title') or '').strip()}"
        by_menu_title[key] = line

    subtotal = 0
    for row in item_rows:
        source_line = None
        if row.get("restaurant_external_line_id"):
            source_line = by_line_id.get(row.get("restaurant_external_line_id"))
        if not source_line:
            key = f"{row.get('restaurant_external_menu_item_id') or ''}|{(row.get('item_name') or '').strip()}"
            source_line = by_menu_title.get(key)
        if not source_line:
            subtotal += flt(row.get("qty") or 0) * flt(frappe.db.get_value("Sales Order Item", row.name, "rate") or 0)
            continue

        qty = max(flt(source_line.get("qty") or 1), 1)
        rate = flt(source_line.get("unit_price") or 0)
        amount = qty * rate
        subtotal += amount

        updates = {
            "qty": qty,
            "rate": rate,
            "amount": amount,
            "base_rate": rate,
            "base_amount": amount,
        }
        _set_if_column(updates, "Sales Order Item", "restaurant_external_discount", flt(source_line.get("discount") or 0))
        _set_if_column(
            updates,
            "Sales Order Item",
            "restaurant_external_packaging_cost",
            flt(source_line.get("packaging_cost") or 0),
        )
        _set_if_column(updates, "Sales Order Item", "restaurant_external_with_tax", cint(source_line.get("with_tax") or 0))
        _set_if_column(
            updates,
            "Sales Order Item",
            "restaurant_external_toppings_json",
            json.dumps(source_line.get("toppings") or [], ensure_ascii=False),
        )
        frappe.db.set_value("Sales Order Item", row.name, updates, update_modified=False)

    grand_total = flt(order_payload.get("final_amount") or subtotal or 0)
    totals = {
        "total": subtotal,
        "net_total": subtotal,
        "base_total": subtotal,
        "base_net_total": subtotal,
        "grand_total": grand_total,
        "rounded_total": grand_total,
        "base_grand_total": grand_total,
        "base_rounded_total": grand_total,
    }
    frappe.db.set_value("Sales Order", sales_order_name, totals, update_modified=False)


def _sync_existing_sales_order(sales_order_name, order_payload, reconcile_lines=False):
    so_doc = frappe.get_doc("Sales Order", sales_order_name)

    updates = {}
    if _has_column("Sales Order", "restaurant_external_state"):
        updates["restaurant_external_state"] = order_payload["external_state"]
    if _has_column("Sales Order", "restaurant_status"):
        updates["restaurant_status"] = order_payload["status"]
    _apply_sales_order_external_fields(updates, order_payload)
    if _has_column("Sales Order", "restaurant_customer_mobile"):
        updates["restaurant_customer_mobile"] = order_payload["mobile"]
    if _has_column("Sales Order", "restaurant_order_type"):
        updates["restaurant_order_type"] = order_payload["order_type"]
    if _has_column("Sales Order", "restaurant_delivery_address"):
        updates["restaurant_delivery_address"] = order_payload["address"]
    if _has_column("Sales Order", "restaurant_note"):
        updates["restaurant_note"] = order_payload["note"]

    for fieldname, value in updates.items():
        frappe.db.set_value("Sales Order", sales_order_name, fieldname, value, update_modified=False)

    if reconcile_lines and so_doc.docstatus == 1:
        _update_existing_sales_order_lines(sales_order_name, order_payload)

    if order_payload["status"] == "cancelled" and so_doc.docstatus == 1:
        so_doc.flags.ignore_permissions = True
        so_doc.cancel()
        return "cancelled"
    return "updated"


def _create_sales_order(order_payload):
    company = _default_company()
    if not company:
        raise frappe.ValidationError("Default company is not configured.")

    currency = frappe.db.get_value("Company", company, "default_currency")
    selling_price_list = _default_selling_price_list(currency)
    if not selling_price_list:
        raise frappe.ValidationError("Selling Price List is not configured.")

    customer = _ensure_customer(
        customer_name=order_payload["customer_name"],
        mobile=order_payload["mobile"],
        external_customer_id=order_payload["external_customer_id"],
    )
    items = _build_sales_order_items(order_payload)
    if not items:
        raise frappe.ValidationError(f"Order {order_payload['order_id']} has no valid items.")

    created_date = get_datetime(order_payload.get("created_at")) if order_payload.get("created_at") else now_datetime()
    order_code = _unique_restaurant_order_code(order_payload["bill_number"] or f"SNP-{order_payload['order_id'][:8]}")

    doc_payload = {
        "doctype": "Sales Order",
        "customer": customer,
        "company": company,
        "transaction_date": str(created_date.date()) if created_date else today(),
        "delivery_date": str(created_date.date()) if created_date else today(),
        "currency": currency,
        "selling_price_list": selling_price_list,
        "ignore_pricing_rule": 1,
        "items": items,
    }
    if _has_column("Sales Order", "restaurant_order_code"):
        doc_payload["restaurant_order_code"] = order_code
    if _has_column("Sales Order", "restaurant_customer_mobile"):
        doc_payload["restaurant_customer_mobile"] = order_payload["mobile"]
    if _has_column("Sales Order", "restaurant_order_type"):
        doc_payload["restaurant_order_type"] = order_payload["order_type"]
    if _has_column("Sales Order", "restaurant_delivery_address"):
        doc_payload["restaurant_delivery_address"] = order_payload["address"]
    if _has_column("Sales Order", "restaurant_note"):
        doc_payload["restaurant_note"] = order_payload["note"]
    if _has_column("Sales Order", "restaurant_status"):
        doc_payload["restaurant_status"] = order_payload["status"]
    _apply_sales_order_external_fields(doc_payload, order_payload)

    so_doc = frappe.get_doc(doc_payload)
    subtotal = sum(flt(row.get("amount") or 0) for row in items)

    # Some ERPNext forks include custom commission hooks that expect these attributes.
    if not getattr(so_doc, "total_structure", None):
        setattr(so_doc, "total_structure", subtotal)
    if getattr(so_doc, "amount_eligible_for_commission", None) is None:
        setattr(so_doc, "amount_eligible_for_commission", subtotal or flt(order_payload.get("final_amount") or 0))
    if getattr(so_doc, "commission_rate", None) is None:
        setattr(so_doc, "commission_rate", 0)
    if getattr(so_doc, "total_commission", None) is None:
        setattr(so_doc, "total_commission", 0)

    so_doc.insert(ignore_permissions=True)
    so_doc.submit()

    if order_payload["status"] == "cancelled" and so_doc.docstatus == 1:
        so_doc.flags.ignore_permissions = True
        so_doc.cancel()
        return so_doc.name, "cancelled"
    return so_doc.name, "created"


def _notify_new_order(sales_order_name, order_payload):
    if not frappe.db.exists("DocType", "Notification Log"):
        return
    if not frappe.db.exists("User", "Administrator"):
        return

    subject = f"New Snapp order imported: {order_payload['bill_number'] or order_payload['order_id']}"
    notification = frappe.get_doc(
        {
            "doctype": "Notification Log",
            "subject": subject,
            "for_user": "Administrator",
            "type": "Alert",
            "document_type": "Sales Order",
            "document_name": sales_order_name,
            "from_user": frappe.session.user if frappe.session.user != "Guest" else "Administrator",
        }
    )
    notification.insert(ignore_permissions=True)


def _write_debug_json(payload):
    output_path = Path(frappe.get_app_path("restaurant", "restaurant", "www", "snapp_orders.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=4)


def sync_snapp_orders(trigger="scheduler", from_datetime=None, to_datetime=None, only_new=1, update_status_fields=1):
    settings = _get_settings()
    if settings.get("reason"):
        return {"status": "skipped", "reason": settings["reason"]}
    if not settings["enabled"]:
        return {"status": "skipped", "reason": "Snapp sync is disabled in Restaurant Web Settings."}
    if not settings["token"]:
        return {"status": "error", "reason": "Snapp bearer token is missing."}

    started_at = now_datetime()
    only_new = cint(only_new)
    update_status_fields = cint(update_status_fields)
    result = {
        "status": "success",
        "trigger": trigger,
        "only_new": only_new,
        "fetched_count": 0,
        "created_count": 0,
        "updated_count": 0,
        "cancelled_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "pages_fetched": 0,
        "errors": [],
    }

    try:
        fetched_payload = fetch_snapp_orders(
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            page_size=settings["page_size"],
            max_pages=MAX_PAGES,
            settings=settings,
        )
        result["fetched_count"] = cint(fetched_payload.get("orders_count") or 0)
        result["pages_fetched"] = cint(fetched_payload.get("pages_fetched") or 0)
        rows = fetched_payload.get("orders") or []
        rows = sorted(rows, key=lambda row: str(row.get("createdAt") or ""))

        for raw_order in rows:
            try:
                normalized = normalize_snapp_order(raw_order, amount_multiplier=settings.get("amount_multiplier") or 1)
                existing = None
                if _has_column("Sales Order", "restaurant_external_order_id"):
                    existing = frappe.db.get_value(
                        "Sales Order",
                        {"restaurant_external_order_id": normalized["order_id"]},
                        "name",
                    )

                if existing:
                    if only_new:
                        result["skipped_count"] += 1
                    else:
                        action = _sync_existing_sales_order(existing, normalized, reconcile_lines=True)
                        if action == "cancelled":
                            result["cancelled_count"] += 1
                        else:
                            result["updated_count"] += 1
                    continue

                sales_order_name, action = _create_sales_order(normalized)
                _notify_new_order(sales_order_name, normalized)
                if action == "cancelled":
                    result["cancelled_count"] += 1
                else:
                    result["created_count"] += 1
            except Exception:
                result["failed_count"] += 1
                result["errors"].append(
                    {
                        "order_id": raw_order.get("id"),
                        "error": frappe.get_traceback(with_context=False),
                    }
                )

        if settings["write_debug_json"]:
            _write_debug_json(fetched_payload)

        if update_status_fields:
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_success_at", get_datetime_str(now_datetime()))
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", None)
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_message", "")
            if _has_field("Restaurant Web Settings", "snapp_last_seen_created_at") and rows:
                _set_single_if_exists("Restaurant Web Settings", "snapp_last_seen_created_at", rows[-1].get("createdAt"))

        result["duration_seconds"] = flt((now_datetime() - started_at).total_seconds())
        frappe.db.commit()
        return result
    except Exception:
        trace = frappe.get_traceback()
        if update_status_fields:
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", get_datetime_str(now_datetime()))
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_message", trace.splitlines()[-1][:500])
        frappe.log_error(trace, "Snapp Sync Error")
        frappe.db.commit()
        return {
            "status": "error",
            "trigger": trigger,
            "reason": trace.splitlines()[-1] if trace else "Unknown error",
        }


def sync_snapp_orders_backfill(start_date, end_date=None, chunk_days=7, only_new=1):
    if not start_date:
        return {"status": "error", "reason": "start_date is required."}

    start_dt = get_datetime(start_date)
    end_dt = get_datetime(end_date) if end_date else now_datetime()
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    chunk_days = max(cint(chunk_days or 7), 1)
    only_new = cint(only_new)

    cursor = start_dt
    summary = {
        "status": "success",
        "start_date": get_datetime_str(start_dt),
        "end_date": get_datetime_str(end_dt),
        "chunk_days": chunk_days,
        "only_new": only_new,
        "chunks_total": 0,
        "chunks_success": 0,
        "chunks_failed": 0,
        "created_count": 0,
        "updated_count": 0,
        "cancelled_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "fetched_count": 0,
        "errors": [],
    }

    while cursor < end_dt:
        chunk_end = min(cursor + timedelta(days=chunk_days), end_dt)
        summary["chunks_total"] += 1

        result = sync_snapp_orders(
            trigger="backfill",
            from_datetime=cursor,
            to_datetime=chunk_end,
            only_new=only_new,
            update_status_fields=0,
        )
        if result.get("status") != "success":
            summary["chunks_failed"] += 1
            summary["errors"].append(
                {
                    "from": get_datetime_str(cursor),
                    "to": get_datetime_str(chunk_end),
                    "reason": result.get("reason") or "Unknown error",
                }
            )
        else:
            summary["chunks_success"] += 1
            for key in (
                "created_count",
                "updated_count",
                "cancelled_count",
                "skipped_count",
                "failed_count",
                "fetched_count",
            ):
                summary[key] += cint(result.get(key) or 0)

        cursor = chunk_end

    _set_single_if_exists("Restaurant Web Settings", "snapp_last_success_at", get_datetime_str(now_datetime()))
    if summary["chunks_failed"]:
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", get_datetime_str(now_datetime()))
        _set_single_if_exists(
            "Restaurant Web Settings",
            "snapp_last_error_message",
            f"Backfill finished with {summary['chunks_failed']} failed chunk(s).",
        )
    else:
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", None)
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_message", "")

    frappe.db.commit()
    return summary


def repair_existing_snapp_orders(amount_multiplier=None, batch_size=200):
    settings = _get_settings()
    multiplier = flt(amount_multiplier if amount_multiplier is not None else settings.get("amount_multiplier") or 1)
    batch_size = max(cint(batch_size or 200), 1)

    rows = frappe.get_all(
        "Sales Order",
        filters={"restaurant_external_source": SNAPP_SOURCE},
        fields=["name", "restaurant_external_payload_json"],
        order_by="creation asc",
        limit_page_length=0,
        ignore_permissions=True,
    )

    result = {
        "status": "success",
        "multiplier": multiplier,
        "orders_total": len(rows),
        "orders_updated": 0,
        "orders_failed": 0,
        "errors": [],
    }

    for idx, row in enumerate(rows, 1):
        try:
            raw = json.loads(row.get("restaurant_external_payload_json") or "{}")
            if not isinstance(raw, dict):
                continue
            normalized = normalize_snapp_order(raw, amount_multiplier=multiplier)
            _sync_existing_sales_order(row["name"], normalized, reconcile_lines=True)
            result["orders_updated"] += 1
        except Exception:
            result["orders_failed"] += 1
            result["errors"].append(
                {
                    "sales_order": row.get("name"),
                    "error": frappe.get_traceback(with_context=False),
                }
            )

        if idx % batch_size == 0:
            frappe.db.commit()

    _set_single_if_exists("Restaurant Web Settings", "snapp_last_success_at", get_datetime_str(now_datetime()))
    if result["orders_failed"]:
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", get_datetime_str(now_datetime()))
        _set_single_if_exists(
            "Restaurant Web Settings",
            "snapp_last_error_message",
            f"Repair completed with {result['orders_failed']} failed order(s).",
        )
    frappe.db.commit()
    return result
