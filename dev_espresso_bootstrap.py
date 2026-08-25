#!/usr/bin/env python
"""bootstrap_espresso.py — ساخت قالب اسپرسو + واریانت‌های سینگل/دبل + قهوه ربوستا/عربیکا.
اجرا: cd /home/user/bench/sites && /home/user/bench/env/bin/python /home/user/restaurant/dev_espresso_bootstrap.py
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


def ensure_item(name, item_name, rate=None, item_group="All Item Groups", slug=None, enabled=1, stock_uom="Nos", **kwargs):
    # attributes قبل از insert لازم است (برای قالب‌های دارای variant)
    attributes = kwargs.pop("attributes", None)
    if frappe.db.exists("Item", name):
        item = frappe.get_doc("Item", name)
    else:
        payload = {
            "doctype": "Item",
            "item_code": name,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": stock_uom,
            "is_stock_item": 0,
            **kwargs,
        }
        if attributes:
            payload["attributes"] = [
                {"attribute": a, "attribute_value": v} for a, v in attributes.items()
            ]
        item = frappe.get_doc(payload).insert(ignore_permissions=True)
    if rate:
        item.standard_rate = rate
    if slug is not None:
        item.restaurant_slug = slug
    if "restaurant_enabled" in kwargs:
        item.restaurant_enabled = kwargs["restaurant_enabled"]
    if kwargs.get("allow_alternative_item"):
        item.allow_alternative_item = 1
    item.restaurant_enabled = 1 if enabled else 0
    item.show_in_website = 1
    item.save(ignore_permissions=True)
    return item


def ensure_attribute(attr_name, values):
    """Item Attribute با مقادیر مشخص + فلگ‌های نمایش در وب"""
    if frappe.db.exists("Item Attribute", attr_name):
        doc = frappe.get_doc("Item Attribute", attr_name)
    else:
        doc = frappe.get_doc({"doctype": "Item Attribute", "attribute_name": attr_name})
    # فلگ‌های رستورانی برای نمایش selector در سفارشی‌سازی
    if frappe.db.has_column("Item Attribute", "restaurant_show_in_website"):
        doc.restaurant_show_in_website = 1
    if frappe.db.has_column("Item Attribute", "restaurant_selection_only"):
        doc.restaurant_selection_only = 1
    existing_values = {v.attribute_value for v in doc.item_attribute_values}
    for value in values:
        if value not in existing_values:
            doc.append("item_attribute_values", {"attribute_value": value, "abbr": value[:2]})
    doc.save(ignore_permissions=True)
    return doc.name


def ensure_variant_attributes(item_name, attributes):
    """فیلد variant_attributes روی آیتم"""
    item = frappe.get_doc("Item", item_name)
    item.attributes = []
    for attr, value in attributes.items():
        item.append("attributes", {"attribute": attr, "attribute_value": value})
    item.save(ignore_permissions=True)


def ensure_bom(name, item_code, qty, items, is_default=1):
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
    bom.items = []
    for it in items:
        bom.append("items", {
            "item_code": it["item_code"],
            "qty": it["qty"],
            "uom": it.get("uom", "Nos"),
            "rate": it.get("rate", 0),
            "amount": it.get("rate", 0) * it["qty"],
            "do_not_explode": 1,
            "allow_alternative_item": 1 if it.get("allow_alternative_item") else 0,
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


def ensure_item_alternative(base_item, alternative_item):
    """Item Alternative: base_item → alternative_item (رکورد مستقل، نه child)"""
    if not frappe.db.exists("DocType", "Item Alternative"):
        print("  !! Item Alternative doctype missing")
        return
    existing = frappe.db.get_value(
        "Item Alternative",
        {"item_code": base_item, "alternative_item_code": alternative_item},
        "name",
    )
    if existing:
        doc = frappe.get_doc("Item Alternative", existing)
    else:
        doc = frappe.get_doc({
            "doctype": "Item Alternative",
            "item_code": base_item,
            "alternative_item_code": alternative_item,
            "two_way": 1,
        })
    doc.item_code = base_item
    doc.alternative_item_code = alternative_item
    doc.two_way = 1
    doc.save(ignore_permissions=True)
    print(f"  alternative: {base_item} → {alternative_item}")


def main():
    # ── 1) فیلدهای سفارشی ──
    ensure_field("Item", "restaurant_requires_bom", "نیازمند BOM", "Check", "0")
    ensure_field("Item", "restaurant_enabled", "نمایش در منو", "Check", "1")
    print("custom fields OK")

    # ── 2) قهوه‌ها (مواد اولیه) ──
    robusta = ensure_item(
        "REST-ING-COFFEE-ROBUSTA", "قهوه ربوستا", rate=2400000,
        item_group="All Item Groups", slug="coffee-robusta", enabled=1,
        stock_uom="Kg", allow_alternative_item=1,
    )
    arabica = ensure_item(
        "REST-ING-COFFEE-ARABICA", "قهوه عربیکا", rate=3200000,
        item_group="All Item Groups", slug="coffee-arabica", enabled=1,
        stock_uom="Kg", allow_alternative_item=1,
    )
    ensure_item_price(robusta.name, 2400000)
    ensure_item_price(arabica.name, 3200000)
    print("coffees OK:", robusta.name, arabica.name)

    # ── 3) جایگزین: ربوستا → عربیکا ──
    ensure_item_alternative(robusta.name, arabica.name)

    # ── 4) ویژگی «سایز اسپرسو» ──
    ensure_field("Item Attribute", "restaurant_show_in_website", "نمایش در وب", "Check", "1")
    ensure_field("Item Attribute", "restaurant_selection_only", "فقط انتخاب (بدون قیمت)", "Check", "1")
    ensure_field("Item Attribute Value", "restaurant_is_default", "پیش‌فرض", "Check", "0")
    attr = ensure_attribute("سایز اسپرسو", ["سینگل", "دبل"])
    # «سینگل» پیش‌فرض باشد
    if frappe.db.has_column("Item Attribute Value", "restaurant_is_default"):
        frappe.db.set_value(
            "Item Attribute Value",
            {"parent": "سایز اسپرسو", "attribute_value": "سینگل"},
            "restaurant_is_default", 1,
        )
        frappe.db.set_value(
            "Item Attribute Value",
            {"parent": "سایز اسپرسو", "attribute_value": "دبل"},
            "restaurant_is_default", 0,
        )
    print("attribute OK:", attr)

    # ── 5) قالب اسپرسو ──
    template = ensure_item(
        "REST-ESPRESSO", "اسپرسو", rate=180000,
        item_group="All Item Groups", slug="espresso", enabled=1,
        has_variants=1, variant_based_on="Item Attribute",
        attributes={"سایز اسپرسو": "سینگل"},
    )
    template.restaurant_requires_bom = 1
    template.restaurant_category = "نوشیدنی"
    template.save(ignore_permissions=True)
    print("template OK:", template.name)

    # ── 6) واریانت‌ها: سینگل و دبل ──
    single = ensure_item(
        "REST-ESPRESSO-SINGLE", "اسپرسو سینگل", rate=180000,
        item_group="All Item Groups", slug="espresso-single", enabled=1,
        variant_of=template.name, has_variants=0,
        attributes={"سایز اسپرسو": "سینگل"},
    )
    single.restaurant_requires_bom = 1
    single.restaurant_category = "نوشیدنی"
    single.save(ignore_permissions=True)

    double = ensure_item(
        "REST-ESPRESSO-DOUBLE", "اسپرسو دبل", rate=320000,
        item_group="All Item Groups", slug="espresso-double", enabled=1,
        variant_of=template.name, has_variants=0,
        attributes={"سایز اسپرسو": "دبل"},
    )
    double.restaurant_requires_bom = 1
    double.restaurant_category = "نوشیدنی"
    double.save(ignore_permissions=True)

    ensure_item_price(single.name, 180000)
    ensure_item_price(double.name, 320000)
    print("variants OK:", single.name, double.name)

    # ── 7) BOM ها ──
    # سینگل: 10 گرم ربوستا (قابل جایگزینی با عربیکا)
    bom_single = ensure_bom(
        "BOM-REST-ESPRESSO-SINGLE",
        single.name,
        1,
        [
            {"item_code": robusta.name, "qty": 0.01, "uom": "Kg", "rate": 2400000, "allow_alternative_item": 1},
        ],
        is_default=1,
    )
    # دبل: 20 گرم ربوستا (نه default — default فقط سینگل است)
    bom_double = ensure_bom(
        "BOM-REST-ESPRESSO-DOUBLE",
        double.name,
        1,
        [
            {"item_code": robusta.name, "qty": 0.02, "uom": "Kg", "rate": 2400000, "allow_alternative_item": 1},
        ],
        is_default=0,
    )
    print("BOMs OK:", bom_single, bom_double)

    frappe.db.commit()
    print("\n✅ ESPRESSO TEST DATA READY")


main()
frappe.destroy()
