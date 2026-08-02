from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant.api import (
    _create_delivery_note_for_sales_order,
    _management_fetch_web_orders,
    _production_auto_settings,
    _recalculate_line,
    _run_sales_order_auto_flow,
    _set_sales_order_payment_method,
    deliver_invoice_only,
    mark_management_order_paid,
    settle_pos_order,
)


def assert_deliver_invoice_only_runs_production_before_delivery_note():
    calls = []

    def run_auto_flow(
        order_name, trigger="", payment_status=None, force=False, allow_negative_stock=False
    ):
        calls.append(("auto_flow", order_name, trigger, payment_status, force, allow_negative_stock))
        return {"status": "success", "stock_entries": ["SE-1"], "fg_warehouse_map": {"ITEM-1": "Finished Goods Warehouse"}}

    def create_delivery_note(
        order_name, fg_warehouse_map=None, submit_doc=True, allow_negative_stock=False
    ):
        calls.append(("delivery_note", order_name, fg_warehouse_map, submit_doc, allow_negative_stock))
        return "DN-1"

    with patch("restaurant.api._ensure_management_access"), patch(
        "restaurant.api._resolve_sales_order_name", return_value="SO-1"
    ), patch("restaurant.api.frappe.db.exists", return_value=True), patch(
        "restaurant.api._run_sales_order_auto_flow", side_effect=run_auto_flow
    ), patch(
        "restaurant.api._create_delivery_note_for_sales_order", side_effect=create_delivery_note
    ), patch(
        "restaurant.api._set_restaurant_order_status"
    ) as set_status, patch(
        "restaurant.api._append_sales_order_note"
    ) as append_note, patch(
        "restaurant.api.frappe.db.commit"
    ):
        payload = deliver_invoice_only("SO-1")

    assert payload.get("delivery_note") == "DN-1"
    assert calls[0] == ("auto_flow", "SO-1", "manual", None, True, True)
    assert calls[1] == ("delivery_note", "SO-1", {"ITEM-1": "Finished Goods Warehouse"}, True, True)
    set_status.assert_called_once_with("SO-1", "delivered", force=True)
    append_note.assert_called_once()


def assert_delivery_note_uses_finished_goods_warehouse_map():
    appended_rows = []

    class FakeDeliveryNote:
        def __init__(self):
            self.items = []
            self.flags = frappe._dict()
            self.name = "DN-1"

        def append(self, fieldname, payload):
            appended_rows.append(payload)
            self.items.append(payload)

        def insert(self):
            return self

        def submit(self):
            return self

    class FakeSalesOrder:
        company = "Company"
        customer = "Customer"
        items = [
            frappe._dict(
                {
                    "item_code": "ITEM-1",
                    "item_name": "Item 1",
                    "description": "",
                    "qty": 2,
                    "delivered_qty": 0,
                    "warehouse": "Sales Warehouse",
                    "rate": 10,
                    "uom": "Nos",
                    "stock_uom": "Nos",
                    "conversion_factor": 1,
                    "name": "SO-ITEM-1",
                }
            )
        ]

    so_doc = FakeSalesOrder()

    with patch("restaurant.api.frappe.db.exists", side_effect=lambda doctype, *args, **kwargs: doctype != "Delivery Note Item"), patch(
        "restaurant.api.frappe.get_doc", return_value=so_doc
    ), patch(
        "restaurant.api.frappe.new_doc", return_value=FakeDeliveryNote()
    ), patch(
        "restaurant.api.frappe.db.get_single_value", return_value=""
    ):
        _create_delivery_note_for_sales_order(
            "SO-1",
            fg_warehouse_map={"ITEM-1": "Finished Goods Warehouse"},
            submit_doc=True,
        )

    assert appended_rows[0]["warehouse"] == "Finished Goods Warehouse"


def assert_sales_order_payment_method_updates_submitted_order_without_save():
    with patch("restaurant.api._has_column", return_value=True), patch(
        "restaurant.api.frappe.db.set_value"
    ) as set_value, patch("restaurant.api.frappe.get_doc") as get_doc:
        _set_sales_order_payment_method("SO-1", "card")

    set_value.assert_called_once_with(
        "Sales Order",
        "SO-1",
        "restaurant_payment_method",
        "card",
        update_modified=False,
    )
    get_doc.assert_not_called()


