"""Pure balance rules shared by customer wallet endpoints and tests."""

import re


PROMOTIONAL_CREDIT_KINDS = frozenset({"کش‌بک", "پاداش معرف", "تبدیل امتیاز"})


def split_legacy_wallet_ledger(rows, stored_total):
	"""Split old mixed balances; unknown legacy value remains purchase-only."""
	cash_balance = 0.0
	cashback_balance = 0.0
	for row in rows or []:
		amount = max(float(row.get("amount") or 0), 0)
		if row.get("direction") == "واریز":
			if row.get("kind") in PROMOTIONAL_CREDIT_KINDS:
				cashback_balance += amount
			else:
				cash_balance += amount
		elif row.get("direction") == "برداشت":
			promo_used = min(cashback_balance, amount)
			cashback_balance -= promo_used
			cash_balance = max(cash_balance - (amount - promo_used), 0)

	stored_total = max(float(stored_total or 0), 0)
	unclassified = stored_total - cash_balance - cashback_balance
	if unclassified > 0:
		cashback_balance += unclassified
	elif unclassified < 0:
		correction = abs(unclassified)
		promo_correction = min(cashback_balance, correction)
		cashback_balance -= promo_correction
		cash_balance = max(cash_balance - (correction - promo_correction), 0)
	return round(cash_balance, 2), round(cashback_balance, 2)


def allocate_wallet_payment(withdrawable_balance, cashback_balance, amount):
	"""Spend cashback first while keeping purchase-only credit non-withdrawable."""
	withdrawable = max(float(withdrawable_balance or 0), 0)
	cashback = max(float(cashback_balance or 0), 0)
	amount = float(amount or 0)
	if amount <= 0 or amount > withdrawable + cashback + 0.009:
		raise ValueError("موجودی کیف پول برای این پرداخت کافی نیست.")
	cashback_used = min(cashback, amount)
	withdrawable_used = amount - cashback_used
	return round(withdrawable_used, 2), round(cashback_used, 2)


def normalize_iranian_iban(value):
	iban = re.sub(r"[\s-]+", "", str(value or "")).upper()
	if not re.fullmatch(r"IR\d{24}", iban):
		return ""
	rotated = iban[4:] + iban[:4]
	numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rotated)
	remainder = 0
	for char in numeric:
		remainder = (remainder * 10 + int(char)) % 97
	return iban if remainder == 1 else ""
