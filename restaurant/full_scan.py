import frappe

def is_non_food(name):
    keywords = ['\u0644\u06cc\u0648\u0627\u0646', '\u062f\u0631\u0628', '\u06a9\u0627\u0633\u0647', '\u062c\u0639\u0628\u0647', '\u06cc\u062e', '\u0646\u062e', '\u0627\u0633\u062a\u06cc\u06a9', '\u067e\u0627\u0631\u0686', '\u06a9\u0627\u063a\u0630', '\u0635\u0641\u062d\u0647', '\u0633\u0633\u062a']
    for kw in keywords:
        if kw in name:
            return True
    return False

# Get all BOMs with their items
boms = frappe.db.sql("SELECT b.name, b.item, b.quantity as bom_qty FROM `tabBOM` b WHERE b.is_active = 1 ORDER BY b.item", as_dict=True)

output = []

for bom in boms:
    items = frappe.db.sql("SELECT bi.item_code, bi.qty, bi.uom, COALESCE(CAST(i.restaurant_nutrition_kcal AS DECIMAL(10,1)), 0) as kcal, COALESCE(CAST(i.restaurant_nutrition_protein_g AS DECIMAL(10,1)), 0) as protein FROM `tabBOM Item` bi JOIN `tabItem` i ON i.name = bi.item_code WHERE bi.parent = %s", (bom.name,), as_dict=True)
    
    total_kcal = 0
    item_details = []
    
    for it in items:
        if is_non_food(it.item_code):
            continue
        qty = float(it.qty or 1)
        kcal = float(it.kcal or 0)
        item_total_kcal = kcal * qty
        total_kcal += item_total_kcal
        item_details.append(it.item_code + ' | ' + str(it.qty) + ' ' + it.uom + ' | ' + str(kcal) + ' kcal/uni | t=' + str(round(item_total_kcal,1)))
    
    bom_qty = float(bom.bom_qty or 1)
    per_serving = total_kcal / bom_qty
    
    output.append('=== ' + bom.item + ' ===')
    output.append('  Total: ' + str(round(total_kcal,1)) + ' kcal / ' + str(bom_qty) + ' = ' + str(round(per_serving,1)) + ' per serving')
    for d in item_details:
        output.append('  ' + d)
    output.append('')

result = '\n'.join(output)
print(result)
