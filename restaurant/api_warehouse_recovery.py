"""Reviewed, resumable warehouse history repair for restaurant operations.

The preview is read-only. Submitted stock documents are changed only by native
cancel/amend/submit calls; unsupported dependencies remain visible as blockers.
"""

from __future__ import annotations

import hashlib
import json
import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, now_datetime

from restaurant.api import _ensure_management_access


RUN_DOCTYPE = "Restaurant Warehouse Recovery Run"
ROW_DOCTYPE = "Restaurant Warehouse Recovery Row"
RUN_CACHE_PREFIX = "restaurant-warehouse-recovery-preview:"
PREVIEW_TTL_SECONDS = 3600
BATCH_SIZE = 25
SOURCE_WAREHOUSE_LABEL = "کالاها در ترانزیت - V"
TARGET_WAREHOUSE_LABEL = "فروشگاه - V"

# Only vouchers with a known stock-warehouse field map use the automatic native
# amendment path. Other voucher types are listed as blockers in the preview.
WAREHOUSE_MAPS = {
	"Work Order": {
		"parents": ("source_warehouse", "wip_warehouse", "fg_warehouse"),
		"tables": {},
	},
	"Stock Entry": {
		"parents": ("from_warehouse", "to_warehouse"),
		"tables": {"items": ("s_warehouse", "t_warehouse")},
	},
	"Delivery Note": {"parents": (), "tables": {"items": ("warehouse",)}},
	"Purchase Receipt": {"parents": (), "tables": {"items": ("warehouse",)}},
	"Stock Reconciliation": {"parents": (), "tables": {"items": ("warehouse",)}},
}

ITEM_REFERENCE_DOCTYPES = (
	("Delivery Note Item", "Delivery Note"),
	("Sales Invoice Item", "Sales Invoice"),
	("POS Invoice Item", "POS Invoice"),
	("Purchase Receipt Item", "Purchase Receipt"),
	("Purchase Invoice Item", "Purchase Invoice"),
	("Stock Entry Detail", "Stock Entry"),
	("Stock Reconciliation Item", "Stock Reconciliation"),
	("Sales Order Item", "Sales Order"),
	("Purchase Order Item", "Purchase Order"),
	("Material Request Item", "Material Request"),
	("Product Bundle", "Product Bundle"),
	("BOM", "BOM"),
)


def _json(value):
	return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def _parse_json(value, fallback=None):
	if not value:
		return fallback if fallback is not None else {}
	try:
		return json.loads(value) if isinstance(value, str) else value
	except (TypeError, ValueError):
		return fallback if fallback is not None else {}


def _warehouse_name(label, company):
	if frappe.db.exists("Warehouse", label):
		name = label
	else:
		name = frappe.db.get_value("Warehouse", {"warehouse_name": label, "company": company}, "name")
	if not name:
		frappe.throw(_("انبار «{0}» در شرکت انتخاب‌شده پیدا نشد.").format(label))
	row = frappe.db.get_value("Warehouse", name, ["company", "disabled", "is_group"], as_dict=True)
	if not row or row.company != company or cint(row.is_group):
		frappe.throw(_("انبار «{0}» برای این شرکت معتبر نیست.").format(name))
	if name != label and cint(row.disabled):
		frappe.throw(_("انبار «{0}» غیرفعال است.").format(name))
	return name


def _resolve_scope(branch="DEFAULT"):
	from restaurant.api_inventory import _inv_get_production_settings_doc

	branch = str(branch or "DEFAULT").strip() or "DEFAULT"
	settings = _inv_get_production_settings_doc(branch, require_active=True)
	company = settings.company
	source = _warehouse_name(SOURCE_WAREHOUSE_LABEL, company)
	target = _warehouse_name(TARGET_WAREHOUSE_LABEL, company)
	if source == target:
		frappe.throw(_("انبار مبدأ و مقصد یکی هستند؛ پیش‌نمایش ساخته نشد."))
	return settings, source, target


def _warehouse_changes(doc, source, target):
	meta = frappe.get_meta(doc.doctype)
	config = WAREHOUSE_MAPS.get(doc.doctype)
	if not config:
		return [], _("این نوع سند در مسیر بازثبت ایمن پشتیبانی نشده است.")
	if not meta.has_field("amended_from"):
		return [], _("این نوع سند امکان اصلاح بومی با amended_from ندارد.")
	changes = []
	for fieldname in config["parents"]:
		if meta.has_field(fieldname) and doc.get(fieldname) == source:
			changes.append({"path": f"parent:{fieldname}", "from": source, "to": target})
	for table_field, warehouse_fields in config["tables"].items():
		if not meta.has_field(table_field):
			continue
		for index, row in enumerate(doc.get(table_field) or [], start=1):
			for fieldname in warehouse_fields:
				if row.get(fieldname) == source:
					changes.append({
						"path": f"table:{table_field}:{index}:{fieldname}",
						"from": source,
						"to": target,
					})
	if not changes:
		return [], _("ردیف سند به انبار مبدأ وصل نیست.")
	if doc.doctype == "Stock Entry":
		items = doc.get("items") or []
		collapsed = 0
		for row in items:
			source_wh = target if row.get("s_warehouse") == source else row.get("s_warehouse")
			target_wh = target if row.get("t_warehouse") == source else row.get("t_warehouse")
			if source_wh and target_wh and source_wh == target_wh:
				collapsed += 1
		if collapsed and collapsed != len(items):
			return [], _("بخشی از ردیف‌های انتقال پس از ادغام به انتقال از انبار به خودش تبدیل می‌شوند؛ سند به بررسی دستی نیاز دارد.")
		if collapsed and (doc.get("purpose") or doc.get("stock_entry_type")) not in {
			"Material Transfer",
			"Material Transfer for Manufacture",
		}:
			return [], _("این سند پس از ادغام انبارها ردیف انتقال از انبار به خودش خواهد داشت.")
	return changes, ""


