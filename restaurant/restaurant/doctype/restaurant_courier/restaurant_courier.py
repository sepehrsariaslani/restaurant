import re

import frappe
from frappe.model.document import Document


def _normalize_mobile(value):
	mobile = re.sub(r"\D+", "", str(value or ""))
	if mobile.startswith("98") and len(mobile) == 12:
		mobile = "0" + mobile[2:]
	if len(mobile) == 10 and mobile.startswith("9"):
		mobile = "0" + mobile
	return mobile


class RestaurantCourier(Document):
	def validate(self):
		self.courier_name = (self.courier_name or "").strip()
		self.courier_code = (self.courier_code or "").strip()
		self.mobile = _normalize_mobile(self.mobile)
		self.vehicle_type = (self.vehicle_type or "").strip()
		self.plate_number = (self.plate_number or "").strip()
		self.zone = (self.zone or "").strip()
		self.notes = (self.notes or "").strip()
		self.assignment_priority = cint(self.assignment_priority or 0)

		if not self.courier_name:
			frappe.throw("Courier name is required.")
		if not self.courier_code:
			frappe.throw("Courier code is required.")
		if len(self.mobile) < 10:
			frappe.throw("A valid mobile number is required.")
		if not self.vehicle_type:
			frappe.throw("Vehicle type is required.")
		if not self.plate_number:
			frappe.throw("Vehicle plate number is required.")


def cint(value):
	try:
		return int(value)
	except Exception:
		return 0

