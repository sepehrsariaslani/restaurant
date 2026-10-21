"""Availability contracts with fabricated menu rows; no upstream mutations."""

from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from restaurant import api_food_partner, snapp_sync


class TestFoodPartnerMenuAvailability(TestCase):
    config = {"vendor_id": "vendor-1", "token": "test-token"}

    def mutate(self, row=None, payload=None, **kwargs):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = payload or {"success": True}
        menu = {"items": [row or {"status_id": "variation-1", "active": True}]}
        with (
            patch.object(snapp_sync, "_require_snapp_menu_settings", return_value=self.config),
            patch.object(snapp_sync, "fetch_snapp_menu", return_value=menu),
            patch.object(snapp_sync.requests, "post", return_value=response) as request,
        ):
            result = snapp_sync.set_snappfood_menu_item_status("variation-1", **kwargs)
        return result, request

    def test_temporary_unavailability_uses_the_next_shift_flag(self):
        result, request = self.mutate(active=0, disable_until_next_shift="true")
        self.assertEqual(request.call_args.kwargs["json"], {
            "ids": ["variation-1"], "status": "IN_ACTIVE", "disable_until_next_shift": True,
        })
        self.assertTrue(result["disable_until_next_shift"])

    def test_reactivation_clears_temporary_unavailability(self):
        _, request = self.mutate(row={"status_id": "variation-1", "active": True, "disabled_until": "next-shift"}, active=1)
        self.assertEqual(request.call_args.kwargs["json"], {
            "ids": ["variation-1"], "status": "ACTIVE", "disable_until_next_shift": False,
        })

    def test_invalid_status_flags_do_not_send_a_request(self):
        for active, temporary in ((1, True), (0, "unknown"), ("unknown", False)):
            with self.subTest(active=active, temporary=temporary), patch.object(snapp_sync.requests, "post") as request:
                with self.assertRaises(frappe.ValidationError):
                    self.mutate(active=active, disable_until_next_shift=temporary)
                request.assert_not_called()

    def test_foreign_unknown_pending_and_inactive_rows_are_guarded(self):
        rows = [
            {"status_id": "foreign", "active": True},
            {"status_id": "variation-1", "active": None},
            {"status_id": "variation-1", "active": True, "is_virtual": True},
            {"status_id": "variation-1", "active": True, "availability_in_review": True},
            {"status_id": "variation-1", "active": True, "availability_verified": False},
            {"status_id": "variation-1", "active": True, "price": 1000, "field_reviews": {"price": {"status": "PENDING", "pending_value": 2000}}},
            {"status_id": "variation-1", "active": False},
        ]
        for row in rows:
            with self.subTest(row=row), patch.object(snapp_sync.requests, "post") as request:
                with self.assertRaises(frappe.ValidationError):
                    self.mutate(row=row, active=0, disable_until_next_shift=True)
                request.assert_not_called()

    def test_a_parent_id_cannot_change_one_of_its_variations(self):
        with self.assertRaises(frappe.ValidationError):
            self.mutate(row={"product_id": "variation-1", "variation_id": "child-1", "active": True}, active=0)

    def test_rejected_price_is_not_a_pending_price(self):
        _, request = self.mutate(row={"status_id": "variation-1", "active": True, "field_reviews": {"price": {"status": "REJECTED", "pending_value": 2000}}}, active=0)
        request.assert_called_once()

    def test_bulk_item_price_rejection_is_not_success(self):
        with self.assertRaisesRegex(frappe.ValidationError, "محدودیت قیمت"):
            self.mutate(active=1, payload={"data": [{"id": "variation-1", "reason": {"code": "REJECTED_BY_MAX_PRICE"}}]})

    def test_bulk_item_failure_is_not_http_success(self):
        with self.assertRaisesRegex(frappe.ValidationError, "دسترسی"):
            self.mutate(active=1, payload={"data": [{"id": "variation-1", "status": False, "reason": {"message": "دسترسی رد شد"}}]})

    def test_nested_temporary_status_keeps_active_and_disabled_until(self):
        record = {"status": {"active": True, "disabledUntil": "2026-10-22T08:00:00"}}
        self.assertTrue(snapp_sync._food_partner_variation_active(record))
        self.assertEqual(snapp_sync._food_partner_disabled_until(record), "2026-10-22T08:00:00")

    def test_vms_availability_retains_the_boolean_temporary_flag(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"included": [
            {"id": "variation-1", "type": "productVariation", "attributes": {"active": True, "disabledUntil": True, "isReviewed": True, "isNewProduct": False}},
            {"id": "new-1", "type": "productVariation", "attributes": {"active": False, "disabledUntil": False, "isReviewed": False, "isNewProduct": True}},
            {"id": "unknown-1", "type": "productVariation", "attributes": {"active": True}},
            {"id": "category-1", "type": "category", "attributes": {"active": True, "disabledUntil": False}},
        ]}
        with patch.object(snapp_sync.requests, "get", return_value=response) as request:
            result = snapp_sync._food_partner_menu_availability(self.config)
        self.assertEqual(request.call_args.args[0], "https://vendor.snappfood.ir/vms/v2/vendor/menu")
        self.assertEqual(request.call_args.kwargs["params"], {"vendorId": "vendor-1"})
        self.assertTrue(result["variation-1"]["active"])
        self.assertIs(result["variation-1"]["disabled_until"], True)
        self.assertFalse(result["variation-1"]["availability_in_review"])
        self.assertTrue(result["new-1"]["availability_in_review"])
        self.assertNotIn("unknown-1", result)
        self.assertNotIn("category-1", result)

    def test_catalog_enrichment_uses_exact_ids_without_replacing_product_data(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"data": [{"type": "category", "id": "category-1", "products": [
            {"id": "variation-1", "fields": {"title": {"value": "محصول"}, "price": {"value": 25000}}, "status": "IN_ACTIVE"},
            {"id": "unmatched", "fields": {"title": {"value": "محصول"}}, "status": "ACTIVE"},
        ]}]}
        with (
            patch.object(snapp_sync.requests, "get", return_value=response),
            patch.object(snapp_sync, "_food_partner_menu_availability", return_value={"variation-1": {"active": True, "disabled_until": True, "availability_verified": True}}),
            patch.object(snapp_sync, "_has_field", return_value=False),
            patch.object(frappe.db, "commit"),
        ):
            result = snapp_sync.fetch_snapp_menu(self.config, include_availability=True)
        first, second = result["items"]
        self.assertEqual(first["product_title"], "محصول")
        self.assertEqual(first["price"], 25000)
        self.assertIs(first["active"], True)
        self.assertIs(first["disabled_until"], True)
        self.assertIs(first["availability_verified"], True)
        self.assertIs(second["availability_verified"], False)

    def test_failed_availability_read_preserves_the_catalog_and_marks_it_unverified(self):
        response = Mock(status_code=200, ok=True)
        response.json.return_value = {"data": [{"type": "category", "id": "category-1", "products": [
            {"id": "variation-1", "fields": {"title": {"value": "محصول"}}, "status": "ACTIVE"},
        ]}]}
        with (
            patch.object(snapp_sync.requests, "get", return_value=response),
            patch.object(snapp_sync, "_food_partner_menu_availability", side_effect=frappe.ValidationError("دریافت موجودی انجام نشد")),
            patch.object(snapp_sync, "_has_field", return_value=False),
            patch.object(frappe.db, "commit"),
        ):
            result = snapp_sync.fetch_snapp_menu(self.config, include_availability=True)
        self.assertEqual(len(result["items"]), 1)
        self.assertFalse(result["items"][0]["availability_verified"])
        self.assertIn("دریافت موجودی", result["availability_error"])

    def test_native_facade_checks_access_and_forwards_the_flag(self):
        with (
            patch("restaurant.api._ensure_management_access") as access,
            patch.object(snapp_sync, "set_snappfood_menu_item_status", return_value={"status": "success"}) as mutation,
        ):
            api_food_partner.set_snappfood_menu_item_status("variation-1", 0, True)
        access.assert_called_once()
        mutation.assert_called_once_with(item_id="variation-1", active=0, disable_until_next_shift=True)


def run_food_partner_menu_availability_contract_check():
    names = sorted(name for name in dir(TestFoodPartnerMenuAvailability) if name.startswith("test_"))
    for name in names:
        case = TestFoodPartnerMenuAvailability(name)
        getattr(case, name)()
    return {"status": "success", "checks": names, "count": len(names)}
