import re
from typing import Dict, List, Optional

import frappe
from frappe.utils import cint, flt

ROOT_ITEM_GROUP = "Restaurant Menu"

ORDER_STATUS_OPTIONS = "new\nconfirmed\npreparing\nready\ndelivered\ncancelled"
ORDER_TYPE_OPTIONS = "dine_in\ntakeaway\ndelivery"


CUSTOM_FIELDS = {
    "Item Group": [
        {
            "fieldname": "restaurant_is_menu_category",
            "label": "Restaurant Is Menu Category",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "image",
        },
        {
            "fieldname": "restaurant_is_subcategory",
            "label": "Restaurant Is Subcategory",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_is_menu_category",
        },
        {
            "fieldname": "restaurant_slug",
            "label": "Restaurant Slug",
            "fieldtype": "Data",
            "insert_after": "restaurant_is_subcategory",
            "unique": 1,
        },
        {
            "fieldname": "restaurant_sort_order",
            "label": "Restaurant Sort Order",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "restaurant_slug",
        },
        {
            "fieldname": "restaurant_description",
            "label": "Restaurant Description",
            "fieldtype": "Small Text",
            "insert_after": "restaurant_sort_order",
        },
        {
            "fieldname": "restaurant_active",
            "label": "Restaurant Active",
            "fieldtype": "Check",
            "default": "1",
            "insert_after": "restaurant_description",
        },
    ],
    "Item": [
        {
            "fieldname": "restaurant_enabled",
            "label": "Restaurant Enabled",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_slug",
            "label": "Restaurant Slug",
            "fieldtype": "Data",
            "insert_after": "restaurant_enabled",
            "unique": 1,
        },
        {
            "fieldname": "restaurant_category",
            "label": "Restaurant Category",
            "fieldtype": "Link",
            "options": "Item Group",
            "insert_after": "restaurant_slug",
        },
        {
            "fieldname": "restaurant_subcategory",
            "label": "Restaurant Subcategory",
            "fieldtype": "Link",
            "options": "Item Group",
            "insert_after": "restaurant_category",
        },
        {
            "fieldname": "restaurant_short_desc",
            "label": "Restaurant Short Description",
            "fieldtype": "Small Text",
            "insert_after": "restaurant_subcategory",
        },
        {
            "fieldname": "restaurant_long_desc",
            "label": "Restaurant Long Description",
            "fieldtype": "Text Editor",
            "insert_after": "restaurant_short_desc",
        },
        {
            "fieldname": "restaurant_base_price",
            "label": "Restaurant Base Price",
            "fieldtype": "Currency",
            "insert_after": "restaurant_long_desc",
        },
        {
            "fieldname": "restaurant_is_featured",
            "label": "Restaurant Is Featured",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "restaurant_base_price",
        },
        {
            "fieldname": "restaurant_sort_order",
            "label": "Restaurant Sort Order",
            "fieldtype": "Int",
            "default": "0",
            "insert_after": "restaurant_is_featured",
        },
        {
            "fieldname": "restaurant_allergen_tags",
            "label": "Restaurant Allergen Tags",
            "fieldtype": "Small Text",
            "insert_after": "restaurant_sort_order",
        },
        {
            "fieldname": "restaurant_branch",
            "label": "Restaurant Branch",
            "fieldtype": "Data",
            "insert_after": "restaurant_allergen_tags",
        },
        {
            "fieldname": "restaurant_prep_time_mins",
            "label": "Restaurant Prep Time (Mins)",
            "fieldtype": "Int",
            "default": "20",
            "insert_after": "restaurant_branch",
        },
        {
            "fieldname": "restaurant_ingredients",
            "label": "Restaurant Ingredients",
            "fieldtype": "Table",
            "options": "Restaurant Item Ingredient",
            "insert_after": "restaurant_prep_time_mins",
        },
        {
            "fieldname": "restaurant_modifier_groups",
            "label": "Restaurant Modifier Groups",
            "fieldtype": "Table",
            "options": "Restaurant Menu Item Modifier",
            "insert_after": "restaurant_ingredients",
        },
    ],
    "Sales Order": [
        {
            "fieldname": "restaurant_order_code",
            "label": "Restaurant Order Code",
            "fieldtype": "Data",
            "insert_after": "status",
            "unique": 1,
            "in_list_view": 1,
        },
        {
            "fieldname": "restaurant_customer_mobile",
            "label": "Restaurant Customer Mobile",
            "fieldtype": "Data",
            "insert_after": "restaurant_order_code",
        },
        {
            "fieldname": "restaurant_order_type",
            "label": "Restaurant Order Type",
            "fieldtype": "Select",
            "options": ORDER_TYPE_OPTIONS,
            "insert_after": "restaurant_customer_mobile",
        },
        {
            "fieldname": "restaurant_delivery_address",
            "label": "Restaurant Delivery Address",
            "fieldtype": "Small Text",
            "insert_after": "restaurant_order_type",
        },
        {
            "fieldname": "restaurant_note",
            "label": "Restaurant Note",
            "fieldtype": "Small Text",
            "insert_after": "restaurant_delivery_address",
        },
        {
            "fieldname": "restaurant_status",
            "label": "Restaurant Status",
            "fieldtype": "Select",
            "options": ORDER_STATUS_OPTIONS,
            "default": "new",
            "insert_after": "restaurant_note",
        },
        {
            "fieldname": "restaurant_payload_json",
            "label": "Restaurant Payload JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_status",
        },
    ],
    "Sales Order Item": [
        {
            "fieldname": "restaurant_menu_slug",
            "label": "Restaurant Menu Slug",
            "fieldtype": "Data",
            "insert_after": "description",
        },
        {
            "fieldname": "restaurant_customization_json",
            "label": "Restaurant Customization JSON",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_menu_slug",
        },
        {
            "fieldname": "restaurant_selection_summary",
            "label": "Restaurant Selection Summary",
            "fieldtype": "Long Text",
            "insert_after": "restaurant_customization_json",
        },
    ],
}


