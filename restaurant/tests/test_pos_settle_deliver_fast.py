"""The combined POS action keeps the payment result when delivery cannot start."""

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace


class PosSettleDeliverTests(unittest.TestCase):
    def test_delivery_lock_skips_cancelled_orders(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_lock_pos_sales_order")
        calls = []
        row = SimpleNamespace(name="SO-1", docstatus=1, status="To Deliver and Bill")
        namespace = {
            "frappe": SimpleNamespace(db=SimpleNamespace(sql=lambda query, name, **kwargs: calls.append((query, name)) or [row])),
            "cint": int,
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        lock = namespace["_lock_pos_sales_order"]
        self.assertTrue(lock("SO-1"))
        self.assertIn("FOR UPDATE", calls[0][0])
        row.status = "Cancelled"
        self.assertFalse(lock("SO-1"))
        self.assertTrue(lock("SO-1", require_active=False))

    def test_background_delivery_and_purge_lock_the_same_sales_order(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue("_lock_pos_sales_order" in functions)
        for name in ("_background_deliver_pos_order", "_background_production_and_delivery", "purge_management_pos_order"):
            calls = [
                node.func.id for node in ast.walk(functions[name])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            ]
            self.assertIn("_lock_pos_sales_order", calls, name)
        purge = functions["purge_management_pos_order"]
        top_level_calls = [
            node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for statement in purge.body for node in ast.walk(statement)
            if isinstance(node, ast.Call) and (isinstance(node.func, ast.Name) or isinstance(node.func, ast.Attribute))
        ]
        self.assertLess(top_level_calls.index("commit"), top_level_calls.index("_lock_pos_sales_order"))

    def test_purge_rolls_back_a_document_when_cancel_hook_fails(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        purge = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "purge_management_pos_order")
        cancel_and_delete = next(
            node for node in purge.body
            if isinstance(node, ast.FunctionDef) and node.name == "_cancel_and_delete"
        )
        document = SimpleNamespace(docstatus=1, flags=SimpleNamespace())
        savepoints = {}
        rollback_calls = []

        def savepoint(name):
            savepoints[name] = document.docstatus

        def rollback(*, save_point):
            rollback_calls.append(save_point)
            document.docstatus = savepoints[save_point]

        def cancel():
            document.docstatus = 2
            raise RuntimeError("(1205, 'Lock wait timeout exceeded')")

        document.cancel = cancel
        db = SimpleNamespace(savepoint=savepoint, rollback=rollback, exists=lambda *args: True)
        frappe = SimpleNamespace(
            db=db,
            get_doc=lambda *args: document,
            generate_hash=lambda **kwargs: "savepoint-1",
            delete_doc=lambda *args, **kwargs: None,
        )
        summary = {"cleaned_records": {}, "errors": []}
        namespace = {"frappe": frappe, "summary": summary, "purge_state": {"transaction_rolled_back": False}}
        exec(compile(ast.Module(body=[cancel_and_delete], type_ignores=[]), str(source), "exec"), namespace)

        namespace["_cancel_and_delete"]("Sales Invoice", ["SI-1"])

        self.assertEqual(document.docstatus, 1)
        self.assertEqual(rollback_calls, ["pos_purge_savepoint-1"])
        self.assertIn("1205", summary["errors"][0])

    def test_purge_preserves_deadlock_error_when_database_invalidates_savepoint(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        purge = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "purge_management_pos_order")
        cancel_and_delete = next(
            node for node in purge.body
            if isinstance(node, ast.FunctionDef) and node.name == "_cancel_and_delete"
        )
        document = SimpleNamespace(docstatus=1, flags=SimpleNamespace())
        cancel_calls = []
        rollback_calls = []

        def cancel():
            cancel_calls.append(document.name)
            raise RuntimeError("(1213, 'Deadlock found when trying to get lock')")

        document.name = "SI-1"
        document.cancel = cancel
        def rollback(*, save_point=None):
            if save_point:
                raise RuntimeError("SAVEPOINT does not exist")
            rollback_calls.append("full")

        db = SimpleNamespace(savepoint=lambda name: None, rollback=rollback, exists=lambda *args: True)
        frappe = SimpleNamespace(
            db=db,
            get_doc=lambda doctype, name: document,
            generate_hash=lambda **kwargs: "savepoint-1",
            delete_doc=lambda *args, **kwargs: None,
        )
        summary = {"cleaned_records": {}, "errors": []}
        purge_state = {"transaction_rolled_back": False}
        namespace = {"frappe": frappe, "summary": summary, "purge_state": purge_state}
        exec(compile(ast.Module(body=[cancel_and_delete], type_ignores=[]), str(source), "exec"), namespace)

        namespace["_cancel_and_delete"]("Sales Invoice", ["SI-1", "SI-2"])

        self.assertEqual(cancel_calls, ["SI-1"])
        self.assertTrue(purge_state["transaction_rolled_back"])
        self.assertIn("Deadlock found when trying to get lock", summary["errors"][0])
        self.assertEqual(rollback_calls, ["full"])

    def test_purge_returns_retryable_partial_result_after_a_deadlock(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        purge = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "purge_management_pos_order")
        purge.decorator_list = []
        commits = []
        rollback_calls = []
        callbacks = {
            "before_commit": ["old before commit"],
            "after_commit": ["old after commit"],
            "value_cache": {"Sales Invoice": "stale value"},
        }

        def get_all(doctype, **kwargs):
            return ["SI-1"] if doctype == "Sales Invoice Item" else []

        def cancel():
            raise RuntimeError("(1213, 'Deadlock found when trying to get lock')")

        document = SimpleNamespace(docstatus=1, flags=SimpleNamespace(), cancel=cancel)
        def rollback(*, save_point=None):
            if save_point:
                raise RuntimeError("SAVEPOINT does not exist")
            rollback_calls.append("full")
            callbacks["before_commit"].clear()
            callbacks["after_commit"].clear()
            callbacks["value_cache"].clear()

        db = SimpleNamespace(
            commit=lambda: commits.append("commit"),
            exists=lambda doctype, name: True,
            savepoint=lambda name: None,
            rollback=rollback,
        )
        frappe = SimpleNamespace(
            db=db,
            get_all=get_all,
            get_doc=lambda *args: document,
            generate_hash=lambda **kwargs: "savepoint-1",
            delete_doc=lambda *args, **kwargs: None,
        )
        namespace = {
            "frappe": frappe,
            "_ensure_management_access": lambda: None,
            "_resolve_sales_order_name": lambda name: name,
            "_lock_pos_sales_order": lambda *args, **kwargs: True,
            "_has_column": lambda *args: True,
        }
        exec(compile(ast.Module(body=[purge], type_ignores=[]), str(source), "exec"), namespace)

        result = namespace["purge_management_pos_order"]("SO-1")

        self.assertEqual(result["status"], "partial_success")
        self.assertIn("Deadlock found when trying to get lock", result["summary"]["errors"][0])
        self.assertEqual(commits, ["commit"])
        self.assertEqual(rollback_calls, ["full"])
        self.assertEqual(callbacks, {"before_commit": [], "after_commit": [], "value_cache": {}})

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
            "_lock_pos_sales_order": lambda *args: True,
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

    def test_create_and_settle_background_failure_keeps_order_undelivered(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_background_production_and_delivery")
        fn.decorator_list = []
        statuses = []
        notes = []
        attempts = []

        def fail_delivery(*args, **kwargs):
            attempts.append(args)
            raise RuntimeError("delivery note failed")

        frappe = SimpleNamespace(
            db=SimpleNamespace(commit=lambda: None, exists=lambda *args: False),
            get_doc=lambda *args: SimpleNamespace(),
            get_traceback=lambda: "traceback",
            log_error=lambda *args: None,
        )
        namespace = {
            "frappe": frappe,
            "_lock_pos_sales_order": lambda *args: True,
            "_create_production_for_sales_order": lambda *args: {"production_tickets": []},
            "_create_delivery_note_for_sales_order": fail_delivery,
            "_set_restaurant_order_status": lambda *args, **kwargs: statuses.append(args),
            "_append_sales_order_note": lambda *args: notes.append(args),
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        namespace["_background_production_and_delivery"]("SO-1")
        self.assertEqual(len(attempts), 2)
        self.assertNotIn(("SO-1", "delivered"), statuses)
        self.assertIn("Delivery", notes[0][1])

        attempts.clear()
        statuses.clear()
        notes.clear()

        def deliver_on_retry(*args, **kwargs):
            attempts.append(args)
            if len(attempts) == 1:
                raise RuntimeError("stock not ready")
            return "DN-1"

        namespace["_create_delivery_note_for_sales_order"] = deliver_on_retry
        namespace["_background_production_and_delivery"]("SO-2")
        self.assertEqual(len(attempts), 2)
        self.assertEqual(statuses, [("SO-2", "delivered")])
        self.assertEqual(notes, [])


if __name__ == "__main__":
    unittest.main()
