"""Idempotent coach cashback lifecycle for native ERPNext selling documents."""

import json

import frappe
from frappe import _
from frappe.utils import cint, flt

from restaurant.pricing_policy import allocate_return_amount_by_order


def _club():
	from restaurant import api_club

	api_club._club_ensure_ops_ready()
	return api_club


def _lock(doctype, name):
	frappe.db.sql("select name from `tab{0}` where name = %s for update".format(doctype), name)


def _coach_commission_txn_exists(api_club, reference_doctype, reference_name):
	return bool(frappe.db.exists(api_club.CLUB_DOCTYPES["wallet_txn"], {
		"reference_doctype": reference_doctype,
		"reference_name": reference_name,
		"kind": "کمیسیون مربی",
	}))


def _consume_recovery_due(api_club, wallet, coach, reference_doctype, reference_name):
	wallet_name = wallet.name if hasattr(wallet, "name") else wallet
	due = flt(frappe.db.get_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, "restaurant_coach_recovery_due") or 0)
	if due <= 0:
		return
	# The input may be the stale wallet object used by the immediately preceding
	# commission credit, so reload after that credit before recovering debt.
	wallet_doc = frappe.get_doc(api_club.CLUB_DOCTYPES["wallet"], wallet_name)
	available = flt(wallet_doc.get("cashback_balance") or 0)
	recovery = min(due, available)
	if recovery <= 0:
		return
	api_club._club_wallet_txn(
		wallet=wallet_doc,
		customer=coach,
		kind="بازگشت کمیسیون مربی",
		direction="برداشت",
		amount=recovery,
		bucket="کش‌بک",
		note=_("بازیابی اعتبار مرجوعی قبلی از سهم {0}").format(reference_name),
		reference_doctype=reference_doctype,
		reference_name=reference_name,
	)
	remaining = recovery
	for doctype in ("Sales Order", "Sales Invoice"):
		if not frappe.db.exists("DocType", doctype) or not frappe.db.has_column(doctype, "restaurant_coach_recovery_due"):
			continue
		rows = frappe.get_all(
			doctype,
			filters={"restaurant_coach_customer": coach, "restaurant_coach_recovery_due": [">", 0]},
			fields=["name", "restaurant_coach_recovery_due"],
			order_by="modified asc, name asc",
			limit_page_length=0,
			ignore_permissions=True,
		)
		for row in rows:
			if remaining <= 0.009:
				break
			applied = min(remaining, flt(row.restaurant_coach_recovery_due or 0))
			frappe.db.set_value(doctype, row.name, "restaurant_coach_recovery_due", max(flt(row.restaurant_coach_recovery_due or 0) - applied, 0), update_modified=False)
			remaining -= applied
	frappe.db.set_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, "restaurant_coach_recovery_due", max(due - recovery, 0), update_modified=False)


def _credit(api_club, doctype, name, customer, coach, amount):
	"""Credit once after eligibility was confirmed by the caller."""
	_lock(doctype, name)
	doc = frappe.get_doc(doctype, name)
	if doctype == "Sales Order":
		if doc.docstatus != 1 or not _order_delivered(doc) or not api_club.coach_payment_settled(name):
			return False
	elif doctype == "Sales Invoice":
		if doc.docstatus != 1 or cint(doc.get("is_return")) or not _invoice_fulfilled(doc) or flt(doc.get("outstanding_amount") or 0) > 0.01:
			return False
	current = {
		"customer": doc.get("customer"),
		"restaurant_coach_customer": doc.get("restaurant_coach_customer"),
		"restaurant_coach_commission_amount": doc.get("restaurant_coach_commission_amount"),
		"restaurant_coach_reversed_amount": doc.get("restaurant_coach_reversed_amount"),
		"restaurant_coach_credited": doc.get("restaurant_coach_credited"),
	}
	if not current or not current.get("restaurant_coach_customer"):
		return False
	if cint(current.get("restaurant_coach_credited") or 0) or _coach_commission_txn_exists(api_club, doctype, name):
		return False
	coach = current.get("restaurant_coach_customer")
	customer = current.get("customer")
	amount = max(
		flt(current.get("restaurant_coach_commission_amount") or 0)
		- flt(current.get("restaurant_coach_reversed_amount") or 0),
		0,
	)
	if amount <= 0:
		return False
	wallet = api_club._club_get_or_create_wallet(coach)
	api_club._club_wallet_txn(
		wallet=wallet,
		customer=coach,
		kind="کمیسیون مربی",
		direction="واریز",
		amount=amount,
		bucket="کش‌بک",
		note=_("سهم خرید شاگرد {0}").format(name),
		reference_doctype=doctype,
		reference_name=name,
	)
	_consume_recovery_due(api_club, wallet, coach, doctype, name)
	frappe.db.set_value(doctype, name, "restaurant_coach_credited", 1, update_modified=False)
	return True


