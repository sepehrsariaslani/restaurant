from types import SimpleNamespace
import unittest
from unittest.mock import patch

from restaurant.employee_meals import (
    EmployeeMealValidationError,
    employee_meal_avoids_stock_reservation,
    employee_meal_checkout_route,
    can_release_reservation,
    employee_meal_include_service_items,
    has_employee_meal_customization,
    is_employee_meal_order_delivered,
    release_employee_meal_order,
    validate_employee_meal_order,
)


class EmployeeMealOrderRulesTests(unittest.TestCase):
    def test_checkout_route_uses_reliable_path_for_any_employee_meal_marker(self):
        self.assertEqual(employee_meal_checkout_route({"employee": "EMP-1"}), "reliable")
        self.assertEqual(employee_meal_checkout_route({"reservation": "MRV-1"}), "reliable")
        self.assertEqual(employee_meal_checkout_route({"items": [{"item_code": "TEA"}]}), "offline")

    def test_employee_meal_payload_never_reserves_stock(self):
        self.assertTrue(employee_meal_avoids_stock_reservation({"employee": "EMP-1", "reservation": "MRV-1"}))
        self.assertFalse(employee_meal_avoids_stock_reservation({"items": [{"item_slug": "burger"}]}))

    def test_employee_meal_orders_skip_service_items_but_regular_orders_keep_them(self):
        meal = {"employee": "EMP-1", "reservation": "MRV-1"}
        regular = {"items": [{"item_slug": "burger"}]}
        self.assertEqual(employee_meal_include_service_items(meal), 0)
        self.assertEqual(employee_meal_include_service_items(regular), 1)

    def test_empty_default_customization_is_not_a_customization(self):
        self.assertFalse(has_employee_meal_customization({
            "ingredient_adjustments": [],
            "selected_modifiers": [],
            "selected_alternatives": [],
            "removed_ingredients": [],
            "added_ingredients": [],
            "variant_fixed_attributes": {},
        }))
        self.assertTrue(has_employee_meal_customization({"selected_modifiers": [{"group": "Size", "option": "Large"}]}))

    def setUp(self):
        self.employee = {"name": "EMP-1", "status": "Active", "company": "COMP-1"}
        self.reservation = {
            "name": "MRV-1",
            "employee": "EMP-1",
            "company": "COMP-1",
            "reservation_date": "2026-11-16",
            "meal_type": "Lunch",
            "meal_item": "MEAL-1",
            "reservation_status": "Reserved",
            "pos_sales_order": "",
        }
        self.items = [{"item_code": "MEAL-1", "qty": 1}]

    def validate(self, **overrides):
        values = {
            "employee": self.employee,
            "reservation": self.reservation,
            "company": "COMP-1",
            "today": "2026-11-16",
            "items": self.items,
            "requested_employee": "EMP-1",
            "client_order_key": "order-key-1",
        }
        values.update(overrides)
        return validate_employee_meal_order(**values)

    def test_accepts_the_active_employees_reserved_lunch_for_exact_item_and_quantity(self):
        result = self.validate()
        self.assertEqual(result["employee"], "EMP-1")
        self.assertEqual(result["reservation"], "MRV-1")
        self.assertEqual(result["item_code"], "MEAL-1")

    def test_rejects_inactive_employee_or_employee_from_another_company(self):
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(employee={**self.employee, "status": "Left"})
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(employee={**self.employee, "company": "COMP-2"})

    def test_rejects_reservation_outside_today_or_not_reserved(self):
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(reservation={**self.reservation, "reservation_date": "2026-11-15"})
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(reservation={**self.reservation, "reservation_status": "Not Required"})

    def test_requires_exactly_the_reserved_item_once(self):
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(items=[{"item_code": "OTHER", "qty": 1}])
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(items=[{"item_code": "MEAL-1", "qty": 2}])
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(items=self.items + [{"item_code": "OTHER", "qty": 1}])

    def test_rejects_new_key_for_reservation_linked_to_order_but_allows_same_key_replay(self):
        occupied = {**self.reservation, "restaurant_pos_sales_order": "SO-1"}
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(reservation=occupied)
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(
                reservation=occupied,
                client_order_key="new-order-key",
                linked_order_client_key="order-key-1",
                linked_order_name="SO-1",
            )
        result = self.validate(
            reservation=occupied,
            linked_order_client_key="order-key-1",
            linked_order_name="SO-1",
        )
        self.assertTrue(result["idempotent_replay"])
        self.assertEqual(result["order_id"], "SO-1")

    def test_rejects_employee_meal_price_overrides_and_order_level_discounts(self):
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(price_overrides=True)
        with self.assertRaises(EmployeeMealValidationError):
            self.validate(financial_modifiers={"discount_amount": 100})

    def test_cancellation_releases_only_matching_undelivered_order(self):
        self.assertTrue(can_release_reservation("SO-1", "SO-1", delivered=False))
        self.assertFalse(can_release_reservation("SO-2", "SO-1", delivered=False))
        self.assertFalse(can_release_reservation("SO-1", "SO-1", delivered=True))

    def test_served_and_fully_delivered_orders_are_not_released_as_undelivered(self):
        self.assertTrue(is_employee_meal_order_delivered("delivered", 0))
        self.assertTrue(is_employee_meal_order_delivered("served", 0))
        self.assertTrue(is_employee_meal_order_delivered("ready", 100))
        self.assertFalse(is_employee_meal_order_delivered("ready", 99))

    def test_cancellation_does_not_release_hrms_delivered_reservation(self):
        class ReservationDB:
            def __init__(self):
                self.cleared = []

            def has_column(self, doctype, fieldname):
                return True

            def sql(self, *args, **kwargs):
                return None

            def get_value(self, doctype, name, fieldname, **kwargs):
                values = {
                    "restaurant_pos_sales_order": "SO-1",
                    "reservation_status": "Delivered",
                }
                return values[fieldname]

            def set_value(self, *args, **kwargs):
                self.cleared.append((args, kwargs))

        db = ReservationDB()
        frappe = SimpleNamespace(db=db)
        class SalesOrder(dict):
            @property
            def name(self):
                return self["name"]

        order = SalesOrder({
            "name": "SO-1",
            "restaurant_employee_meal_reservation": "MRV-1",
            "restaurant_status": "Ready",
            "per_delivered": 0,
        })

        with patch("restaurant.employee_meals._frappe_module", return_value=frappe):
            released = release_employee_meal_order(order)

        self.assertFalse(released)
        self.assertEqual(db.cleared, [])

    def test_cancellation_clears_unique_reservation_order_link_to_null(self):
        class ReservationDB:
            def __init__(self):
                self.cleared = []

            def has_column(self, doctype, fieldname):
                return True

            def sql(self, *args, **kwargs):
                return None

            def get_value(self, doctype, name, fieldname, **kwargs):
                values = {
                    "restaurant_pos_sales_order": "SO-1",
                    "reservation_status": "Reserved",
                }
                return values[fieldname]

            def set_value(self, *args, **kwargs):
                self.cleared.append((args, kwargs))

        db = ReservationDB()
        frappe = SimpleNamespace(db=db)

        class SalesOrder(dict):
            @property
            def name(self):
                return self["name"]

        order = SalesOrder({
            "name": "SO-1",
            "restaurant_employee_meal_reservation": "MRV-1",
            "restaurant_status": "Ready",
            "per_delivered": 0,
        })

        with patch("restaurant.employee_meals._frappe_module", return_value=frappe):
            released = release_employee_meal_order(order)

        self.assertTrue(released)
        self.assertEqual(
            db.cleared,
            [(("Meal Reservation", "MRV-1", "restaurant_pos_sales_order", None), {"update_modified": False})],
        )


if __name__ == "__main__":
    unittest.main()
