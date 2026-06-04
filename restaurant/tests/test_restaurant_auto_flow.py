from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from restaurant.api import _production_auto_settings, _run_sales_order_auto_flow


class TestRestaurantAutoFlow(FrappeTestCase):
    def test_production_auto_settings_are_normalized(self):
        values = {
            "restaurant_auto_flow_enabled": 1,
            "restaurant_auto_flow_on_order_submit": 0,
            "restaurant_auto_flow_on_payment": 1,
            "restaurant_auto_flow_submit_work_order": 1,
            "restaurant_auto_flow_material_transfer": 0,
            "restaurant_auto_flow_manufacture": 1,
            "restaurant_auto_flow_mark_ready": 1,
            "restaurant_auto_flow_mark_delivered_on_paid": 0,
            "restaurant_auto_flow_create_delivery_note": 1,
            "restaurant_auto_flow_submit_stock_entries": 0,
            "restaurant_auto_flow_submit_delivery_note": 1,
        }

        with patch("restaurant.api._ensure_production_auto_setting_fields"), patch(
            "restaurant.api._get_single_setting",
            side_effect=lambda doctype, fieldname, default=None: values.get(fieldname, default),
        ):
            payload = _production_auto_settings()

        self.assertTrue(payload["enabled"])
        self.assertFalse(payload["on_order_submit"])
        self.assertTrue(payload["on_payment"])
        self.assertFalse(payload["material_transfer"])
        self.assertFalse(payload["submit_stock_entries"])
        self.assertTrue(payload["create_delivery_note_on_paid"])
        self.assertFalse(payload["mark_delivered_on_paid"])

    def test_auto_flow_returns_skip_when_order_missing(self):
        with patch("restaurant.api._resolve_sales_order_name", return_value=""):
            payload = _run_sales_order_auto_flow("SO-UNKNOWN", trigger="manual")
        self.assertEqual(payload.get("status"), "skipped")
        self.assertEqual(payload.get("reason"), "order_not_found")
