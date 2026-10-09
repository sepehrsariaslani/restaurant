"""An invoice contributes its unpaid balance once per order, not once per item."""

import ast
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace


class PosInvoiceOutstandingTests(unittest.TestCase):
    def test_multi_line_invoice_is_counted_once(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_management_invoice_outstanding_maps")
        namespace = {"defaultdict": defaultdict, "flt": float}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        items = [
            SimpleNamespace(sales_order="SO-1", parent="SI-1"),
            SimpleNamespace(sales_order="SO-1", parent="SI-1"),
            SimpleNamespace(sales_order="SO-1", parent="SI-2"),
            SimpleNamespace(sales_order="SO-1", parent="SI-CANCELLED"),
        ]
        invoices = [SimpleNamespace(name="SI-1", outstanding_amount=100), SimpleNamespace(name="SI-2", outstanding_amount=25)]
        outstanding, linked = namespace["_management_invoice_outstanding_maps"](items, invoices)
        self.assertEqual(outstanding["SO-1"], 125.0)
        self.assertEqual(linked["SO-1"], {"SI-1", "SI-2"})


if __name__ == "__main__":
    unittest.main()
