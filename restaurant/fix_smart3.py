import frappe

def run():
    items = frappe.db.sql("SELECT name, stock_uom, COALESCE(CAST(restaurant_nutrition_kcal AS DECIMAL(10,1)), 0) as kcal FROM tabItem WHERE disabled = 0 AND has_variants = 0 AND is_stock_item = 1 AND restaurant_nutrition_kcal > 0", as_dict=True)
    fixes = {}
    for item in items:
        name = item.name
        uom = item.stock_uom
        kcal = float(item.kcal or 0)
        ig = frappe.db.get_value("Item", name, "item_group") or ""
        skip = ["نوشیدنی\u200cها", "غذاهای اصلی", "پیش\u200cغذا", "دسر", "سالاد", "ساندویچ", "صبحانه", "مکمل", "قهوه", "بار سرد", "بار گرم", "اسموتی", "آبمیوه"]
        if ig in skip:
            continue
        if uom == "گرم" and kcal > 500:
            fixes[name] = kcal / 100
        elif uom == "کیلوگرم" and kcal > 5000:
            fixes[name] = kcal / 100
        elif uom == "لیتر" and kcal > 2000:
            fixes[name] = kcal / 100
        elif uom == "میلی\u200cلیتر" and kcal > 50:
            fixes[name] = kcal / 100
    print("Items to fix: " + str(len(fixes)))
    updated = 0
    for name, new_kcal in fixes.items():
        try:
            frappe.db.set_value("Item", name, {"restaurant_nutrition_kcal": round(new_kcal, 2)})
            frappe.db.commit()
            updated += 1
        except Exception as e:
            print("ERR: " + name + " -> " + str(e))
    print("Fixed: " + str(updated))
