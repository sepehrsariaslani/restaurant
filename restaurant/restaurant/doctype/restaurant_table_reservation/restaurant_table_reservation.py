import frappe
from frappe.model.document import Document


class RestaurantTableReservation(Document):
	def validate(self):
		if self.guest_count and int(self.guest_count) < 1:
			frappe.throw("Guest count must be at least 1.")