EXTRA_MENU_ITEMS = [
    {
        "slug": "pizza-four-cheese-premium",
        "title": "پیتزا چهار پنیر پریمیوم",
        "category_slug": "pizza",
        "subcategory_slug": "pizza-special",
        "short_desc": "ترکیب موزارلا، پارمزان، چدار و گودا",
        "long_desc": "پیتزای پنیر دوست ها با بافت نرم و عطر عالی.",
        "base_price": 1980000,
        "is_featured": 1,
        "sort_order": 101,
        "ingredients": [
            {"ingredient_name": "پنیر موزارلا", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 110000, "sort_order": 1},
            {"ingredient_name": "پنیر پارمزان", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 130000, "sort_order": 2},
            {"ingredient_name": "پنیر چدار", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 120000, "sort_order": 3},
        ],
        "modifier_titles": ["نوع خمیر پیتزا", "پنیر اضافه", "سایز پرس"],
        "allergen_tags": "لبنیات, گلوتن",
    },
    {
        "slug": "pizza-mushroom-olive",
        "title": "پیتزا قارچ و زیتون",
        "category_slug": "pizza",
        "subcategory_slug": "pizza-classic",
        "short_desc": "سس گوجه، قارچ تازه و زیتون سیاه",
        "long_desc": "پیتزای کلاسیک سبک با طعم متعادل.",
        "base_price": 1560000,
        "is_featured": 0,
        "sort_order": 102,
        "ingredients": [
            {"ingredient_name": "قارچ", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 70000, "sort_order": 1},
            {"ingredient_name": "زیتون", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 60000, "sort_order": 2},
        ],
        "modifier_titles": ["نوع خمیر پیتزا", "سایز پرس"],
        "allergen_tags": "لبنیات, گلوتن",
    },
    {
        "slug": "spaghetti-arrabbiata",
        "title": "اسپاگتی آرابیاتا",
        "category_slug": "pasta",
        "subcategory_slug": "pasta-special",
        "short_desc": "سس تند گوجه و ریحان",
        "long_desc": "پاستای ایتالیایی با سس تند و عطر سبزیجات تازه.",
        "base_price": 1480000,
        "is_featured": 0,
        "sort_order": 103,
        "ingredients": [
            {"ingredient_name": "سس گوجه تند", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 1},
            {"ingredient_name": "ریحان", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 30000, "sort_order": 2},
        ],
        "modifier_titles": ["نوع سس پاستا", "افزودنی پروتئین", "سایز پرس"],
        "allergen_tags": "گلوتن",
    },
    {
        "slug": "shrimp-pesto-pasta",
        "title": "پاستا پستو میگو",
        "category_slug": "pasta",
        "subcategory_slug": "pasta-creamy",
        "short_desc": "پنه، سس پستو و میگوی سوخاری",
        "long_desc": "پاستای دریایی خوش عطر با بافت کرمی.",
        "base_price": 2140000,
        "is_featured": 1,
        "sort_order": 104,
        "ingredients": [
            {"ingredient_name": "میگو", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 250000, "sort_order": 1},
            {"ingredient_name": "پستو", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 2},
        ],
        "modifier_titles": ["نوع سس پاستا", "سایز پرس"],
        "allergen_tags": "گلوتن, سخت پوستان",
    },
    {
        "slug": "salad-tuna-avocado",
        "title": "سالاد تن و آووکادو",
        "category_slug": "salads",
        "subcategory_slug": "salad-protein",
        "short_desc": "تن ماهی، آووکادو و سبزیجات تازه",
        "long_desc": "سالاد پروتئینی سبک برای وعده کامل.",
        "base_price": 1390000,
        "is_featured": 0,
        "sort_order": 105,
        "ingredients": [
            {"ingredient_name": "تن ماهی", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 140000, "sort_order": 1},
            {"ingredient_name": "آووکادو", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 140000, "sort_order": 2},
        ],
        "modifier_titles": ["انتخاب سس سالاد", "افزودنی پروتئین"],
        "allergen_tags": "ماهی",
    },
    {
        "slug": "salad-lentil-detox",
        "title": "سالاد عدس دیتاکس",
        "category_slug": "salads",
        "subcategory_slug": "salad-green",
        "short_desc": "عدس پخته، سبزیجات و سس لیمویی",
        "long_desc": "سالاد گیاهی مقوی با فیبر بالا.",
        "base_price": 980000,
        "is_featured": 0,
        "sort_order": 106,
        "ingredients": [
            {"ingredient_name": "عدس", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 1},
            {"ingredient_name": "گردو", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 90000, "sort_order": 2},
        ],
        "modifier_titles": ["انتخاب سس سالاد"],
        "allergen_tags": "",
    },
    {
        "slug": "cold-brew-orange",
        "title": "کلدبرو پرتقال",
        "category_slug": "drinks",
        "subcategory_slug": "drink-cold",
        "short_desc": "کافی کلدبرو با عصاره پرتقال",
        "long_desc": "نوشیدنی سرد انرژی زا با طعم مرکبات.",
        "base_price": 410000,
        "is_featured": 0,
        "sort_order": 107,
        "ingredients": [],
        "modifier_titles": ["سایز پرس"],
        "allergen_tags": "",
    },
    {
        "slug": "iced-matcha",
        "title": "آیس ماچا",
        "category_slug": "drinks",
        "subcategory_slug": "drink-cold",
        "short_desc": "چای سبز ماچا با یخ",
        "long_desc": "نوشیدنی خنک سبک و پرطرفدار.",
        "base_price": 460000,
        "is_featured": 0,
        "sort_order": 108,
        "ingredients": [],
        "modifier_titles": ["سایز پرس"],
        "allergen_tags": "",
    },
    {
        "slug": "molten-choco-cake",
        "title": "کیک شکلاتی لاوا",
        "category_slug": "desserts",
        "subcategory_slug": "",
        "short_desc": "کیک گرم با مغز شکلاتی روان",
        "long_desc": "دسر شکلاتی محبوب با سرو گرم.",
        "base_price": 780000,
        "is_featured": 1,
        "sort_order": 109,
        "ingredients": [
            {"ingredient_name": "سس شکلات", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 45000, "sort_order": 1},
        ],
        "modifier_titles": [],
        "allergen_tags": "گلوتن, لبنیات",
    },
    {
        "slug": "rice-chicken-bowl",
        "title": "بول برنج و مرغ گریل",
        "category_slug": "mains",
        "subcategory_slug": "",
        "short_desc": "برنج ادویه ای، مرغ گریل و سبزیجات",
        "long_desc": "وعده کامل و متعادل برای نهار یا شام.",
        "base_price": 1720000,
        "is_featured": 1,
        "sort_order": 110,
        "ingredients": [
            {"ingredient_name": "مرغ گریل", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 180000, "sort_order": 1},
            {"ingredient_name": "برنج", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 2},
        ],
        "modifier_titles": ["میزان تندی"],
        "allergen_tags": "",
    },
]


