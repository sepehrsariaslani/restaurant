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
            "_serialize_core_item": lambda row, **kwargs: {"name": row["name"], "price_list_used": kwargs.get("price_list"), "tags_loaded": kwargs.get("tag_titles")},
            "_get_default_selling_price_list_name": expensive("price_list", "Standard Selling"),
            "_get_pos_boot_item_price_map": lambda names, price_list: {},
            "_get_item_tag_titles_for_items": expensive("tags", {"ITEM-1": ["ویژه"]}),
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
        self.assertEqual(result["items"], [{"name": "ITEM-1", "price_list_used": "Standard Selling", "tags_loaded": ["ویژه"], "out_of_stock": 0, "packaging_price": 0.0}])
        self.assertEqual(result["items_limit_start"], 300)
        self.assertFalse(result["items_has_more"])
        self.assertNotIn("categories", result)
        self.assertEqual(calls, ["price_list", "tags"])

    def test_first_page_keeps_complete_boot_contract(self):
        boot, calls = self._boot()
        result = boot()
        self.assertEqual(result["currency"], "IRR")
        self.assertIn("categories", result)
        self.assertIn("payment", result)
        self.assertIn("pos_config", result)
        self.assertEqual(set(calls), {"price_list", "tags", "config", "print", "payment", "profile", "currency"})

    def test_item_tags_are_fetched_in_one_ordered_query(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_get_item_tag_titles_for_items")
        calls = []

        class Row(dict):
            __getattr__ = dict.get

        def query(sql, params, **kwargs):
            calls.append((sql, params, kwargs))
            return [Row(parent="A", title="ویژه"), Row(parent="A", title="تند"), Row(parent="B", title="جدید")]

        namespace = {"frappe": types.SimpleNamespace(db=types.SimpleNamespace(sql=query)), "_item_tag_tables_ready": lambda: True}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        result = namespace["_get_item_tag_titles_for_items"](["A", "B"])
        self.assertEqual(result, {"A": ["ویژه", "تند"], "B": ["جدید"]})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], {"names": ("A", "B")})
        namespace["frappe"].db.sql = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("database unavailable"))
        self.assertIsNone(namespace["_get_item_tag_titles_for_items"](["A"]))

    def test_boot_price_map_reads_unique_item_prices_in_one_query(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_get_pos_boot_item_price_map")
        calls = []

        def get_all(doctype, **kwargs):
            calls.append((doctype, kwargs))
            return [
                {"item_code": "A", "price_list_rate": 25},
                {"item_code": "B", "price_list_rate": 30},
                {"item_code": "B", "price_list_rate": 40},
            ]

        namespace = {"frappe": types.SimpleNamespace(get_all=get_all), "flt": float}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        result = namespace["_get_pos_boot_item_price_map"](["A", "B"], "Standard Selling")
        self.assertEqual(result, {"A": 25.0})
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "Item Price")
        self.assertEqual(calls[0][1]["filters"]["item_code"], ["in", ["A", "B"]])

    def test_broad_customer_search_caps_dropdown_results(self):
        source = Path(__file__).resolve().parents[1] / "api.py"
        tree = ast.parse(source.read_text())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "list_management_customers")
        fn.decorator_list = []
        orders = [
            {"customer_name": f"Customer {index}", "mobile": f"09{index:09d}", "grand_total": index}
            for index in range(250)
        ]
        namespace = {
            "frappe": types.SimpleNamespace(get_all=lambda **kwargs: []),
            "_ensure_management_access": lambda: None,
            "_has_column": lambda *args: False,
            "_management_fetch_web_orders": lambda **kwargs: orders,
            "_is_revenue_order": lambda order: True,
            "_json_safe_datetime": lambda value: value,
            "flt": lambda value: float(value or 0),
            "cint": lambda value: int(value or 0),
        }
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), namespace)
        search = namespace["list_management_customers"]
        self.assertEqual(len(search(search="09")["customers"]), 100)
        self.assertEqual(len(search()["customers"]), 250)


if __name__ == "__main__":
    unittest.main()