def assert_management_web_orders_expose_invoice_and_delivery_state():
    order_row = frappe._dict(
        {
            "name": "SO-1",
            "customer": "Customer",
            "customer_name": "POS Customer",
            "status": "To Bill",
            "docstatus": 1,
            "total": 100,
            "net_total": 100,
            "grand_total": 100,
            "creation": "2026-07-29 10:00:00",
            "transaction_date": "2026-07-29",
            "owner": "cashier@example.com",
            "restaurant_payment_method": "cash",
            "restaurant_payment_status": "",
            "restaurant_payment_provider": "",
            "restaurant_status": "delivered",
            "restaurant_note": "",
            "restaurant_order_type": "takeaway",
            "restaurant_customer_mobile": "",
            "restaurant_table": "",
        }
    )

    def has_column(doctype, fieldname):
        return fieldname in order_row

    def exists(doctype, *args, **kwargs):
        return doctype in {"Sales Order", "DocType", "Sales Order Item", "Sales Invoice Item", "Delivery Note Item"}

    def get_all(doctype, *args, **kwargs):
        if doctype == "Sales Order":
            return [order_row]
        if doctype == "Sales Order Item":
            return []
        if doctype == "Sales Invoice Item":
            return []
        if doctype == "Delivery Note Item":
            return [frappe._dict({"against_sales_order": "SO-1"})]
        return []

    with patch("restaurant.api._has_column", side_effect=has_column), patch(
        "restaurant.api.frappe.db.exists", side_effect=exists
    ), patch("restaurant.api.frappe.get_all", side_effect=get_all):
        rows = _management_fetch_web_orders(date_from="2026-07-29", date_to="2026-07-29")

    assert len(rows) == 1
    assert rows[0]["has_sales_invoice"] is False
    assert rows[0]["delivery_exists"] is True
    assert rows[0]["outstanding_amount"] == 100


def assert_management_web_orders_report_delivered_when_delivery_note_exists():
    order_row = frappe._dict(
        {
            "name": "SO-1",
            "customer": "Customer",
            "customer_name": "POS Customer",
            "status": "To Bill",
            "docstatus": 1,
            "total": 100,
            "net_total": 100,
            "grand_total": 100,
            "creation": "2026-07-29 10:00:00",
            "transaction_date": "2026-07-29",
            "owner": "cashier@example.com",
            "restaurant_payment_method": "cash",
            "restaurant_payment_status": "paid",
            "restaurant_payment_provider": "manual",
            "restaurant_status": "preparing",
            "restaurant_note": "",
            "restaurant_order_type": "takeaway",
            "restaurant_customer_mobile": "",
            "restaurant_table": "",
        }
    )

    def has_column(doctype, fieldname):
        return fieldname in order_row

    def exists(doctype, *args, **kwargs):
        return doctype in {"Sales Order", "DocType", "Sales Order Item", "Sales Invoice Item", "Delivery Note Item"}

    def get_all(doctype, *args, **kwargs):
        if doctype == "Sales Order":
            return [order_row]
        if doctype == "Sales Order Item":
            return []
        if doctype == "Sales Invoice Item":
            return [frappe._dict({"parent": "SI-1", "sales_order": "SO-1"})]
        if doctype == "Sales Invoice":
            return [frappe._dict({"name": "SI-1", "outstanding_amount": 0})]
        if doctype == "Delivery Note Item":
            return [frappe._dict({"against_sales_order": "SO-1"})]
        return []

    with patch("restaurant.api._has_column", side_effect=has_column), patch(
        "restaurant.api.frappe.db.exists", side_effect=exists
    ), patch("restaurant.api.frappe.get_all", side_effect=get_all):
        rows = _management_fetch_web_orders(date_from="2026-07-29", date_to="2026-07-29")

    assert rows[0]["delivery_exists"] is True
    assert rows[0]["status"] == "delivered"


