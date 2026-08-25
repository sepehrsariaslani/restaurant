#!/usr/bin/env python
"""Seed داده‌های تستی فروش برای داشبورد فروش.

~۱۲۰ سفارش در ۳۰ روز گذشته با تاریخ/ساعت/مشتری/کانال/وضعیت متنوع می‌سازد تا
چارت‌های داشبورد فروش (روند روزانه، ساعتی، مشتریان برتر، کانال‌ها) پر شوند.
اجرا:  cd /home/user/bench/sites && /home/user/bench/env/bin/python /home/user/restaurant/dev_sales_seed.py
"""
import frappe
import json
import random
from datetime import datetime, timedelta

random.seed(20260820)

CUSTOMERS = [
    ("اسنپ", "09120000001", True),
    ("زهرا قاسمی", "09120000002", False),
    ("علی رضایی", "09120000003", False),
    ("سارا محمدی", "09120000004", False),
    ("حسین کریمی", "09120000005", False),
    ("مریم احمدی", "09120000006", False),
    ("محمد رستمی", "09120000007", False),
    ("نگار موسوی", "09120000008", False),
]

CHANNELS = ["dine_in", "takeaway", "delivery"]
PAYMENTS = ["cash", "card", "credit"]
STATUSES = ["paid", "paid", "paid", "delivered", "delivered", "confirmed", "confirmed", "cancelled"]
HOURS = [10, 11, 12, 13, 13, 14, 14, 15, 16, 17, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23]


def ensure_sales_order_fields():
    """فیلدهای سفارشی Sales Order را می‌سازد (دیتابیس بعد از ریست تازه است)."""
    fields = [
        ("restaurant_customer_mobile", "Customer Mobile"),
        ("restaurant_order_type", "Order Type"),
        ("restaurant_note", "Order Note"),
        ("restaurant_status", "Restaurant Status"),
        ("restaurant_secondary_customer", "Secondary Customer"),
        ("restaurant_payment_method", "Payment Method"),
        ("restaurant_payment_status", "Payment Status"),
        ("restaurant_payment_provider", "Payment Provider"),
        ("restaurant_payment_reference", "Payment Reference"),
        ("restaurant_payment_rrn", "Payment RRN"),
        ("restaurant_courier", "Courier"),
    ]
    for fieldname, label in fields:
        if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": fieldname}):
            frappe.get_doc(
                {
                    "doctype": "Custom Field",
                    "dt": "Sales Order",
                    "fieldname": fieldname,
                    "label": label,
                    "fieldtype": "Data",
                }
            ).insert(ignore_permissions=True)
    frappe.db.commit()


def main():
    frappe.init(site="site1.local")
    frappe.connect()
    import restaurant.api as api

    ensure_sales_order_fields()

    items = frappe.get_all(
        "Item",
        filters={"restaurant_slug": ["!=", ""], "variant_of": ["in", ["", None]]},
        fields=["name", "restaurant_slug", "standard_rate"],
        limit_page_length=30,
    )
    if not items:
        print("no items — run dev_pos_bootstrap first")
        frappe.destroy()
        return

    # حذف seed قبلی (اگر ناقص بود) و ساخت دوباره
    existing = frappe.get_all(
        "Sales Order",
        filters={"restaurant_note": ["like", "%[SEED]%"]},
        fields=["name"],
        ignore_permissions=True,
    )
    for so in existing:
        frappe.db.sql("DELETE FROM `tabSales Order Item` WHERE parent = %s", (so.name,))
        frappe.db.sql("DELETE FROM `tabSales Order` WHERE name = %s", (so.name,))
    if existing:
        frappe.db.commit()
        print(f"removed {len(existing)} previous seed orders")

    created = 0
    today = datetime.now().date()
    for day_offset in range(29, -1, -1):
        day = today - timedelta(days=day_offset)
        # آخر هفته‌ها شلوغ‌تر
        weekend = day.weekday() >= 4
        order_count = random.randint(3, 5) + (2 if weekend else 0)
        for _ in range(order_count):
            cname, cmobile, is_agent = random.choice(CUSTOMERS)
            item = random.choice(items)
            qty = random.choice([1, 1, 1, 2, 2, 3])
            channel = random.choice(CHANNELS)
            hour = random.choice(HOURS)
            dt = datetime(day.year, day.month, day.day, hour, random.randint(0, 59))

            secondary = ""
            if is_agent:
                other = random.choice([c for c in CUSTOMERS if not c[2]])
                secondary = other[0]

            payload = {
                "customer_name": cname,
                "secondary_customer": secondary,
                "mobile": cmobile,
                "order_type": channel,
                "address": "آدرس نمونه: خیابان تست، پلاک ۱۲" if channel == "delivery" else "",
                "note": "[SEED] سفارش نمونه داشبورد",
                "items": [{"item_slug": item.restaurant_slug, "qty": qty}],
                "totals": {
                    "subtotal": float(item.standard_rate or 0) * qty,
                    "grand_total": float(item.standard_rate or 0) * qty,
                    "currency": "IRR",
                },
                "financial_modifiers": {},
                "guest_count": random.randint(1, 4),
            }
            try:
                result = api.create_pos_order(json.dumps(payload))
                so_name = result.get("order_id")
                # تاریخ/ساعت سفارش را تنظیم کن
                frappe.db.set_value("Sales Order", so_name, "transaction_date", str(day), update_modified=False)
                frappe.db.sql(
                    "UPDATE `tabSales Order` SET creation=%s, modified=%s WHERE name=%s",
                    (dt, dt, so_name),
                )
                # وضعیت
                status = random.choice(STATUSES)
                api._set_restaurant_order_status(so_name, status, force=True)
                # روش پرداخت متناسب با وضعیت
                if status != "confirmed":
                    method = random.choice(PAYMENTS)
                    frappe.db.set_value("Sales Order", so_name, "restaurant_payment_method", method, update_modified=False)
                    if method != "credit" and status != "cancelled":
                        frappe.db.set_value("Sales Order", so_name, "restaurant_payment_status", "paid", update_modified=False)
                created += 1
            except Exception as exc:
                frappe.db.rollback()
                print("ERR", cname, channel, str(exc)[:100])

    frappe.db.commit()
    print(f"✅ SALES SEED DONE — {created} orders created across 30 days")
    frappe.destroy()


if __name__ == "__main__":
    main()
