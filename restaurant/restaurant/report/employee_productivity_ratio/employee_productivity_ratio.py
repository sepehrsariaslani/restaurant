import frappe
from frappe import _

from restaurant.activity_tracking import service


def execute(filters=None):
    filters = filters or {}
    service.ensure_management_access()

    columns = [
        {"label": _("Date"), "fieldname": "summary_date", "fieldtype": "Date", "width": 110},
        {"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 180},
        {"label": _("Active Hours"), "fieldname": "active_hours", "fieldtype": "Float", "width": 120},
        {"label": _("Outputs"), "fieldname": "outputs_count", "fieldtype": "Int", "width": 95},
        {
            "label": _("Outputs / Active Hour"),
            "fieldname": "outputs_per_active_hour",
            "fieldtype": "Float",
            "width": 170,
        },
        {"label": _("Sales Invoices"), "fieldname": "sales_invoice_count", "fieldtype": "Int", "width": 120},
        {
            "label": _("Purchase Invoices"),
            "fieldname": "purchase_invoice_count",
            "fieldtype": "Int",
            "width": 135,
        },
        {"label": _("Payment Entries"), "fieldname": "payment_entry_count", "fieldtype": "Int", "width": 120},
        {"label": _("Journal Entries"), "fieldname": "journal_entry_count", "fieldtype": "Int", "width": 120},
    ]

    rows = service.get_summary_rows(filters)
    data = []

    for row in rows:
        active_seconds = frappe.utils.cint(row.active_seconds or 0)
        data.append(
            {
                "summary_date": row.summary_date,
                "user": row.user,
                "active_hours": round(active_seconds / 3600.0, 2),
                "outputs_count": row.outputs_count,
                "outputs_per_active_hour": row.outputs_per_active_hour,
                "sales_invoice_count": row.sales_invoice_count,
                "purchase_invoice_count": row.purchase_invoice_count,
                "payment_entry_count": row.payment_entry_count,
                "journal_entry_count": row.journal_entry_count,
            }
        )

    return columns, data
