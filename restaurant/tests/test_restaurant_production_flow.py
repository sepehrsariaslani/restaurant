import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant.api import _recalculate_line


class TestRestaurantProductionFlow(FrappeTestCase):
    def _menu_doc(self):
        return frappe._dict(
            {
                "doctype": "Restaurant Menu Item",
                "title": "سالاد مرغ",
                "base_price": 600000,
                "ingredients": [
                    frappe._dict(
                        {
                            "ingredient_name": "مرغ",
                            "customer_label": "مرغ",
                            "base_qty": 1,
                            "is_included_by_default": 1,
                            "can_remove": 0,
                            "is_required": 1,
                            "is_editable_qty": 1,
                            "min_multiplier": 1,
                            "max_multiplier": 3,
                            "step_multiplier": 0.5,
                            "extra_when_added": 80000,
                        }
                    ),
                    frappe._dict(
                        {
                            "ingredient_name": "خیار",
                            "customer_label": "خیار",
                            "base_qty": 1,
                            "is_included_by_default": 1,
                            "can_remove": 1,
                            "is_required": 0,
                            "is_editable_qty": 1,
                            "min_multiplier": 0,
                            "max_multiplier": 2,
                            "step_multiplier": 0.5,
                            "extra_when_added": 20000,
                        }
                    ),
                ],
                "modifier_groups": [],
            }
        )

    def test_recalculate_line_accepts_double_protein(self):
        menu_doc = self._menu_doc()
        calc = _recalculate_line(
            menu_doc,
            quantity=1,
            customization={
                "ingredient_adjustments": [
                    {"ingredient_key": "مرغ", "multiplier": 2},
                    {"ingredient_key": "خیار", "multiplier": 1},
                ],
                "selected_modifiers": [],
            },
            branch_markup_percent=0,
        )

        self.assertGreater(calc["unit_price"], 600000)
        self.assertEqual(calc["normalized_customization"]["ingredient_adjustments"][0]["ingredient_key"], "مرغ")

    def test_recalculate_line_rejects_required_below_min(self):
        menu_doc = self._menu_doc()

        with self.assertRaises(frappe.ValidationError):
            _recalculate_line(
                menu_doc,
                quantity=1,
                customization={
                    "ingredient_adjustments": [
                        {"ingredient_key": "مرغ", "multiplier": 0},
                    ],
                    "selected_modifiers": [],
                },
                branch_markup_percent=0,
            )

    def test_recalculate_line_rejects_step_mismatch(self):
        menu_doc = self._menu_doc()

        with self.assertRaises(frappe.ValidationError):
            _recalculate_line(
                menu_doc,
                quantity=1,
                customization={
                    "ingredient_adjustments": [
                        {"ingredient_key": "مرغ", "multiplier": 1.3},
                    ],
                    "selected_modifiers": [],
                },
                branch_markup_percent=0,
            )
