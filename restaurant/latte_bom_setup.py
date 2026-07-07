import re

import frappe
from frappe.utils import cint, flt


DEFAULT_LATTE_ITEM_CODE = "SNP-F905B10AA0"

SIZE_PROFILES = {
    "small": {"label": "کوچک", "espresso_qty": 1, "milk_qty": 0.18},
    "medium": {"label": "متوسط", "espresso_qty": 1, "milk_qty": 0.22},
    "large": {"label": "بزرگ", "espresso_qty": 2, "milk_qty": 0.28},
}

RAW_ITEMS = {
    "espresso": {"item_code": "RAW-LATTE_ESPRESSO_SHOT", "item_name": "شات اسپرسو لاته", "stock_uom": "عدد", "rate": 45000},
    "milk_full": {"item_code": "RAW-LATTE_MILK_FULL_FAT", "item_name": "شیر پرچرب لاته", "stock_uom": "Litre", "rate": 180000},
    "milk_low": {"item_code": "RAW-LATTE_MILK_LOW_FAT", "item_name": "شیر کم چرب لاته", "stock_uom": "Litre", "rate": 180000},
    "milk_almond": {"item_code": "RAW-LATTE_MILK_ALMOND", "item_name": "شیر بادام لاته", "stock_uom": "Litre", "rate": 240000},
    "syrup_vanilla": {"item_code": "RAW-SYRUP_VANILLA", "item_name": "سیروپ وانیل", "stock_uom": "Litre", "rate": 260000},
    "syrup_caramel": {"item_code": "RAW-SYRUP_CARAMEL", "item_name": "سیروپ کارامل", "stock_uom": "Litre", "rate": 280000},
    "syrup_hazelnut": {"item_code": "RAW-SYRUP_HAZELNUT", "item_name": "سیروپ فندق", "stock_uom": "Litre", "rate": 290000},
}


def _slugify(value):
    cleaned = re.sub(r"[^a-zA-Z0-9\u0600-\u06FF\s_-]", "", (value or "").strip().lower())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def _pick_uom(preferred, fallback="عدد"):
    for candidate in preferred:
        if candidate and frappe.db.exists("UOM", candidate):
            return candidate
    return fallback


def _default_company():
    return frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")


def _default_currency(company):
    return (
        frappe.db.get_value("Company", company, "default_currency")
        or frappe.db.get_single_value("Global Defaults", "default_currency")
        or "IRR"
    )


def _ingredient_group():
    for group_name in ["مواد اولیه", "Raw Material", "مواد اوليه"]:
        if frappe.db.exists("Item Group", group_name):
            return group_name
    return frappe.db.get_value("Item Group", {"is_group": 0}, "name") or frappe.db.get_value("Item Group", {}, "name")


def _ensure_item_default(item_doc, company):
    existing = frappe.db.get_value("Item Default", {"parent": item_doc.name, "company": company}, "name")
    if not existing:
        item_doc.append("item_defaults", {"company": company})


def _ensure_raw_item(item_payload, company):
    item_code = (item_payload.get("item_code") or "").strip()
    existing_name = frappe.db.get_value("Item", {"item_code": item_code}, "name")
    stock_uom = _pick_uom([item_payload.get("stock_uom")], fallback=item_payload.get("stock_uom") or "عدد")

    if existing_name:
        item_doc = frappe.get_doc("Item", existing_name)
    else:
        item_doc = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_payload.get("item_name"),
                "item_group": _ingredient_group(),
                "stock_uom": stock_uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
            }
        )

    item_doc.item_name = item_payload.get("item_name")
    item_doc.item_group = _ingredient_group()
    item_doc.stock_uom = stock_uom
    item_doc.disabled = 0
    item_doc.is_stock_item = 1
    item_doc.is_sales_item = 0
    item_doc.is_purchase_item = 1
    if frappe.db.has_column("Item", "include_item_in_manufacturing"):
        item_doc.include_item_in_manufacturing = 1
    if not flt(item_doc.standard_rate):
        item_doc.standard_rate = flt(item_payload.get("rate") or 0)
    if not flt(item_doc.valuation_rate):
        item_doc.valuation_rate = flt(item_payload.get("rate") or 0)

    _ensure_item_default(item_doc, company)

    if item_doc.is_new():
        item_doc.insert(ignore_permissions=True)
    else:
        item_doc.save(ignore_permissions=True)
    return item_doc


