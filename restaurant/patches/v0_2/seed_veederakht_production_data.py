import re

import frappe
from frappe.utils import cint, flt


EXTRA_MENU_ITEMS = [
    {
        "slug": "grilled-chicken-salad-pro",
        "title": "سالاد مرغ گریل پرو",
        "category_slug": "salads",
        "subcategory_slug": "salad-protein",
        "base_price": 1540000,
        "short_desc": "سالاد پروتئینی با مرغ گریل و سبزیجات تازه",
        "nutrition": {"kcal": 365, "protein_g": 38, "carb_g": 11, "fat_g": 17},
        "ingredients": [
            {"name": "کاهو", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.12},
            {"name": "مرغ گریل", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.15, "max_multiplier": 2.5},
            {"name": "خیار", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.05},
            {"name": "پنیر پارمزان", "included": 0, "required": 0, "can_remove": 0, "base_qty": 0.03},
        ],
    },
    {
        "slug": "salmon-green-bowl",
        "title": "بول سالمون و سبزیجات",
        "category_slug": "mains",
        "subcategory_slug": "",
        "base_price": 2380000,
        "short_desc": "سالمون گریل با برنج و سبزیجات بخارپز",
        "nutrition": {"kcal": 520, "protein_g": 35, "carb_g": 42, "fat_g": 23},
        "ingredients": [
            {"name": "سالمون", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.18},
            {"name": "برنج", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.2},
            {"name": "بروکلی", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.08},
        ],
    },
    {
        "slug": "truffle-mushroom-pasta",
        "title": "پاستا قارچ ترافل",
        "category_slug": "pasta",
        "subcategory_slug": "pasta-special",
        "base_price": 1890000,
        "short_desc": "پنه با سس خامه و روغن ترافل",
        "nutrition": {"kcal": 610, "protein_g": 18, "carb_g": 71, "fat_g": 24},
        "ingredients": [
            {"name": "پنه", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.14},
            {"name": "قارچ", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.08},
            {"name": "خامه", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.06},
        ],
    },
    {
        "slug": "berry-cheesecake-cup",
        "title": "چیزکیک بری",
        "category_slug": "desserts",
        "subcategory_slug": "",
        "base_price": 820000,
        "short_desc": "چیزکیک سرو تک نفره با سس بری",
        "nutrition": {"kcal": 340, "protein_g": 7, "carb_g": 27, "fat_g": 22},
        "ingredients": [
            {"name": "پنیر خامه ای", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.05},
            {"name": "سس بری", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.03},
        ],
    },
    {
        "slug": "sparkling-mojito-zero",
        "title": "موهیتو زرو",
        "category_slug": "drinks",
        "subcategory_slug": "drink-cold",
        "base_price": 510000,
        "short_desc": "موهیتو بدون قند با لیمو و نعنا",
        "nutrition": {"kcal": 35, "protein_g": 0, "carb_g": 7, "fat_g": 0},
        "ingredients": [
            {"name": "آب گازدار", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.25},
            {"name": "نعنا", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.01},
            {"name": "آب لیمو", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.02},
        ],
    },
]

COFFEE_MENU_ITEM = {
    "slug": "iced-latte-veederakht",
    "title": "آیس لاته ویدرخت",
    "category_slug": "drinks",
    "subcategory_slug": "drink-cold",
    "base_price": 690000,
    "short_desc": "قهوه سرد با شیر انتخابی و یخ",
    "nutrition": {"kcal": 125, "protein_g": 6, "carb_g": 11, "fat_g": 5},
    "ingredients": [
        {"name": "قهوه", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.03},
        {"name": "شیر", "included": 1, "required": 1, "can_remove": 0, "base_qty": 0.18},
        {"name": "یخ", "included": 1, "required": 0, "can_remove": 1, "base_qty": 0.06},
    ],
}


