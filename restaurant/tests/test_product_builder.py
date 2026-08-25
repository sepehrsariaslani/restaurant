# Copyright (c) 2026, Sepehr Sariaslani
# See license.txt

import frappe
import unittest
import json

try:
    from frappe.utils import slugify
except ImportError:
    import re

    def slugify(text):
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        text = re.sub(r"^-+|-+$", "", text)
        return text


class TestProductBuilderTemplate(unittest.TestCase):
    """Unit tests for Product Builder Template DocType."""

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        frappe.set_user("Administrator")

    def setUp(self):
        """Clean up before each test."""
        frappe.db.delete("Product Builder Template", {"title": ["like", "Test%"]})
        frappe.db.commit()

    def tearDown(self):
        """Clean up after each test."""
        frappe.db.delete("Product Builder Template", {"title": ["like", "Test%"]})
        frappe.db.commit()

    def _make_template(self, title="Test Template", slug=None, steps=None, is_active=1):
        """Helper to create a template with minimal valid data."""
        if steps is None:
            steps = [
                {
                    "step_title": "Step 1",
                    "step_key": "step_1",
                    "sort_order": 0,
                    "selection_mode": "single",
                    "options": [
                        {
                            "option_label": "Option A",
                            "option_key": "opt_a",
                            "sort_order": 0,
                            "price_type": "fixed",
                        }
                    ],
                }
            ]

        doc = frappe.get_doc(
            {
                "doctype": "Product Builder Template",
                "title": title,
                "slug": slug or slugify(title),
                "is_active": is_active,
                "steps": steps,
            }
        )
        doc.insert(ignore_permissions=True)
        return doc

    def test_template_creation(self):
        """Template with valid steps/options saves correctly."""
        doc = self._make_template()
        self.assertIsNotNone(doc.name)
        self.assertTrue(doc.name.startswith("PBT-"))

    def test_template_slug_auto_generation(self):
        """Slug is auto-generated from title."""
        doc = self._make_template(title="My Salad Builder")
        self.assertEqual(doc.slug, "my-salad-builder")

    def test_template_unique_slug(self):
        """Duplicate slug is rejected."""
        self._make_template(title="Test Unique", slug="unique-slug")
        with self.assertRaises(frappe.exceptions.ValidationError):
            self._make_template(title="Test Unique 2", slug="unique-slug")

    def test_template_minimum_steps(self):
        """Template with 0 steps is rejected."""
        doc = frappe.get_doc(
            {
                "doctype": "Product Builder Template",
                "title": "Test No Steps",
                "slug": "no-steps",
                "steps": [],
            }
        )
        with self.assertRaises(frappe.exceptions.ValidationError):
            doc.insert(ignore_permissions=True)

    def test_template_unique_step_keys(self):
        """Duplicate step keys are rejected."""
        steps = [
            {
                "step_title": "Step 1",
                "step_key": "same_key",
                "sort_order": 0,
                "selection_mode": "single",
                "options": [
                    {
                        "option_label": "Opt A",
                        "option_key": "opt_a",
                        "sort_order": 0,
                        "price_type": "fixed",
                    }
                ],
            },
            {
                "step_title": "Step 2",
                "step_key": "same_key",
                "sort_order": 1,
                "selection_mode": "single",
                "options": [
                    {
                        "option_label": "Opt B",
                        "option_key": "opt_b",
                        "sort_order": 0,
                        "price_type": "fixed",
                    }
                ],
            },
        ]
        with self.assertRaises(frappe.exceptions.ValidationError):
            self._make_template(title="Test Dup Steps", steps=steps)

    def test_template_unique_option_keys(self):
        """Duplicate option keys within a step are rejected."""
        steps = [
            {
                "step_title": "Step 1",
                "step_key": "step_1",
                "sort_order": 0,
                "selection_mode": "single",
                "options": [
                    {
                        "option_label": "Opt A",
                        "option_key": "same_opt",
                        "sort_order": 0,
                        "price_type": "fixed",
                    },
                    {
                        "option_label": "Opt B",
                        "option_key": "same_opt",
                        "sort_order": 1,
                        "price_type": "fixed",
                    },
                ],
            }
        ]
        with self.assertRaises(frappe.exceptions.ValidationError):
            self._make_template(title="Test Dup Opts", steps=steps)

    def test_template_step_sorting(self):
        """Steps are sorted by sort_order on save."""
        steps = [
            {
                "step_title": "Step 3",
                "step_key": "step_3",
                "sort_order": 3,
                "selection_mode": "single",
                "options": [
                    {
                        "option_label": "Opt C",
                        "option_key": "opt_c",
                        "sort_order": 0,
                        "price_type": "fixed",
                    }
                ],
            },
            {
                "step_title": "Step 1",
                "step_key": "step_1",
                "sort_order": 1,
                "selection_mode": "single",
                "options": [
                    {
                        "option_label": "Opt A",
                        "option_key": "opt_a",
                        "sort_order": 0,
                        "price_type": "fixed",
                    }
                ],
            },
        ]
        doc = self._make_template(title="Test Sorting", steps=steps)
        self.assertEqual(doc.steps[0].step_key, "step_1")
        self.assertEqual(doc.steps[1].step_key, "step_3")


