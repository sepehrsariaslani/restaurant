import frappe

def check_problematic():
    items = ['\u0686\u0627\u06cc \u06a9\u0631\u06a9', '\u0686\u0627\u06cc \u0645\u0627\u0633\u0627\u0644\u0627', '\u0645\u0648\u06a9\u0627\u0686\u06cc\u0646\u0648', '\u06a9\u0627\u0631\u0627\u0645\u0644 \u0645\u0627\u06a9\u06cc\u0627\u062a\u0648', '\u0634\u0627\u062e\u0633\u0627\u0631', '\u0633\u0631\u062f\u0646\u0648\u0634 \u0686\u0627\u06cc \u062a\u0631\u0634 \u0648 \u062a\u0648\u062a \u0641\u0631\u0646\u06af\u06cc', '\u06a9\u0627\u0633\u0647 \u0628\u0631\u0646\u062c\u06cc\u0646 \u0645\u0631\u063a', '\u06a9\u0627\u0633\u0647 \u0628\u0631\u0646\u062c\u06cc\u0646 \u062a\u0646 \u0645\u0627\u0647\u06cc']
    result = []
    for item_name in items:
        bom = frappe.db.get_value('BOM', {'item': item_name, 'is_active': 1}, ['name', 'quantity'], as_dict=True)
        if not bom:
            result.append(item_name + ': No BOM')
            continue
        bom_items = frappe.db.sql("SELECT bi.item_code, bi.qty, bi.uom, COALESCE(CAST(i.restaurant_nutrition_kcal AS DECIMAL(10,1)), 0) as kcal FROM `tabBOM Item` bi JOIN `tabItem` i ON i.name = bi.item_code WHERE bi.parent = %s ORDER BY i.restaurant_nutrition_kcal * bi.qty DESC", (bom.name,), as_dict=True)
        result.append('=== ' + item_name + ' ===')
        total = 0
        for it in bom_items:
            t = float(it.qty or 1) * float(it.kcal or 0)
            total += t
            if t > 50:
                result.append('  ' + it.item_code + ' | ' + str(it.qty) + ' ' + it.uom + ' x ' + str(it.kcal) + ' = ' + str(round(t,1)))
        result.append('  TOTAL: ' + str(round(total,1)) + ' / ' + str(bom.quantity) + ' = ' + str(round(total/float(bom.quantity or 1),1)))
        result.append('')
    return '\n'.join(result)
