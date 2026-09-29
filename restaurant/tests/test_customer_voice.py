import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeVoiceDocument:
	def __init__(self):
		self.flags = types.SimpleNamespace(ignore_permissions=False)
		self.name = "CV-2026-00001"
		self.creation = "2026-09-28 12:00:00"
		self.saved = False

	def save(self):
		self.saved = True

	def as_dict(self):
		return {
			"name": self.name,
			"customer": self.customer,
			"customer_name": self.customer_name,
			"mobile": self.mobile,
			"sales_order": self.sales_order,
			"order_code": self.order_code,
			"type": self.type,
			"subject": self.subject,
			"message": self.message,
			"status": self.status,
			"response": "",
			"responded_by": "",
			"responded_at": "",
			"creation": self.creation,
		}


class CustomerVoiceApiTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		frappe = types.ModuleType("frappe")
		frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
		frappe._ = lambda value: value
		frappe.PermissionError = PermissionError
		frappe.ValidationError = ValueError
		frappe.throw = lambda message, error=ValueError: (_ for _ in ()).throw(error(message))
		utils = types.ModuleType("frappe.utils")
		utils.add_days = lambda value, days: value
		utils.cint = lambda value=0: int(float(value or 0))
		utils.flt = lambda value=0: float(value or 0)
		utils.getdate = lambda value=None: value
		utils.now_datetime = lambda: "2026-09-28 12:00:00"
		utils.today = lambda: "2026-09-28"
		api = types.ModuleType("restaurant.api")
		api._bi_kpi = lambda *args, **kwargs: None
		api._compose_management_report = lambda *args, **kwargs: None
		api._ensure_mobile = lambda value, allow_empty=False: str(value or "")
		api._ensure_management_access = lambda: None
		api._has_column = lambda *args, **kwargs: True
		api._table_columns_from_rows = lambda *args, **kwargs: []
		customer_account = types.ModuleType("restaurant.customer_account")

		originals = {
			name: sys.modules.get(name)
		for name in ("frappe", "frappe.utils", "restaurant.api", "restaurant.customer_account")
		}
		package = sys.modules.get("restaurant")
		original_package_api = getattr(package, "api", None) if package else None
		sys.modules["frappe"] = frappe
		sys.modules["frappe.utils"] = utils
		sys.modules["restaurant.api"] = api
		sys.modules["restaurant.customer_account"] = customer_account
		if package:
			package.api = api

		target = Path(__file__).resolve().parents[1] / "api_club.py"
		spec = importlib.util.spec_from_file_location("restaurant.api_club_customer_voice_test", target)
		cls.module = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(cls.module)
		cls.frappe = frappe
		cls.customer_account = customer_account
		cls.originals = originals
		cls.package = package
		cls.original_package_api = original_package_api

	@classmethod
	def tearDownClass(cls):
		for name, value in cls.originals.items():
			if value is None:
				sys.modules.pop(name, None)
			else:
				sys.modules[name] = value
		if cls.package:
			if cls.original_package_api is None:
				delattr(cls.package, "api")
			else:
				cls.package.api = cls.original_package_api

	def setUp(self):
		self.saved = None
		self.identity = {"customer": "CUST-1", "mobile": "09123456789"}
		self.customer_account._require_customer = lambda token: self.identity if token == "valid-token" else (_ for _ in ()).throw(PermissionError("invalid"))
		self.frappe.db = types.SimpleNamespace(
			exists=lambda doctype, name=None: doctype == "DocType" and name == "Restaurant Customer Voice",
			get_value=lambda doctype, name, field: "مشتری اول" if doctype == "Customer" and name == "CUST-1" and field == "customer_name" else None,
			commit=lambda: None,
		)
		self.frappe.new_doc = lambda doctype: self._new_doc(doctype)
		self.module._club_parse_json = lambda value, fallback=None: value if isinstance(value, dict) else (fallback or {})
		self.module._club_verify_survey_order = lambda order_code, mobile: None

	def _new_doc(self, doctype):
		self.saved = FakeVoiceDocument()
		return self.saved

	def test_account_voice_uses_session_identity_and_starts_new(self):
		result = self.module.submit_my_customer_voice(
			customer_token="valid-token",
			payload={
				"type": "پیشنهاد",
				"subject": "منوی روزانه",
				"message": "غذای روزانه اضافه شود",
				"customer": "FORGED-CUSTOMER",
				"mobile": "09000000000",
			},
		)

		self.assertEqual(result["status"], "success")
		self.assertEqual(result["voice"]["status"], "جدید")
		self.assertEqual(self.saved.customer, "CUST-1")
		self.assertEqual(self.saved.mobile, "09123456789")
		self.assertTrue(self.saved.saved)

	def test_account_voice_rejects_invalid_type_and_missing_content(self):
		with self.assertRaises(ValueError):
			self.module.submit_my_customer_voice(
				customer_token="valid-token",
				payload={"type": "نامعتبر", "subject": "موضوع", "message": "متن"},
			)
		with self.assertRaises(ValueError):
			self.module.submit_my_customer_voice(
				customer_token="valid-token",
				payload={"type": "انتقاد", "subject": "", "message": "متن"},
			)

	def test_account_voice_rejects_order_owned_by_another_customer(self):
		self.module._club_verify_survey_order = lambda order_code, mobile: {"sales_order": "SO-2", "customer": "CUST-2"}
		with self.assertRaises(PermissionError):
			self.module.submit_my_customer_voice(
				customer_token="valid-token",
				payload={"type": "شکایت", "subject": "سفارش", "message": "مشکل", "order_code": "SO-2"},
			)

	def test_account_voice_requires_a_valid_customer_session(self):
		with self.assertRaises(PermissionError):
			self.module.submit_my_customer_voice(
				customer_token="bad-token",
				payload={"type": "پیشنهاد", "subject": "موضوع", "message": "متن"},
			)

	def test_account_voice_list_is_scoped_to_authenticated_customer(self):
		rows = [
			{"name": "CV-1", "customer": "CUST-1", "customer_name": "اول", "mobile": "09123456789", "type": "پیشنهاد", "subject": "اول", "message": "متن اول", "status": "جدید", "creation": "2026-09-28 12:00:00"},
			{"name": "CV-2", "customer": "CUST-2", "customer_name": "دوم", "mobile": "09120000000", "type": "شکایت", "subject": "دوم", "message": "متن دوم", "status": "جدید", "creation": "2026-09-28 11:00:00"},
		]
		self.frappe.get_all = lambda doctype, filters=None, **kwargs: [row for row in rows if row["customer"] == filters["customer"]]

		result = self.module.list_my_customer_voices(customer_token="valid-token")

		self.assertEqual(result["count"], 1)
		self.assertEqual(result["voices"][0]["name"], "CV-1")
		self.assertNotIn("responded_by", result["voices"][0])


if __name__ == "__main__":
	unittest.main()
