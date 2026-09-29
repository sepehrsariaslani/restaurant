import importlib.util
import sys
import types
import unittest
from pathlib import Path


class SurveyScalePatchTests(unittest.TestCase):
    def test_single_settings_doctype_uses_metadata_instead_of_table_columns(self):
        calls = []

        class Database:
            def exists(self, doctype, name):
                return doctype == "DocType" and name == "Restaurant Web Settings"

            def has_column(self, doctype, fieldname):
                raise AssertionError("single DocType must not be checked with has_column")

            def get_single_value(self, doctype, fieldname):
                return 3

            def set_single_value(self, doctype, fieldname, value):
                calls.append((doctype, fieldname, value))

            def commit(self):
                pass

        frappe = types.ModuleType("frappe")
        frappe.db = Database()
        frappe.get_meta = lambda doctype: types.SimpleNamespace(
            has_field=lambda fieldname: fieldname == "restaurant_survey_alert_threshold"
        )

        original_frappe = sys.modules.get("frappe")
        sys.modules["frappe"] = frappe
        try:
            target = Path(__file__).resolve().parents[1] / "patches/v2_17/upgrade_customer_surveys_to_ten.py"
            spec = importlib.util.spec_from_file_location("survey_scale_patch_test_target", target)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.execute()
        finally:
            if original_frappe is None:
                sys.modules.pop("frappe", None)
            else:
                sys.modules["frappe"] = original_frappe

        self.assertEqual(
            calls,
            [("Restaurant Web Settings", "restaurant_survey_alert_threshold", 6)],
        )


if __name__ == "__main__":
    unittest.main()
