import frappe
from frappe.utils import flt


def execute():
    if not frappe.db.exists("DocType", "Restaurant Modifier Group"):
        return

    changed = 0
    for group_name in frappe.get_all("Restaurant Modifier Group", pluck="name", ignore_permissions=True):
        doc = frappe.get_doc("Restaurant Modifier Group", group_name)
        doc_changed = False

        for row in doc.get("options") or []:
            action_type = (row.get("action_type") or "add_on").strip() or "add_on"
            row.action_type = action_type

            if action_type == "add_on" and row.get("option_item"):
                item_meta = frappe.db.get_value(
                    "Item",
                    row.option_item,
                    ["stock_uom", "valuation_rate", "standard_rate"],
                    as_dict=True,
                ) or {}
                row.option_uom = (item_meta.get("stock_uom") or "").strip()
                row.option_cost_rate = flt(item_meta.get("valuation_rate") or item_meta.get("standard_rate") or 0)
                row.option_qty = flt(row.get("option_qty") or 1)
                if row.option_qty <= 0:
                    row.option_qty = 1
                row.option_cost_amount = flt(row.option_qty) * flt(row.option_cost_rate)
                row.min_qty = max(flt(row.get("min_qty") if row.get("min_qty") not in (None, "") else 1), 0)
                row.max_qty = max(flt(row.get("max_qty") if row.get("max_qty") not in (None, "") else 9), row.min_qty)
                row.qty_step = flt(row.get("qty_step") or 1)
                if row.qty_step <= 0:
                    row.qty_step = 1
                doc_changed = True
                continue

            if action_type == "bom_variant":
                row.option_item = ""
                row.option_uom = ""
                row.option_qty = 1
                row.option_cost_rate = 0
                row.option_cost_amount = 0
                row.min_qty = 1
                row.max_qty = 1
                row.qty_step = 1
                doc_changed = True

        if doc_changed:
            doc.save(ignore_permissions=True)
            changed += 1

    if changed:
        frappe.clear_cache()
        frappe.db.commit()
