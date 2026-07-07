from frappe.tests.utils import FrappeTestCase

from restaurant.snapp_sync import _extract_orders, _extract_total_pages, _map_order_type, _map_status, normalize_snapp_order


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