def _document_dependency_blocker(doc, check_work_order_entries=True):
	if cint(doc.docstatus) != 1:
		return _("سند مبدأ دیگر در وضعیت ثبت‌شده نیست.")
	if cint(doc.get("is_return")) or doc.get("return_against"):
		return _("سند به برگشت کالا مربوط است و زنجیرهٔ برگشت باید جداگانه بررسی شود.")
	if doc.doctype == "Delivery Note":
		invoice_item_meta = frappe.get_meta("Sales Invoice Item")
		linked = []
		if invoice_item_meta.has_field("delivery_note"):
			linked = frappe.db.sql(
				"""select distinct sii.parent
					from `tabSales Invoice Item` sii
					join `tabSales Invoice` si on si.name = sii.parent
					where sii.delivery_note = %s and si.docstatus != 2 limit 20""",
				doc.name,
				as_dict=True,
			)
		if not linked and invoice_item_meta.has_field("dn_detail"):
			dn_rows = frappe.get_all("Delivery Note Item", filters={"parent": doc.name}, fields=["name"], limit_page_length=10000, ignore_permissions=True)
			if dn_rows:
				linked = frappe.db.sql(
					"""select distinct sii.parent
						from `tabSales Invoice Item` sii
						join `tabSales Invoice` si on si.name = sii.parent
						where sii.dn_detail in %s and si.docstatus != 2 limit 20""",
					(tuple(row.name for row in dn_rows),),
					as_dict=True,
				)
		if linked:
			return _("فاکتور فروش ثبت‌شده به این رسید وصل است: {0}").format(", ".join(sorted({r.parent for r in linked}))
		)
	if doc.doctype == "Purchase Receipt":
		pr_rows = frappe.get_all("Purchase Receipt Item", filters={"parent": doc.name}, fields=["name"], limit_page_length=10000, ignore_permissions=True)
		if pr_rows and frappe.get_meta("Purchase Invoice Item").has_field("pr_detail"):
			linked = frappe.db.sql(
				"""select distinct pii.parent
					from `tabPurchase Invoice Item` pii
					join `tabPurchase Invoice` pi on pi.name = pii.parent
					where pii.pr_detail in %s and pi.docstatus != 2 limit 20""",
				(tuple(row.name for row in pr_rows),),
				as_dict=True,
			)
			if linked:
				return _("فاکتور خرید ثبت‌شده به این رسید وصل است: {0}").format(", ".join(sorted({r.parent for r in linked}))
			)
	if doc.doctype == "Work Order" and check_work_order_entries:
		active_entries = frappe.get_all(
			"Stock Entry",
			filters={"work_order": doc.name, "docstatus": 1},
			fields=["name"],
			limit_page_length=20,
			ignore_permissions=True,
		)
		if active_entries:
			return _("ابتدا اسناد انبار متصل به دستور تولید باید اصلاح شوند: {0}").format(", ".join(row.name for row in active_entries))
	return ""


def _active_source_sle(company, source):
	return frappe.db.sql(
		"""select name, voucher_type, voucher_no, voucher_detail_no, item_code,
			actual_qty, qty_after_transaction, posting_date, posting_time, company,
			warehouse, creation
			from `tabStock Ledger Entry`
			where company = %s and warehouse = %s and is_cancelled = 0
			order by posting_date asc, posting_time asc, creation asc, name asc""",
		(company, source),
		as_dict=True,
	)


def _item_reference_counts(item_code):
	counts = {}
	for child_doctype, parent_doctype in ITEM_REFERENCE_DOCTYPES:
		if not frappe.db.exists("DocType", child_doctype) or not frappe.db.exists("DocType", parent_doctype):
			continue
		meta = frappe.get_meta(child_doctype)
		if child_doctype == parent_doctype:
			reference_field = {
				"Product Bundle": "new_item_code",
				"BOM": "item",
			}.get(child_doctype, "item_code")
			if not meta.has_field(reference_field):
				continue
			filters = {reference_field: item_code}
			if meta.has_field("docstatus") or child_doctype == "BOM":
				filters["docstatus"] = 1
			count = frappe.db.count(child_doctype, filters)
			if count:
				counts[child_doctype] = cint(count)
			continue
		if not meta.istable or not meta.has_field("item_code"):
			continue
		parent_meta = frappe.get_meta(parent_doctype)
		# Frappe's standard child-table columns (parent, parenttype, parentfield)
		# are present in SQL but are not declared as DocField metadata.
		if parent_meta.istable:
			continue
		parent_table = "tab" + parent_doctype.replace("`", "")
		child_table = "tab" + child_doctype.replace("`", "")
		count = frappe.db.sql(
			f"select count(*) from `{child_table}` c join `{parent_table}` p on p.name = c.parent where c.item_code = %s and p.docstatus = 1",
			item_code,
		)[0][0]
		if count:
			counts[child_doctype] = cint(count)
	return counts


def _pending_order_rows(company):
	if not frappe.db.exists("DocType", "Sales Order Item"):
		return [], []
	branch_select = "item.restaurant_branch" if frappe.get_meta("Item").has_field("restaurant_branch") else "'DEFAULT' as restaurant_branch"
	rows = frappe.db.sql(
		f"""select so.name as sales_order, so.customer, so.company, so.transaction_date,
			so.status, soi.name as sales_order_item, soi.item_code, soi.item_name,
			soi.qty, soi.delivered_qty, item.is_stock_item, item.stock_uom,
			{branch_select}
			from `tabSales Order` so
			join `tabSales Order Item` soi on soi.parent = so.name
			left join `tabItem` item on item.name = soi.item_code
			where so.company = %s and so.docstatus = 1
				and so.status not in ('Closed', 'Cancelled')
				and ifnull(soi.qty, 0) > ifnull(soi.delivered_qty, 0)
			order by so.transaction_date asc, so.name asc, soi.idx asc""",
		company,
		as_dict=True,
	)
	by_order = {}
	misclassified = {}
	for row in rows:
		if not row.item_code or not cint(row.is_stock_item):
			if row.item_code:
				misclassified.setdefault(row.item_code, []).append(row)
			continue
		by_order.setdefault(row.sales_order, []).append(row)

	from restaurant.order_review import require_order_approved

	order_rows = []
	for order_name, lines in by_order.items():
		try:
			require_order_approved(order_name)
		except Exception:
			continue
		order_rows.append({
			"doctype": "Sales Order",
			"name": order_name,
			"action": "Repair Sales Order",
			"customer": lines[0].customer,
			"posting_date": lines[0].transaction_date,
			"item_count": len(lines),
			"pending_qty": sum(flt(line.qty) - flt(line.delivered_qty) for line in lines),
			"items": [
				{
					"sales_order_item": line.sales_order_item,
					"item_code": line.item_code,
					"item_name": line.item_name,
					"pending_qty": flt(line.qty) - flt(line.delivered_qty),
					"stock_uom": line.stock_uom,
					"branch": line.restaurant_branch or "DEFAULT",
				}
				for line in lines
			],
		})

	classification_rows = []
	for item_code, lines in sorted(misclassified.items()):
		item_name = frappe.db.get_value("Item", item_code, "item_name") or item_code
		refs = _item_reference_counts(item_code)
		bom_count = frappe.db.count("BOM", {"item": item_code, "docstatus": 1}) if frappe.db.exists("DocType", "BOM") else 0
		classification_rows.append({
			"doctype": "Item",
			"name": item_code,
			"action": "Item Classification",
			"item_name": item_name,
			"pending_sales_order_count": len({line.sales_order for line in lines}),
			"submitted_bom_count": bom_count,
			"references": refs,
			"reason": _("این قلم برای فروش به‌صورت غیرانبارشونده ثبت شده، اما در سفارش‌های باز/تأییدشده استفاده شده است. تغییر طبقه‌بندی به وابستگی‌های ثبت‌شدهٔ زیر می‌رسد و از این اجرای خودکار خارج است."),
		})
	return order_rows, classification_rows


def _operational_references(company, source):
	refs = []
	for doctype, fieldname in (
		("Work Order", "fg_warehouse"),
		("Work Order", "source_warehouse"),
		("Work Order", "wip_warehouse"),
		("Restaurant Production Ticket", "fg_warehouse"),
		("Restaurant Branch Production Settings", "raw_warehouse"),
		("Restaurant Branch Production Settings", "kitchen_wip_warehouse"),
		("Restaurant Branch Production Settings", "finished_goods_warehouse"),
		("Item Default", "default_warehouse"),
	):
		if not frappe.db.exists("DocType", doctype) or not frappe.get_meta(doctype).has_field(fieldname):
			continue
		filters = {fieldname: source}
		if frappe.get_meta(doctype).has_field("company"):
			filters["company"] = company
		# docstatus is a standard column on Work Order even though it is not an
		# explicit DocField in its metadata.
		if frappe.get_meta(doctype).has_field("docstatus") or doctype == "Work Order":
			filters["docstatus"] = ["!=", 2]
		rows = frappe.get_all(doctype, filters=filters, fields=["name"], limit_page_length=100000, ignore_permissions=True)
		for row in rows:
			refs.append({"doctype": doctype, "name": row.name, "field": fieldname})
	return refs


