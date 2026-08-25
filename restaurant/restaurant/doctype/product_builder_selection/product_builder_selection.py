import frappe
import json
from frappe import _
from frappe.model.document import Document


class ProductBuilderSelection(Document):
    def validate(self):
        self._compute_pricing()
        self._build_summary()
        self._denormalize()

    def _compute_pricing(self):
        self.options_total = sum(
            (s.get("total_price") if hasattr(s, "get") else None)
            or ((s.price_delta or 0) * (s.qty or 1))
            for s in self.selections
        )
        self.final_price = (self.base_price or 0) + self.options_total

    def _build_summary(self):
        lines = []
        for sel in self.selections:
            portion_count = sel.get("portion_count") if hasattr(sel, "get") else getattr(sel, "portion_count", 0)
            portion_qty = sel.get("portion_qty") if hasattr(sel, "get") else getattr(sel, "portion_qty", 0)
            portion_uom = sel.get("portion_uom") if hasattr(sel, "get") else getattr(sel, "portion_uom", "")
            qty_value = portion_count or sel.qty or 0
            qty_str = " x{0}".format(qty_value) if qty_value and qty_value > 1 else ""
            if portion_qty:
                portion_label = "{0:g} {1}".format(portion_qty, portion_uom or "").strip()
                if portion_label:
                    qty_str = "{0} ({1})".format(qty_str or "", portion_label).strip()
            price_str = ""
            total_price = (
                sel.get("total_price") if hasattr(sel, "get") else getattr(sel, "total_price", None)
            )
            if (total_price or sel.price_delta) and (total_price or sel.price_delta) > 0:
                price_str = " (+{0:,.0f})".format(total_price or sel.price_delta)
            lines.append(
                "{0}: {1}{2}{3}".format(
                    sel.step_title, sel.option_label, qty_str, price_str
                )
            )
        self.summary_text = "\n".join(lines)

    def _denormalize(self):
        self.template_title = frappe.db.get_value(
            "Product Builder Template", self.template, "title"
        )
        self.item_name = frappe.db.get_value("Item", self.item, "item_name")


def on_sales_order_submit(doc, method):
    """Hook: When a Sales Order with builder items is submitted, validate selections."""
    for item in doc.items:
        if item.get("builder_selection"):
            selection = frappe.get_doc("Product Builder Selection", item.builder_selection)
            if selection.docstatus != 0:
                frappe.throw(
                    _(
                        "Builder Selection {0} for item {1} is not in draft state."
                    ).format(selection.name, item.item_code)
                )


def purge_orphaned_selections():
    """Daily scheduled job: purge builder selections not linked to any Sales Order Item older than 30 days."""
    from frappe.utils import add_days, nowdate

    cutoff = add_days(nowdate(), -30)
    orphaned = frappe.get_all(
        "Product Builder Selection",
        filters={
            "creation": ["<", cutoff],
            "name": [
                "not in",
                frappe.db.sql_list(
                    """SELECT DISTINCT builder_selection
                    FROM `tabSales Order Item`
                    WHERE builder_selection IS NOT NULL
                    AND builder_selection != ''"""
                ),
            ],
        },
        pluck="name",
    )
    for name in orphaned:
        frappe.delete_doc("Product Builder Selection", name, ignore_permissions=True)

    if orphaned:
        frappe.logger().info(
            "Purged {0} orphaned Product Builder Selections older than 30 days.".format(
                len(orphaned)
            )
        )
