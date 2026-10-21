import unittest
from unittest.mock import patch

import frappe

from restaurant import api, snapp_sync


class TestFoodPartnerItemCreationPrice(unittest.TestCase):
    def test_menu_items_use_an_existing_count_unit_instead_of_an_arbitrary_weight(self):
        with (
            patch.object(snapp_sync, "_has_column", return_value=False),
            patch.object(frappe.db, "get_value", side_effect=lambda doctype, filters, field: "واحد" if filters.get("name") == "واحد" else None) as lookup,
        ):
            self.assertEqual(snapp_sync._default_uom(), "واحد")
        self.assertTrue(all(call.args[1].get("name") for call in lookup.call_args_list))

    def test_disabled_count_units_are_not_used(self):
        with (
            patch.object(snapp_sync, "_has_column", return_value=True),
            patch.object(frappe.db, "get_value", side_effect=lambda doctype, filters, field: "عدد" if filters.get("name") == "عدد" and filters.get("enabled") == 1 else None) as lookup,
        ):
            self.assertEqual(snapp_sync._default_uom(), "عدد")
        self.assertTrue(all(call.args[1].get("enabled") == 1 for call in lookup.call_args_list))

    def test_missing_count_unit_stops_creation_instead_of_guessing_kilograms(self):
        with patch.object(snapp_sync, "_has_column", return_value=False), patch.object(frappe.db, "get_value", return_value=None):
            with self.assertRaisesRegex(frappe.ValidationError, "واحد شمارشی"):
                snapp_sync._default_uom()

    def test_explicit_toman_price_is_converted_once_to_native_currency(self):
        self.assertEqual(snapp_sync._food_partner_native_item_rate(15000, {"amount_multiplier": 10}), 150000)
        self.assertEqual(snapp_sync._food_partner_native_item_rate(15000, {"amount_multiplier": 1}), 15000)
        self.assertEqual(snapp_sync._food_partner_native_item_rate("۱٬۵۰۰٫۵".replace("٫", "."), {"amount_multiplier": 10}), 15005)

    def test_invalid_menu_prices_are_rejected_before_creation(self):
        for price in (None, "", 0, -1, 999, "NaN", "Infinity", 1_000_000_000):
            with self.subTest(price=price), self.assertRaises(frappe.ValidationError):
                snapp_sync._food_partner_native_item_rate(price, {"amount_multiplier": 10})

    def test_invalid_configured_multipliers_are_rejected(self):
        for multiplier in (None, 0, -1, "NaN", "Infinity", "bad"):
            with self.subTest(multiplier=multiplier), self.assertRaises(frappe.ValidationError):
                snapp_sync._food_partner_native_item_rate(15000, {"amount_multiplier": multiplier})

    def test_browser_creation_converts_explicit_toman_and_preserves_real_description(self):
        with (
            patch.object(api, "_ensure_management_access"),
            patch.object(snapp_sync, "_get_settings", return_value={"amount_multiplier": 10}),
            patch.object(snapp_sync, "create_snappfood_item_from_mapping", return_value={"created": True, "item": "ITEM"}) as create,
        ):
            api.create_snappfood_item_from_mapping(payload={
                "title": "شیر ماسالا", "price_toman": 130000, "price": 1,
                "product_id": "123", "map_product_group": True,
                "description": "شیر، پودر ماسالا",
            })
        self.assertEqual(create.call_args.kwargs["price"], 1300000)
        self.assertEqual(create.call_args.kwargs["description"], "شیر، پودر ماسالا")
        self.assertTrue(create.call_args.kwargs["map_product_group"])

    def test_legacy_native_currency_call_is_not_converted_again(self):
        with (
            patch.object(api, "_ensure_management_access"),
            patch.object(snapp_sync, "_get_settings") as settings,
            patch.object(snapp_sync, "create_snappfood_item_from_mapping", return_value={"item": "ITEM"}) as create,
        ):
            api.create_snappfood_item_from_mapping(payload={"title": "محصول", "price": 150000})
        self.assertEqual(create.call_args.kwargs["price"], 150000)
        settings.assert_not_called()

    def test_invalid_explicit_price_cannot_fall_back_to_a_legacy_price(self):
        with (
            patch.object(api, "_ensure_management_access"),
            patch.object(snapp_sync, "create_snappfood_item_from_mapping") as create,
        ):
            with self.assertRaises(frappe.ValidationError):
                api.create_snappfood_item_from_mapping(payload={"title": "محصول", "price_toman": None, "price": 150000})
        create.assert_not_called()

    def test_automatic_missing_item_creation_converts_the_menu_price(self):
        mapping = {"status": "success", "settings": {"amount_multiplier": 10}, "items": [], "menu": [
            {"external_id": "123", "product_id": "123", "title": "محصول جدید", "price": 15000},
        ]}
        with (
            patch.object(snapp_sync, "get_snappfood_mapping_rows", return_value=mapping),
            patch.object(snapp_sync, "create_snappfood_item_from_mapping", return_value={"created": True, "item": "ITEM"}) as create,
            patch.object(frappe.db, "commit"),
        ):
            result = snapp_sync.auto_map_snappfood_items(create_missing=True)
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(create.call_args.kwargs["price"], 150000)

    def test_native_payload_uses_the_supplied_description_and_native_rate(self):
        with patch.object(snapp_sync, "_default_uom", return_value="Nos"):
            payload = snapp_sync._build_snapp_item_creation_values(
                {"title": "شیر ماسالا", "unit_price": 1300000, "description": "شیر، پودر ماسالا"}, "Imported", "ITEM",
            )
            fallback = snapp_sync._build_snapp_item_creation_values({"title": "محصول", "unit_price": 150000}, "Imported", "OTHER")
        self.assertEqual(payload["standard_rate"], 1300000)
        self.assertEqual(payload["description"], "شیر، پودر ماسالا")
        self.assertEqual(fallback["description"], "محصول")

    def test_strict_import_never_binds_a_same_name_item_awaiting_manual_mapping(self):
        with (
            patch.object(snapp_sync, "_find_mapped_product_group_item", return_value=""),
            patch.object(snapp_sync, "_has_column", return_value=False),
            patch.object(snapp_sync, "_get_settings", return_value={"require_item_mapping": True}),
            patch.object(frappe.db, "get_value", return_value="SAME-NAME-ITEM") as lookup,
            patch.object(snapp_sync, "_tag_item_mapping") as tag,
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "نگاشت نشده"):
                snapp_sync._resolve_item_code({"title": "کرانچی رول", "menu_item_id": "35496661"})
        lookup.assert_not_called()
        tag.assert_not_called()

    def test_non_strict_import_keeps_its_existing_title_fallback(self):
        with (
            patch.object(snapp_sync, "_find_mapped_product_group_item", return_value=""),
            patch.object(snapp_sync, "_has_column", return_value=False),
            patch.object(snapp_sync, "_get_settings", return_value={"require_item_mapping": False}),
            patch.object(frappe.db, "get_value", return_value="SAME-NAME-ITEM"),
            patch.object(snapp_sync, "_tag_item_mapping") as tag,
        ):
            result = snapp_sync._resolve_item_code({"title": "کرانچی رول", "menu_item_id": "35496661"})
        self.assertEqual(result, "SAME-NAME-ITEM")
        tag.assert_called_once()

    def test_saved_external_id_is_resolved_before_any_strict_title_check(self):
        with (
            patch.object(snapp_sync, "_find_mapped_product_group_item", return_value=""),
            patch.object(snapp_sync, "_has_column", side_effect=lambda doctype, field: field == "restaurant_external_menu_item_id"),
            patch.object(snapp_sync, "_get_settings") as settings,
            patch.object(frappe.db, "get_value", return_value="MAPPED-ITEM"),
            patch.object(snapp_sync, "_tag_item_mapping"),
        ):
            result = snapp_sync._resolve_item_code({"title": "شیر ماسالا", "menu_item_id": "34788146"})
        self.assertEqual(result, "MAPPED-ITEM")
        settings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