def _build_snapshot(branch="DEFAULT"):
	settings, source, target = _resolve_scope(branch)
	company = settings.company
	sle_rows = _active_source_sle(company, source)
	sle_by_voucher = {}
	for sle in sle_rows:
		key = (sle.voucher_type, sle.voucher_no)
		group = sle_by_voucher.setdefault(key, {"count": 0, "qty": 0.0, "item_codes": set()})
		group["count"] += 1
		group["qty"] += flt(sle.actual_qty)
		if sle.item_code:
			group["item_codes"].add(sle.item_code)
	voucher_key_set = {(row.voucher_type, row.voucher_no) for row in sle_rows}
	work_order_filters = {"company": company, "docstatus": 1}
	work_order_or_filters = [
		{"fg_warehouse": source},
		{"source_warehouse": source},
		{"wip_warehouse": source},
	]
	if frappe.db.exists("DocType", "Work Order"):
		for work_order in frappe.get_all(
			"Work Order",
			filters=work_order_filters,
			or_filters=work_order_or_filters,
			fields=["name"],
			limit_page_length=100000,
			ignore_permissions=True,
		):
			voucher_key_set.add(("Work Order", work_order.name))
	voucher_keys = sorted(voucher_key_set)
	voucher_rows = []
	blockers = []
	for doctype, name in voucher_keys:
		try:
			doc = frappe.get_doc(doctype, name)
		except frappe.DoesNotExistError:
			blockers.append({"doctype": doctype, "name": name, "action": "Blocked", "reason": _("سند اصلی در سیستم پیدا نشد."), "state": "Blocked"})
			continue
		changes, reason = _warehouse_changes(doc, source, target)
		dependency_reason = _document_dependency_blocker(
			doc,
			check_work_order_entries=(doctype != "Work Order"),
		)
		reason = dependency_reason or reason
		eligible = bool(changes) and not reason
		row = {
			"doctype": doctype,
			"name": name,
			"action": "Amend Voucher" if eligible else "Blocked",
			"state": "Previewed" if eligible else "Blocked",
			"posting_date": str(doc.get("posting_date") or ""),
			"posting_time": str(doc.get("posting_time") or ""),
			"modified": str(doc.modified or ""),
			"docstatus": cint(doc.docstatus),
			"warehouse_changes": changes,
			"reason": reason,
			"sle_count": sle_by_voucher.get((doctype, name), {}).get("count", 0),
			"item_codes": sorted(sle_by_voucher.get((doctype, name), {}).get("item_codes", set())),
		}
		if doctype == "Stock Entry" and changes:
			items = doc.get("items") or []
			collapsed = all(
				(target if row.get("s_warehouse") == source else row.get("s_warehouse"))
				and (target if row.get("t_warehouse") == source else row.get("t_warehouse"))
				and (target if row.get("s_warehouse") == source else row.get("s_warehouse"))
				== (target if row.get("t_warehouse") == source else row.get("t_warehouse"))
				for row in items
			)
			row["cancel_only"] = bool(collapsed)
		row.update({
			"document_name": name,
			"source_warehouse": source,
			"target_warehouse": target,
			"original_posting_date": row.get("posting_date") or "",
			"original_posting_time": row.get("posting_time") or "",
			"proposed_posting_date": row.get("posting_date") or "",
			"proposed_posting_time": row.get("posting_time") or "",
			"qty": sle_by_voucher.get((doctype, name), {}).get("qty", 0.0),
		})
		voucher_rows.append(row)
		if not eligible:
			blockers.append({**row, "reason": reason or _("سند واجد شرایط بازثبت نبود.")})

	eligible_vouchers = {
		(row["doctype"], row["name"])
		for row in voucher_rows
		if row["action"] == "Amend Voucher"
	}
	eligible_work_order_rows = [
		row for row in voucher_rows
		if row["doctype"] == "Work Order" and row["action"] == "Amend Voucher"
	]
	active_entries_by_work_order = {}
	if eligible_work_order_rows:
		active_entries = frappe.get_all(
			"Stock Entry",
			filters={"work_order": ["in", [row["name"] for row in eligible_work_order_rows]], "docstatus": 1},
			fields=["name", "work_order"],
			limit_page_length=100000,
			ignore_permissions=True,
		)
		for entry in active_entries:
			active_entries_by_work_order.setdefault(entry.work_order, []).append(entry.name)
	for row in eligible_work_order_rows:
		uncovered = [
			name for name in active_entries_by_work_order.get(row["name"], [])
			if ("Stock Entry", name) not in eligible_vouchers
		]
		if uncovered:
			row["action"] = "Blocked"
			row["state"] = "Blocked"
			row["reason"] = _("دستور تولید اسناد انبار ثبت‌شده‌ای دارد که در این پیش‌نمایش اصلاح‌پذیر نیستند: {0}").format(", ".join(uncovered[:20]))
			blockers.append({**row, "reason": row["reason"]})

	order_rows, classification_rows = _pending_order_rows(company)
	for row in order_rows:
		row.update({
			"document_name": row["name"],
			"source_warehouse": source,
			"target_warehouse": target,
			"original_posting_date": str(row.get("posting_date") or ""),
			"proposed_posting_date": "",
			"proposed_posting_time": "",
		})
	for row in classification_rows:
		row["document_name"] = row["name"]
		row["source_warehouse"] = source
		row["target_warehouse"] = target
		row["original_posting_date"] = ""
		row["proposed_posting_date"] = ""
		blockers.append({**row, "state": "Blocked"})
	operational_refs = _operational_references(company, source)
	configuration_rows = []
	pending_order_items = {
		item.get("sales_order_item")
		for order in order_rows
		for item in (order.get("items") or [])
		if item.get("sales_order_item")
	}
	for ref in operational_refs:
		if ref["doctype"] not in {"Restaurant Branch Production Settings", "Item Default"}:
			continue
		configuration_name = ref["name"]
		configuration_doctype = ref["doctype"]
		if configuration_doctype == "Item Default":
			configuration_name = frappe.db.get_value("Item Default", ref["name"], "parent") or ref["name"]
			configuration_doctype = "Item"
		configuration_rows.append({
			"doctype": configuration_doctype,
			"name": configuration_name,
			"document_name": configuration_name,
			"action": "Update Settings",
			"state": "Previewed",
			"source_warehouse": source,
			"target_warehouse": target,
			"reason": _("تنظیم پیش‌فرض انبار پس از بازبینی به انبار فروشگاه تغییر می‌کند."),
			"original_warehouse_json": [{"field": ref["field"], "from": source, "to": target}],
		})
	ticket_configuration_names = set()
	for ref in operational_refs:
		if ref["doctype"] != "Restaurant Production Ticket" or ref["name"] in ticket_configuration_names:
			continue
		ticket = frappe.get_doc("Restaurant Production Ticket", ref["name"])
		if (ticket.get("work_order") or "").strip():
			continue
		warehouse_changes = [
			{"field": fieldname, "from": source, "to": target}
			for fieldname in ("source_warehouse", "wip_warehouse", "fg_warehouse")
			if ticket.get(fieldname) == source
		]
		if not warehouse_changes:
			continue
		ticket_configuration_names.add(ticket.name)
		configuration_rows.append({
			"doctype": "Restaurant Production Ticket",
			"name": ticket.name,
			"document_name": ticket.name,
			"action": "Update Production Ticket",
			"state": "Previewed",
			"source_warehouse": source,
			"target_warehouse": target,
			"modified": str(ticket.modified or ""),
			"original_warehouse_json": warehouse_changes,
			"reason": _("تیکت تولید بدون دستور تولید است؛ فقط انبارهای مسیر آن به فروشگاه تغییر می‌کنند."),
		})
	stock_default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse") or ""
	if stock_default_warehouse != target:
		configuration_rows.append({
			"doctype": "Stock Settings",
			"name": "Stock Settings",
			"document_name": "Stock Settings",
			"action": "Update Settings",
			"state": "Previewed",
			"source_warehouse": stock_default_warehouse or source,
			"target_warehouse": target,
			"reason": _("انبار پیش‌فرض سیستم پس از بازبینی روی انبار فروشگاه تنظیم می‌شود."),
			"original_warehouse_json": [{"field": "default_warehouse", "from": stock_default_warehouse, "to": target}],
		})
	restaurant_settings_meta = frappe.get_meta("Restaurant Web Settings")
	if restaurant_settings_meta.has_field("restaurant_inventory_default_warehouse"):
		restaurant_default_warehouse = (
			frappe.db.get_single_value("Restaurant Web Settings", "restaurant_inventory_default_warehouse") or ""
		)
		if restaurant_default_warehouse != target:
			configuration_rows.append({
				"doctype": "Restaurant Web Settings",
				"name": "Restaurant Web Settings",
				"document_name": "Restaurant Web Settings",
				"action": "Update Settings",
				"state": "Previewed",
				"source_warehouse": restaurant_default_warehouse or source,
				"target_warehouse": target,
				"reason": _("انبار پیش‌فرض ماژول موجودی رستوران روی انبار فروشگاه تنظیم می‌شود."),
				"original_warehouse_json": [{
					"field": "restaurant_inventory_default_warehouse",
					"from": restaurant_default_warehouse,
					"to": target,
				}],
			})
	eligible_work_orders = {
		row["name"] for row in voucher_rows
		if row["doctype"] == "Work Order" and row["action"] == "Amend Voucher"
	}
	for ref in operational_refs:
		if ref["doctype"] in {"Restaurant Branch Production Settings", "Item Default"}:
			continue
		if ref["doctype"] == "Work Order" and ref["name"] in eligible_work_orders:
			continue
		if ref["doctype"] == "Restaurant Production Ticket":
			if ref["name"] in ticket_configuration_names:
				continue
			ticket = frappe.db.get_value(
				"Restaurant Production Ticket",
				ref["name"],
				["work_order", "sales_order_item", "status"],
				as_dict=True,
			)
			work_order = ticket.work_order if ticket else ""
			if work_order in eligible_work_orders:
				continue
			if (
				ticket
				and not work_order
				and (ticket.status or "").lower() == "planned"
				and ticket.sales_order_item in pending_order_items
			):
				# The linked approved order repair creates the missing Work Order
				# before attempting its stock movements and Delivery Note.
				continue
		blockers.append({
			"doctype": ref["doctype"],
			"name": ref["name"],
			"action": "Informational",
			"state": "Blocked",
			"reason": _("این سند یا دستور تولید هنوز به انبار ترانزیت اشاره می‌کند و در این اجرا اصلاح مستقیم نمی‌شود."),
		})

	settings_snapshot = {
		"branch": settings.branch,
		"company": company,
		"raw_warehouse": settings.raw_warehouse,
		"kitchen_wip_warehouse": settings.kitchen_wip_warehouse,
		"finished_goods_warehouse": settings.finished_goods_warehouse,
	}
	sle_snapshot = [
		{
			"name": row.name,
			"voucher_type": row.voucher_type,
			"voucher_no": row.voucher_no,
			"voucher_detail_no": row.voucher_detail_no,
			"item_code": row.item_code,
			"actual_qty": str(row.actual_qty),
			"qty_after_transaction": str(row.qty_after_transaction),
			"posting_date": str(row.posting_date),
			"posting_time": str(row.posting_time),
			"modified": str(row.creation),
		}
		for row in sle_rows
	]
	snapshot = {
		"company": company,
		"branch": settings.branch,
		"source_warehouse": source,
		"target_warehouse": target,
		"settings": settings_snapshot,
		"stock_ledger_entries": sle_snapshot,
		"vouchers": voucher_rows,
		"sales_orders": order_rows,
		"item_classification": classification_rows,
		"configuration_rows": configuration_rows,
		"operational_references": operational_refs,
	}
	fingerprint = hashlib.sha256(_json(snapshot).encode("utf-8")).hexdigest()
	return {
		**snapshot,
		"fingerprint": fingerprint,
		"blockers": blockers,
		"summary": {
			"total_rows": len(voucher_rows) + len(order_rows) + len(classification_rows) + len(configuration_rows),
			"total_documents": len(voucher_rows),
			"eligible_rows": sum(1 for row in voucher_rows if row["action"] == "Amend Voucher") + len(order_rows) + len(configuration_rows),
			"blocked_rows": len(blockers),
			"production_documents": sum(1 for row in voucher_rows if row["doctype"] == "Work Order"),
			"missing_delivery_notes": len(order_rows),
			"item_type_corrections": len(classification_rows),
			"stock_ledger_rows": len(sle_rows),
			"vouchers": len(voucher_rows),
			"eligible_vouchers": sum(1 for row in voucher_rows if row["action"] == "Amend Voucher"),
			"blocked_vouchers": sum(1 for row in voucher_rows if row["action"] == "Blocked"),
			"pending_sales_orders": len(order_rows),
			"misclassified_items": len(classification_rows),
			"production_ticket_routes": len(ticket_configuration_names),
			"operational_references": len(operational_refs),
			"blockers": len(blockers),
		},
	}


