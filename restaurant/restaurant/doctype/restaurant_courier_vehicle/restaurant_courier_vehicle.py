import frappe
from frappe.model.document import Document


class RestaurantCourierVehicle(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		self.courier = (self.courier or "").strip()
		self.vehicle_type = (self.vehicle_type or "").strip()
		self.plate_number = (self.plate_number or "").strip()
		self.notes = (self.notes or "").strip()

		if not self.courier:
			frappe.throw("Courier is required.")
		if not self.vehicle_type:
			frappe.throw("Vehicle type is required.")
		if not self.plate_number:
			frappe.throw("Vehicle plate number is required.")
		if not self.title:
			self.title = f"{self.vehicle_type} - {self.plate_number}"

		if cint(self.is_primary):
			for sibling in frappe.get_all(
				"Restaurant Courier Vehicle",
				filters={"courier": self.courier, "name": ["!=", self.name or ""]},
				pluck="name",
				ignore_permissions=True,
			):
				frappe.db.set_value(
					"Restaurant Courier Vehicle",
					sibling,
					"is_primary",
					0,
					update_modified=False,
				)


def cint(value):
	try:
		return int(value)
	except Exception:
		return 0

