import json

import frappe

from restaurant.activity_tracking import service


def _parse_payload(payload):
    if payload is None:
        payload = frappe.form_dict.get("payload")

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            return {}

    return {}


@frappe.whitelist(methods=["POST"])
def heartbeat(payload=None):
    parsed = _parse_payload(payload)
    return service.process_heartbeat(parsed)


@frappe.whitelist(methods=["POST"])
def flush_events(payload=None):
    parsed = _parse_payload(payload)
    if not parsed.get("events"):
        return {"ok": True, "message": "No events to persist."}

    parsed.setdefault("status_hint", parsed.get("status_hint") or "active")
    return service.process_heartbeat(parsed)


@frappe.whitelist(methods=["POST"])
def close_session(reason=None):
    reason = (reason or "logout").strip().lower()
    closed = service.close_open_session(reason=reason)
    return {"ok": True, "session_name": closed}


@frappe.whitelist()
def get_employee_activity_summary(filters=None):
    service.ensure_management_access()

    parsed_filters = _parse_payload(filters)
    rows = service.get_summary_rows(parsed_filters)

    return {
        "ok": True,
        "rows": rows,
        "count": len(rows),
    }


def on_session_creation(login_manager=None):
    user = frappe.session.user
    settings = service.get_tracker_settings()
    if not service.is_user_trackable(user, settings=settings):
        return

    service.get_or_create_open_session(user=user, sid=frappe.session.sid)


def on_logout(login_manager=None):
    user = frappe.session.user
    settings = service.get_tracker_settings()
    if not service.is_user_trackable(user, settings=settings):
        return

    service.close_open_session(user=user, sid=frappe.session.sid, reason="logout")
