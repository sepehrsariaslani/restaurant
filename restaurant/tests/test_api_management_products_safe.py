import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

frappe = types.ModuleType('frappe')
frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn) if args == () else args[0]
frappe._ = lambda value: value
frappe.db = types.SimpleNamespace()
sys.modules.setdefault('frappe', frappe)

from restaurant import api_management_products_safe as products_safe


class ManagementProductsSafeTests(unittest.TestCase):
    def test_normalizes_boot_items_for_management_products(self):
        rows = products_safe._management_products_from_boot({
            'items': [{
                'name': 'ITEM-1',
                'title': 'Burger',
                'category_title': 'Food',
                'base_price': 120,
                'out_of_stock': 1,
            }]
        })
        self.assertEqual(rows[0]['name'], 'ITEM-1')
        self.assertEqual(rows[0]['item_code'], 'ITEM-1')
        self.assertEqual(rows[0]['title'], 'Burger')
        self.assertEqual(rows[0]['base_price'], 120)
        self.assertEqual(rows[0]['is_active'], 1)
        self.assertEqual(rows[0]['out_of_stock'], 1)

    def test_filters_boot_fallback_rows(self):
        rows = [
            {
                'name': 'A', 'title': 'Burger', 'item_code': 'BUR-1',
                'category_title': 'Food', 'category_slug': 'food',
                'is_active': 1, 'tags': ['hot'],
            },
            {
                'name': 'B', 'title': 'Cola', 'item_code': 'COLA',
                'category_title': 'Drink', 'category_slug': 'drink',
                'is_active': 0, 'tags': [],
            },
        ]
        self.assertEqual([r['name'] for r in products_safe._filter_management_products(rows, search='bur')], ['A'])
        self.assertEqual([r['name'] for r in products_safe._filter_management_products(rows, category='food')], ['A'])
        self.assertEqual([r['name'] for r in products_safe._filter_management_products(rows, active_only=1)], ['A'])
        self.assertEqual([r['name'] for r in products_safe._filter_management_products(rows, tag='hot')], ['A'])


if __name__ == '__main__':
    unittest.main()
