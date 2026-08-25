import random
import string

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import now_datetime


class RestaurantOrder(Document):
    def autoname(self):
        if not self.name:
            self.name = make_autoname("RO-.#####")

    def before_insert(self):
        if not self.order_code:
            self.order_code = self._generate_order_code()
        if not self.placed_at:
            self.placed_at = now_datetime()

    def validate(self):
        if self.order_type == "delivery" and not (self.address or "").strip():
            frappe.throw(_("Address is required for delivery orders."))

    def _generate_order_code(self):
        while True:
            code = "R" + "".join(random.choices(string.digits, k=7))
            if not frappe.db.exists("Restaurant Order", {"order_code": code}):
                return code
