import frappe
from frappe.utils import now


def _upsert_web_settings():
    if not frappe.db.exists("DocType", "Restaurant Web Settings"):
        return

    settings = frappe.get_doc("Restaurant Web Settings")
    defaults = {
        "brand_name": "Veederakht Restaurant",
        "brand_tagline": "منوی موبایل با دسته بندی و ساب دسته حرفه ای",
        "default_currency": "IRR",
        "hero_title": "پیتزا، پاستا، سالاد و سفارش کاملا شخصی سازی شده",
        "hero_subtitle": "مشتری دسته اصلی و زیر دسته را انتخاب می کند، مواد را کم و زیاد می کند و سریع سفارش می دهد.",
        "primary_cta_label": "شروع سفارش",
    }

    changed = False
    for fieldname, value in defaults.items():
        if not settings.get(fieldname):
            settings.set(fieldname, value)
            changed = True

    if changed:
        settings.save(ignore_permissions=True)


def _ensure_category(title, slug, description, image="", sort_order=0):
    doc_name = frappe.db.get_value("Restaurant Menu Category", {"slug": slug}, "name")

    if doc_name:
        doc = frappe.get_doc("Restaurant Menu Category", doc_name)
        doc.title = title
        doc.description = description
        doc.image = image
        doc.sort_order = sort_order
        doc.is_active = 1
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Restaurant Menu Category",
            "title": title,
            "slug": slug,
            "description": description,
            "image": image,
            "sort_order": sort_order,
            "is_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _has_subcategory_support():
    return frappe.db.exists("DocType", "Restaurant Menu Subcategory") and frappe.db.has_column(
        "Restaurant Menu Item", "subcategory"
    )


