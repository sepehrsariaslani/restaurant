"""Bench-executable smoke checks for the final ERPNext discount hook."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe

from restaurant import api_club


class FakeSalesDocument:
	"""Small document double seeded with a native Pricing Rule's prior result."""

	def __init__(self, **values):
		object.__setattr__(self, "values", values)
		object.__setattr__(self, "doctype", values.get("doctype", "Sales Order"))

	def __setattr__(self, key, value):
		if key in {"values", "doctype"} or "values" not in self.__dict__:
			object.__setattr__(self, key, value)
		else:
			self.values[key] = value

	def get(self, key, default=None):
		return self.values.get(key, default)

	def set(self, key, value):
		self.values[key] = value

	def calculate_taxes_and_totals(self):
		self.values["taxes_recalculated"] = True

	def __getattr__(self, key):
		try:
			return self.values[key]
		except KeyError as exc:
			raise AttributeError(key) from exc


def run_discount_hook_smoke():
	"""Run with `bench --site <site> execute restaurant.tests.test_customer_discount_hook.run_discount_hook_smoke`."""
	doc = FakeSalesDocument(
		doctype="Sales Order",
		customer="TEST-CUSTOMER",
		net_total=1000,
		discount_amount=100,
		additional_discount_percentage=10,
		restaurant_discount_policy_applied=1,
	)
	coach_terms = {
		"coach": "TEST-COACH",
		"discount": 50,
		"discount_percent": 5,
		"commission": 50,
		"commission_percent": 5,
	}

	with (
		patch.object(api_club, "_club_ensure_ops_ready"),
		patch.object(api_club.frappe.db, "exists", return_value=True),
		patch.object(api_club, "_club_copy_sales_order_discount_policy_to_invoice", return_value=False),
		patch.object(api_club, "_club_strip_managed_pricing_rules", return_value=False),
		patch.object(api_club, "_club_customer_group_discount_percent", return_value=10),
		patch.object(api_club, "_club_partner_order_terms", return_value=coach_terms),
		patch.object(api_club, "_club_native_coupon_amount", return_value=120),
		patch.object(api_club, "_club_assign_referral_code", return_value="COACH123"),
		patch.object(api_club, "_has_column", return_value=True),
		patch.object(api_club.frappe.db, "get_value", return_value=""),
	):
		api_club.apply_customer_discount_policy(doc)

	assert doc.get("discount_amount") == 120, repr(doc.values)
	assert doc.get("additional_discount_percentage") == 0
	assert doc.get("restaurant_discount_source") == "کد تخفیف"
	assert doc.get("restaurant_coach_commission_amount") == 44
	assert doc.get("restaurant_coach_customer") == "TEST-COACH"
	assert doc.get("taxes_recalculated") is True

	invoice = FakeSalesDocument(
		doctype="Sales Invoice",
		customer="TEST-CUSTOMER",
		restaurant_discount_policy_applied=1,
	)
	with (
		patch.object(api_club, "_club_ensure_ops_ready"),
		patch.object(api_club.frappe.db, "exists", return_value=True),
		patch.object(api_club, "_club_copy_sales_order_discount_policy_to_invoice", return_value=True) as copy_policy,
	):
		api_club.apply_customer_discount_policy(invoice)
	copy_policy.assert_called_once_with(invoice)
	return {"status": "ok", "discount_amount": 120, "coach_commission": 44, "invoice_copy": True}


def run_settlement_gate_smoke():
	"""A paid partial invoice must not release the full Sales Order commission."""
	db = api_club.frappe.db
	with (
		patch.object(db, "exists", return_value=True),
		patch.object(db, "has_column", return_value=True),
		patch.object(db, "get_value", return_value=50),
		patch.object(db, "sql", return_value=[{"outstanding_amount": 0}]),
		patch("restaurant.api._get_sales_order_payment_status", return_value=""),
	):
		assert api_club.coach_payment_settled("SO-TEST") is False
	with (
		patch.object(db, "exists", return_value=True),
		patch.object(db, "has_column", return_value=True),
		patch.object(db, "get_value", return_value=100),
		patch.object(db, "sql", return_value=[{"outstanding_amount": 0}]),
		patch("restaurant.api._get_sales_order_payment_status", return_value=""),
	):
		assert api_club.coach_payment_settled("SO-TEST") is True
	return {"status": "ok", "partial_paid_order_blocked": True, "fully_billed_and_paid_released": True}


def run_sales_invoice_discount_policy_dict_smoke():
	"""A normal dict returned by frappe.get_all must be accepted for invoice rows."""
	doc = FakeSalesDocument(
		doctype="Sales Invoice",
		name="SINV-TEST",
		items=[],
	)
	policy = SimpleNamespace(
		restaurant_discount_policy_applied=1,
		net_total=1000,
		discount_amount=100,
		restaurant_group_discount_amount=100,
		restaurant_coach_discount_amount=0,
		restaurant_coach_commission_amount=0,
		restaurant_coach_customer="",
		restaurant_discount_source="گروه مشتری",
	)

	with (
		patch.object(api_club.frappe.db, "exists", return_value=True),
		patch.object(api_club.frappe.db, "has_column", return_value=True),
		patch.object(
			api_club.frappe,
			"get_all",
			return_value=[{"sales_order": "SO-TEST", "net_amount": 1000, "amount": 1000}],
		),
		patch.object(api_club.frappe.db, "get_value", return_value=policy),
		patch.object(api_club, "_has_column", return_value=True),
	):
		assert api_club._club_copy_sales_order_discount_policy_to_invoice(doc) is True

	assert doc.get("discount_amount") == 100, repr(doc.values)
	assert doc.get("restaurant_discount_policy_applied") == 1
	return {"status": "ok", "discount_amount": 100}


def run_pos_customer_group_discount_smoke():
	"""The generic POS customer must not receive a loyalty/customer-group discount."""
	with (
		patch.object(api_club, "_has_column", return_value=True),
		patch.object(
			api_club.frappe.db,
			"get_value",
			side_effect=lambda doctype, name, fieldname: "Government" if doctype == "Customer" else 10,
		) as get_value,
	):
		assert api_club._club_customer_group_discount_percent("POS Customer") == 0

	get_value.assert_not_called()

	with (
		patch.object(api_club, "_has_column", return_value=True),
		patch.object(
			api_club.frappe.db,
			"get_value",
			side_effect=lambda doctype, name, fieldname: "Government" if doctype == "Customer" else 10,
		),
	):
		assert api_club._club_customer_group_discount_percent("CUST-TEST") == 10

	return {"status": "ok", "pos_customer_discount_percent": 0}
