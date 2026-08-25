import frappe

def run():
    item_name = 'برنج پخته شده'
    
    if not frappe.db.exists('Item', item_name):
        item = frappe.new_doc('Item')
        item.item_code = item_name
        item.item_name = item_name
        item.item_group = 'مواد اولیه'
        item.stock_uom = 'گرم'
        item.is_stock_item = 1
        item.restaurant_nutrition_kcal = 1.30
        item.restaurant_nutrition_protein_g = 0.027
        item.restaurant_nutrition_fat_g = 0.003
        item.restaurant_nutrition_carb_g = 0.28
        item.insert()
        frappe.db.commit()
        print('Created: ' + item_name)
    else:
        frappe.db.set_value('Item', item_name, {
            'restaurant_nutrition_kcal': 1.30,
            'restaurant_nutrition_protein_g': 0.027,
            'restaurant_nutrition_fat_g': 0.003,
            'restaurant_nutrition_carb_g': 0.28,
        })
        frappe.db.commit()
        print('Updated: ' + item_name)
    
    bom_name = 'BOM-برنج پخته شده-001'
    if frappe.db.exists('BOM', bom_name):
        frappe.delete_doc('BOM', bom_name)
        frappe.db.commit()
    
    bom = frappe.new_doc('BOM')
    bom.item = item_name
    bom.quantity = 250
    bom.uom = 'گرم'
    bom.is_active = 1
    bom.is_default = 1
    bom.with_operations = 0
    bom.append('items', {
        'item_code': 'برنج سفید',
        'qty': 100,
        'uom': 'گرم',
    })
    bom.insert()
    frappe.db.commit()
    print('Created BOM: ' + bom_name)
    
    raw_rice_boms = frappe.db.sql("SELECT DISTINCT b.name, b.item, bi.qty as raw_qty FROM `tabBOM` b JOIN `tabBOM Item` bi ON bi.parent = b.name WHERE bi.item_code = 'برنج سفید' AND b.is_active = 1", as_dict=True)
    
    print('BOMs with raw rice: ' + str(len(raw_rice_boms)))
    
    for bom_info in raw_rice_boms:
        bom_doc = frappe.get_doc('BOM', bom_info.name)
        raw_qty = bom_info.raw_qty
        
        for itm in list(bom_doc.items):
            if itm.item_code == 'برنج سفید':
                bom_doc.items.remove(itm)
                break
        
        bom_doc.append('items', {
            'item_code': item_name,
            'qty': raw_qty,
            'uom': 'گرم',
        })
        bom_doc.save()
        frappe.db.commit()
        print('  ' + bom_info.item + ': ' + str(raw_qty) + 'g raw -> ' + str(raw_qty) + 'g cooked')

run()
