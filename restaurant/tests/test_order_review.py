"""Regression tests for the Food Partner Sales Order review endpoint."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe

from restaurant import api_order_review
from restaurant import api as restaurant_api
from restaurant.order_review import (
	ORDER_REVIEW_APPROVED,
	ORDER_REVIEW_FIELD,
	ORDER_REVIEW_PENDING,
)


class FakeReviewDB:
	"""Small database double that keeps the review transaction observable."""

	def __init__(self, review_status=ORDER_REVIEW_PENDING):
		self.review_status = review_status
		self.sales_invoice_name = ""
		self.commits = 0
		self.rollbacks = 0
		self.updates = []

	def exists(self, doctype, name):
		return doctype == "Sales Order" and name == "SO-1"

	def has_column(self, doctype, fieldname):
		return doctype == "Sales Order" or fieldname == ORDER_REVIEW_FIELD

	def sql(self, query, values=None):
		return [(values,)]

	def get_value(self, doctype, name, fieldname):
		if doctype == "Sales Invoice Item":
			return self.sales_invoice_name
		if fieldname == ORDER_REVIEW_FIELD:
			return self.review_status
		return None

	def set_value(self, doctype, name, fieldname, value=None, **kwargs):
		updates = fieldname if isinstance(fieldname, dict) else {fieldname: value}
		self.updates.append(updates)
		if ORDER_REVIEW_FIELD in updates:
			self.review_status = updates[ORDER_REVIEW_FIELD]

	def commit(self):
		self.commits += 1

	def rollback(self):
		self.rollbacks += 1
		self.review_status = ORDER_REVIEW_PENDING

	def set_single_value(self, *args, **kwargs):
		return None


class ReviewOrderDouble:
	def __init__(self, submit_error=None, docstatus=0):
		self.docstatus = docstatus
		self.flags = SimpleNamespace(ignore_permissions=False)
		self.submit_error = submit_error
		self.submit_calls = 0

	def get(self, fieldname):
		return "snapp_food" if fieldname == "restaurant_external_source" else ""

	def submit(self):
		self.submit_calls += 1
		if self.submit_error:
			raise self.submit_error
		self.docstatus = 1


class OrderReviewTests(TestCase):
	def make_context(self, review_status=ORDER_REVIEW_PENDING, order=None):
		database = FakeReviewDB(review_status)
		order = order or ReviewOrderDouble()
		patches = [
			patch.object(api_order_review.frappe, "db", database),
			patch.object(api_order_review.frappe, "get_doc", return_value=order),
			patch.object(api_order_review.frappe, "session", SimpleNamespace(user="Administrator")),
			patch.object(restaurant_api, "_ensure_management_access"),
			patch.object(restaurant_api, "_set_restaurant_order_status"),
			patch.object(restaurant_api, "_append_sales_order_note"),
			patch.object(api_order_review.frappe, "log_error"),
		]
		self.addCleanup(lambda: [item.stop() for item in reversed(patches)])
		for item in patches:
			item.start()
		return database, order

	def test_approve_pending_order_submits_and_returns_approved(self):
		database, order = self.make_context()

		result = api_order_review.review_management_order("SO-1", "approve")

		self.assertEqual(result["status"], "success")
		self.assertEqual(result["review_status"], ORDER_REVIEW_APPROVED)
		self.assertEqual(result["order_name"], "SO-1")
		self.assertEqual(order.submit_calls, 1)
		self.assertEqual(database.commits, 1)

	def test_repeating_same_approval_is_successful_and_idempotent(self):
		database, order = self.make_context(review_status=ORDER_REVIEW_APPROVED)
		database.sales_invoice_name = "ACC-SINV-0001"

		result = api_order_review.review_management_order("SO-1", "approve")

		self.assertEqual(result["status"], "success")
		self.assertTrue(result["idempotent"])
		self.assertEqual(result["review_status"], ORDER_REVIEW_APPROVED)
		self.assertEqual(result["sales_invoice"], "ACC-SINV-0001")
		self.assertEqual(order.submit_calls, 0)
		self.assertEqual(database.commits, 0)

	def test_review_failure_rolls_back_and_logs_stage(self):
		database, order = self.make_context(order=ReviewOrderDouble(frappe.ValidationError("submit failed")))
		log_error = api_order_review.frappe.log_error

		with self.assertRaises(frappe.ValidationError):
			api_order_review.review_management_order("SO-1", "approve")

		self.assertEqual(database.review_status, ORDER_REVIEW_PENDING)
		self.assertEqual(database.rollbacks, 1)
		log_error.assert_called_once()
		self.assertIn("Food Partner order review failed at ثبت سفارش فروش", log_error.call_args.args)
