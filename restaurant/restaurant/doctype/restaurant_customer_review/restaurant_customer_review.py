import frappe
from frappe.model.document import Document


class RestaurantCustomerReview(Document):
	def validate(self):
		rating = int(self.rating or 0)
		if rating < 1 or rating > 5:
			frappe.throw("Rating must be between 1 and 5.")