INGREDIENT_NUTRITION_HINTS = {
    "کاهو": {"kcal": 150, "protein_g": 14, "carb_g": 29, "fat_g": 2},
    "مرغ گریل": {"kcal": 1650, "protein_g": 310, "carb_g": 0, "fat_g": 36},
    "خیار": {"kcal": 160, "protein_g": 7, "carb_g": 36, "fat_g": 1},
    "پنیر پارمزان": {"kcal": 4310, "protein_g": 380, "carb_g": 44, "fat_g": 290},
    "سالمون": {"kcal": 2080, "protein_g": 200, "carb_g": 0, "fat_g": 130},
    "برنج": {"kcal": 1300, "protein_g": 26, "carb_g": 282, "fat_g": 3},
    "بروکلی": {"kcal": 340, "protein_g": 28, "carb_g": 66, "fat_g": 4},
    "پنه": {"kcal": 3570, "protein_g": 125, "carb_g": 722, "fat_g": 16},
    "قارچ": {"kcal": 220, "protein_g": 31, "carb_g": 33, "fat_g": 3},
    "خامه": {"kcal": 3400, "protein_g": 21, "carb_g": 29, "fat_g": 360},
    "پنیر خامه ای": {"kcal": 3420, "protein_g": 61, "carb_g": 43, "fat_g": 340},
    "سس بری": {"kcal": 2230, "protein_g": 4, "carb_g": 580, "fat_g": 3},
    "آب گازدار": {"kcal": 0, "protein_g": 0, "carb_g": 0, "fat_g": 0},
    "نعنا": {"kcal": 440, "protein_g": 33, "carb_g": 86, "fat_g": 7},
    "آب لیمو": {"kcal": 220, "protein_g": 4, "carb_g": 69, "fat_g": 2},
    "قهوه": {"kcal": 20, "protein_g": 2, "carb_g": 3, "fat_g": 0},
    "شیر": {"kcal": 640, "protein_g": 34, "carb_g": 48, "fat_g": 35},
    "یخ": {"kcal": 0, "protein_g": 0, "carb_g": 0, "fat_g": 0},
}

NUTRITION_FIELDS = {
    "kcal": "restaurant_nutrition_kcal",
    "protein_g": "restaurant_nutrition_protein_g",
    "carb_g": "restaurant_nutrition_carb_g",
    "fat_g": "restaurant_nutrition_fat_g",
}


def _slugify(value):
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u0600-\u06FF\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def _item_code(slug):
    return f"REST-{_slugify(slug).replace('-', '_').upper()}"


def _raw_code(name):
    slug = _slugify(name)
    return f"RAW-{slug.replace('-', '_').upper()}"


def _default_company():
    return frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")


def _default_uom():
    for name in ["Kg", "Nos", "Unit", "واحد"]:
        if frappe.db.exists("UOM", name):
            return name
    return frappe.db.get_value("UOM", {}, "name") or "Nos"


def _default_currency(company):
    return frappe.db.get_value("Company", company, "default_currency") or frappe.db.get_single_value("Global Defaults", "default_currency")


def _has_nutrition_field(fieldname):
    return frappe.db.has_column("Item", fieldname)


def _set_nutrition(doc, nutrition_payload):
    changed = False
    for key, fieldname in NUTRITION_FIELDS.items():
        if not _has_nutrition_field(fieldname):
            continue
        next_value = flt((nutrition_payload or {}).get(key) or 0)
        if flt(doc.get(fieldname) or 0) != next_value:
            doc.set(fieldname, next_value)
            changed = True
    return changed


def _estimate_nutrition_from_rows(rows):
    totals = {"kcal": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0}
    for row in rows or []:
        name = (row.get("name") or row.get("ingredient_name") or "").strip()
        if not name:
            continue
        hint = INGREDIENT_NUTRITION_HINTS.get(name)
        if not hint:
            continue
        qty = flt(row.get("base_qty") or 0)
        if qty <= 0:
            continue
        for key in totals:
            totals[key] += flt(hint.get(key) or 0) * qty
    return totals


def _ensure_item_group(slug, fallback="All Item Groups"):
    name = frappe.db.get_value(
        "Item Group",
        {
            "restaurant_slug": slug,
            "restaurant_is_menu_category": 1,
            "restaurant_is_subcategory": 0,
        },
        "name",
    )
    if name:
        return name

    return frappe.db.get_value("Item Group", {"item_group_name": fallback}, "name") or frappe.db.get_value(
        "Item Group", {}, "name"
    )


def _ensure_subcategory_group(slug):
    if not slug:
        return ""

    return frappe.db.get_value(
        "Item Group",
        {
            "restaurant_slug": slug,
            "restaurant_is_menu_category": 1,
            "restaurant_is_subcategory": 1,
        },
        "name",
    )


