import frappe

# Step 1: Fix granola cookie - divide by 10
frappe.db.set_value('Item', '\u06a9\u0648\u06a9\u06cc \u06af\u0631\u0627\u0646\u0648\u0644\u0627', {
    'restaurant_nutrition_kcal': 45.0,
    'restaurant_nutrition_protein_g': 0.7,
    'restaurant_nutrition_fat_g': 2.0,
    'restaurant_nutrition_carb_g': 6.5,
})
frappe.db.commit()
print('Cookie fixed: 45 kcal')

# Step 2: Fix demiglace sauce (was 0!)
frappe.db.set_value('Item', '\u0633\u0633 \u062f\u0645\u0648\u06af\u0644\u0627\u0633', {
    'restaurant_nutrition_kcal': 150.0,
    'restaurant_nutrition_protein_g': 10.0,
    'restaurant_nutrition_fat_g': 10.0,
    'restaurant_nutrition_carb_g': 5.0,
})
frappe.db.commit()
print('Demiglace fixed: 150 kcal')

# Step 3: Fix tomato paste / \u0628\u0644\u0627\u0644 \u0628\u0627\u0645\u0648\u0646 (was 0!)
# Check items with 0 kcal that should have nutrition
zero_items = frappe.db.sql("SELECT name, item_group FROM `tabItem` WHERE disabled = 0 AND has_variants = 0 AND is_stock_item = 1 AND restaurant_nutrition_kcal = 0 AND EXISTS (SELECT 1 FROM `tabBOM Item` bi WHERE bi.item_code = `tabItem`.name)", as_dict=True)
print('\nItems with 0 kcal that are in BOMs:')
for z in zero_items:
    print('  ' + z.name + ' (' + z.item_group + ')')

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
    return (round(total_kcal / bom_qty, 1), round(total_p / bom_qty, 1), round(total_f / bom_qty, 1), round(total_c / bom_qty, 1))

bom_products = frappe.db.sql("SELECT DISTINCT b.item FROM `tabBOM` b WHERE b.is_active = 1", as_dict=True)
updated = 0
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

print('\nTotal products updated: ' + str(updated))
