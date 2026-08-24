"""Fast/background POS operations and fail-safe POS boot helpers."""

import hashlib
import json
import time
import uuid

import frappe
from frappe import _


JOB_CACHE_PREFIX = "restaurant:pos:bg:"
JOB_TTL_SECONDS = 24 * 60 * 60


def _legacy_api():
    from restaurant import api as legacy
    return legacy


def _reliability_api():
    from restaurant import api_pos_reliability as reliability
    return reliability


def _as_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _parse_dict(value):
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _background_job_key(order_name, action):
    normalized_order = str(order_name or "").strip()
    normalized_action = str(action or "").strip().lower()
    digest = hashlib.sha1(
        f"{normalized_order}|{normalized_action}".encode("utf-8")
    ).hexdigest()[:20]
    return f"pos-bg-{digest}"


def _build_job_state(job_key, status, order_id="", action="", result=None, error=""):
    result = result if isinstance(result, dict) else {}
    return {
        "job_key": str(job_key or ""),
        "status": str(status or "unknown"),
        "order_id": str(order_id or ""),
        "action": str(action or ""),
        "sales_invoice": str(result.get("sales_invoice") or ""),
        "delivery_note": str(result.get("delivery_note") or ""),
        "error": str(error or "")[:500],
        "updated_at": int(time.time()),
    }


def _cache_key(job_key):
    return f"{JOB_CACHE_PREFIX}{str(job_key or '').strip()}"


def _cache_client():
    client = getattr(frappe, "cache", None)
    return client() if callable(client) else client


def _set_job_state(state):
    if not isinstance(state, dict) or not state.get("job_key"):
        return state
    client = _cache_client()
    if client is None:
        return state
    raw = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
    try:
        client.set_value(_cache_key(state["job_key"]), raw, expires_in_sec=JOB_TTL_SECONDS)
    except TypeError:
        client.set_value(_cache_key(state["job_key"]), raw)
    return state


def _get_job_state(job_key):
    client = _cache_client()
    if client is None:
        return None
    raw = client.get_value(_cache_key(job_key))
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    if isinstance(raw, dict):
        return raw
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _enqueue_worker(job_key, order_name, payment, deliver_after):
    try:
        from frappe.utils.background_jobs import enqueue
        enqueue(
            "restaurant.api_pos_background.run_pos_background_settlement",
            queue="short",
            job_name=job_key,
            job_key=job_key,
            order_name=order_name,
            payment=payment,
            deliver_after=1 if deliver_after else 0,
        )
    except Exception as exc:
        state = _build_job_state(
            job_key,
            "failed",
            order_name,
            "settle-deliver" if deliver_after else "settle",
            error=str(exc),
        )
        _set_job_state(state)
        raise


def _queue_existing_order(order_name, payment=None, deliver_after=False):
    legacy = _legacy_api()
    resolved = legacy._resolve_sales_order_name(order_name)
    if not resolved or not frappe.db.exists("Sales Order", resolved):
        frappe.throw(_("Sales Order not found."))

    action = "settle-deliver" if deliver_after else "settle"
    job_key = _background_job_key(resolved, action)
    existing = _get_job_state(job_key)
    if existing and existing.get("status") in {"queued", "running", "done"}:
        return existing

    state = _build_job_state(job_key, "queued", resolved, action)
    _set_job_state(state)
    _enqueue_worker(job_key, resolved, _parse_dict(payment), deliver_after)
    return state


@frappe.whitelist()
def enqueue_pos_settlement(order_name="", payment=None, deliver_after=0):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    if not str(order_name or "").strip():
        frappe.throw(_("Order name is required."))
    return _queue_existing_order(
        order_name,
        payment=payment,
        deliver_after=_as_bool(deliver_after),
    )