def _ensure_warehouse(name_hint):
    existing = frappe.db.get_value("Warehouse", {"warehouse_name": name_hint}, "name")
    if existing:
        return existing

    by_name = frappe.db.get_value("Warehouse", name_hint, "name")
    if by_name:
        return by_name

    return frappe.db.get_value("Warehouse", {"is_group": 0}, "name") or frappe.db.get_value("Warehouse", {}, "name")


def _ensure_branch_settings():
    if not frappe.db.exists("DocType", "Restaurant Branch Production Settings"):
        return

    company = _default_company()
    raw_warehouse = _ensure_warehouse("Stores")
    kitchen_wip = _ensure_warehouse("Work In Progress")
    fg_warehouse = _ensure_warehouse("Finished Goods")

    branch = "DEFAULT"
    existing = frappe.db.get_value("Restaurant Branch Production Settings", {"branch": branch}, "name")
    payload = {
        "doctype": "Restaurant Branch Production Settings",
        "branch": branch,
        "company": company,
        "raw_warehouse": raw_warehouse,
        "kitchen_wip_warehouse": kitchen_wip,
        "finished_goods_warehouse": fg_warehouse,
        "pricing_markup_percent": 35,
        "is_active": 1,
    }

    if existing:
        doc = frappe.get_doc("Restaurant Branch Production Settings", existing)
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


def _ensure_raw_ingredient_item(name, company, uom):
    code = _raw_code(name)
    existing = frappe.db.get_value("Item", {"item_code": code}, "name")
    if existing:
        item = frappe.get_doc("Item", existing)
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": code,
                "item_name": name,
                "item_group": _ensure_item_group("restaurant-menu", fallback="All Item Groups"),
                "stock_uom": uom,
                "is_stock_item": 1,
                "is_sales_item": 0,
                "is_purchase_item": 1,
            }
        )

    item.item_name = name
    item.stock_uom = uom
    item.disabled = 0
    item.is_stock_item = 1
    item.is_sales_item = 0
    item.is_purchase_item = 1
    if item.is_new():
        item.insert(ignore_permissions=True)
    else:
        item.save(ignore_permissions=True)

    hint = INGREDIENT_NUTRITION_HINTS.get(name, {})
    if hint and _set_nutrition(item, hint):
        item.save(ignore_permissions=True)

    valuation = flt(item.valuation_rate) or flt(item.standard_rate) or 500000
    if not valuation:
        valuation = 500000

    if not flt(item.standard_rate):
        item.db_set("standard_rate", valuation, update_modified=False)

    if not flt(item.valuation_rate):
        item.db_set("valuation_rate", valuation, update_modified=False)

    item_default = frappe.db.get_value("Item Default", {"parent": item.name, "company": company}, "name")
    if not item_default:
        item.append("item_defaults", {"company": company})
        item.save(ignore_permissions=True)

    return item.name


def _row_multiplier_defaults(row):
    def _get(fieldname):
        if hasattr(row, "get"):
            return row.get(fieldname)
        return getattr(row, fieldname, None)

    def _set(fieldname, value):
        if isinstance(row, dict):
            row[fieldname] = value
        else:
            setattr(row, fieldname, value)

    is_default = cint(_get("is_included_by_default"))
    can_remove = cint(_get("can_remove"))
    is_required = cint(_get("is_required"))

    if not _get("customer_label"):
        _set("customer_label", _get("ingredient_name"))

    if not _get("base_qty"):
        _set("base_qty", 1 if is_default else 0.5)

    if not _get("step_multiplier"):
        _set("step_multiplier", 0.5)

    if not _get("max_multiplier"):
        _set("max_multiplier", 3)

    if is_required or (is_default and not can_remove):
        _set("is_required", 1)
        if flt(_get("min_multiplier")) < 1:
            _set("min_multiplier", 1)
        if _get("is_editable_qty") in (None, ""):
            _set("is_editable_qty", 0 if not can_remove else 1)
    else:
        if _get("min_multiplier") in (None, ""):
            _set("min_multiplier", 0)
        if _get("is_editable_qty") in (None, ""):
            _set("is_editable_qty", 1)


