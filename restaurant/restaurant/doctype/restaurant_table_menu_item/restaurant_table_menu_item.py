import frappe
from frappe.model.document import Document
from frappe.utils import flt


class RestaurantTableMenuItem(Document):
    def validate(self):
        self.item_name = (self.item_name or "").strip()
        if not self.item_name:
            frappe.throw("Item Name is required.")

        if flt(self.price) < 0:
            frappe.throw("Price cannot be negative.")