def assert_mark_management_order_paid_creates_sales_invoice_from_sales_order():
    with patch("restaurant.api._ensure_management_access"), patch(
        "restaurant.api._resolve_sales_order_name", return_value="SO-1"
    ), patch("restaurant.api.frappe.db.exists", return_value=True), patch(
        "restaurant.api._manual_management_payment_result",
        return_value={
            "method": "cash",
            "mode_of_payment": "Cash",
            "provider": "manual",
            "status": "paid",
            "reference_no": "REF-1",
            "rrn": "",
            "message": "Payment status updated manually.",
            "provider_payload": {},
        },
    ), patch("restaurant.api.settle_pos_order", return_value={"sales_invoice": "SI-1"}) as settle, patch(
        "restaurant.api._save_management_pos_payment"
    ) as save_payment, patch(
        "restaurant.api._append_sales_order_note"
    ), patch(
        "restaurant.api.frappe.get_doc",
        return_value=frappe._dict({"name": "SO-1", "status": "To Bill", "restaurant_status": "delivered"}),
    ), patch("restaurant.api.frappe.db.commit"):
        payload = mark_management_order_paid("SO-1", reference_no="REF-1")

    settle.assert_called_once()
    assert settle.call_args.kwargs["order_name"] == "SO-1"
    assert settle.call_args.kwargs["payment"]["method"] == "cash"
    save_payment.assert_not_called()
    assert payload["sales_invoice"] == "SI-1"


def assert_required_single_modifier_uses_default_when_missing():
    menu_doc = frappe._dict(
        {
            "doctype": "Item",
            "name": "ITEM-1",
            "item_code": "ITEM-1",
            "item_name": "Item 1",
            "restaurant_base_price": 100,
            "standard_rate": 100,
            "restaurant_slug": "item-1",
            "restaurant_short_desc": "",
            "restaurant_long_desc": "",
            "description": "",
            "restaurant_is_customizable": 0,
            "restaurant_builder_active": 0,
        }
    )
    modifier_group = {
        "group_name": "گریل",
        "title": "گریل",
        "selection_mode": "single",
        "required": 1,
        "min_select": 1,
        "max_select": 1,
        "options": [
            {
                "name": "سرد",
                "label": "سرد",
                "is_default": 1,
                "is_selectable": 1,
                "option_qty": 1,
                "base_qty": 1,
                "min_qty": 1,
                "max_qty": 9,
                "qty_step": 1,
                "action_type": "add_on",
                "modifier_type": "add_on",
                "option_item": "",
                "unit_rate": 0,
                "price_delta": 0,
                "recipe_multiplier": 1,
                "conversion_factor": 1,
            }
        ],
    }

    with patch("restaurant.api._resolve_variant_item_for_customization", return_value=None), patch(
        "restaurant.api._get_default_item_price_rate", return_value=None
    ), patch("restaurant.api._get_bom_ingredient_rows", return_value=[]), patch(
        "restaurant.api._build_modifier_groups",
        return_value=([modifier_group], {"گریل": {"meta": modifier_group, "options": {"سرد": modifier_group["options"][0]}}}, {"گریل": "گریل"}),
    ):
        payload = _recalculate_line(menu_doc, 1, {"selected_modifiers": []})

    assert payload["normalized_customization"]["selected_modifiers"][0]["group"] == "گریل"
    assert payload["normalized_customization"]["selected_modifiers"][0]["option"] == "سرد"