class TestProductBuilderSelection(unittest.TestCase):
    """Unit tests for Product Builder Selection DocType."""

    @classmethod
    def setUpClass(cls):
        frappe.set_user("Administrator")

    def setUp(self):
        frappe.db.delete("Product Builder Selection", {"item": "TEST-ITEM-001"})
        frappe.db.delete("Product Builder Template", {"title": "Test Selection Template"})
        frappe.db.commit()

    def tearDown(self):
        frappe.db.delete("Product Builder Selection", {"item": "TEST-ITEM-001"})
        frappe.db.delete("Product Builder Template", {"title": "Test Selection Template"})
        frappe.db.commit()

    def _make_template(self):
        doc = frappe.get_doc(
            {
                "doctype": "Product Builder Template",
                "title": "Test Selection Template",
                "slug": "test-selection-tpl",
                "is_active": 1,
                "steps": [
                    {
                        "step_title": "Choose Size",
                        "step_key": "size",
                        "sort_order": 0,
                        "selection_mode": "single",
                        "options": [
                            {
                                "option_label": "Small",
                                "option_key": "small",
                                "sort_order": 0,
                                "price_type": "fixed",
                                "base_price_delta": 0,
                            },
                            {
                                "option_label": "Large",
                                "option_key": "large",
                                "sort_order": 1,
                                "price_type": "fixed",
                                "base_price_delta": 30000,
                            },
                        ],
                    }
                ],
            }
        )
        doc.insert(ignore_permissions=True)
        return doc

    def test_selection_creation(self):
        """Selection with valid data saves and computes pricing."""
        tpl = self._make_template()
        sel = frappe.get_doc(
            {
                "doctype": "Product Builder Selection",
                "template": tpl.name,
                "item": "TEST-ITEM-001",
                "base_price": 100000,
                "selections": [
                    {
                        "step_key": "size",
                        "step_title": "Choose Size",
                        "option_key": "large",
                        "option_label": "Large",
                        "qty": 1,
                        "price_delta": 30000,
                    }
                ],
            }
        )
        sel.insert(ignore_permissions=True)
        self.assertEqual(sel.options_total, 30000)
        self.assertEqual(sel.final_price, 130000)

    def test_selection_pricing_fixed(self):
        """Fixed price deltas are summed correctly."""
        tpl = self._make_template()
        sel = frappe.get_doc(
            {
                "doctype": "Product Builder Selection",
                "template": tpl.name,
                "item": "TEST-ITEM-001",
                "base_price": 100000,
                "selections": [
                    {
                        "step_key": "size",
                        "step_title": "Choose Size",
                        "option_key": "large",
                        "option_label": "Large",
                        "qty": 1,
                        "price_delta": 30000,
                    },
                    {
                        "step_key": "size",
                        "step_title": "Choose Size",
                        "option_key": "small",
                        "option_label": "Small",
                        "qty": 2,
                        "price_delta": 5000,
                    },
                ],
            }
        )
        sel.insert(ignore_permissions=True)
        self.assertEqual(sel.options_total, 40000)
        self.assertEqual(sel.final_price, 140000)

    def test_selection_summary(self):
        """Summary text is built correctly."""
        tpl = self._make_template()
        sel = frappe.get_doc(
            {
                "doctype": "Product Builder Selection",
                "template": tpl.name,
                "item": "TEST-ITEM-001",
                "base_price": 100000,
                "selections": [
                    {
                        "step_key": "size",
                        "step_title": "Choose Size",
                        "option_key": "large",
                        "option_label": "Large",
                        "qty": 1,
                        "price_delta": 30000,
                    }
                ],
            }
        )
        sel.insert(ignore_permissions=True)
        self.assertIn("Choose Size", sel.summary_text)
        self.assertIn("Large", sel.summary_text)
        self.assertIn("30,000", sel.summary_text)

    def test_selection_denormalize(self):
        """Template title and item name are denormalized."""
        tpl = self._make_template()
        sel = frappe.get_doc(
            {
                "doctype": "Product Builder Selection",
                "template": tpl.name,
                "item": "TEST-ITEM-001",
                "base_price": 100000,
                "selections": [
                    {
                        "step_key": "size",
                        "step_title": "Choose Size",
                        "option_key": "large",
                        "option_label": "Large",
                        "qty": 1,
                        "price_delta": 30000,
                    }
                ],
            }
        )
        sel.insert(ignore_permissions=True)
        self.assertEqual(sel.template_title, "Test Selection Template")


class TestProductBuilderPricing(unittest.TestCase):
    """Unit tests for pricing calculation utility."""

    def test_fixed_pricing(self):
        from restaurant.restaurant.doctype.product_builder_template.product_builder_pricing import (
            compute_builder_price,
        )

        result = compute_builder_price(
            100000,
            [
                {"price_delta": 30000, "price_type": "fixed", "qty": 1},
                {"price_delta": 15000, "price_type": "fixed", "qty": 2},
            ],
        )
        self.assertEqual(result["base_price"], 100000)
        self.assertEqual(result["options_total"], 60000)
        self.assertEqual(result["final_price"], 160000)

    def test_percentage_pricing(self):
        from restaurant.restaurant.doctype.product_builder_template.product_builder_pricing import (
            compute_builder_price,
        )

        result = compute_builder_price(
            100000,
            [{"price_delta": 0, "price_type": "percentage", "price_percentage": 10, "qty": 1}],
        )
        self.assertEqual(result["options_total"], 10000)
        self.assertEqual(result["final_price"], 110000)

    def test_multiply_pricing(self):
        from restaurant.restaurant.doctype.product_builder_template.product_builder_pricing import (
            compute_builder_price,
        )

        result = compute_builder_price(
            100000,
            [{"price_delta": 0.5, "price_type": "multiply", "qty": 1}],
        )
        self.assertEqual(result["options_total"], 50000)
        self.assertEqual(result["final_price"], 150000)

    def test_empty_selections(self):
        from restaurant.restaurant.doctype.product_builder_template.product_builder_pricing import (
            compute_builder_price,
        )

        result = compute_builder_price(100000, [])
        self.assertEqual(result["options_total"], 0)
        self.assertEqual(result["final_price"], 100000)


if __name__ == "__main__":
    unittest.main()
