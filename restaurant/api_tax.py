# Copyright (c) 2026, Restaurant and contributors
"""Moadian (سامانه مودیان) integration for sales invoices.

- Keeps a per-invoice submission log (Restaurant Tax Submission).
- Builds the standard electronic-invoice JSON payload per invoice.
- Dispatches to a configurable taxpayer API endpoint (token auth,
  sandbox mode) similar to the courier-provider connector.
- Optional daily auto-submission job + periodic reconciliation report
  (internal sales vs what was sent to the tax authority).

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import json
import urllib.request

import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, now_datetime, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_table_columns_from_rows,
)

__all__ = [
	"TAX_REPORT_KEYS",
	"TAX_DOCTYPE",
	"tax_build_report_bi",
	"_tax_ensure_ops_ready",
	"get_management_tax_boot",
	"set_management_tax_settings",
	"list_management_tax_submissions",
	"build_tax_invoice_payload",
	"submit_management_tax_invoice",
	"run_daily_tax_auto_submissions",
	"get_management_report_tax_reconciliation",
]

TAX_DOCTYPE = "Restaurant Tax Submission"
TAX_REPORT_KEYS = {"tax-reconciliation"}
SUBMISSION_STATUSES = ["در صف", "ارسال‌شده", "خطا", "لغوشده"]


# ---------------------------------------------------------------------------
# Lazy bridge (import-cycle safety)
# ---------------------------------------------------------------------------


def _tax_fp_call(helper_name, *args, **kwargs):
	from restaurant import api_feature_pack

	fn = getattr(api_feature_pack, helper_name, None)
	if not callable(fn):
		raise RuntimeError(f"api_feature_pack helper missing: {helper_name}")
	return fn(*args, **kwargs)


def _parse_json(value, fallback=None):
	import json as _json

	if isinstance(value, str):
		try:
			return _json.loads(value)
		except Exception:
			return fallback if fallback is not None else {}
	if isinstance(value, (dict, list)):
		return value
	return fallback if fallback is not None else {}


# ---------------------------------------------------------------------------
# Provisioning & settings
# ---------------------------------------------------------------------------


def _tax_ensure_ops_ready():
	try:
		_tax_fp_call(
			"_fp_ensure_custom_fields",
			"Restaurant Web Settings",
			[
				{"fieldname": "restaurant_tax_section", "label": "سامانه مودیان", "fieldtype": "Section Break"},
				{"fieldname": "restaurant_tax_enabled", "label": "اتصال سامانه مودیان فعال", "fieldtype": "Check", "default": "0"},
				{"fieldname": "restaurant_tax_sandbox", "label": "حالت آزمایشی (محیط تست)", "fieldtype": "Check", "default": "1"},
				{"fieldname": "restaurant_tax_column", "label": "", "fieldtype": "Column Break"},
				{"fieldname": "restaurant_tax_api_url", "label": "نشانی سرویس ارسال صورتحساب", "fieldtype": "Data"},
				{"fieldname": "restaurant_tax_memory_code", "label": "کد حافظه مالیاتی", "fieldtype": "Data"},
				{"fieldname": "restaurant_tax_auth_token", "label": "توکن احراز هویت", "fieldtype": "Password"},
				{"fieldname": "restaurant_tax_economic_code", "label": "کد اقتصادی", "fieldtype": "Data"},
				{"fieldname": "restaurant_tax_auto_submit", "label": "ارسال خودکار روزانه فاکتورها", "fieldtype": "Check", "default": "0"},
			],
			anchor_candidates=["restaurant_reservation_section", "restaurant_delivery_section", "restaurant_club_section", "configuration_tab"],
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Restaurant tax ensure fields failed")


def _tax_setting(fieldname, default=None):
	try:
		value = frappe.db.get_single_value("Restaurant Web Settings", fieldname)
		return default if value in (None, "") else value
	except Exception:
		return default


def _tax_settings():
	return {
		"enabled": cint(_tax_setting("restaurant_tax_enabled", 0)) == 1,
		"sandbox": cint(_tax_setting("restaurant_tax_sandbox", 1)) == 1,
		"api_url": (_tax_setting("restaurant_tax_api_url", "") or "").strip(),
		"memory_code": (_tax_setting("restaurant_tax_memory_code", "") or "").strip(),
		"token_set": bool((_tax_setting("restaurant_tax_auth_token", "") or "").strip()),
		"economic_code": (_tax_setting("restaurant_tax_economic_code", "") or "").strip(),
		"auto_submit": cint(_tax_setting("restaurant_tax_auto_submit", 0)) == 1,
	}


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------


def build_tax_invoice_payload(sales_invoice):
	"""Standard electronic-invoice JSON (header/body) for a Sales Invoice."""
	if not frappe.db.exists("Sales Invoice", sales_invoice):
		frappe.throw(_("فاکتور یافت نشد: {0}").format(sales_invoice or "-"))
	si = frappe.get_doc("Sales Invoice", sales_invoice)
	settings = _tax_settings()
	posting_dt = getdate(si.posting_date) if si.posting_date else getdate(today())
	import time as _time

	ref = frappe.db.get_value(TAX_DOCTYPE, {"sales_invoice": si.name}, "reference_id") if frappe.db.exists("DocType", TAX_DOCTYPE) else None
	if not ref:
		serial = "".join(ch for ch in si.name if ch.isdigit())[-7:] or "1"
		ref = f"{settings['memory_code'] or 'MEM'}{serial}{posting_dt.strftime('%y%m%d')}"
	tax_total = flt(getattr(si, "total_taxes_and_charges", 0) or sum(flt(t.tax_amount) for t in getattr(si, "taxes", []) or []))
	net_total = flt(si.net_total or si.total)
	grand_total = flt(si.grand_total or si.rounded_total)
	discount = flt(getattr(si, "discount_amount", 0))

	body = []
	for item in si.items:
		amount = flt(item.amount or (flt(item.qty) * flt(item.rate)))
		body.append(
			{
				"sstid": item.item_code,
				"sstt": item.item_name,
				"am": flt(item.qty, 3),
				"mu": item.uom or item.stock_uom or "",
				"fee": flt(item.rate),
				"prdis": amount,
				"dis": flt(item.discount_amount or 0),
				"tsstim": amount,
			}
		)
	return {
		"header": {
			"taxid": "",
			"indatim": int(_time.mktime(posting_dt.timetuple()) * 1000),
			"inty": 1,
			"ins": 1,
			"ft": "sale",
			"inno": si.name,
			"tins": settings["economic_code"] or "",
			"tonam": si.customer_name or "",
			"mob": (si.get("contact_mobile") or si.get("restaurant_customer_mobile") or ""),
			"tprdis": net_total,
			"tdis": discount,
			"tvop": tax_total,
			"cap": grand_total,
			"ref": ref,
		},
		"body": body,
	}


# ---------------------------------------------------------------------------
# Management endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_tax_boot():
	_ensure_management_access()
	_tax_ensure_ops_ready()
	settings = _tax_settings()
	summary = {"queued": 0, "sent": 0, "error": 0, "unsent_invoices_30d": 0}
	recent = []
	if frappe.db.exists("DocType", TAX_DOCTYPE):
		rows = frappe.get_all(TAX_DOCTYPE, fields=["status", "COUNT(*) AS count"], group_by="status")
		for row in rows:
			if row.get("status") == "در صف":
				summary["queued"] = cint(row.get("count"))
			elif row.get("status") == "ارسال‌شده":
				summary["sent"] = cint(row.get("count"))
			elif row.get("status") == "خطا":
				summary["error"] = cint(row.get("count"))
		recent = frappe.get_all(
			TAX_DOCTYPE,
			fields=["name", "sales_invoice", "status", "reference_id", "tax_id", "submitted_at", "modified"],
			order_by="modified desc",
			limit_page_length=10,
		)
	if frappe.db.exists("DocType", "Sales Invoice"):
		already = set()
		if frappe.db.exists("DocType", TAX_DOCTYPE):
			already = {r["sales_invoice"] for r in frappe.get_all(TAX_DOCTYPE, filters={"status": ["!=", "لغوشده"]}, fields=["sales_invoice"])}
		candidates = frappe.get_all(
			"Sales Invoice",
			filters={"docstatus": 1, "posting_date": [">=", add_days(today(), -30)], "is_return": 0},
			fields=["name"],
			limit_page_length=500,
		)
		summary["unsent_invoices_30d"] = len([c for c in candidates if c["name"] not in already])
	return {"settings": settings, "summary": summary, "recent": recent, "statuses": SUBMISSION_STATUSES}


@frappe.whitelist()
def set_management_tax_settings(payload=None):
	_ensure_management_access()
	_tax_ensure_ops_ready()
	payload = _parse_json(payload, {})
	for key in ("restaurant_tax_enabled", "restaurant_tax_sandbox", "restaurant_tax_auto_submit"):
		if key in payload:
			frappe.db.set_single_value("Restaurant Web Settings", key, cint(payload.get(key)), update_modified=False)
	for key in ("restaurant_tax_api_url", "restaurant_tax_memory_code", "restaurant_tax_economic_code"):
		if key in payload:
			frappe.db.set_single_value("Restaurant Web Settings", key, (payload.get(key) or "").strip(), update_modified=False)
	if "restaurant_tax_auth_token" in payload:
		frappe.db.set_single_value("Restaurant Web Settings", "restaurant_tax_auth_token", (payload.get("restaurant_tax_auth_token") or "").strip(), update_modified=False)
	frappe.db.commit()
	return {"status": "success", "settings": _tax_settings()}


@frappe.whitelist()
def list_management_tax_submissions(status="", date_from="", date_to="", search="", limit=50, offset=0):
	_ensure_management_access()
	if not frappe.db.exists("DocType", TAX_DOCTYPE):
		return {"submissions": [], "count": 0}
	filters = {}
	if status:
		filters["status"] = status
	rows = frappe.get_all(
		TAX_DOCTYPE,
		filters=filters,
		fields=["name", "sales_invoice", "status", "reference_id", "tax_id", "error", "submitted_at", "retry_count", "creation"],
		order_by="creation desc",
		limit_start=cint(offset),
		limit_page_length=min(cint(limit) or 50, 200),
	)
	search = (search or "").strip().lower()
	from frappe.utils import getdate as _gd

	items = []
	for row in rows:
		if date_from or date_to:
			when = _gd(row.get("creation") or today())
			if date_from and str(when) < date_from:
				continue
			if date_to and str(when) > date_to:
				continue
		if search and search not in (row.get("sales_invoice") or "").lower() and search not in (row.get("reference_id") or "").lower():
			continue
		row_out = dict(row)
		row_out["submitted_at"] = str(row.get("submitted_at") or "")
		row_out["creation"] = str(row.get("creation") or "")[:16]
		items.append(row_out)
	return {"submissions": items, "count": len(items)}


def _tax_get_or_create_submission(si_name, payload_json):
	if not frappe.db.exists("DocType", TAX_DOCTYPE):
		frappe.throw(_("داکتایپ ارسال مودیان هنوز ساخته نشده؛ migrate اجرا کنید."))
	existing = frappe.db.get_value(TAX_DOCTYPE, {"sales_invoice": si_name}, "name")
	if existing:
		doc = frappe.get_doc(TAX_DOCTYPE, existing)
		if doc.status == "ارسال‌شده":
			return doc, False
	else:
		doc = frappe.new_doc(TAX_DOCTYPE)
		doc.sales_invoice = si_name
	doc.status = "در صف"
	doc.reference_id = (payload_json.get("header") or {}).get("ref") or doc.reference_id or ""
	doc.payload_json = json.dumps(payload_json, ensure_ascii=False)
	doc.error = ""
	doc.save(ignore_permissions=True)
	return doc, True


@frappe.whitelist()
def submit_management_tax_invoice(sales_invoice=""):
	_ensure_management_access()
	sales_invoice = (sales_invoice or "").strip()
	settings = _tax_settings()
	payload_json = build_tax_invoice_payload(sales_invoice)
	doc, proceeding = _tax_get_or_create_submission(sales_invoice, payload_json)
	if not proceeding:
		return {"status": "already", "submission": doc.name, "tax_id": doc.tax_id}

	if not settings["enabled"] or not settings["api_url"]:
		doc.error = _("درگاه ارسال پیکربندی نشده؛ فاکتور در صف ماند.")
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"status": "queued", "submission": doc.name, "note": _("اتصال غیرفعال است؛ صورتحساب در صف ثبت شد."), "payload_preview": payload_json.get("header")}

	try:
		request = urllib.request.Request(
			settings["api_url"],
			data=json.dumps(payload_json, ensure_ascii=False).encode("utf-8"),
			headers={
				"Content-Type": "application/json",
				"Authorization": f"Bearer {_tax_setting('restaurant_tax_auth_token', '')}",
			},
			method="POST",
		)
		with urllib.request.urlopen(request, timeout=20) as response:
			raw = response.read().decode("utf-8", errors="ignore")
		data = _parse_json(raw, {})
		if isinstance(data, dict) and data.get("status") in ("success", "Success", "ok", True):
			doc.status = "ارسال‌شده"
			doc.tax_id = str(data.get("tax_id") or data.get("reference") or data.get("id") or "")[:140]
			doc.response_json = raw[:4000]
			doc.submitted_at = now_datetime()
		else:
			doc.status = "خطا"
			doc.error = (raw or _("پاسخ نامعتبر سرویس"))[:400]
			doc.retry_count = cint(doc.retry_count) + 1
	except Exception as exc:
		doc.status = "خطا"
		doc.error = str(exc)[:400]
		doc.retry_count = cint(doc.retry_count) + 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": doc.status, "submission": doc.name, "tax_id": doc.tax_id}


def run_daily_tax_auto_submissions():
	"""Auto-submit yesterday's invoices when daily auto mode is on."""
	settings = _tax_settings()
	if not settings["enabled"] or not settings["api_url"] or not settings["auto_submit"]:
		return {"status": "skipped", "reason": "disabled"}
	if not frappe.db.exists("DocType", TAX_DOCTYPE) or not frappe.db.exists("DocType", "Sales Invoice"):
		return {"status": "skipped", "reason": "doctypes-missing"}
	yesterday = add_days(today(), -1)
	sent = frappe.get_all(TAX_DOCTYPE, filters={"status": ["!=", "لغوشده"]}, fields=["sales_invoice"])
	already = {r["sales_invoice"] for r in sent}
	invoices = frappe.get_all(
		"Sales Invoice",
		filters={"docstatus": 1, "posting_date": yesterday, "is_return": 0},
		fields=["name"],
		limit_page_length=200,
	)
	done = 0
	for inv in invoices:
		if inv["name"] in already:
			continue
		try:
			submit_management_tax_invoice(inv["name"])
			done += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Restaurant tax auto submit failed: {inv['name']}")
	return {"status": "success", "submitted": done}


