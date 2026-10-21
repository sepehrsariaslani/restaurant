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
            patch.object(snapp_sync, "fetch_snapp_menu", return_value={"items": [{"product_id": "product-1", "variation_id": "variation-1"}]}),
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

    def test_review_metadata_preserves_approved_parent_and_variation_values(self):
        payload = {"data": [{"type": "category", "id": "category-1", "products": [{
            "id": "product-1",
            "fields": {"title": {"value": "نام فعلی", "pendingValue": "نام پیشنهادی", "status": "PENDING"}},
            "variations": [{
                "id": "variation-1",
                "fields": {
                    "title": {"value": "گزینه فعلی", "pendingValue": "گزینه پیشنهادی", "status": "REJECTED", "statusReason": "عنوان دقیق نیست"},
                    "price": {"value": 150000, "pendingValue": 175000, "status": "PENDING"},
                },
            }],
        }]}]}
        entry = snapp_sync._extract_menu_entries(payload)[0]
        self.assertEqual(entry["productTitle"], "نام فعلی")
        self.assertEqual(entry["variationTitle"], "گزینه فعلی")
        self.assertEqual(entry["price"], 150000)
        self.assertEqual(entry["field_reviews"]["product_title"]["pending_value"], "نام پیشنهادی")
        self.assertEqual(entry["field_reviews"]["variation_title"]["status"], "REJECTED")
        self.assertEqual(entry["field_reviews"]["variation_title"]["reason"], "عنوان دقیق نیست")
        self.assertEqual(entry["field_reviews"]["price"]["pending_value"], 175000)
        legacy = snapp_sync._food_partner_field_review({"price": {"value": 150000, "pendingValue": 175000, "status": "REJECTED"}}, "price")
        self.assertEqual(legacy["pending_value"], 175000)
        self.assertEqual(legacy["status"], "REJECTED")

    def test_pending_fields_and_foreign_variations_fail_before_any_product_patch(self):
        row = {"product_id": "product-1", "variation_id": "variation-1", "product_title": "محصول", "price": 150000}
        cases = [
            ({**row, "field_reviews": {"product_title": {"status": "PENDING"}}}, {"title": "تازه"}),
            ({**row, "field_reviews": {"price": {"status": "PENDING"}}}, {"title": "تازه", "variations": [{"variation_id": "variation-1", "price": 175000}]}),
            ({**row, "description_review_status": "PENDING"}, {"description": "توضیح تازه"}),
            (row, {"title": "تازه", "variations": [{"variation_id": "foreign-variation", "price": 175000}]}),
        ]
        for current, fields in cases:
            with (
                patch.object(snapp_sync, "_require_snapp_menu_settings", return_value={"vendor_id": "vendor-1"}),
                patch.object(snapp_sync, "fetch_snapp_menu", return_value={"items": [current]}),
                patch.object(snapp_sync.requests, "patch") as patch_request,
                self.assertRaises(frappe.ValidationError),
            ):
                snapp_sync.update_snappfood_product("product-1", fields)
            patch_request.assert_not_called()

    def test_rejected_price_can_be_corrected_while_the_title_waits_for_review(self):
        row = {"product_id": "product-1", "price": 150000, "field_reviews": {
            "product_title": {"status": "PENDING", "pending_value": "نام تازه"},
            "price": {"status": "REJECTED", "pending_value": 200000},
        }}
        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value={"vendor_id": "vendor-1"}),
            patch.object(snapp_sync, "fetch_snapp_menu", return_value={"items": [row]}),
            patch.object(snapp_sync, "_food_partner_variation_patch", return_value={"updated_fields": ["price"]}) as mutation,
        ):
            snapp_sync.update_snappfood_product("product-1", {"price": 175000})
        self.assertEqual(mutation.call_args.args, ("product-1", {"price": "175000"}))

    def test_rejected_description_is_editable_even_if_the_proposal_is_retained(self):
        row = {"product_id": "product-1", "description": "متن فعلی", "description_pending_value": "متن ردشده", "description_review_status": "REJECTED"}
        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value={"vendor_id": "vendor-1"}),
            patch.object(snapp_sync, "fetch_snapp_menu", return_value={"items": [row]}),
            patch.object(snapp_sync, "_food_partner_variation_patch", return_value={"updated_fields": ["description"]}) as mutation,
        ):
            snapp_sync.update_snappfood_product("product-1", {"description": "متن اصلاح‌شده"})
        mutation.assert_called_once()

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
            patch.object(snapp_sync, "fetch_snapp_menu_categories", return_value={"items": [{"category_id": "category-1", "title": "گروه آزمایشی", "status": "ACTIVE"}]}),
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

    def test_delete_product_uses_the_partner_variation_delete_contract(self):
        config = {
            "vendor_id": "466275",
            "token": "test-token",
            "menu_api_base_url": "https://apigw.snappfood.ir",
        }
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}

        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=config),
            patch.object(snapp_sync, "fetch_snapp_menu", return_value={"items": [{"product_id": "product-1", "variation_id": "variation-1"}]}),
            patch.object(snapp_sync.requests, "delete", return_value=response) as delete_request,
        ):
            result = snapp_sync.delete_snappfood_product(item_id="variation-1", delete_neighbours=True)

        self.assertEqual(delete_request.call_args.args[0], "https://snappfood.ir/vms/v1.2/product-variation/variation-1")
        self.assertEqual(delete_request.call_args.kwargs["params"], {"deleteNeighbours": "true"})
        self.assertEqual(delete_request.call_args.kwargs["headers"]["authorization"], "Bearer test-token")
        self.assertEqual(result, {"status": "success", "item_id": "variation-1", "delete_neighbours": True})


def run_food_partner_menu_management_contract_check():
    checks = (
        "simple product and variation ID normalization",
        "parent and variation product edits",
        "bulk availability update",
        "new product review request",
        "delete product with neighbor variations",
        "approved and proposed field values stay separate",
        "pending fields and foreign variations cannot be patched",
        "rejected price correction with a pending title",
        "rejected description correction",
    )
    for method_name in (
        "test_simple_product_and_variation_ids_normalize_for_management",
        "test_product_edit_patches_parent_and_each_changed_variation",
        "test_product_availability_uses_the_bulk_variation_status_contract",
        "test_create_product_sends_a_review_request_to_the_partner_api",
        "test_delete_product_uses_the_partner_variation_delete_contract",
        "test_review_metadata_preserves_approved_parent_and_variation_values",
        "test_pending_fields_and_foreign_variations_fail_before_any_product_patch",
        "test_rejected_price_can_be_corrected_while_the_title_waits_for_review",
        "test_rejected_description_is_editable_even_if_the_proposal_is_retained",
    ):
        case = TestFoodPartnerMenuManagement(method_name)
        getattr(case, method_name)()
    return {"status": "success", "checks": checks}
