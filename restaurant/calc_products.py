import frappe

def is_non_food(name):
    keywords = ['\u0644\u06cc\u0648\u0627\u0646', '\u062f\u0631\u0628', '\u06a9\u0627\u0633\u0647', '\u062c\u0639\u0628\u0647', '\u06cc\u062e', '\u0646\u062e', '\u0627\u0633\u062a\u06cc\u06a9', '\u067e\u0627\u0631\u0686', '\u06a9\u0627\u063a\u0630', '\u0635\u0641\u062d\u0647', '\u0633\u0633\u062a']
    for kw in keywords:
        if kw in name:
            return True
    return False

def calc_product_nutrition(item_name):
    bom = frappe.db.get_value('BOM', {'item': item_name, 'is_active': 1}, ['name', 'quantity'], as_dict=True)
    if not bom:
        return None
    
    items = frappe.db.sql("SELECT bi.item_code, bi.qty, i.restaurant_nutrition_kcal, i.restaurant_nutrition_protein_g, i.restaurant_nutrition_fat_g, i.restaurant_nutrition_carb_g FROM `tabBOM Item` bi JOIN `tabItem` i ON i.name = bi.item_code WHERE bi.parent = %s", (bom.name,), as_dict=True)
    
    total_kcal = 0
    total_p = 0
    total_f = 0
    total_c = 0
    
    for it in items:
        if is_non_food(it.item_code):
            continue
        qty = float(it.qty or 1)
        total_kcal += float(it.restaurant_nutrition_kcal or 0) * qty
        total_p += float(it.restaurant_nutrition_protein_g or 0) * qty
        total_f += float(it.restaurant_nutrition_fat_g or 0) * qty
        total_c += float(it.restaurant_nutrition_carb_g or 0) * qty
    
    bom_qty = float(bom.quantity or 1)
    return (total_kcal / bom_qty, total_p / bom_qty, total_f / bom_qty, total_c / bom_qty)

# Get all BOM products
bom_products = frappe.db.sql("SELECT DISTINCT b.item FROM `tabBOM` b WHERE b.is_active = 1", as_dict=True)

updated = 0
errors = []

for bp in bom_products:
    item_name = bp.item
    result = calc_product_nutrition(item_name)
    if result is None:
        continue
    
    kcal, protein, fat, carbs = result
    
    try:
        frappe.db.set_value('Item', item_name, {
            'restaurant_nutrition_kcal': round(kcal, 1),
            'restaurant_nutrition_protein_g': round(protein, 1),
            'restaurant_nutrition_fat_g': round(fat, 1),
            'restaurant_nutrition_carb_g': round(carbs, 1),
        })
        frappe.db.commit()
        updated += 1
        print('OK: ' + item_name + ' -> kcal=' + str(round(kcal,1)) + ' P=' + str(round(protein,1)) + ' F=' + str(round(fat,1)) + ' C=' + str(round(carbs,1)))
    except Exception as e:
        errors.append(item_name + ': ' + str(e))

print('\nTotal updated: ' + str(updated))
if errors:
    print('Errors:')
    for e in errors:
        print('  ' + e)