def _slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u0600-\u06FF\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-")


def _ensure_custom_field(dt: str, field_def: dict):
    existing_name = frappe.db.get_value("Custom Field", {"dt": dt, "fieldname": field_def["fieldname"]}, "name")
    payload = {
        "doctype": "Custom Field",
        "dt": dt,
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
        return doc.name

    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_custom_fields():
    for dt, field_defs in CUSTOM_FIELDS.items():
        for field_def in field_defs:
            _ensure_custom_field(dt, field_def)


def _pick_uom() -> str:
    for name in ["Nos", "Unit", "واحد", "Box"]:
        if frappe.db.exists("UOM", name):
            return name

    fallback = frappe.db.get_value("UOM", {}, "name")
    return fallback or "Nos"


def _get_selling_price_list() -> str:
    for filters in [{"selling": 1}, {}]:
        name = frappe.db.get_value("Price List", filters, "name")
        if name:
            return name
    return ""


def _item_image_field() -> Optional[str]:
    if frappe.db.has_column("Item", "item_image"):
        return "item_image"
    if frappe.db.has_column("Item", "image"):
        return "image"
    return None


def _item_group_root():
    root = frappe.db.get_value("Item Group", {"parent_item_group": ""}, "name")
    if root:
        return root
    return frappe.db.get_value("Item Group", {"is_group": 1}, "name")


def _ensure_root_item_group() -> str:
    if frappe.db.exists("Item Group", ROOT_ITEM_GROUP):
        doc = frappe.get_doc("Item Group", ROOT_ITEM_GROUP)
    else:
        parent_root = _item_group_root()
        if not parent_root:
            frappe.throw("Could not resolve Item Group root.")

        doc = frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": ROOT_ITEM_GROUP,
                "parent_item_group": parent_root,
                "is_group": 1,
            }
        )
        doc.insert(ignore_permissions=True)

    doc.restaurant_is_menu_category = 0
    doc.restaurant_is_subcategory = 0
    doc.restaurant_slug = "restaurant-menu"
    doc.restaurant_sort_order = -1
    doc.restaurant_active = 1
    doc.save(ignore_permissions=True)
    return doc.name


