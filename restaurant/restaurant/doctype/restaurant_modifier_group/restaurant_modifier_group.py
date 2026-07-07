import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantModifierGroup(Document):
    def validate(self):
        if self.selection_mode == "single":
            self.min_select = 1 if self.required else 0
            self.max_select = 1

        self.min_select = max(int(self.min_select or 0), 0)
        self.max_select = max(int(self.max_select or 1), 1)

        if self.min_select > self.max_select:
            frappe.throw(_("Min Select cannot be greater than Max Select."))
