"""Smoke checks for request-scoped customer club schema provisioning."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe

from restaurant import api_club


def run_club_ops_ready_cache_smoke():
	flag = "_restaurant_club_ops_ready"
	previous = getattr(frappe.local, flag, None)
	setattr(frappe.local, flag, False)
	try:
		with (
			patch.object(api_club.frappe, "cache", SimpleNamespace(get_value=lambda key: None)),
			patch.object(api_club.frappe.db, "after_commit", SimpleNamespace(add=lambda callback: None)),
			patch.object(api_club, "_club_ensure_customer_fields") as customer,
			patch.object(api_club, "_club_ensure_sales_order_fields") as order,
			patch.object(api_club, "_club_ensure_settings_fields") as settings,
			patch.object(api_club, "_club_fp_call") as fields,
		):
			api_club._club_ensure_ops_ready()
			api_club._club_ensure_ops_ready()
			assert customer.call_count == 1
			assert order.call_count == 1
			assert settings.call_count == 1
			assert fields.call_count == 1

		setattr(frappe.local, flag, False)
		with patch.object(api_club, "_club_ensure_customer_fields", side_effect=RuntimeError("temporary failure")) as customer:
			try:
				api_club._club_ensure_ops_ready()
			except RuntimeError:
				pass
			else:
				raise AssertionError("schema failure must propagate")
			assert not getattr(frappe.local, flag, False)
			assert customer.call_count == 1
	finally:
		if previous is None:
			delattr(frappe.local, flag)
		else:
			setattr(frappe.local, flag, previous)
	return {"status": "ok"}


def run_club_ops_shared_cache_smoke():
	"""A committed schema check can be reused by later cashier requests."""
	flag = "_restaurant_club_ops_ready"
	previous = getattr(frappe.local, flag, None)
	setattr(frappe.local, flag, False)
	values = {}
	callbacks = []
	cache = SimpleNamespace(
		get_value=lambda key: values.get(key),
		set_value=lambda key, value, expires_in_sec=None: values.update({key: (value, expires_in_sec)}),
	)
	try:
		with (
			patch.object(api_club.frappe, "cache", cache),
			patch.object(api_club.frappe.db, "after_commit", SimpleNamespace(add=callbacks.append)),
			patch.object(api_club, "_club_ensure_customer_fields") as customer,
			patch.object(api_club, "_club_ensure_sales_order_fields"),
			patch.object(api_club, "_club_ensure_settings_fields"),
			patch.object(api_club, "_club_fp_call"),
		):
			api_club._club_ensure_ops_ready()
			assert customer.call_count == 1
			assert len(callbacks) == 1
			assert not values, "uncommitted provisioning must not be shared"
			callbacks.pop()()
			assert len(values) == 1
			assert next(iter(values.values())) == (1, 60)
			setattr(frappe.local, flag, False)
			api_club._club_ensure_ops_ready()
			assert customer.call_count == 1, "a later request should use the shared marker"
	finally:
		if previous is None:
			delattr(frappe.local, flag)
		else:
			setattr(frappe.local, flag, previous)
	return {"status": "ok"}
