import unittest
from unittest.mock import patch

from restaurant.snapp_sync import (
    _build_snapp_item_creation_values,
    _build_order_menu_rows,
    _find_mapped_local_item,
    _plan_snappfood_auto_mapping,
    search_snappfood_items,
    _match_local_item_by_title,
    _normalize_sales_invoice_line_value,
    normalize_snapp_order,
)


class TestSnappItemMatching(unittest.TestCase):
    def test_item_search_is_empty_and_side_effect_free_without_query(self):
        self.assertEqual(search_snappfood_items(""), {"status": "success", "items": []})

    def test_auto_mapping_plans_exact_ids_before_exact_names(self):
        plan = _plan_snappfood_auto_mapping(
            [
                {
                    "external_id": "menu-1",
                    "title": "محصول اول",
                    "menu_item_id": "menu-1",
                },
                {
                    "external_id": "menu-2",
                    "title": "محصول دوم",
                    "menu_item_id": "menu-2",
                },
                {
                    "external_id": "menu-3",
                    "title": "محصول سوم",
                    "menu_item_id": "menu-3",
                },
            ],
            [
                {
                    "name": "ITEM-1",
                    "item_name": "محصول اول",
                    "restaurant_external_menu_item_id": "menu-1",
                },
                {
                    "name": "ITEM-2",
                    "item_name": "محصول دوم",
                },
            ],
        )

        self.assertEqual([row["action"] for row in plan], ["already_mapped", "map", "unmatched"])
        self.assertEqual(plan[1]["item_name"], "ITEM-2")

    def test_auto_mapping_can_plan_missing_item_creation_without_orders(self):
        plan = _plan_snappfood_auto_mapping(
            [{"external_id": "menu-1", "title": "محصول جدید", "menu_item_id": "menu-1"}],
            [],
            create_missing=True,
        )

        self.assertEqual(plan[0]["action"], "create")
        self.assertEqual(plan[0]["title"], "محصول جدید")
        self.assertNotIn("Sales Order", plan[0])
        self.assertNotIn("Sales Invoice", plan[0])

    def test_mapping_match_requires_an_external_id_match_not_a_similar_title(self):
        rows = [
            {
                "name": "ITEM-1",
                "item_name": "کره بادام شکلاتی و توت فرنگی",
                "restaurant_external_menu_item_id": "other-id",
            }
        ]

        self.assertIsNone(
            _find_mapped_local_item(
                {
                    "external_id": "36485633",
                    "title": "کلاب بادام شکلاتی و توت فرنگی",
                    "menu_item_id": "36485633",
                },
                rows,
            )
        )

    def test_mapping_match_accepts_any_exact_food_partner_identifier(self):
        rows = [
            {
                "name": "ITEM-1",
                "item_name": "کلاب بادام شکلاتی و توت فرنگی",
                "restaurant_external_menu_item_id": "menu-1",
                "restaurant_external_variation_id": "36485633",
            }
        ]

        result = _find_mapped_local_item(
            {
                "external_id": "36485633",
                "title": "کلاب بادام شکلاتی و توت فرنگی",
                "variation_id": "36485633",
            },
            rows,
        )

        self.assertEqual(result["name"], "ITEM-1")

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

    def test_mapping_item_creation_payload_is_a_native_sales_item_only(self):
        with patch("restaurant.snapp_sync._default_uom", return_value="Nos"):
            values = _build_snapp_item_creation_values(
                {
                    "title": "آیس هانی لته 70 درصد روبوستا، 30 درصد عربیکا",
                    "unit_price": 2660000,
                    "menu_item_id": "34837339",
                },
                item_group="Snapp Imported Items",
                item_code="آیس هانی لته 70 درصد روبوستا، 30 درصد عربیکا",
            )

        self.assertEqual(values["doctype"], "Item")
        self.assertEqual(values["item_group"], "Snapp Imported Items")
        self.assertEqual(values["is_stock_item"], 0)
        self.assertEqual(values["is_sales_item"], 1)
        self.assertNotIn("Sales Order", values)
        self.assertNotIn("Sales Invoice", values)


if __name__ == "__main__":
    unittest.main()
