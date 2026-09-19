from unittest.mock import Mock, patch

from frappe.tests.utils import FrappeTestCase

from restaurant.snapp_sync import (
    _extract_menu_entries,
    _extract_orders,
    _extract_total_pages,
    _build_sales_invoice_external_values,
    fetch_snapp_orders,
    _map_order_type,
    _map_status,
    normalize_snapp_order,
)


class TestSnappSync(FrappeTestCase):
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
            "phoneNumber": "+98 912 000 0000",
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
        self.assertEqual(normalized["mobile"], "989120000000")
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
