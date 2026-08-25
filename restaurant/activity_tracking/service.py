import json
from datetime import datetime

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime, getdate, now_datetime

from restaurant.activity_tracking.constants import (
    DEFAULT_ACTIVE_WINDOW_MINUTES,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    DEFAULT_IDLE_AFTER_MINUTES,
    DEFAULT_MAX_EVENT_BATCH_SIZE,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_SESSION_TIMEOUT_MINUTES,
    EVENT_TYPES,
    OUTPUT_DOCTYPES,
    SESSION_CLOSED,
    SESSION_OPEN,
    SESSION_TIMED_OUT,
    STATUS_ACTIVE,
    STATUS_IDLE,
    TRACKED_ROLES_DEFAULT,
)


def get_tracker_settings() -> dict:
    defaults = {
        "enabled": 1,
        "track_desk_routes": 1,
        "track_pos_routes": 1,
        "allow_guest": 0,
        "heartbeat_interval_seconds": DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
        "active_window_minutes": DEFAULT_ACTIVE_WINDOW_MINUTES,
        "idle_after_minutes": DEFAULT_IDLE_AFTER_MINUTES,
        "session_timeout_minutes": DEFAULT_SESSION_TIMEOUT_MINUTES,
        "raw_retention_days": DEFAULT_RETENTION_DAYS,
        "max_event_batch_size": DEFAULT_MAX_EVENT_BATCH_SIZE,
        "tracked_roles": TRACKED_ROLES_DEFAULT,
    }

    if not frappe.db.exists("DocType", "Employee Activity Settings"):
        return defaults

    doc = frappe.get_cached_doc("Employee Activity Settings")
    settings = {
        "enabled": cint(doc.get("enabled") or defaults["enabled"]),
        "track_desk_routes": cint(doc.get("track_desk_routes") or 0),
        "track_pos_routes": cint(doc.get("track_pos_routes") or 0),
        "allow_guest": cint(doc.get("allow_guest") or 0),
        "heartbeat_interval_seconds": max(
            cint(doc.get("heartbeat_interval_seconds") or defaults["heartbeat_interval_seconds"]),
            20,
        ),
        "active_window_minutes": max(
            cint(doc.get("active_window_minutes") or defaults["active_window_minutes"]),
            1,
        ),
        "idle_after_minutes": max(
            cint(doc.get("idle_after_minutes") or defaults["idle_after_minutes"]),
            2,
        ),
        "session_timeout_minutes": max(
            cint(doc.get("session_timeout_minutes") or defaults["session_timeout_minutes"]),
            5,
        ),
        "raw_retention_days": max(cint(doc.get("raw_retention_days") or defaults["raw_retention_days"]), 1),
        "max_event_batch_size": max(
            cint(doc.get("max_event_batch_size") or defaults["max_event_batch_size"]),
            10,
        ),
        "tracked_roles": (doc.get("tracked_roles") or TRACKED_ROLES_DEFAULT).strip(),
    }

    if settings["idle_after_minutes"] <= settings["active_window_minutes"]:
        settings["idle_after_minutes"] = settings["active_window_minutes"] + 1

    return settings


def _parse_role_list(raw_value: str) -> set[str]:
    roles = set()
    for line in (raw_value or "").replace(",", "\n").splitlines():
        role = (line or "").strip()
        if role:
            roles.add(role)
    return roles


def is_user_trackable(user: str, settings: dict | None = None) -> bool:
    if not user:
        return False

    settings = settings or get_tracker_settings()
    if not cint(settings.get("enabled")):
        return False

    if user == "Guest":
        return cint(settings.get("allow_guest")) == 1

    required_roles = _parse_role_list(settings.get("tracked_roles") or "")
    if not required_roles:
        return True

    user_roles = set(frappe.get_roles(user))
    return bool(user_roles.intersection(required_roles))


def _normalize_datetime(value, fallback: datetime) -> datetime:
    if not value:
        return fallback

    try:
        return get_datetime(value)
    except Exception:
        return fallback


def _to_int_seconds(value) -> int:
    try:
        return max(cint(value), 0)
    except Exception:
        return 0


