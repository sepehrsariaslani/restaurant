import frappe
from frappe.utils import cint, flt


TABLES = [
    {"table_number": "T01", "location": "Main Hall"},
    {"table_number": "T02", "location": "Main Hall"},
    {"table_number": "T03", "location": "Main Hall"},
    {"table_number": "T04", "location": "Main Hall"},
    {"table_number": "T05", "location": "Terrace"},
    {"table_number": "T06", "location": "Terrace"},
    {"table_number": "T07", "location": "Terrace"},
    {"table_number": "T08", "location": "VIP"},
    {"table_number": "T09", "location": "VIP"},
    {"table_number": "T10", "location": "VIP"},
    {"table_number": "T11", "location": "Family"},
    {"table_number": "T12", "location": "Family"},
]

MENU_ITEMS = [
    {"item_name": "سالاد سزار مرغ", "category": "سالاد", "price": 780000, "prep_time_mins": 12},
    {"item_name": "سالاد یونانی", "category": "سالاد", "price": 690000, "prep_time_mins": 10},
    {"item_name": "سالاد تن ماهی", "category": "سالاد", "price": 720000, "prep_time_mins": 11},
    {"item_name": "سالاد کینوآ", "category": "سالاد", "price": 840000, "prep_time_mins": 14},
    {"item_name": "پیتزا مارگاریتا", "category": "پیتزا", "price": 980000, "prep_time_mins": 18},
    {"item_name": "پیتزا پپرونی", "category": "پیتزا", "price": 1160000, "prep_time_mins": 19},
    {"item_name": "پیتزا مرغ باربیکیو", "category": "پیتزا", "price": 1240000, "prep_time_mins": 20},
    {"item_name": "پیتزا سبزیجات", "category": "پیتزا", "price": 1040000, "prep_time_mins": 18},
    {"item_name": "پاستا آلفردو", "category": "پاستا", "price": 1020000, "prep_time_mins": 17},
    {"item_name": "پاستا پستو", "category": "پاستا", "price": 940000, "prep_time_mins": 16},
    {"item_name": "پاستا آرابیاتا", "category": "پاستا", "price": 890000, "prep_time_mins": 15},
    {"item_name": "لازانیا گوشت", "category": "پاستا", "price": 1180000, "prep_time_mins": 22},
    {"item_name": "برگر کلاسیک", "category": "غذای اصلی", "price": 970000, "prep_time_mins": 14},
    {"item_name": "برگر قارچ و پنیر", "category": "غذای اصلی", "price": 1090000, "prep_time_mins": 16},
    {"item_name": "ساندویچ استیک", "category": "غذای اصلی", "price": 1210000, "prep_time_mins": 17},
    {"item_name": "مرغ گریل", "category": "غذای اصلی", "price": 1130000, "prep_time_mins": 18},
    {"item_name": "موهیتو", "category": "نوشیدنی", "price": 320000, "prep_time_mins": 4},
    {"item_name": "لیموناد", "category": "نوشیدنی", "price": 280000, "prep_time_mins": 3},
    {"item_name": "آب پرتقال طبیعی", "category": "نوشیدنی", "price": 360000, "prep_time_mins": 5},
    {"item_name": "قهوه لاته", "category": "نوشیدنی", "price": 340000, "prep_time_mins": 6},
    {"item_name": "چیزکیک", "category": "دسر", "price": 420000, "prep_time_mins": 5},
    {"item_name": "براونی شکلاتی", "category": "دسر", "price": 390000, "prep_time_mins": 5},
    {"item_name": "تیرامیسو", "category": "دسر", "price": 460000, "prep_time_mins": 6},
    {"item_name": "بستنی وانیلی", "category": "دسر", "price": 250000, "prep_time_mins": 3},
]


def _upsert_table(row):
    existing = frappe.db.get_value("Restaurant Table", {"table_number": row["table_number"]}, "name")
    if existing:
        doc = frappe.get_doc("Restaurant Table", existing)
    else:
        doc = frappe.get_doc({"doctype": "Restaurant Table", "table_number": row["table_number"]})

    doc.location = row.get("location") or ""
    doc.is_active = 1
    if not doc.status:
        doc.status = "empty"

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def _upsert_menu_item(payload, sort_order):
    existing = frappe.db.get_value(
        "Restaurant Table Menu Item",
        {
            "item_name": payload["item_name"],
            "category": payload["category"],
        },
        "name",
    )
    if existing:
        doc = frappe.get_doc("Restaurant Table Menu Item", existing)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Restaurant Table Menu Item",
                "item_name": payload["item_name"],
                "category": payload["category"],
            }
        )

    doc.price = flt(payload.get("price") or 0)
    doc.description = payload.get("description") or payload["item_name"]
    doc.prep_time_mins = cint(payload.get("prep_time_mins") or 10)
    doc.sort_order = cint(sort_order)
    doc.is_available = 1

    if doc.is_new():
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)


def execute():
    required = [
        "Restaurant Table",
        "Restaurant Table Menu Item",
    ]
    if any(not frappe.db.exists("DocType", dt) for dt in required):
        return

    for row in TABLES:
        _upsert_table(row)

    for index, item in enumerate(MENU_ITEMS, start=1):
        _upsert_menu_item(item, index)
