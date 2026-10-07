import unittest
import ast
from pathlib import Path

from restaurant.production_inventory_helpers import (
	_inv_branch_production_work_order_names,
	_inv_build_production_correction_rows,
	_inv_correction_rows_match,
	_inv_merge_branch_production_settings,
	_inv_summarize_correction_rows,
)


class TestBranchProductionSettings(unittest.TestCase):
	def test_save_changes_only_requested_warehouse(self):
		current = {
			"branch": "DEFAULT",
			"company": "وی‌درخت",
			"is_active": 1,
			"raw_warehouse": "کالاها در ترانزیت - V",
			"kitchen_wip_warehouse": "کالاها در ترانزیت - V",
			"finished_goods_warehouse": "کالاها در ترانزیت - V",
		}

		result = _inv_merge_branch_production_settings(
			current, {"finished_goods_warehouse": "فروشگاه - V"}
		)

		self.assertEqual(result["finished_goods_warehouse"], "فروشگاه - V")
		self.assertEqual(result["raw_warehouse"], "کالاها در ترانزیت - V")
		self.assertEqual(result["kitchen_wip_warehouse"], "کالاها در ترانزیت - V")
		self.assertEqual(result["company"], "وی‌درخت")

	def test_correction_candidates_are_limited_to_matching_branch_tickets(self):
		tickets = [
			{"name": "T-DEFAULT", "branch": "DEFAULT", "company": "وی‌درخت", "work_order": "WO-1"},
			{"name": "T-OTHER", "branch": "شعبه دوم", "company": "وی‌درخت", "work_order": "WO-2"},
			{"name": "T-OTHER-COMPANY", "branch": "DEFAULT", "company": "شرکت دیگر", "work_order": "WO-3"},
		]
		linked_work_orders = [
			{"name": "WO-4", "company": "وی‌درخت", "docstatus": 1, "restaurant_production_ticket": "T-DEFAULT"},
			{"name": "WO-5", "company": "وی‌درخت", "docstatus": 0, "restaurant_production_ticket": "T-DEFAULT"},
			{"name": "WO-6", "company": "وی‌درخت", "docstatus": 1, "restaurant_production_ticket": "T-OTHER"},
		]

		result = _inv_branch_production_work_order_names(
			tickets, linked_work_orders, "DEFAULT", "وی‌درخت"
		)

		self.assertEqual(result, ["WO-1", "WO-4"])

	def test_unapproved_fields_are_not_merged(self):
		result = _inv_merge_branch_production_settings(
			{"branch": "DEFAULT", "company": "وی‌درخت", "pricing_markup_percent": 35},
			{"pricing_markup_percent": 99, "company": "شرکت دیگر", "finished_goods_warehouse": "فروشگاه - V"},
		)

		self.assertEqual(result["company"], "وی‌درخت")
		self.assertEqual(result["pricing_markup_percent"], 35)
		self.assertEqual(result["finished_goods_warehouse"], "فروشگاه - V")


class TestProductionCorrectionPreview(unittest.TestCase):
	def test_preview_only_includes_positive_balances_and_preserves_uom(self):
		rows = _inv_build_production_correction_rows(
			produced_warehouses={"A": ["ترانزیت"], "B": ["ترانزیت"], "C": ["ترانزیت"]},
			balances={
				("A", "ترانزیت"): 3,
				("B", "ترانزیت"): 0,
				("C", "ترانزیت"): -4,
			},
			item_uoms={"A": "عدد", "B": "گرم", "C": "عدد"},
			item_names={"A": "کالای یک", "B": "کالای دو", "C": "کالای سه"},
			store_balances={"A": -2, "B": -4, "C": 1},
			target_warehouse="فروشگاه",
		)

		self.assertEqual(len(rows), 1)
		self.assertEqual(rows[0]["item_code"], "A")
		self.assertEqual(rows[0]["qty_to_transfer"], 3)
		self.assertEqual(rows[0]["stock_uom"], "عدد")
		self.assertEqual(rows[0]["store_qty"], -2)

	def test_summary_never_combines_different_uoms(self):
		result = _inv_summarize_correction_rows([
			{"item_code": "A", "stock_uom": "عدد", "qty_to_transfer": 3},
			{"item_code": "B", "stock_uom": "گرم", "qty_to_transfer": 12},
			{"item_code": "C", "stock_uom": "عدد", "qty_to_transfer": 2},
		])

		self.assertEqual(result, [
			{"stock_uom": "عدد", "item_count": 2, "qty_to_transfer": 5},
			{"stock_uom": "گرم", "item_count": 1, "qty_to_transfer": 12},
		])

	def test_apply_detects_bin_changes_after_preview(self):
		preview = [{
			"item_code": "A",
			"source_warehouse": "ترانزیت",
			"target_warehouse": "فروشگاه",
			"stock_uom": "عدد",
			"transit_qty": 3,
			"store_qty": -2,
			"qty_to_transfer": 3,
		}]
		changed = [{**preview[0], "transit_qty": 2, "qty_to_transfer": 2}]

		self.assertFalse(_inv_correction_rows_match(preview, changed))
		self.assertTrue(_inv_correction_rows_match(preview, preview))


class TestInventoryWriteContracts(unittest.TestCase):
	def test_native_settings_and_correction_writes_are_post_only(self):
		source = Path(__file__).resolve().parents[1] / "api_inventory.py"
		module = ast.parse(source.read_text())
		functions = {
			node.name: node
			for node in module.body
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
		}
		for name in (
			"save_management_branch_production_settings",
			"apply_management_production_warehouse_correction",
		):
			decorator = next(
				decorator
				for decorator in functions[name].decorator_list
				if isinstance(decorator, ast.Call)
				and isinstance(decorator.func, ast.Attribute)
				and decorator.func.attr == "whitelist"
			)
			methods = next(keyword.value for keyword in decorator.keywords if keyword.arg == "methods")
			self.assertEqual(ast.literal_eval(methods), ["POST"])

	def test_inventory_writes_enforce_native_permissions(self):
		source = Path(__file__).resolve().parents[1] / "api_inventory.py"
		module = ast.parse(source.read_text())
		text = source.read_text()
		self.assertIn("_inv_require_doctype_permission(\n\t\tBRANCH_PRODUCTION_SETTINGS_DOCTYPE", text)
		self.assertIn('"Stock Entry", "create"', text)
		self.assertIn('"Stock Entry", "submit"', text)
		create_entry = next(
			node
			for node in module.body
			if isinstance(node, ast.FunctionDef)
			and node.name == "_inv_create_production_correction_entry"
		)
		insert_calls = [
			node
			for node in ast.walk(create_entry)
			if isinstance(node, ast.Call)
			and isinstance(node.func, ast.Attribute)
			and node.func.attr == "insert"
		]
		self.assertEqual(len(insert_calls), 1)
		self.assertNotIn(
			"ignore_permissions",
			{keyword.arg for keyword in insert_calls[0].keywords},
		)
