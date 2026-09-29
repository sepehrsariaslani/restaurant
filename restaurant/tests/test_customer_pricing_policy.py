import unittest

from restaurant.pricing_policy import (
	allocate_return_amount_by_order,
	calculate_manual_discount_amount,
	coach_commission_amount,
	resolve_manual_discount_active,
	select_order_discount,
)


class TestCustomerPricingPolicy(unittest.TestCase):
	def test_largest_discount_wins_without_stacking(self):
		result = select_order_discount(1000, group_percent=10, coach_percent=5, coupon_amount=80)
		self.assertEqual(result["discount_amount"], 100)
		self.assertEqual(result["discount_source"], "customer_group")
		self.assertEqual(result["net_items"], 900)

	def test_coupon_can_win_and_coach_commission_uses_discounted_items(self):
		result = select_order_discount(1000, group_percent=5, coach_percent=5, coupon_amount=120)
		self.assertEqual(result["discount_source"], "coupon")
		self.assertEqual(result["net_items"], 880)
		self.assertEqual(coach_commission_amount(result["net_items"], 5), 44)

	def test_discounts_are_bounded_by_subtotal_and_negative_inputs_are_ignored(self):
		result = select_order_discount(50, group_percent=200, coach_percent=-5, coupon_amount=75)
		self.assertEqual(result["discount_amount"], 50)
		self.assertEqual(result["net_items"], 0)

	def test_ties_are_stable(self):
		result = select_order_discount(100, group_percent=5, coach_percent=5, coupon_amount=5)
		self.assertEqual(result["discount_source"], "customer_group")

	def test_manual_discount_replaces_group_discount_even_when_smaller(self):
		result = select_order_discount(
			1000,
			group_percent=20,
			coupon_amount=180,
			manual_discount_amount=50,
			manual_discount_active=True,
		)
		self.assertEqual(result["discount_amount"], 50)
		self.assertEqual(result["discount_source"], "manual")
		self.assertEqual(result["group_discount"], 200)
		self.assertEqual(result["net_items"], 950)

	def test_manual_percent_and_fixed_amount_are_bounded(self):
		self.assertEqual(calculate_manual_discount_amount(1000, "percent", 7.5), 75)
		self.assertEqual(calculate_manual_discount_amount(1000, "fixed", 1200), 1000)

	def test_clearing_manual_discount_allows_group_discount_to_return(self):
		result = select_order_discount(1000, group_percent=10, manual_discount_active=False)
		self.assertEqual(result["discount_source"], "customer_group")
		self.assertEqual(result["discount_amount"], 100)

	def test_legacy_pos_payload_infers_manual_discount_when_it_differs_from_group(self):
		self.assertTrue(
			resolve_manual_discount_active(
				{"discount_type": "percent", "discount_value": 10},
				group_percent=9,
			)
		)
		self.assertFalse(
			resolve_manual_discount_active(
				{"discount_type": "percent", "discount_value": 9, "discount_source": "customer_group"},
				group_percent=9,
			)
		)

	def test_invoice_return_is_allocated_by_each_linked_order_amount(self):
		result = allocate_return_amount_by_order(100, {"SO-1": 100, "SO-2": 300})
		self.assertEqual(result, {"SO-1": 25, "SO-2": 75})

	def test_return_allocation_is_capped_and_ignores_negative_source_amounts(self):
		result = allocate_return_amount_by_order(500, {"SO-1": 100, "SO-2": -20})
		self.assertEqual(result, {"SO-1": 100})


if __name__ == "__main__":
	unittest.main()