def _ensure_menu_item(payload, company, uom):
    slug = _slugify(payload["slug"])
    code = _item_code(slug)

    existing = frappe.db.get_value("Item", {"restaurant_slug": slug}, "name")
    if not existing:
        existing = frappe.db.get_value("Item", {"item_code": code}, "name")

    group = _ensure_subcategory_group(payload.get("subcategory_slug")) or _ensure_item_group(payload["category_slug"])

    if existing:
        item = frappe.get_doc("Item", existing)
    else:
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": code,
                "item_name": payload["title"],
                "item_group": group,
                "stock_uom": uom,
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
            }
        )

    item.item_name = payload["title"]
    item.item_group = group
    item.stock_uom = uom
    item.standard_rate = flt(payload.get("base_price") or 0)
    item.restaurant_enabled = 1
    item.restaurant_slug = slug
    item.restaurant_short_desc = payload.get("short_desc") or ""
    item.restaurant_long_desc = payload.get("long_desc") or payload.get("short_desc") or ""
    item.restaurant_base_price = flt(payload.get("base_price") or 0)
    item.restaurant_is_featured = 0
    item.restaurant_sort_order = 400
    item.restaurant_category = _ensure_item_group(payload["category_slug"])
    item.restaurant_subcategory = _ensure_subcategory_group(payload.get("subcategory_slug")) or ""
    item.restaurant_branch = "DEFAULT"
    item.restaurant_allow_customization = 1
    item.restaurant_recipe_yield_qty = 1
    item.restaurant_recipe_uom = uom

    ingredient_rows = []
    for idx, ingredient in enumerate(payload.get("ingredients") or [], start=1):
        ingredient_item = _ensure_raw_ingredient_item(ingredient["name"], company, uom)
        row = {
            "ingredient_name": ingredient["name"],
            "customer_label": ingredient["name"],
            "ingredient_item": ingredient_item,
            "qty_uom": uom,
            "base_qty": flt(ingredient.get("base_qty") or 1),
            "is_included_by_default": cint(ingredient.get("included", 1)),
            "can_remove": cint(ingredient.get("can_remove", 1)),
            "is_required": cint(ingredient.get("required", 0)),
            "is_editable_qty": 1,
            "min_multiplier": 1 if cint(ingredient.get("required", 0)) else 0,
            "max_multiplier": flt(ingredient.get("max_multiplier") or 3),
            "step_multiplier": 0.5,
            "extra_when_added": 0,
            "sort_order": idx,
        }
        _row_multiplier_defaults(row)
        ingredient_rows.append(row)

    item.set("restaurant_ingredients", ingredient_rows)
    nutrition = payload.get("nutrition") or _estimate_nutrition_from_rows(payload.get("ingredients") or [])
    _set_nutrition(item, nutrition)

    if item.is_new():
        item.insert(ignore_permissions=True)
    else:
        item.save(ignore_permissions=True)

    item_default = frappe.db.get_value("Item Default", {"parent": item.name, "company": company}, "name")
    if not item_default:
        item.append("item_defaults", {"company": company})
        item.save(ignore_permissions=True)

    return item.name


