import frappe
frappe.init(site='veederakht.ir', sites_path='/home/frappe/frappe-bench/sites')
frappe.connect()

# Get the main BOM
bom_name = 'BOM-BOWL-BEEF-TERIYAKI-001'
bom_items = frappe.db.sql('''
    SELECT bi.idx, bi.item_code, bi.qty, bi.uom
    FROM `tabBOM Item` bi
    WHERE bi.parent = %s
    ORDER BY bi.idx
''', bom_name, as_dict=True)

print('=== MAIN BOM ITEMS ===')
print(f'BOM: {bom_name}')
for bi in bom_items:
    item = frappe.db.get_value('Item', {'name': bi['item_code']}, 
        ['name', 'item_name', 'stock_uom', 'restaurant_nutrition_kcal',
         'restaurant_nutrition_protein_g', 'restaurant_nutrition_carb_g', 'restaurant_nutrition_fat_g'], 
        as_dict=True)
    if item:
        uom_match = 'OK' if item['stock_uom'] == bi['uom'] else 'MISMATCH'
        print(f"{bi['idx']}. {bi['item_code']} ({item['item_name']})")
        print(f"    Qty: {bi['qty']} {bi['uom']} | Stock UOM: {item['stock_uom']} [{uom_match}]")
        print(f"    kcal={item['restaurant_nutrition_kcal']}, p={item['restaurant_nutrition_protein_g']}, c={item['restaurant_nutrition_carb_g']}, f={item['restaurant_nutrition_fat_g']}")
    else:
        print(f"{bi['idx']}. {bi['item_code']}: ITEM NOT FOUND IN SYSTEM")

frappe.destroy()