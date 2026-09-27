"""Pure discount selection helpers shared by Restaurant order channels."""


def _money(value):
	try:
		return round(max(float(value or 0), 0), 2)
	except (TypeError, ValueError):
		return 0.0


def select_order_discount(subtotal, group_percent=0, coach_percent=0, coupon_amount=0):
	"""Choose one valid discount and calculate coach cashback on the remaining items."""
	subtotal = _money(subtotal)
	group_amount = min(subtotal, _money(subtotal * max(float(group_percent or 0), 0) / 100))
	coach_amount = min(subtotal, _money(subtotal * max(float(coach_percent or 0), 0) / 100))
	coupon_amount = min(subtotal, _money(coupon_amount))
	candidates = [
		{"source": "customer_group", "amount": group_amount},
		{"source": "coach", "amount": coach_amount},
		{"source": "coupon", "amount": coupon_amount},
	]
	# max() preserves the first candidate on a tie: group, then coach, then coupon.
	winner = max(candidates, key=lambda candidate: candidate["amount"])
	net_items = max(subtotal - winner["amount"], 0)
	return {
		"subtotal": subtotal,
		"group_discount": group_amount,
		"coach_discount": coach_amount,
		"coupon_discount": coupon_amount,
		"discount_amount": winner["amount"],
		"discount_source": winner["source"] if winner["amount"] > 0 else "",
		"net_items": round(net_items, 2),
	}


def coach_commission_amount(net_items, commission_percent):
	return round(_money(net_items) * max(float(commission_percent or 0), 0) / 100, 2)


def allocate_return_amount_by_order(return_amount, source_order_amounts):
	"""Allocate an invoice return across linked orders by their returned-item basis."""
	amounts = {str(name): _money(value) for name, value in (source_order_amounts or {}).items() if name}
	total = sum(amounts.values())
	if total <= 0:
		return {}
	remaining = min(_money(return_amount), total)
	allocated = {}
	entries = [(name, value) for name, value in amounts.items() if value > 0]
	for index, (name, value) in enumerate(entries):
		part = remaining if index == len(entries) - 1 else min(value, round(min(_money(return_amount), total) * value / total, 2))
		part = min(part, value, remaining)
		allocated[name] = round(part, 2)
		remaining = round(remaining - part, 2)
	return allocated