def _normalize_route_context(payload: dict | None, settings: dict) -> dict:
    payload = payload or {}

    route = (payload.get("route") or "").strip()
    doctype = (payload.get("doctype") or "").strip()
    docname = (payload.get("docname") or "").strip()

    lowered_route = route.lower()
    inferred_pos = bool(
        cint(payload.get("is_pos") or 0)
        or "point-of-sale" in lowered_route
        or lowered_route.startswith("app/point-of-sale")
        or lowered_route.startswith("point-of-sale")
        or doctype in {"POS Invoice", "POS Opening Entry", "POS Closing Entry"}
    )

    if inferred_pos and not cint(settings.get("track_pos_routes")):
        return {
            "route": route,
            "doctype": doctype,
            "docname": docname,
            "is_pos": 1,
            "ignore": True,
        }

    if (not inferred_pos) and not cint(settings.get("track_desk_routes")):
        return {
            "route": route,
            "doctype": doctype,
            "docname": docname,
            "is_pos": 0,
            "ignore": True,
        }

    return {
        "route": route[:240],
        "doctype": doctype[:140],
        "docname": docname[:140],
        "is_pos": 1 if inferred_pos else 0,
        "ignore": False,
    }


def _normalize_status(payload: dict | None, settings: dict) -> str:
    payload = payload or {}

    hint = (payload.get("status_hint") or "").strip().lower()
    if hint in {STATUS_ACTIVE, STATUS_IDLE}:
        return hint

    inactive_seconds = flt(payload.get("inactive_seconds") or 0)
    idle_after_seconds = cint(settings.get("idle_after_minutes") or DEFAULT_IDLE_AFTER_MINUTES) * 60

    if inactive_seconds >= idle_after_seconds:
        return STATUS_IDLE

    return STATUS_ACTIVE


def _find_open_session(user: str, sid: str | None = None):
    query = """
        select name
        from `tabEmployee Activity Session`
        where user = %s
          and status = %s
    """
    values = [user, SESSION_OPEN]

    if sid:
        query += " and session_id = %s"
        values.append(sid)

    query += " order by modified desc limit 1"

    row = frappe.db.sql(query, values, as_dict=True)
    return row[0].name if row else ""


def get_or_create_open_session(user: str, sid: str | None = None, now_dt: datetime | None = None):
    now_dt = now_dt or now_datetime()
    existing = _find_open_session(user, sid=sid)

    if existing:
        return frappe.get_doc("Employee Activity Session", existing)

    if sid:
        fallback = _find_open_session(user)
        if fallback:
            return frappe.get_doc("Employee Activity Session", fallback)

    session = frappe.get_doc(
        {
            "doctype": "Employee Activity Session",
            "user": user,
            "site": frappe.local.site,
            "session_id": (sid or "")[:140],
            "status": SESSION_OPEN,
            "session_start": now_dt,
            "last_heartbeat": now_dt,
        }
    )
    session.insert(ignore_permissions=True)
    return session


def _find_open_slice(session_name: str) -> str:
    rows = frappe.db.sql(
        """
        select name
        from `tabEmployee Activity Slice`
        where activity_session = %s
          and ifnull(to_time, '') = ''
        order by from_time desc
        limit 1
        """,
        (session_name,),
        as_dict=True,
    )
    return rows[0].name if rows else ""


def _duration_seconds(from_time, to_time) -> int:
    if not from_time or not to_time:
        return 0

    delta = (get_datetime(to_time) - get_datetime(from_time)).total_seconds()
    return max(int(delta), 0)


def _close_slice(slice_doc, to_time: datetime):
    if slice_doc.to_time:
        return

    if to_time < get_datetime(slice_doc.from_time):
        to_time = get_datetime(slice_doc.from_time)

    slice_doc.to_time = to_time
    slice_doc.duration_seconds = _duration_seconds(slice_doc.from_time, to_time)
    slice_doc.save(ignore_permissions=True)


