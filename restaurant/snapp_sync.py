import base64
import binascii
import hashlib
import json
import re
from difflib import SequenceMatcher
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
DEFAULT_REPORT_URL = "https://snappfood.ir/vms/v3/restaurant/report"
DEFAULT_MENU_API_BASE_URL = "https://apigw.snappfood.ir"
MAX_PAGE_SIZE = 100
MAX_PAGES = 300
IMPORT_ITEM_GROUP = "Snapp Imported Items"
FALLBACK_GUEST_NAME = "Snapp Guest"
_REQUIRED_SCHEMA_FIELDS = {
    "Restaurant Web Settings": (
        "snapp_bearer_token",
        "snapp_vendor_id",
        "snapp_report_url",
        "snapp_menu_api_base_url",
        "snapp_auto_sync_invoices",
        "snapp_require_item_mapping",
        "snapp_default_customer",
    ),
    "Sales Order": ("restaurant_external_source", "restaurant_external_order_id"),
    "Sales Invoice": ("restaurant_external_source", "restaurant_external_order_id"),
    "Sales Order Item": ("restaurant_external_product_id",),
    "Sales Invoice Item": ("restaurant_external_product_id",),
    "Customer": ("restaurant_external_customer_id",),
    "Item": ("restaurant_external_product_id", "restaurant_external_variation_id"),
}
_EXTERNAL_PRIVATE_KEY_PARTS = (
    "fullname",
    "firstname",
    "lastname",
    "customername",
    "phonenumber",
    "mobileno",
    "phone",
    "mobile",
    "address",
    "latitude",
    "longitude",
    "useragent",
)

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


def _get_schema_status():
    missing = [
        f"{doctype}.{fieldname}"
        for doctype, fieldnames in _REQUIRED_SCHEMA_FIELDS.items()
        for fieldname in fieldnames
        if not _has_field(doctype, fieldname)
    ]
    return {"ready": not missing, "missing": missing}


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
    mobile = "".join(ch for ch in str(value or "") if ch.isdigit())
    if mobile.startswith("98") and len(mobile) == 12:
        mobile = "0" + mobile[2:]
    if len(mobile) == 10 and mobile.startswith("9"):
        mobile = "0" + mobile
    if mobile == "09120000000":
        return ""
    return mobile


def _redact_external_payload(value):
    """Keep business metadata while avoiding a second raw PII snapshot."""
    if isinstance(value, dict):
        safe = {}
        for key, child in value.items():
            normalized_key = re.sub(r"[^a-z0-9]", "", str(key or "").lower())
            if any(part in normalized_key for part in _EXTERNAL_PRIVATE_KEY_PARTS):
                continue
            safe[key] = _redact_external_payload(child)
        return safe
    if isinstance(value, list):
        return [_redact_external_payload(child) for child in value]
    return value


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


def _normalize_bearer_token(value):
    """Accept either the raw token or the full ``Bearer <token>`` header value."""
    token = str(value or "").strip()
    if token.lower().startswith("bearer "):
        return token[7:].strip()
    return token


def _extract_vendor_id_from_token(value):
    """Read a vendor identifier claim from a JWT without logging or returning the token."""
    token = _normalize_bearer_token(value)
    parts = token.split(".")
    if len(parts) != 3 or not parts[1]:
        return ""
    try:
        encoded = parts[1] + ("=" * (-len(parts[1]) % 4))
        payload = json.loads(base64.urlsafe_b64decode(encoded.encode("ascii")).decode("utf-8"))
    except (binascii.Error, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return ""

    id_keys = {
        "vendorid",
        "vendorids",
        "vendor_id",
        "vendor_ids",
        "restaurantid",
        "restaurantids",
        "restaurant_id",
        "restaurant_ids",
        "merchantid",
        "merchantids",
        "merchant_id",
        "merchant_ids",
    }
    container_keys = {"vendor", "restaurant", "merchant"}

    def candidate(raw):
        if isinstance(raw, (list, tuple)):
            for value in raw:
                found = candidate(value)
                if found:
                    return found
            return ""
        if isinstance(raw, bool) or raw is None:
            return ""
        text = str(raw).strip()
        if not text or len(text) > 80 or not re.fullmatch(r"[A-Za-z0-9_-]+", text):
            return ""
        return text

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                normalized = re.sub(r"[^a-z0-9_]", "", str(key or "").lower())
                if normalized in {"username", "sub"}:
                    identity_match = re.search(
                        r"(?:^|[^a-z0-9])vmo([0-9]+)(?:$|[^a-z0-9])",
                        str(value or ""),
                        flags=re.IGNORECASE,
                    )
                    if identity_match:
                        return identity_match.group(1)
                if normalized in id_keys:
                    found = candidate(value)
                    if found:
                        return found
                if normalized in container_keys and isinstance(value, dict):
                    found = visit(value)
                    if found:
                        return found
                if isinstance(value, (dict, list)):
                    found = visit(value)
                    if found:
                        return found
        elif isinstance(node, list):
            for value in node:
                found = visit(value)
                if found:
                    return found
        return ""

    return visit(payload)


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
        token = _normalize_bearer_token(
            settings_doc.get_password("snapp_bearer_token", raise_exception=False) or ""
        )

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
        "vendor_id": (settings_doc.get("snapp_vendor_id") or "").strip()
        if _has_field("Restaurant Web Settings", "snapp_vendor_id")
        else "",
        "report_url": (settings_doc.get("snapp_report_url") or DEFAULT_REPORT_URL).strip(),
        "menu_api_base_url": (settings_doc.get("snapp_menu_api_base_url") or DEFAULT_MENU_API_BASE_URL).strip().rstrip("/"),
        "auto_sync_invoices": bool(cint(settings_doc.get("snapp_auto_sync_invoices") or 0))
        if _has_field("Restaurant Web Settings", "snapp_auto_sync_invoices")
        else False,
        "require_item_mapping": bool(cint(settings_doc.get("snapp_require_item_mapping") or 0))
        if _has_field("Restaurant Web Settings", "snapp_require_item_mapping")
        else False,
        "default_customer": (settings_doc.get("snapp_default_customer") or "")
        if _has_field("Restaurant Web Settings", "snapp_default_customer")
        else "",
    }


