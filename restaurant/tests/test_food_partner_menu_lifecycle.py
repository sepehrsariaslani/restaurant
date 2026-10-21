import unittest
from unittest.mock import Mock, patch

import frappe

from restaurant import snapp_sync as sync


class TestFoodPartnerMenuLifecycle(unittest.TestCase):
    cfg = {"vendor_id": "466275", "token": "test-token", "menu_api_base_url": "https://apigw.snappfood.ir"}
    product = {"title": "محصول", "description": "ترکیبات واقعی محصول", "price": 125000}

    def response(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"success": True}
        return response

    def test_category_parser_preserves_state_and_schedules(self):
        rows = sync._extract_menu_categories({"data": [{"id": 1, "title": "گروه", "status": "PENDING", "schedules": {"beginTime": "10:00:00", "endTime": "18:30:00"}}]})
        self.assertEqual(rows[0]["status"], "PENDING")
        self.assertEqual(rows[0]["schedules"], [{"start": "10:00", "stop": "18:30"}])

    def test_business_errors_with_http_200_are_not_empty_menus(self):
        response = self.response()
        response.json.return_value = {"success": False, "message": "دسترسی رد شد"}
        with patch.object(sync.requests, "get", return_value=response), patch.object(frappe.db, "commit") as commit:
            for fetch in (sync.fetch_snapp_menu, sync.fetch_snapp_menu_categories):
                with self.assertRaises(frappe.ValidationError):
                    fetch(self.cfg)
            commit.assert_not_called()

    def test_new_full_time_category_uses_title_without_invented_id(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu_categories", return_value={"items": []}), patch.object(sync.requests, "post", return_value=self.response()) as post:
            sync.create_snappfood_product({**self.product, "create_category": True, "category_title": "صبحانه"})
        fields = post.call_args.kwargs["files"]
        self.assertEqual(fields["menuCategoryTitle"], (None, "صبحانه"))
        self.assertNotIn("menuCategoryId", fields)
        self.assertNotIn("menuCategorySchedules[0][start]", fields)
        self.assertEqual(post.call_args.kwargs["headers"]["backoffice-authorization"], "true")

    def test_new_category_custom_schedule_matches_portal_form(self):
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu_categories", return_value={"items": []}), patch.object(sync.requests, "post", return_value=self.response()) as post:
            sync.create_snappfood_product({**self.product, "create_category": True, "category_title": "صبحانه", "category_schedule": {"start": "08:00", "stop": "11:30"}})
        self.assertEqual(post.call_args.kwargs["files"]["menuCategorySchedules[0][start]"], (None, "08:00:00"))
        self.assertEqual(post.call_args.kwargs["files"]["menuCategorySchedules[0][stop]"], (None, "11:30:00"))

    def test_existing_pending_category_uses_fresh_title_and_schedule(self):
        catalog = {"items": [{"category_id": "cat-1", "title": "عنوان فعلی", "status": "PENDING", "schedules": [{"start": "10:00", "stop": "19:00"}]}]}
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu_categories", return_value=catalog), patch.object(sync.requests, "post", return_value=self.response()) as post:
            sync.create_snappfood_product({**self.product, "category_id": "cat-1", "category_title": "عنوان کهنه"})
        fields = post.call_args.kwargs["files"]
        self.assertNotIn("menuCategoryId", fields)
        self.assertEqual(fields["menuCategoryTitle"], (None, "عنوان فعلی"))
        self.assertEqual(fields["menuCategorySchedules[0][stop]"], (None, "19:00:00"))

    def test_invalid_or_duplicate_category_never_creates_product(self):
        catalog = {"items": [{"category_id": "cat-1", "title": "کیک", "status": "ACTIVE"}]}
        cases = [
            {"create_category": True, "category_title": "كيك"},
            {"create_category": True, "category_title": "صبحانه", "category_schedule": {"start": "12:00", "stop": "08:00"}},
            {"create_category": True, "category_title": "صبحانه", "category_schedule": {"start": "25:00", "stop": "26:00"}},
            {"create_category": True, "category_title": "صبحانه", "category_id": "cat-1"},
            {"category_id": "stale-category"},
            {"category_id": "cat-1", "category_schedule": {"start": "08:00", "stop": "10:00"}},
        ]
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu_categories", return_value=catalog), patch.object(sync.requests, "post") as post:
            for category in cases:
                with self.subTest(category=category), self.assertRaises(frappe.ValidationError):
                    sync.create_snappfood_product({**self.product, **category})
            post.assert_not_called()

    def test_single_option_delete_keeps_siblings_out_of_request(self):
        rows = [{"product_id": "p-1", "variation_id": "v-1"}, {"product_id": "p-1", "variation_id": "v-2"}]
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value={"items": rows}), patch.object(sync.requests, "delete", return_value=self.response()) as delete:
            result = sync.delete_snappfood_product("v-1", delete_neighbours=False, product_id="p-1")
        self.assertEqual(delete.call_args.kwargs["params"], {"deleteNeighbours": "false"})
        self.assertTrue(delete.call_args.args[0].endswith("/product-variation/v-1"))
        self.assertFalse(result["delete_neighbours"])

    def test_foreign_missing_and_last_option_deletes_fail_before_upstream(self):
        rows = [{"product_id": "p-1", "variation_id": "v-1"}, {"product_id": "p-2", "status_id": "p-2"}]
        with patch.object(sync, "_require_snapp_menu_settings", return_value=self.cfg), patch.object(sync, "fetch_snapp_menu", return_value={"items": rows}), patch.object(sync.requests, "delete") as delete:
            for target, parent, whole in [("v-1", "wrong-parent", True), ("missing", "p-1", True), ("v-1", "p-1", False), ("p-2", "p-2", False)]:
                with self.subTest(target=target, parent=parent, whole=whole), self.assertRaises(frappe.ValidationError):
                    sync.delete_snappfood_product(target, delete_neighbours=whole, product_id=parent)
            delete.assert_not_called()


def run_food_partner_menu_lifecycle_contract_check():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestFoodPartnerMenuLifecycle)
    result = unittest.TestResult()
    suite.run(result)
    if result.failures or result.errors:
        raise AssertionError(result.failures + result.errors)
    return {"status": "success", "checks": result.testsRun}
