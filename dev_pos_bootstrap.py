#!/usr/bin/env python
"""bootstrap_pos_test_data.py — ساخت داده تست POS (modifier + BOM) برای محصولات نمونه.
اجرا: cd /home/user/bench/sites && /home/user/bench/env/bin/python /home/user/restaurant/dev_pos_bootstrap.py
"""
import frappe

frappe.init(site="site1.local", sites_path="/home/user/bench/sites")
frappe.connect()


def ensure_field(doctype, fieldname, label, fieldtype="Check", default="0", options=None):
    if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": doctype,
        "module": "Restaurant",
        "fieldname": fieldname,
        "label": label,
        "fieldtype": fieldtype,
        "default": default,
        "options": options or "",
    }).insert(ignore_permissions=True)


def ensure_item(name, item_name, rate, is_stock=0, item_group="All Item Groups", disabled=0):
    if frappe.db.exists("Item", name):
        item = frappe.get_doc("Item", name)
    else:
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": name,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": is_stock,
            "disabled": disabled,
            "include_item_in_manufacturing": 1,
        }).insert(ignore_permissions=True)
    if rate:
        # قیمت فروش
        item.standard_rate = rate
    item.save(ignore_permissions=True)
    return item


def ensure_item_price(item_code, rate, price_list="Standard Selling"):
    if not frappe.db.exists("Price List", price_list):
        frappe.get_doc({
            "doctype": "Price List",
            "price_list_name": price_list,
            "selling": 1,
            "currency": "IRR",
        }).insert(ignore_permissions=True)
    existing = frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list, "selling": 1}, "name")
    if existing:
        doc = frappe.get_doc("Item Price", existing)
    else:
        doc = frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": rate,
            "selling": 1,
            "currency": "IRR",
        })
    doc.price_list_rate = rate
    doc.save(ignore_permissions=True)


def ensure_modifier_group(name, title, mode, required, options, min_select=0, max_select=1):
    existing = frappe.db.get_value("Restaurant Modifier Group", {"title": title}, "name")
    if existing:
        group = frappe.get_doc("Restaurant Modifier Group", existing)
        group.options = []
    else:
        group = frappe.get_doc({
            "doctype": "Restaurant Modifier Group",
            "title": title,
            "selection_mode": mode,
            "required": required,
            "min_select": min_select,
            "max_select": max_select,
            "is_active": 1,
        })
    group.selection_mode = mode
    group.required = required
    group.min_select = min_select
    group.max_select = max_select
    group.is_active = 1
    for opt in options:
        group.append("options", opt)
    group.save(ignore_permissions=True)
    return group.name


def ensure_bom(name, item_code, qty, items, modifier_rows, is_default=1):
    existing_name = frappe.db.get_value("BOM", {"name": name}, "name") or \
        frappe.db.get_value("BOM", {"item": item_code, "is_default": is_default}, "name")
    if existing_name:
        bom = frappe.get_doc("BOM", existing_name)
    else:
        company = frappe.db.get_value("Company", {}, "name") or "Your Company"
        bom = frappe.get_doc({
            "doctype": "BOM",
            "item": item_code,
            "quantity": qty,
            "is_active": 1,
            "is_default": is_default,
            "company": company,
            "rm_cost_as_per": "Valuation Rate",
        })
    bom.item = item_code
    bom.quantity = qty
    bom.is_active = 1
    bom.is_default = is_default
    bom.rm_cost_as_per = "Valuation Rate"
    # items
    bom.items = []
    for it in items:
        bom.append("items", {
            "item_code": it["item_code"],
            "qty": it["qty"],
            "uom": "Nos",
            "rate": it.get("rate", 0),
            "amount": it.get("rate", 0) * it["qty"],
            "do_not_explode": 1,
        })
    # modifier rows (linked groups)
    bom.restaurant_modifier_rows = []
    for grp in modifier_rows:
        bom.append("restaurant_modifier_rows", {
            "modifier_group": grp,
        })
    bom.save(ignore_permissions=True)
    if bom.docstatus == 0:
        bom.submit()
    if bom.name != name and not frappe.db.exists("BOM", name):
        try:
            from frappe.model.rename_doc import rename_doc
            rename_doc("BOM", bom.name, name, force=True, ignore_permissions=True)
            frappe.db.commit()
            return name
        except Exception:
            pass
    return bom.name


