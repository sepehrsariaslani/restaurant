import unittest

from restaurant.pos_custom_pricing import apply_custom_price_overrides


class TestPosCustomPricing(unittest.TestCase):
	def setUp(self):
		self.line = {
			"item_code": "MENU-ITEM",
			"qty": 2,
			"unit_price": 130,
			"line_total": 260,
			"extra_charge": 30,
			"normalized_customization": {
				"selected_modifiers": [
					{
						"group": "افزودنی",
						"option": "فیله مرغ",
						"qty": 2,
						"type": "add_on",
						"item_code": "MOD-FILLET",
						"unit_rate": 10,
						"pricing_qty_in_stock_uom": 2,
						"pricing_uom": "Nos",
						"pricing_delta": 20,
					}
				],
				"selected_alternatives": [
					{"ingredient_key": "قهوه", "alternative_item": "ARABICA"}
				],
			},
			"pricing_breakdown": {
				"base_price": 100,
				"modifier_delta_total": 20,
				"ingredient_delta_total": 10,
				"unit_price": 130,
				"line_total": 260,
				"modifiers": [],
				"ingredients": [
					{
						"ingredient_key": "قهوه",
						"base_item_code": "ROBUSTA",
						"item_code": "ARABICA",
						"selected_alternative_item": "ARABICA",
						"source_type": "bom_item",
						"base_qty_in_stock_uom": 4,
						"base_stock_uom": "Nos",
						"base_pricing_unit_rate": 10,
						"pricing_rate": 30,
						"pricing_qty_in_stock_uom": 2,
						"base_pricing_total_price": 40,
						"base_qty": 2,
						"base_multiplier": 2,
						"selected_base_qty": 2,
						"selected_multiplier": 1,
						"pricing_delta": 10,
						"stock_uom": "Nos",
					}
				],
			},
			"ingredient_components": [],
			"selections": [
				{
					"kind": "modifier",
					"group": "افزودنی",
					"option": "فیله مرغ",
					"delta_price": 20,
				},
				{
					"kind": "ingredient_alternative",
					"ingredient_key": "قهوه",
					"item_code": "ARABICA",
					"delta_price": 10,
				},
			],
		}
		self.line["pricing_breakdown"]["modifiers"] = self.line["normalized_customization"]["selected_modifiers"]

	def test_overrides_are_applied_to_this_line_and_snapshotted(self):
		result = apply_custom_price_overrides(
			self.line,
			{
				"base_unit_price": 120,
				"modifier_unit_prices": [
					{"group": "افزودنی", "option": "فیله مرغ", "unit_rate": 12}
				],
				"ingredient_unit_prices": [
					{"ingredient_key": "قهوه", "item_code": "ARABICA", "unit_rate": 20}
				],
			},
			item_code="MENU-VARIANT",
		)

		self.assertEqual(result["unit_price"], 144)
		self.assertEqual(result["line_total"], 288)
		self.assertEqual(result["pricing_breakdown"]["base_price"], 120)
		self.assertEqual(result["pricing_breakdown"]["modifier_delta_total"], 24)
		self.assertEqual(result["pricing_breakdown"]["ingredient_delta_total"], 0)
		self.assertEqual(result["normalized_customization"]["custom_price_overrides"]["base_unit_price"], 120)
		self.assertEqual(result["pricing_breakdown"]["ingredients"][0]["custom_price_unit_rate"], 20)
		self.assertEqual(result["normalized_customization"]["custom_price_overrides"]["item_code"], "MENU-VARIANT")
		self.assertEqual(result["normalized_customization"]["custom_price_overrides"]["modifier_unit_prices"][0], {
			"group": "افزودنی",
			"option": "فیله مرغ",
			"item_code": "MOD-FILLET",
			"pricing_qty_in_stock_uom": 2,
			"pricing_uom": "Nos",
			"unit_rate": 12,
			"pricing_delta": 24,
		})
		self.assertEqual(result["normalized_customization"]["custom_price_overrides"]["ingredient_unit_prices"][0], {
			"ingredient_key": "قهوه",
			"base_item_code": "ROBUSTA",
			"item_code": "ARABICA",
			"base_qty_in_stock_uom": 4,
			"selected_qty_in_stock_uom": 2,
			"base_unit_rate": 10,
			"unit_rate": 20,
			"base_total_price": 40,
			"selected_total_price": 40,
			"pricing_delta": 0,
			"base_stock_uom": "Nos",
			"selected_stock_uom": "Nos",
		})
		self.assertEqual(self.line["unit_price"], 130)
		self.assertEqual(
			self.line["normalized_customization"]["selected_modifiers"][0]["unit_rate"], 10
		)

	def test_reapplying_same_overrides_is_idempotent(self):
		overrides = {
			"base_unit_price": 120,
			"modifier_unit_prices": [
				{"group": "افزودنی", "option": "فیله مرغ", "unit_rate": 12}
			],
			"ingredient_unit_prices": [
				{"ingredient_key": "قهوه", "item_code": "ARABICA", "unit_rate": 20}
			],
		}
		first = apply_custom_price_overrides(self.line, overrides, item_code="MENU-VARIANT")
		second = apply_custom_price_overrides(first, overrides, item_code="MENU-VARIANT")

		self.assertEqual(second, first)
		self.assertEqual(second["line_total"], 288)

	def test_rejects_price_override_for_unselected_modifier(self):
		with self.assertRaisesRegex(ValueError, "selected modifier"):
			apply_custom_price_overrides(
				self.line,
				{"modifier_unit_prices": [{"group": "افزودنی", "option": "پنیر", "unit_rate": 5}]},
			)

	def test_rejects_duplicate_modifier_price_override_targets(self):
		with self.assertRaisesRegex(ValueError, "duplicate modifier"):
			apply_custom_price_overrides(
				self.line,
				{
					"modifier_unit_prices": [
						{"group": "افزودنی", "option": "فیله مرغ", "unit_rate": 12},
						{"group": "افزودنی", "option": "فیله مرغ", "unit_rate": 13},
					]
				},
			)

	def test_rejects_negative_or_non_finite_rates(self):
		for rate in (-1, float("inf"), float("nan")):
			with self.subTest(rate=rate):
				with self.assertRaises(ValueError):
					apply_custom_price_overrides(self.line, {"base_unit_price": rate})

	def test_rejects_alternative_price_that_does_not_match_selected_bom_item(self):
		with self.assertRaisesRegex(ValueError, "selected BOM alternative"):
			apply_custom_price_overrides(
				self.line,
				{
					"ingredient_unit_prices": [
						{"ingredient_key": "قهوه", "item_code": "ROBUSTA", "unit_rate": 25}
					]
				},
			)

	def test_prices_a_selected_alternative_with_a_negative_catalog_delta(self):
		self.line["unit_price"] = 110
		self.line["line_total"] = 220
		self.line["pricing_breakdown"]["unit_price"] = 110
		self.line["pricing_breakdown"]["line_total"] = 220
		self.line["pricing_breakdown"]["ingredient_delta_total"] = -10
		self.line["pricing_breakdown"]["ingredients"][0]["pricing_delta"] = -10

		result = apply_custom_price_overrides(
			self.line,
			{
				"ingredient_unit_prices": [
					{"ingredient_key": "قهوه", "item_code": "ARABICA", "unit_rate": 20}
				]
			},
		)

		self.assertEqual(result["unit_price"], 120)
		self.assertEqual(result["pricing_breakdown"]["ingredient_delta_total"], 0)


if __name__ == "__main__":
	unittest.main()