# ---------------------------------------------------------------------------
# Reconciliation report
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_tax_reconciliation(date_from=None, date_to=None):
	_ensure_management_access()
	if not frappe.db.exists("DocType", "Sales Invoice"):
		return _compose_management_report("tax-reconciliation", _("تطبیق فروش و ارسال به سامانه مودیان"), {}, [], date_from=date_from, date_to=date_to, orders=[])
	clauses = ["si.docstatus = 1", "ifnull(si.is_return,0) = 0"]
	params = {}
	if date_from:
		clauses.append("si.posting_date >= %(df)s")
		params["df"] = date_from
	if date_to:
		clauses.append("si.posting_date <= %(dt)s")
		params["dt"] = date_to
	sales = frappe.db.sql(
		f"""
		SELECT DATE_FORMAT(si.posting_date, '%Y-%m') AS period, COUNT(*) AS invoices,
			   COALESCE(SUM(si.grand_total),0) AS sales_total,
			   COALESCE(SUM(si.total_taxes_and_charges),0) AS tax_total
		FROM `tabSales Invoice` si
		WHERE {' AND '.join(clauses)}
		GROUP BY period ORDER BY period
		""",
		params,
		as_dict=True,
	)
	sent_map = {}
	if frappe.db.exists("DocType", TAX_DOCTYPE) and sales:
		sent_rows = frappe.db.sql(
			"""
			SELECT si.name, DATE_FORMAT(si.posting_date, '%Y-%m') AS period, si.grand_total, si.total_taxes_and_charges
			FROM `tabSales Invoice` si
			INNER JOIN `tabRestaurant Tax Submission` ts ON ts.sales_invoice = si.name AND ts.status = 'ارسال‌شده'
			WHERE si.docstatus = 1
			""",
			as_dict=True,
		)
		for row in sent_rows:
			bucket = sent_map.setdefault(row["period"], {"invoices": 0, "sales_total": 0.0, "tax_total": 0.0})
			bucket["invoices"] += 1
			bucket["sales_total"] += flt(row.get("grand_total"))
			bucket["tax_total"] += flt(row.get("total_taxes_and_charges"))

	rows = []
	tot_sales = tot_sent = tot_tax = tot_sent_tax = 0
	for s in sales:
		sent = sent_map.get(s["period"], {"invoices": 0, "sales_total": 0.0, "tax_total": 0.0})
		rows.append(
			{
				"period": s["period"],
				"internal_invoices": cint(s["invoices"]),
				"internal_sales": flt(s["sales_total"]),
				"internal_tax": flt(s["tax_total"]),
				"sent_invoices": cint(sent["invoices"]),
				"sent_sales": flt(sent["sales_total"]),
				"sent_tax": flt(sent["tax_total"]),
				"diff_sales": flt(s["sales_total"] - sent["sales_total"]),
				"diff_invoices": cint(s["invoices"]) - cint(sent["invoices"]),
			}
		)
		tot_sales += flt(s["sales_total"])
		tot_sent += flt(sent["sales_total"])
		tot_tax += flt(s["tax_total"])
		tot_sent_tax += flt(sent["tax_total"])
	summary = {
		"periods": len(rows),
		"internal_sales_total": flt(tot_sales),
		"sent_sales_total": flt(tot_sent),
		"internal_tax_total": flt(tot_tax),
		"sent_tax_total": flt(tot_sent_tax),
		"unmatched_sales": flt(tot_sales - tot_sent),
	}
	return _compose_management_report(
		"tax-reconciliation",
		_("تطبیق فروش و ارسال به سامانه مودیان"),
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		orders=[],
	)


