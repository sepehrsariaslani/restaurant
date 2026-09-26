"""Pure safety and estimate checks for customer meal planning."""

import importlib.util
import sys
import types
import unittest
from datetime import date, datetime
from pathlib import Path


def _cint(value=0):
	try:
		return int(float(value or 0))
	except (TypeError, ValueError):
		return 0


def _flt(value=0):
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0.0


class MealPlanningTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe = types.ModuleType("frappe")
		frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
		frappe._ = lambda value: value
		frappe.PermissionError = PermissionError
		frappe.throw = lambda message, error=ValueError: (_ for _ in ()).throw(error(message))
		utils = types.ModuleType("frappe.utils")
		utils.cint = _cint
		utils.flt = _flt
		utils.getdate = lambda value=None: date(2026, 9, 26) if value is None else (value if isinstance(value, date) else datetime.strptime(str(value)[:10], "%Y-%m-%d").date())
		originals = {name: sys.modules.get(name) for name in ("frappe", "frappe.utils")}
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils
		target = Path(__file__).resolve().parents[1] / "api_meal_planning.py"
		spec = importlib.util.spec_from_file_location("restaurant.api_meal_planning_test_target", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)
		for name, value in originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value

	def test_mifflin_estimate_uses_ten_percent_goal_adjustment_and_adult_reference(self):
		result = self.module.calculate_targets({
			"age_years": 30,
			"formula_sex": "مرد",
			"height_cm": 180,
			"weight_kg": 80,
			"activity_level": "فعالیت متوسط",
			"goal": "کاهش وزن",
		})
		self.assertEqual(result["bmi"], 24.7)
		self.assertEqual(result["maintenance_kcal"], 2759)
		self.assertEqual(result["calorie_target_kcal"], 2483)
		self.assertEqual(result["protein_reference_g"], 64)

	def test_missing_formula_inputs_allow_manual_goal_and_require_adult_age_for_suggestions(self):
		adult = self.module.calculate_targets({"age_years": 30, "calorie_target": 1900, "weight_kg": 70})
		self.assertEqual(adult["calorie_target_kcal"], 1900)
		self.assertTrue(adult["estimate_available"])
		self.assertEqual(adult["protein_reference_g"], 56)

		result = self.module.calculate_targets({"calorie_target": 1900, "weight_kg": 70})
		self.assertEqual(result["calorie_target_kcal"], 1900)
		self.assertFalse(result["estimate_available"])
		self.assertIsNone(result["protein_reference_g"])

	def test_minor_and_specialist_profiles_do_not_receive_automatic_targets(self):
		minor = self.module.calculate_targets({"age_years": 16, "height_cm": 165, "weight_kg": 60, "calorie_target": 2000})
		self.assertFalse(minor["estimate_available"])
		self.assertIsNone(minor["calorie_target_kcal"])
		self.assertIsNone(minor["protein_reference_g"])
		self.assertIsNone(minor["bmi"])

		specialist = self.module.calculate_targets({"needs_specialist": 1, "age_years": 30, "weight_kg": 70})
		self.assertFalse(specialist["estimate_available"])
		self.assertIsNone(specialist["protein_reference_g"])

	def test_incomplete_item_data_and_allergy_match_block_automatic_suggestions(self):
		base = {
			"name": "FOOD-1",
			"nutrition_verified": 1,
			"allergen_reviewed": 1,
			"ingredients_reviewed": 1,
			"nutrition": {"kcal": 350, "protein_g": 28},
			"base_price": 120000,
			"allergens": ["بادام"],
			"ingredient_tags": ["مرغ"],
		}
		self.assertEqual(self.module._recommendation_block_reason(base, {"بادام"}, set(), set()), "با حساسیت ثبت‌شدهٔ مشتری تطابق دارد.")
		incomplete = {**base, "nutrition_verified": 0}
		self.assertTrue(self.module._recommendation_block_reason(incomplete, set(), set(), set()))
		self.assertTrue(self.module._recommendation_block_reason(base, set(), {"FOOD-1"}, set()))

	def test_order_revalidation_blocks_unknown_allergens_and_disliked_foods(self):
		item = {"name": "FOOD-2", "allergens": [], "allergen_reviewed": 0, "ingredient_tags": []}
		self.assertTrue(self.module._order_block_reason(item, set(), set(), set()))
		item["allergen_reviewed"] = 1
		self.assertEqual(self.module._order_block_reason(item, set(), {"FOOD-2"}, set()), "این محصول با انتخاب‌های نامطلوب ثبت‌شدهٔ شما تطابق دارد.")

	def test_manual_food_keeps_missing_nutrients_unknown_after_saving(self):
		row = self.module._normalize_plan_item({
			"source_type": "ثبت دستی",
			"meal_slot": "میان‌وعده",
			"manual_name": "خوراک دستی",
			"nutrition": {"kcal": 85, "protein_g": None},
		})
		self.assertEqual(row["manual_kcal_known"], 1)
		self.assertEqual(row["manual_protein_known"], 0)
		self.assertEqual(row["manual_nutrition_complete"], 0)

		manual = types.SimpleNamespace(
			name="ROW-1", meal_slot="میان‌وعده", source_type="ثبت دستی", item_code="",
			qty=1, customization_json="{}", manual_name="خوراک دستی", manual_quantity="یک عدد",
			manual_kcal_known=1, manual_protein_known=0, kcal=85, protein_g=0, carb_g=0, fat_g=0,
		)
		plan = types.SimpleNamespace(
			name="PLAN-1", title="روز من", branch="BRANCH-1", weekdays_json="[]", active=1,
			last_cart_prepared_date="", get=lambda key, default=None: {"items": [manual]}.get(key, default),
		)
		payload = self.module._meal_plan_payload(plan)
		self.assertEqual(payload["items"][0]["nutrition"]["kcal"], 85)
		self.assertIsNone(payload["items"][0]["nutrition"]["protein_g"])

	def test_plan_ownership_and_one_plan_per_date_are_checked_server_side(self):
		frappe = self.module.frappe
		frappe.db = types.SimpleNamespace(
			exists=lambda _doctype, filters: filters.get("customer") == "CUST-1",
		)
		frappe.get_doc = lambda _doctype, _name: types.SimpleNamespace(name="PLAN-1")
		self.assertEqual(self.module._owned_plan("PLAN-1", "CUST-1").name, "PLAN-1")
		with self.assertRaises(PermissionError):
			self.module._owned_plan("PLAN-1", "CUST-2")
		plan = types.SimpleNamespace(active=1, weekdays_json='["شنبه"]', last_cart_prepared_date="2026-09-26")
		with self.assertRaises(ValueError):
			self.module._validate_plan_run(plan, date(2026, 9, 26), "شنبه")

	def test_branch_change_never_substitutes_a_missing_product(self):
		frappe = self.module.frappe
		class Plan(types.SimpleNamespace):
			def get(self, key, default=None):
				return getattr(self, key, default)

		plan = Plan(
			name="PLAN-1", title="برنامهٔ من", active=1, customer="CUST-1", branch="BRANCH-A",
			weekdays_json='["شنبه"]', last_cart_prepared_date="", items=[types.SimpleNamespace(
				source_type="وی‌درخت", item_code="SKU-1", qty=1, customization_json="{}"
			)], save=lambda **_kwargs: self.fail("a warning must not mark this date as prepared"),
		)
		profile = types.SimpleNamespace(consent=1, allergens_json="[]", disliked_items_json="[]", disliked_ingredients_json="[]")
		frappe.db = types.SimpleNamespace(
			exists=lambda _doctype, filters: filters.get("customer") == "CUST-1" and filters.get("name") == "PLAN-1",
			sql=lambda *_args, **_kwargs: None,
		)
		frappe.get_doc = lambda _doctype, _name: plan
		originals = {
			"_identity": self.module._identity,
			"_get_profile": self.module._get_profile,
			"_valid_customer_branch": self.module._valid_customer_branch,
			"_get_catalog": self.module._get_catalog,
		}
		self.addCleanup(lambda: [setattr(self.module, key, value) for key, value in originals.items()])
		self.module._identity = lambda _token: {"customer": "CUST-1"}
		self.module._get_profile = lambda _customer: profile
		self.module._valid_customer_branch = lambda _branch: True
		self.module._get_catalog = lambda _branch: []
		result = self.module.prepare_my_meal_plan_order(customer_token="signed-session", name="PLAN-1", branch="BRANCH-B")
		self.assertFalse(result["can_order"])
		self.assertEqual(result["items"], [])
		self.assertIn("محصول در این شعبه ناموجود است.", [row["reason"] for row in result["warnings"]])


if __name__ == "__main__":
	unittest.main()
