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
utils = types.ModuleType('frappe.utils')
utils.cint = lambda value: int(value or 0)
utils.flt = lambda value: float(value or 0)
utils.getdate = lambda value=None: value
sys.modules.setdefault('frappe.utils', utils)

from restaurant import api_pos_reliability as reliability


class PosReliabilityHelperTests(unittest.TestCase):
    def test_normalizes_client_order_key(self):
        self.assertEqual(reliability._normalize_client_order_key(' pos-abc_123 '), 'pos-abc_123')
        self.assertEqual(reliability._normalize_client_order_key('bad key/with spaces'), 'bad-key-with-spaces')
        self.assertEqual(reliability._normalize_client_order_key(''), '')

    def test_normalizes_atomic_quick_edit_payload(self):
        payload = reliability._normalize_atomic_quick_edit_payload(
            {
                'item_name': ' ITEM-1 ',
                'price_list_rate': '125000',
                'restaurant_short_desc': ' کوتاه ',
                'restaurant_long_desc': ' بلند ',
                'item_group': ' Food ',
                'restaurant_out_of_stock': 1,
                'restaurant_out_of_stock_until': '2026-08-30',
                'dangerous_field': 'ignored',
            }
        )
        self.assertEqual(payload['item_name'], 'ITEM-1')
        self.assertEqual(payload['price_list_rate'], 125000.0)
        self.assertEqual(payload['restaurant_short_desc'], 'کوتاه')
        self.assertEqual(payload['restaurant_long_desc'], 'بلند')
        self.assertEqual(payload['item_group'], 'Food')
        self.assertEqual(payload['restaurant_out_of_stock'], 1)
        self.assertEqual(payload['restaurant_out_of_stock_until'], '2026-08-30')
        self.assertNotIn('dangerous_field', payload)

        available = reliability._normalize_atomic_quick_edit_payload(
            {
                'item_name': 'ITEM-1',
                'price_list_rate': 0,
                'restaurant_out_of_stock': 0,
                'restaurant_out_of_stock_until': '2026-08-30',
            }
        )
        self.assertEqual(available['restaurant_out_of_stock_until'], '')

    def test_merges_unavailable_items_without_duplicates(self):
        base = [{'name': 'ITEM-A', 'title': 'A', 'out_of_stock': 0}]
        extra = [
            {'name': 'ITEM-A', 'title': 'A newer', 'out_of_stock': 1},
            {'name': 'ITEM-B', 'title': 'B', 'out_of_stock': 1},
        ]
        merged = reliability._merge_pos_items(base, extra)
        self.assertEqual([row['name'] for row in merged], ['ITEM-A', 'ITEM-B'])
        self.assertEqual(merged[0]['title'], 'A newer')
        self.assertEqual(merged[1]['out_of_stock'], 1)

    def test_extracts_order_id_from_legacy_result(self):
        self.assertEqual(reliability._extract_order_id({'order_id': 'SO-1'}), 'SO-1')
        self.assertEqual(reliability._extract_order_id({'name': 'SO-2'}), 'SO-2')
        self.assertEqual(reliability._extract_order_id(None), '')

    def test_detects_expired_out_of_stock_window(self):
        self.assertTrue(reliability._should_clear_expired_out_of_stock(1, '2026-08-22', '2026-08-23'))
        self.assertFalse(reliability._should_clear_expired_out_of_stock(1, '2026-08-23', '2026-08-23'))
        self.assertFalse(reliability._should_clear_expired_out_of_stock(1, '', '2026-08-23'))
        self.assertFalse(reliability._should_clear_expired_out_of_stock(0, '2026-08-22', '2026-08-23'))


if __name__ == '__main__':
    unittest.main()
