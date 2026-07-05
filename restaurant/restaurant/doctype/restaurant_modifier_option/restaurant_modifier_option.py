import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class RestaurantModifierOption(Document):
    def validate(self):
        action_type = (self.action_type or "add_on").strip()
        self.action_type = action_type
        if action_type not in {"add_on", "bom_variant"}:
            frappe.throw(_("Action Type must be add_on or bom_variant."))

        self.option_qty = flt(self.option_qty or 1)
        if self.option_qty <= 0:
            self.option_qty = 1

        self.qty_step = flt(self.qty_step or self.option_qty or 1)
        if self.qty_step <= 0:
            self.qty_step = self.option_qty or 1

        self.min_qty = max(flt(self.min_qty if self.min_qty not in (None, "") else 0), 0)
        default_max_qty = max(self.option_qty, self.qty_step, self.option_qty * 4)
        self.max_qty = max(
            flt(self.max_qty if self.max_qty not in (None, "") else default_max_qty),
            self.min_qty,
            self.option_qty,
        )

        if action_type == "add_on":
            if not self.option_item:
                frappe.throw(_("Option Item is required for add_on action type."))

            item_meta = frappe.db.get_value(
                "Item",
                self.option_item,
                ["stock_uom", "valuation_rate", "standard_rate"],
                as_dict=True,
            ) or {}
            current_option_uom = (self.option_uom or "").strip()
            self.option_uom = current_option_uom or (item_meta.get("stock_uom") or "").strip()
            self.option_cost_rate = flt(item_meta.get("valuation_rate") or item_meta.get("standard_rate") or 0)
            self.option_cost_amount = flt(self.option_qty) * flt(self.option_cost_rate)
            self.alternative_bom = ""

        if action_type == "bom_variant":
            if not self.alternative_bom:
                frappe.throw(_("Alternative BOM is required for bom_variant action type."))
            self.option_item = ""
            self.option_uom = ""
            self.option_cost_rate = 0
            self.option_cost_amount = 0
            self.option_qty = 1
            self.min_qty = 1
            self.max_qty = 1
            self.qty_step = 1

        if self.min_qty > self.max_qty:
            frappe.throw(_("Min Qty cannot be greater than Max Qty."))