def _find_latte_item(item_code=None):
    target_code = (item_code or DEFAULT_LATTE_ITEM_CODE).strip()
    if target_code and frappe.db.exists("Item", target_code):
        return frappe.get_doc("Item", target_code)

    rows = frappe.get_all(
        "Item",
        filters={"disabled": 0, "item_name": ["like", "%لاته%"]},
        fields=["name", "item_name"],
        order_by="modified desc",
        ignore_permissions=True,
        limit_page_length=20,
    )
    if rows:
        return frappe.get_doc("Item", rows[0].name)

    frappe.throw("No latte item was found.")


def _ensure_modifier_group(title, selection_mode, required, min_select, max_select, options):
    existing = frappe.db.get_value("Restaurant Modifier Group", {"title": title}, "name")
    if existing:
        group_doc = frappe.get_doc("Restaurant Modifier Group", existing)
    else:
        group_doc = frappe.get_doc({"doctype": "Restaurant Modifier Group", "title": title})

    group_doc.title = title
    group_doc.selection_mode = selection_mode
    group_doc.required = cint(required)
    group_doc.min_select = cint(min_select)
    group_doc.max_select = cint(max_select)
    group_doc.is_active = 1

    existing_option_map = {(row.get("option_name") or "").strip(): row for row in group_doc.get("options") or []}
    kept_names = set()
    for index, option in enumerate(options, start=1):
        option_name = (option.get("option_name") or "").strip()
        if not option_name:
            continue
        kept_names.add(option_name)
        row = existing_option_map.get(option_name)
        if not row:
            row = group_doc.append("options", {})
        row.option_name = option_name
        row.action_type = (option.get("action_type") or "add_on").strip() or "add_on"
        row.option_item = (option.get("option_item") or "").strip()
        row.alternative_bom = (option.get("alternative_bom") or "").strip()
        row.option_qty = flt(option.get("option_qty") or 1)
        row.price_delta = flt(option.get("price_delta") or 0)
        row.recipe_multiplier = flt(option.get("recipe_multiplier") or 1)
        row.is_default = cint(option.get("is_default") or 0)
        row.sort_order = cint(option.get("sort_order") or index)
        row.is_active = cint(option.get("is_active") if option.get("is_active") not in ("", None) else 1)

    for row in group_doc.get("options") or []:
        option_name = (row.get("option_name") or "").strip()
        if option_name and option_name not in kept_names:
            row.is_active = 0

    if group_doc.is_new():
        group_doc.insert(ignore_permissions=True)
    else:
        group_doc.save(ignore_permissions=True)

    return group_doc


def _resolve_variant_bom(item_code, preferred_bom=None, use_default=False):
    preferred_bom = (preferred_bom or "").strip()
    if preferred_bom and frappe.db.exists("BOM", preferred_bom):
        bom_doc = frappe.get_doc("BOM", preferred_bom)
        if bom_doc.item == item_code and bom_doc.docstatus != 2:
            return bom_doc

    if use_default:
        default_bom = frappe.db.get_value(
            "BOM",
            {"item": item_code, "is_default": 1, "docstatus": ["!=", 2]},
            "name",
        )
        if default_bom:
            return frappe.get_doc("BOM", default_bom)

    return frappe.get_doc(
        {
            "doctype": "BOM",
            "item": item_code,
            "is_default": 0,
            "is_active": 1,
            "quantity": 1,
        }
    )