def _ensure_item_group(
    *,
    title: str,
    slug: str,
    parent_item_group: str,
    is_subcategory: int,
    sort_order: int = 0,
    description: str = "",
    image: str = "",
):
    slug = _slugify(slug)
    existing = frappe.db.get_value("Item Group", {"restaurant_slug": slug}, "name")
    if not existing:
        existing = frappe.db.get_value(
            "Item Group",
            {
                "item_group_name": title,
                "parent_item_group": parent_item_group,
            },
            "name",
        )

    if existing:
        doc = frappe.get_doc("Item Group", existing)
    else:
        item_group_name = title
        if frappe.db.exists("Item Group", item_group_name):
            item_group_name = f"{title} ({slug})"
            counter = 2
            while frappe.db.exists("Item Group", item_group_name):
                item_group_name = f"{title} ({slug}-{counter})"
                counter += 1

        doc = frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": item_group_name,
                "parent_item_group": parent_item_group,
                "is_group": 0 if is_subcategory else 1,
            }
        )
        doc.insert(ignore_permissions=True)

    doc.item_group_name = title
    doc.parent_item_group = parent_item_group
    doc.is_group = 0 if is_subcategory else 1
    doc.image = image or ""
    doc.restaurant_is_menu_category = 1
    doc.restaurant_is_subcategory = cint(is_subcategory)
    doc.restaurant_slug = slug
    doc.restaurant_sort_order = cint(sort_order)
    doc.restaurant_description = description or ""
    doc.restaurant_active = 1
    doc.save(ignore_permissions=True)
    return doc.name


def _build_modifier_rows(menu_doc) -> List[dict]:
    rows = []
    for row in sorted(menu_doc.modifier_groups or [], key=lambda d: cint(d.sort_order or 0)):
        rows.append(
            {
                "modifier_group": row.modifier_group,
                "required": cint(row.required),
                "min_select": cint(row.min_select),
                "max_select": cint(row.max_select),
                "sort_order": cint(row.sort_order),
            }
        )
    return rows


def _build_ingredient_rows(menu_doc) -> List[dict]:
    rows = []
    for row in sorted(menu_doc.ingredients or [], key=lambda d: cint(d.sort_order or 0)):
        rows.append(
            {
                "ingredient_name": row.ingredient_name,
                "is_included_by_default": cint(row.is_included_by_default),
                "can_remove": cint(row.can_remove),
                "extra_when_added": flt(row.extra_when_added),
                "sort_order": cint(row.sort_order),
            }
        )
    return rows


def _item_code_from_slug(slug: str) -> str:
    return f"REST-{_slugify(slug).replace('-', '_').upper()}"


