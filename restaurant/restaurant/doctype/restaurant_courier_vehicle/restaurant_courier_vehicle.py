import frappe
from frappe.model.document import Document


class RestaurantCourierVehicle(Document):
	def validate(self):
		self.title = (self.title or "").strip()
		self.courier = (self.courier or "").strip()
		self.vehicle_type = (self.vehicle_type or "").strip()
		self.plate_number = (self.plate_number or "").strip()
		self.notes = (self.notes or "").strip()
		fleet_vehicle = (self.get("fleet_vehicle") or "").strip()

		if fleet_vehicle:
			vehicle = frappe.db.get_value(
				"Vehicle", fleet_vehicle, ["license_plate", "make", "model"], as_dict=True
			)
			if not vehicle:
				frappe.throw("Select an existing ERPNext Fleet Vehicle.")
			if not (vehicle.get("license_plate") or "").strip():
				frappe.throw("The selected Fleet Vehicle needs a license plate.")
			self.plate_number = vehicle.license_plate.strip()
			self.vehicle_type = self.vehicle_type or " ".join(
				part for part in (vehicle.get("make"), vehicle.get("model")) if part
			) or "Fleet Vehicle"

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
