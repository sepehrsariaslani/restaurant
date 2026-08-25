import frappe
import json

def get_all_items_data():
    items = frappe.db.sql("""
        SELECT 
            i.name,
            i.description,
            i.item_group,
            i.restaurant_nutrition_kcal
        FROM `tabItem` i
        WHERE i.restaurant_enabled = 1 
        ORDER BY i.item_group, i.name
    """, as_dict=True)

    results = []
    for item in items:
        bom_items = frappe.db.sql("""
            SELECT b.item, b.qty, b.uom, i.item_name
            FROM `tabBOM Item` b
            LEFT JOIN `tabItem` i ON i.name = b.item
            WHERE b.parent = %s
        """, (item['name'],), as_dict=True)
        
        materials = []
        for bi in bom_items:
            name = bi.get('item_name') or bi['item']
            qty = bi['qty']
            uom = bi['uom']
            materials.append(name + " (" + str(qty) + " " + uom + ")")
        
        desc = item.get('description') or ''
        has_html = '<p>' in desc
        
        results.append({
            'name': item['name'],
            'group': item.get('item_group', ''),
            'kcal': item.get('restaurant_nutrition_kcal', 0),
            'has_html_desc': has_html,
            'desc_preview': desc[:120] if desc else '',
            'bom_materials': materials[:10]
        })
    
    print(json.dumps(results, ensure_ascii=False))

get_all_items_data()
