import frappe

def run():
    item_name = "\u0628\u0631\u0646\u062c \u067e\u062e\u062a\u0647 \u0634\u062f\u0647"
    
    if not frappe.db.exists("Item", item_name):
        item = frappe.new_doc("Item")
        item.item_code = item_name
        item.item_name = item_name
        item.item_group = "\u0645\u0648\u0627\u062f \u0627\u0648\u0644\u06cc\u0647"
        item.stock_uom = "\u06af\u0631\u0645"
        item.is_stock_item = 1
        item.restaurant_nutrition_kcal = 1.30
        item.restaurant_nutrition_protein_g = 0.027
        item.restaurant_nutrition_fat_g = 0.003
        item.restaurant_nutrition_carb_g = 0.28
        item.insert()
        frappe.db.commit()
        print("Created: " + item_name)
    else:
        frappe.db.set_value("Item", item_name, {
            "restaurant_nutrition_kcal": 1.30,
            "restaurant_nutrition_protein_g": 0.027,
            "restaurant_nutrition_fat_g": 0.003,
            "restaurant_nutrition_carb_g": 0.28,
        })
        frappe.db.commit()
        print("Updated: " + item_name)
    
    bom_name = "BOM-\u0628\u0631\u0646\u062c \u067e\u062e\u062a\u0647 \u0634\u062f\u0647-001"
    if frappe.db.exists("BOM", bom_name):
        frappe.delete_doc("BOM", bom_name)
        frappe.db.commit()
    
    bom = frappe.new_doc("BOM")
    bom.item = item_name
    bom.quantity = 250
    bom.uom = "\u06af\u0631\u0645"
    bom.is_active = 1
    bom.is_default = 1
    bom.with_operations = 0
    bom.append("items", {
        "item_code": "\u0628\u0631\u0646\u062c \u0633\u0641\u06cc\u062f",
        "qty": 100,
        "uom": "\u06af\u0631\u0645",
    })
    bom.insert()
    frappe.db.commit()
    print("Created BOM: " + bom_name)
    
    raw_rice_boms = frappe.db.sql("SELECT DISTINCT b.name, b.item, bi.qty as raw_qty FROM  b JOIN  bi ON bi.parent = b.name WHERE bi.item_code = u0628u0631u0646u062c
