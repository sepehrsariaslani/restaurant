import frappe
from frappe.model.document import Document


class RestaurantCustomerReview(Document):
	def validate(self):
		if self.score_10 not in (None, ""):
			score = int(self.score_10 or 0)
			if score < 1 or score > 10:
				frappe.throw("Rating must be between 1 and 10.")
			self.rating = score / 2
		else:
			rating = int(self.rating or 0)
			if rating < 1 or rating > 5:
				frappe.throw("Rating must be between 1 and 5.")