# ---------------------------------------------------------------------------
# BI
# ---------------------------------------------------------------------------


def tax_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	kpis = [
		_bi_kpi("tax-internal", _("فروش داخلی ثبت‌شده"), flt(summary.get("internal_sales_total")), "money", None),
		_bi_kpi("tax-sent", _("ارسال‌شده به سامانه"), flt(summary.get("sent_sales_total")), "money", None),
		_bi_kpi("tax-diff", _("مابه‌التفاوت ارسال"), flt(summary.get("unmatched_sales")), "money", None),
		_bi_kpi("tax-tax", _("مالیات ثبت‌شده"), flt(summary.get("internal_tax_total")), "money", None),
	]
	charts = [
		{
			"key": "tax-compare",
			"type": "bar",
			"title": _("مقایسه ماهانه فروش ثبت‌شده و ارسالی"),
			"categories": [r.get("period") for r in rows],
			"series": [
				{"key": "internal", "label": _("فروش داخلی"), "color": "#3e8ed0", "values": [flt(r.get("internal_sales")) for r in rows]},
				{"key": "sent", "label": _("ارسال‌شده"), "color": "#2f6f5c", "values": [flt(r.get("sent_sales")) for r in rows]},
			],
		}
	]
	tables = [
		{"key": "tax-table", "title": _("جزئیات ماهانه تطبیق"), "columns": _table_columns_from_rows(rows), "rows": rows},
	]
	insights = []
	if flt(summary.get("unmatched_sales")) > 0:
		insights.append(
			{
				"key": "tax-gap",
				"severity": "warn",
				"text": _("به مبلغ {0} فروش هنوز به سامانه مودیان ارسال نشده است.").format(f"{flt(summary.get('unmatched_sales')):,}"),
			}
		)
	else:
		insights.append({"key": "tax-ok", "severity": "info", "text": _("گزارش فروش داخلی با ارسالی‌ها به سامانه مالیاتی تطابق دارد.")})
	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _tax_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_tax_register_into_api_module()
