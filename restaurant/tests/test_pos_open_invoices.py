"""The POS open invoice feed is paged before order details are loaded."""

import ast
import unittest
from pathlib import Path
from types import SimpleNamespace


class PosOpenInvoiceTests(unittest.TestCase):
    def test_open_feed_limits_detail_loading_to_one_page(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "list_management_open_invoices")
        fn.decorator_list = []
        queries = []
        detailed_names = []

        def sql(query, params, **kwargs):
            queries.append((query, params))
            return [SimpleNamespace(name=name) for name in ("SO-1", "SO-2", "SO-3")]

        def details(**kwargs):
            detailed_names.extend(kwargs["order_names"])
            self.assertFalse(kwargs["include_items"])
            return [{"name": name, "outstanding_amount": 100} for name in kwargs["order_names"]]

        namespace = {
            "frappe": SimpleNamespace(db=SimpleNamespace(sql=sql)),
            "_ensure_management_access": lambda: None,
            "_has_column": lambda *args: True,
            "_management_fetch_web_orders": details,
            "cint": int,
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        result = namespace["list_management_open_invoices"](limit_start=10, limit_page_length=2)
        self.assertEqual([row["name"] for row in result["orders"]], ["SO-1", "SO-2"])
        self.assertTrue(result["has_more"])
        self.assertEqual(detailed_names, ["SO-1", "SO-2"])
        self.assertEqual(queries[0][1]["limit"], 3)
        self.assertEqual(queries[0][1]["offset"], 10)


if __name__ == "__main__":
    unittest.main()
