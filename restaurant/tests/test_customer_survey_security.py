"""Isolated security checks for the order-backed customer survey API."""

import importlib.util
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path


def _cint(value=0):
	try:
		return int(float(value or 0))
	except (TypeError, ValueError):
		return 0


class SurveySecurityTests(unittest.TestCase):
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
		utils.cint = _cint
		utils.flt = lambda value=0: float(value or 0)
		utils.get_datetime = lambda value: value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
		utils.now_datetime = datetime.now

		club = types.ModuleType("restaurant.api_club")
		originals = {
			name: sys.modules.get(name)
			for name in ("frappe", "frappe.utils", "restaurant.api_club")
		}
		package = sys.modules.get("restaurant")
		original_package_club = getattr(package, "api_club", None) if package else None
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils
		sys.modules["restaurant.api_club"] = club
		if package:
			package.api_club = club

		target = Path(__file__).resolve().parents[1] / "api_survey.py"
		spec = importlib.util.spec_from_file_location("restaurant.api_survey_security_test", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)

		for name, value in originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value
		if package:
			if original_package_club is None:
				delattr(package, "api_club")
			else:
				package.api_club = original_package_club

	def setUp(self):
		self.frappe = self.module.frappe
		class Data(dict):
			__getattr__ = dict.__getitem__

		self.question = Data({
			"name": "SQ-FLAVOR",
			"question": "طعم غذا چطور بود؟",
			"answer_type": "ویژگی خوب/بد",
			"scope": "محصول",
			"target_item": "FOOD-1",
			"target_item_group": "",
		})
		self.item = {
			"order_item": "SOI-1",
			"item": "FOOD-1",
			"item_group": "Meals",
		}
		self.frappe.get_all = lambda *args, **kwargs: [self.question]

	def set_customer_identity(self, identity):
		api = types.ModuleType("restaurant.api")
		api._customer_session_identity = lambda *args, **kwargs: identity
		api._ensure_mobile = lambda value, allow_empty=False: str(value or "")
		original_api = sys.modules.get("restaurant.api")
		package = sys.modules.get("restaurant")
		original_package_api = getattr(package, "api", None) if package else None
		sys.modules["restaurant.api"] = api
		if package:
			package.api = api

		def restore():
			if original_api is None:
				sys.modules.pop("restaurant.api", None)
			else:
				sys.modules["restaurant.api"] = original_api
			if package:
				if original_package_api is None:
					delattr(package, "api")
				else:
					package.api = original_package_api

		self.addCleanup(restore)

	def test_answers_must_match_a_real_order_line_and_configured_target(self):
		with self.assertRaises(PermissionError):
			self.module._validate_answers(
				{"answers": [{"question": "SQ-FLAVOR", "order_item": "SOI-FORGED", "value": "نقطه قوت"}]},
				[self.item],
			)

		answers = self.module._validate_answers(
			{"answers": [{"question": "SQ-FLAVOR", "order_item": "SOI-1", "value": "نقطه قوت"}]},
			[self.item],
		)
		self.assertEqual(answers[0]["order_item"], "SOI-1")

	def test_duplicate_answers_for_the_same_question_and_item_are_rejected(self):
		answer = {"question": "SQ-FLAVOR", "order_item": "SOI-1", "value": "نقطه قوت"}
		with self.assertRaises(ValueError):
			self.module._validate_answers({"answers": [answer, answer]}, [self.item])

	def test_submission_rejects_an_item_row_not_present_in_the_order(self):
		now = datetime.now()
		invitation = types.SimpleNamespace(
			name="RSI-1",
			order_key="Sales Order:SO-1",
			order_code="SO-1",
			submitted_at=None,
			status="ارسال‌شده",
			due_at=now - timedelta(minutes=1),
			expires_at=now + timedelta(days=2),
			sales_order="SO-1",
			table_order=None,
			customer="CUST-1",
			mobile="09120000000",
		)
		self.module._invitation_by_token = lambda token: invitation if token == "private-token" else None
		self.module._load_order = lambda doc: {"order_code": "SO-1", "items": [self.item]}
		self.module.api_club._club_parse_payload = lambda value: value or {}
		self.frappe.db = types.SimpleNamespace(
			exists=lambda *args, **kwargs: False,
			get_value=lambda *args, **kwargs: None,
		)
		payload = {
			"token": "private-token",
			"items": [{"order_item": "SOI-FORGED", "score_10": 10}],
		}
		with self.assertRaises(PermissionError):
			self.module.submit_public_survey(payload)

	def test_edit_cannot_use_a_public_sms_token(self):
		self.module.api_club._club_parse_payload = lambda value: value or {}
		with self.assertRaises(PermissionError):
			self.module.submit_public_survey({"token": "sms-token", "edit": 1})

	def test_order_survey_ownership_requires_matching_customer_or_verified_mobile(self):
		self.module._valid_mobile = lambda value: str(value or "")
		self.assertTrue(self.module._order_owned_by_identity(
			{"customer": "CUST-1", "mobile": "09120000000"},
			{"customer": "CUST-1", "mobile": "09120000000"},
		))
		self.assertFalse(self.module._order_owned_by_identity(
			{"customer": "CUST-1", "mobile": "09120000000"},
			{"customer": "CUST-2", "mobile": "09121111111"},
		))

	def test_customer_request_activates_account_flow_without_queuing_sms(self):
		self.set_customer_identity({"customer": "CUST-1", "mobile": "09120000000"})
		self.module._valid_mobile = lambda value: str(value or "")
		self.module._read_order_identity = lambda doctype, name: {"customer": "CUST-1", "mobile": "09120000000"}
		now = datetime.now()
		self.module.now_datetime = lambda: now
		invitation = types.SimpleNamespace(
			name="RSI-1", submitted_at=None, status="در انتظار ارسال", due_at=None,
			expires_at=None, token_hash="sms-hash", last_error="",
			save=lambda **kwargs: None,
		)
		self.module._queue_invitation = lambda doctype, name: invitation
		self.frappe.db = types.SimpleNamespace(commit=lambda: None)
		result = self.module.request_my_order_survey("SO-1", customer_token="customer-token")

		self.assertEqual(result["status"], "ready")
		self.assertIn("invitation=RSI-1", result["href"])
		self.assertEqual(invitation.status, "بدون درگاه")
		self.assertEqual(invitation.due_at, now)
		self.assertEqual(invitation.token_hash, "")

	def test_submission_does_not_bypass_the_invitation_delay(self):
		now = datetime.now()
		invitation = types.SimpleNamespace(
			name="RSI-EARLY",
			status="در انتظار ارسال",
			submitted_at=None,
			due_at=now + timedelta(minutes=30),
			expires_at=now + timedelta(days=30),
		)
		self.module._invitation_by_token = lambda token: invitation if token == "private-token" else None
		self.module.api_club._club_parse_payload = lambda value: value or {}
		with self.assertRaises(PermissionError):
			self.module.submit_public_survey({"token": "private-token"})

	def test_sms_history_does_not_store_the_bearer_link(self):
		url = "https://example.test/survey?token=private-secret"
		logged = self.module._redact_survey_url(f"ثبت نظر: {url}", url)
		self.assertNotIn("private-secret", logged)
		self.assertIn("[پیوند امن نظرسنجی]", logged)

	def test_account_invitation_rejects_another_customer(self):
		invitation = types.SimpleNamespace(customer="CUST-1", mobile="09120000000")
		self.frappe.get_doc = lambda *args, **kwargs: invitation
		api = types.ModuleType("restaurant.api")
		api._customer_session_identity = lambda *args, **kwargs: {"customer": "CUST-2", "mobile": "09121111111"}
		api._ensure_mobile = lambda value, allow_empty=False: str(value or "")
		original_api = sys.modules.get("restaurant.api")
		package = sys.modules.get("restaurant")
		original_package_api = getattr(package, "api", None) if package else None
		sys.modules["restaurant.api"] = api
		if package:
			package.api = api
		try:
			with self.assertRaises(PermissionError):
				self.module._owned_invitation("RSI-1", "customer-token")
		finally:
			if original_api is None:
				sys.modules.pop("restaurant.api", None)
			else:
				sys.modules["restaurant.api"] = original_api
			if package:
				if original_package_api is None:
					delattr(package, "api")
				else:
					package.api = original_package_api
