"""Fail-safe management product listing for schema-drift tolerant UI loading."""

import frappe
from frappe import _


def _legacy_api():
    from restaurant import api as legacy

    return legacy


def _safe_pos_api():
    from restaurant import api_pos_background

    return api_pos_background


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _tags(value):
    if isinstance(value, list):
        return [str(row or "").strip() for row in value if str(row or "").strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _management_products_from_boot(boot):
    """Normalize the smaller POS item shape for the management products page."""
    rows = []
    for source in list((boot or {}).get("items") or []):
        item = dict(source or {})
        name = str(item.get("name") or item.get("item_code") or item.get("slug") or "").strip()
        if not name:
            continue
        title = str(item.get("title") or item.get("item_name") or name).strip()
        disabled = _to_int(item.get("disabled") or item.get("is_disabled") or 0)
        if "is_active" in item:
            is_active = 1 if _to_int(item.get("is_active"), 0) else 0
        elif "restaurant_enabled" in item:
            is_active = 1 if _to_int(item.get("restaurant_enabled"), 0) else 0
        else:
            is_active = 0 if disabled else 1
        base_price = item.get("base_price", item.get("standard_rate", 0)) or 0
        rows.append(
            {
                **item,
                "name": name,
                "item_code": str(item.get("item_code") or name).strip(),
                "item_name": str(item.get("item_name") or title).strip(),
                "title": title,
                "base_price": base_price,
                "standard_rate": item.get("standard_rate", base_price) or 0,
                "category_title": str(item.get("category_title") or item.get("category") or "").strip(),
                "category_slug": str(item.get("category_slug") or item.get("category") or "").strip(),
                "subcategory_title": str(item.get("subcategory_title") or item.get("subcategory") or "").strip(),
                "subcategory_slug": str(item.get("subcategory_slug") or item.get("subcategory") or "").strip(),
                "is_active": is_active,
                "is_disabled": disabled,
                "out_of_stock": _to_int(item.get("out_of_stock", item.get("restaurant_out_of_stock", 0)) or 0),
                "tags": _tags(item.get("tags") or item.get("restaurant_item_tags")),
            }
        )
    return rows


def _filter_management_products(rows, search="", category="", active_only=0, tag=""):
    query = str(search or "").strip().lower()
    category_key = str(category or "").strip().lower()
    tag_key = str(tag or "").strip().lower()
    active = str(active_only or "").strip().lower() in {"1", "true", "yes", "on"}
    result = []
    for row in list(rows or []):
        if active and not _to_int(row.get("is_active") or 0):
            continue
        if category_key:
            category_values = {
                str(row.get("category_slug") or "").strip().lower(),
                str(row.get("category_title") or "").strip().lower(),
            }
            if category_key not in category_values:
                continue
        if tag_key:
            tags = [str(value or "").strip().lower() for value in _tags(row.get("tags"))]
            if tag_key not in tags:
                continue
        if query:
            haystack = " ".join(
                [
                    str(row.get("name") or ""),
                    str(row.get("item_code") or ""),
                    str(row.get("item_name") or ""),
                    str(row.get("title") or ""),
                ]
            ).lower()
            if query not in haystack:
                continue
        result.append(row)
    return result


@frappe.whitelist()
def list_management_products_safe(search="", category="", active_only=0, branch="", tag=""):
    """Return products even when optional Restaurant fields are missing or stale.

    Prefer the rich legacy management endpoint. If schema drift makes that fail,
    use the already fail-safe POS boot and normalize its items so the products
    page still renders instead of becoming empty.
    """
    legacy = _legacy_api()
    legacy._ensure_management_access()
    try:
        payload = legacy.list_management_products(
            search=search,
            category=category,
            active_only=active_only,
            branch=branch,
            tag=tag,
        )
        if isinstance(payload, dict) and isinstance(payload.get("products"), list):
            return payload
    except Exception:
        try:
            frappe.log_error(frappe.get_traceback(), "Management Products Primary List Error")
        except Exception:
            pass

    boot = _safe_pos_api().get_management_pos_boot_safe(branch)
    rows = _filter_management_products(
        _management_products_from_boot(boot),
        search=search,
        category=category,
        active_only=active_only,
        tag=tag,
    )
    return {
        "products": rows,
        "currency": str((boot or {}).get("currency") or "IRR"),
        "fallback": 1,
    }
