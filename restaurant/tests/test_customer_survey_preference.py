"""Regression tests for POS customer identity and survey preference reads."""

from unittest import TestCase
from unittest.mock import patch

import frappe

from restaurant import api as restaurant_api
from restaurant import api_survey


class CustomerSurveyPreferenceTests(TestCase):
	def test_customer_listing_preserves_stable_customer_name(self):
		customer_docs = [{
			"name": "CUST-1",
			"customer_name": "مشتری تکراری",
			"mobile_no": "09120000000",
			"customer_primary_mobile": "",
			"customer_group": "",
		}]

		with patch.object(restaurant_api, "_ensure_management_access"), patch.object(
			restaurant_api, "_has_column", return_value=False
		), patch.object(
			restaurant_api.frappe, "get_all", return_value=customer_docs
		), patch.object(
			restaurant_api, "_management_fetch_web_orders", return_value=[]
		):
			result = restaurant_api.list_management_customers()

		self.assertEqual(result["customers"][0]["name"], "CUST-1")

	def test_survey_read_with_exact_customer_name_uses_stable_identity(self):
		with patch.object(api_survey.api_club, "_ensure_management_access"), patch.object(
			api_survey, "_ensure_survey_customer_preference_field"
		), patch.object(api_survey.frappe.db, "exists", return_value=True), patch.object(
			api_survey.frappe.db, "get_value", return_value=1
		) as get_value:
			result = api_survey.get_management_customer_survey_preference("CUST-1", "")

		self.assertEqual(result["customer"], "CUST-1")
		self.assertEqual(result["opt_out"], 1)
		self.assertTrue(result["resolved"])
		get_value.assert_called_once_with("Customer", "CUST-1", api_survey.SURVEY_OPT_OUT_FIELD)

	def test_survey_read_for_unresolved_customer_returns_safe_default(self):
		with patch.object(api_survey.api_club, "_ensure_management_access"), patch.object(
			api_survey, "_ensure_survey_customer_preference_field"
		), patch.object(
			api_survey, "_resolve_survey_preference_customer",
			side_effect=frappe.DoesNotExistError("missing customer"),
		):
			result = api_survey.get_management_customer_survey_preference("missing", "")

		self.assertEqual(result["status"], "success")
		self.assertEqual(result["customer"], "")
		self.assertEqual(result["opt_out"], 0)
		self.assertFalse(result["resolved"])

	def test_survey_write_remains_strict_for_unresolved_customer(self):
		with patch.object(api_survey.api_club, "_ensure_management_access"), patch.object(
			api_survey, "_ensure_survey_customer_preference_field"
		), patch.object(
			api_survey, "_resolve_survey_preference_customer",
			side_effect=frappe.DoesNotExistError("missing customer"),
		):
			with self.assertRaises(frappe.DoesNotExistError):
				api_survey.set_management_customer_survey_preference("missing", "", 1)
