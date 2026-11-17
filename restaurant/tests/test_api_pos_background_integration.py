from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant import api_pos_background as background


class PaidEmployeeMealCheckoutIntegrationTests(FrappeTestCase):
    def test_checkout_creates_reserved_meal_reliably_then_queues_payment(self):
        calls = []
        payload = {
            "client_order_key": "employee-meal-checkout-1",
            "employee": "EMP-1",
            "reservation": "MRV-1",
            "payment": {"mode": "Cash", "amount": 120000},
        }

        class Legacy:
            def _ensure_management_access(self):
                calls.append(("access",))

        class Reliability:
            def create_management_pos_order_reliable(self, data):
                calls.append(("reliable", data))
                return {"status": "created", "order_id": "SO-MEAL-1"}

            def replay_offline_pos_order(self, data):
                calls.append(("offline", data))
                raise AssertionError("employee meals must not use offline price replay")

        def queue(order_id, payment=None, deliver_after=False):
            calls.append(("queue", order_id, payment, deliver_after))
            return {
                "job_key": "job-meal-1",
                "status": "queued",
                "order_id": order_id,
                "action": "settle-deliver" if deliver_after else "settle",
            }

        with patch.object(background, "_legacy_api", return_value=Legacy()), \
             patch.object(background, "_reliability_api", return_value=Reliability()), \
             patch.object(background, "_queue_existing_order", side_effect=queue):
            result = background.enqueue_pos_checkout(payload, deliver_after=1)

        self.assertEqual(calls, [
            ("access",),
            ("reliable", payload),
            ("queue", "SO-MEAL-1", payload["payment"], True),
        ])
        self.assertEqual(result["order_id"], "SO-MEAL-1")
        self.assertEqual(result["action"], "settle-deliver")
