# Copyright (c) 2026, Restaurant and contributors
"""Integrated cloud accounting surface.

The actual books live in ERPNext (Chart of Accounts, Journal Entries,
Payment Entries, Opening Entries, GL, financial statements, fiscal-year
closing) — this module adds the restaurant management surface on top:
live KPIs (cash/bank, receivables/payables), daily receipt/payment
balances and a DIN to the standard ERPNext desk pages.

Endpoints are re-exported into ``restaurant.api`` (star-import at the
bottom of ``api.py``) and called as ``/api/method/restaurant.api.<endpoint>``.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, today

from restaurant.api import (
	_bi_kpi,
	_compose_management_report,
	_ensure_management_access,
	_management_datetime_bounds,
	_table_columns_from_rows,
)

__all__ = [
	"ACC_REPORT_KEYS",
	"acc_build_report_bi",
	"get_management_accounting_boot",
	"get_management_report_receipt_payment_balance",
]

ACC_REPORT_KEYS = {"receipt-payment-balance"}

DESK_LINKS = [
	{"key": "coa", "label": "درخت حساب‌ها (کل/معین/تفصیلی)", "url": "/app/account/view/Chart of Accounts", "desc": "ساختار درختی حساب‌های حسابداری"},
	{"key": "journal", "label": "سند حسابداری (دستی/پیش‌نویس)", "url": "/app/journal-entry", "desc": "ثبت سند دستی و پیش‌نویس"},
	{"key": "opening", "label": "تراز افتتاحیه", "url": "/app/opening-invoice-creation-tool", "desc": "ثبت موجودی و تراز دوره اول"},
	{"key": "payment-entry", "label": "دریافت و پرداخت", "url": "/app/payment-entry", "desc": "اسناد دریافت (نقدی/بانکی/چک) و پرداخت"},
	{"key": "gl", "label": "دفتر کل (گردش حساب‌ها)", "url": "/app/query-report/General Ledger", "desc": "گزارش تفصیلی بدهکار/بستانکار هر حساب"},
	{"key": "trial-balance", "label": "تراز آزمایشی", "url": "/app/query-report/Trial Balance", "desc": "تراز کل حساب‌ها"},
	{"key": "ar", "label": "بدهکاران (دریافتنی)", "url": "/app/query-report/Accounts Receivable", "desc": "مانده مشتریان بدهکار"},
	{"key": "ap", "label": "بستانکاران (پرداختنی)", "url": "/app/query-report/Accounts Payable", "desc": "مانده تأمین‌کنندگان و بستانکاران"},
	{"key": "balance-sheet", "label": "ترازنامه", "url": "/app/query-report/Balance Sheet", "desc": "صورت مالی استاندارد"},
	{"key": "pnl", "label": "سود و زیان", "url": "/app/query-report/Profit and Loss Statement", "desc": "صورت سود و زیان"},
	{"key": "cashflow", "label": "جریان وجوه نقد", "url": "/app/query-report/Cash Flow", "desc": "صورت جریان نقدینگی"},
	{"key": "closing", "label": "بستن سال مالی", "url": "/app/period-closing-voucher", "desc": "بستن حساب‌ها و انتقال به سال جدید"},
]


# ---------------------------------------------------------------------------
# KPI helpers
# ---------------------------------------------------------------------------


def _acc_gl_balance(root_types=None, account_types=None, upto=None):
	"""Cash/bank style balance from posted GL entries."""
	if not frappe.db.exists("DocType", "GL Entry"):
		return 0.0
	clauses = ["gle.is_cancelled = 0"]
	params = {}
	if root_types:
		clauses.append("acc.root_type IN %(root)s")
		params["root"] = tuple(root_types)
	if account_types:
		clauses.append("acc.account_type IN %(atypes)s")
		params["atypes"] = tuple(account_types)
	if upto:
		clauses.append("gle.posting_date <= %(upto)s")
		params["upto"] = upto
	row = frappe.db.sql(
		f"""
		SELECT COALESCE(SUM(gle.debit - gle.credit), 0) AS balance
		FROM `tabGL Entry` gle
		INNER JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE {' AND '.join(clauses)}
		""",
		params,
		as_dict=True,
	)
	return flt(row[0].get("balance")) if row else 0.0


def _acc_payment_totals(date_from=None, date_to=None):
	"""Receive/pay totals from submitted Payment Entries in a window."""
	if not frappe.db.exists("DocType", "Payment Entry"):
		return {"receive": 0.0, "pay": 0.0}
	clauses = ["docstatus = 1"]
	params = {}
	if date_from:
		clauses.append("posting_date >= %(df)s")
		params["df"] = date_from
	if date_to:
		clauses.append("posting_date <= %(dt)s")
		params["dt"] = date_to
	rows = frappe.db.sql(
		f"""
		SELECT payment_type, COALESCE(SUM(paid_amount),0) AS total
		FROM `tabPayment Entry`
		WHERE {' AND '.join(clauses)}
		GROUP BY payment_type
		""",
		params,
		as_dict=True,
	)
	out = {"receive": 0.0, "pay": 0.0}
	for row in rows:
		if row["payment_type"] == "Receive":
			out["receive"] = flt(row["total"])
		elif row["payment_type"] == "Pay":
			out["pay"] = flt(row["total"])
	return out


@frappe.whitelist()
def get_management_accounting_boot():
	_ensure_management_access()
	oko = frappe.db.exists("DocType", "GL Entry")
	cash_balance = _acc_gl_balance(account_types=["Cash"]) if oko else 0.0
	bank_balance = _acc_gl_balance(account_types=["Bank"]) if oko else 0.0
	receivables = payables = 0.0
	if frappe.db.exists("DocType", "Sales Invoice"):
		row = frappe.db.sql("SELECT COALESCE(SUM(outstanding_amount),0) AS t FROM `tabSales Invoice` WHERE docstatus = 1 AND outstanding_amount > 0", as_dict=True)
		receivables = flt(row[0]["t"]) if row else 0.0
	if frappe.db.exists("DocType", "Purchase Invoice"):
		row = frappe.db.sql("SELECT COALESCE(SUM(outstanding_amount),0) AS t FROM `tabPurchase Invoice` WHERE docstatus = 1 AND outstanding_amount > 0", as_dict=True)
		payables = flt(row[0]["t"]) if row else 0.0
	today_flow = _acc_payment_totals(today(), today())
	recent_entries = []
	if frappe.db.exists("DocType", "Journal Entry"):
		recent_entries = frappe.get_all(
			"Journal Entry",
			fields=["name", "posting_date", "total_debit", "docstatus", "user_remark"],
			order_by="creation desc",
			limit_page_length=5,
		)
		recent_entries = [
			{
				"name": r["name"],
				"posting_date": str(r.get("posting_date") or ""),
				"total_debit": flt(r.get("total_debit")),
				"status": "ثبت‌شده" if cint(r.get("docstatus")) == 1 else ("لغوشده" if cint(r.get("docstatus")) == 2 else "پیش‌نویس"),
				"user_remark": (r.get("user_remark") or "")[:120],
			}
			for r in recent_entries
		]
	return {
		"kpis": {
			"cash_balance": cash_balance,
			"bank_balance": bank_balance,
			"receivables": receivables,
			"payables": payables,
			"today_receipts": today_flow["receive"],
			"today_payments": today_flow["pay"],
		},
		"recent_journal_entries": recent_entries,
		"desk_links": DESK_LINKS,
	}


# ---------------------------------------------------------------------------
# Daily/periodic receipt-payment balance report
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_management_report_receipt_payment_balance(date_from=None, date_to=None):
	_ensure_management_access()
	rows = []
	summary = {"days": 0, "receipts_total": 0.0, "payments_total": 0.0, "net_total": 0.0, "by_mop": []}
	if frappe.db.exists("DocType", "Payment Entry"):
		start_dt, end_dt = _management_datetime_bounds(date_from=date_from, date_to=date_to)
		clauses = ["docstatus = 1", "posting_date BETWEEN %(df)s AND %(dt)s"]
		params = {"df": str(start_dt)[:10], "dt": str(end_dt)[:10]}
		daily = frappe.db.sql(
			f"""
			SELECT posting_date,
				   SUM(CASE WHEN payment_type = 'Receive' THEN paid_amount ELSE 0 END) AS receipts,
				   SUM(CASE WHEN payment_type = 'Pay' THEN paid_amount ELSE 0 END) AS payments,
				   COUNT(*) AS entries
			FROM `tabPayment Entry`
			WHERE {' AND '.join(clauses)}
			GROUP BY posting_date ORDER BY posting_date
			""",
			params,
			as_dict=True,
		)
		mop = frappe.db.sql(
			f"""
			SELECT payment_type, mode_of_payment, COALESCE(SUM(paid_amount),0) AS total, COUNT(*) AS entries
			FROM `tabPayment Entry`
			WHERE {' AND '.join(clauses)}
			GROUP BY payment_type, mode_of_payment
			ORDER BY total DESC
			""",
			params,
			as_dict=True,
		)
		for row in daily:
			receipts = flt(row["receipts"])
			payments = flt(row["payments"])
			rows.append(
				{
					"date": str(row["posting_date"]),
					"entries": cint(row["entries"]),
					"receipts": receipts,
					"payments": payments,
					"net": flt(receipts - payments),
					"balance_run": 0.0,
				}
			)
		running = 0.0
		for row in rows:
			running += flt(row["net"])
			row["balance_run"] = flt(running)
		summary.update(
			{
				"days": len(rows),
				"receipts_total": flt(sum(r["receipts"] for r in rows)),
				"payments_total": flt(sum(r["payments"] for r in rows)),
				"net_total": flt(sum(r["net"] for r in rows)),
				"by_mop": [
					{
						"payment_type": _("دریافت") if m["payment_type"] == "Receive" else (_("پرداخت") if m["payment_type"] == "Pay" else m["payment_type"]),
						"mode_of_payment": m.get("mode_of_payment") or "-",
						"entries": cint(m["entries"]),
						"total": flt(m["total"]),
					}
					for m in mop
				],
			}
		)
	return _compose_management_report(
		"receipt-payment-balance",
		_("تراز دریافت و پرداخت"),
		summary,
		rows,
		date_from=date_from,
		date_to=date_to,
		orders=[],
	)


# ---------------------------------------------------------------------------
# BI
# ---------------------------------------------------------------------------


def acc_build_report_bi(report_key, title, summary, rows, orders, previous_orders, meta):
	kpis = [
		_bi_kpi("rp-receipts", _("مجموع دریافت‌ها"), flt(summary.get("receipts_total")), "money", None),
		_bi_kpi("rp-payments", _("مجموع پرداخت‌ها"), flt(summary.get("payments_total")), "money", None),
		_bi_kpi("rp-net", _("خالص جریان نقد"), flt(summary.get("net_total")), "money", None),
		_bi_kpi("rp-days", _("روزهای دارای سند"), cint(summary.get("days")), "count", None),
	]
	charts = [
		{
			"key": "rp-line",
			"type": "line",
			"title": _("تراز روزانه دریافت/پرداخت"),
			"categories": [r.get("date") for r in rows],
			"series": [
				{"key": "receipts", "label": _("دریافت"), "color": "#2f6f5c", "values": [flt(r.get("receipts")) for r in rows]},
				{"key": "payments", "label": _("پرداخت"), "color": "#b84f4f", "values": [flt(r.get("payments")) for r in rows]},
			],
		}
	]
	tables = [
		{"key": "rp-daily", "title": _("تراز روزانه"), "columns": _table_columns_from_rows(rows), "rows": rows},
		{"key": "rp-mop", "title": _("تفکیک روش‌های دریافت/پرداخت"), "columns": _table_columns_from_rows(summary.get("by_mop") or []), "rows": summary.get("by_mop") or []},
	]
	insights = []
	top = next(iter(summary.get("by_mop") or []), None)
	if top:
		insights.append(
			{
				"key": "rp-top",
				"severity": "info",
				"text": _("پربازدیدترین روش تسویه: «{0}» ({1}) با مبلغ {2}.").format(top.get("mode_of_payment"), top.get("payment_type"), f"{flt(top.get('total')):,}"),
			}
		)
	return {"kpis": kpis, "charts": charts, "tables": tables, "insights": insights}


# ---------------------------------------------------------------------------
# Re-export into restaurant.api (robust against partial imports)
# ---------------------------------------------------------------------------


def _acc_register_into_api_module():
	import sys

	api_module = sys.modules.get("restaurant.api")
	if api_module is None:
		return
	for _name in __all__:
		if _name in globals():
			setattr(api_module, _name, globals()[_name])


_acc_register_into_api_module()
