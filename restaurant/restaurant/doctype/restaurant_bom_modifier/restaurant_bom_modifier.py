import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantBOMModifier(Document):
    def validate(self):
        if self.modifier_group:
            return

        # Legacy fallback for old rows that still use flat fields.
        if not self.group_key:
            frappe.throw(_("Modifier Group is required."))

        self.min_select = max(int(self.min_select or 0), 0)
        self.max_select = max(int(self.max_select or 1), 1)

        if self.required and self.min_select < 1:
            self.min_select = 1

        if self.min_select > self.max_select:
            frappe.throw(_("Min Select cannot be greater than Max Select."))