@frappe.whitelist()
def get_management_warehouse_recovery_preview(branch="DEFAULT"):
	"""Read the full warehouse-history snapshot and return a short-lived token."""
	_ensure_management_access()
	preview = _build_snapshot(branch)
	token = secrets.token_urlsafe(32)
	payload = {
		"user": frappe.session.user,
		"fingerprint": preview["fingerprint"],
		"company": preview["company"],
		"branch": preview["branch"],
		"source_warehouse": preview["source_warehouse"],
		"target_warehouse": preview["target_warehouse"],
		"snapshot": preview,
	}
	frappe.cache().set_value(f"{RUN_CACHE_PREFIX}{token}", payload, expires_in_sec=PREVIEW_TTL_SECONDS)
	return {
		"preview_token": token,
		"company": preview["company"],
		"branch": preview["branch"],
		"source_warehouse": preview["source_warehouse"],
		"target_warehouse": preview["target_warehouse"],
		"rows": preview["vouchers"] + preview["sales_orders"] + preview["item_classification"] + preview["configuration_rows"],
		"blockers": preview["blockers"],
		"summary": preview["summary"],
	}


def _preview_from_cache(token):
	payload = frappe.cache().get_value(f"{RUN_CACHE_PREFIX}{token}")
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	if not payload or payload.get("user") != frappe.session.user:
		frappe.throw(_("پیش‌نمایش منقضی شده یا به کاربر دیگری تعلق دارد. دوباره پیش‌نمایش بگیرید."))
	return payload