def _ensure_ingredient_links_and_constraints(company, uom):
    def _ing_get(ing, fieldname):
        if hasattr(ing, "get"):
            return ing.get(fieldname)
        return getattr(ing, fieldname, None)

    def _ing_set(ing, fieldname, value):
        if isinstance(ing, dict):
            ing[fieldname] = value
        else:
            setattr(ing, fieldname, value)

    menu_items = frappe.get_all(
        "Item",
        fields=["name", "restaurant_slug", "item_name", "stock_uom"],
        filters={"restaurant_enabled": 1, "disabled": 0},
        ignore_permissions=True,
        limit_page_length=200,
    )

    for row in menu_items:
        doc = frappe.get_doc("Item", row.name)
        changed = False

        rows = list(doc.restaurant_ingredients or [])
        if row.restaurant_slug == "protein-caesar-salad":
            keys = {_ing_get(d, "ingredient_name") for d in rows}
            if "خیار" not in keys:
                rows.append(
                    {
                        "ingredient_name": "خیار",
                        "is_included_by_default": 1,
                        "can_remove": 1,
                        "extra_when_added": 0,
                        "sort_order": len(rows) + 1,
                    }
                )
                changed = True

        for idx, ing in enumerate(rows, start=1):
            ingredient_name = _ing_get(ing, "ingredient_name")
            if not ingredient_name:
                continue

            ingredient_item = _ensure_raw_ingredient_item(ingredient_name, company, uom)
            if _ing_get(ing, "ingredient_item") != ingredient_item:
                _ing_set(ing, "ingredient_item", ingredient_item)
                changed = True

            if not _ing_get(ing, "customer_label"):
                _ing_set(ing, "customer_label", ingredient_name)
                changed = True

            if not _ing_get(ing, "qty_uom"):
                _ing_set(ing, "qty_uom", doc.stock_uom or uom)
                changed = True

            if not flt(_ing_get(ing, "base_qty")):
                _ing_set(ing, "base_qty", 1 if cint(_ing_get(ing, "is_included_by_default")) else 0.5)
                changed = True

            before = {
                "is_required": cint(_ing_get(ing, "is_required")),
                "min_multiplier": flt(_ing_get(ing, "min_multiplier")),
                "max_multiplier": flt(_ing_get(ing, "max_multiplier")),
                "step_multiplier": flt(_ing_get(ing, "step_multiplier")),
                "is_editable_qty": cint(_ing_get(ing, "is_editable_qty")),
            }

            _row_multiplier_defaults(ing)
            if row.restaurant_slug == "protein-caesar-salad" and idx == 1:
                _ing_set(ing, "is_required", 1)
                _ing_set(ing, "can_remove", 0)
                _ing_set(ing, "min_multiplier", 1)
                _ing_set(ing, "max_multiplier", max(flt(_ing_get(ing, "max_multiplier")), 2))
                _ing_set(ing, "is_editable_qty", 1)

            after = {
                "is_required": cint(_ing_get(ing, "is_required")),
                "min_multiplier": flt(_ing_get(ing, "min_multiplier")),
                "max_multiplier": flt(_ing_get(ing, "max_multiplier")),
                "step_multiplier": flt(_ing_get(ing, "step_multiplier")),
                "is_editable_qty": cint(_ing_get(ing, "is_editable_qty")),
            }
            if before != after:
                changed = True

        if changed:
            doc.set("restaurant_ingredients", rows)
            doc.restaurant_allow_customization = 1
            doc.restaurant_recipe_yield_qty = flt(doc.restaurant_recipe_yield_qty or 1)
            doc.restaurant_recipe_uom = doc.stock_uom or uom
            if not flt(doc.get("restaurant_nutrition_kcal") or 0):
                _set_nutrition(doc, _estimate_nutrition_from_rows(rows))
            doc.save(ignore_permissions=True)


def _backfill_menu_item_nutrition(uom):
    if not _has_nutrition_field("restaurant_nutrition_kcal"):
        return

    items = frappe.get_all(
        "Item",
        fields=["name"],
        filters={"restaurant_enabled": 1, "disabled": 0},
        ignore_permissions=True,
        limit_page_length=500,
    )

    for row in items:
        doc = frappe.get_doc("Item", row.name)
        if flt(doc.get("restaurant_nutrition_kcal") or 0) > 0:
            continue

        normalized_rows = []
        for ing in doc.restaurant_ingredients or []:
            normalized_rows.append(
                {
                    "name": ing.ingredient_name,
                    "base_qty": flt(ing.get("base_qty") or 0),
                }
            )

        if not normalized_rows:
            continue

        nutrition = _estimate_nutrition_from_rows(normalized_rows)
        if _set_nutrition(doc, nutrition):
            if not doc.get("restaurant_recipe_uom"):
                doc.restaurant_recipe_uom = doc.stock_uom or uom
            if not flt(doc.get("restaurant_recipe_yield_qty") or 0):
                doc.restaurant_recipe_yield_qty = 1
            doc.save(ignore_permissions=True)


def _ensure_bom_template(item_name, company, currency):
    item = frappe.get_doc("Item", item_name)
    existing_template = item.get("restaurant_bom_template")
    if existing_template and frappe.db.exists("BOM", existing_template):
        return existing_template

    existing_default = frappe.db.get_value(
        "BOM",
        {
            "item": item.item_code,
            "is_default": 1,
            "is_active": 1,
            "docstatus": 1,
        },
        "name",
    )
    if existing_default:
        item.db_set("restaurant_bom_template", existing_default, update_modified=False)
        return existing_default

    recipe_uom = item.stock_uom or _default_uom()

    rows = []
    for ing in item.restaurant_ingredients or []:
        if not ing.get("ingredient_item"):
            continue
        include = cint(ing.get("is_included_by_default"))
        if not include:
            continue

        qty = flt(ing.get("base_qty") or 0)
        if qty <= 0:
            qty = 1

        rate = flt(frappe.db.get_value("Item", ing.ingredient_item, "valuation_rate") or 0)
        if not rate:
            rate = flt(frappe.db.get_value("Item", ing.ingredient_item, "standard_rate") or 0)

        rows.append(
            {
                "item_code": ing.ingredient_item,
                "qty": qty,
                "uom": ing.get("qty_uom") or recipe_uom,
                "rate": rate,
            }
        )

    if not rows:
        return ""

    bom = frappe.get_doc(
        {
            "doctype": "BOM",
            "item": item.item_code,
            "company": company,
            "currency": currency,
            "conversion_rate": 1,
            "quantity": flt(item.get("restaurant_recipe_yield_qty") or 1),
            "is_active": 1,
            "is_default": 1,
            "items": rows,
        }
    )
    bom.insert(ignore_permissions=True)
    bom.submit()

    item.db_set("restaurant_bom_template", bom.name, update_modified=False)
    return bom.name


