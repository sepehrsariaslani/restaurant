import json
from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant import snapp_sync


class TestFoodPartnerAddonPublication(FrappeTestCase):
    def test_single_product_menu_id_publishes_modifier_and_persists_topping_mapping(self):
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
            patch.object(snapp_sync, "get_snappfood_product_toppings", return_value={
                "groups": [{
                    "id": "50",
                    "title": "افزودنی‌ها",
                    "options": [{"id": "9001", "title": "پنیر اضافه", "selected": False}],
                }],
            }),
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
        self.assertEqual(post_request.call_args.kwargs["json"], {"toppingIds": [9001]})

        saved_mappings = json.loads(set_value.call_args.args[3])
        self.assertEqual(saved_mappings[0]["lookup_field"], "topping_id")
        self.assertEqual(saved_mappings[0]["lookup_value"], "9001")
        self.assertEqual(saved_mappings[0]["group_name"], modifier_group)
        self.assertEqual(saved_mappings[0]["option_name"], option_name)
        commit.assert_called_once()


def run_addon_publish_contract_check():
    case = TestFoodPartnerAddonPublication(
        "test_single_product_menu_id_publishes_modifier_and_persists_topping_mapping"
    )
    case.test_single_product_menu_id_publishes_modifier_and_persists_topping_mapping()
    return {"status": "success", "check": "modifier add-on publish and topping mapping"}