def _row_payload(preview_row):
	return {
		"preview_row": preview_row,
		"source_modified": preview_row.get("modified"),
		"warehouse_changes": preview_row.get("warehouse_changes") or [],
	}


def _queue_run(run_name):
	frappe.enqueue(
		"restaurant.api_warehouse_recovery._run_recovery_batch",
		queue="long",
		timeout=600,
		job_name=f"restaurant-warehouse-recovery-{run_name}",
		run_name=run_name,
	)


@frappe.whitelist(methods=["POST"])
def start_management_warehouse_recovery(preview_token):
	"""Create or reuse a durable run for the exact reviewed preview."""
	_ensure_management_access()
	preview = _preview_from_cache(str(preview_token or "").strip())
	fresh = _build_snapshot(preview.get("branch") or "DEFAULT")
	if fresh["fingerprint"] != preview.get("fingerprint"):
		frappe.throw(_("داده‌ها پس از پیش‌نمایش تغییر کرده‌اند؛ پیش‌نمایش تازه بگیرید."))
	existing = frappe.db.get_value(
		RUN_DOCTYPE,
		{"preview_fingerprint": preview["fingerprint"], "requested_by": frappe.session.user},
		["name", "state"],
		as_dict=True,
	)
	if existing:
		if existing.state not in {"Completed", "Completed With Blocks", "Failed"}:
			_queue_run(existing.name)
		return {"name": existing.name, "state": existing.state, "reused": True}

	snapshot = preview["snapshot"]
	run = frappe.new_doc(RUN_DOCTYPE)
	run.company = snapshot["company"]
	run.branch = snapshot["branch"]
	run.source_warehouse = snapshot["source_warehouse"]
	run.target_warehouse = snapshot["target_warehouse"]
	run.state = "Running"
	run.phase = "Cancel"
	run.preview_fingerprint = preview["fingerprint"]
	run.preview_token = str(preview_token)
	run.requested_by = frappe.session.user
	run.started_at = now_datetime()
	run.summary_json = _json({"preview": snapshot["summary"], "blockers": snapshot["blockers"]})
	for row in snapshot["vouchers"]:
		state = "Previewed" if row["action"] == "Amend Voucher" else "Blocked"
		run.append("rows", {
			"source_doctype": row["doctype"],
			"source_name": row["name"],
			"action": row["action"],
			"original_posting_date": row.get("posting_date") or None,
			"original_posting_time": row.get("posting_time") or None,
			"state": state,
			"original_warehouse_json": _json(row.get("warehouse_changes") or []),
			"payload_json": _json(_row_payload(row)),
			"error_text": row.get("reason") or "",
		})
	for row in snapshot["sales_orders"]:
		run.append("rows", {
			"source_doctype": "Sales Order",
			"source_name": row["name"],
			"action": "Repair Sales Order",
			"original_posting_date": row.get("posting_date") or None,
			"state": "Previewed",
			"payload_json": _json(row),
		})
	for row in snapshot["item_classification"]:
		run.append("rows", {
			"source_doctype": "Item",
			"source_name": row["name"],
			"action": "Item Classification",
			"state": "Blocked",
			"payload_json": _json(row),
			"error_text": row.get("reason") or "",
		})
	for row in snapshot["configuration_rows"]:
		run.append("rows", {
			"source_doctype": row["doctype"],
			"source_name": row["name"],
			"action": row.get("action") or "Update Settings",
			"state": "Previewed",
			"original_warehouse_json": _json(row.get("original_warehouse_json") or []),
			"payload_json": _json(row),
		})
	run.insert(ignore_permissions=True)
	frappe.db.commit()
	_queue_run(run.name)
	return {"name": run.name, "state": run.state, "reused": False}


def _replace_warehouse_fields(doc, changes):
	for change in changes:
		path = change.get("path") or ""
		if path.startswith("parent:"):
			doc.set(path.split(":", 1)[1], change["to"])
			continue
		if path.startswith("table:"):
			_, table_field, index, fieldname = path.split(":", 3)
			rows = doc.get(table_field) or []
			position = cint(index) - 1
			if position < 0 or position >= len(rows):
				frappe.throw(_("ردیف انبار در سند {0} پس از پیش‌نمایش تغییر کرده است.").format(doc.name))
			rows[position].set(fieldname, change["to"])


def _submit_without_negative_stock(doc):
	previous = cint(frappe.db.get_single_value("Stock Settings", "allow_negative_stock"))
	if previous:
		frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
		frappe.clear_cache(doctype="Stock Settings")
	try:
		doc.submit()
	finally:
		if previous:
			frappe.db.set_single_value("Stock Settings", "allow_negative_stock", previous)
			frappe.clear_cache(doctype="Stock Settings")


def _cancel_voucher(row):
	doc = frappe.get_doc(row.source_doctype, row.source_name)
	if cint(doc.docstatus) != 1:
		frappe.throw(_("سند {0} دیگر ثبت‌شده نیست؛ پیش‌نمایش تازه لازم است.").format(row.source_name))
	payload = _parse_json(row.payload_json, {})
	preview_row = payload.get("preview_row") or {}
	if str(doc.modified or "") != str(preview_row.get("modified") or ""):
		frappe.throw(_("سند {0} پس از پیش‌نمایش ویرایش شده است.").format(row.source_name))
	if _document_dependency_blocker(doc):
		frappe.throw(_document_dependency_blocker(doc))
	doc.flags.ignore_permissions = True
	doc.cancel()
	row.state = "Cancelled"
	row.error_text = ""