def _upsert_slice(
    user: str,
    session_name: str,
    status: str,
    context: dict,
    occurred_at: datetime,
):
    open_slice_name = _find_open_slice(session_name)
    if open_slice_name:
        open_slice = frappe.get_doc("Employee Activity Slice", open_slice_name)

        unchanged = (
            (open_slice.status or "") == status
            and (open_slice.route or "") == context.get("route", "")
            and (open_slice.ref_doctype or "") == context.get("doctype", "")
            and (open_slice.ref_docname or "") == context.get("docname", "")
            and cint(open_slice.is_pos or 0) == cint(context.get("is_pos") or 0)
        )
        if unchanged:
            return open_slice

        _close_slice(open_slice, occurred_at)

    new_slice = frappe.get_doc(
        {
            "doctype": "Employee Activity Slice",
            "user": user,
            "activity_session": session_name,
            "from_time": occurred_at,
            "status": status,
            "route": context.get("route") or "",
            "ref_doctype": context.get("doctype") or "",
            "ref_docname": context.get("docname") or "",
            "is_pos": cint(context.get("is_pos") or 0),
            "slice_date": getdate(occurred_at),
        }
    )
    new_slice.insert(ignore_permissions=True)
    return new_slice


def _sync_session_snapshot(session_name: str, occurred_at: datetime, context: dict):
    frappe.db.set_value(
        "Employee Activity Session",
        session_name,
        {
            "last_heartbeat": occurred_at,
            "last_route": context.get("route") or "",
            "last_doctype": context.get("doctype") or "",
            "last_docname": context.get("docname") or "",
            "is_pos": cint(context.get("is_pos") or 0),
        },
        update_modified=False,
    )


def _normalize_event_row(row: dict | str, context: dict, occurred_at: datetime) -> dict:
    if isinstance(row, str):
        row = {"event_type": row}
    elif not isinstance(row, dict):
        row = {}

    event_type = (row.get("event_type") or row.get("type") or "").strip().lower()
    if event_type not in EVENT_TYPES:
        return {}

    return {
        "event_type": event_type,
        "event_ts": _normalize_datetime(row.get("event_ts") or row.get("ts"), occurred_at),
        "route": (row.get("route") or context.get("route") or "")[:240],
        "ref_doctype": (row.get("doctype") or context.get("doctype") or "")[:140],
        "ref_docname": (row.get("docname") or context.get("docname") or "")[:140],
        "is_pos": cint(row.get("is_pos") if row.get("is_pos") is not None else context.get("is_pos") or 0),
        "meta_json": json.dumps(row.get("meta") or {}, ensure_ascii=True),
    }


def _record_events(user: str, session_name: str, events: list, context: dict, occurred_at: datetime, settings: dict):
    if not events:
        return

    max_size = cint(settings.get("max_event_batch_size") or DEFAULT_MAX_EVENT_BATCH_SIZE)
    for raw in events[:max_size]:
        normalized = _normalize_event_row(raw, context, occurred_at)
        if not normalized:
            continue

        doc = frappe.get_doc(
            {
                "doctype": "Employee Activity Event",
                "user": user,
                "activity_session": session_name,
                **normalized,
            }
        )
        doc.insert(ignore_permissions=True)


def process_heartbeat(payload: dict | None = None) -> dict:
    payload = payload or {}
    user = frappe.session.user
    settings = get_tracker_settings()

    if not is_user_trackable(user, settings=settings):
        return {
            "ok": True,
            "tracking_enabled": False,
            "reason": "user_not_trackable",
            "next_interval_sec": settings["heartbeat_interval_seconds"],
        }

    occurred_at = _normalize_datetime(payload.get("client_ts") or payload.get("event_ts"), now_datetime())
    context = _normalize_route_context(payload, settings)

    if context.get("ignore"):
        return {
            "ok": True,
            "tracking_enabled": True,
            "ignored": True,
            "next_interval_sec": settings["heartbeat_interval_seconds"],
        }

    session = get_or_create_open_session(user=user, sid=frappe.session.sid, now_dt=occurred_at)
    status = _normalize_status(payload, settings)
    active_slice = _upsert_slice(user, session.name, status, context, occurred_at)

    events = payload.get("events") or []
    if isinstance(events, dict):
        events = [events]
    elif not isinstance(events, list):
        events = []
    if not events:
        events = [{"event_type": "heartbeat", "event_ts": occurred_at.isoformat()}]

    _record_events(
        user=user,
        session_name=session.name,
        events=events,
        context=context,
        occurred_at=occurred_at,
        settings=settings,
    )
    _sync_session_snapshot(session.name, occurred_at, context)

    return {
        "ok": True,
        "tracking_enabled": True,
        "session_name": session.name,
        "slice_name": active_slice.name,
        "status": status,
        "server_ts": now_datetime().isoformat(),
        "next_interval_sec": settings["heartbeat_interval_seconds"],
    }


