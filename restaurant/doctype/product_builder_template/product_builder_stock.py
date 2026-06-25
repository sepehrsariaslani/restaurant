import frappe
import json
from frappe import _


def compute_stock_consumption(selections, base_item):
    """
    Compute stock consumption from builder selections.

    Returns list of dicts with item_code, qty, uom.
    """
    consumption = {}

    for sel in selections:
        qty = sel.get("qty", 1) or 1
        stock_impact = sel.get("stock_impact", {})
        if isinstance(stock_impact, str):
            stock_impact = json.loads(stock_impact)

        for consume in stock_impact.get("consumes", []):
            item_code = consume["item_code"]
            per_qty = consume["qty_per_selection"]
            uom = consume.get("uom", "Unit")
            total_qty = per_qty * qty

            if item_code in consumption:
                consumption[item_code]["qty"] += total_qty
            else:
                consumption[item_code] = {
                    "item_code": item_code,
                    "qty": total_qty,
                    "uom": uom,
                }

    return list(consumption.values())
