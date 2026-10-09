"""The combined POS action keeps the payment result when delivery cannot start."""

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace


class PosSettleDeliverTests(unittest.TestCase):
    def _action(self, fail_delivery=False):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "settle_and_deliver_pos_order")
        fn.decorator_list = []
        calls = []

        def settle(*args, **kwargs):
            calls.append(("settle", args, kwargs))
            return {"status": "success", "sales_invoice": "SI-1"}

        def deliver(*args, **kwargs):
            calls.append(("deliver", args, kwargs))
            if fail_delivery:
                raise RuntimeError("delivery queue unavailable")
            return {"status": "success", "delivery_note": "در حال صدور..."}

        namespace = {
            "settle_pos_order": settle,
            "deliver_pos_order": deliver,
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        return namespace["settle_and_deliver_pos_order"], calls

    def test_one_action_settles_then_starts_delivery(self):
        action, calls = self._action()
        result = action(order_name="SO-1", payment={"method": "cash"})
        self.assertEqual([call[0] for call in calls], ["settle", "deliver"])
        self.assertEqual(result["sales_invoice"], "SI-1")
        self.assertEqual(result["delivery_note"], "در حال صدور...")

    def test_delivery_failure_does_not_hide_successful_settlement(self):
        action, calls = self._action(fail_delivery=True)
        result = action(order_name="SO-1", payment={"method": "cash"})
        self.assertEqual([call[0] for call in calls], ["settle", "deliver"])
        self.assertEqual(result["sales_invoice"], "SI-1")
        self.assertIn("delivery queue unavailable", result["delivery_error"])

    def test_background_delivery_failure_does_not_mark_order_delivered(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_background_deliver_pos_order")
        statuses = []
        notes = []

        def fail_delivery(*args, **kwargs):
            raise RuntimeError("delivery note failed")

        frappe = SimpleNamespace(
            db=SimpleNamespace(commit=lambda: None, exists=lambda *args: False),
            get_doc=lambda *args: SimpleNamespace(),
            get_traceback=lambda: "traceback",
            log_error=lambda *args: None,
        )
        namespace = {
            "frappe": frappe,
            "_create_production_for_sales_order": lambda *args: {"production_tickets": []},
            "_create_delivery_note_for_sales_order": fail_delivery,
            "_set_restaurant_order_status": lambda *args, **kwargs: statuses.append(args),
            "_append_sales_order_note": lambda *args: notes.append(args),
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        namespace["_background_deliver_pos_order"]("SO-1", previous_status="ready")
        self.assertEqual(statuses, [("SO-1", "ready")])
        self.assertIn("Delivery failed", notes[0][1])
        statuses.clear()
        namespace["_create_delivery_note_for_sales_order"] = lambda *args, **kwargs: "DN-1"
        namespace["_background_deliver_pos_order"]("SO-2", previous_status="ready")
        self.assertEqual(statuses, [("SO-2", "delivered")])

    def test_delivery_queue_deduplicates_repeated_clicks(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        for name in ("deliver_pos_order", "produce_and_deliver_pos_order"):
            fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
            enqueue = next(node for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "enqueue")
            keywords = {item.arg: item.value for item in enqueue.keywords}
            self.assertTrue(ast.literal_eval(keywords["deduplicate"]))
            self.assertIn("restaurant-pos-deliver-", ast.unparse(keywords["job_id"]))
            self.assertIn("previous_status", keywords)


if __name__ == "__main__":
    unittest.main()