def get_sync_status():
    settings = _get_settings()
    if settings.get("reason"):
        return {**settings, "schema_ready": False, "schema_missing": []}

    schema_status = _get_schema_status()

    return {
        "enabled": settings["enabled"],
        "has_token": bool(settings["token"]),
        "api_base_url": settings["api_base_url"],
        "report_url": settings.get("report_url") or DEFAULT_REPORT_URL,
        "menu_api_base_url": settings.get("menu_api_base_url") or DEFAULT_MENU_API_BASE_URL,
        "host_domain": settings.get("host_domain") or "",
        "origin_url": settings.get("origin_url") or "",
        "page_size": settings.get("page_size") or DEFAULT_PAGE_SIZE,
        "lookback_minutes": settings["lookback_minutes"],
        "amount_multiplier": settings.get("amount_multiplier") or DEFAULT_AMOUNT_MULTIPLIER,
        "vendor_id": settings.get("vendor_id") or "",
        "auto_sync_invoices": settings.get("auto_sync_invoices", False),
        "require_item_mapping": settings.get("require_item_mapping", False),
        "default_customer": settings.get("default_customer") or "",
        "schema_ready": schema_status["ready"],
        "schema_missing": schema_status["missing"],
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

    if not cfg.get("vendor_id"):
        raise frappe.ValidationError("شناسه فروشنده Food Partner تنظیم نشده است؛ مسیر قدیمی سفارش غیرفعال است.")

    all_orders = []
    page_number = 0
    pages_fetched = 0
    total_pages = None

    while page_number < max_pages:
        report_data = {
            "vendorId": cfg["vendor_id"],
            "startDate": get_datetime(start_dt).strftime("%Y-%m-%d %H:%M:%S"),
            "endDate": get_datetime(end_dt).strftime("%Y-%m-%d %H:%M:%S"),
            "pageSize": str(page_size),
            "pageNumber": str(page_number),
            "deviceType": "VTS-PWA-ELECTRON",
            "source": "order-pwa",
            "appVersion": "3.14.1",
        }
        report_files = {key: (None, value) for key, value in report_data.items()}
        response = requests.post(
            cfg.get("report_url") or DEFAULT_REPORT_URL,
            headers=headers,
            files=report_files,
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
        if total_pages and page_number + 1 >= total_pages:
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


def _extract_menu_entries(payload):
    """Flatten Food Partner categories into product/variation rows.

    The menu response contains category containers alongside product and
    variation objects.  Category ``id``/``title`` pairs must not become
    mappable Items, but their title is useful context for each child row.
    """
    entries = []
    seen = set()
    category_child_keys = {
        "products",
        "items",
        "menuitems",
        "children",
        "subcategories",
        "productgroups",
        "categories",
        "menucategories",
        "categoryproducts",
        "productlist",
        "submenus",
        "submenu",
        "menus",
        "menu",
        "groups",
        "entries",
        "data",
    }
    category_parent_keys = {
        "category",
        "categories",
        "menucategory",
        "menucategories",
        "productgroup",
        "productgroups",
        "group",
        "groups",
    }
    variation_child_keys = {"variations", "variation", "productvariations"}
    product_marker_keys = {
        "productid",
        "variationid",
        "menuitemid",
        "producthashid",
        "variationhashid",
        "hashid",
        "price",
        "status",
        "canchangestatus",
        "producttitle",
        "variationtitle",
        "productname",
        "variationname",
        "description",
    }

    def normalize_key(key):
        return re.sub(r"[^a-z0-9]", "", str(key or "").lower())

    def first_value(value, keys):
        wanted = {normalize_key(key) for key in keys}
        for raw_key, candidate in value.items():
            if normalize_key(raw_key) in wanted and candidate not in (None, "", []):
                return candidate
        return ""

    def visit(value, category_title="", category_id="", parent_key=""):
        if isinstance(value, list):
            for child in value:
                visit(child, category_title, category_id, parent_key)
            return
        if not isinstance(value, dict):
            return

        normalized_keys = {normalize_key(key) for key in value}
        nested_children = [
            (raw_key, child)
            for raw_key, child in value.items()
            if isinstance(child, (dict, list))
        ]
        has_category_children = any(
            normalize_key(raw_key) in category_child_keys
            for raw_key, _child in nested_children
        )
        has_nested_values = bool(nested_children)
        has_variation_children = any(
            normalize_key(raw_key) in variation_child_keys
            for raw_key, _child in nested_children
        )
        has_product_markers = bool(normalized_keys.intersection(product_marker_keys))
        explicit_product_id = first_value(
            value,
            (
                "productId",
                "product_id",
                "productHashId",
                "product_hash_id",
                "menuItemId",
                "menu_item_id",
            ),
        )
        explicit_variation_id = first_value(
            value,
            ("variationId", "variation_id", "variationHashId", "variation_hash_id"),
        )
        explicit_category_id = first_value(
            value,
            ("categoryId", "category_id", "menuCategoryId", "menu_category_id"),
        )
        explicit_category_title = first_value(
            value,
            ("categoryTitle", "category_title", "categoryName", "menuCategoryName"),
        )
        generic_title = first_value(value, ("title", "name"))
        product_title = first_value(
            value,
            ("productTitle", "product_title", "productName", "product_name"),
        )
        variation_title = first_value(
            value,
            ("variationTitle", "variation_title", "variationName", "variation_name"),
        )
        category_identity_matches_product = bool(
            explicit_category_id
            and explicit_product_id
            and str(explicit_category_id) == str(explicit_product_id)
        )
        category_identity_matches_id = bool(
            explicit_category_id
            and value.get("id") not in (None, "")
            and str(explicit_category_id) == str(value.get("id"))
        )
        is_category = bool(
            has_nested_values
            and not explicit_variation_id
            and not has_variation_children
            and (
                (has_category_children and not has_product_markers)
                or explicit_category_title
                or category_identity_matches_product
                or category_identity_matches_id
                or (
                    generic_title
                    and not product_title
                    and not variation_title
                    and not first_value(value, ("price", "status"))
                    and not has_variation_children
                    and (has_category_children or explicit_product_id)
                )
                or (
                    generic_title
                    and not product_title
                    and not variation_title
                    and not first_value(value, ("price", "status"))
                    and normalize_key(parent_key) in category_parent_keys
                )
            )
        )

        title = str(
            first_value(
                value,
                (
                    "title",
                    "name",
                    "productName",
                    "product_name",
                    "productTitle",
                    "variationTitle",
                    "variation_title",
                    "variationName",
                    "menuItemName",
                    "itemName",
                    "displayName",
                ),
            )
            or ""
        ).strip()
        next_category_title = str(
            first_value(
                value,
                ("categoryTitle", "category_title", "categoryName", "menuCategoryName"),
            )
            or category_title
            or (title if is_category else "")
        ).strip()
        next_category_id = str(
            first_value(value, ("categoryId", "category_id", "menuCategoryId", "menu_category_id"))
            or category_id
            or (value.get("id") if is_category else "")
            or (explicit_product_id if is_category else "")
            or ""
        ).strip()
        external_id = str(
            first_value(
                value,
                (
                    "variationId",
                    "variation_id",
                    "productId",
                    "product_id",
                    "menuItemId",
                    "menu_item_id",
                    "variationHashId",
                    "variation_hash_id",
                    "productHashId",
                    "product_hash_id",
                    "hashId",
                ),
            )
            or (value.get("id") if not is_category else "")
            or ""
        ).strip()
        if external_id and title and not is_category:
            row = dict(value)
            if next_category_title:
                row["_category_title"] = next_category_title
            if next_category_id:
                row["_category_id"] = next_category_id
            key = f"{external_id}|{title}|{next_category_id}"
            if key not in seen:
                seen.add(key)
                entries.append(row)
        for raw_key, child in value.items():
            if isinstance(child, (dict, list)):
                visit(child, next_category_title, next_category_id, raw_key)

    visit(payload)
    return entries


def _normalize_mapping_text(value):
    text = str(value or "").strip().lower()
    replacements = {"ي": "ی", "ك": "ک", "ۀ": "ه", "ة": "ه"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[\s\-_/]+", "", text)


def fetch_snapp_menu(settings=None):
    cfg = settings or _get_settings()
    if not cfg.get("token"):
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")
    if not cfg.get("vendor_id"):
        raise frappe.ValidationError("شناسه فروشنده Food Partner تنظیم نشده است.")

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {cfg['token']}",
        "vendor-authorization": "true",
        "user-agent": "Mozilla/5.0",
    }
    if cfg.get("host_domain"):
        headers["hostdomain"] = cfg["host_domain"]
    if cfg.get("origin_url"):
        headers["origin"] = cfg["origin_url"]
        headers["referer"] = f"{cfg['origin_url'].rstrip('/')}/"
    try:
        response = requests.get(
            f"{cfg.get('menu_api_base_url') or DEFAULT_MENU_API_BASE_URL}/vendor-menu/v2/vendor/{cfg['vendor_id']}/menu",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code in (401, 403):
            raise frappe.ValidationError(
                "توکن Food Partner معتبر نیست یا دسترسی منوی فروشنده رد شد. توکن خام یا مقدار Bearer را دوباره ذخیره کنید."
            ) from exc
        raise frappe.ValidationError(
            f"دریافت منوی Food Partner با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
        ) from exc
    except requests.RequestException as exc:
        raise frappe.ValidationError(
            "ارتباط با API منوی Food Partner برقرار نشد؛ آدرس API و اتصال شبکه را بررسی کنید."
        ) from exc
    except (TypeError, ValueError) as exc:
        raise frappe.ValidationError("پاسخ API منوی Food Partner قابل خواندن نیست.") from exc
    rows = []
    for entry in _extract_menu_entries(payload):
        fallback_id = str(entry.get("id") or "").strip()
        explicit_product_id = str(entry.get("productId") or entry.get("product_id") or "").strip()
        explicit_variation_id = str(entry.get("variationId") or entry.get("variation_id") or "").strip()
        variation_like = bool(
            explicit_variation_id
            or entry.get("variationTitle")
            or entry.get("variation_title")
            or entry.get("variationName")
            or ("price" in entry and fallback_id)
        )
        product_id = explicit_product_id or (fallback_id if not variation_like else "")
        variation_id = explicit_variation_id or (fallback_id if variation_like else "")
        rows.append(
            {
                "external_id": str(
                    variation_id
                    or product_id
                    or entry.get("variationHashId")
                    or entry.get("variation_hash_id")
                    or entry.get("productHashId")
                    or entry.get("product_hash_id")
                    or fallback_id
                    or ""
                ).strip(),
                "product_id": product_id,
                "variation_id": variation_id,
                "product_hash_id": str(entry.get("productHashId") or entry.get("product_hash_id") or "").strip(),
                "variation_hash_id": str(entry.get("variationHashId") or entry.get("variation_hash_id") or "").strip(),
                "category_id": str(entry.get("_category_id") or entry.get("categoryId") or entry.get("category_id") or "").strip(),
                "category_title": str(
                    entry.get("_category_title")
                    or entry.get("categoryTitle")
                    or entry.get("category_title")
                    or entry.get("categoryName")
                    or entry.get("menuCategoryName")
                    or ""
                ).strip(),
                "title": str(
                    entry.get("title")
                    or entry.get("name")
                    or entry.get("productName")
                    or entry.get("product_name")
                    or entry.get("productTitle")
                    or entry.get("variationTitle")
                    or entry.get("variation_title")
                    or entry.get("variationName")
                    or entry.get("menuItemName")
                    or entry.get("itemName")
                    or entry.get("displayName")
                    or ""
                ).strip(),
                "price": flt(entry.get("price") or entry.get("variationPrice") or entry.get("variation_price") or 0),
                "status": str(entry.get("status") or "").strip(),
            }
        )
    if _has_field("Restaurant Web Settings", "snapp_last_menu_sync_at"):
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_menu_sync_at", get_datetime_str(now_datetime()))
    frappe.db.commit()
    return {"status": "success", "count": len(rows), "items": rows}


def _get_local_item_rows(search=""):
    fields = ["name", "item_code", "item_name", "disabled"]
    for fieldname in (
        "custom_snapp_code",
        "restaurant_external_menu_item_id",
        "restaurant_external_product_id",
        "restaurant_external_variation_id",
        "restaurant_external_product_hash_id",
        "restaurant_external_variation_hash_id",
        "restaurant_external_mapping_status",
    ):
        if _has_column("Item", fieldname):
            fields.append(fieldname)
    filters = {"disabled": 0}
    rows = frappe.get_all("Item", filters=filters, fields=fields, limit_page_length=1000, ignore_permissions=True)
    needle = _normalize_mapping_text(search)
    if needle:
        rows = [row for row in rows if needle in _normalize_mapping_text(row.get("item_name")) or needle in _normalize_mapping_text(row.get("item_code"))]
    return rows


def get_snappfood_mapping_rows(search="", refresh_menu=0):
    cfg = _get_settings()
    local_items = _get_local_item_rows(search)
    menu_rows = []
    if refresh_menu:
        menu_rows = fetch_snapp_menu(cfg).get("items") or []
    local_by_external = {}
    for item in local_items:
        for key in (
            "restaurant_external_variation_id",
            "restaurant_external_product_id",
            "restaurant_external_variation_hash_id",
            "restaurant_external_product_hash_id",
            "restaurant_external_menu_item_id",
        ):
            value = str(item.get(key) or "").strip()
            if value:
                local_by_external[value] = item

    mappings = []
    for row in menu_rows:
        exact = local_by_external.get(row["external_id"])
        if exact:
            suggested = exact
            match_score = 1
        else:
            suggested = max(
                local_items,
                key=lambda item: SequenceMatcher(
                    None,
                    _normalize_mapping_text(row.get("title")),
                    _normalize_mapping_text(item.get("item_name")),
                ).ratio(),
                default=None,
            )
            match_score = (
                SequenceMatcher(
                    None,
                    _normalize_mapping_text(row.get("title")),
                    _normalize_mapping_text((suggested or {}).get("item_name")),
                ).ratio()
                if suggested
                else 0
            )
        mappings.append({**row, "suggested_item": suggested, "match_score": round(match_score, 3)})
    return {"status": "success", "settings": get_sync_status(), "menu": mappings, "items": local_items}


def save_snappfood_item_mapping(item_name, product_id="", variation_id="", product_hash_id="", variation_hash_id="", menu_item_id=""):
    if not item_name or not frappe.db.exists("Item", item_name):
        raise frappe.ValidationError("آیتم داخلی برای نگاشت معتبر نیست.")
    values = {}
    for fieldname, value in (
        ("restaurant_external_product_id", product_id),
        ("restaurant_external_variation_id", variation_id),
        ("restaurant_external_product_hash_id", product_hash_id),
        ("restaurant_external_variation_hash_id", variation_hash_id),
        ("restaurant_external_menu_item_id", menu_item_id or variation_id or product_id),
    ):
        if _has_column("Item", fieldname):
            values[fieldname] = str(value or "").strip()
    if _has_column("Item", "restaurant_external_mapping_status"):
        values["restaurant_external_mapping_status"] = "Mapped"
    if not values:
        raise frappe.ValidationError("فیلدهای اتصال اسنپ‌فود هنوز روی Item ساخته نشده‌اند.")
    frappe.db.set_value("Item", item_name, values, update_modified=True)
    frappe.db.commit()
    return {"status": "success", "item": item_name, "values": values}


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
    order_id = str(raw_order.get("id") or raw_order.get("orderId") or raw_order.get("order_id") or "").strip()
    if not order_id:
        raise frappe.ValidationError("Missing Snapp order id.")

    full_name = (raw_order.get("fullName") or raw_order.get("customerName") or raw_order.get("customer_name") or "").strip()
    if not full_name:
        full_name = " ".join(
            part
            for part in [
                (raw_order.get("firstName") or "").strip(),
                (raw_order.get("lastName") or "").strip(),
            ]
            if part
        ).strip()
    if not full_name:
        full_name = FALLBACK_GUEST_NAME

    items = []
    raw_items = (
        raw_order.get("orderItems")
        or raw_order.get("orderProducts")
        or raw_order.get("order_products")
        or raw_order.get("items")
        or raw_order.get("products")
        or []
    )
    if isinstance(raw_items, dict):
        raw_items = raw_items.get("items") or raw_items.get("products") or []
    for row in raw_items:
        qty = max(flt(row.get("count") or row.get("newCount") or row.get("quantity") or row.get("qty") or 1), 1)
        items.append(
            {
                "line_id": str(
                    row.get("id") or row.get("orderProductId") or row.get("order_product_id") or row.get("orderProductID") or ""
                ).strip(),
                "menu_item_id": str(
                    row.get("menuItemId")
                    or row.get("variationId")
                    or row.get("variation_id")
                    or row.get("productId")
                    or row.get("product_id")
                    or ""
                ).strip(),
                "product_id": str(row.get("productId") or row.get("product_id") or "").strip(),
                "variation_id": str(row.get("variationId") or row.get("variation_id") or "").strip(),
                "product_hash_id": str(row.get("productHashId") or row.get("product_hash_id") or "").strip(),
                "variation_hash_id": str(row.get("variationHashId") or row.get("variation_hash_id") or "").strip(),
                "title": (
                    row.get("title")
                    or row.get("menuItemTitle")
                    or row.get("productName")
                    or row.get("product_name")
                    or row.get("name")
                    or ""
                ).strip()
                or "Snapp Item",
                "qty": qty,
                "unit_price": _scale_amount(row.get("price") or row.get("unitPrice") or row.get("unit_price"), amount_multiplier),
                "discount": _scale_amount(row.get("discount") or row.get("discountAmount"), amount_multiplier),
                "packaging_cost": _scale_amount(row.get("packagingCost"), amount_multiplier),
                "with_tax": cint(row.get("withTax") or 0),
                "toppings": row.get("toppings") or [],
            }
        )

    return {
        "order_id": order_id,
        "bill_number": str(
            raw_order.get("billNumber")
            or raw_order.get("vendorOrderCode")
            or raw_order.get("orderCode")
            or raw_order.get("supportOrderId")
            or ""
        ).strip(),
        "offline_bill_number": str(raw_order.get("offlineBillNumber") or "").strip(),
        "external_state": str(
            raw_order.get("orderHistoryState")
            or raw_order.get("externalStatusLabel")
            or raw_order.get("status")
            or ""
        ).strip(),
        "last_state": cint(raw_order.get("lastState") or raw_order.get("externalStatusCode") or 0),
        "status": _map_status(
            raw_order.get("orderHistoryState") or raw_order.get("externalStatusLabel") or raw_order.get("status"),
            raw_order.get("lastState") or raw_order.get("externalStatusCode"),
        ),
        "order_type": _map_order_type(raw_order.get("orderType"), raw_order.get("deliveryType") or raw_order.get("expeditionType")),
        "delivery_type": str(raw_order.get("deliveryType") or raw_order.get("expeditionType") or "").strip(),
        "payment_method": str(raw_order.get("paymentMethod") or raw_order.get("payment_type_raw") or raw_order.get("paymentTypeRaw") or "").strip(),
        "factor_number": cstr(raw_order.get("factorNumber") or "").strip(),
        "customer_name": full_name,
        "mobile": _normalize_mobile(
            raw_order.get("phoneNumber") or raw_order.get("phone") or raw_order.get("mobile") or raw_order.get("mobileNo")
        ),
        "external_customer_id": str(
            raw_order.get("customerId") or raw_order.get("customer_id") or raw_order.get("userId") or ""
        ).strip(),
        "created_at": get_datetime(
            raw_order.get("createdAt") or raw_order.get("orderDate") or raw_order.get("newOrderDate")
        )
        if (raw_order.get("createdAt") or raw_order.get("orderDate") or raw_order.get("newOrderDate"))
        else now_datetime(),
        "preparation_time": get_datetime(raw_order.get("preparationTime")) if raw_order.get("preparationTime") else None,
        "print_time": get_datetime(raw_order.get("printTime") or raw_order.get("deliveryTime"))
        if (raw_order.get("printTime") or raw_order.get("deliveryTime"))
        else None,
        "address": (raw_order.get("addressDescription") or raw_order.get("address") or raw_order.get("deliveryAddress") or "").strip(),
        "note": (raw_order.get("note") or raw_order.get("description") or "").strip(),
        "discount_code": cstr(raw_order.get("discountCode") or "").strip(),
        "discount_type": cstr(raw_order.get("discountType") or "").strip(),
        "vendor_name": cstr(raw_order.get("vendorName") or "").strip(),
        "vendor_subdomain": cstr(raw_order.get("vendorSubdomain") or "").strip(),
        "items": items,
        "final_amount": _scale_amount(
            raw_order.get("finalAmount")
            or raw_order.get("finalPrice")
            or raw_order.get("totalPrice")
            or raw_order.get("total")
            or raw_order.get("paidPrice")
            or raw_order.get("price"),
            amount_multiplier,
        ),
        "final_price": _scale_amount(
            raw_order.get("finalPrice") or raw_order.get("totalPrice") or raw_order.get("paidPrice"), amount_multiplier
        ),
        "paid_price": _scale_amount(raw_order.get("paidPrice") or raw_order.get("paid_price"), amount_multiplier),
        "discount": _scale_amount(
            raw_order.get("discount") or raw_order.get("discountAmount") or raw_order.get("otherDiscounts"),
            amount_multiplier,
        ),
        "discount_amount": _scale_amount(raw_order.get("discountAmount") or 0, amount_multiplier),
        "packaging_cost": _scale_amount(raw_order.get("packagingCost") or raw_order.get("packingPrice"), amount_multiplier),
        "delivery_cost": _scale_amount(raw_order.get("deliveryCost") or raw_order.get("deliveryPrice"), amount_multiplier),
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
            updates = {}
            if external_customer_id and _has_column("Customer", "restaurant_external_customer_id"):
                updates["restaurant_external_customer_id"] = external_customer_id
            if _has_column("Customer", "restaurant_external_source"):
                updates["restaurant_external_source"] = SNAPP_SOURCE
            if updates:
                frappe.db.set_value("Customer", existing, updates, update_modified=False)
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
    if _has_column("Customer", "restaurant_external_source"):
        customer_doc.restaurant_external_source = SNAPP_SOURCE
    if _has_column("Customer", "restaurant_external_customer_id"):
        customer_doc.restaurant_external_customer_id = external_customer_id or ""
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


def _tag_item_mapping(item_name, line):
    values = {}
    for fieldname, value in (
        ("restaurant_external_menu_item_id", line.get("menu_item_id")),
        ("restaurant_external_product_id", line.get("product_id")),
        ("restaurant_external_variation_id", line.get("variation_id")),
        ("restaurant_external_product_hash_id", line.get("product_hash_id")),
        ("restaurant_external_variation_hash_id", line.get("variation_hash_id")),
    ):
        if value and _has_column("Item", fieldname):
            values[fieldname] = value
    if values and _has_column("Item", "restaurant_external_mapping_status"):
        values["restaurant_external_mapping_status"] = "Mapped"
    if values:
        frappe.db.set_value("Item", item_name, values, update_modified=False)


def _resolve_item_code(line):
    external_menu_item_id = (line.get("menu_item_id") or "").strip()
    external_product_id = (line.get("product_id") or "").strip()
    external_variation_id = (line.get("variation_id") or "").strip()
    external_product_hash_id = (line.get("product_hash_id") or "").strip()
    external_variation_hash_id = (line.get("variation_hash_id") or "").strip()
    title = (line.get("title") or "").strip() or "Snapp Item"
    snapp_code = _build_item_code(line)

    if _has_column("Item", "custom_snapp_code"):
        by_snapp_code = frappe.db.get_value("Item", {"custom_snapp_code": snapp_code}, "name")
        if by_snapp_code:
            _tag_item_mapping(by_snapp_code, line)
            return by_snapp_code

    if external_menu_item_id and _has_column("Item", "restaurant_external_menu_item_id"):
        by_external = frappe.db.get_value("Item", {"restaurant_external_menu_item_id": external_menu_item_id}, "name")
        if by_external:
            _tag_item_mapping(by_external, line)
            if _has_column("Item", "custom_snapp_code"):
                current_snapp_code = frappe.db.get_value("Item", by_external, "custom_snapp_code")
                if not (current_snapp_code or "").strip():
                    frappe.db.set_value("Item", by_external, "custom_snapp_code", snapp_code, update_modified=False)
            return by_external

    if external_variation_id and _has_column("Item", "restaurant_external_variation_id"):
        by_variation = frappe.db.get_value("Item", {"restaurant_external_variation_id": external_variation_id}, "name")
        if by_variation:
            _tag_item_mapping(by_variation, line)
            return by_variation

    if external_product_id and _has_column("Item", "restaurant_external_product_id"):
        by_product = frappe.db.get_value("Item", {"restaurant_external_product_id": external_product_id}, "name")
        if by_product:
            _tag_item_mapping(by_product, line)
            return by_product

    if external_variation_hash_id and _has_column("Item", "restaurant_external_variation_hash_id"):
        by_variation_hash = frappe.db.get_value(
            "Item",
            {"restaurant_external_variation_hash_id": external_variation_hash_id},
            "name",
        )
        if by_variation_hash:
            _tag_item_mapping(by_variation_hash, line)
            return by_variation_hash

    if external_product_hash_id and _has_column("Item", "restaurant_external_product_hash_id"):
        by_product_hash = frappe.db.get_value(
            "Item",
            {"restaurant_external_product_hash_id": external_product_hash_id},
            "name",
        )
        if by_product_hash:
            _tag_item_mapping(by_product_hash, line)
            return by_product_hash

    by_title = frappe.db.get_value("Item", {"item_name": title}, "name")
    if by_title:
        _tag_item_mapping(by_title, line)
        if _has_column("Item", "custom_snapp_code"):
            current_snapp_code = frappe.db.get_value("Item", by_title, "custom_snapp_code")
            if not (current_snapp_code or "").strip():
                frappe.db.set_value("Item", by_title, "custom_snapp_code", snapp_code, update_modified=False)
        return by_title

    settings = _get_settings()
    if settings.get("require_item_mapping"):
        raise frappe.ValidationError(
            f"کالای Food Partner نگاشت نشده است: {title} ({external_variation_id or external_product_id or external_menu_item_id or 'بدون شناسه'})"
        )

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
    if _has_column("Item", "restaurant_external_product_id"):
        item_doc.set("restaurant_external_product_id", external_product_id)
    if _has_column("Item", "restaurant_external_variation_id"):
        item_doc.set("restaurant_external_variation_id", external_variation_id)
    if _has_column("Item", "restaurant_external_product_hash_id"):
        item_doc.set("restaurant_external_product_hash_id", line.get("product_hash_id") or "")
    if _has_column("Item", "restaurant_external_variation_hash_id"):
        item_doc.set("restaurant_external_variation_hash_id", line.get("variation_hash_id") or "")
    if _has_column("Item", "restaurant_external_mapping_status"):
        item_doc.set("restaurant_external_mapping_status", "Mapped")
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
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_product_id", line.get("product_id") or "")
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_variation_id", line.get("variation_id") or "")
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_product_hash_id", line.get("product_hash_id") or "")
        _set_if_column(line_payload, "Sales Order Item", "restaurant_external_variation_hash_id", line.get("variation_hash_id") or "")
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
    _set_if_column(target_payload, "Sales Order", "restaurant_external_customer_id", order_payload.get("external_customer_id") or "")
    _set_if_column(target_payload, "Sales Order", "restaurant_external_order_created_at", order_payload.get("created_at"))
    _set_if_column(
        target_payload,
        "Sales Order",
        "restaurant_external_payload_json",
        json.dumps(_redact_external_payload(order_payload["raw"]), ensure_ascii=False),
    )


def _build_sales_invoice_external_values(order_payload):
    """Build the Food Partner snapshot kept on the native Sales Invoice.

    POS/ERPNext totals remain authoritative for the invoice itself. These
    values are a reconciliation snapshot of the external report so an
    accountant can compare the imported amount, fees and discounts later.
    """
    return {
        "restaurant_external_source": SNAPP_SOURCE,
        "restaurant_external_order_id": order_payload.get("order_id"),
        "restaurant_external_bill_number": order_payload.get("bill_number"),
        "restaurant_external_state": order_payload.get("external_state"),
        "restaurant_external_payment_method": order_payload.get("payment_method"),
        "restaurant_external_customer_id": order_payload.get("external_customer_id") or "",
        "restaurant_external_delivery_type": order_payload.get("delivery_type") or "",
        "restaurant_external_factor_number": order_payload.get("factor_number") or "",
        "restaurant_external_discount": flt(order_payload.get("discount") or 0),
        "restaurant_external_discount_amount": flt(order_payload.get("discount_amount") or 0),
        "restaurant_external_delivery_cost": flt(order_payload.get("delivery_cost") or 0),
        "restaurant_external_packaging_cost": flt(order_payload.get("packaging_cost") or 0),
        "restaurant_external_tax": flt(order_payload.get("tax") or 0),
        "restaurant_external_service_cost": flt(order_payload.get("service_cost") or 0),
        "restaurant_external_service_fee": flt(order_payload.get("service_fee") or 0),
        "restaurant_external_tip": flt(order_payload.get("tip") or 0),
        "restaurant_external_refund_amount": flt(order_payload.get("refund_amount") or 0),
        "restaurant_external_final_price": flt(order_payload.get("final_price") or 0),
        "restaurant_external_paid_price": flt(order_payload.get("paid_price") or 0),
        "restaurant_external_payload_json": json.dumps(
            _redact_external_payload(order_payload.get("raw") or {}), ensure_ascii=False
        ),
    }


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
    """Create an imported order through the same native POS order builder."""
    external_customer = _ensure_customer(
        customer_name=order_payload["customer_name"],
        mobile=order_payload["mobile"],
        external_customer_id=order_payload["external_customer_id"],
    )
    settings = _get_settings()
    customer = external_customer
    secondary_customer = ""
    customer_mobile_for_pos = order_payload["mobile"]
    configured_customer = settings.get("default_customer") or ""
    if configured_customer and frappe.db.exists("Customer", configured_customer):
        customer = configured_customer
        customer_mobile_for_pos = ""
        if external_customer != configured_customer:
            secondary_customer = frappe.db.get_value("Customer", external_customer, "customer_name") or external_customer
    source_items = order_payload.get("items") or []
    if not source_items:
        raise frappe.ValidationError(f"Order {order_payload['order_id']} has no valid items.")
    # POS resolves pricing, BOM/customization, service items, taxes and order
    # context itself. Resolve each mapped Item to the slug/name accepted by it.
    cart_items = []
    resolved_lines = []
    for line in source_items:
        item_code = _resolve_item_code(line)
        item_slug = (frappe.db.get_value("Item", item_code, "restaurant_slug") or item_code or "").strip()
        if not item_slug:
            raise frappe.ValidationError(f"کد Item برای ردیف سفارش {order_payload['order_id']} خالی است.")
        cart_items.append(
            {
                "item_slug": item_slug,
                "qty": max(flt(line.get("qty") or 1), 1),
                "note": line.get("title") or "",
            }
        )
        resolved_lines.append({**line, "item_code": item_code, "item_slug": item_slug})

    totals = {
        "discountAmount": flt(order_payload.get("discount_amount") or order_payload.get("discount") or 0),
        "taxAmount": flt(order_payload.get("tax") or 0),
        "serviceAmount": flt(order_payload.get("service_cost") or order_payload.get("service_fee") or 0),
        "packagingAmount": flt(order_payload.get("packaging_cost") or 0),
        "tipAmount": flt(order_payload.get("tip") or 0),
    }
    order_context = {
        "source": SNAPP_SOURCE,
        "external_order_id": order_payload["order_id"],
        "order_type": order_payload["order_type"],
    }
    # Import lazily to avoid loading the API module while Frappe imports this module.
    from restaurant.api import _append_sales_order_note, _create_pos_order_payload, _set_restaurant_order_status

    result = _create_pos_order_payload(
        {
            "customer_name": frappe.db.get_value("Customer", customer, "customer_name") or customer,
            "mobile": customer_mobile_for_pos,
            "order_type": order_payload["order_type"],
            "items": cart_items,
            "address": order_payload["address"],
            "note": order_payload["note"],
            "include_service_items": 1,
            "order_context": order_context,
            "totals": totals,
            "secondary_customer": secondary_customer,
        },
        commit=False,
    )
    so_name = result.get("order_id") or result.get("name") or ""
    if not so_name:
        raise frappe.ValidationError(f"سفارش Food Partner {order_payload['order_id']} ساخته نشد.")

    updates = {}
    _apply_sales_order_external_fields(updates, order_payload)
    if _has_column("Sales Order", "restaurant_customer_mobile"):
        updates["restaurant_customer_mobile"] = order_payload["mobile"]
    if _has_column("Sales Order", "restaurant_order_type"):
        updates["restaurant_order_type"] = order_payload["order_type"]
    if _has_column("Sales Order", "restaurant_delivery_address"):
        updates["restaurant_delivery_address"] = order_payload["address"]
    if _has_column("Sales Order", "restaurant_note"):
        updates["restaurant_note"] = order_payload["note"]
    if _has_column("Sales Order", "restaurant_status"):
        updates["restaurant_status"] = order_payload["status"]
    if secondary_customer and _has_column("Sales Order", "restaurant_secondary_customer"):
        updates["restaurant_secondary_customer"] = secondary_customer
    for fieldname, value in updates.items():
        frappe.db.set_value("Sales Order", so_name, fieldname, value, update_modified=False)

    # POS added service rows as well; only annotate the imported product lines.
    so_rows = frappe.get_all(
        "Sales Order Item",
        filters={"parent": so_name},
        fields=["name", "item_code", "idx"],
        order_by="idx asc",
        limit_page_length=500,
        ignore_permissions=True,
    )
    used_rows = set()
    for line in resolved_lines:
        target = next(
            (
                row
                for row in so_rows
                if row.name not in used_rows and row.item_code == line["item_code"]
            ),
            None,
        )
        if not target:
            continue
        used_rows.add(target.name)
        line_updates = {}
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_line_id", line.get("line_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_menu_item_id", line.get("menu_item_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_item_title", line.get("title") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_product_id", line.get("product_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_variation_id", line.get("variation_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_product_hash_id", line.get("product_hash_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_variation_hash_id", line.get("variation_hash_id") or "")
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_discount", flt(line.get("discount") or 0))
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_packaging_cost", flt(line.get("packaging_cost") or 0))
        _set_if_column(line_updates, "Sales Order Item", "restaurant_external_with_tax", cint(line.get("with_tax") or 0))
        _set_if_column(
            line_updates,
            "Sales Order Item",
            "restaurant_external_toppings_json",
            json.dumps(line.get("toppings") or [], ensure_ascii=False),
        )
        if line_updates:
            frappe.db.set_value("Sales Order Item", target.name, line_updates, update_modified=False)

    _append_sales_order_note(so_name, f"[FOOD_PARTNER] Imported order {order_payload['order_id']} through POS flow.")
    _set_restaurant_order_status(so_name, order_payload["status"], force=True)
    if order_payload["status"] == "cancelled":
        so_doc = frappe.get_doc("Sales Order", so_name)
        if so_doc.docstatus == 1:
            so_doc.flags.ignore_permissions = True
            so_doc.cancel()
        return so_name, "cancelled"
    return so_name, "created"


def _ensure_sales_invoice_for_order(sales_order_name, order_payload):
    """Create the native Sales Invoice through the existing POS settlement path."""
    if not _has_column("Sales Invoice", "restaurant_external_order_id"):
        return {"status": "skipped", "reason": "Sales Invoice integration fields are not migrated."}

    existing_invoice = frappe.db.get_value(
        "Sales Invoice",
        {"restaurant_external_order_id": order_payload["order_id"]},
        "name",
    )
    if existing_invoice:
        return {"status": "exists", "sales_invoice": existing_invoice}

    payment_text = str(order_payload.get("payment_method") or "").strip().lower()
    if any(token in payment_text for token in ("cash", "نقد")):
        payment_method = "cash"
    elif any(token in payment_text for token in ("credit", "اعتبار")):
        payment_method = "credit"
    elif any(token in payment_text for token in ("card", "online", "bank", "درگاه", "کارت")):
        payment_method = "card"
    elif flt(order_payload.get("paid_price") or order_payload.get("final_amount") or 0) > 0:
        payment_method = "card"
    else:
        payment_method = "credit"

    # This is the same settlement function used by Management POS. It creates
    # the SI, payments, payment method, status and audit note consistently.
    from restaurant.api import settle_pos_order

    settlement = settle_pos_order(
        order_name=sales_order_name,
        payment={
            "method": payment_method,
            "reference_no": order_payload.get("bill_number") or order_payload.get("order_id") or "",
        },
        commit=False,
    )
    invoice_name = settlement.get("sales_invoice") if isinstance(settlement, dict) else ""
    if not invoice_name:
        raise frappe.ValidationError(f"فاکتور سفارش Food Partner {order_payload['order_id']} ساخته نشد.")

    invoice_updates = _build_sales_invoice_external_values(order_payload)
    for fieldname in list(invoice_updates):
        if not _has_column("Sales Invoice", fieldname):
            invoice_updates.pop(fieldname, None)
    if invoice_updates:
        frappe.db.set_value("Sales Invoice", invoice_name, invoice_updates, update_modified=False)

    so_rows = frappe.get_all(
        "Sales Order Item",
        filters={"parent": sales_order_name},
        fields=["name", "item_code", "restaurant_external_line_id", "restaurant_external_menu_item_id"],
        order_by="idx asc",
        limit_page_length=500,
        ignore_permissions=True,
    )
    invoice_rows = frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": invoice_name},
        fields=["name", "sales_order", "so_detail", "item_code", "idx"],
        order_by="idx asc",
        limit_page_length=500,
        ignore_permissions=True,
    )
    for invoice_row in invoice_rows:
        source_row = next(
            (
                row
                for row in so_rows
                if row.item_code == invoice_row.item_code
                and (
                    not invoice_row.so_detail
                    or row.name == invoice_row.so_detail
                )
            ),
            None,
        )
        if not source_row:
            continue
        source_values = frappe.db.get_value(
            "Sales Order Item",
            source_row.name,
            [
                field
                for field in (
                    "restaurant_external_line_id",
                    "restaurant_external_menu_item_id",
                    "restaurant_external_item_title",
                    "restaurant_external_product_id",
                    "restaurant_external_variation_id",
                    "restaurant_external_product_hash_id",
                    "restaurant_external_variation_hash_id",
                    "restaurant_external_discount",
                    "restaurant_external_packaging_cost",
                    "restaurant_external_with_tax",
                    "restaurant_external_toppings_json",
                )
                if _has_column("Sales Order Item", field)
            ],
            as_dict=True,
        ) or {}
        invoice_values = {}
        for fieldname in (
            "restaurant_external_line_id",
            "restaurant_external_menu_item_id",
            "restaurant_external_item_title",
            "restaurant_external_product_id",
            "restaurant_external_variation_id",
            "restaurant_external_product_hash_id",
            "restaurant_external_variation_hash_id",
            "restaurant_external_discount",
            "restaurant_external_packaging_cost",
            "restaurant_external_with_tax",
            "restaurant_external_toppings_json",
        ):
            if _has_column("Sales Invoice Item", fieldname) and fieldname in source_values:
                invoice_values[fieldname] = source_values.get(fieldname) or ""
        if invoice_values:
            frappe.db.set_value("Sales Invoice Item", invoice_row.name, invoice_values, update_modified=False)

    return {"status": "created", "sales_invoice": invoice_name, "payment_method": payment_method}


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
    schema_status = _get_schema_status()
    if not schema_status["ready"]:
        return {
            "status": "skipped",
            "reason": "Food Partner integration fields are not migrated.",
            "schema_ready": False,
            "schema_missing": schema_status["missing"],
        }
    if not settings["token"]:
        return {"status": "error", "reason": "Snapp bearer token is missing."}
    if not settings.get("vendor_id"):
        return {
            "status": "skipped",
            "reason": "Food Partner vendor ID is not configured; the legacy order endpoint is disabled.",
        }

    started_at = now_datetime()
    only_new = cint(only_new)
    update_status_fields = cint(update_status_fields)
    result = {
        "status": "success",
        "trigger": trigger,
        "only_new": only_new,
        "fetched_count": 0,
        "created_count": 0,
        "invoices_created_count": 0,
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
                    # ``only_new`` controls line reconciliation/backfill; it
                    # must not freeze the native order state. The scheduler
                    # runs with this flag enabled, so status fields on an
                    # existing Sales Order still need to follow Food Partner
                    # (including native cancellation) on every poll.
                    action = "skipped"
                    if update_status_fields:
                        action = _sync_existing_sales_order(
                            existing,
                            normalized,
                            reconcile_lines=not bool(only_new),
                        )
                        if action == "cancelled":
                            result["cancelled_count"] += 1
                        else:
                            result["updated_count"] += 1

                    if settings.get("auto_sync_invoices") and action != "cancelled":
                        try:
                            invoice_result = _ensure_sales_invoice_for_order(existing, normalized)
                            if invoice_result.get("status") == "created":
                                result.setdefault("invoices_created_count", 0)
                                result["invoices_created_count"] += 1
                        except Exception:
                            result["failed_count"] += 1
                            result["errors"].append(
                                {
                                    "order_id": normalized["order_id"],
                                    "error": frappe.get_traceback(with_context=False),
                                }
                            )

                    if action == "skipped":
                        result["skipped_count"] += 1
                    continue

                sales_order_name, action = _create_sales_order(normalized)
                if settings.get("auto_sync_invoices") and action != "cancelled":
                    invoice_result = _ensure_sales_invoice_for_order(sales_order_name, normalized)
                    if invoice_result.get("status") == "created":
                        result.setdefault("invoices_created_count", 0)
                        result["invoices_created_count"] += 1
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