def assert_credit_settlement_creates_non_pos_invoice_without_payment_rows():
    class FakeSalesInvoice:
        def __init__(self):
            self.name = "SI-CREDIT-1"
            self.docstatus = 0
            self.grand_total = 100
            self.total = 100
            self.is_pos = None
            self.update_stock = None
            self.payments = []
            self.flags = frappe._dict()
            self.outstanding_amount = 100

        def as_dict(self):
            return {"name": self.name}

        def append(self, fieldname, payload):
            if fieldname == "payments":
                self.payments.append(payload)

        def insert(self):
            return self

        def submit(self):
            self.docstatus = 1
            return self

    fake_si = FakeSalesInvoice()

    def db_get_value(doctype, *args, **kwargs):
        if doctype == "Sales Invoice Item":
            return None
        if doctype == "Sales Invoice":
            return 100
        return None

    with patch("restaurant.api._ensure_management_access"), patch(
        "restaurant.api._resolve_sales_order_name", return_value="SO-CREDIT-1"
    ), patch("restaurant.api.frappe.db.exists", return_value=True), patch(
        "restaurant.api.frappe.db.get_value", side_effect=db_get_value
    ), patch(
        "restaurant.api.frappe.get_attr", return_value=lambda so_name: fake_si
    ), patch("restaurant.api.frappe.get_all", return_value=[]), patch(
        "restaurant.api._set_sales_order_payment_method"
    ) as set_method, patch(
        "restaurant.api._save_management_pos_payment"
    ) as save_payment, patch("restaurant.api._append_sales_order_note"), patch(
        "restaurant.api.club_apply_settle_effects"
    ), patch("restaurant.api.frappe.db.commit"):
        payload = settle_pos_order(
            "SO-CREDIT-1",
            payment={"method": "credit", "mode_of_payment": "اعتباری"},
        )

    assert payload["sales_invoice"] == "SI-CREDIT-1"
    assert fake_si.is_pos == 0
    assert fake_si.payments == []
    set_method.assert_called_once_with("SO-CREDIT-1", "credit")
    assert save_payment.call_args.args[1]["status"] == "pending"


class TestRestaurantAutoFlow(FrappeTestCase):
    def test_production_auto_settings_are_normalized(self):
        values = {
            "restaurant_auto_flow_enabled": 1,
            "restaurant_auto_flow_on_order_submit": 0,
            "restaurant_auto_flow_on_payment": 1,
            "restaurant_auto_flow_submit_work_order": 1,
            "restaurant_auto_flow_material_transfer": 0,
            "restaurant_auto_flow_manufacture": 1,
            "restaurant_auto_flow_mark_ready": 1,
            "restaurant_auto_flow_mark_delivered_on_paid": 0,
            "restaurant_auto_flow_create_delivery_note": 1,
            "restaurant_auto_flow_submit_stock_entries": 0,
            "restaurant_auto_flow_submit_delivery_note": 1,
        }

        with patch("restaurant.api._ensure_production_auto_setting_fields"), patch(
            "restaurant.api._get_single_setting",
            side_effect=lambda doctype, fieldname, default=None: values.get(fieldname, default),
        ):
            payload = _production_auto_settings()

        self.assertTrue(payload["enabled"])
        self.assertFalse(payload["on_order_submit"])
        self.assertTrue(payload["on_payment"])
        self.assertFalse(payload["material_transfer"])
        self.assertFalse(payload["submit_stock_entries"])
        self.assertTrue(payload["create_delivery_note_on_paid"])
        self.assertFalse(payload["mark_delivered_on_paid"])

    def test_auto_flow_returns_skip_when_order_missing(self):
        with patch("restaurant.api._resolve_sales_order_name", return_value=""):
            payload = _run_sales_order_auto_flow("SO-UNKNOWN", trigger="manual")
        self.assertEqual(payload.get("status"), "skipped")
        self.assertEqual(payload.get("reason"), "order_not_found")

    def test_deliver_invoice_only_runs_production_before_delivery_note(self):
        assert_deliver_invoice_only_runs_production_before_delivery_note()

    def test_delivery_note_uses_finished_goods_warehouse_map(self):
        assert_delivery_note_uses_finished_goods_warehouse_map()

    def test_sales_order_payment_method_updates_submitted_order_without_save(self):
        assert_sales_order_payment_method_updates_submitted_order_without_save()

    def test_management_web_orders_expose_invoice_and_delivery_state(self):
        assert_management_web_orders_expose_invoice_and_delivery_state()

    def test_management_web_orders_report_delivered_when_delivery_note_exists(self):
        assert_management_web_orders_report_delivered_when_delivery_note_exists()

    def test_mark_management_order_paid_creates_sales_invoice_from_sales_order(self):
        assert_mark_management_order_paid_creates_sales_invoice_from_sales_order()

    def test_required_single_modifier_uses_default_when_missing(self):
        assert_required_single_modifier_uses_default_when_missing()

    def test_credit_settlement_creates_non_pos_invoice_without_payment_rows(self):
        assert_credit_settlement_creates_non_pos_invoice_without_payment_rows()
