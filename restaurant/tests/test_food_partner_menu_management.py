from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant import snapp_sync


class TestFoodPartnerMenuManagement(FrappeTestCase):
    def test_simple_product_and_variation_ids_normalize_for_management(self):
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {
            "data": [
                {
                    "type": "category",
                    "id": "category-1",
                    "title": "گروه آزمایشی",
                    "products": [
                        {
                            "id": "product-1",
                            "title": {"value": "محصول ساده"},
                            "description": {"value": "توضیح تأییدشده"},
                            "price": {"value": 150000},
                            "status": "ACTIVE",
                        },
                        {
                            "id": "product-2",
                            "title": {"value": "محصول چندگزینه‌ای"},
                            "variations": [
                                {
                                    "id": "variation-2",
                                    "title": {"value": "گزینه یک"},
                                    "price": {"value": 170000},
                                    "status": "IN_ACTIVE",
                                }
                            ],
                        },
                    ],
                }
            ]
        }

        with (
            patch.object(snapp_sync.requests, "get", return_value=response) as get_request,
            patch.object(snapp_sync, "_has_field", return_value=False),
            patch.object(frappe.db, "commit") as commit,
        ):
            result = snapp_sync.fetch_snapp_menu(settings=config)

        self.assertEqual(get_request.call_args.args[0], "https://apigw.snappfood.ir/vendor-menu/v2/vendor/466275/menu")
        simple, variant = result["items"]
        self.assertEqual(simple["product_id"], "product-1")
        self.assertEqual(simple["variation_id"], "")
        self.assertEqual(simple["status_id"], "product-1")
        self.assertEqual(simple["external_id"], "product-1")
        self.assertTrue(simple["active"])
        self.assertEqual(variant["product_id"], "product-2")
        self.assertEqual(variant["variation_id"], "variation-2")
        self.assertEqual(variant["status_id"], "variation-2")
        self.assertEqual(variant["external_id"], "variation-2")
        self.assertFalse(variant["active"])
        commit.assert_called_once()

    def test_product_edit_patches_parent_and_each_changed_variation(self):
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}

        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync.requests, "patch", side_effect=[response, response]) as patch_request,
        ):
            result = snapp_sync.update_snappfood_product(
                product_id="product-1",
                fields={
                    "title": "نام تازه",
                    "description": "توضیح دقیق",
                    "variations": [{"variation_id": "variation-1", "title": "گزینه تازه", "price": 175000}],
                },
            )

        calls = patch_request.call_args_list
        self.assertTrue(calls[0].args[0].endswith("/product-variation/product-1"))
        self.assertEqual(calls[0].kwargs["json"], {"title": "نام تازه", "description": "توضیح دقیق"})
        self.assertTrue(calls[1].args[0].endswith("/product-variation/variation-1"))
        self.assertEqual(calls[1].kwargs["json"], {"title": "گزینه تازه", "price": "175000"})
        self.assertEqual(result["updated_fields"], ["description", "title"])
        self.assertEqual(result["updated_variation_ids"], ["variation-1"])

    def test_product_availability_uses_the_bulk_variation_status_contract(self):
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}

        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync.requests, "post", return_value=response) as post_request,
        ):
            result = snapp_sync.set_snappfood_menu_item_status(item_id="product-1", active=0)

        self.assertTrue(post_request.call_args.args[0].endswith("/vendor-menu/v4/vendors/466275/variations/status/bulk"))
        self.assertEqual(
            post_request.call_args.kwargs["json"],
            {"ids": ["product-1"], "status": "IN_ACTIVE", "disable_until_next_shift": False},
        )
        self.assertEqual(result, {"status": "success", "item_id": "product-1", "active": False})

    def test_create_product_sends_a_review_request_to_the_partner_api(self):
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}

        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync.requests, "post", return_value=response) as post_request,
        ):
            result = snapp_sync.create_snappfood_product(
                {
                    "title": "محصول تازه",
                    "description": "توضیح واقعی محصول",
                    "category_id": "category-1",
                    "category_title": "گروه آزمایشی",
                    "price": 185000,
                }
            )

        self.assertEqual(post_request.call_args.args[0], "https://apigw.snappfood.ir/vendor-menu/v2/vendors/466275/products")
        self.assertEqual(post_request.call_args.kwargs["files"]["productTitle"], (None, "محصول تازه"))
        self.assertEqual(post_request.call_args.kwargs["files"]["description"], (None, "توضیح واقعی محصول"))
        self.assertEqual(post_request.call_args.kwargs["files"]["menuCategoryId"], (None, "category-1"))
        self.assertEqual(post_request.call_args.kwargs["files"]["price"], (None, "185000"))
        self.assertEqual(post_request.call_args.kwargs["headers"]["vendor-authorization"], "true")
        self.assertEqual(result, {"status": "success", "title": "محصول تازه", "category_id": "category-1"})


def run_food_partner_menu_management_contract_check():
    checks = (
        "simple product and variation ID normalization",
        "parent and variation product edits",
        "bulk availability update",
        "new product review request",
    )
    for method_name in (
        "test_simple_product_and_variation_ids_normalize_for_management",
        "test_product_edit_patches_parent_and_each_changed_variation",
        "test_product_availability_uses_the_bulk_variation_status_contract",
        "test_create_product_sends_a_review_request_to_the_partner_api",
    ):
        case = TestFoodPartnerMenuManagement(method_name)
        getattr(case, method_name)()
    return {"status": "success", "checks": checks}
