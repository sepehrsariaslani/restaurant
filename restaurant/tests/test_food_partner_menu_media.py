import unittest
from unittest.mock import Mock, patch

import frappe

from restaurant import snapp_sync as sync


class TestFoodPartnerMenuMedia(unittest.TestCase):
    cfg = {"vendor_id": "466275", "token": "test-token", "menu_api_base_url": "https://apigw.snappfood.ir"}
    menu = {"items": [{"product_id": "100", "variation_id": "101", "status_id": "101", "variation_title": "کوچک"}]}

    def response(self, payload):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = payload
        return response

    def image_response(self, **overrides):
        image = {"id": None, "changeId": 42, "url": "https://cdn.snappfood.ir/photo.jpg", "userType": "VENDOR", "status": "REJECTED", "rejectReason": {"title": "عکس نامناسب"}, **overrides}
        return self.response({"data": [{"productVariationId": 101, "images": [image]}, {"productVariationId": 999, "images": [{**image, "changeId": 99}]}]})

    def test_add_variation_uses_current_parent_contract_and_toman(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "post", return_value=self.response({"success": True})) as post:
            result = sync.add_snappfood_product_variations("100", [{"title": " بزرگ ", "price": "۲۵۰٬۰۰۰"}])
        self.assertEqual(post.call_args.args[0], "https://apigw.snappfood.ir/vendor-menu/v1/vendor/product/product-variation/add-variation")
        self.assertEqual(post.call_args.kwargs["json"], {"parentId": 100, "parentIdType": "productVariation", "variations": [{"title": "بزرگ", "price": "250000"}]})
        self.assertEqual(result["submitted_count"], 1)

    def test_duplicate_foreign_and_invalid_variations_never_post(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "post") as post:
            for parent, variations in [("999", [{"title": "بزرگ", "price": 10000}]), ("100", [{"title": "کوچک", "price": 10000}]), ("100", [{"title": "بزرگ", "price": 10}]), ("100", [{"title": "بزرگ", "price": 10000}, {"title": "بزرگ", "price": 11000}])]:
                with self.assertRaises(frappe.ValidationError):
                    sync.add_snappfood_product_variations(parent, variations)
            post.assert_not_called()

    def test_image_read_filters_other_products_and_preserves_review(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.image_response()) as get:
            result = sync.get_snappfood_product_images("101")
        self.assertTrue(get.call_args.args[0].endswith("/vendor-menu/v1/vendor/466275/product/images"))
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0]["key"], "change:42")
        self.assertEqual(result["images"][0]["reason"], "عکس نامناسب")
        self.assertEqual(result["images"][0]["status"], "REJECTED")

    def test_main_product_image_is_owned_even_with_separate_variations(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.response({"data": [{"productVariationId": 100, "images": [{"id": 1, "userType": "SUPPORT", "status": "CONFIRMED"}]}]})):
            result = sync.get_snappfood_product_images("100")
        self.assertEqual(len(result["images"]), 1)
        self.assertFalse(result["images"][0]["can_delete"])

    def test_pending_image_blocks_upload_before_mutation(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.image_response(status="NOT_REVIEWED")), patch.object(sync.requests, "post") as post:
            with self.assertRaisesRegex(frappe.ValidationError, "انتظار بررسی"):
                sync.upload_snappfood_product_image("101", "data:image/jpeg;base64,YWJj")
            post.assert_not_called()

    def test_upload_uses_multipart_image_and_exact_target(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.image_response()), patch.object(sync.requests, "post", return_value=self.response({"success": True})) as post:
            sync.upload_snappfood_product_image("101", "data:image/jpeg;base64,YWJj")
        self.assertTrue(post.call_args.args[0].endswith("/vendor-menu/v2/vendor/product/product-variation/image"))
        self.assertEqual(post.call_args.kwargs["files"], {"parentId": (None, "101"), "parentIdType": (None, "productVariation"), "image": ("uploadedImage.jpg", b"abc", "image/jpeg")})
        self.assertEqual(post.call_args.kwargs["headers"]["vendor-authorization"], "true")

    def test_delete_change_and_approved_image_use_their_own_routes(self):
        for overrides, key, ending in [({}, "change:42", "/vendor-menu/v1/vendor/product/image/42"), ({"changeId": None, "id": 7, "status": "CONFIRMED"}, "image:7", "/vms/v1/product/101/image/7")]:
            with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.image_response(**overrides)), patch.object(sync.requests, "delete", return_value=self.response({"success": True})) as delete:
                sync.delete_snappfood_product_image("101", key)
            self.assertTrue(delete.call_args.args[0].endswith(ending))

    def test_foreign_images_and_support_images_cannot_be_deleted(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "get", return_value=self.image_response(userType="SUPPORT")), patch.object(sync.requests, "delete") as delete:
            for key in ["change:42", "change:99", "change:untrusted"]:
                with self.assertRaises(frappe.ValidationError):
                    sync.delete_snappfood_product_image("101", key)
            delete.assert_not_called()

    def test_invalid_image_or_foreign_target_cannot_be_uploaded(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "post") as post:
            for target, image in [("101", "data:image/png;base64,YWJj"), ("999", "data:image/jpeg;base64,YWJj"), ("101", "data:image/jpeg;base64," + "a" * 3_000_001)]:
                with self.assertRaises(frappe.ValidationError):
                    sync.upload_snappfood_product_image(target, image)
            post.assert_not_called()

    def test_provider_business_failure_does_not_report_success(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value=self.menu), patch.object(sync.requests, "post", return_value=self.response({"success": False, "message": "رد شد"})):
            with self.assertRaises(frappe.ValidationError):
                sync.add_snappfood_product_variations("100", [{"title": "بزرگ", "price": 10000}])


def run_food_partner_menu_media_contract_check():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestFoodPartnerMenuMedia)
    result = unittest.TestResult()
    suite.run(result)
    if result.failures or result.errors:
        raise AssertionError(result.failures + result.errors)
    return {"status": "success", "checks": result.testsRun}