def _close_session_doc(session_doc, reason: str, end_time=None):
    end_time = _normalize_datetime(end_time, now_datetime())

    open_slice_name = _find_open_slice(session_doc.name)
    if open_slice_name:
        open_slice = frappe.get_doc("Employee Activity Slice", open_slice_name)
        _close_slice(open_slice, end_time)

    session_start = _normalize_datetime(session_doc.session_start, end_time)
    online_seconds = _duration_seconds(session_start, end_time)

    status = SESSION_TIMED_OUT if reason == "timeout" else SESSION_CLOSED
    session_doc.status = status
    session_doc.session_end = end_time
    session_doc.online_seconds = _to_int_seconds(online_seconds)
    session_doc.save(ignore_permissions=True)


def close_open_session(user: str | None = None, sid: str | None = None, reason: str = "logout"):
    user = user or frappe.session.user
    if not user:
        return ""

    open_name = _find_open_session(user, sid=sid)
    if not open_name and sid:
        open_name = _find_open_session(user)

    if not open_name:
        return ""

    session_doc = frappe.get_doc("Employee Activity Session", open_name)
    _close_session_doc(session_doc, reason=reason)
    return open_name


def close_timed_out_sessions() -> int:
    settings = get_tracker_settings()
    timeout_minutes = cint(settings.get("session_timeout_minutes") or DEFAULT_SESSION_TIMEOUT_MINUTES)
    cutoff = add_to_date(now_datetime(), minutes=-timeout_minutes)

    rows = frappe.db.sql(
        """
        select name
        from `tabEmployee Activity Session`
        where status = %s
          and ifnull(last_heartbeat, session_start) < %s
        """,
        (SESSION_OPEN, cutoff),
        as_dict=True,
    )

    closed = 0
    for row in rows:
        session_doc = frappe.get_doc("Employee Activity Session", row.name)
        _close_session_doc(session_doc, reason="timeout", end_time=cutoff)
        closed += 1

    return closed


def _summary_output_counts(user: str, target_date):
    result = {doctype: 0 for doctype in OUTPUT_DOCTYPES}

    for doctype in OUTPUT_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            continue

        conditions = {
            "docstatus": 1,
            "owner": user,
            "creation": ["between", [f"{target_date} 00:00:00", f"{target_date} 23:59:59"]],
        }
        result[doctype] = cint(frappe.db.count(doctype, conditions))

    return result


def _top_breakdown_for_day(user: str, target_date: str):
    rows = frappe.db.sql(
        """
        select
            ifnull(route, '') as route,
            ifnull(ref_doctype, '') as ref_doctype,
            sum(duration_seconds) as duration_seconds
        from `tabEmployee Activity Slice`
        where user = %s
          and slice_date = %s
          and status = %s
        group by route, ref_doctype
        order by duration_seconds desc
        limit 15
        """,
        (user, target_date, STATUS_ACTIVE),
        as_dict=True,
    )

    routes = []
    doctypes = []
    for row in rows:
        if row.route:
            routes.append({"route": row.route, "seconds": cint(row.duration_seconds)})
        if row.ref_doctype:
            doctypes.append({"doctype": row.ref_doctype, "seconds": cint(row.duration_seconds)})

    return {
        "routes": routes[:5],
        "doctypes": doctypes[:5],
    }