def main():
    # ── 1) فیلدهای سفارشی ──
    ensure_field("Item", "restaurant_requires_bom", "نیازمند BOM", "Check", "0")
    print("custom fields OK")

    # ── 2) مواد اولیه ──
    ingredients = [
        ("REST-ING-MOZZARELLA", "پنیر موزارلا", 480000, "All Item Groups"),
        ("REST-ING-PIZZA-SAUCE", "سس پیتزا", 120000, "All Item Groups"),
        ("REST-ING-DOUGH", "خمیر پیتزا", 90000, "All Item Groups"),
        ("REST-ING-GF-DOUGH", "خمیر گلوتن‌فری", 180000, "All Item Groups"),
        ("REST-ING-MUSHROOM", "قارچ", 350000, "All Item Groups"),
        ("REST-ING-PEPPERONI", "پپرونی", 520000, "All Item Groups"),
        ("REST-ING-EXTRA-CHEESE", "پنیر اضافه", 600000, "All Item Groups"),
        ("REST-ING-MARINARA", "سس مارینارا", 150000, "All Item Groups"),
        ("REST-ING-CHEDDAR", "پنیر چدار", 550000, "All Item Groups"),
        ("REST-ING-PARMESAN", "پنیر پارمزان", 700000, "All Item Groups"),
    ]
    for code, name, rate, grp in ingredients:
        ensure_item(code, name, rate, is_stock=0, item_group=grp)
    # قیمت فروش مواد اولیه (برای محاسبه delta گزینه‌ها)
    for code, _name, rate, _grp in ingredients:
        ensure_item_price(code, rate)
    print("item prices OK:", len(ingredients))

    # ── 3) Modifier Groups ──
    dough_group = ensure_modifier_group(
        "REST-MOD-DOUGH",
        "نوع خمیر",
        "single",
        1,
        [
            {"option_name": "خمیر معمولی", "action_type": "add_on", "option_item": "",
             "price_delta": 0, "is_default": 1, "is_active": 1},
            {"option_name": "خمیر گلوتن‌فری", "action_type": "bom_variant", "option_item": "REST-ING-GF-DOUGH",
             "price_delta": 50000, "is_active": 1},
        ],
    )
    toppings_group = ensure_modifier_group(
        "REST-MOD-TOPPINGS",
        "افزودنی‌ها",
        "multi",
        0,
        [
            {"option_name": "قارچ", "action_type": "add_on", "option_item": "REST-ING-MUSHROOM",
             "option_qty": 0.1, "price_delta": 0, "is_active": 1},
            {"option_name": "پپرونی", "action_type": "add_on", "option_item": "REST-ING-PEPPERONI",
             "option_qty": 0.1, "price_delta": 0, "is_active": 1},
            {"option_name": "پنیر اضافه", "action_type": "add_on", "option_item": "REST-ING-EXTRA-CHEESE",
             "option_qty": 0.1, "price_delta": 0, "is_active": 1},
        ],
        min_select=0,
        max_select=3,
    )
    sauce_group = ensure_modifier_group(
        "REST-MOD-SAUCE",
        "سس اضافه",
        "single",
        0,
        [
            {"option_name": "سس مارینارا", "action_type": "add_on", "option_item": "REST-ING-MARINARA",
             "option_qty": 0.1, "price_delta": 0, "is_active": 1},
        ],
    )
    print("modifier groups OK:", dough_group, toppings_group, sauce_group)

    # ── 4) BOM ها ──
    # BOM پیش‌فرض پیتزا چهار پنیر
    bom_normal = ensure_bom(
        "BOM-REST-PIZZA-FOUR-CHEESE",
        "REST-PIZZA_FOUR_CHEESE_PREMIUM",
        1,
        [
            {"item_code": "REST-ING-DOUGH", "qty": 1, "rate": 90000},
            {"item_code": "REST-ING-PIZZA-SAUCE", "qty": 0.12, "rate": 120000},
            {"item_code": "REST-ING-MOZZARELLA", "qty": 0.15, "rate": 480000},
            {"item_code": "REST-ING-CHEDDAR", "qty": 0.1, "rate": 550000},
            {"item_code": "REST-ING-PARMESAN", "qty": 0.08, "rate": 700000},
        ],
        [dough_group, toppings_group, sauce_group],
        is_default=1,
    )
    # BOM جایگزین (خمیر گلوتن‌فری)
    bom_gf = ensure_bom(
        "BOM-REST-PIZZA-FOUR-CHEESE-GF",
        "REST-PIZZA_FOUR_CHEESE_PREMIUM",
        1,
        [
            {"item_code": "REST-ING-GF-DOUGH", "qty": 1, "rate": 180000},
            {"item_code": "REST-ING-PIZZA-SAUCE", "qty": 0.12, "rate": 120000},
            {"item_code": "REST-ING-MOZZARELLA", "qty": 0.15, "rate": 480000},
            {"item_code": "REST-ING-CHEDDAR", "qty": 0.1, "rate": 550000},
            {"item_code": "REST-ING-PARMESAN", "qty": 0.08, "rate": 700000},
        ],
        [dough_group, toppings_group, sauce_group],
        is_default=0,
    )
    # لینک BOM جایگزین روی گزینه خمیر گلوتن‌فری
    dough_doc = frappe.get_doc("Restaurant Modifier Group", dough_group)
    for opt in dough_doc.options:
        if opt.option_name == "خمیر گلوتن‌فری":
            opt.action_type = "bom_variant"
            opt.alternative_bom = bom_gf
            opt.price_delta = 50000
    dough_doc.save(ignore_permissions=True)
    print("BOMs OK:", bom_normal, "| GF:", bom_gf)

    # ── 5) اتصال به محصول ──
    pizza = frappe.get_doc("Item", "REST-PIZZA_FOUR_CHEESE_PREMIUM")
    pizza.restaurant_requires_bom = 1
    pizza.save(ignore_permissions=True)
    print("item linked OK")

    frappe.db.commit()
    print("\n✅ POS TEST DATA READY")


main()
frappe.destroy()