def _amend_voucher(row, run):
	original = frappe.get_doc(row.source_doctype, row.source_name)
	if cint(original.docstatus) != 2:
		frappe.throw(_("سند مبدأ {0} باید از مسیر بومی لغو شده باشد.").format(row.source_name))
	meta = frappe.get_meta(row.source_doctype)
	if not meta.has_field("amended_from"):
		frappe.throw(_("سند {0} امکان اصلاح بومی ندارد.").format(row.source_name))
	payload = _parse_json(row.payload_json, {})
	changes = payload.get("warehouse_changes") or []
	if not changes:
		frappe.throw(_("تغییر انبار ثبت‌شده‌ای برای سند {0} پیدا نشد.").format(row.source_name))
	new_doc = frappe.copy_doc(original)
	new_doc.flags.ignore_permissions = True
	new_doc.amended_from = original.name
	if row.source_doctype == "Stock Entry" and original.get("work_order"):
		old_work_order = original.get("work_order")
		if frappe.db.get_value("Work Order", old_work_order, "docstatus") == 2:
			new_work_order = frappe.db.get_value(
				"Work Order", {"amended_from": old_work_order, "docstatus": 1}, "name"
			)
			if not new_work_order:
				frappe.throw(_("دستور تولید اصلاح‌شده برای سند {0} پیدا نشد.").format(row.source_name))
			new_doc.work_order = new_work_order
	_replace_warehouse_fields(new_doc, changes)
	if row.source_doctype == "Stock Entry" and _is_collapsed_transfer(new_doc):
		row.state = "Completed"
		row.replacement_document = ""
		row.error_text = _("انتقال پس از ادغام انبارها زائد شد و با لغو بومی حذف شد.")
		return
	if meta.has_field("posting_date"):
		new_doc.posting_date = row.original_posting_date
	if meta.has_field("posting_time"):
		new_doc.posting_time = row.original_posting_time
	if meta.has_field("set_posting_time"):
		new_doc.set_posting_time = 1
	new_doc.insert(ignore_permissions=True)
	if row.source_doctype == "Work Order":
		new_doc.submit()
	else:
		_submit_without_negative_stock(new_doc)
	row.state = "Completed"
	row.replacement_document = new_doc.name
	row.error_text = ""
	if row.source_doctype == "Work Order":
		for ticket_row in frappe.get_all(
			"Restaurant Production Ticket",
			filters={"work_order": original.name},
			fields=["name"],
			limit_page_length=10000,
			ignore_permissions=True,
		):
			ticket = frappe.get_doc("Restaurant Production Ticket", ticket_row.name)
			ticket.work_order = new_doc.name
			for fieldname in ("source_warehouse", "wip_warehouse", "fg_warehouse"):
				if ticket.get(fieldname) == run.source_warehouse:
					ticket.set(fieldname, run.target_warehouse)
			ticket.save(ignore_permissions=True)


def _is_collapsed_transfer(doc):
	if doc.doctype != "Stock Entry" or (doc.get("purpose") or doc.get("stock_entry_type")) not in {
		"Material Transfer",
		"Material Transfer for Manufacture",
	}:
		return False
	items = doc.get("items") or []
	return bool(items) and all(
		row.get("s_warehouse") and row.get("t_warehouse") and row.get("s_warehouse") == row.get("t_warehouse")
		for row in items
	)


def _update_warehouse_defaults(run):
	from restaurant.api_inventory import BRANCH_PRODUCTION_SETTINGS_DOCTYPE

	settings_rows = frappe.get_all(
		BRANCH_PRODUCTION_SETTINGS_DOCTYPE,
		filters={"company": run.company},
		fields=["name", "raw_warehouse", "kitchen_wip_warehouse", "finished_goods_warehouse"],
		limit_page_length=100000,
		ignore_permissions=True,
	)
	for row in settings_rows:
		doc = frappe.get_doc(BRANCH_PRODUCTION_SETTINGS_DOCTYPE, row.name)
		changed = False
		for fieldname in ("raw_warehouse", "kitchen_wip_warehouse", "finished_goods_warehouse"):
			if doc.get(fieldname) == run.source_warehouse:
				doc.set(fieldname, run.target_warehouse)
				changed = True
		if changed:
			doc.save(ignore_permissions=True)

	item_defaults = frappe.get_all(
		"Item Default",
		filters={"company": run.company, "default_warehouse": run.source_warehouse},
		fields=["parent"],
		limit_page_length=100000,
		ignore_permissions=True,
	)
	for item_code in sorted({row.parent for row in item_defaults if row.parent}):
		item = frappe.get_doc("Item", item_code)
		changed = False
		for default in item.get("item_defaults") or []:
			if default.company == run.company and default.default_warehouse == run.source_warehouse:
				default.default_warehouse = run.target_warehouse
				changed = True
		if changed:
			item.flags.ignore_permissions = True
			item.save(ignore_permissions=True)

	if frappe.db.get_single_value("Stock Settings", "default_warehouse") != run.target_warehouse:
		frappe.db.set_single_value("Stock Settings", "default_warehouse", run.target_warehouse)
		frappe.clear_cache(doctype="Stock Settings")
	if (
		frappe.get_meta("Restaurant Web Settings").has_field("restaurant_inventory_default_warehouse")
		and frappe.db.get_single_value("Restaurant Web Settings", "restaurant_inventory_default_warehouse")
		!= run.target_warehouse
	):
		frappe.db.set_single_value(
			"Restaurant Web Settings", "restaurant_inventory_default_warehouse", run.target_warehouse
		)
		frappe.clear_cache(doctype="Restaurant Web Settings")

	pending_ticket_rows = frappe.get_all(
		ROW_DOCTYPE,
		filters={
			"parent": run.name,
			"parenttype": RUN_DOCTYPE,
			"parentfield": "rows",
			"action": "Update Production Ticket",
			"state": "Previewed",
		},
		fields=["name", "source_name", "payload_json", "idx"],
		order_by="idx asc",
		limit_page_length=1000,
		ignore_permissions=True,
	)
	for run_row in pending_ticket_rows:
		sp = f"warehouse_recovery_ticket_{run_row.idx}"
		frappe.db.savepoint(sp)
		try:
			payload = _parse_json(run_row.payload_json, {})
			expected_modified = str(payload.get("modified") or "")
			ticket = frappe.get_doc("Restaurant Production Ticket", run_row.source_name)
			if expected_modified and str(ticket.modified or "") != expected_modified:
				frappe.throw(_("تیکت تولید {0} پس از پیش‌نمایش تغییر کرده است.").format(run_row.source_name))
			changed = False
			for fieldname in ("source_warehouse", "wip_warehouse", "fg_warehouse"):
				if ticket.get(fieldname) == run.source_warehouse:
					ticket.set(fieldname, run.target_warehouse)
					changed = True
			if changed:
				ticket.save(ignore_permissions=True)
			frappe.db.set_value(ROW_DOCTYPE, run_row.name, {"state": "Completed", "error_text": ""}, update_modified=False)
		except Exception as exc:
			frappe.db.rollback(save_point=sp)
			frappe.db.set_value(ROW_DOCTYPE, run_row.name, {"state": "Blocked", "error_text": str(exc)}, update_modified=False)


def _repair_sales_order(row):
	if not frappe.db.exists("Sales Order", row.source_name):
		frappe.throw(_("سفارش فروش {0} پیدا نشد.").format(row.source_name))
	from restaurant.api import _run_sales_order_auto_flow
	previous_allow_negative = cint(frappe.db.get_single_value("Stock Settings", "allow_negative_stock"))
	if previous_allow_negative:
		frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 0)
		frappe.clear_cache(doctype="Stock Settings")
	try:
		result = _run_sales_order_auto_flow(
			row.source_name,
			trigger="manual",
			force=True,
			allow_negative_stock=False,
		)
	finally:
		if previous_allow_negative:
			frappe.db.set_single_value("Stock Settings", "allow_negative_stock", previous_allow_negative)
			frappe.clear_cache(doctype="Stock Settings")
	if result.get("errors"):
		frappe.throw("؛ ".join(result.get("errors") or []))
	if not result.get("delivery_note"):
		frappe.throw(_("برای سفارش {0} رسید تحویل قابل ثبت نبود؛ موجودی، فرمول تولید یا وضعیت سفارش را بررسی کنید.").format(row.source_name))
	row.state = "Completed"
	row.replacement_document = result.get("delivery_note")
	row.error_text = ""