def _ensure_subcategory(title, slug, category, description="", sort_order=0):
    if not _has_subcategory_support():
        return ""

    existing = frappe.db.get_value("Restaurant Menu Subcategory", {"slug": slug}, "name")
    if existing:
        doc = frappe.get_doc("Restaurant Menu Subcategory", existing)
        doc.title = title
        doc.category = category
        doc.description = description
        doc.sort_order = sort_order
        doc.is_active = 1
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Restaurant Menu Subcategory",
            "title": title,
            "slug": slug,
            "category": category,
            "description": description,
            "sort_order": sort_order,
            "is_active": 1,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_modifier_group(title, selection_mode, required, min_select, max_select, options, sort_order=0):
    existing = frappe.db.get_value("Restaurant Modifier Group", {"title": title}, "name")

    if existing:
        doc = frappe.get_doc("Restaurant Modifier Group", existing)
        doc.selection_mode = selection_mode
        doc.required = required
        doc.min_select = min_select
        doc.max_select = max_select
        doc.sort_order = sort_order
        doc.is_active = 1
        doc.set("options", options)
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc(
        {
            "doctype": "Restaurant Modifier Group",
            "title": title,
            "selection_mode": selection_mode,
            "required": required,
            "min_select": min_select,
            "max_select": max_select,
            "sort_order": sort_order,
            "is_active": 1,
            "options": options,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_menu_item(payload):
    existing = frappe.db.get_value("Restaurant Menu Item", {"slug": payload["slug"]}, "name")

    if existing:
        doc = frappe.get_doc("Restaurant Menu Item", existing)
        for key, value in payload.items():
            if key in {"ingredients", "modifier_groups"}:
                continue
            if key == "subcategory" and not _has_subcategory_support():
                continue
            doc.set(key, value)

        doc.set("ingredients", payload.get("ingredients", []))
        doc.set("modifier_groups", payload.get("modifier_groups", []))
        doc.save(ignore_permissions=True)
        return doc.name

    doc = frappe.get_doc({"doctype": "Restaurant Menu Item", **payload})
    if not _has_subcategory_support() and doc.get("subcategory"):
        doc.subcategory = ""
    doc.insert(ignore_permissions=True)
    return doc.name


def execute():
    if not frappe.db.table_exists("Restaurant Menu Item"):
        return

    _upsert_web_settings()

    categories = {
        "pizza": _ensure_category("پیتزا", "pizza", "پیتزاهای تازه و دست ساز", sort_order=1),
        "pasta": _ensure_category("پاستا", "pasta", "پاستاهای خانگی و ایتالیایی", sort_order=2),
        "salads": _ensure_category("سالاد", "salads", "سالادهای سالم و رژیمی", sort_order=3),
        "drinks": _ensure_category("نوشیدنی", "drinks", "نوشیدنی های گرم و سرد", sort_order=4),
        "desserts": _ensure_category("دسر", "desserts", "دسرهای خوشمزه", sort_order=5),
        "mains": _ensure_category("غذای اصلی", "mains", "وعده اصلی", sort_order=6),
    }

    subcategories = {
        "pizza_diet": _ensure_subcategory("رژیمی", "pizza-diet", categories["pizza"], "پیتزای سبک", sort_order=1),
        "pizza_classic": _ensure_subcategory(
            "کلاسیک", "pizza-classic", categories["pizza"], "پیتزای کلاسیک ایتالیایی", sort_order=2
        ),
        "pizza_special": _ensure_subcategory(
            "اسپشیال", "pizza-special", categories["pizza"], "پیتزای ویژه سرآشپز", sort_order=3
        ),
        "pasta_light": _ensure_subcategory("رژیمی", "pasta-light", categories["pasta"], "پاستای سبک", sort_order=1),
        "pasta_creamy": _ensure_subcategory("کرم دار", "pasta-creamy", categories["pasta"], "پاستای خامه ای", sort_order=2),
        "pasta_special": _ensure_subcategory(
            "اسپشیال", "pasta-special", categories["pasta"], "پاستای ویژه سرآشپز", sort_order=3
        ),
        "salad_green": _ensure_subcategory("گرین", "salad-green", categories["salads"], "سالاد سبز", sort_order=1),
        "salad_protein": _ensure_subcategory(
            "پروتئینی", "salad-protein", categories["salads"], "سالاد با پروتئین", sort_order=2
        ),
        "drink_cold": _ensure_subcategory("سرد", "drink-cold", categories["drinks"], "نوشیدنی خنک", sort_order=1),
        "drink_hot": _ensure_subcategory("گرم", "drink-hot", categories["drinks"], "نوشیدنی گرم", sort_order=2),
    }

    size_group = _ensure_modifier_group(
        title="سایز پرس",
        selection_mode="single",
        required=1,
        min_select=1,
        max_select=1,
        sort_order=1,
        options=[
            {"option_name": "معمولی", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "بزرگ", "price_delta": 180000, "sort_order": 2},
        ],
    )

    crust_group = _ensure_modifier_group(
        title="نوع خمیر پیتزا",
        selection_mode="single",
        required=1,
        min_select=1,
        max_select=1,
        sort_order=2,
        options=[
            {"option_name": "نازک ایتالیایی", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "سبوس دار رژیمی", "price_delta": 120000, "sort_order": 2},
            {"option_name": "پن پفکی", "price_delta": 90000, "sort_order": 3},
        ],
    )

    spice_group = _ensure_modifier_group(
        title="میزان تندی",
        selection_mode="single",
        required=0,
        min_select=0,
        max_select=1,
        sort_order=3,
        options=[
            {"option_name": "بدون تندی", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "متوسط", "price_delta": 0, "sort_order": 2},
            {"option_name": "تند", "price_delta": 0, "sort_order": 3},
        ],
    )

    extra_cheese_group = _ensure_modifier_group(
        title="پنیر اضافه",
        selection_mode="single",
        required=0,
        min_select=0,
        max_select=1,
        sort_order=4,
        options=[
            {"option_name": "بدون پنیر اضافه", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "موزارلا", "price_delta": 110000, "sort_order": 2},
            {"option_name": "پارمزان", "price_delta": 130000, "sort_order": 3},
        ],
    )

    pasta_sauce_group = _ensure_modifier_group(
        title="نوع سس پاستا",
        selection_mode="single",
        required=1,
        min_select=1,
        max_select=1,
        sort_order=5,
        options=[
            {"option_name": "آلفردو", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "پستو", "price_delta": 50000, "sort_order": 2},
            {"option_name": "گوجه ایتالیایی", "price_delta": 30000, "sort_order": 3},
        ],
    )

    protein_group = _ensure_modifier_group(
        title="افزودنی پروتئین",
        selection_mode="single",
        required=0,
        min_select=0,
        max_select=1,
        sort_order=6,
        options=[
            {"option_name": "بدون افزودنی", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "مرغ گریل", "price_delta": 180000, "sort_order": 2},
            {"option_name": "میگو", "price_delta": 250000, "sort_order": 3},
            {"option_name": "توفو", "price_delta": 120000, "sort_order": 4},
        ],
    )

    dressing_group = _ensure_modifier_group(
        title="انتخاب سس سالاد",
        selection_mode="single",
        required=1,
        min_select=1,
        max_select=1,
        sort_order=7,
        options=[
            {"option_name": "سس سزار", "price_delta": 0, "is_default": 1, "sort_order": 1},
            {"option_name": "بالزامیک", "price_delta": 0, "sort_order": 2},
            {"option_name": "لیمو و روغن زیتون", "price_delta": 0, "sort_order": 3},
        ],
    )

    _ensure_menu_item(
        {
            "title": "پیتزا رژیمی مرغ و سبزیجات",
            "slug": "diet-chicken-pizza",
            "category": categories["pizza"],
            "subcategory": subcategories["pizza_diet"],
            "short_desc": "خمیر سبوس دار، مرغ گریل، سبزیجات تازه",
            "long_desc": "پیتزای سبک با کالری کمتر، مناسب رژیم غذایی سالم.",
            "base_price": 1680000,
            "sort_order": 1,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "گلوتن, لبنیات",
            "ingredients": [
                {"ingredient_name": "مرغ گریل", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 180000, "sort_order": 1},
                {"ingredient_name": "فلفل دلمه", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 60000, "sort_order": 2},
                {"ingredient_name": "کدو", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 70000, "sort_order": 3},
                {"ingredient_name": "پنیر موزارلا", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 110000, "sort_order": 4},
            ],
            "modifier_groups": [
                {"modifier_group": crust_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": extra_cheese_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
                {"modifier_group": size_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 3},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "پیتزا مارگاریتا کلاسیک",
            "slug": "margherita-classic",
            "category": categories["pizza"],
            "subcategory": subcategories["pizza_classic"],
            "short_desc": "سس گوجه، پنیر موزارلا و ریحان",
            "long_desc": "نسخه کلاسیک ایتالیایی با خمیر نازک و عطر ریحان تازه.",
            "base_price": 1490000,
            "sort_order": 2,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "گلوتن, لبنیات",
            "ingredients": [
                {"ingredient_name": "سس گوجه", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 1},
                {"ingredient_name": "پنیر موزارلا", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 110000, "sort_order": 2},
                {"ingredient_name": "ریحان", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 30000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": crust_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": spice_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
                {"modifier_group": size_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 3},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "پیتزا پپرونی اسپایسی",
            "slug": "spicy-pepperoni-pizza",
            "category": categories["pizza"],
            "subcategory": subcategories["pizza_special"],
            "short_desc": "پپرونی، پنیر ترکیبی، فلفل هالوپینو",
            "long_desc": "پیتزای تند و هیجان انگیز برای علاقه مندان طعم قوی.",
            "base_price": 1820000,
            "sort_order": 3,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "گلوتن, لبنیات",
            "ingredients": [
                {"ingredient_name": "پپرونی", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 150000, "sort_order": 1},
                {"ingredient_name": "هالوپینو", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 50000, "sort_order": 2},
                {"ingredient_name": "زیتون", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 60000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": crust_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": spice_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
                {"modifier_group": extra_cheese_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 3},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "پاستا آلفردو مرغ",
            "slug": "chicken-alfredo-pasta",
            "category": categories["pasta"],
            "subcategory": subcategories["pasta_creamy"],
            "short_desc": "پنه، مرغ گریل، سس آلفردو",
            "long_desc": "پاستای کرمی محبوب با بافت لطیف و پنیر پارمزان.",
            "base_price": 1590000,
            "sort_order": 4,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "گلوتن, لبنیات",
            "ingredients": [
                {"ingredient_name": "مرغ گریل", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 180000, "sort_order": 1},
                {"ingredient_name": "قارچ", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 70000, "sort_order": 2},
                {"ingredient_name": "پارمزان", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 130000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": pasta_sauce_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": protein_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
                {"modifier_group": size_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 3},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "پاستا پستو رژیمی",
            "slug": "diet-pesto-pasta",
            "category": categories["pasta"],
            "subcategory": subcategories["pasta_light"],
            "short_desc": "پاستای سبوس دار با سس پستو و سبزیجات",
            "long_desc": "گزینه سبک و سالم برای رژیم غذایی روزانه.",
            "base_price": 1420000,
            "sort_order": 5,
            "is_active": 1,
            "is_featured": 0,
            "allergen_tags": "گلوتن",
            "ingredients": [
                {"ingredient_name": "پاستای سبوس دار", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 1},
                {"ingredient_name": "بروکلی", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 70000, "sort_order": 2},
                {"ingredient_name": "ذرت", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 70000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": pasta_sauce_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": protein_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "پاستا بلونز اسپشیال",
            "slug": "special-bolognese-pasta",
            "category": categories["pasta"],
            "subcategory": subcategories["pasta_special"],
            "short_desc": "اسپاگتی، سس بلونز، گوشت مزه دار",
            "long_desc": "پاستای پرطرفدار با سس غلیظ خانگی و ادویه ملایم.",
            "base_price": 1710000,
            "sort_order": 6,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "گلوتن",
            "ingredients": [
                {"ingredient_name": "گوشت", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 170000, "sort_order": 1},
                {"ingredient_name": "فلفل دلمه", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 60000, "sort_order": 2},
            ],
            "modifier_groups": [
                {"modifier_group": spice_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 1},
                {"modifier_group": size_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 2},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "سالاد سزار پروتئینی",
            "slug": "protein-caesar-salad",
            "category": categories["salads"],
            "subcategory": subcategories["salad_protein"],
            "short_desc": "کاهو، مرغ گریل، پنیر پارمزان",
            "long_desc": "سالاد پروتئینی برای وعده سبک اما کامل.",
            "base_price": 1240000,
            "sort_order": 7,
            "is_active": 1,
            "is_featured": 0,
            "allergen_tags": "لبنیات",
            "ingredients": [
                {"ingredient_name": "مرغ گریل", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 180000, "sort_order": 1},
                {"ingredient_name": "پارمزان", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 120000, "sort_order": 2},
                {"ingredient_name": "نان تست", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 40000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": dressing_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
                {"modifier_group": protein_group, "required": 0, "min_select": 0, "max_select": 1, "sort_order": 2},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "سالاد گرین دیتاکس",
            "slug": "green-detox-salad",
            "category": categories["salads"],
            "subcategory": subcategories["salad_green"],
            "short_desc": "کاهو، آووکادو، کینوا و سبزیجات تازه",
            "long_desc": "سالاد گیاهی و سبک، مناسب رژیم و سبک زندگی سالم.",
            "base_price": 1120000,
            "sort_order": 8,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "",
            "ingredients": [
                {"ingredient_name": "آووکادو", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 140000, "sort_order": 1},
                {"ingredient_name": "کینوا", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 2},
                {"ingredient_name": "گردو", "is_included_by_default": 0, "can_remove": 0, "extra_when_added": 90000, "sort_order": 3},
            ],
            "modifier_groups": [
                {"modifier_group": dressing_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1},
            ],
        }
    )

    _ensure_menu_item(
        {
            "title": "لیموناد نعناع",
            "slug": "mint-lemonade",
            "category": categories["drinks"],
            "subcategory": subcategories["drink_cold"],
            "short_desc": "لیموناد طبیعی با نعناع تازه",
            "long_desc": "نوشیدنی سرد و تازه برای کنار غذا.",
            "base_price": 340000,
            "sort_order": 9,
            "is_active": 1,
            "is_featured": 1,
            "allergen_tags": "",
            "ingredients": [],
            "modifier_groups": [{"modifier_group": size_group, "required": 1, "min_select": 1, "max_select": 1, "sort_order": 1}],
        }
    )

    _ensure_menu_item(
        {
            "title": "چای ماسالا",
            "slug": "masala-tea",
            "category": categories["drinks"],
            "subcategory": subcategories["drink_hot"],
            "short_desc": "چای گرم با ادویه ماسالا",
            "long_desc": "نوشیدنی گرم و خوش عطر برای عصرانه.",
            "base_price": 290000,
            "sort_order": 10,
            "is_active": 1,
            "is_featured": 0,
            "allergen_tags": "",
            "ingredients": [],
            "modifier_groups": [],
        }
    )

    _ensure_menu_item(
        {
            "title": "تیرامیسو",
            "slug": "tiramisu",
            "category": categories["desserts"],
            "short_desc": "دسر ایتالیایی با کرم پنیر و قهوه",
            "long_desc": "تیرامیسوی تازه و سبک با لایه بیسکویت و کرم.",
            "base_price": 720000,
            "sort_order": 11,
            "is_active": 1,
            "is_featured": 0,
            "allergen_tags": "لبنیات, گلوتن",
            "ingredients": [
                {"ingredient_name": "کرم پنیر", "is_included_by_default": 1, "can_remove": 0, "extra_when_added": 0, "sort_order": 1},
                {"ingredient_name": "پودر کاکائو", "is_included_by_default": 1, "can_remove": 1, "extra_when_added": 25000, "sort_order": 2},
            ],
            "modifier_groups": [],
        }
    )

    frappe.db.commit()
    frappe.logger("restaurant").info("Seeded/updated restaurant demo data at %s", now())