def _reverse(api_club, doctype, name, coach, commission, previous, credited, target=None, note=None):
	_lock(doctype, name)
	current = frappe.db.get_value(doctype, name, ["restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
	if current:
		coach = current.restaurant_coach_customer
		commission = flt(current.restaurant_coach_commission_amount or 0)
		previous = flt(current.restaurant_coach_reversed_amount or 0)
		credited = current.restaurant_coach_credited
	if not coach or commission <= 0:
		return False
	target = min(commission, flt(target) if target is not None else commission)
	previous = flt(previous or 0)
	due = max(target - previous, 0)
	if due <= 0:
		return False
	was_credited = bool(cint(credited) or _coach_commission_txn_exists(api_club, doctype, name))
	# If cashback has not been granted, store the reduction so a later eligible
	# payout is smaller. Do not create a debt for money the coach never received.
	if not was_credited:
		frappe.db.set_value(doctype, name, "restaurant_coach_reversed_amount", previous + due, update_modified=False)
		return {"amount": due, "credited": False, "cashback_debit": 0.0, "recovery_due": 0.0}
	wallet = api_club._club_get_or_create_wallet(coach)
	wallet_name = wallet.name if hasattr(wallet, "name") else wallet
	wallet_doc = wallet if hasattr(wallet, "name") else frappe.get_doc(api_club.CLUB_DOCTYPES["wallet"], wallet_name)
	available = flt(wallet_doc.get("cashback_balance") or 0)
	debit = min(available, due)
	if debit > 0:
		api_club._club_wallet_txn(
			wallet=wallet,
			customer=coach,
			kind="بازگشت کمیسیون مربی",
			direction="برداشت",
			amount=debit,
			bucket="کش‌بک",
			note=note or _("برگشت سهم مربی بابت سند {0}").format(name),
			reference_doctype=doctype,
			reference_name=name,
		)
	remaining = due - debit
	if remaining > 0:
		field = "restaurant_coach_recovery_due"
		current_due = flt(frappe.db.get_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, field) or 0)
		frappe.db.set_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, field, current_due + remaining, update_modified=False)
		if frappe.db.has_column(doctype, field):
			current_source_due = flt(frappe.db.get_value(doctype, name, field) or 0)
			frappe.db.set_value(doctype, name, field, current_source_due + remaining, update_modified=False)
	frappe.db.set_value(doctype, name, "restaurant_coach_reversed_amount", previous + due, update_modified=False)
	return {"amount": due, "credited": True, "cashback_debit": debit, "recovery_due": remaining}


def _order_delivered(order):
	return bool(order and (order.get("restaurant_status") in {"delivered", "served"} or flt(order.get("per_delivered") or 0) >= 99.99))


def process_sales_order(name):
	api_club = _club()
	fields = ["customer", "restaurant_status", "per_delivered", "restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"]
	order = frappe.db.get_value("Sales Order", name, fields, as_dict=True)
	if not order or not _order_delivered(order) or not api_club.coach_payment_settled(name):
		return False
	amount = max(flt(order.get("restaurant_coach_commission_amount") or 0) - flt(order.get("restaurant_coach_reversed_amount") or 0), 0)
	return _credit(api_club, "Sales Order", name, order.customer, order.restaurant_coach_customer, amount)


