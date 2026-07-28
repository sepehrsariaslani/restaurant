# Copyright (c) 2026, Sepehr Sariaslani and Contributors

import frappe
from frappe.tests.utils import FrappeTestCase


class TestRestaurantCourierVehicle(FrappeTestCase):
	def tearDown(self):
		for doctype, code_field, prefix in (
			("Restaurant Courier Vehicle", "plate_number", "99تست"),
			("Restaurant Courier", "courier_code", "TEST-%"),
		):
			for name in frappe.get_all(
				doctype,
				filters={code_field: ["like", prefix]},
				pluck="name",
				ignore_permissions=True,
			):
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)

	def test_validate_sets_title_from_type_and_plate(self):
		courier = frappe.get_doc(
			{
				"doctype": "Restaurant Courier",
				"courier_name": "پیک ناوگان",
				"courier_code": "TEST-FLEET-001",
				"mobile": "09120000001",
				"vehicle_type": "موتور",
				"plate_number": "11الف11111",
				"zone": "شمال",
				"assignment_priority": 10,
			}
		).insert(ignore_permissions=True)

		vehicle = frappe.get_doc(
			{
				"doctype": "Restaurant Courier Vehicle",
				"courier": courier.name,
				"vehicle_type": "پراید",
				"plate_number": "99تست12345",
				"is_primary": 1,
			}
		)

		vehicle.insert(ignore_permissions=True)

		self.assertEqual(vehicle.title, "پراید - 99تست12345")
