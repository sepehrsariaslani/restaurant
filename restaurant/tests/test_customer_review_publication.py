"""Focused contracts for public product-review publication and moderation."""

import ast
import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class FakeDocument(dict):
	def __getattr__(self, name):
		return self.get(name)

	def __setattr__(self, name, value):
		self[name] = value

	def insert(self, **kwargs):
		self.insert_kwargs = kwargs
		self.name = self.name or f"DOC-{len(self)}"

	def save(self, **kwargs):
		self.save_kwargs = kwargs


class CustomerReviewPublicationTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe = types.ModuleType("frappe")
		frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
		frappe._ = lambda value: value
		frappe.PermissionError = PermissionError

		def throw(message, error=None):
			raise (error or ValueError)(message)

		frappe.throw = throw
		utils = types.ModuleType("frappe.utils")
		utils.cint = lambda value=0: int(float(value or 0))
		utils.flt = lambda value=0, precision=None: float(value or 0)
		utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
		utils.now_datetime = datetime.now

		club = types.ModuleType("restaurant.api_club")
		cls.originals = {
			name: sys.modules.get(name)
			for name in ("frappe", "frappe.utils", "restaurant.api_club")
		}
		package = sys.modules.get("restaurant")
		cls.package = package
		cls.original_package_club = getattr(package, "api_club", None) if package else None
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils
		sys.modules["restaurant.api_club"] = club
		if package:
			package.api_club = club

		target = ROOT / "restaurant" / "api_survey.py"
		spec = importlib.util.spec_from_file_location("restaurant.api_survey_publication_test", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)

	@classmethod
	def tearDownClass(cls):
		for name, value in cls.originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value
		if cls.package:
			if cls.original_package_club is None:
				delattr(cls.package, "api_club")
			else:
				cls.package.api_club = cls.original_package_club

	def setUp(self):
		self.module = self.__class__.module
		self.frappe = sys.modules["frappe"]
		self.saved_reviews = []
		self.saved_responses = []
		now = datetime(2026, 9, 28, 12, 0)
		self.invitation = FakeDocument(
			name="RSI-1",
			order_key="Sales Order:SO-1",
			order_code="SO-1",
			submitted_at=None,
			status="در انتظار ارسال",
			due_at=now - timedelta(minutes=1),
			expires_at=now + timedelta(days=2),
			sales_order="SO-1",
			table_order=None,
			customer="CUST-1",
			customer_name="مشتری اصلی",
			mobile="09120000001",
		)
		self.item = {
			"order_item": "SOI-1",
			"item": "FOOD-1",
			"item_slug": "food-1",
			"item_group": "Meals",
		}
		self.module._invitation_by_token = lambda token: self.invitation if token == "private-token" else None
		self.module._load_order = lambda invitation: {"order_code": "SO-1", "items": [self.item]}
		self.module.now_datetime = lambda: now
		self.module.api_club._club_parse_payload = lambda value: value or {}
		self.module.api_club._club_club_settings = lambda: {
			"survey_alert_threshold": 1,
			"survey_alert_users": [],
		}

		class Database:
			def get_value(self, doctype, filters, fieldname, **kwargs):
				return None

			def commit(self):
				pass

		self.frappe.db = Database()
		self.frappe.get_all = lambda *args, **kwargs: []

		def new_doc(doctype):
			doc = FakeDocument(name=None)
			if doctype == self.module.RESPONSE:
				self.saved_responses.append(doc)
			else:
				self.saved_reviews.append(doc)
			return doc

		self.frappe.new_doc = new_doc

	def test_new_product_review_is_published_immediately(self):
		self.module.submit_public_survey({
			"token": "private-token",
			"items": [{"order_item": "SOI-1", "score_10": 9, "comment": "عالی بود"}],
		})

		self.assertEqual(len(self.saved_reviews), 1)
		saved_review = self.saved_reviews[0]
		self.assertEqual(saved_review.moderation_status, "تأییدشده")
		self.assertEqual(saved_review.is_approved, 1)

	def test_public_reviews_keep_manager_reply_and_hide_rejections(self):
		source = (ROOT / "restaurant" / "api.py").read_text()
		tree = ast.parse(source)
		function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "get_item_reviews")
		function_source = ast.get_source_segment(source, function)

		self.assertIn('filters = {"is_approved": 1}', function_source)
		self.assertIn('where = "is_approved=1"', function_source)
		self.assertIn('"manager_reply": row.get("manager_reply") or ""', function_source)


if __name__ == "__main__":
	unittest.main()
