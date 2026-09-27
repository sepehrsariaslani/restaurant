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

	def test_automatic_suggestions_use_recorded_nutrients_and_keep_sensitivity_checks(self):
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
		unverified = {**base, "nutrition_verified": 0}
		self.assertTrue(self.module._nutrition_is_complete(unverified))
		self.assertEqual(self.module._recommendation_block_reason(unverified, set(), set(), set()), "")
		incomplete = {**unverified, "nutrition": {"kcal": 350, "protein_g": None}}
		self.assertIn("کالری و پروتئین", self.module._recommendation_block_reason(incomplete, set(), set(), set()))
		unreviewed = {**unverified, "allergen_reviewed": 0}
		self.assertTrue(self.module._recommendation_block_reason(unreviewed, {"بادام"}, set(), set()))
		self.assertTrue(self.module._recommendation_block_reason(base, set(), {"FOOD-1"}, set()))

	def test_untagged_main_food_is_not_assigned_to_breakfast_or_snack_and_water_is_never_a_meal(self):
		main = {"name": "FOOD-2", "title": "خوراک روز", "meal_slots": []}
		self.assertEqual(self.module._infer_meal_slots(main), ["ناهار", "شام"])
		self.assertEqual(self.module._suggestion_candidates_for_slot([main], "میان‌وعده"), [])
		water = {"name": "WATER-1", "title": "آب واتا کوچولو", "meal_slots": ["میان‌وعده"]}
		self.assertTrue(self.module._is_beverage(water))
		self.assertTrue(self.module._is_beverage({"name": "ESPRESSO-1", "title": "اسپرسو", "category_title": "بار", "subcategory_title": "بار گرم"}))
		self.assertTrue(self.module._is_beverage({"name": "HERBAL-1", "title": "گرم‌نوش طبیعت", "category_title": "بار", "subcategory_title": "دم‌نوش"}))
		self.assertFalse(self.module._is_beverage({"name": "BBQ-1", "title": "باربیکیو مرغ", "category_title": "کاسه"}))
		self.assertEqual(self.module._infer_meal_slots(water), [])
		water_with_zero_calories = {
			**water, "nutrition_verified": 1, "nutrition": {"kcal": 0, "protein_g": 0},
			"base_price": 10000,
		}
		self.assertFalse(self.module._nutrition_is_complete(water_with_zero_calories))
		self.assertIn("نوشیدنی", self.module._recommendation_block_reason(water_with_zero_calories, set(), set(), set()))
		calorie_drink = {
			"name": "SMOOTHIE-1", "title": "اسموتی موز", "category_title": "نوشیدنی",
			"nutrition": {"kcal": 240, "protein_g": 8}, "base_price": 0, "out_of_stock": 1,
		}
		self.assertEqual(self.module._infer_meal_slots(calorie_drink), ["میان‌وعده"])
		self.assertEqual(self.module._recommendation_block_reason(calorie_drink, set(), set(), set()), "")

	def test_suggestion_chooses_calorie_matched_meals_and_leaves_water_out(self):
		profile = types.SimpleNamespace(
			consent=1,
			needs_specialist=0,
			allergens_json="[]",
			disliked_items_json="[]",
			disliked_ingredients_json="[]",
			liked_items_json="[]",
			liked_ingredients_json="[]",
		)
		def item(code, title, kcal, protein, slots):
			return {
				"name": code, "title": title,
				"nutrition": {"kcal": kcal, "protein_g": protein},
				"nutrition_verified": 0, "allergen_reviewed": 1, "ingredients_reviewed": 1,
				"meal_slots": slots, "base_price": 120000, "out_of_stock": 0,
				"allergens": [], "ingredient_tags": [],
			}
		lunch_near_target = item("FOOD-3", "ناهار مرغ", 650, 30, ["ناهار"])
		lunch_far_target = item("FOOD-4", "ناهار سبک", 280, 12, ["ناهار"])
		dinner_near_target = item("FOOD-5", "شام مرغ", 550, 25, ["شام"])
		dinner_far_target = item("FOOD-6", "شام سنگین", 900, 30, ["شام"])
		water = item("WATER-1", "آب واتا کوچولو", 0, 0, ["میان‌وعده"])
		espresso = {**item("ESPRESSO-1", "اسپرسو", 650, 30, ["ناهار"]), "category_title": "بار", "subcategory_title": "بار گرم"}
		herbal_tea = {**item("HERBAL-1", "گرم‌نوش طبیعت", 190, 6, ["میان‌وعده"]), "category_title": "بار", "subcategory_title": "دم‌نوش"}
		originals = {
			"_identity": self.module._identity,
			"_get_profile": self.module._get_profile,
			"_profile_payload": self.module._profile_payload,
			"_valid_customer_branch": self.module._valid_customer_branch,
			"_get_catalog": self.module._get_catalog,
		}
		self.addCleanup(lambda: [setattr(self.module, key, value) for key, value in originals.items()])
		self.module._identity = lambda _token: {"customer": "CUST-1"}
		self.module._get_profile = lambda _customer: profile
		self.module._profile_payload = lambda _doc: {"targets": {"estimate_available": True, "calorie_target_kcal": 1900, "protein_reference_g": 60}}
		self.module._valid_customer_branch = lambda _branch: True
		self.module._get_catalog = lambda _branch: [lunch_near_target, lunch_far_target, dinner_near_target, dinner_far_target, water, espresso, herbal_tea]

		result = self.module.suggest_my_meal_plans(customer_token="signed-session", branch="BRANCH-1")
		self.assertEqual(len(result["suggestions"]), 3)
		first = result["suggestions"][0]
		self.assertEqual([row["item_code"] for row in first["items"]], ["FOOD-3", "FOOD-5", "HERBAL-1"])
		self.assertEqual([row["meal_slot"] for row in first["items"]], ["ناهار", "شام", "میان‌وعده"])
		self.assertEqual(first["covered_slots"], ["ناهار", "شام", "میان‌وعده"])
		self.assertFalse(first["full_day"])
		self.assertNotIn("WATER-1", [row["item_code"] for row in first["items"]])
		self.assertTrue(any(row["item_code"] == "ESPRESSO-1" for suggestion in result["suggestions"] for row in suggestion["items"]))
		self.assertFalse(any(row["item_code"] == "WATER-1" for suggestion in result["suggestions"] for row in suggestion["items"]))
		self.assertFalse(first["nutrition_reviewed"])
		self.assertFalse(first["items"][0]["nutrition_verified"])
		self.assertIn("ثبت‌شدهٔ محصولات", result["reason"])
		self.assertIn("وعده‌های روز را پوشش نمی‌دهد", result["reason"])

	def test_customer_ingredient_options_use_active_first_level_bom_components_with_calories(self):
		menu = [{"name": "MEAL-1", "ingredient_tags": ["برچسب قبلی"]}]
		boms = [
			{"name": "BOM-DEFAULT", "item": "MEAL-1", "is_default": 1, "is_active": 1, "docstatus": 1, "modified": "2026-09-01"},
			{"name": "BOM-OLD", "item": "MEAL-1", "is_default": 0, "is_active": 1, "docstatus": 1, "modified": "2026-09-20"},
			{"name": "BOM-INACTIVE", "item": "MEAL-1", "is_default": 1, "is_active": 0, "docstatus": 1, "modified": "2026-09-25"},
		]
		components = [
			{"parent": "BOM-DEFAULT", "item_code": "ING-WALNUT", "item_name": "مغز گردو"},
			{"parent": "BOM-DEFAULT", "item_code": "PKG-BOX", "item_name": "ظرف غذا"},
			{"parent": "BOM-OLD", "item_code": "ING-CHICKEN", "item_name": "مرغ"},
		]
		masters = [
			{"name": "ING-WALNUT", "item_name": "مغز گردو", "restaurant_nutrition_kcal": 654, "restaurant_allergen_tags": "مغزها"},
			{"name": "PKG-BOX", "item_name": "ظرف غذا", "restaurant_nutrition_kcal": 0, "restaurant_allergen_tags": ""},
			{"name": "ING-CHICKEN", "item_name": "مرغ", "restaurant_nutrition_kcal": 165, "restaurant_allergen_tags": ""},
		]

		result = self.module._attach_direct_bom_ingredients(menu, boms, components, masters)
		self.assertEqual(result[0]["nutrition_ingredient_tags"], ["مغز گردو"])
		self.assertEqual(result[0]["ingredient_tags"], ["برچسب قبلی", "مغز گردو", "ظرف غذا"])
		self.assertEqual(result[0]["allergen_ingredient_tags"], ["مغزها"])
		self.assertTrue(result[0]["ingredient_composition_available"])
		# A nested recipe for one of the ingredients is not traversed.
		self.assertNotIn("مرغ", result[0]["ingredient_tags"])

	def test_known_recipe_ingredients_filter_selected_allergens_without_claiming_review(self):
		item = {
			"name": "MEAL-1", "nutrition": {"kcal": 420, "protein_g": 20}, "base_price": 100000,
			"ingredient_tags": ["مرغ", "گردو"], "ingredient_composition_available": True,
			"allergens": [], "allergen_reviewed": 0, "ingredients_reviewed": 0,
		}
		self.assertEqual(self.module._recommendation_block_reason(item, {"گردو"}, set(), set()), "با حساسیت ثبت‌شدهٔ مشتری تطابق دارد.")
		self.assertEqual(self.module._recommendation_block_reason(item, {"کنجد"}, set(), set()), "")
		self.assertEqual(self.module._recommendation_block_reason(item, set(), set(), {"مرغ"}), "با انتخاب‌های نامطلوب مشتری تطابق دارد.")

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

	def test_scheduled_plan_preparation_bypasses_today_only_guard_and_does_not_mark_day_used(self):
		frappe = self.module.frappe
		class Plan(types.SimpleNamespace):
			def get(self, key, default=None):
				return getattr(self, key, default)
		plan = Plan(
			name="PLAN-SCHEDULE", title="ناهار هفته", active=1, customer="CUST-1", branch="BRANCH-1",
			weekdays_json="[]", last_cart_prepared_date="2026-09-26",
			items=[types.SimpleNamespace(source_type="وی‌درخت", item_code="SKU-1", qty=1, customization_json="{}")],
			save=lambda **_kwargs: self.fail("preparing for a future schedule must not mark today's plan as used"),
		)
		profile = types.SimpleNamespace(consent=1, allergens_json="[]", disliked_items_json="[]", disliked_ingredients_json="[]")
		frappe.db = types.SimpleNamespace(
			exists=lambda _doctype, filters: filters.get("customer") == "CUST-1" and filters.get("name") == "PLAN-SCHEDULE",
			sql=lambda *_args, **_kwargs: None,
		)
		frappe.get_doc = lambda _doctype, _name: plan
		originals = {key: getattr(self.module, key) for key in ("_identity", "_get_profile", "_valid_customer_branch", "_get_catalog")}
		self.addCleanup(lambda: [setattr(self.module, key, value) for key, value in originals.items()])
		self.module._identity = lambda _token: {"customer": "CUST-1"}
		self.module._get_profile = lambda _customer: profile
		self.module._valid_customer_branch = lambda _branch: True
		self.module._get_catalog = lambda _branch: [{
			"name": "SKU-1", "slug": "meal-1", "title": "غذای روز", "base_price": 120000,
			"out_of_stock": 0, "allergens": [], "ingredient_tags": [],
			"allergen_reviewed": 0, "ingredient_composition_available": True,
		}]

		result = self.module.prepare_my_meal_plan_order(customer_token="signed-session", name="PLAN-SCHEDULE", branch="BRANCH-1", for_schedule=1)
		self.assertTrue(result["can_order"])
		self.assertTrue(result["prepared_for_schedule"])
		self.assertEqual(result["items"][0]["item_slug"], "meal-1")
		self.assertEqual(plan.last_cart_prepared_date, "2026-09-26")

	def test_saved_plan_can_be_ordered_off_schedule_once_per_day(self):
		frappe = self.module.frappe
		class Plan(types.SimpleNamespace):
			def get(self, key, default=None):
				return getattr(self, key, default)
		plan = Plan(
			name="PLAN-NOW", title="ناهار من", active=1, customer="CUST-1", branch="BRANCH-1",
			weekdays_json="[]", last_cart_prepared_date="",
			items=[types.SimpleNamespace(source_type="وی‌درخت", item_code="SKU-1", qty=1, customization_json="{}")],
			save=lambda **_kwargs: None,
		)
		profile = types.SimpleNamespace(consent=1, allergens_json="[]", disliked_items_json="[]", disliked_ingredients_json="[]")
		frappe.db = types.SimpleNamespace(
			exists=lambda _doctype, filters: filters.get("customer") == "CUST-1" and filters.get("name") == "PLAN-NOW",
			sql=lambda *_args, **_kwargs: None,
		)
		frappe.get_doc = lambda _doctype, _name: plan
		originals = {key: getattr(self.module, key) for key in ("_identity", "_get_profile", "_valid_customer_branch", "_get_catalog")}
		self.addCleanup(lambda: [setattr(self.module, key, value) for key, value in originals.items()])
		self.module._identity = lambda _token: {"customer": "CUST-1"}
		self.module._get_profile = lambda _customer: profile
		self.module._valid_customer_branch = lambda _branch: True
		self.module._get_catalog = lambda _branch: [{
			"name": "SKU-1", "slug": "meal-1", "title": "غذای روز", "base_price": 120000,
			"out_of_stock": 0, "allergens": [], "ingredient_tags": [], "allergen_reviewed": 1,
		}]

		result = self.module.prepare_my_meal_plan_order(customer_token="signed-session", name="PLAN-NOW", branch="BRANCH-1", order_now=1)
		self.assertTrue(result["can_order"])
		self.assertTrue(result["ordered_outside_plan_weekday"])
		self.assertEqual(plan.last_cart_prepared_date, "2026-09-26")
		with self.assertRaises(ValueError):
			self.module.prepare_my_meal_plan_order(customer_token="signed-session", name="PLAN-NOW", branch="BRANCH-1", order_now=1)


if __name__ == "__main__":
	unittest.main()
