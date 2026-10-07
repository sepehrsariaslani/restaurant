"""Pure helpers for branch production routing and stock correction previews."""

from collections import defaultdict


_EDITABLE_ROUTING_FIELDS = (
	"is_active",
	"raw_warehouse",
	"kitchen_wip_warehouse",
	"finished_goods_warehouse",
)


def _inv_merge_branch_production_settings(current, patch):
	"""Merge only the settings fields intentionally exposed by the API."""
	current = current or {}
	patch = patch or {}
	result = dict(current)
	for key in _EDITABLE_ROUTING_FIELDS:
		if key in patch:
			result[key] = patch[key]
	return result


def _inv_branch_production_work_order_names(tickets, linked_work_orders, branch, company):
	"""Return submitted-work-order candidates linked to this company's branch tickets."""
	branch = str(branch or "DEFAULT").strip() or "DEFAULT"
	company = str(company or "").strip()
	matching_tickets = {
		str(ticket.get("name") or "").strip()
		for ticket in tickets or []
		if str(ticket.get("branch") or "DEFAULT").strip() == branch
		and str(ticket.get("company") or "").strip() == company
		and str(ticket.get("name") or "").strip()
	}
	work_order_names = {
		str(ticket.get("work_order") or "").strip()
		for ticket in tickets or []
		if str(ticket.get("branch") or "DEFAULT").strip() == branch
		and str(ticket.get("company") or "").strip() == company
		and str(ticket.get("work_order") or "").strip()
	}
	work_order_names.update(
		str(work_order.get("name") or "").strip()
		for work_order in linked_work_orders or []
		if str(work_order.get("restaurant_production_ticket") or "").strip() in matching_tickets
		and str(work_order.get("company") or "").strip() == company
		and int(work_order.get("docstatus") or 0) == 1
		and str(work_order.get("name") or "").strip()
	)
	return sorted(work_order_names)


def _inv_build_production_correction_rows(
	*, produced_warehouses, balances, item_uoms, item_names, store_balances, target_warehouse
):
	"""Build item/source rows, keeping UOMs separate and excluding non-positive bins."""
	rows = []
	for item_code, warehouses in (produced_warehouses or {}).items():
		for source_warehouse in warehouses or []:
			qty = float((balances or {}).get((item_code, source_warehouse), 0) or 0)
			if qty <= 0:
				continue
			stock_uom = str((item_uoms or {}).get(item_code) or "").strip()
			if not stock_uom:
				continue
			rows.append({
				"correction_key": f"{item_code}::{source_warehouse}",
				"item_code": item_code,
				"item_name": (item_names or {}).get(item_code) or item_code,
				"source_warehouse": source_warehouse,
				"target_warehouse": target_warehouse,
				"stock_uom": stock_uom,
				"transit_qty": qty,
				"store_qty": float((store_balances or {}).get(item_code, 0) or 0),
				"qty_to_transfer": qty,
			})
	return sorted(rows, key=lambda row: (row["item_code"], row["source_warehouse"]))


def _inv_summarize_correction_rows(rows):
	"""Aggregate only within the same stock UOM."""
	groups = defaultdict(lambda: {"stock_uom": "", "item_count": 0, "qty_to_transfer": 0.0})
	for row in rows or []:
		uom = str(row.get("stock_uom") or "").strip()
		if not uom:
			continue
		group = groups[uom]
		group["stock_uom"] = uom
		group["item_count"] += 1
		group["qty_to_transfer"] += float(row.get("qty_to_transfer") or 0)
	return [groups[uom] for uom in sorted(groups)]


def _inv_correction_rows_match(preview_rows, current_rows):
	"""Compare the exact stock snapshot, including UOM and both warehouse balances."""
	def snapshot(rows):
		return sorted(
			(
				str(row.get("item_code") or ""),
				str(row.get("source_warehouse") or ""),
				str(row.get("target_warehouse") or ""),
				str(row.get("stock_uom") or ""),
				round(float(row.get("transit_qty") or 0), 9),
				round(float(row.get("store_qty") or 0), 9),
				round(float(row.get("qty_to_transfer") or 0), 9),
			)
			for row in rows or []
		)

	return snapshot(preview_rows) == snapshot(current_rows)
