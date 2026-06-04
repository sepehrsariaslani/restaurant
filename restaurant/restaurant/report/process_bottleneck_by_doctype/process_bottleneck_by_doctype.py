import frappe
from frappe import _

from restaurant.activity_tracking import service


def execute(filters=None):
    filters = filters or {}
    service.ensure_management_access()

    conditions = ["status = 'active'"]
    values = {}

    if filters.get("date_from"):
        conditions.append("slice_date >= %(date_from)s")
        values["date_from"] = filters.get("date_from")

    if filters.get("date_to"):
        conditions.append("slice_date <= %(date_to)s")
        values["date_to"] = filters.get("date_to")

    if filters.get("user"):
        conditions.append("user = %(user)s")
        values["user"] = filters.get("user")

    where_clause = " and ".join(conditions)

    rows = frappe.db.sql(
        f"""
        select
            case when ifnull(ref_doctype, '') = '' then '(No DocType)' else ref_doctype end as ref_doctype,
            count(*) as slices_count,
            count(distinct user) as users_count,
            sum(duration_seconds) as total_seconds,
            avg(duration_seconds) as avg_seconds,
            sum(case when is_pos = 1 then duration_seconds else 0 end) as pos_seconds
        from `tabEmployee Activity Slice`
        where {where_clause}
        group by case when ifnull(ref_doctype, '') = '' then '(No DocType)' else ref_doctype end
        order by total_seconds desc
        """,
        values,
        as_dict=True,
    )

    columns = [
        {"label": _("DocType"), "fieldname": "ref_doctype", "fieldtype": "Data", "width": 220},
        {"label": _("Total Active Hours"), "fieldname": "total_active_hours", "fieldtype": "Float", "width": 150},
        {
            "label": _("Average Minutes per Slice"),
            "fieldname": "avg_minutes_per_slice",
            "fieldtype": "Float",
            "width": 180,
        },
        {"label": _("Slices"), "fieldname": "slices_count", "fieldtype": "Int", "width": 100},
        {"label": _("Users"), "fieldname": "users_count", "fieldtype": "Int", "width": 90},
        {"label": _("POS Share %"), "fieldname": "pos_share_percent", "fieldtype": "Percent", "width": 120},
    ]

    data = []
    labels = []
    chart_values = []

    for row in rows:
        total_seconds = frappe.utils.cint(row.total_seconds or 0)
        pos_seconds = frappe.utils.cint(row.pos_seconds or 0)
        pos_share = 0
        if total_seconds > 0:
            pos_share = round((pos_seconds * 100.0) / total_seconds, 2)

        item = {
            "ref_doctype": row.ref_doctype,
            "total_active_hours": round(total_seconds / 3600.0, 2),
            "avg_minutes_per_slice": round((frappe.utils.flt(row.avg_seconds or 0)) / 60.0, 2),
            "slices_count": row.slices_count,
            "users_count": row.users_count,
            "pos_share_percent": pos_share,
        }
        data.append(item)

        if len(labels) < 10:
            labels.append(item["ref_doctype"])
            chart_values.append(item["total_active_hours"])

    chart = {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": _("Active Hours"),
                    "values": chart_values,
                }
            ],
        },
        "type": "bar",
    }

    return columns, data, None, chart
