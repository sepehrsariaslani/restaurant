import unittest

from restaurant.snapp_sync import (
    _build_order_menu_rows,
    _match_local_item_by_title,
    _normalize_sales_invoice_line_value,
    normalize_snapp_order,
)


class TestSnappItemMatching(unittest.TestCase):
    def test_matches_persian_title_after_spacing_and_arabic_character_normalization(self):
        rows = [
            {
                "name": "ITEM-STEAK-MEXICAN",
                "item_name": "کاسه برنجین استیک پلو میکس مکزیکی",
            }
        ]

        result = _match_local_item_by_title(
            "کاسه‌ برنجين  استیک پلو میکس مکزیکی",
            rows,
        )

        self.assertEqual(result["name"], "ITEM-STEAK-MEXICAN")

    def test_does_not_guess_when_normalized_title_is_ambiguous(self):
        rows = [
            {"name": "ITEM-1", "item_name": "کلاب مرغ کاراملی"},
            {"name": "ITEM-2", "item_name": "کلاب مرغ کاراملی"},
        ]

        self.assertIsNone(_match_local_item_by_title("کلاب مرغ کاراملی", rows))

    def test_normalizes_report_food_id_and_order_product_id(self):
        result = normalize_snapp_order(
            {
                "orderId": "884149903",
                "newOrderDate": "2026/09/18 18:22:33",
                "orderProducts": [
                    {
                        "id": 34935662,
                        "orderProductId": 2035835693,
                        "quantity": 2,
                        "title": "کاسه برنجین مرغ پلو میکس مکزیکی",
                        "price": 771400,
                    }
                ],
            },
            amount_multiplier=10,
        )

        self.assertEqual(result["items"][0]["menu_item_id"], "34935662")
        self.assertEqual(result["items"][0]["line_id"], "2035835693")

    def test_empty_numeric_invoice_snapshot_becomes_zero(self):
        self.assertEqual(
            _normalize_sales_invoice_line_value("restaurant_external_packaging_cost", ""),
            0,
        )
        self.assertEqual(
            _normalize_sales_invoice_line_value("restaurant_external_item_title", ""),
            "",
        )

    def test_order_rows_provide_food_partner_id_when_menu_endpoint_is_empty(self):
        rows = _build_order_menu_rows(
            [
                {
                    "orderId": "884149903",
                    "newOrderDate": "2026/09/18 18:22:33",
                    "orderProducts": [
                        {
                            "id": 34935662,
                            "orderProductId": 2035835693,
                            "quantity": 2,
                            "title": " کاسه برنجین مرغ پلو میکس مکزیکی ",
                            "price": 771400,
                        }
                    ],
                }
            ],
            amount_multiplier=10,
        )

        self.assertEqual(rows[0]["external_id"], "34935662")
        self.assertEqual(rows[0]["title"], "کاسه برنجین مرغ پلو میکس مکزیکی")


if __name__ == "__main__":
    unittest.main()
