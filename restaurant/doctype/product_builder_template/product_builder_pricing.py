import frappe
from frappe import _


def compute_builder_price(base_price, selections, pricing_mode="additive"):
    """
    Compute final price from base price and builder selections.

    Args:
        base_price: float — the item's base price
        selections: list of dicts — each with price_delta, price_type, qty
        pricing_mode: str — "additive" (default) or "override"

    Returns:
        dict with base_price, options_total, final_price
    """
    options_total = 0

    for sel in selections:
        delta = sel.get("price_delta", 0) or 0
        price_type = sel.get("price_type", "fixed")
        qty = sel.get("qty", 1) or 1
        percentage = sel.get("price_percentage", 0) or 0

        if price_type == "fixed":
            line_delta = delta * qty
        elif price_type == "percentage":
            line_delta = (base_price * percentage / 100) * qty
        elif price_type == "multiply":
            line_delta = base_price * delta * qty
        else:
            line_delta = delta * qty

        options_total += line_delta

    return {
        "base_price": base_price,
        "options_total": options_total,
        "final_price": base_price + options_total,
    }