def _upsert_item_price(item_code: str, uom: str, rate: float):
    price_list = _get_selling_price_list()
    if not price_list:
        return

    price_name = frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": price_list,
            "uom": uom,
            "selling": 1,
        },
        "name",
    )

    if price_name:
        price_doc = frappe.get_doc("Item Price", price_name)
        price_doc.price_list_rate = flt(rate)
        price_doc.selling = 1
        price_doc.save(ignore_permissions=True)
        return

    currency = frappe.db.get_value("Price List", price_list, "currency")
    price_doc = frappe.get_doc(
        {
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "uom": uom,
            "price_list_rate": flt(rate),
            "selling": 1,
            "currency": currency,
        }
    )
    price_doc.insert(ignore_permissions=True)


def _upsert_core_item(payload: dict):
    slug = _slugify(payload["slug"])
    item_code = payload.get("item_code") or _item_code_from_slug(slug)

    existing = frappe.db.get_value("Item", {"restaurant_slug": slug}, "name")
    if not existing:
        existing = frappe.db.get_value("Item", {"item_code": item_code}, "name")

    if existing:
        doc = frappe.get_doc("Item", existing)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": payload["title"],
                "item_group": payload["item_group"],
                "stock_uom": payload["stock_uom"],
                "is_stock_item": 0,
                "is_sales_item": 1,
                "is_purchase_item": 0,
            }
        )

    doc.item_name = payload["title"]
    doc.item_group = payload["item_group"]
    doc.stock_uom = payload["stock_uom"]
    image_field = _item_image_field()
    if image_field:
        setattr(doc, image_field, payload.get("image") or "")
    doc.description = payload.get("long_desc") or payload.get("short_desc") or ""
    doc.disabled = 0 if cint(payload.get("is_active", 1)) else 1
    doc.standard_rate = flt(payload.get("base_price") or 0)
    doc.is_sales_item = 1
    doc.is_purchase_item = 0
    doc.is_stock_item = 0

    doc.restaurant_enabled = cint(payload.get("is_active", 1))
    doc.restaurant_slug = slug
    doc.restaurant_category = payload.get("category_group") or ""
    doc.restaurant_subcategory = payload.get("subcategory_group") or ""
    doc.restaurant_short_desc = payload.get("short_desc") or ""
    doc.restaurant_long_desc = payload.get("long_desc") or ""
    doc.restaurant_base_price = flt(payload.get("base_price") or 0)
    doc.restaurant_is_featured = cint(payload.get("is_featured", 0))
    doc.restaurant_sort_order = cint(payload.get("sort_order") or 0)
    doc.restaurant_allergen_tags = payload.get("allergen_tags") or ""
    doc.restaurant_branch = payload.get("branch") or ""
    doc.restaurant_prep_time_mins = cint(payload.get("prep_time_mins") or 20)

    doc.set("restaurant_ingredients", payload.get("ingredients") or [])
    doc.set("restaurant_modifier_groups", payload.get("modifier_groups") or [])

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)

    _upsert_item_price(doc.item_code, doc.stock_uom, flt(payload.get("base_price") or 0))
    return doc.name


