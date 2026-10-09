"""Exercise the catalog page contract without starting a Frappe site."""

import ast
import types
import unittest
from pathlib import Path


class PosBootPageTests(unittest.TestCase):
    def _boot(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_management_pos_boot")
        fn.decorator_list = []
        calls = []
        frappe = types.SimpleNamespace(
            get_all=lambda doctype, **kwargs: [{"name": "ITEM-1", "image": "/item.png"}] if doctype == "Item" else [],
            db=types.SimpleNamespace(exists=lambda *args: False),
        )

        def expensive(name, result):
            def record(*args, **kwargs):
                calls.append(name)
                return result
            return record

        namespace = {
            "frappe": frappe,
            "cint": lambda value: int(value or 0),
            "flt": lambda value: float(value or 0),
            "_": lambda value: value,
            "_ensure_management_access": lambda: None,
            "_core_item_image_field": lambda: "image",
            "_get_core_category_meta_map": lambda: {},
            "_get_core_subcategory_meta_map": lambda: {},
            "_has_column": lambda *args: False,
            "_core_item_filters": lambda *args: {},
            "_serialize_core_item": lambda row, **kwargs: {"name": row["name"]},
            "get_management_pos_config": expensive("config", {}),
            "_management_get_print_brand_settings": expensive("print", {}),
            "_management_pos_payment_boot": expensive("payment", {}),
            "_management_pos_profile_summary": expensive("profile", {}),
            "_get_currency": expensive("currency", "IRR"),
            "_get_single_setting": lambda *args: 0,
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        return namespace["get_management_pos_boot"], calls

    def test_later_pages_skip_expensive_configuration(self):
        boot, calls = self._boot()
        result = boot(limit_start=300, items_only=1)
        self.assertEqual(result["items"], [{"name": "ITEM-1", "out_of_stock": 0, "packaging_price": 0.0}])
        self.assertEqual(result["items_limit_start"], 300)
        self.assertFalse(result["items_has_more"])
        self.assertNotIn("categories", result)
        self.assertEqual(calls, [])

    def test_first_page_keeps_complete_boot_contract(self):
        boot, calls = self._boot()
        result = boot()
        self.assertEqual(result["currency"], "IRR")
        self.assertIn("categories", result)
        self.assertIn("payment", result)
        self.assertIn("pos_config", result)
        self.assertEqual(set(calls), {"config", "print", "payment", "profile", "currency"})


if __name__ == "__main__":
    unittest.main()
