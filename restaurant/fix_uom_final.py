import frappe

def fix_all_uom():
    items = frappe.db.sql("SELECT name, stock_uom, COALESCE(CAST(restaurant_nutrition_kcal AS DECIMAL(10,1)), 0) as kcal, COALESCE(CAST(restaurant_nutrition_protein_g AS DECIMAL(10,1)), 0) as protein, COALESCE(CAST(restaurant_nutrition_fat_g AS DECIMAL(10,1)), 0) as fat, COALESCE(CAST(restaurant_nutrition_carb_g AS DECIMAL(10,1)), 0) as carbs FROM tabItem WHERE disabled = 0 AND has_variants = 0 AND is_stock_item = 1 AND restaurant_nutrition_kcal > 0", as_dict=True)
    
    result = []
    result.append('Total items with nutrition: ' + str(len(items)))
    
    fixed = 0
    for item in items:
        uom = item.stock_uom
        if not uom:
            continue
        
        kcal = float(item.kcal or 0)
        protein = float(item.protein or 0)
        fat = float(item.fat or 0)
        carbs = float(item.carbs or 0)
        
        if uom == '\u06af\u0631\u0645':
            kcal_new = round(kcal / 100, 2)
            protein_new = round(protein / 100, 2)
            fat_new = round(fat / 100, 2)
            carbs_new = round(carbs / 100, 2)
        elif uom == '\u06a9\u06cc\u0644\u0648\u06af\u0631\u0645':
            kcal_new = round(kcal * 10, 2)
            protein_new = round(protein * 10, 2)
            fat_new = round(fat * 10, 2)
            carbs_new = round(carbs * 10, 2)
        elif uom == '\u0644\u06cc\u062a\u0631':
            kcal_new = round(kcal * 10, 2)
            protein_new = round(protein * 10, 2)
            fat_new = round(fat * 10, 2)
            carbs_new = round(carbs * 10, 2)
        elif uom == '\u0645\u06cc\u0644\u06cc\u200c\u0644\u06cc\u062a\u0631':
            kcal_new = round(kcal / 100, 2)
            protein_new = round(protein / 100, 2)
            fat_new = round(fat / 100, 2)
            carbs_new = round(carbs / 100, 2)
        elif uom == '\u0639\u062f\u062f':
            kcal_new = round(kcal, 2)
            protein_new = round(protein, 2)
            fat_new = round(fat, 2)
            carbs_new = round(carbs, 2)
        else:
            continue
        
        try:
            frappe.db.set_value('Item', item.name, {
                'restaurant_nutrition_kcal': kcal_new,
                'restaurant_nutrition_protein_g': protein_new,
                'restaurant_nutrition_fat_g': fat_new,
                'restaurant_nutrition_carb_g': carbs_new,
            })
            frappe.db.commit()
            fixed += 1
        except Exception as e:
            result.append('ERR: ' + item.name + ' -> ' + str(e))
    
    result.append('Fixed ' + str(fixed) + ' items')
    return '\n'.join(result)

print(fix_all_uom())
