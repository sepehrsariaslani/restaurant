import base64
import json
import sys
import types
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

import frappe
from frappe.tests.utils import FrappeTestCase
import restaurant.snapp_sync as snapp_sync

from restaurant.snapp_sync import (
    _extract_menu_entries,
    _extract_orders,
    _extract_total_pages,
    _build_sales_invoice_external_values,
    _create_sales_order,
    _ensure_sales_invoice_for_order,
    _get_schema_status,
    _extract_vendor_id_from_token,
    fetch_snapp_menu,
    _normalize_bearer_token,
    fetch_snapp_orders,
    _map_order_type,
    _map_status,
    normalize_snapp_order,
)


class TestSnappSync(FrappeTestCase):
    def test_normalize_bearer_header_value_before_request(self):
        self.assertEqual(_normalize_bearer_token(" Bearer abc123 "), "abc123")

    def test_extract_vendor_id_from_jwt_claim(self):
        payload = base64.urlsafe_b64encode(
            json.dumps({"vendorId": 466275}).encode("utf-8")
        ).decode("ascii").rstrip("=")

        self.assertEqual(
            _extract_vendor_id_from_token(f"header.{payload}.signature"),
            "466275",
        )

        username_payload = base64.urlsafe_b64encode(
            json.dumps({"username": "vmo466275", "sub": "vmo466275:opaque"}).encode("utf-8")
        ).decode("ascii").rstrip("=")
        self.assertEqual(
            _extract_vendor_id_from_token(f"header.{username_payload}.signature"),
            "466275",
        )

    def test_menu_auth_failure_becomes_user_facing_validation_error(self):
        response = Mock(status_code=401, reason="Unauthorized")
        response.raise_for_status.side_effect = requests.HTTPError(
            "401 Client Error", response=response
        )
        with patch("restaurant.snapp_sync.requests.get", return_value=response):
            with self.assertRaises(frappe.ValidationError) as context:
                fetch_snapp_menu(
                    {
                        "token": "secret",
                        "vendor_id": "466275",
                        "menu_api_base_url": "https://apigw.snappfood.ir",
                    }
                )

        self.assertIn("توکن Food Partner", str(context.exception))

    def test_food_partner_menu_sends_vendor_authorization_header(self):
        response = Mock()
        response.json.return_value = {"data": []}
        with patch("restaurant.snapp_sync.requests.get", return_value=response) as request:
            fetch_snapp_menu(
                {
                    "token": "secret",
                    "vendor_id": "466275",
                    "menu_api_base_url": "https://apigw.snappfood.ir",
                }
            )

        self.assertEqual(request.call_args.kwargs["headers"]["vendor-authorization"], "true")

    def test_extract_orders_from_nested_payload(self):
        payload = {"data": {"items": [{"id": "ord-1"}, {"id": "ord-2"}], "totalPages": 4}}
        orders = _extract_orders(payload)
        total_pages = _extract_total_pages(payload)

        self.assertEqual(len(orders), 2)
        self.assertEqual(total_pages, 4)

    def test_status_and_order_type_mapping(self):
        self.assertEqual(_map_order_type("SALON", ""), "dine_in")
        self.assertEqual(_map_order_type("", "DELIVERY"), "delivery")
        self.assertEqual(_map_status("CONFIRMED", 2), "confirmed")
        self.assertEqual(_map_status("CANCELLED", 2), "cancelled")
        self.assertEqual(_map_status("", 4), "ready")

    def test_normalize_snapp_order_payload(self):
        raw = {
            "id": "order-123",
            "billNumber": "rop-123",
            "orderHistoryState": "CONFIRMED",
            "orderType": "SALON",
            "phoneNumber": "+98 912 123 4567",
            "fullName": "Test Customer",
            "createdAt": "2026-04-04T19:18:54.877",
            "orderItems": [
                {
                    "id": "line-1",
                    "menuItemId": "menu-1",
                    "title": "Chicken Club",
                    "count": 2,
                    "price": 120000,
                }
            ],
        }

        normalized = normalize_snapp_order(raw)

        self.assertEqual(normalized["order_id"], "order-123")
        self.assertEqual(normalized["bill_number"], "rop-123")
        self.assertEqual(normalized["status"], "confirmed")
        self.assertEqual(normalized["order_type"], "dine_in")
        self.assertEqual(normalized["mobile"], "09121234567")
        self.assertEqual(len(normalized["items"]), 1)
        self.assertEqual(normalized["items"][0]["menu_item_id"], "menu-1")

    def test_normalize_food_partner_report_order(self):
        raw = {
            "orderId": "884984812",
            "vendorOrderCode": "V-100",
            "externalStatusCode": 2,
            "externalStatusLabel": "ACCEPTED",
            "orderDate": "2026-09-19 12:00:00",
            "customerName": "گارسون تست",
            "phone": "09120000000",
            "paidPrice": 185000,
            "orderProducts": [
                {
                    "orderProductId": "line-10",
                    "productId": "34788176",
                    "variationId": "34788176-v1",
                    "title": "شیر خرما",
                    "quantity": 1,
                    "price": 185000,
                }
            ],
        }

        normalized = normalize_snapp_order(raw, amount_multiplier=1)

        self.assertEqual(normalized["order_id"], "884984812")
        self.assertEqual(normalized["bill_number"], "V-100")
        self.assertEqual(normalized["status"], "confirmed")
        self.assertEqual(normalized["items"][0]["product_id"], "34788176")
        self.assertEqual(normalized["items"][0]["variation_id"], "34788176-v1")

    def test_extract_food_partner_menu_entries(self):
        payload = {"data": [{"productId": "p1", "title": "شیر خرما", "variations": [{"variationId": "v1", "title": "سایز معمولی"}]}]}
        entries = _extract_menu_entries(payload)

        self.assertEqual({row.get("productId") or row.get("variationId") for row in entries}, {"p1", "v1"})

    def test_invoice_keeps_external_financial_snapshot_for_reconciliation(self):
        values = _build_sales_invoice_external_values(
            {
                "order_id": "884984812",
                "bill_number": "V-100",
                "external_state": "ACCEPTED",
                "payment_method": "ONLINE",
                "external_customer_id": "customer-7",
                "delivery_type": "DELIVERY",
                "factor_number": "F-9",
                "discount": 120,
                "delivery_cost": 300,
                "packaging_cost": 40,
                "tax": 18,
                "service_cost": 25,
                "service_fee": 5,
                "tip": 10,
                "refund_amount": 2,
                "final_price": 1250,
                "paid_price": 1250,
                "discount_amount": 120,
                "raw": {"customerName": "نباید ذخیره شود", "orderId": "884984812"},
            }
        )

        self.assertEqual(values["restaurant_external_order_id"], "884984812")
        self.assertEqual(values["restaurant_external_customer_id"], "customer-7")
        self.assertEqual(values["restaurant_external_delivery_cost"], 300)
        self.assertEqual(values["restaurant_external_final_price"], 1250)
        self.assertNotIn("نباید ذخیره شود", values["restaurant_external_payload_json"])

    def test_food_partner_report_uses_multipart_form_fields(self):
        response = Mock()
        response.json.return_value = {"data": {"items": [{"orderId": "order-1"}], "totalPages": 1}}
        with patch("restaurant.snapp_sync.requests.post", return_value=response) as request:
            fetch_snapp_orders(
                from_datetime="2026-09-19 00:00:00",
                to_datetime="2026-09-19 23:59:59",
                settings={
                    "token": "secret",
                    "vendor_id": "466275",
                    "page_size": 50,
                    "lookback_minutes": 180,
                    "report_url": "https://snappfood.ir/vms/v3/restaurant/report",
                },
            )

        kwargs = request.call_args.kwargs
        self.assertNotIn("data", kwargs)
        self.assertEqual(kwargs["files"]["vendorId"], (None, "466275"))
        self.assertEqual(kwargs["files"]["pageNumber"], (None, "0"))

    def test_food_partner_report_respects_max_page_limit(self):
        response = Mock()
        response.json.return_value = {"data": {"items": [{"orderId": "order-1"}]}}
        with patch("restaurant.snapp_sync.requests.post", return_value=response) as request:
            result = fetch_snapp_orders(
                from_datetime="2026-09-19 00:00:00",
                to_datetime="2026-09-19 23:59:59",
                page_size=1,
                max_pages=2,
                settings={
                    "token": "secret",
                    "vendor_id": "466275",
                    "page_size": 1,
                    "lookback_minutes": 180,
                    "report_url": "https://snappfood.ir/vms/v3/restaurant/report",
                },
            )

        self.assertEqual(result["pages_fetched"], 2)
        self.assertEqual(request.call_count, 2)

    def test_imported_order_uses_native_pos_order_builder(self):
        order_payload = {
            "order_id": "884984812",
            "customer_name": "مشتری تست",
            "mobile": "989120000000",
            "external_customer_id": "customer-7",
            "order_type": "delivery",
            "address": "نشانی تست",
            "note": "یادداشت تست",
            "status": "confirmed",
            "discount_amount": 0,
            "tax": 0,
            "service_cost": 0,
            "service_fee": 0,
            "packaging_cost": 0,
            "tip": 0,
            "items": [{"title": "شیر خرما", "qty": 1, "unit_price": 185000}],
        }
        fake_api = types.ModuleType("restaurant.api")
        fake_api._create_pos_order_payload = Mock(return_value={"order_id": "SO-1"})
        fake_api._set_restaurant_order_status = Mock()
        fake_api._append_sales_order_note = Mock()
        fake_db = SimpleNamespace(
            get_value=lambda doctype, *args, **kwargs: "item-1" if doctype == "Item" else "مشتری تست"
        )
        with patch("restaurant.snapp_sync._ensure_customer", return_value="CUST-7"), patch(
            "restaurant.snapp_sync._get_settings", return_value={"default_customer": ""}
        ), patch("restaurant.snapp_sync._resolve_item_code", return_value="ITEM-1"), patch(
            "restaurant.snapp_sync._apply_sales_order_external_fields"
        ), patch("restaurant.snapp_sync._has_column", return_value=False), patch.object(
            snapp_sync.frappe, "db", fake_db
        ), patch.object(snapp_sync.frappe, "get_all", return_value=[]), patch.dict(
            sys.modules, {"restaurant.api": fake_api}
        ):
            result = _create_sales_order(order_payload)

        self.assertEqual(result, ("SO-1", "created"))
        fake_api._create_pos_order_payload.assert_called_once()
        payload = fake_api._create_pos_order_payload.call_args.args[0]
        self.assertEqual(fake_api._create_pos_order_payload.call_args.kwargs["commit"], False)
        self.assertEqual(payload["order_type"], "delivery")
        self.assertEqual(payload["items"][0]["item_slug"], "item-1")

    def test_imported_order_uses_the_same_management_pos_payload_builder(self):
        order_payload = {
            "order_id": "884984813",
            "customer_name": "مشتری تست",
            "mobile": "09120000000",
            "external_customer_id": "customer-8",
            "order_type": "takeaway",
            "address": "",
            "note": "یادداشت تست",
            "status": "confirmed",
            "discount_amount": 120,
            "tax": 0,
            "service_cost": 0,
            "service_fee": 0,
            "packaging_cost": 0,
            "tip": 0,
            "items": [{"title": "شیر خرما", "qty": 2, "unit_price": 185000}],
        }
        fake_api = types.ModuleType("restaurant.api")
        fake_api._create_pos_order_payload = Mock(return_value={"order_id": "SO-2"})
        fake_api._set_restaurant_order_status = Mock()
        fake_api._append_sales_order_note = Mock()
        fake_db = SimpleNamespace(
            get_value=lambda doctype, *args, **kwargs: "item-2" if doctype == "Item" else "مشتری تست"
        )
        with patch("restaurant.snapp_sync._ensure_customer", return_value="CUST-8"), patch(
            "restaurant.snapp_sync._get_settings", return_value={"default_customer": ""}
        ), patch("restaurant.snapp_sync._resolve_item_code", return_value="ITEM-2"), patch(
            "restaurant.snapp_sync._apply_sales_order_external_fields"
        ), patch("restaurant.snapp_sync._has_column", return_value=False), patch.object(
            snapp_sync.frappe, "db", fake_db
        ), patch.object(snapp_sync.frappe, "get_all", return_value=[]), patch.dict(
            sys.modules, {"restaurant.api": fake_api}
        ):
            result = _create_sales_order(order_payload)

        self.assertEqual(result, ("SO-2", "created"))
        fake_api._create_pos_order_payload.assert_called_once()
        payload = fake_api._create_pos_order_payload.call_args.args[0]
        self.assertEqual(payload["customer_name"], "مشتری تست")
        self.assertEqual(payload["mobile"], "09120000000")
        self.assertEqual(payload["order_type"], "takeaway")
        self.assertEqual(payload["secondary_customer"], "")
        self.assertEqual(payload["items"][0]["item_slug"], "item-2")
        self.assertEqual(payload["totals"]["discountAmount"], 120)
        self.assertFalse(fake_api._create_pos_order_payload.call_args.kwargs["commit"])

    def test_item_mapping_can_resolve_variation_hash_id(self):
        lookup = Mock(side_effect=lambda doctype, filters, *args, **kwargs: (
            "ITEM-HASH" if filters == {"restaurant_external_variation_hash_id": "vh-1"} else None
        ))
        with patch("restaurant.snapp_sync._has_column", return_value=True), patch.object(
            snapp_sync.frappe, "db", SimpleNamespace(get_value=lookup)
        ), patch("restaurant.snapp_sync._tag_item_mapping") as tag_mapping:
            resolved = snapp_sync._resolve_item_code(
                {
                    "variation_hash_id": "vh-1",
                    "title": "شیر خرما",
                }
            )

        self.assertEqual(resolved, "ITEM-HASH")
        tag_mapping.assert_called_once()

    def test_imported_order_uses_native_pos_settlement(self):
        order_payload = {
            "order_id": "884984812",
            "bill_number": "V-100",
            "payment_method": "ONLINE",
            "external_state": "ACCEPTED",
            "external_customer_id": "customer-7",
            "raw": {"orderId": "884984812"},
        }
        fake_api = types.ModuleType("restaurant.api")
        fake_api.settle_pos_order = Mock(return_value={"sales_invoice": "SI-1"})
        fake_db = SimpleNamespace(get_value=lambda *args, **kwargs: None, set_value=Mock())
        with patch("restaurant.snapp_sync._has_column", return_value=True), patch.object(
            snapp_sync.frappe, "db", fake_db
        ), patch.object(snapp_sync.frappe, "get_all", return_value=[]), patch.dict(
            sys.modules, {"restaurant.api": fake_api}
        ):
            result = _ensure_sales_invoice_for_order("SO-1", order_payload)

        self.assertEqual(result["sales_invoice"], "SI-1")
        fake_api.settle_pos_order.assert_called_once()
        self.assertEqual(fake_api.settle_pos_order.call_args.kwargs["order_name"], "SO-1")
        self.assertEqual(fake_api.settle_pos_order.call_args.kwargs["payment"]["method"], "card")
        self.assertEqual(fake_api.settle_pos_order.call_args.kwargs["commit"], False)

    def test_schema_status_exposes_fields_missing_before_migration(self):
        with patch(
            "restaurant.snapp_sync._has_field",
            side_effect=lambda doctype, fieldname: (doctype, fieldname)
            in {
                ("Restaurant Web Settings", "snapp_bearer_token"),
                ("Sales Order", "restaurant_external_order_id"),
            },
        ):
            status = _get_schema_status()

        self.assertFalse(status["ready"])
        self.assertIn("Sales Invoice.restaurant_external_order_id", status["missing"])
        self.assertIn("Item.restaurant_external_product_id", status["missing"])

    def test_sync_skips_before_request_when_native_schema_is_not_migrated(self):
        with patch(
            "restaurant.snapp_sync._get_settings",
            return_value={"enabled": True, "token": "secret", "vendor_id": "466275"},
        ), patch(
            "restaurant.snapp_sync._get_schema_status",
            return_value={"ready": False, "missing": ["Sales Invoice.restaurant_external_order_id"]},
        ), patch("restaurant.snapp_sync.fetch_snapp_orders") as fetch_orders:
            result = snapp_sync.sync_snapp_orders(trigger="test")

        self.assertEqual(result["status"], "skipped")
        self.assertFalse(result["schema_ready"])
        self.assertIn("Sales Invoice.restaurant_external_order_id", result["schema_missing"])
        fetch_orders.assert_not_called()

    def test_scheduler_updates_existing_native_order_status_even_when_only_new(self):
        normalized = {
            "order_id": "884984812",
            "status": "delivered",
            "external_state": "DELIVERED",
        }
        fake_db = SimpleNamespace(
            get_value=Mock(return_value="SO-1"),
            commit=Mock(),
        )
        with patch(
            "restaurant.snapp_sync._get_settings",
            return_value={
                "enabled": True,
                "token": "secret",
                "vendor_id": "466275",
                "page_size": 50,
                "amount_multiplier": 1,
                "auto_sync_invoices": False,
                "write_debug_json": False,
            },
        ), patch(
            "restaurant.snapp_sync._get_schema_status",
            return_value={"ready": True, "missing": []},
        ), patch(
            "restaurant.snapp_sync.fetch_snapp_orders",
            return_value={"orders_count": 1, "pages_fetched": 1, "orders": [{"id": "884984812"}]},
        ), patch(
            "restaurant.snapp_sync.normalize_snapp_order",
            return_value=normalized,
        ), patch(
            "restaurant.snapp_sync._sync_existing_sales_order",
            return_value="updated",
        ) as sync_existing, patch.object(snapp_sync.frappe, "db", fake_db), patch(
            "restaurant.snapp_sync._has_column",
            return_value=True,
        ), patch("restaurant.snapp_sync._set_single_if_exists"):
            result = snapp_sync.sync_snapp_orders(trigger="test", only_new=1, update_status_fields=1)

        sync_existing.assert_called_once_with("SO-1", normalized, reconcile_lines=False)
        self.assertEqual(result["updated_count"], 1)
        self.assertEqual(result["skipped_count"], 0)
