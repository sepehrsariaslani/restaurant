import base64
import binascii
import hashlib
import json
import re
import uuid
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from datetime import datetime, timedelta, timezone
from pathlib import Path

import frappe
import requests
from frappe.utils import cint, cstr, flt, get_datetime, get_datetime_str, now_datetime, today
from restaurant.order_review import (
	ORDER_REVIEW_APPROVED,
	ORDER_REVIEW_FIELD,
	ORDER_REVIEW_PENDING,
	ORDER_REVIEW_REJECTED,
	order_is_approved,
)


SNAPP_SOURCE = "snapp_food"
DEFAULT_API_BASE_URL = "https://api.prod.snapp-store.com"
DEFAULT_ORIGIN_URL = ""
DEFAULT_HOST_DOMAIN = ""
DEFAULT_PAGE_SIZE = 50
DEFAULT_LOOKBACK_MINUTES = 180
DEFAULT_AMOUNT_MULTIPLIER = 10
DEFAULT_REPORT_URL = "https://snappfood.ir/vms/v3/restaurant/report"
DEFAULT_PARTNER_WEB_API_BASE_URL = "https://snappfood.ir"
DEFAULT_MENU_API_BASE_URL = "https://apigw.snappfood.ir"
DEFAULT_VENDOR_ACCOUNT_API_BASE_URL = "https://vendor.snappfood.ir"
MAX_PAGE_SIZE = 100
MAX_PAGES = 300
IMPORT_ITEM_GROUP = "Snapp Imported Items"
FALLBACK_GUEST_NAME = "Snapp Guest"
FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD = "restaurant_food_partner_modifier_mappings"
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
    access_token = ""
    if _has_field("Restaurant Web Settings", "snapp_access_token"):
        access_token = _normalize_bearer_token(
            settings_doc.get_password("snapp_access_token", raise_exception=False) or ""
        )

    enabled = cint(settings_doc.get("snapp_sync_enabled")) if _has_field("Restaurant Web Settings", "snapp_sync_enabled") else 0
    return {
        "enabled": bool(enabled),
        "api_base_url": (settings_doc.get("snapp_api_base_url") or DEFAULT_API_BASE_URL).strip().rstrip("/"),
        "origin_url": (settings_doc.get("snapp_origin_url") or DEFAULT_ORIGIN_URL).strip(),
        "host_domain": (settings_doc.get("snapp_hostdomain") or DEFAULT_HOST_DOMAIN).strip(),
        "token": token,
        "access_token": access_token,
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


def _food_partner_token_metadata(token):
    token = _normalize_bearer_token(token)
    if not token:
        return {"hint": "", "username": "", "expires_at": ""}

    metadata = {"hint": f"••••{token[-4:]}", "username": "", "expires_at": ""}
    parts = token.split(".")
    if len(parts) != 3:
        return metadata
    try:
        encoded_payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(encoded_payload.encode("ascii")))
    except (binascii.Error, ValueError, UnicodeError, json.JSONDecodeError):
        return metadata
    if not isinstance(claims, dict):
        return metadata

    metadata["username"] = str(claims.get("username") or "").strip()[:120]
    try:
        expiry = int(claims.get("exp") or 0)
        if expiry > 0:
            metadata["expires_at"] = datetime.fromtimestamp(expiry, tz=timezone.utc).isoformat(timespec="minutes")
    except (OverflowError, OSError, TypeError, ValueError):
        pass
    return metadata