def _apply_bom_components(bom_doc, variant_profile, raw_items):
    component_rows = [
        {
            "item_code": raw_items["espresso"].item_code,
            "qty": flt(variant_profile["espresso_qty"]),
            "uom": raw_items["espresso"].stock_uom,
            "rate": flt(raw_items["espresso"].standard_rate or raw_items["espresso"].valuation_rate or 0),
            "restaurant_customer_label": "اسپرسو",
            "restaurant_is_included_by_default": 1,
            "restaurant_can_remove": 0,
            "restaurant_is_required": 1,
            "restaurant_is_editable_qty": 0,
            "restaurant_min_multiplier": 1,
            "restaurant_max_multiplier": 1,
            "restaurant_step_multiplier": 1,
            "restaurant_extra_when_added": 0,
            "allow_alternative_item": 0,
        },
        {
            "item_code": raw_items["milk_full"].item_code,
            "qty": flt(variant_profile["milk_qty"]),
            "uom": raw_items["milk_full"].stock_uom,
            "rate": flt(raw_items["milk_full"].standard_rate or raw_items["milk_full"].valuation_rate or 0),
            "restaurant_customer_label": "شیر",
            "restaurant_is_included_by_default": 1,
            "restaurant_can_remove": 0,
            "restaurant_is_required": 1,
            "restaurant_is_editable_qty": 0,
            "restaurant_min_multiplier": 1,
            "restaurant_max_multiplier": 1,
            "restaurant_step_multiplier": 0.1,
            "restaurant_extra_when_added": 0,
            "allow_alternative_item": 1,
        },
    ]

    bom_doc.set("items", [])
    for row_payload in component_rows:
        row = bom_doc.append("items", {})
        for key, value in row_payload.items():
            if hasattr(row, key):
                setattr(row, key, value)


def _apply_bom_modifier_groups(bom_doc, size_group_name, syrup_group_name):
    bom_doc.set("restaurant_modifier_rows", [])
    bom_doc.append(
        "restaurant_modifier_rows",
        {
            "modifier_group": size_group_name,
            "required": 1,
            "min_select": 1,
            "max_select": 1,
            "sort_order": 1,
            "is_active": 1,
        },
    )
    bom_doc.append(
        "restaurant_modifier_rows",
        {
            "modifier_group": syrup_group_name,
            "required": 0,
            "min_select": 0,
            "max_select": 2,
            "sort_order": 2,
            "is_active": 1,
        },
    )


def _save_bom(bom_doc, item_code, company, currency, is_default):
    bom_doc.item = item_code
    bom_doc.company = company
    bom_doc.currency = currency
    bom_doc.conversion_rate = 1
    bom_doc.quantity = 1
    bom_doc.is_active = 1
    bom_doc.is_default = cint(is_default)
    if hasattr(bom_doc, "restaurant_menu_item_ref"):
        bom_doc.restaurant_menu_item_ref = item_code

    if bom_doc.is_new():
        bom_doc.insert(ignore_permissions=True)
        bom_doc.submit()
        return bom_doc

    if bom_doc.docstatus == 0:
        bom_doc.save(ignore_permissions=True)
        bom_doc.submit()
        return bom_doc

    bom_doc.flags.ignore_validate_update_after_submit = True
    bom_doc.save(ignore_permissions=True)
    return bom_doc


def _ensure_item_alternative(base_item_code, alternative_item_code):
    if not base_item_code or not alternative_item_code:
        return
    if not frappe.db.exists("Item", base_item_code) or not frappe.db.exists("Item", alternative_item_code):
        return
    if frappe.db.exists(
        "Item Alternative",
        {"item_code": base_item_code, "alternative_item_code": alternative_item_code},
    ):
        return
    doc = frappe.get_doc(
        {
            "doctype": "Item Alternative",
            "item_code": base_item_code,
            "alternative_item_code": alternative_item_code,
            "two_way": 0,
        }
    )
    doc.insert(ignore_permissions=True)


