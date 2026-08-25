import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant.api import (
    close_table_session,
    confirm_table_order,
    create_management_table_order_from_pos,
    create_table_request,
    get_table_detail,
    get_table_overview,
    get_table_session_state,
    move_table_session,
    pay_table_order,
    place_table_order,
    resolve_table_request,
    serve_table_order,
    table_boot,
    update_table_order_item,
)


class TestRestaurantTableFlow(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        suffix = frappe.generate_hash(length=6).upper()
        cls.table_number = f"UT-{suffix}"

        table = frappe.get_doc(
            {
                "doctype": "Restaurant Table",
                "table_number": cls.table_number,
                "status": "empty",
                "is_active": 1,
                "location": "Test Hall",
            }
        )
        table.insert(ignore_permissions=True)
        cls.table_name = table.name
        cls.qr_token = table.qr_code_token

        menu = frappe.get_doc(
            {
                "doctype": "Restaurant Table Menu Item",
                "item_name": f"Unit Pizza {suffix}",
                "category": "Unit Test",
                "price": 123000,
                "is_available": 1,
                "prep_time_mins": 10,
                "description": "test item",
            }
        )
        menu.insert(ignore_permissions=True)
        cls.menu_item_name = menu.name

        frappe.db.commit()

    def setUp(self):
        active_sessions = frappe.get_all(
            "Restaurant Table Session",
            filters={"table": self.table_name, "status": "active"},
            fields=["name"],
            ignore_permissions=True,
        )

        for session in active_sessions:
            orders = frappe.get_all(
                "Restaurant Table Order",
                filters={"session": session.name, "status": ["in", ["pending", "confirmed", "served"]]},
                fields=["name"],
                ignore_permissions=True,
            )
            for order in orders:
                doc = frappe.get_doc("Restaurant Table Order", order.name)
                doc.status = "paid"
                doc.save(ignore_permissions=True)

            reqs = frappe.get_all(
                "Restaurant Table Request",
                filters={"session": session.name, "status": "pending"},
                fields=["name"],
                ignore_permissions=True,
            )
            for req in reqs:
                doc = frappe.get_doc("Restaurant Table Request", req.name)
                doc.status = "done"
                doc.save(ignore_permissions=True)

            sdoc = frappe.get_doc("Restaurant Table Session", session.name)
            sdoc.status = "closed"
            sdoc.save(ignore_permissions=True)

        frappe.db.commit()

    def test_end_to_end_table_flow(self):
        boot = table_boot(self.qr_token)
        self.assertEqual(boot["table"]["name"], self.table_name)
        self.assertTrue(boot["session"]["name"])
        session_name = boot["session"]["name"]

        order_payload = place_table_order(
            self.qr_token,
            [
                {
                    "menu_item": self.menu_item_name,
                    "quantity": 2,
                }
            ],
            note="unit-order",
        )
        self.assertEqual(order_payload["status"], "success")
        self.assertEqual(order_payload["order"]["status"], "pending")
        order_name = order_payload["order"]["name"]

        request_payload = create_table_request(self.qr_token, "waiter", "please come")
        self.assertEqual(request_payload["status"], "success")
        self.assertEqual(request_payload["request"]["status"], "pending")
        request_name = request_payload["request"]["name"]

        state = get_table_session_state(self.qr_token)
        self.assertGreaterEqual(state["counts"]["pending_orders"], 1)
        self.assertGreaterEqual(state["counts"]["pending_requests"], 1)

        confirm = confirm_table_order(order_name)
        self.assertEqual(confirm["order"]["status"], "confirmed")

        served = serve_table_order(order_name)
        self.assertEqual(served["order"]["status"], "served")

        paid = pay_table_order(order_name)
        self.assertEqual(paid["order"]["status"], "paid")

        resolved = resolve_table_request(request_name)
        self.assertEqual(resolved["request"]["status"], "done")

        close_payload = close_table_session(session_name)
        self.assertEqual(close_payload["status"], "success")
        self.assertEqual(close_payload["session"]["status"], "closed")

        table_doc = frappe.get_doc("Restaurant Table", self.table_name)
        self.assertEqual(table_doc.status, "empty")

        detail = get_table_detail(self.table_name)
        self.assertEqual(detail["table"]["name"], self.table_name)

        overview = get_table_overview()
        self.assertTrue(any(row["name"] == self.table_name for row in overview["tables"]))

    def test_table_qr_fields_generated(self):
        table_doc = frappe.get_doc("Restaurant Table", self.table_name)
        self.assertTrue(table_doc.qr_code_token)
        self.assertTrue(table_doc.qr_target_url)
        self.assertTrue(table_doc.qr_code_image)

    def test_close_session_blocked_with_active_order(self):
        boot = table_boot(self.qr_token)
        session_name = boot["session"]["name"]

        order_payload = place_table_order(
            self.qr_token,
            [
                {
                    "menu_item": self.menu_item_name,
                    "quantity": 1,
                }
            ],
            note="unit-open-order",
        )
        self.assertEqual(order_payload["status"], "success")

        with self.assertRaises(frappe.ValidationError):
            close_table_session(session_name)

    def test_update_table_order_item_and_move_session(self):
        boot = table_boot(self.qr_token)
        session_name = boot["session"]["name"]
        order_payload = place_table_order(
            self.qr_token,
            [
                {
                    "menu_item": self.menu_item_name,
                    "quantity": 1,
                }
            ],
            note="unit-edit-order",
        )
        order_name = order_payload["order"]["name"]
        row_name = order_payload["order"]["items"][0]["row_name"]

        updated = update_table_order_item(
            order_name=order_name,
            row_name=row_name,
            quantity_delta=2,
        )
        self.assertEqual(updated["status"], "success")
        edited_order = next((row for row in updated["orders"] if row["name"] == order_name), None)
        self.assertIsNotNone(edited_order)
        self.assertEqual(edited_order["items"][0]["quantity"], 3)

        suffix = frappe.generate_hash(length=6).upper()
        target_table_number = f"UT-MOVE-{suffix}"
        target_table = frappe.get_doc(
            {
                "doctype": "Restaurant Table",
                "table_number": target_table_number,
                "status": "empty",
                "is_active": 1,
                "location": "Test Hall",
            }
        )
        target_table.insert(ignore_permissions=True)

        move_payload = move_table_session(session_name=session_name, target_table=target_table.name)
        self.assertEqual(move_payload["status"], "success")
        self.assertEqual(move_payload["target_table"], target_table.name)

        moved_order = frappe.get_doc("Restaurant Table Order", order_name)
        self.assertEqual(moved_order.table, target_table.name)

        # can still add from POS on moved session table
        pos_order = create_management_table_order_from_pos(
            table_name=target_table.name,
            items=[{"menu_item": self.menu_item_name, "qty": 1}],
            note="pos-add",
        )
        self.assertEqual(pos_order["status"], "success")
        self.assertEqual(pos_order["table"]["name"], target_table.name)