def get_sync_status():
    settings = _get_settings()
    if settings.get("reason"):
        return {**settings, "schema_ready": False, "schema_missing": []}

    schema_status = _get_schema_status()
    token_metadata = _food_partner_token_metadata(settings.get("token"))
    order_access_token_metadata = _food_partner_token_metadata(settings.get("access_token"))

    return {
        "enabled": settings["enabled"],
        "has_token": bool(settings["token"]),
        "has_order_access_token": bool(settings.get("access_token")),
        "token_hint": token_metadata["hint"],
        "token_username": token_metadata["username"],
        "token_expires_at": token_metadata["expires_at"],
        "order_access_token_hint": order_access_token_metadata["hint"],
        "order_access_token_username": order_access_token_metadata["username"],
        "order_access_token_expires_at": order_access_token_metadata["expires_at"],
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


def _food_partner_account_request(url, token):
    try:
        response = requests.get(
            url,
            headers={
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {_normalize_bearer_token(token)}",
                "user-agent": "Mozilla/5.0",
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code in (401, 403):
            message = "توکن Food Partner برای دریافت اطلاعات حساب پذیرفته نشد."
        else:
            message = f"دریافت اطلاعات حساب Food Partner با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
        raise frappe.ValidationError(message) from exc
    except (requests.RequestException, TypeError, ValueError) as exc:
        raise frappe.ValidationError("ارتباط با سرویس اطلاعات حساب Food Partner برقرار نشد.") from exc
    if not isinstance(payload, dict):
        raise frappe.ValidationError("پاسخ اطلاعات حساب Food Partner قابل خواندن نیست.")
    return payload


def _food_partner_json_api_record_attributes(record):
    if not isinstance(record, dict):
        return {}
    attributes = record.get("attributes")
    return attributes if isinstance(attributes, dict) else {}


def _food_partner_json_api_display(value):
    if isinstance(value, dict):
        value = value.get("title") or value.get("name") or value.get("value") or ""
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return str(value).strip()
    return ""


def _food_partner_vendor_user_records(user_payload):
    user_record = user_payload.get("data") if isinstance(user_payload.get("data"), dict) else {}
    relationships = user_record.get("relationships") if isinstance(user_record.get("relationships"), dict) else {}
    vendor_users = relationships.get("vendorUsers") if isinstance(relationships.get("vendorUsers"), dict) else {}
    references = vendor_users.get("data") if isinstance(vendor_users.get("data"), list) else []
    included = user_payload.get("included") if isinstance(user_payload.get("included"), list) else []
    included_by_id = {
        (str(record.get("type") or ""), str(record.get("id") or "")): record
        for record in included
        if isinstance(record, dict)
    }
    records = []
    for reference in references:
        if not isinstance(reference, dict):
            continue
        record = included_by_id.get((str(reference.get("type") or ""), str(reference.get("id") or "")))
        if record:
            records.append(record)
    if not records:
        records = [
            record
            for record in included
            if isinstance(record, dict) and str(record.get("type") or "").lower() == "vendoruser"
        ]
    return user_record, references, records


def _food_partner_vendor_identity(record):
    attributes = _food_partner_json_api_record_attributes(record)
    return {
        str(record.get("id") or "").strip(),
        str(attributes.get("code") or "").strip(),
        str(attributes.get("uid") or "").strip(),
        str(attributes.get("vendorId") or attributes.get("vendor_id") or "").strip(),
    }


def _discover_snappfood_vendor_id(token, user_payload=None):
    """Resolve a vendor ID from the token claims or its authenticated vendor list."""
    token = _normalize_bearer_token(token)
    if not token:
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")
    payload = user_payload or _food_partner_account_request(
        f"{DEFAULT_VENDOR_ACCOUNT_API_BASE_URL}/vms/v2/user/vendors", token
    )
    _user_record, _references, records = _food_partner_vendor_user_records(payload)
    token_vendor_id = _extract_vendor_id_from_token(token)
    if token_vendor_id and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", token_vendor_id):
        if not records or any(token_vendor_id in _food_partner_vendor_identity(record) for record in records):
            return token_vendor_id
    if len(records) == 1:
        record = records[0]
        attributes = _food_partner_json_api_record_attributes(record)
        vendor_id = str(
            attributes.get("vendorId") or attributes.get("vendor_id") or record.get("id") or ""
        ).strip()
        if re.fullmatch(r"[A-Za-z0-9_-]{1,80}", vendor_id):
            return vendor_id
    if records:
        raise frappe.ValidationError("چند فروشگاه به این حساب متصل است؛ شناسهٔ فروشگاه موردنظر را وارد کنید.")
    raise frappe.ValidationError("برای این حساب فروشگاه قابل تشخیصی پیدا نشد؛ شناسهٔ فروشنده را وارد کنید.")


def get_snappfood_account_info(settings=None):
    """Read the authenticated user's and selected vendor's safe profile fields."""
    cfg = settings or _get_settings()
    token = _normalize_bearer_token(cfg.get("token"))
    vendor_id = str(cfg.get("vendor_id") or "").strip()
    if not token:
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")

    user_payload = _food_partner_account_request(
        f"{DEFAULT_VENDOR_ACCOUNT_API_BASE_URL}/vms/v2/user/vendors", token
    )
    user_record, vendor_user_refs, vendor_user_records = _food_partner_vendor_user_records(user_payload)
    if not vendor_id:
        vendor_id = _discover_snappfood_vendor_id(token, user_payload=user_payload)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", vendor_id):
        raise frappe.ValidationError("شناسه فروشنده Food Partner معتبر نیست.")

    user_attributes = _food_partner_json_api_record_attributes(user_record)
    user_name = str(user_attributes.get("name") or "").strip()
    if not user_name:
        user_name = " ".join(
            str(user_attributes.get(key) or "").strip()
            for key in ("firstName", "lastName")
            if str(user_attributes.get(key) or "").strip()
        )

    selected_vendor_record = next(
        (record for record in vendor_user_records if vendor_id in _food_partner_vendor_identity(record)),
        vendor_user_records[0] if len(vendor_user_records) == 1 else None,
    )
    selected_vendor_attributes = _food_partner_json_api_record_attributes(selected_vendor_record)
    profile_payload = _food_partner_account_request(
        f"{DEFAULT_VENDOR_ACCOUNT_API_BASE_URL}/vms/v2/vendor-registration/vendor/{vendor_id}", token
    )
    profile_record = profile_payload.get("data") if isinstance(profile_payload.get("data"), dict) else {}
    profile_attributes = _food_partner_json_api_record_attributes(profile_record)

    def first_display(*values):
        return next((display for display in (_food_partner_json_api_display(value) for value in values) if display), "")

    vendor = {
        "vendor_id": vendor_id,
        "title": first_display(profile_attributes.get("title"), selected_vendor_attributes.get("title")),
        "english_title": first_display(profile_attributes.get("englishTitle")),
        "address": first_display(profile_attributes.get("address"), selected_vendor_attributes.get("address")),
        "phone": first_display(profile_attributes.get("phoneNumber"), selected_vendor_attributes.get("customerPhone")),
        "postal_code": first_display(profile_attributes.get("postalCode")),
        "status": first_display(profile_attributes.get("status"), selected_vendor_attributes.get("status")),
        "city": first_display(selected_vendor_attributes.get("city")),
        "expedition_type": first_display(profile_attributes.get("expeditionType"), selected_vendor_attributes.get("expeditionType")),
        "account_access_active": selected_vendor_attributes.get("isActive") if isinstance(selected_vendor_attributes.get("isActive"), bool) else None,
        "has_delivery": bool(profile_attributes.get("hasVendorDelivery") or selected_vendor_attributes.get("hasVendorDelivery")),
    }
    return {
        "status": "success",
        "user": {
            "name": user_name,
            "username": str(user_attributes.get("username") or "").strip(),
            "mobile": first_display(user_attributes.get("cellphone")),
            "email": first_display(user_attributes.get("email")),
        },
        "vendor": vendor,
        "vendors_count": len(vendor_user_refs),
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
        try:
            response = requests.post(
                cfg.get("report_url") or DEFAULT_REPORT_URL,
                headers=headers,
                files=report_files,
                timeout=30,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code == 401:
                message = "توکن Food Partner برای دریافت سفارش‌ها پذیرفته نشد (HTTP 401)."
            elif status_code == 403:
                message = (
                    "دسترسی سرویس گزارش سفارش‌های Food Partner رد شد (HTTP 403). "
                    "این پاسخ به‌تنهایی نامعتبر بودن توکن را ثابت نمی‌کند؛ آدرس یا مجوز endpoint گزارش را بررسی کنید."
                )
            else:
                message = (
                    f"دریافت سفارش‌های Food Partner با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
                )
            raise frappe.ValidationError(message) from exc
        except requests.RequestException as exc:
            raise frappe.ValidationError(
                "ارتباط با سرویس گزارش سفارش‌های Food Partner برقرار نشد؛ اتصال شبکه و آدرس گزارش را بررسی کنید."
            ) from exc
        pages_fetched += 1

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise frappe.ValidationError(
                "پاسخ سرویس گزارش سفارش‌های Food Partner قابل خواندن نیست."
            ) from exc
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


_FOOD_PARTNER_LIVE_STATUS_LABELS = {
    "56": "سفارش جدید",
    "714": "در انتظار پذیرش",
    "61": "دریافت‌شده",
    "713": "بازشده",
    "42": "پذیرفته‌شده",
    "51": "درخواست تغییر ثبت شده",
    "54": "لغوشده",
    "71": "در انتظار پرداخت",
    "WAITING_FOR_CONFIRMATION": "در حال تأیید",
    "CONFIRMATION_TIMEOUT": "تأیید نیازمند تلاش دوباره",
    "EDITED": "ویرایش‌شده",
}
_FOOD_PARTNER_ACCEPTABLE_ORDER_STATUSES = {
    "56",
    "714",
    "61",
    "713",
    "NEW_ORDER",
    "SENT",
    "RECEIVED",
    "OPENED",
    "CONFIRMATION_TIMEOUT",
}
_FOOD_PARTNER_ACCEPTED_ORDER_STATUSES = {"42", "ACCEPTED"}
_FOOD_PARTNER_LIVE_ORDER_STATUSES = (
    _FOOD_PARTNER_ACCEPTABLE_ORDER_STATUSES
    | _FOOD_PARTNER_ACCEPTED_ORDER_STATUSES
    | {"61", "713", "51", "71", "WAITING_FOR_CONFIRMATION", "CONFIRMATION_TIMEOUT", "EDITED"}
)


def _food_partner_order_status_code(raw_order):
    value = (
        raw_order.get("statusCode")
        or raw_order.get("externalStatusCode")
        or raw_order.get("lastState")
        or raw_order.get("status")
        or ""
    )
    return str(value).strip().upper()


def _find_food_partner_token(payload, token_name):
    wanted = str(token_name or "").replace("_", "").lower()
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).replace("_", "").lower() == wanted and isinstance(value, str) and value.strip():
                return _normalize_bearer_token(value)
        for value in payload.values():
            found = _find_food_partner_token(value, token_name)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = _find_food_partner_token(value, token_name)
            if found:
                return found
    return ""


def _get_food_partner_order_tokens(settings=None):
    cfg = settings or _get_settings()
    access_token = _normalize_bearer_token(cfg.get("access_token"))
    if not access_token:
        raise frappe.ValidationError(
            "برای پذیرش سفارش، توکن دسترسی حساب Food Partner را در تنظیمات اتصال وارد کنید."
        )
    try:
        response = requests.get(
            "https://snappfood.ir/vms/v1/user/ordering-tokens",
            headers={
                "accept": "application/json, text/plain, */*",
                "authorization": f"Bearer {access_token}",
                "user-agent": "Mozilla/5.0",
            },
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code == 401:
            message = "توکن حساب Food Partner برای دریافت دسترسی سفارش معتبر شناخته نشد (HTTP 401)؛ آن را از مسیر رسمی به‌روزرسانی کنید."
        elif status_code == 403:
            message = (
                "دریافت دسترسی عملیات سفارش از Food Partner رد شد (HTTP 403). "
                "این پاسخ به‌تنهایی نامعتبر بودن توکن منو را ثابت نمی‌کند؛ دسترسی سفارش باید جداگانه فعال شود."
            )
        else:
            message = f"دریافت دسترسی امن سفارش با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
        raise frappe.ValidationError(message) from exc
    except (requests.RequestException, TypeError, ValueError) as exc:
        raise frappe.ValidationError("ارتباط امن با سرویس سفارش Food Partner برقرار نشد.") from exc

    ordering_token = _find_food_partner_token(payload, "orderingToken")
    vendor_token = _find_food_partner_token(payload, "vendorToken")
    if not ordering_token:
        raise frappe.ValidationError("سرویس Food Partner توکن عملیات سفارش را برنگرداند؛ اتصال را بررسی کنید.")
    if not vendor_token:
        vendor_token = _normalize_bearer_token(cfg.get("token"))
    return {"ordering_token": ordering_token, "vendor_token": vendor_token}


def test_snappfood_order_access():
    """Verify order-action credentials without reading or changing an order."""
    tokens = _get_food_partner_order_tokens()
    return {
        "status": "success",
        "order_actions_ready": bool(tokens.get("ordering_token")),
    }


def _fetch_food_partner_recent_orders(settings=None):
    cfg = settings or _get_settings()
    now = now_datetime()
    fetched = fetch_snapp_orders(
        from_datetime=now - timedelta(hours=24),
        to_datetime=now,
        page_size=min(cint(cfg.get("page_size") or DEFAULT_PAGE_SIZE), 100),
        max_pages=10,
        settings=cfg,
    )
    return cfg, fetched.get("orders") or []


def _find_food_partner_live_order(order_id, settings=None):
    order_id = str(order_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", order_id):
        raise frappe.ValidationError("شناسه سفارش Food Partner معتبر نیست.")
    cfg, rows = _fetch_food_partner_recent_orders(settings=settings)
    raw_order = next((row for row in rows if _raw_snapp_order_id(row) == order_id), None)
    if not raw_order:
        raise frappe.ValidationError("سفارش در فهرست تازهٔ Food Partner پیدا نشد؛ فهرست را تازه کنید.")
    raw_vendor_id = str(raw_order.get("vendorId") or raw_order.get("vendor_id") or "").strip()
    if raw_vendor_id and raw_vendor_id != str(cfg.get("vendor_id") or "").strip():
        raise frappe.ValidationError("این سفارش به شناسه فروشندهٔ تنظیم‌شده تعلق ندارد.")
    return cfg, raw_order


def _food_partner_live_order_preview(raw_order, cfg):
    normalized = normalize_snapp_order(raw_order, amount_multiplier=cfg.get("amount_multiplier") or 1)
    status_code = _food_partner_order_status_code(raw_order)
    expedition_type = str(raw_order.get("expeditionType") or raw_order.get("deliveryType") or "").strip().upper()
    changeable_value = raw_order.get("isMinPrepTimeChangeable")
    is_prep_changeable = changeable_value not in (False, 0, "0", "false", "False")
    min_minutes = max(1, min(cint(raw_order.get("vendorMinPreparationTime") or 5), 240))
    max_minutes = cint(raw_order.get("vendorMaxPreparationTime") or raw_order.get("vendorMaxDeliveryTime") or 120)
    if max_minutes < min_minutes:
        max_minutes = min_minutes
    items = []
    for item in normalized.get("items") or []:
        toppings = item.get("toppings") or []
        topping_names = []
        for topping in toppings if isinstance(toppings, list) else []:
            if isinstance(topping, dict):
                name = topping.get("title") or topping.get("name") or topping.get("productName")
            else:
                name = topping
            if name:
                topping_names.append(str(name).strip())
        items.append(
            {
                "title": item.get("title") or "محصول",
                "qty": flt(item.get("qty") or 0),
                "unit_price": flt(item.get("unit_price") or 0),
                "toppings": topping_names,
            }
        )

    already_ready = any(
        raw_order.get(key) is True
        for key in ("foodIsReady", "hasOrderAlreadyBeenAnnouncedReady", "food_is_ready")
    )
    return {
        "order_id": normalized["order_id"],
        "bill_number": normalized.get("bill_number") or "",
        "customer_name": normalized.get("customer_name") or FALLBACK_GUEST_NAME,
        "mobile": normalized.get("mobile") or "",
        "address": normalized.get("address") or "",
        "note": normalized.get("note") or "",
        "created_at": get_datetime_str(normalized.get("created_at")) if normalized.get("created_at") else "",
        "order_type": normalized.get("order_type") or "",
        "expedition_type": expedition_type,
        "status_code": status_code,
        "status_label": (
            "آمادهٔ ارسال"
            if already_ready
            else _FOOD_PARTNER_LIVE_STATUS_LABELS.get(status_code, normalized.get("status") or "وضعیت نامشخص")
        ),
        "final_amount": flt(normalized.get("final_amount") or 0),
        "items": items,
        "is_prep_time_changeable": is_prep_changeable,
        "min_preparation_minutes": min_minutes,
        "max_preparation_minutes": min(max_minutes, 240),
        "preparation_minutes": max(min_minutes, min(cint(raw_order.get("vendorMinPreparationTime") or 30), max_minutes)),
        "can_accept": status_code in _FOOD_PARTNER_ACCEPTABLE_ORDER_STATUSES,
        "can_mark_ready": status_code in _FOOD_PARTNER_ACCEPTED_ORDER_STATUSES and not already_ready,
    }


def get_snappfood_live_orders():
    """Read recent order states for the management screen; never stores raw payloads."""
    cfg, rows = _fetch_food_partner_recent_orders()
    orders = []
    for raw_order in rows:
        status_code = _food_partner_order_status_code(raw_order)
        if status_code not in _FOOD_PARTNER_LIVE_ORDER_STATUSES:
            continue
        try:
            orders.append(_food_partner_live_order_preview(raw_order, cfg))
        except Exception:
            # Keep one malformed report row from hiding other actionable orders.
            continue
    orders.sort(key=lambda order: order.get("created_at") or "", reverse=True)
    return {
        "status": "success",
        "fetched_count": len(rows),
        "orders": orders,
        "has_order_access_token": bool(cfg.get("access_token")),
    }


def _food_partner_accept_payload(raw_order, preparation_minutes, cfg):
    expedition_type = str(raw_order.get("expeditionType") or raw_order.get("deliveryType") or "").strip().upper()
    is_delivery = expedition_type == "DELIVERY"
    is_express = expedition_type in {"ZF_EXPRESS", "EXPRESS"} or bool(raw_order.get("onDemandExpressTripV2"))
    minutes = cint(preparation_minutes)
    min_minutes = max(1, min(cint(raw_order.get("vendorMinPreparationTime") or 1), 240))
    max_minutes = cint(raw_order.get("vendorMaxPreparationTime") or raw_order.get("vendorMaxDeliveryTime") or 240)
    max_minutes = max(min_minutes, min(max_minutes, 240))
    if minutes < min_minutes or minutes > max_minutes:
        raise frappe.ValidationError(f"زمان آماده‌سازی باید بین {min_minutes} تا {max_minutes} دقیقه باشد.")
    if raw_order.get("isMinPrepTimeChangeable") is False and minutes != min_minutes:
        raise frappe.ValidationError(f"برای این سفارش زمان قابل تغییر نیست و باید {min_minutes} دقیقه ثبت شود.")

    delivery_price = flt(raw_order.get("deliveryPrice") or raw_order.get("deliveryCost") or 0)
    packing_price = flt(raw_order.get("packingPrice") or raw_order.get("packagingCost") or 0)
    order_id = _raw_snapp_order_id(raw_order)
    if str(raw_order.get("confirmationFlowVersion") or "").lower() == "v1":
        return {
            "order_id": order_id,
            "flow_version": "v1",
            "fields": {
                "addressId": raw_order.get("addressId") or "",
                "orderId": order_id,
                "vendorId": raw_order.get("vendorId") or cfg.get("vendor_id") or "",
                "subscription": raw_order.get("subscription") or "",
                "appVersion": "3.14.1",
                "deviceType": "VTS-PWA-ELECTRON",
                "riderPickupTime": 0 if is_delivery else minutes,
                "deliveryTime": 0 if is_express else minutes,
                "deliveryPrice": delivery_price,
                "packingPrice": packing_price,
                "delta": 0,
            },
        }

    payload = {
        "orderId": order_id,
        "deliveryTime": 0 if is_express else minutes,
        "packingPrice": packing_price,
        "deliveryPrice": delivery_price,
        "riderPickupTime": 0 if is_delivery else minutes,
        "delta": 0,
    }
    if raw_order.get("subscription"):
        payload["subscription"] = raw_order.get("subscription")
    return {"order_id": order_id, "flow_version": "v2", "payload": payload}


def _food_partner_order_mutation_error(response, payload):
    return _snapp_menu_mutation_error(response, payload)


def accept_snappfood_order(order_id, preparation_minutes):
    cfg, raw_order = _find_food_partner_live_order(order_id)
    status_code = _food_partner_order_status_code(raw_order)
    if status_code not in _FOOD_PARTNER_ACCEPTABLE_ORDER_STATUSES:
        raise frappe.ValidationError("این سفارش دیگر در وضعیت قابل‌پذیرش نیست؛ فهرست سفارش‌ها را تازه کنید.")
    accept_data = _food_partner_accept_payload(raw_order, preparation_minutes, cfg)
    tokens = _get_food_partner_order_tokens(cfg)
    vendor_token = tokens.get("vendor_token") or cfg.get("token")
    if not vendor_token:
        raise frappe.ValidationError("توکن Food Partner برای بررسی سفارش تنظیم نشده است.")

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {vendor_token}",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0",
    }
    try:
        validation = requests.post(
            "https://snappfood.ir/vms/v3/order/validate-accept",
            headers=headers,
            json={"orderId": accept_data["order_id"]},
            timeout=20,
        )
        try:
            validation_payload = validation.json()
        except (TypeError, ValueError):
            validation_payload = None
        error = _food_partner_order_mutation_error(validation, validation_payload)
        if error:
            raise frappe.ValidationError(error)

        if accept_data["flow_version"] == "v1":
            fields = {
                f"context[data][{key}]": (None, str(value))
                for key, value in accept_data["fields"].items()
            }
            response = requests.post(
                "https://vmsapi.zoodfood.com/job",
                params={"job": "vms_accept_order"},
                headers={
                    "authorization": f"Bearer {tokens['ordering_token']}",
                    "x-client-version": "VTS-PWA-ELECTRON",
                    "x-correlational-id": str(uuid.uuid4()),
                    "user-agent": "Mozilla/5.0",
                },
                files=fields,
                timeout=25,
            )
        else:
            response = requests.post(
                "https://vmsapi.zoodfood.com/api/v1/vendor-orders/actions/accept",
                headers={
                    "authorization": f"Bearer {tokens['ordering_token']}",
                    "content-type": "application/json",
                    "x-device-type": "VTS-PWA-ELECTRON",
                    "x-app-version": "3.14.1",
                    "user-agent": "Mozilla/5.0",
                },
                json=accept_data["payload"],
                timeout=25,
            )
        try:
            payload = response.json()
        except (TypeError, ValueError):
            payload = None
        error = _food_partner_order_mutation_error(response, payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با سرویس پذیرش سفارش Food Partner برقرار نشد.") from exc
    return {
        "status": "success",
        "order_id": accept_data["order_id"],
        "preparation_minutes": cint(preparation_minutes),
    }


def _food_partner_response_data(payload):
    if not isinstance(payload, dict):
        return {}
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


def mark_snappfood_order_ready(order_id):
    cfg, raw_order = _find_food_partner_live_order(order_id)
    if _food_partner_order_status_code(raw_order) not in _FOOD_PARTNER_ACCEPTED_ORDER_STATUSES:
        raise frappe.ValidationError("فقط سفارش پذیرفته‌شده را می‌توان آمادهٔ ارسال اعلام کرد.")
    headers = _snapp_menu_headers(cfg)
    encoded_order_id = requests.utils.quote(str(order_id), safe="")
    status_url = f"https://snappfood.ir/vms/v1/order/{encoded_order_id}/validateIfFoodAlreadyIsReady"
    ready_url = f"https://snappfood.ir/food-partner/order/v1/{encoded_order_id}/food-is-ready"
    try:
        check_response = requests.get(status_url, headers=headers, timeout=20)
        check_response.raise_for_status()
        check_payload = check_response.json()
        check_data = _food_partner_response_data(check_payload)
        if "hasOrderAlreadyBeenAnnouncedReady" not in check_data:
            raise frappe.ValidationError("وضعیت آماده‌بودن سفارش از Food Partner دریافت نشد.")
        if check_data.get("hasOrderAlreadyBeenAnnouncedReady"):
            return {"status": "already_ready", "order_id": str(order_id)}
        response = requests.post(ready_url, headers=headers, timeout=25)
        try:
            payload = response.json()
        except (TypeError, ValueError):
            payload = None
        error = _food_partner_order_mutation_error(response, payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با سرویس آماده‌سازی سفارش Food Partner برقرار نشد.") from exc
    return {"status": "success", "order_id": str(order_id)}


def _resolve_snapp_order_window(from_date=None, to_date=None):
    """Resolve a user-facing date range to a closed local-day datetime range."""
    start_text = str(from_date or "").strip()[:10]
    end_text = str(to_date or "").strip()[:10]
    if not start_text and not end_text:
        yesterday = get_datetime(today()) - timedelta(days=1)
        start_text = end_text = yesterday.strftime("%Y-%m-%d")
    elif not start_text:
        start_text = end_text
    elif not end_text:
        end_text = start_text

    try:
        start_dt = get_datetime(f"{start_text} 00:00:00")
        end_dt = get_datetime(f"{end_text} 23:59:59")
    except (TypeError, ValueError, OverflowError) as exc:
        raise frappe.ValidationError("تاریخ شروع یا پایان سفارش معتبر نیست.") from exc

    if start_dt > end_dt:
        raise frappe.ValidationError("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
    return start_dt, end_dt


def _raw_snapp_order_id(raw_order):
    return str(
        raw_order.get("id")
        or raw_order.get("orderId")
        or raw_order.get("order_id")
        or ""
    ).strip()


def _food_partner_mapping_lookup_key(identity):
    identity = identity or {}
    for fieldname in (
        "variation_id",
        "menu_item_id",
        "external_id",
        "variation_hash_id",
        "product_id",
        "product_hash_id",
    ):
        value = str(identity.get(fieldname) or "").strip()
        if value:
            return fieldname, value
    return "", ""


def _food_partner_modifier_mapping_index():
    if not _has_field("Item", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD):
        return {}
    rows = frappe.get_all(
        "Item",
        fields=["name", "item_code", "item_name", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD],
        filters={FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD: ["!=", ""]},
        limit_page_length=0,
        ignore_permissions=True,
    )
    index = {}
    for item in rows or []:
        raw_mappings = item.get(FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD) or "[]"
        try:
            mappings = json.loads(raw_mappings) if isinstance(raw_mappings, str) else raw_mappings
        except (TypeError, ValueError):
            mappings = []
        for mapping in mappings if isinstance(mappings, list) else []:
            if not isinstance(mapping, dict):
                continue
            fieldname = str(mapping.get("lookup_field") or "").strip()
            value = str(mapping.get("lookup_value") or "").strip()
            parent_item = str(mapping.get("parent_item") or item.get("name") or "").strip()
            if not fieldname or not value or not parent_item:
                continue
            key = (fieldname, value)
            index.setdefault(key, []).append(
                {
                    **mapping,
                    "parent_item": parent_item,
                    "parent_item_code": item.get("item_code") or parent_item,
                    "parent_item_name": item.get("item_name") or parent_item,
                    "mapping_mode": str(mapping.get("mapping_mode") or "modifier").strip() or "modifier",
                }
            )
    return index


def _find_food_partner_modifier_mapping(identity, mapping_index=None):
    fieldname, value = _food_partner_mapping_lookup_key(identity)
    if not fieldname or not value:
        return None
    matches = (mapping_index if mapping_index is not None else _food_partner_modifier_mapping_index()).get(
        (fieldname, value), []
    )
    unique = {
        (
            row.get("parent_item"),
            row.get("group_name"),
            row.get("option_name"),
            row.get("mapping_mode") or "modifier",
        ): row
        for row in matches
    }
    return next(iter(unique.values())) if len(unique) == 1 else None


def _remove_food_partner_modifier_mapping(identity):
    lookup_field, lookup_value = _food_partner_mapping_lookup_key(identity)
    if not lookup_field or not lookup_value or not _has_field("Item", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD):
        return
    rows = frappe.get_all(
        "Item",
        fields=["name", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD],
        filters={FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD: ["!=", ""]},
        limit_page_length=0,
        ignore_permissions=True,
    )
    for item in rows or []:
        raw = item.get(FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD) or "[]"
        try:
            mappings = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            mappings = []
        if not isinstance(mappings, list):
            continue
        retained = [
            row for row in mappings
            if not (
                isinstance(row, dict)
                and row.get("lookup_field") == lookup_field
                and str(row.get("lookup_value") or "").strip() == lookup_value
            )
        ]
        if len(retained) != len(mappings):
            frappe.db.set_value(
                "Item",
                item.get("name"),
                FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD,
                json.dumps(retained, ensure_ascii=False),
                update_modified=False,
            )


def get_snappfood_modifier_groups(item_name=""):
    """Return the native modifier groups available on one mapped parent Item."""
    item_name = str(item_name or "").strip()
    if not item_name or not frappe.db.exists("Item", item_name):
        raise frappe.ValidationError("کالای اصلی برای انتخاب Modifier معتبر نیست.")
    if not frappe.db.exists("DocType", "Restaurant BOM Modifier"):
        return {"status": "success", "item": item_name, "groups": []}

    from restaurant import api

    item_doc = frappe.get_doc("Item", item_name)
    primary_bom = api._get_bom_doc(item_doc)
    modifier_bom = api._get_modifier_source_bom_doc(item_doc, primary_bom_doc=primary_bom)
    groups, _group_map, _title_map = api._build_modifier_groups(
        item_doc,
        primary_bom_doc=modifier_bom,
    )
    return {
        "status": "success",
        "item": item_name,
        "item_name": item_doc.get("item_name") or item_name,
        "groups": [
            {
                "name": group.get("group_name") or "",
                "title": group.get("title") or group.get("group_name") or "",
                "options": [
                    {
                        "name": option.get("name") or "",
                        "label": option.get("label") or option.get("name") or "",
                        "price_delta": flt(option.get("price_delta") or option.get("unit_rate") or 0),
                        "option_qty": flt(option.get("option_qty") or option.get("base_qty") or 1),
                        "min_qty": flt(option.get("min_qty") or 0),
                        "max_qty": flt(option.get("max_qty") or 0),
                        "qty_step": flt(option.get("qty_step") or 1),
                    }
                    for option in group.get("options") or []
                    if option.get("name")
                ],
            }
            for group in groups or []
            if group.get("group_name")
        ],
    }


def save_snappfood_modifier_mapping(
    item_name="",
    parent_item="",
    group_name="",
    option_name="",
    mapping_mode="modifier",
    product_id="",
    variation_id="",
    product_hash_id="",
    variation_hash_id="",
    menu_item_id="",
):
    """Persist a Food Partner identity as a BOM option on its native base Item."""
    parent_item = str(parent_item or "").strip()
    group_name = str(group_name or "").strip()
    option_name = str(option_name or "").strip()
    mapping_mode = str(mapping_mode or "modifier").strip().lower()
    if mapping_mode not in {"modifier", "item_modifier"}:
        mapping_mode = "modifier"
    if not parent_item or not frappe.db.exists("Item", parent_item):
        raise frappe.ValidationError("کالای اصلی Modifier معتبر نیست.")
    if not _has_field("Item", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD):
        raise frappe.ValidationError("ساختار نگاشت Modifier آماده نیست؛ بروزرسانی Restaurant لازم است.")

    identity = {
        "menu_item_id": str(menu_item_id or "").strip(),
        "variation_id": str(variation_id or "").strip(),
        "product_id": str(product_id or "").strip(),
        "product_hash_id": str(product_hash_id or "").strip(),
        "variation_hash_id": str(variation_hash_id or "").strip(),
    }
    lookup_field, lookup_value = _food_partner_mapping_lookup_key(identity)
    if not lookup_field or not lookup_value:
        raise frappe.ValidationError("شناسهٔ این گزینه در پاسخ Food Partner موجود نیست.")

    context = get_snappfood_modifier_groups(parent_item)
    selected_group = next((row for row in context.get("groups") or [] if row.get("name") == group_name), None)
    selected_option = next(
        (row for row in (selected_group or {}).get("options") or [] if row.get("name") == option_name),
        None,
    )
    if not selected_group or not selected_option:
        raise frappe.ValidationError("گروه یا گزینهٔ انتخاب‌شده روی فرمول فعال این کالا موجود نیست.")

    all_items = frappe.get_all(
        "Item",
        fields=["name", FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD],
        filters={FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD: ["!=", ""]},
        limit_page_length=0,
        ignore_permissions=True,
    )
    mappings_by_item = {}
    for row in all_items or []:
        raw = row.get(FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD) or "[]"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, ValueError):
            parsed = []
        mappings_by_item[row.get("name")] = [entry for entry in parsed if isinstance(entry, dict)] if isinstance(parsed, list) else []

    for name, mappings in mappings_by_item.items():
        retained = [
            row for row in mappings
            if not (
                row.get("lookup_field") == lookup_field
                and str(row.get("lookup_value") or "").strip() == lookup_value
            )
        ]
        if len(retained) != len(mappings):
            frappe.db.set_value(
                "Item",
                name,
                FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD,
                json.dumps(retained, ensure_ascii=False),
                update_modified=False,
            )

    target_mappings = mappings_by_item.get(parent_item, [])
    target_mappings = [
        row for row in target_mappings
        if not (
            row.get("lookup_field") == lookup_field
            and str(row.get("lookup_value") or "").strip() == lookup_value
        )
    ]
    target_mappings.append(
        {
            "lookup_field": lookup_field,
            "lookup_value": lookup_value,
            "identity": identity,
            "parent_item": parent_item,
            "mapping_mode": mapping_mode,
            "group_name": group_name,
            "group_title": selected_group.get("title") or group_name,
            "option_name": option_name,
            "option_label": selected_option.get("label") or option_name,
            "option_qty": flt(selected_option.get("option_qty") or 1),
            "min_qty": flt(selected_option.get("min_qty") or 0),
            "max_qty": flt(selected_option.get("max_qty") or 0),
            "qty_step": flt(selected_option.get("qty_step") or 1),
        }
    )
    frappe.db.set_value(
        "Item",
        parent_item,
        FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD,
        json.dumps(target_mappings, ensure_ascii=False),
        update_modified=True,
    )
    frappe.db.commit()
    return {
        "status": "success",
        "parent_item": parent_item,
        "parent_item_name": context.get("item_name") or parent_item,
        "mapping_mode": mapping_mode,
        "group_name": group_name,
        "group_title": selected_group.get("title") or group_name,
        "option_name": option_name,
        "option_label": selected_option.get("label") or option_name,
    }


def _build_snapp_order_preview(
    order_payload,
    existing_order="",
    existing_invoice="",
    local_items=None,
    modifier_mapping_index=None,
):
    """Return a safe, read-only summary suitable for selecting an import."""
    created_at = order_payload.get("created_at")
    if created_at:
        try:
            created_at = get_datetime_str(created_at)
        except (TypeError, ValueError):
            created_at = str(created_at)
    item_rows = order_payload.get("items") or []
    preview_items = []
    for row in item_rows:
        mapping_identity = {
            "external_id": str(row.get("menu_item_id") or "").strip(),
            "menu_item_id": str(row.get("menu_item_id") or "").strip(),
            "product_id": str(row.get("product_id") or "").strip(),
            "variation_id": str(row.get("variation_id") or "").strip(),
            "product_hash_id": str(row.get("product_hash_id") or "").strip(),
            "variation_hash_id": str(row.get("variation_hash_id") or "").strip(),
        }
        mapped_modifier = _find_food_partner_modifier_mapping(mapping_identity, modifier_mapping_index)
        is_item_modifier_mapping = bool(
            mapped_modifier and mapped_modifier.get("mapping_mode") == "item_modifier"
        )
        mapped_item = (
            {
                "name": mapped_modifier.get("parent_item") or "",
                "item_code": mapped_modifier.get("parent_item_code") or mapped_modifier.get("parent_item") or "",
                "item_name": mapped_modifier.get("parent_item_name") or mapped_modifier.get("parent_item") or "",
            }
            if is_item_modifier_mapping
            else None if mapped_modifier else _find_mapped_local_item(mapping_identity, local_items or [])
        )
        preview_items.append(
            {
                "title": str(row.get("title") or "Snapp Item").strip(),
                "qty": flt(row.get("qty") or 0),
                "unit_price": flt(row.get("unit_price") or 0),
                **mapping_identity,
                "mapped_item": (
                    {
                        "name": mapped_item.get("name") or "",
                        "item_code": mapped_item.get("item_code") or "",
                        "item_name": mapped_item.get("item_name") or mapped_item.get("name") or "",
                    }
                    if mapped_item
                    else None
                ),
                "mapped_modifier": (
                    {
                        "parent_item": mapped_modifier.get("parent_item") or "",
                        "parent_item_code": mapped_modifier.get("parent_item_code") or mapped_modifier.get("parent_item") or "",
                        "parent_item_name": mapped_modifier.get("parent_item_name") or mapped_modifier.get("parent_item") or "",
                        "group_name": mapped_modifier.get("group_name") or "",
                        "group_title": mapped_modifier.get("group_title") or mapped_modifier.get("group_name") or "",
                        "option_name": mapped_modifier.get("option_name") or "",
                        "option_label": mapped_modifier.get("option_label") or mapped_modifier.get("option_name") or "",
                        "mapping_mode": mapped_modifier.get("mapping_mode") or "modifier",
                    }
                    if mapped_modifier
                    else None
                ),
            }
        )
    return {
        "order_id": str(order_payload.get("order_id") or "").strip(),
        "bill_number": str(order_payload.get("bill_number") or "").strip(),
        "created_at": created_at or "",
        "customer_name": str(order_payload.get("customer_name") or FALLBACK_GUEST_NAME).strip(),
        "mobile": str(order_payload.get("mobile") or "").strip(),
        "external_customer_id": str(order_payload.get("external_customer_id") or "").strip(),
        "status": str(order_payload.get("status") or "").strip(),
        "order_type": str(order_payload.get("order_type") or "").strip(),
        "final_amount": flt(order_payload.get("final_amount") or 0),
        "items_count": len(item_rows),
        "items": preview_items,
        "already_imported": bool(existing_order),
        "sales_order": existing_order or "",
        "sales_invoice": existing_invoice or "",
    }


def _select_snapp_orders_for_import(raw_orders, order_ids, max_import=3):
    requested = []
    for value in order_ids or []:
        order_id = str(value or "").strip()
        if order_id and order_id not in requested:
            requested.append(order_id)
    limit = max(1, min(cint(max_import or 3), 3))
    requested_set = set(requested)
    available = set()
    selected = []
    for raw_order in raw_orders or []:
        order_id = _raw_snapp_order_id(raw_order)
        if order_id:
            available.add(order_id)
        if order_id in requested_set and len(selected) < limit:
            selected.append(raw_order)
    missing = [order_id for order_id in requested if order_id not in available]
    return selected, missing


def preview_snapp_orders(from_date=None, to_date=None, settings=None):
    """Fetch a date range without writing orders, invoices, customers or items."""
    cfg = settings if settings is not None else _get_settings()
    start_dt, end_dt = _resolve_snapp_order_window(from_date, to_date)
    fetched = fetch_snapp_orders(
        from_datetime=start_dt,
        to_datetime=end_dt,
        page_size=cfg.get("page_size") or DEFAULT_PAGE_SIZE,
        max_pages=MAX_PAGES,
        settings=cfg,
    )
    previews = []
    errors = []
    local_items = _get_local_item_rows(limit_page_length=5000, mapped_only=True)
    modifier_mapping_index = _food_partner_modifier_mapping_index()
    for raw_order in fetched.get("orders") or []:
        try:
            normalized = normalize_snapp_order(
                raw_order,
                amount_multiplier=cfg.get("amount_multiplier") or 1,
            )
            existing_order = ""
            existing_invoice = ""
            if _has_column("Sales Order", "restaurant_external_order_id"):
                existing_order = frappe.db.get_value(
                    "Sales Order",
                    {"restaurant_external_order_id": normalized["order_id"]},
                    "name",
                ) or ""
            if _has_column("Sales Invoice", "restaurant_external_order_id"):
                existing_invoice = frappe.db.get_value(
                    "Sales Invoice",
                    {"restaurant_external_order_id": normalized["order_id"]},
                    "name",
                ) or ""
            previews.append(
                _build_snapp_order_preview(
                    normalized,
                    existing_order,
                    existing_invoice,
                    local_items=local_items,
                    modifier_mapping_index=modifier_mapping_index,
                )
            )
        except Exception:
            errors.append({"order_id": _raw_snapp_order_id(raw_order), "error": frappe.get_traceback(with_context=False)})
    return {
        "status": "success",
        "from_date": start_dt.strftime("%Y-%m-%d"),
        "to_date": end_dt.strftime("%Y-%m-%d"),
        "fetched_count": cint(fetched.get("orders_count") or 0),
        "pages_fetched": cint(fetched.get("pages_fetched") or 0),
        "orders": previews,
        "errors": errors,
    }


def import_snapp_orders_for_window(from_date=None, to_date=None, order_ids=None, max_import=3, settings=None):
    """Import only selected orders from a bounded date range."""
    requested = []
    for value in order_ids or []:
        order_id = str(value or "").strip()
        if order_id and order_id not in requested:
            requested.append(order_id)
    if not requested:
        raise frappe.ValidationError("حداقل یک سفارش برای واردکردن انتخاب کنید.")
    if len(requested) > 3 or cint(max_import or 3) > 3:
        raise frappe.ValidationError("برای واردکردن تستی حداکثر ۳ سفارش را انتخاب کنید.")
    start_dt, end_dt = _resolve_snapp_order_window(from_date, to_date)
    return sync_snapp_orders(
        trigger="manual_selected",
        from_datetime=start_dt,
        to_datetime=end_dt,
        only_new=1,
        selected_order_ids=requested,
        max_import=max_import,
        settings=settings,
    )


def _food_partner_field_value(record, fieldname):
    """Read a current Food Partner menu field's approved value."""
    fields = record.get("fields") if isinstance(record, dict) else None
    value = fields.get(fieldname) if isinstance(fields, dict) else None
    if isinstance(value, dict):
        if value.get("value") is not None:
            return value.get("value")
        return value.get("pendingValue")
    return value


def _food_partner_boolean(value):
    """Return a boolean for explicit Food Partner status values, otherwise None."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"1", "true", "yes", "active", "enabled", "available"}:
        return True
    if normalized in {"0", "false", "no", "in_active", "inactive", "disabled", "unavailable"}:
        return False
    return None


def _food_partner_variation_active(record):
    explicit = _food_partner_field_value(record, "active")
    if explicit is None:
        explicit = _food_partner_field_value(record, "isActive")
    parsed = _food_partner_boolean(explicit)
    if parsed is not None:
        return parsed
    return _food_partner_boolean(record.get("status") if isinstance(record, dict) else None)


def _extract_current_food_partner_menu_entries(payload):
    """Normalize the current category -> product -> variation menu response."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, list) or not any(
        isinstance(category, dict)
        and str(category.get("type") or "").strip().lower() == "category"
        for category in data
    ):
        return None

    entries = []
    for category in data:
        if not isinstance(category, dict) or str(category.get("type") or "").strip().lower() != "category":
            continue
        category_id = str(category.get("id") or "").strip()
        category_title = str(category.get("title") or "").strip()
        for product in category.get("products") or []:
            if not isinstance(product, dict):
                continue
            variations = product.get("variations")
            variations = variations if isinstance(variations, list) else []
            product_id = str(product.get("id") or "").strip()
            product_hash_id = str(product.get("hashId") or "").strip()
            product_title = str(_food_partner_field_value(product, "title") or "").strip()
            product_description = _food_partner_field_value(product, "description")
            if variations:
                variants = [(variation, True) for variation in variations if isinstance(variation, dict)]
            else:
                variants = [(product, False)]

            for variation, is_variation in variants:
                variation_id = str(variation.get("id") or "").strip() if is_variation else ""
                variation_hash_id = str(variation.get("hashId") or "").strip() if is_variation else ""
                entries.append(
                    {
                        "id": variation_id or product_id,
                        "productId": product_id,
                        "variationId": variation_id,
                        "productHashId": product_hash_id,
                        "variationHashId": variation_hash_id,
                        "productTitle": product_title,
                        "variationTitle": str(_food_partner_field_value(variation, "title") or "").strip()
                        if is_variation
                        else "",
                        "statusId": variation_id or product_id,
                        "title": _food_partner_field_value(variation, "title")
                        or _food_partner_field_value(product, "title")
                        or "",
                        "price": _food_partner_field_value(variation, "price")
                        if _food_partner_field_value(variation, "price") is not None
                        else (_food_partner_field_value(product, "price") or 0),
                        "status": variation.get("status") or product.get("status") or "",
                        # Food Partner stores the description on the product, even
                        # when the visible menu row is one of its variations.
                        "description": product_description
                        if product_description is not None
                        else _food_partner_field_value(variation, "description"),
                        "active": _food_partner_variation_active(variation if is_variation else product),
                        "disabledUntil": variation.get("disabledUntil")
                        or variation.get("disabled_until")
                        or product.get("disabledUntil")
                        or product.get("disabled_until"),
                        "_category_id": category_id,
                        "_category_title": category_title,
                        "_food_partner_menu_v2": 1,
                    }
                )
    return entries


def _extract_menu_entries(payload):
    """Flatten Food Partner categories into product/variation rows.

    The menu response contains category containers alongside product and
    variation objects.  Category ``id``/``title`` pairs must not become
    mappable Items, but their title is useful context for each child row.
    """
    current_entries = _extract_current_food_partner_menu_entries(payload)
    if current_entries is not None:
        return current_entries

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
        category_identity_matches_id_product = bool(
            explicit_product_id
            and value.get("id") not in (None, "")
            and str(explicit_product_id) == str(value.get("id"))
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
                or category_identity_matches_id_product
                or (
                    generic_title
                    and not product_title
                    and not variation_title
                    and not has_variation_children
                    and (
                        has_category_children
                        or normalize_key(parent_key) in category_parent_keys
                    )
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


def _extract_menu_categories(payload):
    """Extract Food Partner menu groups without treating products as groups."""
    categories = []
    seen = set()
    category_parent_keys = {
        "categories",
        "menucategories",
        "category",
        "menucategory",
        "subcategories",
        "groups",
        "data",
        "children",
    }
    product_marker_keys = {
        "productid",
        "variationid",
        "menuitemid",
        "producttitle",
        "productname",
        "variationtitle",
        "variationname",
        "price",
    }

    def normalize_key(key):
        return re.sub(r"[^a-z0-9]", "", str(key or "").lower())

    def first_value(value, keys):
        wanted = {normalize_key(key) for key in keys}
        for raw_key, candidate in value.items():
            if normalize_key(raw_key) in wanted and candidate not in (None, "", []):
                return candidate
        return ""

    def visit(value, parent_key=""):
        if isinstance(value, list):
            for child in value:
                visit(child, parent_key)
            return
        if not isinstance(value, dict):
            return

        category_id = first_value(
            value,
            ("categoryId", "category_id", "menuCategoryId", "menu_category_id", "id"),
        )
        title = first_value(
            value,
            ("categoryTitle", "category_title", "categoryName", "menuCategoryName", "title", "name"),
        )
        normalized_keys = {normalize_key(key) for key in value}
        has_product_markers = bool(normalized_keys.intersection(product_marker_keys))
        has_category_hint = bool(
            normalized_keys.intersection(
                {"categorytitle", "categoryname", "menucategoryname", "categoryid", "menucategoryid"}
            )
            or normalize_key(parent_key) in category_parent_keys
        )
        if category_id and title and (not has_product_markers or has_category_hint):
            category_id = str(category_id).strip()
            title = str(title).strip()
            if category_id and title and category_id not in seen:
                seen.add(category_id)
                categories.append(
                    {
                        "external_id": category_id,
                        "category_id": category_id,
                        "parent_id": str(
                            first_value(value, ("parentId", "parent_id", "parentCategoryId", "parent_category_id"))
                            or ""
                        ).strip(),
                        "title": title,
                    }
                )

        for raw_key, child in value.items():
            if isinstance(child, (dict, list)):
                visit(child, raw_key)

    visit(payload)
    return categories


def fetch_snapp_menu_categories(settings=None):
    cfg = settings or _get_settings()
    if not cfg.get("token"):
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")
    if not cfg.get("vendor_id"):
        raise frappe.ValidationError("شناسه فروشنده Food Partner تنظیم نشده است.")

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {cfg['token']}",
        "backoffice-authorization": "true",
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
            f"{cfg.get('menu_api_base_url') or DEFAULT_MENU_API_BASE_URL}/vendor-menu/v1/vendor/{cfg['vendor_id']}/menu-category",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        if status_code in (401, 403):
            raise frappe.ValidationError(
                "توکن Food Partner معتبر نیست یا دسترسی گروه‌های کالا رد شد."
            ) from exc
        raise frappe.ValidationError(
            f"دریافت گروه‌های کالای Food Partner با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
        ) from exc
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با API گروه‌های کالای Food Partner برقرار نشد.") from exc
    except (TypeError, ValueError) as exc:
        raise frappe.ValidationError("پاسخ API گروه‌های کالای Food Partner قابل خواندن نیست.") from exc

    items = _extract_menu_categories(payload)
    return {"status": "success", "count": len(items), "items": items}


def _normalize_mapping_text(value):
    text = str(value or "").strip().lower()
    replacements = {
        "ي": "ی",
        "ى": "ی",
        "ك": "ک",
        "ۀ": "ه",
        "ة": "ه",
        "ـ": "",
        "\u200c": "",
        "\u200d": "",
        "\u200e": "",
        "\u200f": "",
        "\ufeff": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"[\s\-_/]+", "", text)


def _match_local_item_by_title(title, local_items):
    """Return one unambiguous local Item matching a Food Partner title.

    Order payloads can contain invisible Persian direction/joiner characters or
    Arabic variants of ی/ک, so a database equality query is not sufficient.
    This helper intentionally accepts only one normalized exact match; it
    never guesses between duplicate local products.
    """
    needle = _normalize_mapping_text(title)
    if not needle:
        return None

    matches = [
        item
        for item in local_items or []
        if _normalize_mapping_text(item.get("item_name")) == needle
    ]
    return matches[0] if len(matches) == 1 else None


def fetch_snapp_menu(settings=None):
    cfg = settings or _get_settings()
    if not cfg.get("token"):
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")
    if not cfg.get("vendor_id"):
        raise frappe.ValidationError("شناسه فروشنده Food Partner تنظیم نشده است.")

    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {cfg['token']}",
        "backoffice-authorization": "true",
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
            or ("price" in entry and fallback_id and not entry.get("_food_partner_menu_v2"))
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
                "status_id": str(
                    entry.get("statusId")
                    or entry.get("status_id")
                    or variation_id
                    or product_id
                    or ""
                ).strip(),
                "product_hash_id": str(entry.get("productHashId") or entry.get("product_hash_id") or "").strip(),
                "variation_hash_id": str(entry.get("variationHashId") or entry.get("variation_hash_id") or "").strip(),
                "product_title": str(
                    entry.get("productTitle")
                    or entry.get("product_title")
                    or entry.get("productName")
                    or entry.get("product_name")
                    or ""
                ).strip(),
                "variation_title": str(
                    entry.get("variationTitle")
                    or entry.get("variation_title")
                    or entry.get("variationName")
                    or entry.get("variation_name")
                    or ""
                ).strip(),
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
                "description": str(entry.get("description") or "").strip(),
                "active": _food_partner_variation_active(entry),
                "disabled_until": entry.get("disabledUntil") or entry.get("disabled_until") or "",
            }
        )
    if _has_field("Restaurant Web Settings", "snapp_last_menu_sync_at"):
        _set_single_if_exists("Restaurant Web Settings", "snapp_last_menu_sync_at", get_datetime_str(now_datetime()))
    frappe.db.commit()
    return {"status": "success", "count": len(rows), "items": rows}


def _require_snapp_menu_settings(settings=None):
    cfg = settings or _get_settings()
    if not cfg.get("token"):
        raise frappe.ValidationError("توکن Food Partner تنظیم نشده است.")
    vendor_id = str(cfg.get("vendor_id") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", vendor_id):
        raise frappe.ValidationError("شناسه فروشنده Food Partner معتبر نیست.")
    cfg["vendor_id"] = vendor_id
    return cfg


def _snapp_menu_headers(cfg):
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
    return headers


def _snapp_partner_web_headers(cfg):
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
    return headers


def _snapp_menu_mutation_error(response, payload):
    status_code = getattr(response, "status_code", None)
    if status_code in (401, 403):
        return "توکن Food Partner معتبر نیست یا دسترسی تغییر منو رد شد."
    if not isinstance(payload, dict):
        return None if getattr(response, "ok", False) else f"درخواست تغییر منو با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."

    candidates = [payload.get("message"), payload.get("code"), payload.get("status")]
    nested_details = []
    pending = [payload.get("error"), payload.get("errors"), payload.get("reason"), payload.get("data")]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            details = (value.get("message"), value.get("code"), value.get("reason"))
            candidates.extend(details)
            nested_details.extend(item for item in details if item not in (None, ""))
            pending.extend(value.get(key) for key in ("error", "errors", "data", "details") if key in value)
        elif isinstance(value, list):
            pending.extend(value)
        elif value not in (None, ""):
            candidates.append(value)
    for candidate in candidates:
        if str(candidate or "").strip().upper() == "REJECTED_BY_MAX_PRICE":
            return "اسنپ‌فود این تغییر را به‌دلیل محدودیت قیمت رد کرد؛ قیمت این گزینه را در پنل بررسی کنید."
    nested_data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    business_errors = payload.get("errors") or nested_data.get("errors")
    if (
        not getattr(response, "ok", False)
        or payload.get("success") is False
        or payload.get("status") is False
        or nested_data.get("status") is False
        or bool(business_errors)
        or str(payload.get("status") or "").strip().lower() in {"false", "error", "failed", "rejected"}
    ):
        detail = next(
            (
                str(value).strip()
                for value in nested_details
                if str(value).strip().lower() not in {"unprocessable entity", "bad request"}
            ),
            "",
        )
        if not detail:
            detail = next((str(value).strip() for value in candidates if value not in (None, "")), "")
        return detail or f"درخواست تغییر منو با خطای HTTP {status_code or 'نامشخص'} روبه‌رو شد."
    return None


def get_snappfood_menu_products():
    """Fetch only menu rows for the Food Partner management view."""
    return fetch_snapp_menu()


def _food_partner_decimal(value, label):
    text = str(value or "").strip()
    digit_map = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    text = text.translate(digit_map).replace("٬", "").replace(",", "").replace(" ", "")
    try:
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        raise frappe.ValidationError(f"{label} معتبر نیست.")
    if not amount.is_finite() or amount < 1000 or amount > 999999999:
        raise frappe.ValidationError(f"{label} باید بین ۱٬۰۰۰ و ۹۹۹٬۹۹۹٬۹۹۹ تومان باشد.")
    return format(amount.normalize(), "f")


def _food_partner_variation_patch(variation_id, fields, settings=None):
    cfg = _require_snapp_menu_settings(settings=settings)
    variation_id = str(variation_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", variation_id):
        raise frappe.ValidationError("شناسه گزینهٔ Food Partner معتبر نیست.")
    if not isinstance(fields, dict) or not fields or set(fields) - {"title", "description", "price"}:
        raise frappe.ValidationError("فیلدهای ویرایش گزینهٔ Food Partner معتبر نیستند.")

    payload = {}
    if "title" in fields:
        title = str(fields.get("title") or "").strip()
        if not title or len(title) > 64:
            raise frappe.ValidationError("عنوان محصول یا گزینه باید بین ۱ تا ۶۴ نویسه باشد.")
        payload["title"] = title
    if "description" in fields:
        description = str(fields.get("description") or "")
        if len(description) > 256:
            raise frappe.ValidationError("توضیحات حداکثر می‌تواند ۲۵۶ نویسه باشد.")
        payload["description"] = description
    if "price" in fields:
        payload["price"] = _food_partner_decimal(fields.get("price"), "قیمت محصول")

    url = (
        f"{cfg.get('menu_api_base_url') or DEFAULT_MENU_API_BASE_URL}"
        f"/vendor-menu/v1/vendor/product/product-variation/{variation_id}"
    )
    try:
        response = requests.patch(url, headers=_snapp_menu_headers(cfg), json=payload, timeout=30)
        try:
            response_payload = response.json()
        except (TypeError, ValueError):
            response_payload = None
        error = _snapp_menu_mutation_error(response, response_payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با API ویرایش Food Partner برقرار نشد.") from exc
    return {"status": "success", "variation_id": variation_id, "updated_fields": sorted(payload)}


def _food_partner_product_update_fields(fields):
    if not isinstance(fields, dict) or not fields:
        raise frappe.ValidationError("برای ویرایش محصول، حداقل یک تغییر معتبر وارد کنید.")
    if set(fields) - {"title", "description", "price", "variations"}:
        raise frappe.ValidationError("یکی از فیلدهای ویرایش محصول پشتیبانی نمی‌شود.")

    product_fields = {}
    if "title" in fields:
        title = str(fields.get("title") or "").strip()
        if not title or len(title) > 64:
            raise frappe.ValidationError("نام محصول باید بین ۱ تا ۶۴ نویسه باشد.")
        product_fields["title"] = title
    if "description" in fields:
        description = str(fields.get("description") or "")
        if len(description) > 256:
            raise frappe.ValidationError("توضیحات حداکثر می‌تواند ۲۵۶ نویسه باشد.")
        product_fields["description"] = description
    if "price" in fields:
        product_fields["price"] = _food_partner_decimal(fields.get("price"), "قیمت محصول")

    variation_patches = []
    if "variations" in fields:
        variations = fields.get("variations")
        if not isinstance(variations, list) or not variations or len(variations) > 30:
            raise frappe.ValidationError("فهرست گزینه‌های محصول معتبر نیست.")
        for variation in variations:
            if not isinstance(variation, dict) or set(variation) - {"variation_id", "title", "price"}:
                raise frappe.ValidationError("اطلاعات یکی از گزینه‌های محصول معتبر نیست.")
            variation_id = str(variation.get("variation_id") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", variation_id):
                raise frappe.ValidationError("شناسهٔ یکی از گزینه‌های Food Partner معتبر نیست.")
            patch = {}
            if "title" in variation:
                title = str(variation.get("title") or "").strip()
                if not title or len(title) > 64:
                    raise frappe.ValidationError("عنوان گزینه باید بین ۱ تا ۶۴ نویسه باشد.")
                patch["title"] = title
            if "price" in variation:
                patch["price"] = _food_partner_decimal(variation.get("price"), "قیمت گزینه")
            if not patch:
                raise frappe.ValidationError("برای هر گزینه حداقل عنوان یا قیمت جدید لازم است.")
            variation_patches.append((variation_id, patch))
    if not product_fields and not variation_patches:
        raise frappe.ValidationError("برای ویرایش محصول، حداقل یک تغییر معتبر وارد کنید.")
    return product_fields, variation_patches


def update_snappfood_product(product_id, fields):
    """Patch the parent product fields and changed variations using Partner APIs."""
    cfg = _require_snapp_menu_settings()
    product_id = str(product_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", product_id):
        raise frappe.ValidationError("شناسه محصول Food Partner معتبر نیست.")
    product_fields, variation_patches = _food_partner_product_update_fields(fields)

    updated_fields = []
    updated_variation_ids = []
    try:
        if product_fields:
            result = _food_partner_variation_patch(product_id, product_fields, settings=cfg)
            updated_fields.extend(result["updated_fields"])
        for variation_id, variation_fields in variation_patches:
            _food_partner_variation_patch(variation_id, variation_fields, settings=cfg)
            updated_variation_ids.append(variation_id)
    except frappe.ValidationError as exc:
        if updated_fields or updated_variation_ids:
            raise frappe.ValidationError(
                "بخشی از تغییرات محصول ثبت شد؛ منو را تازه کنید و نتیجه را بررسی کنید. " + str(exc)
            ) from exc
        raise

    return {
        "status": "success",
        "product_id": product_id,
        "updated_fields": updated_fields,
        "updated_variation_ids": updated_variation_ids,
    }


def update_snappfood_product_description(product_id, description):
    result = update_snappfood_product(product_id, {"description": str(description or "")})
    return {**result, "description": str(description or "")}


def create_snappfood_product(payload):
    """Create a product through the Partner product-review form contract."""
    cfg = _require_snapp_menu_settings()
    if not isinstance(payload, dict):
        raise frappe.ValidationError("اطلاعات محصول جدید معتبر نیست.")

    allowed_fields = {
        "title",
        "description",
        "category_id",
        "category_title",
        "price",
        "variations",
        "image_data_url",
    }
    if set(payload) - allowed_fields:
        raise frappe.ValidationError("یکی از فیلدهای محصول جدید پشتیبانی نمی‌شود.")

    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    category_id = str(payload.get("category_id") or "").strip()
    category_title = str(payload.get("category_title") or "").strip()
    if not title or len(title) > 64:
        raise frappe.ValidationError("نام محصول باید بین ۱ تا ۶۴ نویسه باشد.")
    if not description or len(description) > 256:
        raise frappe.ValidationError("توضیحات واقعی و دقیق محصول را وارد کنید؛ متن حداکثر ۲۵۶ نویسه باشد.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", category_id):
        raise frappe.ValidationError("دسته‌بندی محصول را از فهرست Food Partner انتخاب کنید.")
    if not category_title or len(category_title) > 64:
        raise frappe.ValidationError("عنوان دسته‌بندی محصول معتبر نیست.")

    form_fields = {
        "productTitle": (None, title),
        "description": (None, description),
        "menuCategoryId": (None, category_id),
        "menuCategoryTitle": (None, category_title),
        "suggestionDetails[productTitle]": (None, "none"),
        "suggestionDetails[description]": (None, "none"),
        "suggestionDetails[categoryTitle]": (None, "none"),
    }
    image_data_url = str(payload.get("image_data_url") or "").strip()
    if image_data_url:
        match = re.fullmatch(r"data:image/jpeg;base64,([A-Za-z0-9+/]+={0,2})", image_data_url)
        if not match or len(image_data_url) > 3_000_000:
            raise frappe.ValidationError("تصویر محصول معتبر نیست یا حجم آن بیش از اندازه است.")
        try:
            image_bytes = base64.b64decode(match.group(1), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise frappe.ValidationError("تصویر محصول قابل خواندن نیست.") from exc
        if not image_bytes or len(image_bytes) > 2_000_000:
            raise frappe.ValidationError("حجم تصویر محصول باید حداکثر ۲ مگابایت باشد.")
        form_fields["images[0]"] = ("uploadedImage.jpg", image_bytes, "image/jpeg")
    variations = payload.get("variations")
    if variations:
        if not isinstance(variations, list) or len(variations) > 30:
            raise frappe.ValidationError("فهرست گزینه‌های محصول معتبر نیست.")
        for index, variation in enumerate(variations):
            if not isinstance(variation, dict) or set(variation) - {"title", "price"}:
                raise frappe.ValidationError("اطلاعات یکی از گزینه‌های محصول معتبر نیست.")
            variation_title = str(variation.get("title") or "").strip()
            if not variation_title or len(variation_title) > 64:
                raise frappe.ValidationError("عنوان هر گزینه باید بین ۱ تا ۶۴ نویسه باشد.")
            prefix = f"variations[{index}]"
            form_fields[f"{prefix}[title]"] = (None, variation_title)
            form_fields[f"{prefix}[price]"] = (None, _food_partner_decimal(variation.get("price"), "قیمت گزینه"))
            form_fields[f"{prefix}[suggestionDetails][variationTitle]"] = (None, "none")
    else:
        form_fields["price"] = (None, _food_partner_decimal(payload.get("price"), "قیمت محصول"))

    url = f"{DEFAULT_PARTNER_WEB_API_BASE_URL}/vms/v2/products/{cfg['vendor_id']}/create"
    try:
        headers = _snapp_partner_web_headers(cfg)
        response = requests.post(url, headers=headers, files=form_fields, timeout=30)
        try:
            response_payload = response.json()
        except (TypeError, ValueError):
            response_payload = None
        error = _snapp_menu_mutation_error(response, response_payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با API افزودن محصول Food Partner برقرار نشد.") from exc
    return {"status": "success", "title": title, "category_id": category_id}


def update_snappfood_variation_description(variation_id, description):
    cfg = _require_snapp_menu_settings()
    variation_id = str(variation_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", variation_id):
        raise frappe.ValidationError("شناسه گزینهٔ Food Partner معتبر نیست.")
    description = str(description or "")
    if len(description) > 256:
        raise frappe.ValidationError("توضیحات حداکثر می‌تواند ۲۵۶ نویسه باشد.")

    url = (
        f"{cfg.get('menu_api_base_url') or DEFAULT_MENU_API_BASE_URL}"
        f"/vendor-menu/v1/vendor/product/product-variation/{variation_id}"
    )
    try:
        response = requests.patch(url, headers=_snapp_menu_headers(cfg), json={"description": description}, timeout=30)
        try:
            payload = response.json()
        except (TypeError, ValueError):
            payload = None
        error = _snapp_menu_mutation_error(response, payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با API توضیحات Food Partner برقرار نشد.") from exc
    return {"status": "success", "variation_id": variation_id, "description": description}


def set_snappfood_menu_item_status(item_id, active):
    cfg = _require_snapp_menu_settings()
    item_id = str(item_id or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", item_id):
        raise frappe.ValidationError("شناسه گزینهٔ Food Partner معتبر نیست.")
    active_value = _food_partner_boolean(active)
    if active_value is None:
        raise frappe.ValidationError("وضعیت جدید گزینهٔ Food Partner معتبر نیست.")

    url = (
        f"{cfg.get('menu_api_base_url') or DEFAULT_MENU_API_BASE_URL}"
        f"/vendor-menu/v4/vendors/{cfg['vendor_id']}/variations/status/bulk"
    )
    payload = {
        "ids": [item_id],
        "status": "ACTIVE" if active_value else "IN_ACTIVE",
        "disable_until_next_shift": False,
    }
    try:
        response = requests.post(url, headers=_snapp_menu_headers(cfg), json=payload, timeout=30)
        try:
            response_payload = response.json()
        except (TypeError, ValueError):
            response_payload = None
        error = _snapp_menu_mutation_error(response, response_payload)
        if error:
            raise frappe.ValidationError(error)
    except requests.RequestException as exc:
        raise frappe.ValidationError("ارتباط با API وضعیت منوی Food Partner برقرار نشد.") from exc
    return {"status": "success", "item_id": item_id, "active": active_value}


def set_snappfood_variation_status(variation_id, active):
    """Backward-compatible variation status facade."""
    result = set_snappfood_menu_item_status(variation_id, active)
    return {
        "status": result["status"],
        "variation_id": str(variation_id or "").strip(),
        "active": result["active"],
    }


def _local_item_fields():
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
    return fields


def _get_local_item_rows(search="", limit_page_length=5000, mapped_only=False):
    fields = _local_item_fields()
    filters = {"disabled": 0}
    mapping_fields = [
        fieldname
        for fieldname in (
            "restaurant_external_menu_item_id",
            "restaurant_external_product_id",
            "restaurant_external_variation_id",
            "restaurant_external_product_hash_id",
            "restaurant_external_variation_hash_id",
        )
        if _has_column("Item", fieldname)
    ]
    or_filters = [[fieldname, "!=", ""] for fieldname in mapping_fields] if mapped_only else None
    if mapped_only and not or_filters:
        return []
    rows = frappe.get_all(
        "Item",
        filters=filters,
        or_filters=or_filters,
        fields=fields,
        limit_page_length=min(max(cint(limit_page_length or 5000), 1), 5000),
        ignore_permissions=True,
    )
    needle = _normalize_mapping_text(search)
    if needle:
        searchable_fields = (
            "item_name",
            "item_code",
            "name",
            "custom_snapp_code",
            "restaurant_external_menu_item_id",
            "restaurant_external_product_id",
            "restaurant_external_variation_id",
            "restaurant_external_product_hash_id",
            "restaurant_external_variation_hash_id",
        )
        rows = [
            row
            for row in rows
            if any(needle in _normalize_mapping_text(row.get(fieldname)) for fieldname in searchable_fields)
        ]
    return rows


def search_snappfood_items(search="", limit=50):
    """Search native Items for the mapping dropdown without a 1,000-row cap."""
    search = str(search or "").strip()
    if not search:
        return {"status": "success", "items": []}

    like = f"%{search}%"
    or_filters = []
    for fieldname in (
        "name",
        "item_code",
        "item_name",
        "custom_snapp_code",
        "restaurant_external_menu_item_id",
        "restaurant_external_product_id",
        "restaurant_external_variation_id",
        "restaurant_external_product_hash_id",
        "restaurant_external_variation_hash_id",
    ):
        if _has_column("Item", fieldname):
            or_filters.append([fieldname, "like", like])

    if not or_filters:
        return {"status": "success", "items": []}

    rows = frappe.get_all(
        "Item",
        filters={"disabled": 0},
        or_filters=or_filters,
        fields=_local_item_fields(),
        order_by="modified desc",
        limit_page_length=min(max(cint(limit or 50), 1), 100),
        ignore_permissions=True,
    )
    return {"status": "success", "items": rows}


def _build_known_menu_rows(local_items):
    """Build mappable menu rows from menuItemIds learned from prior orders.

    Food Partner's menu endpoint has returned category-only payloads for some
    sessions.  Existing imported order lines still contain the real
    ``menuItemId`` and the exact title, so they are a safe read-only fallback
    until the remote menu response is available again.
    """
    rows = []
    seen = set()
    for item in local_items or []:
        external_id = str(item.get("restaurant_external_menu_item_id") or "").strip()
        title = str(item.get("item_name") or item.get("name") or "").strip()
        if not external_id or not title or external_id in seen:
            continue
        seen.add(external_id)
        rows.append(
            {
                "external_id": external_id,
                "product_id": str(item.get("restaurant_external_product_id") or "").strip(),
                "variation_id": str(item.get("restaurant_external_variation_id") or "").strip(),
                "product_hash_id": str(item.get("restaurant_external_product_hash_id") or "").strip(),
                "variation_hash_id": str(item.get("restaurant_external_variation_hash_id") or "").strip(),
                "category_id": "",
                "category_title": "",
                "title": title,
                "price": 0,
                "status": "KNOWN_FROM_ORDER",
            }
        )
    return rows


def _build_order_menu_rows(raw_orders, amount_multiplier=1):
    """Expose order-line products when Food Partner's menu endpoint is empty."""
    rows = []
    seen = set()
    for raw_order in raw_orders or []:
        try:
            normalized = normalize_snapp_order(raw_order, amount_multiplier=amount_multiplier)
        except Exception:
            continue
        for line in normalized.get("items") or []:
            external_id = str(
                line.get("menu_item_id")
                or line.get("variation_id")
                or line.get("product_id")
                or line.get("variation_hash_id")
                or line.get("product_hash_id")
                or ""
            ).strip()
            title = str(line.get("title") or "").strip()
            if not external_id or not title:
                continue
            key = f"{external_id}|{_normalize_mapping_text(title)}"
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "external_id": external_id,
                    "product_id": str(line.get("product_id") or "").strip(),
                    "variation_id": str(line.get("variation_id") or "").strip(),
                    "product_hash_id": str(line.get("product_hash_id") or "").strip(),
                    "variation_hash_id": str(line.get("variation_hash_id") or "").strip(),
                    "category_id": "",
                    "category_title": "",
                    "title": title,
                    "price": flt(line.get("unit_price") or 0),
                    "status": "KNOWN_FROM_ORDER",
                }
            )
    return rows


def _find_mapped_local_item(row, local_items):
    """Return the local Item bound to an exact Food Partner identifier.

    A title similarity is only a suggestion.  Importing must be based on one
    of the external IDs, otherwise a product such as ``کره ...`` can be shown
    as mapped for a different order line such as ``کلاب ...``.
    """
    external_keys = (
        "external_id",
        "menu_item_id",
        "product_id",
        "variation_id",
        "product_hash_id",
        "variation_hash_id",
    )
    item_keys = (
        "restaurant_external_menu_item_id",
        "restaurant_external_product_id",
        "restaurant_external_variation_id",
        "restaurant_external_product_hash_id",
        "restaurant_external_variation_hash_id",
    )
    wanted = {
        str(row.get(key) or "").strip()
        for key in external_keys
        if str(row.get(key) or "").strip()
    }
    if not wanted:
        return None

    matches = []
    seen = set()
    for item in local_items or []:
        item_ids = {
            str(item.get(key) or "").strip()
            for key in item_keys
            if str(item.get(key) or "").strip()
        }
        if not wanted.intersection(item_ids):
            continue
        item_name = str(item.get("name") or "").strip()
        if item_name and item_name not in seen:
            seen.add(item_name)
            matches.append(item)

    return matches[0] if len(matches) == 1 else None


def _local_item_external_ids(item):
    return {
        str(item.get(key) or "").strip()
        for key in (
            "restaurant_external_menu_item_id",
            "restaurant_external_product_id",
            "restaurant_external_variation_id",
            "restaurant_external_product_hash_id",
            "restaurant_external_variation_hash_id",
        )
        if str(item.get(key) or "").strip()
    }


def _plan_snappfood_auto_mapping(menu_rows, local_items, create_missing=False):
    """Plan safe automatic mapping without mutating ERPNext documents."""
    plan = []
    for row in menu_rows or []:
        title = str(row.get("title") or "").strip()
        external_id = str(
            row.get("external_id")
            or row.get("menu_item_id")
            or row.get("variation_id")
            or row.get("product_id")
            or ""
        ).strip()
        base = {**row, "title": title, "external_id": external_id}
        if not title or not external_id:
            plan.append({**base, "action": "unmatched", "reason": "missing_identity"})
            continue

        exact = _find_mapped_local_item(row, local_items)
        if exact:
            plan.append({**base, "action": "already_mapped", "item_name": exact.get("name") or ""})
            continue

        title_matches = [
            item
            for item in (local_items or [])
            if _normalize_mapping_text(item.get("item_name"))
            == _normalize_mapping_text(title)
        ]
        if len(title_matches) == 1:
            title_match = title_matches[0]
            existing_ids = _local_item_external_ids(title_match)
            if existing_ids:
                plan.append(
                    {
                        **base,
                        "action": "conflict",
                        "item_name": title_match.get("name") or "",
                        "reason": "title_item_has_other_external_id",
                    }
                )
            else:
                plan.append({**base, "action": "map", "item_name": title_match.get("name") or ""})
            continue

        if len(title_matches) > 1:
            plan.append({**base, "action": "unmatched", "reason": "ambiguous_title"})
        elif create_missing:
            plan.append({**base, "action": "create"})
        else:
            plan.append({**base, "action": "unmatched", "reason": "item_not_found"})
    return plan


def get_snappfood_mapping_rows(search="", refresh_menu=0):
    cfg = _get_settings()
    local_items = _get_local_item_rows(search)
    menu_rows = []
    if refresh_menu:
        menu_rows = fetch_snapp_menu(cfg).get("items") or []
        menu_rows = [
            row
            for row in menu_rows
            if row.get("title")
            and row.get("external_id")
            and not (
                row.get("category_title")
                and _normalize_mapping_text(row.get("title"))
                == _normalize_mapping_text(row.get("category_title"))
                and not row.get("variation_id")
            )
        ]
        if not menu_rows:
            menu_rows = _build_known_menu_rows(local_items)
        try:
            start_dt, end_dt = _resolve_snapp_order_window()
            fetched_orders = fetch_snapp_orders(
                from_datetime=start_dt,
                to_datetime=end_dt,
                page_size=cfg.get("page_size") or DEFAULT_PAGE_SIZE,
                max_pages=MAX_PAGES,
                settings=cfg,
            )
            existing_ids = {str(row.get("external_id") or "").strip() for row in menu_rows}
            menu_rows.extend(
                row
                for row in _build_order_menu_rows(
                    fetched_orders.get("orders") or [],
                    amount_multiplier=cfg.get("amount_multiplier") or 1,
                )
                if row.get("external_id") not in existing_ids
            )
        except Exception:
            # Menu refresh remains useful even when the report endpoint is
            # temporarily unavailable; the existing local fallback is enough.
            pass
    elif not menu_rows:
        menu_rows = _build_known_menu_rows(local_items)
    mappings = []
    for row in menu_rows:
        exact = _find_mapped_local_item(row, local_items)
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
            if match_score < 0.9:
                suggested = None
        mappings.append(
            {
                **row,
                "mapped_item": exact,
                "mapping_status": "Mapped" if exact else "Unmapped",
                "suggested_item": suggested,
                "match_score": round(match_score, 3),
            }
        )
    return {"status": "success", "settings": get_sync_status(), "menu": mappings, "items": local_items}


def save_snappfood_item_mapping(
    item_name,
    product_id="",
    variation_id="",
    product_hash_id="",
    variation_hash_id="",
    menu_item_id="",
    map_product_group=False,
    commit=True,
):
    if not item_name or not frappe.db.exists("Item", item_name):
        raise frappe.ValidationError("آیتم داخلی برای نگاشت معتبر نیست.")
    product_id = str(product_id or "").strip()
    product_hash_id = str(product_hash_id or "").strip()
    if map_product_group:
        if not product_id:
            raise frappe.ValidationError("برای نگاشت محصول و گزینه‌های آن، شناسه محصول Food Partner لازم است.")
        current_product_id = str(
            frappe.db.get_value("Item", item_name, "restaurant_external_product_id") or ""
        ).strip() if _has_column("Item", "restaurant_external_product_id") else ""
        if current_product_id and current_product_id != product_id:
            raise frappe.ValidationError(
                "این Item قبلاً به محصول دیگری از Food Partner متصل شده است؛ ابتدا نگاشت قبلی آن را بررسی کنید."
            )
        for fieldname, value in (
            ("restaurant_external_product_id", product_id),
            ("restaurant_external_product_hash_id", product_hash_id),
            ("restaurant_external_menu_item_id", product_id),
        ):
            if not value or not _has_column("Item", fieldname):
                continue
            matches = frappe.get_all(
                "Item",
                filters={fieldname: value},
                fields=["name"],
                limit_page_length=2,
                ignore_permissions=True,
            )
            if any(row.get("name") != item_name for row in matches):
                raise frappe.ValidationError(
                    "شناسه این محصول قبلاً روی Item دیگری نگاشت شده است؛ نگاشت قبلی را بررسی کنید."
                )

    if map_product_group:
        mapping_values = {
            "restaurant_external_product_id": product_id,
            "restaurant_external_variation_id": "",
            "restaurant_external_product_hash_id": product_hash_id,
            "restaurant_external_variation_hash_id": "",
            # In product-group mode the parent ID is the stable mapping key.
            "restaurant_external_menu_item_id": product_id,
        }
    else:
        mapping_values = {
            "restaurant_external_product_id": product_id,
            "restaurant_external_variation_id": str(variation_id or "").strip(),
            "restaurant_external_product_hash_id": product_hash_id,
            "restaurant_external_variation_hash_id": str(variation_hash_id or "").strip(),
            "restaurant_external_menu_item_id": str(menu_item_id or variation_id or product_id or "").strip(),
        }
    values = {}
    for fieldname, value in mapping_values.items():
        if _has_column("Item", fieldname):
            values[fieldname] = str(value or "").strip()
    if _has_column("Item", "restaurant_external_mapping_status"):
        values["restaurant_external_mapping_status"] = "Mapped"
    if not values:
        raise frappe.ValidationError("فیلدهای اتصال اسنپ‌فود هنوز روی Item ساخته نشده‌اند.")
    _remove_food_partner_modifier_mapping(
        {
            "menu_item_id": menu_item_id,
            "variation_id": variation_id,
            "product_id": product_id,
            "product_hash_id": product_hash_id,
            "variation_hash_id": variation_hash_id,
        }
    )
    frappe.db.set_value("Item", item_name, values, update_modified=True)
    if commit:
        frappe.db.commit()
    return {"status": "success", "item": item_name, "values": values}


def _find_mapped_product_group_item(product_id):
    """Resolve a parent-product mapping before any individual variation alias."""
    product_id = str(product_id or "").strip()
    required_fields = (
        "restaurant_external_product_id",
        "restaurant_external_menu_item_id",
        "restaurant_external_variation_id",
    )
    if not product_id or not all(_has_column("Item", fieldname) for fieldname in required_fields):
        return ""
    rows = frappe.get_all(
        "Item",
        filters={"restaurant_external_product_id": product_id},
        fields=["name", "restaurant_external_menu_item_id", "restaurant_external_variation_id"],
        limit_page_length=20,
        ignore_permissions=True,
    )
    matches = [
        row
        for row in rows
        if str(row.get("restaurant_external_menu_item_id") or "").strip() == product_id
        and not str(row.get("restaurant_external_variation_id") or "").strip()
    ]
    return matches[0].get("name") if len(matches) == 1 else ""


def auto_map_snappfood_items(create_missing=False, refresh_menu=1):
    """Map exact Food Partner rows, optionally creating missing native Items."""
    mapping_rows = get_snappfood_mapping_rows(search="", refresh_menu=cint(refresh_menu))
    if mapping_rows.get("status") == "error":
        return mapping_rows

    menu_rows = mapping_rows.get("menu") or []
    local_items = mapping_rows.get("items") or []
    plan = _plan_snappfood_auto_mapping(
        menu_rows,
        local_items,
        create_missing=bool(cint(create_missing)),
    )
    result = {
        "status": "success",
        "menu_count": len(menu_rows),
        "already_mapped_count": 0,
        "mapped_count": 0,
        "created_count": 0,
        "unmatched_count": 0,
        "conflict_count": 0,
        "unmatched": [],
        "conflicts": [],
        "errors": [],
    }
    changed = False
    for row in plan:
        action = row.get("action")
        if action == "already_mapped":
            result["already_mapped_count"] += 1
            continue
        if action == "map":
            try:
                save_snappfood_item_mapping(
                    item_name=row.get("item_name") or "",
                    product_id=row.get("product_id") or "",
                    variation_id=row.get("variation_id") or "",
                    product_hash_id=row.get("product_hash_id") or "",
                    variation_hash_id=row.get("variation_hash_id") or "",
                    menu_item_id=row.get("menu_item_id") or row.get("external_id") or "",
                    commit=False,
                )
                result["mapped_count"] += 1
                changed = True
            except Exception as exc:
                result["errors"].append({"external_id": row.get("external_id") or "", "title": row.get("title") or "", "error": str(exc)})
            continue
        if action == "create":
            try:
                created = create_snappfood_item_from_mapping(
                    title=row.get("title") or "",
                    price=row.get("price") or 0,
                    product_id=row.get("product_id") or "",
                    variation_id=row.get("variation_id") or "",
                    product_hash_id=row.get("product_hash_id") or "",
                    variation_hash_id=row.get("variation_hash_id") or "",
                    menu_item_id=row.get("menu_item_id") or row.get("external_id") or "",
                    commit=False,
                )
                if created.get("created"):
                    result["created_count"] += 1
                else:
                    result["mapped_count"] += 1
                changed = True
            except Exception as exc:
                result["errors"].append({"external_id": row.get("external_id") or "", "title": row.get("title") or "", "error": str(exc)})
            continue
        if action == "conflict":
            result["conflict_count"] += 1
            result["conflicts"].append({"external_id": row.get("external_id") or "", "title": row.get("title") or "", "item_name": row.get("item_name") or "", "reason": row.get("reason") or ""})
            continue
        result["unmatched_count"] += 1
        result["unmatched"].append({"external_id": row.get("external_id") or "", "title": row.get("title") or "", "reason": row.get("reason") or ""})

    if changed:
        frappe.db.commit()
    result["processed_count"] = len(plan)
    return result


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
        unit_price = _scale_amount(
            row.get("price") or row.get("unitPrice") or row.get("unit_price"),
            amount_multiplier,
        )
        explicit_discount = _scale_amount(
            row.get("discount") or row.get("discountAmount") or row.get("discountPerUnit"),
            amount_multiplier,
        )
        gross_unit_price = _scale_amount(
            row.get("originPrice") or row.get("origin_price") or row.get("originalPrice"),
            amount_multiplier,
        )
        if gross_unit_price <= 0:
            gross_unit_price = unit_price + explicit_discount
        gross_unit_price = max(gross_unit_price, unit_price)
        discount_per_unit = max(explicit_discount, gross_unit_price - unit_price, 0)
        items.append(
            {
                "line_id": str(
                    row.get("orderProductId")
                    or row.get("order_product_id")
                    or row.get("orderProductID")
                    or row.get("id")
                    or ""
                ).strip(),
                "menu_item_id": str(
                    row.get("menuItemId")
                    or row.get("id")
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
                "unit_price": unit_price,
                "gross_unit_price": gross_unit_price,
                "discount": explicit_discount,
                "discount_total": discount_per_unit * qty,
                "packaging_cost": _scale_amount(row.get("packagingCost"), amount_multiplier),
                "with_tax": cint(row.get("withTax") or 0),
                "toppings": row.get("toppings") or [],
            }
        )

    line_discount_total = sum(flt(item.get("discount_total") or 0) for item in items)
    reported_discount = max(
        _scale_amount(
            raw_order.get("discountAmount")
            or raw_order.get("discount")
            or raw_order.get("otherDiscounts"),
            amount_multiplier,
        ),
        _scale_amount(raw_order.get("couponDiscountSfShareAmount"), amount_multiplier)
        + _scale_amount(raw_order.get("couponDiscountVendorShareAmount"), amount_multiplier),
    )
    gross_items_total = sum(
        flt(item.get("gross_unit_price") or item.get("unit_price") or 0) * flt(item.get("qty") or 0)
        for item in items
    )
    reported_net_items_total = _scale_amount(raw_order.get("price"), amount_multiplier)
    discount_from_item_total = max(gross_items_total - reported_net_items_total, 0) if reported_net_items_total else 0
    resolved_discount_amount = max(line_discount_total, reported_discount, discount_from_item_total)

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
        "discount": resolved_discount_amount,
        "discount_amount": resolved_discount_amount,
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


def _resolve_snapp_primary_customer(settings=None):
    """Resolve the native customer used as the primary party for imported orders.

    Existing installations often have a customer named ``اسنپ فود`` but leave
    the optional integration setting empty. Prefer an explicit configured
    customer, then safely discover that known native customer without ever
    selecting an arbitrary Customer record.
    """
    settings = settings or {}
    configured = str(settings.get("default_customer") or "").strip()
    if configured:
        if frappe.db.exists("Customer", configured):
            return configured
        resolved = frappe.db.get_value(
            "Customer",
            {"customer_name": configured, "disabled": 0},
            "name",
        )
        if resolved:
            return resolved

    for candidate in ("اسنپ فود", "اسنپ‌فود", "Snappfood", "Snapp Food"):
        try:
            rows = frappe.get_all(
                "Customer",
                filters={"customer_name": candidate, "disabled": 0},
                fields=["name"],
                limit_page_length=1,
                ignore_permissions=True,
            )
        except Exception:
            rows = []
        if rows:
            return rows[0].get("name") or ""
    return ""


def _is_generic_snapp_customer_name(value):
    normalized = re.sub(r"\s+", " ", str(value or "").strip()).casefold()
    return (
        not normalized
        or normalized in {"guest", "snapp guest"}
        or normalized.startswith("snapp guest ")
    )


def _food_partner_customer_name(customer_name, external_customer_id):
    supplied_name = re.sub(r"\s+", " ", str(customer_name or "").strip())
    if supplied_name and not _is_generic_snapp_customer_name(supplied_name):
        return supplied_name

    customer_key = str(external_customer_id or "").strip() or _slugify(supplied_name) or "guest"
    return f"{FALLBACK_GUEST_NAME} ID {customer_key[:12]}"


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

    external_id = str(external_customer_id or "").strip()
    if external_id and _has_column("Customer", "restaurant_external_customer_id"):
        external_filters = {"restaurant_external_customer_id": external_id, "disabled": 0}
        if _has_column("Customer", "restaurant_external_source"):
            external_filters["restaurant_external_source"] = SNAPP_SOURCE
        existing = frappe.db.get_value("Customer", external_filters, "name")
        if existing:
            display_name = _food_partner_customer_name(customer_name, external_id)
            current_name = str(frappe.db.get_value("Customer", existing, "customer_name") or "").strip()
            if (
                display_name != current_name
                and _is_generic_snapp_customer_name(current_name)
                and not _is_generic_snapp_customer_name(display_name)
            ):
                frappe.db.set_value("Customer", existing, "customer_name", display_name, update_modified=False)
            return existing

    if not mobile:
        customer_name = _food_partner_customer_name(customer_name, external_id)
        if _is_generic_snapp_customer_name(customer_name) or not external_id:
            existing = frappe.db.get_value("Customer", {"customer_name": customer_name, "disabled": 0}, "name")
            if existing:
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


def _build_snapp_item_creation_values(line, item_group, item_code):
    """Build only the native Item payload used by the mapping action."""
    title = str(line.get("title") or "").strip()
    return {
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


def create_snappfood_item_from_mapping(
    title,
    price=0,
    product_id="",
    variation_id="",
    product_hash_id="",
    variation_hash_id="",
    menu_item_id="",
    product_title="",
    map_product_group=False,
    commit=True,
):
    """Create or map one native Item without creating an order or invoice."""
    map_product_group = bool(cint(map_product_group))
    product_id = str(product_id or "").strip()
    if map_product_group and not product_id:
        raise frappe.ValidationError("برای ساخت Item و نگاشت گزینه‌ها، شناسه محصول Food Partner لازم است.")
    line = {
        "title": str((product_title if map_product_group else "") or title or "").strip(),
        "unit_price": flt(price or 0),
        "product_id": product_id,
        "variation_id": "" if map_product_group else str(variation_id or "").strip(),
        "product_hash_id": str(product_hash_id or "").strip(),
        "variation_hash_id": "" if map_product_group else str(variation_hash_id or "").strip(),
        "menu_item_id": product_id if map_product_group else str(menu_item_id or variation_id or product_id or "").strip(),
    }
    if not line["title"]:
        raise frappe.ValidationError("عنوان کالای Food Partner برای ساخت Item خالی است.")
    if not any(
        line.get(key)
        for key in (
            "menu_item_id",
            "product_id",
            "variation_id",
            "product_hash_id",
            "variation_hash_id",
        )
    ):
        raise frappe.ValidationError("برای ساخت Item، شناسهٔ کالای Food Partner لازم است.")

    external_fields = (
        (
            ("restaurant_external_product_id", line.get("product_id")),
            ("restaurant_external_product_hash_id", line.get("product_hash_id")),
        )
        if map_product_group
        else (
            ("restaurant_external_menu_item_id", line.get("menu_item_id")),
            ("restaurant_external_product_id", line.get("product_id")),
            ("restaurant_external_variation_id", line.get("variation_id")),
            ("restaurant_external_product_hash_id", line.get("product_hash_id")),
            ("restaurant_external_variation_hash_id", line.get("variation_hash_id")),
        )
    )
    existing_item = ""
    for fieldname, value in external_fields:
        if value and _has_column("Item", fieldname):
            existing_item = frappe.db.get_value("Item", {fieldname: value}, "name") or ""
            if existing_item:
                break
    if not existing_item:
        existing_item = frappe.db.get_value(
            "Item",
            {"item_name": line["title"], "disabled": 0},
            "name",
        ) or ""

    if existing_item:
        if map_product_group:
            save_snappfood_item_mapping(
                item_name=existing_item,
                product_id=line["product_id"],
                product_hash_id=line["product_hash_id"],
                map_product_group=True,
                commit=False,
            )
        else:
            _tag_item_mapping(existing_item, line)
        if _has_column("Item", "custom_snapp_code"):
            current_code = frappe.db.get_value("Item", existing_item, "custom_snapp_code")
            if not (current_code or "").strip():
                frappe.db.set_value(
                    "Item",
                    existing_item,
                    "custom_snapp_code",
                    _build_item_code(line),
                    update_modified=False,
                )
        if commit:
            frappe.db.commit()
        return {"status": "mapped", "created": False, "item": existing_item}

    item_group = _ensure_import_item_group()
    item_code = _unique_item_code(_build_item_code_from_title(line["title"], _build_item_code(line)))
    item_doc = frappe.get_doc(_build_snapp_item_creation_values(line, item_group, item_code))
    if _has_column("Item", "restaurant_enabled"):
        item_doc.set("restaurant_enabled", 0)
    if map_product_group:
        for fieldname, value in (
            ("restaurant_external_menu_item_id", line["menu_item_id"]),
            ("restaurant_external_product_id", line["product_id"]),
            ("restaurant_external_variation_id", ""),
            ("restaurant_external_product_hash_id", line["product_hash_id"]),
            ("restaurant_external_variation_hash_id", ""),
        ):
            if _has_column("Item", fieldname):
                item_doc.set(fieldname, value)
    else:
        if _has_column("Item", "restaurant_external_menu_item_id"):
            item_doc.set("restaurant_external_menu_item_id", line["menu_item_id"])
        if _has_column("Item", "restaurant_external_product_id"):
            item_doc.set("restaurant_external_product_id", line["product_id"])
        if _has_column("Item", "restaurant_external_variation_id"):
            item_doc.set("restaurant_external_variation_id", line["variation_id"])
        if _has_column("Item", "restaurant_external_product_hash_id"):
            item_doc.set("restaurant_external_product_hash_id", line["product_hash_id"])
        if _has_column("Item", "restaurant_external_variation_hash_id"):
            item_doc.set("restaurant_external_variation_hash_id", line["variation_hash_id"])
    if _has_column("Item", "restaurant_external_mapping_status"):
        item_doc.set("restaurant_external_mapping_status", "Mapped")
    if _has_column("Item", "custom_snapp_code"):
        item_doc.set("custom_snapp_code", _build_item_code(line))
    item_doc.insert(ignore_permissions=True)
    if commit:
        frappe.db.commit()
    return {"status": "created", "created": True, "item": item_doc.name}


def _resolve_item_code(line):
    external_menu_item_id = (line.get("menu_item_id") or "").strip()
    external_product_id = (line.get("product_id") or "").strip()
    external_variation_id = (line.get("variation_id") or "").strip()
    external_product_hash_id = (line.get("product_hash_id") or "").strip()
    external_variation_hash_id = (line.get("variation_hash_id") or "").strip()
    title = (line.get("title") or "").strip() or "Snapp Item"
    snapp_code = _build_item_code(line)

    # A product-level mapping represents the parent Item and all of its
    # Food Partner choices. It must win over stale per-variation aliases.
    by_product_group = _find_mapped_product_group_item(external_product_id)
    if by_product_group:
        return by_product_group

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

    normalized_title_match = _match_local_item_by_title(title, _get_local_item_rows())
    if normalized_title_match:
        item_name = normalized_title_match.get("name")
        _tag_item_mapping(item_name, line)
        if _has_column("Item", "custom_snapp_code"):
            current_snapp_code = frappe.db.get_value("Item", item_name, "custom_snapp_code")
            if not (current_snapp_code or "").strip():
                frappe.db.set_value("Item", item_name, "custom_snapp_code", snapp_code, update_modified=False)
        return item_name

    settings = _get_settings()
    if settings.get("require_item_mapping"):
        raise frappe.ValidationError(
            f"کالای Food Partner نگاشت نشده است: {title} ({external_variation_id or external_product_id or external_menu_item_id or 'بدون شناسه'})"
        )

    return create_snappfood_item_from_mapping(
        title=title,
        price=line.get("unit_price") or 0,
        product_id=external_product_id,
        variation_id=external_variation_id,
        product_hash_id=external_product_hash_id,
        variation_hash_id=external_variation_hash_id,
        menu_item_id=external_menu_item_id,
        commit=False,
    )["item"]


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
        _set_if_column(
            line_payload,
            "Sales Order Item",
            "restaurant_external_discount",
            flt(line.get("discount_total") or line.get("discount") or 0),
        )
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


_SALES_INVOICE_NUMERIC_LINE_FIELDS = {
    "restaurant_external_discount",
    "restaurant_external_packaging_cost",
    "restaurant_external_with_tax",
}


def _normalize_sales_invoice_line_value(fieldname, value):
    """Keep empty external numeric snapshots valid for MariaDB decimal fields."""
    if fieldname in _SALES_INVOICE_NUMERIC_LINE_FIELDS:
        return flt(value or 0)
    return value or ""


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
        _set_if_column(
            updates,
            "Sales Order Item",
            "restaurant_external_discount",
            flt(source_line.get("discount_total") or source_line.get("discount") or 0),
        )
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
    review_status = (
        frappe.db.get_value("Sales Order", sales_order_name, ORDER_REVIEW_FIELD) or ORDER_REVIEW_APPROVED
        if _has_column("Sales Order", ORDER_REVIEW_FIELD)
        else ORDER_REVIEW_APPROVED
    )
    if _has_column("Sales Order", "restaurant_external_state"):
        updates["restaurant_external_state"] = order_payload["external_state"]
    if _has_column("Sales Order", "restaurant_status"):
        if order_payload["status"] == "cancelled":
            updates["restaurant_status"] = "cancelled"
        elif review_status == ORDER_REVIEW_PENDING:
            updates["restaurant_status"] = "new"
        elif review_status == ORDER_REVIEW_REJECTED:
            updates["restaurant_status"] = "cancelled"
        else:
            updates["restaurant_status"] = order_payload["status"]
    if order_payload["status"] == "cancelled" and review_status == ORDER_REVIEW_PENDING:
        updates[ORDER_REVIEW_FIELD] = ORDER_REVIEW_REJECTED
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

    if order_payload["status"] == "cancelled":
        if so_doc.docstatus == 1:
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
    configured_customer = _resolve_snapp_primary_customer(settings)
    if configured_customer:
        customer = configured_customer
        customer_mobile_for_pos = ""
        if external_customer != configured_customer:
            secondary_customer = frappe.db.get_value("Customer", external_customer, "customer_name") or external_customer
    source_items = order_payload.get("items") or []
    if not source_items:
        raise frappe.ValidationError(f"Order {order_payload['order_id']} has no valid items.")
    # POS resolves pricing, BOM/customization, service items, taxes and order
    # context itself. A standalone Food Partner modifier is folded into its
    # separate parent line; a combined product/variation carries both the
    # native base Item and selected BOM option in the same cart line.
    cart_items = []
    resolved_lines = []
    pending_modifier_lines = []
    modifier_mapping_index = _food_partner_modifier_mapping_index()
    for line in source_items:
        modifier_mapping = _find_food_partner_modifier_mapping(line, modifier_mapping_index)
        is_item_modifier_mapping = bool(
            modifier_mapping and modifier_mapping.get("mapping_mode") == "item_modifier"
        )
        item_code = str(modifier_mapping.get("parent_item") or "").strip() if modifier_mapping else _resolve_item_code(line)
        if modifier_mapping and not frappe.db.exists("Item", item_code):
            raise frappe.ValidationError("کالای اصلی نگاشت Modifier دیگر در سیستم موجود نیست.")
        item_slug = (frappe.db.get_value("Item", item_code, "restaurant_slug") or item_code or "").strip()
        if not item_slug:
            raise frappe.ValidationError(f"کد Item برای ردیف سفارش {order_payload['order_id']} خالی است.")
        resolved_line = {
            **line,
            "item_code": item_code,
            "item_slug": item_slug,
            "food_partner_modifier_mapping": modifier_mapping,
            "is_modifier_line": bool(modifier_mapping) and not is_item_modifier_mapping,
            "is_item_modifier_line": is_item_modifier_mapping,
        }
        resolved_lines.append(resolved_line)
        if modifier_mapping and not is_item_modifier_mapping:
            pending_modifier_lines.append(resolved_line)
            continue
        cart_item = {
            "item_slug": item_slug,
            "qty": max(flt(line.get("qty") or 1), 1),
            "note": line.get("title") or "",
        }
        if flt(line.get("gross_unit_price") or 0) > 0:
            cart_item["external_unit_price"] = flt(line.get("gross_unit_price"))
        if is_item_modifier_mapping:
            mapping = modifier_mapping or {}
            cart_item.setdefault("customization", {}).setdefault("selected_modifiers", []).append(
                {
                    "group": mapping.get("group_name") or "",
                    "option": mapping.get("option_name") or "",
                    "qty": max(flt(mapping.get("option_qty") or 1), 0.0001),
                }
            )
        cart_items.append(cart_item)
        resolved_line["cart_item"] = cart_item

    for modifier_line in pending_modifier_lines:
        mapping = modifier_line.get("food_partner_modifier_mapping") or {}
        parent_candidates = [
            row for row in resolved_lines
            if not row.get("is_modifier_line") and row.get("item_code") == mapping.get("parent_item")
        ]
        modifier_qty = max(flt(modifier_line.get("qty") or 1), 1)
        exact_qty_candidates = [
            row for row in parent_candidates
            if abs(flt(row.get("qty") or 1) - modifier_qty) < 1e-8
        ]
        if len(exact_qty_candidates) == 1:
            parent_line = exact_qty_candidates[0]
        elif len(parent_candidates) == 1:
            parent_line = parent_candidates[0]
        elif not parent_candidates:
            raise frappe.ValidationError(
                f"گزینهٔ «{modifier_line.get('title') or mapping.get('option_label')}» به Modifier کالای "
                f"«{mapping.get('parent_item_name') or mapping.get('parent_item')}» نگاشت شده، "
                "اما همان کالای اصلی در این سفارش نیست."
            )
        else:
            raise frappe.ValidationError(
                f"چند ردیف از کالای «{mapping.get('parent_item_name') or mapping.get('parent_item')}» "
                "در سفارش وجود دارد و اتصال این Modifier به ردیف درست مبهم است."
            )

        parent_cart_item = parent_line.get("cart_item")
        if not parent_cart_item:
            raise frappe.ValidationError("ردیف کالای اصلی برای ثبت Modifier آماده نیست.")
        parent_qty = max(flt(parent_line.get("qty") or 1), 1)
        selected_qty = max(flt(mapping.get("option_qty") or 1) * modifier_qty / parent_qty, 0.0001)
        customization = parent_cart_item.setdefault("customization", {})
        selected_modifiers = customization.setdefault("selected_modifiers", [])
        selected_modifiers.append(
            {
                "group": mapping.get("group_name") or "",
                "option": mapping.get("option_name") or "",
                "qty": selected_qty,
            }
        )

        modifier_gross_total = flt(
            modifier_line.get("gross_unit_price") or modifier_line.get("unit_price") or 0
        ) * modifier_qty
        parent_gross_unit = flt(
            parent_cart_item.get("external_unit_price")
            or parent_line.get("gross_unit_price")
            or parent_line.get("unit_price")
            or 0
        )
        if modifier_gross_total > 0 or parent_gross_unit > 0:
            parent_cart_item["external_unit_price"] = parent_gross_unit + modifier_gross_total / parent_qty
        parent_line.setdefault("mapped_modifier_lines", []).append(modifier_line)

    totals = {
        "discountAmount": flt(order_payload.get("discount_amount") or order_payload.get("discount") or 0),
        "taxAmount": flt(order_payload.get("tax") or 0),
        "serviceAmount": flt(order_payload.get("service_cost") or order_payload.get("service_fee") or 0),
        "packagingAmount": flt(order_payload.get("packaging_cost") or 0),
        "tipAmount": flt(order_payload.get("tip") or 0),
    }
    # The Food Partner discount is authoritative for imported orders. POS also
    # calculates customer-group, coach, coupon, and manual discounts, so mark
    # this fixed source discount as the explicit manual winner to prevent any
    # local discount from stacking with or replacing it.
    financial_modifiers = {
        "manual_discount": 1,
        "discount_type": "fixed",
        "discount_value": totals["discountAmount"],
        "discount_source": "food_partner",
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
            "financial_modifiers": financial_modifiers,
            "totals": totals,
            "secondary_customer": secondary_customer,
        },
        commit=False,
        requires_review=True,
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
        updates["restaurant_status"] = "cancelled" if order_payload["status"] == "cancelled" else "new"
    if _has_column("Sales Order", ORDER_REVIEW_FIELD):
        updates[ORDER_REVIEW_FIELD] = (
            ORDER_REVIEW_REJECTED if order_payload["status"] == "cancelled" else ORDER_REVIEW_PENDING
        )
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
        if line.get("is_modifier_line"):
            continue
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
        _set_if_column(
            line_updates,
            "Sales Order Item",
            "restaurant_external_discount",
            flt(line.get("discount_total") or line.get("discount") or 0),
        )
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
    _set_restaurant_order_status(
        so_name,
        "cancelled" if order_payload["status"] == "cancelled" else "new",
        force=True,
    )
    if order_payload["status"] == "cancelled":
        so_doc = frappe.get_doc("Sales Order", so_name)
        if so_doc.docstatus == 1:
            so_doc.flags.ignore_permissions = True
            so_doc.cancel()
        return so_name, "cancelled"
    return so_name, "created"


def _ensure_sales_invoice_for_order(sales_order_name, order_payload):
    """Create the native Sales Invoice through the existing POS settlement path."""
    from restaurant.order_review import require_order_approved

    require_order_approved(sales_order_name)
    if not _has_column("Sales Invoice", "restaurant_external_order_id"):
        return {"status": "skipped", "reason": "Sales Invoice integration fields are not migrated."}

    invoice_filters = {
        "restaurant_external_order_id": order_payload["order_id"],
        "docstatus": 1,
    }
    if _has_column("Sales Invoice", "restaurant_external_source"):
        invoice_filters["restaurant_external_source"] = SNAPP_SOURCE
    existing_invoice = frappe.db.get_value("Sales Invoice", invoice_filters, "name")
    if existing_invoice:
        return {"status": "exists", "sales_invoice": existing_invoice}

    # Food Partner's settlement happens outside this ERPNext account. Keep the
    # imported invoice on account; never turn the platform's payment state into
    # a local POS payment or Payment Entry. The source payment method remains
    # available separately in the external snapshot fields.
    payment_method = "credit"

    # This is the same settlement function used by Management POS. It creates
    # the SI, payments, payment method, status and audit note consistently.
    from restaurant.api import settle_pos_order

    payment_details = {
        "method": payment_method,
        "reference_no": order_payload.get("bill_number") or order_payload.get("order_id") or "",
    }
    for fieldname in ("posting_date", "posting_time", "due_date"):
        if order_payload.get(fieldname):
            payment_details[fieldname] = order_payload[fieldname]
    settlement = settle_pos_order(
        order_name=sales_order_name,
        payment=payment_details,
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
                invoice_values[fieldname] = _normalize_sales_invoice_line_value(
                    fieldname,
                    source_values.get(fieldname),
                )
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


def sync_snapp_orders(
    trigger="scheduler",
    from_datetime=None,
    to_datetime=None,
    only_new=1,
    update_status_fields=1,
    selected_order_ids=None,
    max_import=None,
    settings=None,
):
    settings = settings if settings is not None else _get_settings()
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
        all_rows = fetched_payload.get("orders") or []
        all_rows = sorted(
            all_rows,
            key=lambda row: str(row.get("createdAt") or row.get("orderDate") or ""),
        )
        rows = all_rows
        requested_order_ids = [
            str(value or "").strip()
            for value in (selected_order_ids or [])
            if str(value or "").strip()
        ]
        if requested_order_ids:
            rows, missing_order_ids = _select_snapp_orders_for_import(
                all_rows,
                requested_order_ids,
                max_import=max_import or 3,
            )
            result["requested_count"] = len(requested_order_ids)
            result["selected_count"] = len(rows)
            result["missing_order_ids"] = missing_order_ids
            result["sales_orders"] = []

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

                    if settings.get("auto_sync_invoices") and action != "cancelled" and order_is_approved(existing):
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
                    if requested_order_ids:
                        result["sales_orders"].append(
                            {
                                "order_id": normalized["order_id"],
                                "sales_order": existing,
                                "action": action,
                            }
                        )
                    continue

                sales_order_name, action = _create_sales_order(normalized)
                if requested_order_ids:
                    result["sales_orders"].append(
                        {
                            "order_id": normalized["order_id"],
                            "sales_order": sales_order_name,
                            "action": action,
                        }
                    )
                if settings.get("auto_sync_invoices") and action != "cancelled" and order_is_approved(sales_order_name):
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
                        "order_id": _raw_snapp_order_id(raw_order),
                        "error": frappe.get_traceback(with_context=False),
                    }
                )

        if settings["write_debug_json"]:
            _write_debug_json(fetched_payload)

        if update_status_fields:
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_success_at", get_datetime_str(now_datetime()))
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_at", None)
            _set_single_if_exists("Restaurant Web Settings", "snapp_last_error_message", "")
            if _has_field("Restaurant Web Settings", "snapp_last_seen_created_at") and all_rows:
                _set_single_if_exists(
                    "Restaurant Web Settings",
                    "snapp_last_seen_created_at",
                    all_rows[-1].get("createdAt") or all_rows[-1].get("orderDate"),
                )

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
