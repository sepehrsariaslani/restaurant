# Copyright (c) 2026, Sepehr Sariaslani and Contributors

import frappe
from frappe.tests.utils import FrappeTestCase


class TestRestaurantCourier(FrappeTestCase):
	def tearDown(self):
		for name in frappe.get_all(
			"Restaurant Courier",
			filters={"courier_code": ["like", "TEST-%"]},
			pluck="name",
			ignore_permissions=True,
		):
			frappe.delete_doc("Restaurant Courier", name, force=1, ignore_permissions=True)

	def test_validate_normalizes_mobile(self):
		doc = frappe.get_doc(
			{
				"doctype": "Restaurant Courier",
				"courier_name": "پیک تست",
				"courier_code": "TEST-COURIER-001",
				"mobile": "+98 912 123 4567",
				"vehicle_type": "موتور",
				"plate_number": "12الف34567",
				"zone": "مرکز",
				"assignment_priority": 5,
			}
		)

		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.mobile, "09121234567")

