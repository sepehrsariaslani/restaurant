import frappe


def _has_column(doctype, fieldname):
    try:
        return frappe.db.has_column(doctype, fieldname)
    except Exception:
        return False


def _upsert_doc(doctype, lookup, values):
    name = frappe.db.get_value(doctype, lookup, "name")
    if name:
        doc = frappe.get_doc(doctype, name)
    else:
        doc = frappe.new_doc(doctype)

    for fieldname, value in values.items():
        doc.set(fieldname, value)

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def _seed_hero_slides():
    if not frappe.db.exists("DocType", "Restaurant Hero Slide"):
        return
    if frappe.db.count("Restaurant Hero Slide"):
        return

    filters = {"disabled": 0}
    if _has_column("Item", "restaurant_enabled"):
        filters["restaurant_enabled"] = 1

    image_field = "item_image" if _has_column("Item", "item_image") else "image"
    order_by_parts = []
    if _has_column("Item", "restaurant_is_featured"):
        order_by_parts.append("restaurant_is_featured desc")
    if _has_column("Item", "restaurant_sort_order"):
        order_by_parts.append("restaurant_sort_order asc")
    order_by_parts.append("item_name asc")

    rows = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_name", "restaurant_slug", f"{image_field} as image"],
        order_by=", ".join(order_by_parts),
        limit=3,
        ignore_permissions=True,
    )

    default_slides = [
        {
            "title": "طعم تازه هر روز",
            "subtitle": "محصولات روزانه با امکان شخصی سازی کامل",
            "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=1400&auto=format&fit=crop&q=60",
            "cta_label": "مشاهده منو",
            "cta_url": "/restaurant/menu",
            "sort_order": 1,
        },
        {
            "title": "پیشنهاد ویژه سرآشپز",
            "subtitle": "غذاهای محبوب با مواد اولیه تازه",
            "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1400&auto=format&fit=crop&q=60",
            "cta_label": "ثبت سفارش",
            "cta_url": "/restaurant/menu",
            "sort_order": 2,
        },
        {
            "title": "ارسال سریع و مطمئن",
            "subtitle": "از انتخاب تا تحویل، همه چيز شفاف و سريع",
            "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=1400&auto=format&fit=crop&q=60",
            "cta_label": "شروع سفارش",
            "cta_url": "/restaurant/menu",
            "sort_order": 3,
        },
    ]

    for idx, base in enumerate(default_slides):
        item = rows[idx] if idx < len(rows) else None
        values = {
            "title": item.item_name if item else base["title"],
            "subtitle": base["subtitle"],
            "image": item.image if item else base["image"],
            "linked_item": item.name if item else "",
            "cta_label": base["cta_label"],
            "cta_url": base["cta_url"],
            "sort_order": base["sort_order"],
            "is_active": 1,
            "branch": "",
        }
        _upsert_doc(
            "Restaurant Hero Slide",
            {"sort_order": base["sort_order"]},
            values,
        )


def _seed_about_sections():
    if not frappe.db.exists("DocType", "Restaurant About Section"):
        return
    if frappe.db.count("Restaurant About Section"):
        return

    sections = [
        {
            "title": "داستان ما",
            "subtitle": "شروع از یک آشپزخانه کوچک",
            "body_text": "ما کار را با هدف ارائه غذای سالم و قابل شخصی سازی آغاز کردیم. امروز هر سفارش با همان دقت روز اول آماده می شود.",
            "image": "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1200&auto=format&fit=crop&q=60",
            "stat_label": "سال تجربه",
            "stat_value": "10+",
            "sort_order": 1,
            "is_active": 1,
        },
        {
            "title": "کیفیت مواد اولیه",
            "subtitle": "تازه، روزانه، قابل رهگیری",
            "body_text": "برای هر آیتم از مواد اولیه تازه استفاده می کنیم و روند آماده سازی به صورت شفاف در سیستم ثبت می شود.",
            "image": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=1200&auto=format&fit=crop&q=60",
            "stat_label": "آیتم تازه روزانه",
            "stat_value": "50+",
            "sort_order": 2,
            "is_active": 1,
        },
        {
            "title": "تجربه مشتری",
            "subtitle": "از سفارش تا تحویل",
            "body_text": "مسیر سفارش برای موبایل طراحی شده تا مشتری به سرعت آیتم را انتخاب کند، مواد را تنظیم کند و وضعیت سفارش را دنبال کند.",
            "image": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&auto=format&fit=crop&q=60",
            "stat_label": "مشتری راضی",
            "stat_value": "12K+",
            "sort_order": 3,
            "is_active": 1,
        },
    ]

    for row in sections:
        _upsert_doc(
            "Restaurant About Section",
            {"sort_order": row["sort_order"]},
            row,
        )


def _seed_faq_items():
    if not frappe.db.exists("DocType", "Restaurant FAQ"):
        return
    if frappe.db.count("Restaurant FAQ"):
        return

    faqs = [
        {
            "question": "چطور سفارش ثبت کنم؟",
            "answer": "وارد منو شوید، آیتم موردنظر را انتخاب کنید، مواد را شخصی سازی کنید و سفارش را نهایی کنید.",
            "sort_order": 1,
            "is_active": 1,
        },
        {
            "question": "آیا امکان حذف یا اضافه کردن مواد وجود دارد؟",
            "answer": "بله، برای هر محصول می توانید مواد را کم یا زیاد کنید و تغییر قیمت را همان لحظه ببینید.",
            "sort_order": 2,
            "is_active": 1,
        },
        {
            "question": "روش های پرداخت چیست؟",
            "answer": "در حال حاضر پرداخت حضوری و پرداخت آنلاین (در صورت فعال بودن در شعبه) پشتیبانی می شود.",
            "sort_order": 3,
            "is_active": 1,
        },
        {
            "question": "حداقل زمان آماده سازی چقدر است؟",
            "answer": "زمان آماده سازی به نوع سفارش بستگی دارد اما به طور معمول بین 15 تا 35 دقیقه است.",
            "sort_order": 4,
            "is_active": 1,
        },
        {
            "question": "چطور وضعیت سفارش را پیگیری کنم؟",
            "answer": "پس از ثبت سفارش، کد سفارش دریافت می کنید و می توانید از صفحه پیگیری وضعیت آن را مشاهده کنید.",
            "sort_order": 5,
            "is_active": 1,
        },
        {
            "question": "اگر در ثبت سفارش مشکل داشتم چه کنم؟",
            "answer": "از طریق شماره تماس مجموعه یا پشتیبانی آنلاین با ما ارتباط بگیرید تا سریع رسیدگی شود.",
            "sort_order": 6,
            "is_active": 1,
        },
    ]

    for row in faqs:
        _upsert_doc("Restaurant FAQ", {"sort_order": row["sort_order"]}, row)


def execute():
    _seed_hero_slides()
    _seed_about_sections()
    _seed_faq_items()
    frappe.clear_cache()
