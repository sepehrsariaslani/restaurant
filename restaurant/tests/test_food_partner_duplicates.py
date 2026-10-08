import unittest
from unittest.mock import Mock

from restaurant.food_partner_duplicates import (
	MANUAL_DUPLICATE_SOURCE,
	assign_manual_duplicates,
	claim_manual_duplicate_order,
	find_manual_duplicate,
	has_comparable_partner_items,
)


def partner_order(*, order_id="FP-1", day="2026-10-08", total=250000, items=None):
	return {
		"order_id": order_id,
		"created_at": f"{day} 13:05:00",
		"final_amount": total,
		"items": items if items is not None else [
			{"qty": 2, "mapped_item": {"item_code": "BURGER"}},
			{"qty": 1, "mapped_item": {"item_code": "DRINK"}},
		],
	}


def manual_order(*, day="2026-10-08", total=250000, items=None, **extra):
	return {
		"name": "SO-1",
		"source": "web",
		"docstatus": 1,
		"created_at": f"{day} 13:00:00",
		"grand_total": total,
		"items": items if items is not None else [
			{"item_code": "DRINK", "qty": 1},
			{"item_code": "BURGER", "qty": 2},
		],
		**extra,
	}


class TestFoodPartnerManualDuplicates(unittest.TestCase):
	def test_matches_same_day_total_and_item_quantities_independent_of_row_order(self):
		match = find_manual_duplicate(partner_order(), [manual_order()])

		self.assertEqual(match["name"], "SO-1")

	def test_does_not_match_when_final_amount_differs_by_more_than_one_unit(self):
		match = find_manual_duplicate(partner_order(total=250002), [manual_order()])

		self.assertIsNone(match)

	def test_does_not_match_when_item_quantity_differs(self):
		match = find_manual_duplicate(
			partner_order(items=[
				{"qty": 1, "mapped_item": {"item_code": "BURGER"}},
				{"qty": 1, "mapped_item": {"item_code": "DRINK"}},
			]),
			[manual_order()],
		)

		self.assertIsNone(match)

	def test_does_not_match_a_different_order_date(self):
		match = find_manual_duplicate(partner_order(day="2026-10-09"), [manual_order()])

		self.assertIsNone(match)

	def test_does_not_match_when_partner_item_is_unmapped(self):
		match = find_manual_duplicate(
			partner_order(items=[{"qty": 1, "title": "برگر", "mapped_item": None}]),
			[manual_order()],
		)

		self.assertIsNone(match)

	def test_one_manual_order_is_not_consumed_twice(self):
		used = set()

		first = find_manual_duplicate(partner_order(), [manual_order()], used_order_names=used)
		second = find_manual_duplicate(partner_order(), [manual_order()], used_order_names=used)

		self.assertEqual(first["name"], "SO-1")
		self.assertIsNone(second)

	def test_batch_assignment_stays_one_to_one_for_individually_selected_orders(self):
		orders = [partner_order(order_id="FP-1"), partner_order(order_id="FP-2")]

		assignments = assign_manual_duplicates(
			orders,
			{"2026-10-08": [manual_order()]},
		)

		self.assertEqual(assignments, {"FP-1": "SO-1"})

	def test_does_not_match_an_order_that_already_has_an_external_identity(self):
		match = find_manual_duplicate(
			partner_order(),
			[manual_order(external_source="snapp_food", external_order_id="remote-1")],
		)

		self.assertIsNone(match)

	def test_does_not_reuse_a_manual_order_already_linked_to_a_partner_order(self):
		match = find_manual_duplicate(
			partner_order(),
			[
				manual_order(
					external_source="snapp_food_manual_duplicate",
					external_order_id="remote-1",
				)
			],
		)

		self.assertIsNone(match)

	def test_manual_order_claim_uses_a_row_lock_and_sets_partner_identity(self):
		database = Mock()
		database.get_value.return_value = {
			"restaurant_external_source": "",
			"restaurant_external_order_id": "",
		}

		claimed = claim_manual_duplicate_order(database, "SO-1", "FP-1")

		self.assertTrue(claimed)
		database.savepoint.assert_called_once()
		self.assertTrue(database.get_value.call_args.kwargs["for_update"])
		database.set_value.assert_called_once_with(
			"Sales Order",
			"SO-1",
			{
				"restaurant_external_source": MANUAL_DUPLICATE_SOURCE,
				"restaurant_external_order_id": "FP-1",
			},
			update_modified=False,
		)

	def test_manual_order_claim_cannot_overwrite_a_different_partner_identity(self):
		database = Mock()
		database.get_value.return_value = {
			"restaurant_external_source": MANUAL_DUPLICATE_SOURCE,
			"restaurant_external_order_id": "FP-OLD",
		}

		claimed = claim_manual_duplicate_order(database, "SO-1", "FP-NEW")

		self.assertFalse(claimed)
		database.set_value.assert_not_called()
		database.rollback.assert_called_once()

	def test_manual_order_claim_is_idempotent_for_the_same_partner_identity(self):
		database = Mock()
		database.get_value.return_value = {
			"restaurant_external_source": MANUAL_DUPLICATE_SOURCE,
			"restaurant_external_order_id": "FP-1",
		}

		claimed = claim_manual_duplicate_order(database, "SO-1", "FP-1")

		self.assertTrue(claimed)
		database.set_value.assert_not_called()
		database.rollback.assert_called_once()

	def test_manual_order_claim_treats_serialization_conflicts_as_unclaimed(self):
		database = Mock()
		conflict = RuntimeError("serialization conflict")
		conflict.sqlstate = "40001"
		database.get_value.side_effect = conflict

		claimed = claim_manual_duplicate_order(database, "SO-1", "FP-1")

		self.assertFalse(claimed)
		database.rollback.assert_called_once()
		database.set_value.assert_not_called()

	def test_does_not_treat_a_draft_sales_order_as_a_registered_manual_order(self):
		match = find_manual_duplicate(partner_order(), [manual_order(docstatus=0)])

		self.assertIsNone(match)

	def test_does_not_match_when_partner_date_is_not_reliable(self):
		order = partner_order()
		order["manual_duplicate_date_checkable"] = False

		self.assertIsNone(find_manual_duplicate(order, [manual_order()]))

	def test_accepts_item_modifier_mapped_to_its_parent_item(self):
		match = find_manual_duplicate(
			partner_order(items=[
				{
					"qty": 2,
					"mapped_modifier": {
						"mapping_mode": "item_modifier",
						"parent_item_code": "BURGER",
					},
				},
				{"qty": 1, "mapped_item": {"item_code": "DRINK"}},
			]),
			[manual_order()],
		)

		self.assertEqual(match["name"], "SO-1")

	def test_ignores_a_mapped_addon_line_that_is_folded_into_its_parent(self):
		match = find_manual_duplicate(
			partner_order(items=[
				{"qty": 1, "mapped_item": {"item_code": "BURGER"}},
				{
					"qty": 1,
					"mapped_modifier": {
						"mapping_mode": "modifier",
						"parent_item_code": "BURGER",
					},
				},
			]),
			[manual_order(items=[{"item_code": "BURGER", "qty": 1}])],
		)

		self.assertEqual(match["name"], "SO-1")
		self.assertTrue(
			has_comparable_partner_items(
				partner_order(items=[
					{"qty": 1, "mapped_item": {"item_code": "BURGER"}},
					{"qty": 1, "mapped_modifier": {"mapping_mode": "modifier", "parent_item_code": "BURGER"}},
				])
			)
		)

	def test_reports_unmapped_partner_items_as_not_comparable(self):
		self.assertTrue(has_comparable_partner_items(partner_order()))
		self.assertFalse(
			has_comparable_partner_items(
				partner_order(items=[{"qty": 1, "title": "برگر", "mapped_item": None}])
			)
		)


if __name__ == "__main__":
	unittest.main()
