import frappe
from frappe import _

from restaurant.activity_tracking import service


def execute(filters=None):
    filters = filters or {}
    service.ensure_management_access()

    columns = [
        {"label": _("Date"), "fieldname": "summary_date", "fieldtype": "Date", "width": 110},
        {"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 170},
        {"label": _("Online Hours"), "fieldname": "online_hours", "fieldtype": "Float", "width": 120},
        {"label": _("Active Hours"), "fieldname": "active_hours", "fieldtype": "Float", "width": 120},
        {"label": _("Idle Hours"), "fieldname": "idle_hours", "fieldtype": "Float", "width": 120},
        {"label": _("Active %"), "fieldname": "active_ratio", "fieldtype": "Percent", "width": 100},
        {"label": _("Outputs"), "fieldname": "outputs_count", "fieldtype": "Int", "width": 90},
        {
            "label": _("Outputs / Active Hour"),
            "fieldname": "outputs_per_active_hour",
            "fieldtype": "Float",
            "width": 170,
        },
    ]

    rows = service.get_summary_rows(filters)
    data = []
    total_online = 0
    total_active = 0
    total_idle = 0

    for row in rows:
        online_seconds = frappe.utils.cint(row.online_seconds or 0)
        active_seconds = frappe.utils.cint(row.active_seconds or 0)
        idle_seconds = frappe.utils.cint(row.idle_seconds or 0)

        total_online += online_seconds
        total_active += active_seconds
        total_idle += idle_seconds

        data.append(
            {
                "summary_date": row.summary_date,
                "user": row.user,
                "online_hours": round(online_seconds / 3600.0, 2),
                "active_hours": round(active_seconds / 3600.0, 2),
                "idle_hours": round(idle_seconds / 3600.0, 2),
                "active_ratio": row.active_ratio,
                "outputs_count": row.outputs_count,
                "outputs_per_active_hour": row.outputs_per_active_hour,
            }
        )

    chart = {
        "data": {
            "labels": [d["summary_date"] for d in data[:20]][::-1],
            "datasets": [
                {
                    "name": _("Active Hours"),
                    "values": [d["active_hours"] for d in data[:20]][::-1],
                },
                {
                    "name": _("Idle Hours"),
                    "values": [d["idle_hours"] for d in data[:20]][::-1],
                },
            ],
        },
        "type": "bar",
    }

    summary = [
        {
            "label": _("Total Online Hours"),
            "value": round(total_online / 3600.0, 2),
            "indicator": "blue",
        },
        {
            "label": _("Total Active Hours"),
            "value": round(total_active / 3600.0, 2),
            "indicator": "green",
        },
        {
            "label": _("Total Idle Hours"),
            "value": round(total_idle / 3600.0, 2),
            "indicator": "orange",
        },
    ]

    return columns, data, None, chart, summary
