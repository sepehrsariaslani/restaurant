"""Isolated checks for the SMS.ir-to-restaurant survey token bridge."""

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ACCOUNTS_ROOT = ROOT.parent / "accounts"


class Invitation(dict):
	def __getattr__(self, name):
		return self.get(name)

	def __setattr__(self, name, value):
		self[name] = value

	def insert(self, **kwargs):
		self.insert_kwargs = kwargs
		self.name = self.name or "RSI-NEW"

	def save(self, **kwargs):
		self.save_kwargs = kwargs


class SurveyTokenBridgeTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe = types.ModuleType("frappe")
		utils = types.ModuleType("frappe.utils")
		utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
		utils.now_datetime = datetime.now
		frappe.utils = utils

		cls.originals = {name: sys.modules.get(name) for name in ("frappe", "frappe.utils")}
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils

		target = ROOT / "restaurant" / "survey_tokens.py"
		spec = importlib.util.spec_from_file_location("restaurant.survey_tokens_bridge_test", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)

	@classmethod
	def tearDownClass(cls):
		for name, value in cls.originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value

	def setUp(self):
		self.docs = {}
		self.sales_orders = {
			"SO-1": Invitation(
				name="SO-1",
				docstatus=1,
				restaurant_status="confirmed",
				customer="CUST-1",
				customer_name="مشتری اصلی",
				restaurant_customer_mobile="09120000001",
			)
		}
		self.new_docs = []

		def exists(doctype, name):
			return name in (self.sales_orders if doctype == "Sales Order" else self.docs)

		def get_value(doctype, filters, fieldname):
			for name, doc in self.docs.items():
				if all(doc.get(key) == value for key, value in filters.items()):
					return name if fieldname == "name" else doc.get(fieldname)
			return None

		def get_doc(doctype, name):
			return (self.sales_orders if doctype == "Sales Order" else self.docs)[name]

		def new_doc(doctype):
			doc = Invitation(name=None)
			self.new_docs.append(doc)
			return doc

		self.module.frappe.db = types.SimpleNamespace(exists=exists, get_value=get_value)
		self.module.frappe.get_doc = get_doc
		self.module.frappe.new_doc = new_doc
		survey_api = types.ModuleType("restaurant.api_survey")
		survey_api._read_order_identity = lambda doctype, name: {
			"customer": "CUST-1",
			"customer_name": "مشتری اصلی",
			"mobile": "09120000001",
			"order_code": name,
		} if doctype == "Sales Order" and name in self.sales_orders else None
		self.original_survey_api = sys.modules.get("restaurant.api_survey")
		sys.modules["restaurant.api_survey"] = survey_api
		self.addCleanup(self._restore_survey_api)

	def _restore_survey_api(self):
		if self.original_survey_api is None:
			sys.modules.pop("restaurant.api_survey", None)
		else:
			sys.modules["restaurant.api_survey"] = self.original_survey_api

	def test_issued_token_is_short_and_only_digest_is_persisted(self):
		token = self.module.issue_token(
			"SO-1",
			"CUST-1",
			"09120000000",
			datetime.now() + timedelta(days=30),
		)

		self.assertLessEqual(len(token), 25)
		self.assertNotEqual(self.module.token_digest(token), token)
		self.assertEqual(len(self.new_docs), 1)
		invitation = self.new_docs[0]
		self.assertEqual(invitation.order_key, "Sales Order:SO-1")
		self.assertEqual(invitation.token_hash, self.module.token_digest(token))
		self.assertNotIn(token, invitation.values())
		self.assertEqual(invitation.status, "ارسال‌شده")

	def test_issue_token_reuses_the_existing_order_invitation(self):
		existing = Invitation(
			name="RSI-1",
			order_key="Sales Order:SO-1",
			token_hash="old-digest",
			status="ناموفق",
		)
		self.docs[existing.name] = existing

		token = self.module.issue_token(
			"SO-1",
			"CUST-2",
			"09121111111",
			datetime.now() + timedelta(days=30),
		)

		self.assertEqual(self.new_docs, [])
		self.assertEqual(existing.token_hash, self.module.token_digest(token))
		self.assertEqual(existing.customer, "CUST-1")
		self.assertEqual(existing.mobile, "09120000001")
		self.assertEqual(existing.status, "ارسال‌شده")
		self.assertEqual(existing.save_kwargs, {"ignore_permissions": True})

	def test_issue_token_uses_canonical_order_identity_not_log_values(self):
		token = self.module.issue_token(
			"SO-1",
			"FORGED-CUSTOMER",
			"09129999999",
			datetime.now() + timedelta(days=30),
		)

		invitation = self.new_docs[0]
		self.assertEqual(invitation.customer, "CUST-1")
		self.assertEqual(invitation.mobile, "09120000001")
		self.assertEqual(invitation.customer_name, "مشتری اصلی")
		self.assertEqual(invitation.order_code, "SO-1")
		self.assertNotEqual(invitation.mobile, "09129999999")
		self.assertTrue(token)

	def test_issue_token_rejects_unknown_order_before_creating_invitation(self):
		with self.assertRaises(ValueError):
			self.module.issue_token(
				"SO-FORGED",
				"CUST-1",
				"09120000001",
				datetime.now() + timedelta(days=30),
			)
		self.assertEqual(self.new_docs, [])

	def test_resolve_token_checks_digest_and_expiry(self):
		token = self.module.generate_token()
		invitation = Invitation(
			name="RSI-1",
			token_hash=self.module.token_digest(token),
			expires_at=datetime.now() + timedelta(minutes=5),
		)
		self.docs[invitation.name] = invitation

		self.assertIs(self.module.resolve_token(token), invitation)
		self.assertIsNone(self.module.resolve_token(f"{token}x"))

		invitation.expires_at = datetime.now() - timedelta(seconds=1)
		self.assertIsNone(self.module.resolve_token(token))

	def test_revoke_token_clears_only_the_matching_digest(self):
		token = self.module.generate_token()
		invitation = Invitation(
			name="RSI-1",
			token_hash=self.module.token_digest(token),
			expires_at=datetime.now() + timedelta(minutes=5),
			status="ارسال‌شده",
		)
		self.docs[invitation.name] = invitation

		self.module.revoke_token(token)

		self.assertEqual(invitation.token_hash, "")
		self.assertEqual(invitation.status, "ناموفق")
		self.assertEqual(invitation.save_kwargs, {"ignore_permissions": True})

	def test_feedback_dispatch_source_uses_secure_token_module(self):
		source = (ACCOUNTS_ROOT / "accounts" / "sms_ir_events.py").read_text()
		self.assertIn("from restaurant.survey_tokens import issue_token", source)


if __name__ == "__main__":
	unittest.main()
