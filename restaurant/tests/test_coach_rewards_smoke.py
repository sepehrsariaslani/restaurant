"""Bench-executable, side-effect-free checks for coach reward idempotency and recovery."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe

from restaurant import api_club, coach_rewards


class FakeWallet:
	def __init__(self, balance):
		self.name = "WALLET-TEST"
		self.status = "فعال"
		self.cashback_balance = balance

	def get(self, key, default=None):
		return getattr(self, key, default)


class FakeSalesOrder:
	def __init__(self, **values):
		self.__dict__.update(values)

	def get(self, key, default=None):
		return getattr(self, key, default)


class AttributeDict(dict):
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError as exc:
			raise AttributeError(key) from exc


def run_coach_rewards_smoke():
	"""Test exactly-once credit and debt recovery without creating site records."""
	db = frappe.db
	wallet = FakeWallet(0)
	order_state = {
		"customer": "STUDENT",
		"restaurant_coach_customer": "COACH",
		"restaurant_coach_commission_amount": 100,
		"restaurant_coach_reversed_amount": 0,
		"restaurant_coach_credited": 0,
		"restaurant_coach_recovery_due": 0,
	}
	wallet_state = {"restaurant_coach_recovery_due": 0}
	transactions = []

	def get_value(doctype, name, fields, as_dict=False):
		if doctype == "Sales Order" and isinstance(fields, (list, tuple)):
			return AttributeDict({field: order_state.get(field) for field in fields})
		if doctype == api_club.CLUB_DOCTYPES["wallet"]:
			return wallet_state.get(fields, 0)
		return ""

	def set_value(doctype, name, field, value, **kwargs):
		if doctype == "Sales Order":
			if isinstance(field, dict):
				order_state.update(field)
			else:
				order_state[field] = value
		elif doctype == api_club.CLUB_DOCTYPES["wallet"]:
			wallet_state[field] = value

	def exists(doctype, filters=None):
		return bool(transactions) if doctype == api_club.CLUB_DOCTYPES["wallet_txn"] else True

	def append_transaction(**kwargs):
		transactions.append(kwargs)
		if kwargs["direction"] == "واریز":
			wallet.cashback_balance += kwargs["amount"]
		else:
			wallet.cashback_balance -= kwargs["amount"]
		return True

	club = SimpleNamespace(
		CLUB_DOCTYPES=api_club.CLUB_DOCTYPES,
		coach_payment_settled=lambda _name: True,
		_club_get_or_create_wallet=lambda _customer: wallet,
		_club_wallet_txn=append_transaction,
	)
	order = FakeSalesOrder(
		docstatus=1,
		restaurant_status="delivered",
		per_delivered=100,
		customer="STUDENT",
		restaurant_coach_customer="COACH",
		restaurant_coach_commission_amount=100,
		restaurant_coach_reversed_amount=0,
		restaurant_coach_credited=0,
	)
	assert coach_rewards._order_delivered(order) is True
	assert club.coach_payment_settled("SO-TEST") is True

	with (
		patch.object(db, "sql"),
		patch.object(db, "get_value", side_effect=get_value),
		patch.object(db, "set_value", side_effect=set_value),
		patch.object(db, "exists", side_effect=exists),
		patch.object(db, "has_column", return_value=True),
		patch.object(frappe, "get_doc", return_value=order),
	):
		credited = coach_rewards._credit(club, "Sales Order", "SO-TEST", "STUDENT", "COACH", 100)
		assert credited is True, {"credited": credited, "order": order_state, "transactions": transactions, "wallet": wallet.cashback_balance}
		assert coach_rewards._credit(club, "Sales Order", "SO-TEST", "STUDENT", "COACH", 100) is False
		assert len(transactions) == 1
		assert wallet.cashback_balance == 100

		order_state["restaurant_coach_credited"] = 1
		wallet.cashback_balance = 30
		transactions.clear()
		transactions.append({"kind": "کمیسیون مربی", "reference_name": "SO-TEST"})
		result = coach_rewards._reverse(
			club,
			"Sales Order",
			"SO-TEST",
			"COACH",
			100,
			0,
			1,
		)
		assert result["cashback_debit"] == 30
		assert result["recovery_due"] == 70
		assert wallet.cashback_balance == 0
		assert wallet_state["restaurant_coach_recovery_due"] == 70
		assert order_state["restaurant_coach_recovery_due"] == 70
	return {"status": "ok", "credit_once": True, "cashback_debit": 30, "recovery_due": 70}
