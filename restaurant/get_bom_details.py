from frappe.utils.bench_helper import invoke

# This is a direct script that will be eval'd by bench execute
import frappe
import json

bom_names = [
    "BOM-D.F-000546-004",
    "BOM-D.F-000532-009",
    "BOM-D.F-000523-005",
    "BOM-D.F-000507-021",
    "BOM-D.F-000103-011",
    "BOM-D.J0010152-019",
    "BOM-D.F-010001-002",
    "BOM-D.F-000528-002",
    "BOM-D.F-000587-003",
    "BOM-D.F-000574-001",
]

results = {}
for bom_name in bom_names:
    bom = frappe.get_doc("BOM", bom_name)
    items = []
    for item in bom.items:
        items.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": item.qty,
            "uom": item.uom,
            "rate": item.rate,
        })
    results[bom_name] = {
        "item": bom.item,
        "item_name": bom.item_name,
        "quantity": bom.quantity,
        "uom": bom.uom,
        "items": items,
    }

print(json.dumps(results, ensure_ascii=False, indent=2))
