import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

frappe = types.ModuleType("frappe")
frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
frappe._ = lambda value: value
frappe.db = types.SimpleNamespace()
sys.modules["frappe"] = frappe

from restaurant import api_pos_background as bg


class BackgroundHelpersTests(unittest.TestCase):
    def test_job_key_is_stable_for_same_order_action(self):
        a = bg._background_job_key("SO-0001", "settle-deliver")
        b = bg._background_job_key(" SO-0001 ", "settle-deliver")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("pos-bg-"))

    def test_state_is_small_and_does_not_store_payment(self):
        state = bg._build_job_state(
            "job-1",
            "queued",
            "SO-1",
            "settle",
            result={"sales_invoice": "SINV-1", "payment": {"reference_no": "secret"}},
        )
        self.assertEqual(state["job_key"], "job-1")
        self.assertEqual(state["status"], "queued")
        self.assertEqual(state["sales_invoice"], "SINV-1")
        self.assertNotIn("payment", state)

    def test_normalizes_boolean_delivery_flag(self):
        self.assertFalse(bg._as_bool(0))
        self.assertFalse(bg._as_bool("0"))
        self.assertTrue(bg._as_bool(1))
        self.assertTrue(bg._as_bool("true"))

    def test_safe_boot_falls_back_to_base_items_when_optional_enrichment_fails(self):
        class Legacy:
            def _ensure_management_access(self):
                pass

            def get_management_pos_boot(self, branch):
                return {"items": [{"name": "ITEM-A"}], "categories": [{"name": "Food"}]}

        class Reliability:
            def _clear_expired_out_of_stock(self):
                return 0

            def _management_unavailable_items(self, branch):
                raise RuntimeError("missing optional custom field")

            def _merge_pos_items(self, base, extra):
                return list(base) + list(extra)

        old_legacy, old_rel = bg._legacy_api, bg._reliability_api
        old_log = getattr(frappe, "log_error", None)
        old_trace = getattr(frappe, "get_traceback", None)
        try:
            bg._legacy_api = lambda: Legacy()
            bg._reliability_api = lambda: Reliability()
            frappe.log_error = lambda *args, **kwargs: None
            frappe.get_traceback = lambda: "trace"
            payload = bg.get_management_pos_boot_safe("main")
        finally:
            bg._legacy_api, bg._reliability_api = old_legacy, old_rel
            if old_log is None:
                delattr(frappe, "log_error")
            else:
                frappe.log_error = old_log
            if old_trace is None:
                delattr(frappe, "get_traceback")
            else:
                frappe.get_traceback = old_trace

        self.assertEqual(payload["items"], [{"name": "ITEM-A"}])
        self.assertEqual(payload["categories"], [{"name": "Food"}])


class BackgroundWorkerOutcomeTests(unittest.TestCase):
    def test_settle_and_deliver_is_failed_when_delivery_helper_swallows_failure(self):
        states = []

        class Legacy:
            def settle_pos_order(self, order_name, payment=None, commit=True):
                return {"sales_invoice": "SINV-1"}

            def _background_deliver_pos_order(self, order_name):
                return None

            def _has_column(self, doctype, fieldname):
                return doctype == "Sales Order" and fieldname == "restaurant_status"

        old_legacy = bg._legacy_api
        old_set_state = bg._set_job_state
        old_get_value = getattr(frappe.db, "get_value", None)
        old_rollback = getattr(frappe.db, "rollback", None)
        try:
            bg._legacy_api = lambda: Legacy()
            bg._set_job_state = lambda state: states.append(dict(state)) or state
            frappe.db.get_value = lambda *args, **kwargs: "preparing"
            frappe.db.rollback = lambda: None
            state = bg.run_pos_background_settlement("job-1", "SO-1", {}, 1)
        finally:
            bg._legacy_api = old_legacy
            bg._set_job_state = old_set_state
            if old_get_value is None:
                delattr(frappe.db, "get_value")
            else:
                frappe.db.get_value = old_get_value
            if old_rollback is None:
                delattr(frappe.db, "rollback")
            else:
                frappe.db.rollback = old_rollback

        self.assertEqual(state["status"], "failed")
        self.assertEqual(states[-1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
