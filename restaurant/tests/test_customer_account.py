import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeCache:
    def __init__(self):
        self.values = {}

    def set_value(self, key, value, expires_in_sec=None):
        self.values[key] = value

    def get_value(self, key):
        return self.values.get(key)

    def delete_value(self, key):
        self.values.pop(key, None)


class FakeAddress:
    doctype = "Address"

    def __init__(self, customer):
        self.links = [types.SimpleNamespace(link_doctype="Customer", link_name=customer)]
        self.disabled = 0
        self.saved = False

    def get(self, key, default=None):
        return getattr(self, key, default)

    def save(self, ignore_permissions=False):
        self.saved = True


class CustomerAccountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cache = FakeCache()
        frappe = types.ModuleType("frappe")
        frappe.whitelist = lambda *args, **kwargs: (lambda fn: fn)
        frappe._ = lambda value: value
        frappe.PermissionError = PermissionError
        frappe.throw = lambda message, error=ValueError: (_ for _ in ()).throw(error(message))
        frappe.cache = lambda: cls.cache
        frappe.conf = {"encryption_key": "test-only-signing-key"}
        frappe.db = types.SimpleNamespace(exists=lambda doctype, name: doctype == "Customer" and name == "CUST-1")
        rate_limiter = types.ModuleType("frappe.rate_limiter")
        rate_limiter.rate_limit = lambda *args, **kwargs: (lambda fn: fn)
        cls.frappe = frappe
        cls.original = sys.modules.get("frappe")
        cls.original_rate_limiter = sys.modules.get("frappe.rate_limiter")
        sys.modules["frappe"] = frappe
        sys.modules["frappe.rate_limiter"] = rate_limiter
        spec = importlib.util.spec_from_file_location("restaurant.customer_account_test_target", Path(__file__).resolve().parents[1] / "customer_account.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        if cls.original is None:
            sys.modules.pop("frappe", None)
        else:
            sys.modules["frappe"] = cls.original
        if cls.original_rate_limiter is None:
            sys.modules.pop("frappe.rate_limiter", None)
        else:
            sys.modules["frappe.rate_limiter"] = cls.original_rate_limiter

    def setUp(self):
        self.cache.values.clear()
        self.address = FakeAddress("CUST-1")
        self.frappe.get_doc = lambda doctype, name: self.address

    def test_session_is_random_and_cache_stores_only_a_hash_of_the_token(self):
        token = self.module.issue_customer_session("CUST-1", "09123456789")
        self.assertNotIn(token, next(iter(self.cache.values)))
        self.assertEqual(self.module._require_customer(token)["customer"], "CUST-1")
        with self.assertRaises(PermissionError):
            self.module._require_customer("invalid")

    def test_signed_session_survives_cache_loss_and_rejects_tampering(self):
        token = self.module.issue_customer_session("CUST-1", "09123456789")
        self.cache.values.clear()

        self.assertEqual(self.module._require_customer(token)["customer"], "CUST-1")
        with self.assertRaises(PermissionError):
            self.module._require_customer(token[:-1] + ("0" if token[-1] != "0" else "1"))

    def test_logout_revokes_a_signed_session(self):
        token = self.module.issue_customer_session("CUST-1", "09123456789")

        self.assertTrue(self.module.customer_logout(token)["success"])
        with self.assertRaises(PermissionError):
            self.module._require_customer(token)

    def test_archiving_requires_the_owning_customer(self):
        token = self.module.issue_customer_session("CUST-1", "09123456789")
        self.assertTrue(self.module.archive_address(token, "ADDR-1")["success"])
        self.assertEqual(self.address.disabled, 1)
        self.assertTrue(self.address.saved)

        self.address = FakeAddress("CUST-2")
        with self.assertRaises(PermissionError):
            self.module.archive_address(token, "ADDR-2")
        self.assertFalse(self.address.saved)


if __name__ == "__main__":
    unittest.main()
