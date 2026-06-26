import frappe
from frappe.model.document import Document


class RestaurantCoupon(Document):
	def validate(self):
		if self.discount_type == "Percent" and (self.discount_value or 0) > 100:
			frappe.throw("Percent discount cannot be greater than 100.")
