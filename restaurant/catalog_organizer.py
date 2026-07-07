import re

import frappe
from frappe.utils import cint, cstr, flt


def _has_column(doctype, fieldname):
    try:
        return frappe.db.has_column(doctype, fieldname)
    except Exception:
        return False


def _menu_root_group():
    root = frappe.db.get_value(
        "Item Group",
        {"restaurant_slug": "restaurant-menu", "restaurant_is_menu_category": 0},
        "name",
    )
    if root:
        return root

    root = frappe.db.get_value("Item Group", {"item_group_name": "Restaurant Menu"}, "name")
    if root:
        return root

    absolute_root = frappe.db.get_value("Item Group", {"parent_item_group": ""}, "name") or frappe.db.get_value(
        "Item Group", {}, "name"
    )
    if not absolute_root:
        frappe.throw("No Item Group found to create restaurant menu tree.")

    doc = frappe.get_doc(
        {
            "doctype": "Item Group",
            "item_group_name": "Restaurant Menu",
            "parent_item_group": absolute_root,
            "is_group": 1,
            "restaurant_is_menu_category": 0,
            "restaurant_is_subcategory": 0,
            "restaurant_slug": "restaurant-menu",
            "restaurant_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_group(item_group_name, parent_item_group, slug, is_subcategory):
    existing = frappe.db.get_value("Item Group", {"restaurant_slug": slug}, "name")
    if existing:
        return existing

    existing = frappe.db.get_value(
        "Item Group",
        {"item_group_name": item_group_name, "parent_item_group": parent_item_group},
        "name",
    )
    if existing:
        return existing

    doc = frappe.get_doc(
        {
            "doctype": "Item Group",
            "item_group_name": item_group_name,
            "parent_item_group": parent_item_group,
            "is_group": 0 if is_subcategory else 1,
            "restaurant_is_menu_category": 1,
            "restaurant_is_subcategory": 1 if is_subcategory else 0,
            "restaurant_slug": slug,
            "restaurant_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _classify_title(item_name):
    title = cstr(item_name).strip()
    lowered = (
        title.replace("ي", "ی")
        .replace("ك", "ک")
        .replace("آ", "ا")
        .replace("\u200c", " ")
        .strip()
        .lower()
    )

    if lowered in {"لته", "لاته"}:
        normalized_name = "قهوه لاته"
    elif lowered.startswith("لاته"):
        normalized_name = f"قهوه {title}"
    else:
        normalized_name = title

    coffee_keywords = (
        "لاته",
        "لته",
        "قهوه",
        "اسپرسو",
        "امریکانو",
        "مریکانو",
        "کاپوچینو",
        "کاپو",
        "موکا",
        "ماکیاتو",
    )
    if any(key in lowered for key in coffee_keywords):
        return normalized_name, "cafe", "coffee"
    if any(key in lowered for key in ("سالاد", "سزار")):
        return normalized_name, "salad", "salad-types"
    if any(key in lowered for key in ("کلاب", "ساندویچ", "برگر", "گریل")):
        return normalized_name, "sandwich", "club-sandwich"
    return normalized_name, "other", "general"


def _slugify(value, fallback):
    cleaned = re.sub(r"\s+", "-", cstr(value).strip().lower())
    cleaned = re.sub(r"[^a-z0-9\-]+", "", cleaned).strip("-")
    return cleaned or fallback


def _unique_item_slug(base_slug, item_name, fallback_seed):
    candidate = base_slug or f"item-{fallback_seed}"
    if not _has_column("Item", "restaurant_slug"):
        return candidate

    existing = frappe.db.get_value("Item", {"restaurant_slug": candidate}, "name")
    if not existing or existing == item_name:
        return candidate

    suffix_seed = re.sub(r"[^a-z0-9]", "", cstr(fallback_seed).lower())[-6:] or "x"
    candidate = f"{candidate[:120-len(suffix_seed)-1]}-{suffix_seed}"
    existing = frappe.db.get_value("Item", {"restaurant_slug": candidate}, "name")
    if not existing or existing == item_name:
        return candidate

    counter = 1
    while True:
        suffix = f"-{counter}"
        attempt = f"{candidate[: 120 - len(suffix)]}{suffix}"
        existing = frappe.db.get_value("Item", {"restaurant_slug": attempt}, "name")
        if not existing or existing == item_name:
            return attempt
        counter += 1


def organize_imported_items(enable_for_menu=1):
    root = _menu_root_group()
    category_map = {
        "cafe": {"title": "کافه", "slug": "cafe", "sub": {"title": "قهوه", "slug": "coffee"}},
        "salad": {"title": "سالاد", "slug": "salad", "sub": {"title": "انواع سالاد", "slug": "salad-types"}},
        "sandwich": {"title": "ساندویچ", "slug": "sandwich", "sub": {"title": "کلاب و ساندویچ", "slug": "club-sandwich"}},
        "other": {"title": "سایر", "slug": "other", "sub": {"title": "عمومی", "slug": "general"}},
    }

    groups = {}
    for key, config in category_map.items():
        category_name = _ensure_group(
            item_group_name=config["title"],
            parent_item_group=root,
            slug=config["slug"],
            is_subcategory=False,
        )
        subcategory_name = _ensure_group(
            item_group_name=config["sub"]["title"],
            parent_item_group=category_name,
            slug=config["sub"]["slug"],
            is_subcategory=True,
        )
        groups[key] = {"category": category_name, "subcategory": subcategory_name}

    filters = {"disabled": 0}
    if _has_column("Item", "restaurant_external_menu_item_id"):
        filters["restaurant_external_menu_item_id"] = ["!=", ""]
    else:
        filters["item_group"] = "Snapp Imported Items"

    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=[
            "name",
            "item_name",
            "item_code",
            "item_group",
            "standard_rate",
            "restaurant_external_menu_item_id",
            "restaurant_slug",
        ],
        ignore_permissions=True,
        limit_page_length=5000,
    )

    updated = 0
    for row in items:
        normalized_name, category_key, _subcategory_key = _classify_title(row.item_name)
        group_info = groups.get(category_key, groups["other"])
        fallback_slug = f"item-{(row.get('restaurant_external_menu_item_id') or row.item_code or row.name)[:12].lower()}"
        slug_value = _slugify(normalized_name, fallback_slug)
        slug_value = _unique_item_slug(slug_value, row.name, fallback_slug)
        short_desc = {
            "cafe": "نوشیدنی کافه",
            "salad": "سالاد تازه",
            "sandwich": "کلاب و ساندویچ",
            "other": "محصول ویژه رستوران",
        }.get(category_key, "محصول ویژه رستوران")

        updates = {
            "item_group": group_info["subcategory"],
            "item_name": normalized_name,
        }
        if _has_column("Item", "restaurant_enabled"):
            updates["restaurant_enabled"] = cint(enable_for_menu)
        if _has_column("Item", "restaurant_category"):
            updates["restaurant_category"] = group_info["category"]
        if _has_column("Item", "restaurant_subcategory"):
            updates["restaurant_subcategory"] = group_info["subcategory"]
        if _has_column("Item", "restaurant_slug"):
            updates["restaurant_slug"] = slug_value
        if _has_column("Item", "restaurant_short_desc"):
            updates["restaurant_short_desc"] = short_desc
        if _has_column("Item", "restaurant_base_price"):
            updates["restaurant_base_price"] = flt(row.standard_rate or 0)
        if _has_column("Item", "is_sales_item"):
            updates["is_sales_item"] = 1

        frappe.db.set_value("Item", row.name, updates, update_modified=False)
        updated += 1

    frappe.db.commit()
    return {
        "status": "success",
        "items_updated": updated,
        "category_groups": {key: value["category"] for key, value in groups.items()},
        "subcategory_groups": {key: value["subcategory"] for key, value in groups.items()},
    }
