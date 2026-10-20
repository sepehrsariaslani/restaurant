"""Isolated tests for the POS printer profile contract."""

import unittest

from restaurant.pos_print_config import clean_management_pos_print_profiles


class PosPrintConfigTests(unittest.TestCase):
	def test_keeps_legacy_customer_receipt_enabled_with_inherited_printer(self):
		profiles = clean_management_pos_print_profiles([{"label": "رسید مشتری", "kind": "customer"}])
		self.assertEqual(profiles, [{
			"label": "رسید مشتری",
			"kind": "customer",
			"printer_name": "",
			"item_groups": [],
			"paper_width_mm": 0,
			"copies": 0,
			"auto_print": 1,
			"show_prices": 1,
			"enabled": 1,
		}])

	def test_sanitizes_printer_settings_and_preserves_explicit_system_default(self):
		profiles = clean_management_pos_print_profiles([{
			"label": "  آشپزخانه  ",
			"kind": "kitchen",
			"printer_name": "@system-default",
			"item_groups": ["غذای گرم", "  ", None],
			"paper_width_mm": "58",
			"copies": "14",
			"auto_print": 1,
			"enabled": 1,
		}])
		self.assertEqual(profiles[0]["label"], "آشپزخانه")
		self.assertEqual(profiles[0]["printer_name"], "@system-default")
		self.assertEqual(profiles[0]["item_groups"], ["غذای گرم"])
		self.assertEqual(profiles[0]["paper_width_mm"], 58)
		self.assertEqual(profiles[0]["copies"], 10)
		self.assertEqual(profiles[0]["auto_print"], 1)

	def test_invalid_profiles_and_values_are_ignored_or_fall_back_safely(self):
		profiles = clean_management_pos_print_profiles([
			None,
			{"kind": "unknown", "paper_width_mm": 72, "copies": "invalid", "auto_print": 0},
		])
		self.assertEqual(len(profiles), 1)
		self.assertEqual(profiles[0]["kind"], "kitchen")
		self.assertEqual(profiles[0]["paper_width_mm"], 0)
		self.assertEqual(profiles[0]["copies"], 0)
		self.assertEqual(profiles[0]["auto_print"], 0)


if __name__ == "__main__":
	unittest.main()