def _run_recovery_batch(run_name):
	"""Process a durable batch; each worker invocation handles at most 25 rows."""
	if not frappe.db.exists(RUN_DOCTYPE, run_name):
		return
	frappe.db.sql(f"select name from `tab{RUN_DOCTYPE}` where name = %s for update", (run_name,))
	run = frappe.db.get_value(
		RUN_DOCTYPE,
		run_name,
		["name", "state", "phase", "company", "branch", "source_warehouse", "target_warehouse", "finished_at"],
		as_dict=True,
	)
	if not run:
		return
	if run.state in {"Completed", "Completed With Blocks", "Failed"}:
		return
	try:
		run.state = "Running"
		pending_configuration = frappe.db.count(
			ROW_DOCTYPE,
			{
				"parent": run.name,
				"parenttype": RUN_DOCTYPE,
				"parentfield": "rows",
				"action": ["in", ["Update Settings", "Update Production Ticket"]],
				"state": "Previewed",
			},
		)
		if pending_configuration:
			_update_warehouse_defaults(run)
			frappe.db.sql(
				f"update `tab{ROW_DOCTYPE}` set state = 'Completed' where parent = %s and parenttype = %s and parentfield = 'rows' and action = 'Update Settings' and state = 'Previewed'",
				(run.name, RUN_DOCTYPE),
			)
		processed = 0
		reconciliation_state = None
		while processed < BATCH_SIZE:
			if run.phase == "Cancel":
				row_ref = _next_recovery_row(
					run.name,
					"Amend Voucher",
					"Previewed",
					excluded_source_doctype="Work Order",
					order_by="original_posting_date desc, original_posting_time desc, source_name desc",
				)
				if not row_ref:
					row_ref = _next_recovery_row(
						run.name,
						"Amend Voucher",
						"Previewed",
						source_doctype="Work Order",
						order_by="original_posting_date desc, original_posting_time desc, source_name desc",
					)
				if not row_ref:
					run.phase = "Amend"
					continue
				row = frappe.get_doc(ROW_DOCTYPE, row_ref.name)
				sp = f"warehouse_recovery_{processed}"
				frappe.db.savepoint(sp)
				try:
					_cancel_voucher(row)
				except Exception as exc:
					frappe.db.rollback(save_point=sp)
					row.state = "Blocked"
					row.error_text = str(exc)
				row.db_update()
				processed += 1
				continue

			if run.phase == "Amend":
				row_ref = _next_recovery_row(
					run.name,
					"Amend Voucher",
					"Cancelled",
					source_doctype="Work Order",
					order_by="original_posting_date asc, original_posting_time asc, source_name asc",
				)
				if not row_ref:
					row_ref = _next_recovery_row(
						run.name,
						"Amend Voucher",
						"Cancelled",
						excluded_source_doctype="Work Order",
						order_by="original_posting_date asc, original_posting_time asc, source_name asc",
					)
				if not row_ref:
					run.phase = "Repair Orders"
					continue
				row = frappe.get_doc(ROW_DOCTYPE, row_ref.name)
				sp = f"warehouse_recovery_{processed}"
				frappe.db.savepoint(sp)
				try:
					_amend_voucher(row, run)
				except Exception as exc:
					frappe.db.rollback(save_point=sp)
					row.state = "Blocked"
					row.error_text = str(exc)
				row.db_update()
				processed += 1
				continue

			if run.phase == "Repair Orders":
				row_ref = _next_recovery_row(
					run.name,
					"Repair Sales Order",
					"Previewed",
					order_by="source_name asc",
				)
				if not row_ref:
					run.phase = "Reconcile"
					continue
				row = frappe.get_doc(ROW_DOCTYPE, row_ref.name)
				sp = f"warehouse_recovery_{processed}"
				frappe.db.savepoint(sp)
				try:
					_repair_sales_order(row)
				except Exception as exc:
					frappe.db.rollback(save_point=sp)
					row.state = "Blocked"
					row.error_text = str(exc)
				row.db_update()
				processed += 1
				continue

			if run.phase == "Reconcile":
				reconciliation_state = _reconcile_warehouse(run)
				run.phase = "Done"
				continue

			if run.phase == "Done":
				blocked_count = frappe.db.count(
					ROW_DOCTYPE,
					{"parent": run.name, "parenttype": RUN_DOCTYPE, "parentfield": "rows", "state": "Blocked"},
				)
				run.state = "Completed With Blocks" if blocked_count else "Completed"
				run.finished_at = now_datetime()
				break

		summary = _run_summary(run)
		if reconciliation_state is not None:
			summary["source_warehouse_state"] = reconciliation_state
		updates = {
			"state": run.state,
			"phase": run.phase,
			"summary_json": _json(summary),
		}
		if run.get("finished_at"):
			updates["finished_at"] = run.finished_at
		frappe.db.set_value(RUN_DOCTYPE, run.name, updates)
		frappe.db.commit()
		if run.state == "Running":
			_queue_run(run.name)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), f"Restaurant Warehouse Recovery ({run_name})")
		frappe.db.set_value(RUN_DOCTYPE, run_name, {
			"state": "Failed",
			"finished_at": now_datetime(),
			"summary_json": _json({"error": _("اجرای مرحله‌ای با خطای غیرمنتظره متوقف شد.")}),
		})
		frappe.db.commit()


def _next_recovery_row(run_name, action, state, source_doctype=None, excluded_source_doctype=None, order_by="idx asc"):
	filters = {
		"parent": run_name,
		"parenttype": RUN_DOCTYPE,
		"parentfield": "rows",
		"action": action,
		"state": state,
	}
	if source_doctype:
		filters["source_doctype"] = source_doctype
	if excluded_source_doctype:
		filters["source_doctype"] = ["!=", excluded_source_doctype]
	rows = frappe.get_all(
		ROW_DOCTYPE,
		filters=filters,
		fields=["name"],
		order_by=order_by,
		limit_page_length=1,
		ignore_permissions=True,
	)
	return rows[0] if rows else None


def _run_summary(run):
	state_rows = frappe.db.sql(
		f"""select state, count(*) as row_count from `tab{ROW_DOCTYPE}`
			where parent = %s and parenttype = %s and parentfield = 'rows' group by state""",
		(run.name, RUN_DOCTYPE),
		as_dict=True,
	)
	counts = {row.state: cint(row.row_count) for row in state_rows}
	return {
		"run": run.name,
		"state": run.state,
		"phase": run.phase,
		"total_rows": sum(counts.values()),
		"completed": counts.get("Completed", 0),
		"cancelled": counts.get("Cancelled", 0),
		"blocked": counts.get("Blocked", 0),
		"pending": counts.get("Previewed", 0) + counts.get("Cancelling", 0) + counts.get("Cancelled", 0),
		"states": counts,
		"source_warehouse": run.source_warehouse,
		"target_warehouse": run.target_warehouse,
	}