def _sync_categories_and_items_to_core():
    root = _ensure_root_item_group()
    stock_uom = _pick_uom()

    category_map: Dict[str, str] = {}
    category_slug_map: Dict[str, str] = {}

    categories = frappe.get_all(
        "Restaurant Menu Category",
        fields=["name", "title", "slug", "description", "image", "sort_order"],
        filters={"is_active": 1},
        order_by="sort_order asc, title asc",
        ignore_permissions=True,
    )

    for cat in categories:
        group_name = _ensure_item_group(
            title=cat.title,
            slug=cat.slug,
            parent_item_group=root,
            is_subcategory=0,
            sort_order=cint(cat.sort_order),
            description=cat.description or "",
            image=cat.image or "",
        )
        category_map[cat.name] = group_name
        category_slug_map[cat.slug] = group_name

    subcategory_map: Dict[str, str] = {}
    subcategory_slug_map: Dict[str, str] = {}

    if frappe.db.exists("DocType", "Restaurant Menu Subcategory"):
        subcategories = frappe.get_all(
            "Restaurant Menu Subcategory",
            fields=["name", "title", "slug", "category", "description", "sort_order"],
            filters={"is_active": 1},
            order_by="sort_order asc, title asc",
            ignore_permissions=True,
        )
        for sub in subcategories:
            parent_group = category_map.get(sub.category)
            if not parent_group:
                continue

            group_name = _ensure_item_group(
                title=sub.title,
                slug=sub.slug,
                parent_item_group=parent_group,
                is_subcategory=1,
                sort_order=cint(sub.sort_order),
                description=sub.description or "",
            )
            subcategory_map[sub.name] = group_name
            subcategory_slug_map[sub.slug] = group_name

    menu_fields = [
        "name",
        "title",
        "slug",
        "category",
        "short_desc",
        "long_desc",
        "base_price",
        "image",
        "allergen_tags",
        "sort_order",
        "is_active",
        "is_featured",
        "branch",
    ]
    has_subcategory_field = frappe.db.has_column("Restaurant Menu Item", "subcategory")
    if has_subcategory_field:
        menu_fields.append("subcategory")

    menu_rows = frappe.get_all(
        "Restaurant Menu Item",
        fields=menu_fields,
        ignore_permissions=True,
        order_by="sort_order asc, title asc",
    )

    for row in menu_rows:
        menu_doc = frappe.get_doc("Restaurant Menu Item", row.name)
        category_group = category_map.get(row.category)
        subcategory_group = subcategory_map.get(getattr(row, "subcategory", "")) if has_subcategory_field else ""
        if not category_group:
            continue

        _upsert_core_item(
            {
                "slug": row.slug,
                "title": row.title,
                "item_group": subcategory_group or category_group,
                "category_group": category_group,
                "subcategory_group": subcategory_group,
                "short_desc": row.short_desc,
                "long_desc": row.long_desc,
                "base_price": row.base_price,
                "image": row.image,
                "allergen_tags": row.allergen_tags,
                "sort_order": row.sort_order,
                "is_active": row.is_active,
                "is_featured": row.is_featured,
                "branch": row.branch,
                "stock_uom": stock_uom,
                "ingredients": _build_ingredient_rows(menu_doc),
                "modifier_groups": _build_modifier_rows(menu_doc),
                "prep_time_mins": 20,
            }
        )

    modifier_title_map = {
        row.title: row.name
        for row in frappe.get_all(
            "Restaurant Modifier Group",
            fields=["name", "title"],
            filters={"is_active": 1},
            ignore_permissions=True,
        )
    }

    for idx, extra in enumerate(EXTRA_MENU_ITEMS, start=1):
        category_group = category_slug_map.get(extra["category_slug"])
        if not category_group:
            continue

        subcategory_group = subcategory_slug_map.get(extra.get("subcategory_slug") or "")
        modifier_rows = []
        for order, title in enumerate(extra.get("modifier_titles") or [], start=1):
            group_name = modifier_title_map.get(title)
            if not group_name:
                continue
            modifier_rows.append(
                {
                    "modifier_group": group_name,
                    "required": 0,
                    "min_select": 0,
                    "max_select": 1,
                    "sort_order": order,
                }
            )

        _upsert_core_item(
            {
                "slug": extra["slug"],
                "title": extra["title"],
                "item_group": subcategory_group or category_group,
                "category_group": category_group,
                "subcategory_group": subcategory_group,
                "short_desc": extra.get("short_desc"),
                "long_desc": extra.get("long_desc"),
                "base_price": extra.get("base_price", 0),
                "image": extra.get("image", ""),
                "allergen_tags": extra.get("allergen_tags", ""),
                "sort_order": extra.get("sort_order", 100 + idx),
                "is_active": 1,
                "is_featured": extra.get("is_featured", 0),
                "branch": extra.get("branch", ""),
                "stock_uom": stock_uom,
                "ingredients": extra.get("ingredients") or [],
                "modifier_groups": modifier_rows,
                "prep_time_mins": extra.get("prep_time_mins", 20),
            }
        )


def _ensure_guest_customer():
    customer_name = "مشتری مهمان رستوران"
    if frappe.db.exists("Customer", customer_name):
        return customer_name

    customer_group = frappe.db.get_single_value("Selling Settings", "customer_group") or frappe.db.get_value(
        "Customer Group", {}, "name"
    )
    territory = frappe.db.get_single_value("Selling Settings", "territory") or frappe.db.get_value(
        "Territory", {"is_group": 0}, "name"
    )

    if not customer_group:
        return

    if not territory:
        territory = frappe.db.get_value("Territory", {}, "name")

    if not territory:
        return

    doc = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_group": customer_group,
            "territory": territory,
            "customer_type": "Individual",
            "mobile_no": "09120000000",
        }
    )
    doc.insert(ignore_permissions=True)


def execute():
    _ensure_custom_fields()
    _sync_categories_and_items_to_core()
    _ensure_guest_customer()
    frappe.clear_cache()
    frappe.db.commit()
