import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class RestaurantTableOrder(Document):
    def before_insert(self):
        if not self.order_code:
            self.order_code = _generate_order_code()
        if not self.created_at:
            self.created_at = now_datetime()

    def validate(self):
        self._validate_session_table()
        self._calculate_totals()
        self._sync_status_timestamps()

    def _validate_session_table(self):
        if not self.session or not self.table:
            return

        session_table = frappe.db.get_value("Restaurant Table Session", self.session, "table")
        if session_table and session_table != self.table:
            frappe.throw("Table Session is not linked to the selected table.")

        session_status = frappe.db.get_value("Restaurant Table Session", self.session, "status")
        if session_status == "closed" and self.status in {"pending", "confirmed", "served"}:
            frappe.throw("Cannot place active orders for a closed table session.")

    def _calculate_totals(self):
        subtotal = 0.0

        for row in self.items or []:
            row.quantity = max(flt(row.quantity or 1), 1)
            row.price_at_time = max(flt(row.price_at_time or 0), 0)
            row.line_total = flt(row.quantity) * flt(row.price_at_time)
            subtotal += flt(row.line_total)

        self.subtotal = subtotal
        self.grand_total = subtotal

    def _sync_status_timestamps(self):
        now = now_datetime()

        if self.status == "confirmed" and not self.confirmed_at:
            self.confirmed_at = now
        if self.status == "served" and not self.served_at:
            self.served_at = now
        if self.status == "paid" and not self.paid_at:
            self.paid_at = now



def _generate_order_code():
    for _ in range(20):
        code = "T" + frappe.generate_hash(length=7).upper()
        if not frappe.db.exists("Restaurant Table Order", {"order_code": code}):
            return code

    frappe.throw("Unable to generate a unique order code.")