def _warehouse_reconciliation_state(run):
	if not frappe.db.exists("Warehouse", run.source_warehouse):
		return {"exists": False, "disabled": False, "actual_qty": 0, "references": []}
	qty = frappe.db.sql(
		"""select ifnull(sum(actual_qty), 0) as actual_qty,
			ifnull(sum(reserved_qty), 0) as reserved_qty,
			ifnull(sum(projected_qty), 0) as projected_qty
			from `tabBin` where warehouse = %s""",
		run.source_warehouse,
		as_dict=True,
	)[0]
	refs = _operational_references(run.company, run.source_warehouse)
	for parent_doctype, config in WAREHOUSE_MAPS.items():
		if not frappe.db.exists("DocType", parent_doctype):
			continue
		meta = frappe.get_meta(parent_doctype)
		for fieldname in config["parents"]:
			if not meta.has_field(fieldname):
				continue
			filters = {fieldname: run.source_warehouse}
			if meta.has_field("docstatus") or parent_doctype in WAREHOUSE_MAPS:
				filters["docstatus"] = ["!=", 2]
			for row in frappe.get_all(parent_doctype, filters=filters, fields=["name"], limit_page_length=100000, ignore_permissions=True):
				refs.append({"doctype": parent_doctype, "name": row.name, "field": fieldname})
		for table_field, fields in config["tables"].items():
			if not meta.has_field(table_field):
				continue
			child_doctype = meta.get_field(table_field).options
			if not child_doctype or not frappe.db.exists("DocType", child_doctype):
				continue
			child_meta = frappe.get_meta(child_doctype)
			for fieldname in fields:
				if not child_meta.has_field(fieldname):
					continue
				child_rows = frappe.db.sql(
					f"select c.parent, c.name from `tab{child_doctype}` c join `tab{parent_doctype}` p on p.name = c.parent where c.`{fieldname}` = %s and p.docstatus != 2 limit 100000",
					run.source_warehouse,
					as_dict=True,
				)
				refs.extend({"doctype": parent_doctype, "name": row.parent, "field": f"{table_field}.{fieldname}"} for row in child_rows)
	if frappe.get_meta("Restaurant Web Settings").has_field("restaurant_inventory_default_warehouse"):
		if frappe.db.get_single_value("Restaurant Web Settings", "restaurant_inventory_default_warehouse") == run.source_warehouse:
			refs.append({
				"doctype": "Restaurant Web Settings",
				"name": "Restaurant Web Settings",
				"field": "restaurant_inventory_default_warehouse",
			})
	unique_refs = {
		(ref["doctype"], ref["name"], ref["field"]): ref for ref in refs
	}
	return {
		"exists": True,
		"disabled": cint(frappe.db.get_value("Warehouse", run.source_warehouse, "disabled")),
		"actual_qty": flt(qty.actual_qty),
		"reserved_qty": flt(qty.reserved_qty),
		"projected_qty": flt(qty.projected_qty),
		"references": list(unique_refs.values()),
	}


def _reconcile_warehouse(run):
	frappe.clear_cache(doctype="Warehouse")
	state = _warehouse_reconciliation_state(run)
	no_quantity = all(abs(flt(state.get(key))) < 1e-8 for key in ("actual_qty", "reserved_qty", "projected_qty"))
	if no_quantity and not state.get("references"):
		warehouse = frappe.get_doc("Warehouse", run.source_warehouse)
		if not cint(warehouse.disabled):
			warehouse.disabled = 1
			warehouse.save(ignore_permissions=True)
		state["disabled"] = 1
	else:
		state["disabled"] = cint(frappe.db.get_value("Warehouse", run.source_warehouse, "disabled"))
	frappe.clear_cache(doctype="Warehouse")
	return state


def _serialize_run(run, limit=100, offset=0):
	rows = []
	limit = max(1, min(cint(limit) or 100, 500))
	offset = max(cint(offset), 0)
	row_docs = frappe.get_all(
		ROW_DOCTYPE,
		filters={"parent": run.name, "parenttype": RUN_DOCTYPE, "parentfield": "rows"},
		fields=[
			"source_doctype", "source_name", "action", "state", "original_posting_date",
			"original_posting_time", "replacement_document", "original_warehouse_json",
			"payload_json", "error_text",
		],
		order_by="idx asc",
		limit_start=offset,
		limit_page_length=limit,
		ignore_permissions=True,
	)
	for row in row_docs:
		payload = _parse_json(row.get("payload_json"), {})
		preview = payload.get("preview_row") or payload
		rows.append({
			"doctype": row.get("source_doctype"),
			"name": row.get("source_name"),
			"document_name": row.get("source_name"),
			"source_doctype": row.get("source_doctype"),
			"source_name": row.get("source_name"),
			"action": row.get("action"),
			"state": row.get("state"),
			"posting_date": str(row.get("original_posting_date") or preview.get("posting_date") or ""),
			"posting_time": str(row.get("original_posting_time") or preview.get("posting_time") or ""),
			"original_posting_date": str(row.get("original_posting_date") or preview.get("posting_date") or ""),
			"original_posting_time": str(row.get("original_posting_time") or preview.get("posting_time") or ""),
			"proposed_posting_date": str(row.get("original_posting_date") or preview.get("posting_date") or ""),
			"proposed_posting_time": str(row.get("original_posting_time") or preview.get("posting_time") or ""),
			"source_warehouse": run.source_warehouse,
			"target_warehouse": run.target_warehouse,
			"replacement_document": row.get("replacement_document"),
			"warehouse_changes": _parse_json(row.get("original_warehouse_json"), []),
			"reason": row.get("error_text") or preview.get("reason") or "",
			"pending_qty": preview.get("pending_qty"),
			"item_count": preview.get("item_count"),
		})
	return {
		"name": run.name,
		"state": run.state,
		"phase": run.phase,
		"company": run.company,
		"branch": run.branch,
		"source_warehouse": run.source_warehouse,
		"target_warehouse": run.target_warehouse,
		"started_at": str(run.started_at or ""),
		"finished_at": str(run.finished_at or ""),
		"summary": _parse_json(run.summary_json, {}),
		"rows": rows,
		"row_count": frappe.db.count(
			ROW_DOCTYPE,
			{"parent": run.name, "parenttype": RUN_DOCTYPE, "parentfield": "rows"},
		),
		"row_offset": offset,
		"page_size": limit,
	}


@frappe.whitelist()
def get_management_warehouse_recovery_run(run_name, limit=100, offset=0):
	_ensure_management_access()
	if not frappe.db.exists(RUN_DOCTYPE, run_name):
		frappe.throw(_("اجرای اصلاح انبار پیدا نشد."))
	run = frappe.db.get_value(
		RUN_DOCTYPE,
		run_name,
		[
			"name", "state", "phase", "company", "branch", "source_warehouse",
			"target_warehouse", "started_at", "finished_at", "summary_json",
		],
		as_dict=True,
	)
	return _serialize_run(run, limit=limit, offset=offset)


@frappe.whitelist(methods=["POST"])
def resume_management_warehouse_recovery(run_name, limit=100, offset=0):
	_ensure_management_access()
	if not frappe.db.exists(RUN_DOCTYPE, run_name):
		frappe.throw(_("اجرای اصلاح انبار پیدا نشد."))
	run = frappe.db.get_value(
		RUN_DOCTYPE,
		run_name,
		[
			"name", "state", "phase", "company", "branch", "source_warehouse",
			"target_warehouse", "started_at", "finished_at", "summary_json",
		],
		as_dict=True,
	)
	if run.state in {"Completed", "Completed With Blocks", "Failed"}:
		return _serialize_run(run, limit=limit, offset=offset)
	_queue_run(run.name)
	return {"name": run.name, "state": run.state, "queued": True}
