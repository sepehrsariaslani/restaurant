from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant.employee_meals import (
    link_employee_meal_order,
    lock_and_validate_employee_meal_order,
    release_employee_meal_order,
)


class TestEmployeeMealPOSIntegration(FrappeTestCase):
    def test_reserved_employee_meal_is_validated_against_site_date_and_company(self):
        company = "COMP-1"
        reservation = frappe._dict({
            "name": "MRV-1",
            "meal_plan": "MWP-1",
            "company": company,
            "employee": "EMP-1",
            "reservation_date": frappe.utils.nowdate(),
            "meal_type": "Lunch",
            "meal_item": "MEAL-1",
            "reservation_status": "Reserved",
            "restaurant_pos_sales_order": "",
        })
        employee = frappe._dict({"name": "EMP-1", "company": company, "status": "Active"})
        plan = frappe._dict({"company": company, "status": "Published"})

        class Legacy:
            def _management_pos_profile_summary(self):
                return {"name": "POS-1", "company": company}

            def _extract_customization(self, raw):
                return {
                    "ingredient_adjustments": [],
                    "selected_modifiers": [],
                    "selected_alternatives": [],
                    "removed_ingredients": [],
                    "added_ingredients": [],
                    "variant_fixed_attributes": {},
                }

            def _get_item_doc_by_payload(self, row):
                return frappe._dict({"name": "MEAL-1", "item_code": "MEAL-1"})

        def get_value(doctype, name, fields=None, as_dict=False):
            if doctype == "POS Profile":
                return 0
            if doctype == "Meal Reservation":
                return reservation
            if doctype == "Employee":
                return employee
            if doctype == "Meal Weekly Plan":
                return plan
            return None

        with patch.object(frappe.db, "exists", return_value=True), \
             patch.object(frappe.db, "has_column", return_value=True), \
             patch.object(frappe.db, "get_value", side_effect=get_value), \
             patch.object(frappe.db, "sql") as sql:
            claim = lock_and_validate_employee_meal_order(
                {
                    "employee": "EMP-1",
                    "reservation": "MRV-1",
                    "order_context": {"company": company},
                    "items": [{"item_slug": "meal", "qty": 1, "customization": {}}],
                },
                client_order_key="client-key-1",
                legacy=Legacy(),
            )
        self.assertEqual(claim["employee"], "EMP-1")
        self.assertEqual(claim["reservation"], "MRV-1")
        self.assertEqual(claim["company"], company)
        sql.assert_called_once()

    def test_link_persists_only_the_exact_reserved_order_line(self):
        with patch.object(frappe, "get_all", return_value=[{"name": "SOI-1", "qty": 1}]), \
             patch.object(frappe.db, "set_value") as set_value:
            link_employee_meal_order(
                {"employee": "EMP-1", "reservation": "MRV-1", "item_code": "MEAL-1"},
                "SO-1",
            )
        self.assertEqual(set_value.call_count, 3)
        self.assertEqual(set_value.call_args_list[0].args[:2], ("Sales Order", "SO-1"))
        self.assertEqual(set_value.call_args_list[1].args[:2], ("Sales Order Item", "SOI-1"))
        self.assertEqual(set_value.call_args_list[2].args[:2], ("Meal Reservation", "MRV-1"))

    def test_cancel_release_requires_same_undelivered_order(self):
        with patch.object(frappe.db, "has_column", return_value=True), \
             patch.object(frappe.db, "sql"), \
             patch.object(frappe.db, "get_value", return_value="SO-OTHER"), \
             patch.object(frappe.db, "set_value") as set_value:
            self.assertFalse(release_employee_meal_order(frappe._dict({
                "name": "SO-1", "restaurant_employee_meal_reservation": "MRV-1",
                "restaurant_status": "ready", "per_delivered": 0,
            })))
            set_value.assert_not_called()

        with patch.object(frappe.db, "has_column", return_value=True), \
             patch.object(frappe.db, "sql"), \
             patch.object(frappe.db, "get_value", return_value="SO-1"), \
             patch.object(frappe.db, "set_value") as set_value:
            self.assertTrue(release_employee_meal_order(frappe._dict({
                "name": "SO-1", "restaurant_employee_meal_reservation": "MRV-1",
                "restaurant_status": "ready", "per_delivered": 0,
            })))
            set_value.assert_called_once_with(
                "Meal Reservation", "MRV-1", "restaurant_pos_sales_order", None, update_modified=False
            )

        with patch.object(frappe.db, "has_column", return_value=True), \
             patch.object(frappe.db, "sql"), \
             patch.object(frappe.db, "get_value", return_value="SO-1"), \
             patch.object(frappe.db, "set_value") as set_value:
            self.assertFalse(release_employee_meal_order(frappe._dict({
                "name": "SO-1", "restaurant_employee_meal_reservation": "MRV-1",
                "restaurant_status": "served", "per_delivered": 0,
            })))
            set_value.assert_not_called()
