import frappe

def is_non_food(name):
    keywords = ['\u0644\u06cc\u0648\u0627\u0646', '\u062f\u0631\u0628', '\u06a9\u0627\u0633\u0647', '\u062c\u0639\u0628\u0647', '\u06cc\u062e', '\u0646\u062e', '\u0627\u0633\u062a\u06cc\u06a9', '\u067e\u0627\u0631\u0686', '\u06a9\u0627\u063a\u0630', '\u0635\u0641\u062d\u0647', '\u0633\u0633\u062a']
    for kw in keywords:
        if kw in name:
            return True
    return False

def get_uom_conversion(item_code, bom_uom):
    stock_uom = frappe.db.get_value('Item', item_code, 'stock_uom')
    if not stock_uom or stock_uom == bom_uom:
        return 1.0
    to_gram = {'\u06af\u0631\u0645': 1.0, '\u06a9\u06cc\u0644\u0648\u06af\u0631\u0645': 1000.0, '\u0644\u06cc\u062a\u0631': 1000.0, '\u0645\u06cc\u0644\u06cc\u200c\u0644\u06cc\u062a\u0631': 1.0, '\u0639\u062f\u062f': 1.0}
    stock_factor = to_gram.get(stock_uom, 1.0)
    bom_factor = to_gram.get(bom_uom, 1.0)
    if stock_factor and bom_factor:
        return bom_factor / stock_factor
    return 1.0

def calc_product_nutrition(item_name):
    bom = frappe.db.get_value('BOM', {'item': item_name, 'is_active': 1}, ['name', 'quantity'], as_dict=True)
    if not bom:
        return None
    items = frappe.db.sql("SELECT bi.item_code, bi.qty, bi.uom, i.restaurant_nutrition_kcal, i.restaurant_nutrition_protein_g, i.restaurant_nutrition_fat_g, i.restaurant_nutrition_carb_g FROM `tabBOM Item` bi JOIN `tabItem` i ON i.name = bi.item_code WHERE bi.parent = %s", (bom.name,), as_dict=True)
    total_kcal = 0
    total_p = 0
    total_f = 0
    total_c = 0
    for it in items:
        if is_non_food(it.item_code):
            continue
        qty = float(it.qty or 1)
        bom_uom = it.uom
        conv = get_uom_conversion(it.item_code, bom_uom)
        adjusted_qty = qty * conv
        total_kcal += float(it.restaurant_nutrition_kcal or 0) * adjusted_qty
        total_p += float(it.restaurant_nutrition_protein_g or 0) * adjusted_qty
        total_f += float(it.restaurant_nutrition_fat_g or 0) * adjusted_qty
        total_c += float(it.restaurant_nutrition_carb_g or 0) * adjusted_qty
    bom_qty = float(bom.quantity or 1)
    return (round(total_kcal / bom_qty, 1), round(total_p / bom_qty, 1), round(total_f / bom_qty, 1), round(total_c / bom_qty, 1))
bom_products = frappe.db.sql("SELECT DISTINCT b.item FROM `tabBOM` b WHERe b.is_active = 1", as_dict=True)
pdated = 0
for bp in bom_products:
    result = calc_product_nutrition(bp.item)
    if result is None:
        continue
    kcal, protein, fat, carbs = result
    try:
        frappe.db.set_value('Item', bp.item, {
            'restaurant_nutrition_kcal': kcal,
            'restaurant_nutrition_protein_g': protein,
            'restaurant_nutrition_fat_g': fat,
            'restaurant_nutrition_carb_g': carbs,
        })
        frappe.db.commit()
        updated += 1
    except Exception as e:
        print('ERR: ' + bp.item + ' -> ' + str(e))

print('Updated ' + str(updated) + ' products')