def aggregate_daily_activity(target_date=None) -> int:
    if target_date:
        summary_date = getdate(target_date)
    else:
        summary_date = getdate(add_to_date(now_datetime(), days=-1))

    rows = frappe.db.sql(
        """
        select
            user,
            sum(case when status = 'active' then duration_seconds else 0 end) as active_seconds,
            sum(case when status = 'idle' then duration_seconds else 0 end) as idle_seconds,
            sum(duration_seconds) as online_seconds
        from `tabEmployee Activity Slice`
        where slice_date = %s
        group by user
        """,
        (summary_date,),
        as_dict=True,
    )

    written = 0
    for row in rows:
        user = row.user
        online_seconds = cint(row.online_seconds or 0)
        active_seconds = cint(row.active_seconds or 0)
        idle_seconds = cint(row.idle_seconds or 0)

        active_ratio = 0
        if online_seconds > 0:
            active_ratio = round((active_seconds * 100.0) / online_seconds, 2)

        output_counts = _summary_output_counts(user, summary_date)
        total_outputs = sum(output_counts.values())
        outputs_per_active_hour = 0
        if active_seconds > 0:
            outputs_per_active_hour = round((total_outputs * 3600.0) / active_seconds, 2)

        top_breakdown = _top_breakdown_for_day(user, str(summary_date))

        existing = frappe.db.get_value(
            "Employee Activity Daily Summary",
            {"user": user, "summary_date": summary_date},
            "name",
        )

        values = {
            "user": user,
            "summary_date": summary_date,
            "online_seconds": online_seconds,
            "active_seconds": active_seconds,
            "idle_seconds": idle_seconds,
            "active_ratio": active_ratio,
            "outputs_count": total_outputs,
            "outputs_per_active_hour": outputs_per_active_hour,
            "sales_invoice_count": output_counts.get("Sales Invoice", 0),
            "purchase_invoice_count": output_counts.get("Purchase Invoice", 0),
            "payment_entry_count": output_counts.get("Payment Entry", 0),
            "journal_entry_count": output_counts.get("Journal Entry", 0),
            "top_routes_json": json.dumps(top_breakdown.get("routes") or [], ensure_ascii=True),
            "top_doctypes_json": json.dumps(top_breakdown.get("doctypes") or [], ensure_ascii=True),
        }

        if existing:
            frappe.db.set_value(
                "Employee Activity Daily Summary",
                existing,
                values,
                update_modified=False,
            )
        else:
            doc = frappe.get_doc({"doctype": "Employee Activity Daily Summary", **values})
            doc.insert(ignore_permissions=True)

        written += 1

    return written


def purge_raw_activity() -> dict:
    settings = get_tracker_settings()
    retention_days = cint(settings.get("raw_retention_days") or DEFAULT_RETENTION_DAYS)
    cutoff = add_to_date(now_datetime(), days=-retention_days)

    deleted_events = frappe.db.count("Employee Activity Event", {"event_ts": ["<", cutoff]})
    if deleted_events:
        frappe.db.delete("Employee Activity Event", {"event_ts": ["<", cutoff]})

    deleted_slices = frappe.db.count("Employee Activity Slice", {"from_time": ["<", cutoff]})
    if deleted_slices:
        frappe.db.delete("Employee Activity Slice", {"from_time": ["<", cutoff]})

    deleted_sessions = frappe.db.count(
        "Employee Activity Session",
        {"session_start": ["<", cutoff], "status": ["!=", SESSION_OPEN]},
    )
    if deleted_sessions:
        frappe.db.delete(
            "Employee Activity Session",
            {"session_start": ["<", cutoff], "status": ["!=", SESSION_OPEN]},
        )

    return {
        "retention_days": retention_days,
        "events_deleted": deleted_events,
        "slices_deleted": deleted_slices,
        "sessions_deleted": deleted_sessions,
    }


def ensure_management_access():
    roles = set(frappe.get_roles(frappe.session.user))
    if not roles.intersection({"System Manager", "HR Manager"}):
        frappe.throw(_("You do not have permission to view employee activity analytics."), frappe.PermissionError)


def get_summary_rows(filters: dict | None = None):
    filters = filters or {}
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")
    user = (filters.get("user") or "").strip()

    conditions = []
    values = {}

    if date_from:
        conditions.append("summary_date >= %(date_from)s")
        values["date_from"] = getdate(date_from)
    if date_to:
        conditions.append("summary_date <= %(date_to)s")
        values["date_to"] = getdate(date_to)
    if user:
        conditions.append("user = %(user)s")
        values["user"] = user

    where_sql = " and ".join(conditions)
    if where_sql:
        where_sql = f"where {where_sql}"

    return frappe.db.sql(
        f"""
        select
            summary_date,
            user,
            online_seconds,
            active_seconds,
            idle_seconds,
            active_ratio,
            outputs_count,
            outputs_per_active_hour,
            sales_invoice_count,
            purchase_invoice_count,
            payment_entry_count,
            journal_entry_count,
            top_routes_json,
            top_doctypes_json
        from `tabEmployee Activity Daily Summary`
        {where_sql}
        order by summary_date desc, active_seconds desc
        """,
        values,
        as_dict=True,
    )