def _ensure_modifier_recipe_multipliers():
    groups = frappe.get_all(
        "Restaurant Modifier Group",
        fields=["name", "title"],
        filters={"is_active": 1},
        ignore_permissions=True,
    )

    for group in groups:
        if "سایز" not in (group.title or ""):
            continue

        doc = frappe.get_doc("Restaurant Modifier Group", group.name)
        changed = False
        for option in doc.options or []:
            title = (option.option_name or "").strip()
            next_value = flt(option.get("recipe_multiplier") or 1)
            if "کوچک" in title:
                next_value = 0.8
            elif "بزرگ" in title:
                next_value = 1.5
            elif "معمولی" in title or "استاندارد" in title:
                next_value = 1

            if flt(option.get("recipe_multiplier") or 1) != next_value:
                option.recipe_multiplier = next_value
                changed = True

        if changed:
            doc.save(ignore_permissions=True)


def _ensure_modifier_group(title, selection_mode, required, min_select, max_select, options, sort_order=0):
    existing = frappe.db.get_value("Restaurant Modifier Group", {"title": title}, "name")
    if existing:
        doc = frappe.get_doc("Restaurant Modifier Group", existing)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Restaurant Modifier Group",
                "title": title,
            }
        )

    doc.title = title
    doc.selection_mode = selection_mode
    doc.required = cint(required)
    doc.min_select = cint(min_select)
    doc.max_select = cint(max_select)
    doc.sort_order = cint(sort_order)
    doc.is_active = 1
    doc.set("options", [])
    for row in options or []:
        doc.append(
            "options",
            {
                "option_name": row.get("option_name"),
                "price_delta": flt(row.get("price_delta") or 0),
                "is_default": cint(row.get("is_default")),
                "sort_order": cint(row.get("sort_order") or 0),
                "recipe_multiplier": flt(row.get("recipe_multiplier") or 1),
            },
        )

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    return doc.name


def _is_coffee_item(doc):
    slug = (doc.get("restaurant_slug") or "").strip().lower()
    text = " ".join(
        [
            (doc.get("item_name") or "").lower(),
            (doc.get("restaurant_short_desc") or "").lower(),
            (doc.get("restaurant_long_desc") or "").lower(),
            slug,
        ]
    )
    coffee_keywords = ["coffee", "latte", "espresso", "americano", "mocha", "قهوه", "لاته", "اسپرسو", "کاپوچینو"]
    return any(keyword in text for keyword in coffee_keywords)


def _ensure_item_modifier_link(item_doc, group_name, required, min_select, max_select, sort_order):
    links = list(item_doc.get("restaurant_modifier_groups") or [])
    for row in links:
        if row.modifier_group == group_name:
            changed = False
            if cint(row.required) != cint(required):
                row.required = cint(required)
                changed = True
            if cint(row.min_select) != cint(min_select):
                row.min_select = cint(min_select)
                changed = True
            if cint(row.max_select) != cint(max_select):
                row.max_select = cint(max_select)
                changed = True
            if cint(row.sort_order) != cint(sort_order):
                row.sort_order = cint(sort_order)
                changed = True
            return changed

    item_doc.append(
        "restaurant_modifier_groups",
        {
            "modifier_group": group_name,
            "required": cint(required),
            "min_select": cint(min_select),
            "max_select": cint(max_select),
            "sort_order": cint(sort_order),
        },
    )
    return True