def setup_latte_bom(item_code=None):
    latte_item = _find_latte_item(item_code=item_code)
    company = _default_company()
    if not company:
        frappe.throw("Default company is required.")
    currency = _default_currency(company)

    raw_items = {key: _ensure_raw_item(value, company) for key, value in RAW_ITEMS.items()}

    syrup_group = _ensure_modifier_group(
        title="لاته - سیروپ",
        selection_mode="multi",
        required=0,
        min_select=0,
        max_select=2,
        options=[
            {"option_name": "وانیل", "action_type": "add_on", "option_item": raw_items["syrup_vanilla"].item_code, "option_qty": 0.02, "price_delta": 45000, "is_default": 0, "sort_order": 1, "is_active": 1},
            {"option_name": "کارامل", "action_type": "add_on", "option_item": raw_items["syrup_caramel"].item_code, "option_qty": 0.02, "price_delta": 50000, "is_default": 0, "sort_order": 2, "is_active": 1},
            {"option_name": "فندق", "action_type": "add_on", "option_item": raw_items["syrup_hazelnut"].item_code, "option_qty": 0.02, "price_delta": 55000, "is_default": 0, "sort_order": 3, "is_active": 1},
        ],
    )

    size_group = _ensure_modifier_group(
        title="لاته - اندازه",
        selection_mode="single",
        required=1,
        min_select=1,
        max_select=1,
        options=[
            {"option_name": SIZE_PROFILES["small"]["label"], "action_type": "bom_variant", "is_default": 0, "sort_order": 1, "is_active": 1},
            {"option_name": SIZE_PROFILES["medium"]["label"], "action_type": "bom_variant", "is_default": 1, "sort_order": 2, "is_active": 1},
            {"option_name": SIZE_PROFILES["large"]["label"], "action_type": "bom_variant", "is_default": 0, "sort_order": 3, "is_active": 1},
        ],
    )

    option_by_name = {(row.get("option_name") or "").strip(): row for row in (size_group.get("options") or [])}
    created_boms = {}
    for variant_key, profile in SIZE_PROFILES.items():
        option_row = option_by_name.get(profile["label"])
        preferred_bom = option_row.get("alternative_bom") if option_row else ""
        bom_doc = _resolve_variant_bom(
            item_code=latte_item.item_code,
            preferred_bom=preferred_bom,
            use_default=(variant_key == "medium"),
        )
        _apply_bom_components(bom_doc, profile, raw_items)
        _apply_bom_modifier_groups(bom_doc, size_group.name, syrup_group.name)
        bom_doc = _save_bom(
            bom_doc=bom_doc,
            item_code=latte_item.item_code,
            company=company,
            currency=currency,
            is_default=(variant_key == "medium"),
        )
        created_boms[variant_key] = bom_doc.name

    size_group = frappe.get_doc("Restaurant Modifier Group", size_group.name)
    for row in size_group.get("options") or []:
        option_name = (row.get("option_name") or "").strip()
        if option_name == SIZE_PROFILES["small"]["label"]:
            row.action_type = "bom_variant"
            row.alternative_bom = created_boms["small"]
        elif option_name == SIZE_PROFILES["medium"]["label"]:
            row.action_type = "bom_variant"
            row.alternative_bom = created_boms["medium"]
        elif option_name == SIZE_PROFILES["large"]["label"]:
            row.action_type = "bom_variant"
            row.alternative_bom = created_boms["large"]
    size_group.save(ignore_permissions=True)

    _ensure_item_alternative(raw_items["milk_full"].item_code, raw_items["milk_low"].item_code)
    _ensure_item_alternative(raw_items["milk_full"].item_code, raw_items["milk_almond"].item_code)

    if frappe.db.has_column("Item", "default_bom"):
        frappe.db.set_value("Item", latte_item.name, "default_bom", "", update_modified=False)

    frappe.db.commit()
    return {
        "item_code": latte_item.item_code,
        "item_name": latte_item.item_name,
        "size_group": size_group.name,
        "syrup_group": syrup_group.name,
        "bom_small": created_boms["small"],
        "bom_medium": created_boms["medium"],
        "bom_large": created_boms["large"],
        "milk_base": raw_items["milk_full"].item_code,
        "milk_alternatives": [raw_items["milk_low"].item_code, raw_items["milk_almond"].item_code],
    }
