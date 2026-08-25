import re

import frappe
from frappe.model.document import Document


class RestaurantCustomerVehicle(Document):
	def validate(self):
		self.mobile = re.sub(r"\D+", "", str(self.mobile or ""))
		if self.mobile.startswith("98") and len(self.mobile) == 12:
			self.mobile = "0" + self.mobile[2:]
		if len(self.mobile) == 10 and self.mobile.startswith("9"):
			self.mobile = "0" + self.mobile
		if len(self.mobile) < 10:
			frappe.throw("A valid mobile number is required.")

		self.title = (self.title or "").strip()
		self.vehicle_type = (self.vehicle_type or "").strip()
		self.color = (self.color or "").strip()
		self.plate_number = (self.plate_number or "").strip()

		if not self.vehicle_type:
			frappe.throw("Vehicle type is required.")
		if not self.color:
			frappe.throw("Vehicle color is required.")
		if not self.plate_number:
			frappe.throw("Vehicle plate number is required.")

		if not self.title:
			self.title = f"{self.vehicle_type} - {self.plate_number}"