def sales_order_on_update(doc, method=None):
	try:
		if doc.docstatus == 1:
			process_sales_order(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant coach Sales Order credit failed")


def sales_order_on_cancel(doc, method=None):
	try:
		reverse_sales_order(doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant coach Sales Order reversal failed")
		raise


def reverse_sales_order(name, amount=None, note=None):
	api_club = _club()
	_lock("Sales Order", name)
	row = frappe.db.get_value("Sales Order", name, ["restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
	if not row:
		return False
	target = min(flt(row.restaurant_coach_commission_amount or 0), flt(amount) if amount is not None else flt(row.restaurant_coach_commission_amount or 0))
	return bool(_reverse(api_club, "Sales Order", name, row.restaurant_coach_customer, row.restaurant_coach_commission_amount, row.restaurant_coach_reversed_amount, row.restaurant_coach_credited, target=target, note=note))


def _sales_order_links(invoice_name):
	if not frappe.db.exists("DocType", "Sales Invoice Item") or not frappe.db.has_column("Sales Invoice Item", "sales_order"):
		return []
	return sorted(set(frappe.get_all("Sales Invoice Item", filters={"parent": invoice_name, "sales_order": ["!=", ""]}, pluck="sales_order", limit_page_length=0, ignore_permissions=True)))


def _invoice_fulfilled(doc):
	if cint(doc.get("update_stock")) or cint(doc.get("is_pos")):
		return True
	return bool(frappe.get_all("Sales Invoice Item", filters={"parent": doc.name, "delivery_note": ["!=", ""]}, pluck="name", limit_page_length=1, ignore_permissions=True))


def _process_direct_invoice(api_club, doc):
	if doc.docstatus != 1 or cint(doc.get("is_return")) or not _invoice_fulfilled(doc) or flt(doc.get("outstanding_amount") or 0) > 0.01:
		return False
	if _sales_order_links(doc.name):
		return False
	amount = max(flt(doc.get("restaurant_coach_commission_amount") or 0) - flt(doc.get("restaurant_coach_reversed_amount") or 0), 0)
	return _credit(api_club, "Sales Invoice", doc.name, doc.customer, doc.get("restaurant_coach_customer"), amount)


def sales_invoice_on_update(doc, method=None):
	try:
		api_club = _club()
		if cint(doc.get("is_return")) and doc.docstatus == 1:
			_process_sales_invoice_return(api_club, doc)
			return
		orders = _sales_order_links(doc.name)
		if orders:
			for order_name in orders:
				process_sales_order(order_name)
		else:
			_process_direct_invoice(api_club, doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant coach Sales Invoice credit failed")


def _process_sales_invoice_return(api_club, doc):
	if not doc.get("return_against"):
		return
	if doc.get("restaurant_coach_return_reversal_json"):
		return
	reversal_entries = []
	returned_by_order = {}
	for row in doc.get("items") or []:
		if row.get("sales_order"):
			returned_by_order[row.sales_order] = returned_by_order.get(row.sales_order, 0) + abs(flt(row.get("net_amount") or row.get("amount") or 0))
	for order_name, returned_net in returned_by_order.items():
		order = frappe.db.get_value("Sales Order", order_name, ["net_total", "restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
		if not order or flt(order.net_total) <= 0:
			continue
		target = flt(order.restaurant_coach_commission_amount) * min(returned_net / flt(order.net_total), 1)
		result = _reverse(api_club, "Sales Order", order_name, order.restaurant_coach_customer, order.restaurant_coach_commission_amount, order.restaurant_coach_reversed_amount, order.restaurant_coach_credited, target=target)
		if result:
			reversal_entries.append({"doctype": "Sales Order", "name": order_name, **result})
	if returned_by_order:
		_save_return_reversal_snapshot(doc, reversal_entries)
		return
	original_name = doc.get("return_against")
	original_order_links = _sales_order_links(original_name)
	if original_order_links:
		original_items = frappe.get_all(
			"Sales Invoice Item",
			filters={"parent": original_name, "sales_order": ["in", original_order_links]},
			fields=["sales_order", "net_amount", "amount"],
			limit_page_length=0,
			ignore_permissions=True,
		)
		original_amounts_by_order = {}
		for row in original_items:
			order_name = row.get("sales_order")
			amount = abs(flt(row.get("net_amount") or row.get("amount") or 0))
			if order_name and amount > 0:
				original_amounts_by_order[order_name] = original_amounts_by_order.get(order_name, 0) + amount
		returned_net_by_order = allocate_return_amount_by_order(
			abs(flt(doc.get("net_total") or 0)), original_amounts_by_order
		)
		for order_name in original_order_links:
			order = frappe.db.get_value("Sales Order", order_name, ["net_total", "restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
			if not order or flt(order.net_total) <= 0:
				continue
			returned_net = flt(returned_net_by_order.get(order_name) or 0)
			if returned_net <= 0:
				continue
			target = flt(order.restaurant_coach_commission_amount) * min(returned_net / flt(order.net_total), 1)
			result = _reverse(api_club, "Sales Order", order_name, order.restaurant_coach_customer, order.restaurant_coach_commission_amount, order.restaurant_coach_reversed_amount, order.restaurant_coach_credited, target=target)
			if result:
				reversal_entries.append({"doctype": "Sales Order", "name": order_name, **result})
		_save_return_reversal_snapshot(doc, reversal_entries)
		return
	original = frappe.db.get_value("Sales Invoice", original_name, ["net_total", "restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
	if not original or flt(original.net_total) <= 0:
		return
	returned_net = abs(flt(doc.get("net_total") or 0))
	target = flt(original.restaurant_coach_commission_amount) * min(returned_net / flt(original.net_total), 1)
	result = _reverse(api_club, "Sales Invoice", original_name, original.restaurant_coach_customer, original.restaurant_coach_commission_amount, original.restaurant_coach_reversed_amount, original.restaurant_coach_credited, target=target)
	if result:
		reversal_entries.append({"doctype": "Sales Invoice", "name": original_name, **result})
	_save_return_reversal_snapshot(doc, reversal_entries)


def _save_return_reversal_snapshot(doc, entries):
	if entries and frappe.db.has_column("Sales Invoice", "restaurant_coach_return_reversal_json"):
		frappe.db.set_value(
			"Sales Invoice",
			doc.name,
			"restaurant_coach_return_reversal_json",
			json.dumps(entries, ensure_ascii=False),
			update_modified=False,
		)


def _restore_sales_invoice_return(api_club, doc):
	"""Compensate a return's coach commission reversal if that return is cancelled."""
	if not frappe.db.has_column("Sales Invoice", "restaurant_coach_return_reversal_reinstated"):
		return False
	if cint(doc.get("restaurant_coach_return_reversal_reinstated")):
		return False
	try:
		entries = json.loads(doc.get("restaurant_coach_return_reversal_json") or "[]")
	except (TypeError, ValueError):
		entries = []
	if not isinstance(entries, list) or not entries:
		frappe.db.set_value("Sales Invoice", doc.name, "restaurant_coach_return_reversal_reinstated", 1, update_modified=False)
		return False
	for entry in entries:
		doctype = entry.get("doctype")
		name = entry.get("name")
		if doctype not in {"Sales Order", "Sales Invoice"} or not name or not frappe.db.exists(doctype, name):
			continue
		_lock(doctype, name)
		fields = ["restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"]
		if frappe.db.has_column(doctype, "restaurant_coach_recovery_due"):
			fields.append("restaurant_coach_recovery_due")
		origin = frappe.db.get_value(doctype, name, fields, as_dict=True)
		if not origin:
			continue
		amount = min(flt(entry.get("amount") or 0), flt(origin.restaurant_coach_reversed_amount or 0))
		if amount <= 0:
			continue
		frappe.db.set_value(doctype, name, "restaurant_coach_reversed_amount", max(flt(origin.restaurant_coach_reversed_amount or 0) - amount, 0), update_modified=False)
		was_credited = cint(origin.restaurant_coach_credited or 0) or _coach_commission_txn_exists(api_club, doctype, name)
		if not entry.get("credited") or not was_credited or not origin.restaurant_coach_customer:
			continue
		entry_due = min(flt(entry.get("recovery_due") or 0), amount)
		origin_due = min(flt(origin.get("restaurant_coach_recovery_due") or 0), entry_due)
		if origin_due > 0:
			frappe.db.set_value(doctype, name, "restaurant_coach_recovery_due", max(flt(origin.restaurant_coach_recovery_due or 0) - origin_due, 0), update_modified=False)
			wallet_doc = api_club._club_get_or_create_wallet(origin.restaurant_coach_customer)
			wallet_name = wallet_doc.name
			wallet_due = flt(frappe.db.get_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, "restaurant_coach_recovery_due") or 0)
			frappe.db.set_value(api_club.CLUB_DOCTYPES["wallet"], wallet_name, "restaurant_coach_recovery_due", max(wallet_due - origin_due, 0), update_modified=False)
		already_recovered = max(entry_due - origin_due, 0)
		refund = min(amount, flt(entry.get("cashback_debit") or 0) + already_recovered)
		if refund > 0:
			wallet_doc = api_club._club_get_or_create_wallet(origin.restaurant_coach_customer)
			api_club._club_wallet_txn(
				wallet=wallet_doc,
				customer=origin.restaurant_coach_customer,
				kind="کمیسیون مربی",
				direction="واریز",
				amount=refund,
				bucket="کش‌بک",
				note=_("بازگشت سهم مربی پس از لغو مرجوعی {0}").format(doc.name),
				reference_doctype="Sales Invoice",
				reference_name=doc.name,
			)
	frappe.db.set_value("Sales Invoice", doc.name, "restaurant_coach_return_reversal_reinstated", 1, update_modified=False)
	return True


def sales_invoice_on_cancel(doc, method=None):
	try:
		api_club = _club()
		if cint(doc.get("is_return")):
			_restore_sales_invoice_return(api_club, doc)
			return
		orders = _sales_order_links(doc.name)
		for order_name in orders:
			was_credited = cint(frappe.db.get_value("Sales Order", order_name, "restaurant_coach_credited") or 0) or _coach_commission_txn_exists(api_club, "Sales Order", order_name)
			if not api_club.coach_payment_settled(order_name) and was_credited:
				reverse_sales_order(order_name, note=_("فاکتور {0} لغو شد و سفارش دیگر تسویه نیست.").format(doc.name))
		if not orders:
			row = frappe.db.get_value("Sales Invoice", doc.name, ["restaurant_coach_customer", "restaurant_coach_commission_amount", "restaurant_coach_reversed_amount", "restaurant_coach_credited"], as_dict=True)
			if row:
				_reverse(api_club, "Sales Invoice", doc.name, row.restaurant_coach_customer, row.restaurant_coach_commission_amount, row.restaurant_coach_reversed_amount, row.restaurant_coach_credited)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant coach Sales Invoice reversal failed")
		raise


def process_pending_coach_rewards():
	"""Catch order/invoice settlements delivered through payment-entry DB updates."""
	api_club = _club()
	credited = 0
	if frappe.db.exists("DocType", "Sales Order") and frappe.db.has_column("Sales Order", "restaurant_coach_customer"):
		order_names = frappe.get_all("Sales Order", filters={"docstatus": 1, "restaurant_coach_customer": ["!=", ""], "restaurant_coach_credited": 0}, pluck="name", limit_page_length=1000, ignore_permissions=True)
		for name in order_names:
			try:
				credited += bool(process_sales_order(name))
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Restaurant coach order settlement failed: {0}".format(name))
	if frappe.db.exists("DocType", "Sales Invoice") and frappe.db.has_column("Sales Invoice", "restaurant_coach_customer"):
		invoice_names = frappe.get_all("Sales Invoice", filters={"docstatus": 1, "is_return": 0, "restaurant_coach_customer": ["!=", ""], "restaurant_coach_credited": 0}, pluck="name", limit_page_length=1000, ignore_permissions=True)
		for name in invoice_names:
			try:
				doc = frappe.get_doc("Sales Invoice", name)
				orders = _sales_order_links(name)
				if orders:
					for order_name in orders:
						credited += bool(process_sales_order(order_name))
				elif _process_direct_invoice(api_club, doc):
					credited += 1
			except Exception:
				frappe.log_error(frappe.get_traceback(), "Restaurant coach invoice settlement failed: {0}".format(name))
	return credited
