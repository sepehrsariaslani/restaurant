import json
from unittest import defaultTestLoader
from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant import snapp_sync


class TestFoodPartnerAddonPublication(FrappeTestCase):
    def test_menu_modifier_context_uses_exact_item_identity_and_does_not_guess_by_title(self):
        menu = {"status": "success", "items": [
            {"product_id": "product-1", "title": "محصول اصلی"},
            {"product_id": "product-2", "title": "محصول اصلی"},
        ]}
        local_items = [{"name": "ITEM-BASE", "item_name": "محصول اصلی", "restaurant_external_product_id": "product-1"}]
        with (
            patch.object(snapp_sync, "fetch_snapp_menu", return_value=menu),
            patch.object(snapp_sync, "_get_local_item_rows", return_value=local_items),
        ):
            result = snapp_sync.get_snappfood_menu_products()
        self.assertEqual(result["items"][0]["mapped_item"], {"name": "ITEM-BASE", "item_name": "محصول اصلی"})
        self.assertIsNone(result["items"][1]["mapped_item"])

    def test_json_api_topping_relationships_preserve_ids_prices_and_review_state(self):
        payload = {
            "data": [{
                "type": "topping-group", "id": "50",
                "attributes": {"title": "سس", "minLimit": 0, "maxLimit": 1},
                "relationships": {"toppings": {"data": [{"type": "topping", "id": "9001"}, {"type": "topping", "id": "9002"}]}},
            }],
            "included": [
                {"type": "topping", "id": "9001", "attributes": {"title": "سس اضافه", "price": 15000, "isActiveToppingForProduct": True, "isBeingReviewed": False}},
                {"type": "topping", "id": "9002", "attributes": {"title": "سس تند", "price": 12000, "isActiveToppingForProduct": False, "isBeingReviewed": True}},
            ],
        }
        groups = snapp_sync._food_partner_topping_groups(payload)
        self.assertEqual(groups[0]["id"], "50")
        self.assertEqual(groups[0]["min_limit"], 0)
        self.assertEqual(groups[0]["max_limit"], 1)
        self.assertEqual(groups[0]["options"], [
            {"id": "9001", "title": "سس اضافه", "price": 15000, "selected": True, "being_reviewed": False},
            {"id": "9002", "title": "سس تند", "price": 12000, "selected": False, "being_reviewed": True},
        ])
        del payload["included"][0]["attributes"]["isActiveToppingForProduct"]
        selected = snapp_sync._food_partner_topping_groups(payload, selected_by_membership=True)
        self.assertTrue(selected[0]["options"][0]["selected"])
        self.assertFalse(selected[0]["options"][1]["selected"])

    def test_existing_topping_selection_can_be_cleared_without_editing_shared_group(self):
        context = {"variation_id": "variation-1", "groups": [{"id": "50", "options": [{"id": "9001", "selected": True}]}]}
        config = {"vendor_id": "vendor-1", "token": "test-token"}
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}
        with (
            patch.object(snapp_sync, "get_snappfood_product_toppings", return_value=context),
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync.requests, "post", return_value=response) as post_request,
            patch.object(snapp_sync.requests, "patch") as patch_request,
        ):
            result = snapp_sync.set_snappfood_product_topping_selection("variation-1", "[]")
        self.assertEqual(result["selected_topping_ids"], [])
        self.assertEqual(post_request.call_args.kwargs["json"], {"toppingIds": []})
        self.assertEqual(post_request.call_args.kwargs["params"], {"vendorId": "vendor-1"})
        patch_request.assert_not_called()

    def test_unknown_or_pending_topping_cannot_be_activated(self):
        context = {"variation_id": "variation-1", "groups": [{"id": "50", "options": [{"id": "9001", "selected": False, "being_reviewed": True}]}]}
        with (
            patch.object(snapp_sync, "get_snappfood_product_toppings", return_value=context),
            patch.object(snapp_sync.requests, "post") as post_request,
        ):
            for selected_ids in (["unknown"], ["9001"]):
                with self.assertRaises(frappe.ValidationError):
                    snapp_sync.set_snappfood_product_topping_selection("variation-1", selected_ids)
            post_request.assert_not_called()

    def test_pending_group_and_duplicate_title_are_rejected_before_publication(self):
        group = {"id": "50", "title": "افزودنی‌ها", "options": [{"id": "9001", "being_reviewed": True}]}
        payload = {"variation_id": "variation-1", "parent_item": "ITEM-1", "group_name": "GROUP-1", "title": "افزودنی‌ها", "options": [{"option_name": "OPTION-1", "price": 0}]}
        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value={"vendor_id": "vendor-1"}),
            patch.object(snapp_sync, "_has_field", return_value=True),
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(snapp_sync, "get_snappfood_product_toppings", return_value={"groups": [group]}),
            patch.object(snapp_sync.requests, "patch") as patch_request,
        ):
            with self.assertRaisesRegex(frappe.ValidationError, "این عنوان"):
                snapp_sync.save_snappfood_product_toppings(payload)
            with self.assertRaisesRegex(frappe.ValidationError, "در انتظار بررسی"):
                snapp_sync.save_snappfood_product_toppings({**payload, "partner_group_id": "50"})
            patch_request.assert_not_called()

    def test_single_product_menu_id_publishes_modifier_and_persists_topping_mapping(self, being_reviewed=False):
        item_name = "ITEM-BASE"
        modifier_group = "ADDON-GROUP"
        option_name = "ADDON-CHEESE"
        fieldname = snapp_sync.FOOD_PARTNER_MODIFIER_MAPPINGS_FIELD
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }

        create_response = Mock(status_code=200, ok=True)
        create_response.json.return_value = {"status": "success", "data": {"id": "50"}}
        select_response = Mock(status_code=200, ok=True)
        select_response.json.return_value = {"status": "success"}

        payload = {
            "variation_id": "36485633",
            "parent_item": item_name,
            "group_name": modifier_group,
            "title": "افزودنی‌ها",
            "min_limit": 0,
            "max_limit": 1,
            "options": [
                {"option_name": option_name, "title": "پنیر اضافه", "price": 15000},
            ],
        }

        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync, "_has_field", return_value=True),
            patch.object(snapp_sync, "get_snappfood_modifier_groups", return_value={
                "groups": [{
                    "name": modifier_group,
                    "title": "افزودنی‌های رستوران",
                    "min_select": 0,
                    "max_select": 1,
                    "options": [{"name": option_name, "label": "پنیر اضافه", "option_qty": 1}],
                }],
            }),
            patch.object(snapp_sync, "get_snappfood_product_toppings", side_effect=[{"groups": []}, {
                "groups": [{
                    "id": "50",
                    "title": "افزودنی‌ها",
                    "options": [
                        {"id": "9001", "title": "پنیر اضافه", "selected": False, "being_reviewed": being_reviewed},
                        {"id": "9000", "title": "گزینهٔ قبلی", "selected": True},
                    ],
                }, {
                    "id": "51", "title": "نوشیدنی", "options": [{"id": "9100", "selected": True}],
                }],
            }]),
            patch.object(snapp_sync.requests, "patch", return_value=create_response) as patch_request,
            patch.object(snapp_sync.requests, "post", return_value=select_response) as post_request,
            patch.object(frappe.db, "exists", return_value=True),
            patch.object(frappe.db, "set_value") as set_value,
            patch.object(frappe.db, "commit") as commit,
            patch.object(frappe, "get_all", return_value=[{"name": item_name, fieldname: "[]"}]),
        ):
            result = snapp_sync.save_snappfood_product_toppings(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["variation_id"], "36485633")
        self.assertEqual(result["group_id"], "50")
        self.assertEqual(patch_request.call_args.kwargs["json"]["toppings"][0]["title"], "پنیر اضافه")
        expected_selected = [9100] if being_reviewed else [9100, 9001]
        self.assertEqual(post_request.call_args.kwargs["json"], {"toppingIds": expected_selected})
        self.assertEqual(result["pending_review_topping_ids"], ["9001"] if being_reviewed else [])

        saved_mappings = json.loads(set_value.call_args.args[3])
        self.assertEqual(saved_mappings[0]["lookup_field"], "topping_id")
        self.assertEqual(saved_mappings[0]["lookup_value"], "9001")
        self.assertEqual(saved_mappings[0]["group_name"], modifier_group)
        self.assertEqual(saved_mappings[0]["option_name"], option_name)
        commit.assert_called_once()

    def test_pending_topping_keeps_its_native_mapping_without_being_activated(self):
        self.test_single_product_menu_id_publishes_modifier_and_persists_topping_mapping(being_reviewed=True)


def run_addon_publish_contract_check():
    checks = defaultTestLoader.getTestCaseNames(TestFoodPartnerAddonPublication)
    for name in checks:
        case = TestFoodPartnerAddonPublication(name)
        getattr(case, name)()
    return {"status": "success", "checks": checks}