def _ensure_service_and_milk_modifiers():
    milk_group = _ensure_modifier_group(
        title="انتخاب نوع شیر",
        selection_mode="single",
        required=0,
        min_select=0,
        max_select=1,
        sort_order=120,
        options=[
            {"option_name": "شیر معمولی", "price_delta": 0, "is_default": 1, "sort_order": 1, "recipe_multiplier": 1},
            {"option_name": "شیر بدون لاکتوز", "price_delta": 70000, "is_default": 0, "sort_order": 2, "recipe_multiplier": 1},
            {"option_name": "شیر بادام", "price_delta": 120000, "is_default": 0, "sort_order": 3, "recipe_multiplier": 1},
            {"option_name": "شیر جو دوسر", "price_delta": 110000, "is_default": 0, "sort_order": 4, "recipe_multiplier": 1},
        ],
    )

    service_group = _ensure_modifier_group(
        title="افزودنی سرو (چنگال، سس و ...)",
        selection_mode="multi",
        required=0,
        min_select=0,
        max_select=6,
        sort_order=121,
        options=[
            {"option_name": "چنگال", "price_delta": 15000, "is_default": 0, "sort_order": 1, "recipe_multiplier": 1},
            {"option_name": "قاشق", "price_delta": 15000, "is_default": 0, "sort_order": 2, "recipe_multiplier": 1},
            {"option_name": "دستمال اضافه", "price_delta": 10000, "is_default": 0, "sort_order": 3, "recipe_multiplier": 1},
            {"option_name": "سس کچاپ", "price_delta": 25000, "is_default": 0, "sort_order": 4, "recipe_multiplier": 1},
            {"option_name": "سس سیر", "price_delta": 30000, "is_default": 0, "sort_order": 5, "recipe_multiplier": 1},
            {"option_name": "سس خردل", "price_delta": 25000, "is_default": 0, "sort_order": 6, "recipe_multiplier": 1},
        ],
    )

    rows = frappe.get_all(
        "Item",
        fields=["name"],
        filters={"restaurant_enabled": 1, "disabled": 0},
        ignore_permissions=True,
        limit_page_length=500,
    )

    for row in rows:
        doc = frappe.get_doc("Item", row.name)
        changed = False

        changed = _ensure_item_modifier_link(
            doc, service_group, required=0, min_select=0, max_select=6, sort_order=90
        ) or changed

        if _is_coffee_item(doc):
            changed = _ensure_item_modifier_link(
                doc, milk_group, required=0, min_select=0, max_select=1, sort_order=80
            ) or changed

        if changed:
            doc.save(ignore_permissions=True)


def execute():
    if frappe.local.site != "veederakht":
        return

    if not frappe.db.has_column("Item", "restaurant_enabled"):
        return

    company = _default_company()
    if not company:
        return

    uom = _default_uom()
    currency = _default_currency(company)

    _ensure_branch_settings()
    _ensure_modifier_recipe_multipliers()
    _ensure_ingredient_links_and_constraints(company, uom)

    current_count = frappe.db.count("Item", {"restaurant_enabled": 1, "disabled": 0})

    if current_count < 24:
        for payload in EXTRA_MENU_ITEMS:
            _ensure_menu_item(payload, company, uom)
            current_count = frappe.db.count("Item", {"restaurant_enabled": 1, "disabled": 0})
            if current_count >= 24:
                break

    _ensure_menu_item(COFFEE_MENU_ITEM, company, uom)
    _ensure_service_and_milk_modifiers()

    menu_items = frappe.get_all(
        "Item",
        fields=["name", "stock_uom", "restaurant_enabled", "disabled"],
        filters={"restaurant_enabled": 1, "disabled": 0},
        ignore_permissions=True,
        limit_page_length=500,
    )

    for row in menu_items:
        item = frappe.get_doc("Item", row.name)
        changed = False

        if not flt(item.get("restaurant_recipe_yield_qty")):
            item.restaurant_recipe_yield_qty = 1
            changed = True
        if not item.get("restaurant_recipe_uom"):
            item.restaurant_recipe_uom = item.stock_uom or uom
            changed = True
        if cint(item.get("restaurant_allow_customization")) != 1:
            item.restaurant_allow_customization = 1
            changed = True

        if changed:
            item.save(ignore_permissions=True)

        _ensure_bom_template(row.name, company, currency)

    _backfill_menu_item_nutrition(uom)

    frappe.clear_cache()
    frappe.db.commit()