@frappe.whitelist()
def enqueue_pos_checkout(payload=None, deliver_after=0):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    data = _parse_dict(payload)
    if not data:
        frappe.throw(_("Invalid POS payload."))

    client_key = str(data.get("client_order_key") or "").strip()
    if not client_key:
        client_key = f"pos-bg-{uuid.uuid4().hex}"
        data["client_order_key"] = client_key

    replay = _reliability_api().replay_offline_pos_order(data)
    order_id = str(
        (replay or {}).get("order_id")
        or ((replay or {}).get("result") or {}).get("order_id")
        or ""
    ).strip()
    if not order_id:
        frappe.throw(_("POS order could not be created before background settlement."))

    state = _queue_existing_order(
        order_id,
        payment=data.get("payment") or {},
        deliver_after=_as_bool(deliver_after),
    )
    state = dict(state)
    state["order_id"] = order_id
    return state


def _delivery_completed(legacy, order_name):
    """Return whether the legacy delivery helper really finished.

    The legacy background delivery helper logs and swallows its own exceptions,
    so its return value alone cannot distinguish success from failure. Prefer
    the restaurant status field and fall back to an ERPNext Delivery Note link.
    """
    try:
        has_column = getattr(legacy, "_has_column", None)
        if callable(has_column) and has_column("Sales Order", "restaurant_status"):
            status = str(
                frappe.db.get_value("Sales Order", order_name, "restaurant_status") or ""
            ).strip().lower()
            return status == "delivered"
    except Exception:
        pass

    try:
        return bool(
            frappe.db.exists(
                "Delivery Note Item",
                {"against_sales_order": order_name, "docstatus": 1},
            )
        )
    except Exception:
        return False


def run_pos_background_settlement(job_key, order_name, payment=None, deliver_after=0):
    legacy = _legacy_api()
    deliver = _as_bool(deliver_after)
    action = "settle-deliver" if deliver else "settle"
    _set_job_state(_build_job_state(job_key, "running", order_name, action))
    try:
        result = legacy.settle_pos_order(
            order_name,
            payment=_parse_dict(payment),
            commit=True,
        )
        if not isinstance(result, dict):
            result = {}

        if deliver:
            # We are already inside an RQ worker. Run the heavy production /
            # stock / delivery flow here so the cashier request never waits.
            background_deliver = getattr(legacy, "_background_deliver_pos_order", None)
            if callable(background_deliver):
                background_deliver(order_name)
            else:
                legacy.deliver_pos_order(order_name)
            if not _delivery_completed(legacy, order_name):
                raise RuntimeError(
                    _("Delivery/production did not complete. Check background logs and retry delivery.")
                )

        state = _build_job_state(job_key, "done", order_name, action, result=result)
        _set_job_state(state)
        return state
    except Exception as exc:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        try:
            frappe.log_error(frappe.get_traceback(), "POS Background Settlement Error")
        except Exception:
            pass
        state = _build_job_state(
            job_key,
            "failed",
            order_name,
            action,
            error=str(exc),
        )
        _set_job_state(state)
        return state


@frappe.whitelist()
def get_pos_background_operation(job_key=""):
    legacy = _legacy_api()
    legacy._ensure_management_access()
    key = str(job_key or "").strip()
    if not key:
        frappe.throw(_("Job key is required."))
    return _get_job_state(key) or _build_job_state(key, "unknown")


@frappe.whitelist()
def get_management_pos_boot_safe(branch=None):
    """Return base POS boot even if optional unavailable-item enrichment fails."""
    legacy = _legacy_api()
    legacy._ensure_management_access()
    normalized_branch = str(branch or "").strip()
    payload = legacy.get_management_pos_boot(normalized_branch)
    if not isinstance(payload, dict):
        payload = {}

    result = dict(payload)
    try:
        reliability = _reliability_api()
        try:
            reliability._clear_expired_out_of_stock()
        except Exception:
            pass
        extra = reliability._management_unavailable_items(normalized_branch)
        result["items"] = reliability._merge_pos_items(
            payload.get("items") or [],
            extra,
        )
    except Exception:
        # Optional stock enrichment must never blank the whole product panel.
        try:
            frappe.log_error(
                frappe.get_traceback(),
                "POS Optional Unavailable Item Enrichment Error",
            )
        except Exception:
            pass
        result["items"] = list(payload.get("items") or [])
    return result
