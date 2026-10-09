"""The combined POS action keeps the payment result when delivery cannot start."""

import ast
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
