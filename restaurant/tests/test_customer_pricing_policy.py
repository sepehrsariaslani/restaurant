import unittest

from restaurant.pricing_policy import allocate_return_amount_by_order, coach_commission_amount, select_order_discount


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

	def test_invoice_return_is_allocated_by_each_linked_order_amount(self):
		result = allocate_return_amount_by_order(100, {"SO-1": 100, "SO-2": 300})
		self.assertEqual(result, {"SO-1": 25, "SO-2": 75})

	def test_return_allocation_is_capped_and_ignores_negative_source_amounts(self):
		result = allocate_return_amount_by_order(500, {"SO-1": 100, "SO-2": -20})
		self.assertEqual(result, {"SO-1": 100})


if __name__ == "__main__":
	unittest.main()
