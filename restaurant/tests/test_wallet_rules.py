import unittest

from restaurant.wallet_rules import allocate_wallet_payment, normalize_iranian_iban, split_legacy_wallet_ledger


def iranian_iban(body):
	rotated = body[2:] + "IR00"
	numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rotated)
	remainder = 0
	for char in numeric:
		remainder = (remainder * 10 + int(char)) % 97
	return f"IR{98 - remainder:02d}{body[2:]}"


class WalletRuleTests(unittest.TestCase):
	def test_legacy_balance_reconciles_cash_and_promo_without_making_unknown_money_withdrawable(self):
		cash, cashback = split_legacy_wallet_ledger(
			[
				{"kind": "شارژ", "direction": "واریز", "amount": 1000},
				{"kind": "کش‌بک", "direction": "واریز", "amount": 200},
				{"kind": "پرداخت", "direction": "برداشت", "amount": 300},
			],
			1000,
		)
		# The recorded ledger explains 900. The remaining legacy balance is
		# deliberately kept purchase-only because its source is unknown.
		self.assertEqual((cash, cashback), (900, 100))

		known_cash, known_cashback = split_legacy_wallet_ledger(
			[
				{"kind": "شارژ", "direction": "واریز", "amount": 1000},
				{"kind": "کش‌بک", "direction": "واریز", "amount": 200},
				{"kind": "پرداخت", "direction": "برداشت", "amount": 300},
			],
			900,
		)
		self.assertEqual((known_cash, known_cashback), (900, 0))

	def test_payment_uses_purchase_only_credit_first_and_rejects_overspend(self):
		self.assertEqual(allocate_wallet_payment(800, 200, 900), (700, 200))
		with self.assertRaises(ValueError):
			allocate_wallet_payment(800, 200, 1001)

	def test_iranian_iban_is_normalized_and_mod97_checked(self):
		valid = iranian_iban("IR" + "0" * 22)
		self.assertTrue(normalize_iranian_iban(valid))
		self.assertEqual(normalize_iranian_iban(f" {valid[:8]} {valid[8:]} "), valid)
		self.assertEqual(normalize_iranian_iban(valid[:-1] + ("0" if valid[-1] != "0" else "1")), "")
		self.assertEqual(normalize_iranian_iban("123456"), "")


if __name__ == "__main__":
	unittest.main()
