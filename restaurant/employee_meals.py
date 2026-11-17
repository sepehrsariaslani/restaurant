"""Pure rules for consuming HRMS employee meal reservations from Restaurant POS."""
from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


class EmployeeMealValidationError(ValueError):
    """An employee meal payload does not match its reserved meal."""


def has_employee_meal_customization(value: Any) -> bool:
    """Ignore empty defaults added by the normal POS serializer."""
    if isinstance(value, str):
        try:
            value = json.loads(value) if value.strip() else {}
        except (TypeError, ValueError):
            return True
    if not isinstance(value, Mapping):
        return bool(value)
    for key in (
        "bom_name", "ingredient_adjustments", "selected_modifiers", "selected_alternatives",
        "removed_ingredients", "added_ingredients", "builder_selection", "builder_portion_rows",
        "builder_template", "builder_summary",
    ):
        current = value.get(key)
        if current not in (None, "", [], {}):
            return True
    fixed = value.get("variant_fixed_attributes")
    return bool(fixed)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def validate_employee_meal_order(
    *,
    employee: Mapping[str, Any],
    reservation: Mapping[str, Any],
    company: str,
    today: str,
    items: list[Mapping[str, Any]],
    requested_employee: str,
    client_order_key: str,
    price_overrides: bool = False,
    financial_modifiers: Any = None,
    totals: Any = None,
    linked_order_client_key: str | None = None,
    linked_order_name: str | None = None,
) -> dict[str, Any]:
    """Validate one exact reserved lunch before any Sales Order writes."""
    employee_name = _text(employee.get("name"))
    reservation_name = _text(reservation.get("name"))
    requested_employee = _text(requested_employee)
    client_order_key = _text(client_order_key)

    if not employee_name or employee.get("status") != "Active":
        raise EmployeeMealValidationError("Employee must be active.")
    if requested_employee != employee_name or not reservation_name:
        raise EmployeeMealValidationError("Employee does not match the reservation.")
    if _text(employee.get("company")) != _text(company) or _text(reservation.get("company")) != _text(company):
        raise EmployeeMealValidationError("Employee meal must belong to the selected company.")
    if _text(reservation.get("employee")) != employee_name:
        raise EmployeeMealValidationError("Employee does not match the reservation.")
    if _text(reservation.get("reservation_date")) != _text(today):
        raise EmployeeMealValidationError("Employee meal reservation must be for today.")
    if _text(reservation.get("meal_type")) != "Lunch":
        raise EmployeeMealValidationError("Only reserved lunch meals are supported.")
    if _text(reservation.get("reservation_status")) != "Reserved":
        raise EmployeeMealValidationError("Employee meal reservation is not available.")
    item_code = _text(reservation.get("meal_item"))
    if not item_code:
        raise EmployeeMealValidationError("Employee meal reservation has no item.")
    if price_overrides or financial_modifiers or totals:
        raise EmployeeMealValidationError("Employee meal orders must use the regular item price.")

    claimed_order = _text(reservation.get("restaurant_pos_sales_order"))
    if claimed_order:
        if (
            _text(linked_order_name) == claimed_order
            and client_order_key
            and _text(linked_order_client_key) == client_order_key
        ):
            return {
                "employee": employee_name,
                "reservation": reservation_name,
                "item_code": item_code,
                "idempotent_replay": True,
                "order_id": claimed_order,
            }
        raise EmployeeMealValidationError("Employee meal reservation is already linked to another order.")

    if not isinstance(items, list) or len(items) != 1 or not isinstance(items[0], Mapping):
        raise EmployeeMealValidationError("An employee meal order must contain exactly the reserved item.")
    line = items[0]
    if any(line.get(key) not in (None, "", {}, []) for key in ("custom_price_overrides", "offline_unit_price", "external_unit_price", "unit_price", "rate")):
        raise EmployeeMealValidationError("Employee meal orders must use the regular item price.")
    quantity = _decimal(line.get("qty"))
    if _text(line.get("item_code")) != item_code or quantity != Decimal("1"):
        raise EmployeeMealValidationError("Employee meal order must contain the reserved item with quantity 1.")

    return {
        "employee": employee_name,
        "reservation": reservation_name,
        "item_code": item_code,
        "idempotent_replay": False,
        "order_id": None,
    }


def can_release_reservation(
    reservation_order: str | None,
    order_name: str,
    *,
    delivered: bool,
    reservation_status: Any = None,
) -> bool:
    """Only release an association owned by this exact order before delivery."""
    reservation_delivered = _text(reservation_status).lower() in {"delivered", "served"}
    return bool(
        _text(reservation_order)
        and _text(reservation_order) == _text(order_name)
        and not delivered
        and not reservation_delivered
    )


def is_employee_meal_order_delivered(status: Any, per_delivered: Any = 0) -> bool:
    if _text(status).lower() in {"delivered", "served"}:
        return True
    quantity = _decimal(per_delivered)
    return bool(quantity is not None and quantity >= Decimal("99.99"))


def has_employee_meal_payload(payload: Mapping[str, Any] | None) -> bool:
    data = payload if isinstance(payload, Mapping) else {}
    return any(_text(data.get(key)) for key in ("employee", "reservation"))


def employee_meal_checkout_route(payload: Mapping[str, Any] | None) -> str:
    """Select reliable reservation validation for any employee-meal marker."""
    return "reliable" if has_employee_meal_payload(payload) else "offline"


def employee_meal_avoids_stock_reservation(payload: Mapping[str, Any] | None) -> bool:
    """Staff meal Sales Orders must not create ERPNext stock reservations."""
    return has_employee_meal_payload(payload)


def employee_meal_include_service_items(payload: Mapping[str, Any] | None) -> int:
    """Keep service fees off employee entitlement orders only."""
    return 0 if has_employee_meal_payload(payload) else 1


def employee_meal_creation_context():
    """Mark the one idempotent server path allowed to pass meal fields inward."""
    from contextlib import contextmanager
    import frappe

    @contextmanager
    def context():
        attribute = "_restaurant_employee_meal_idempotent_create"
        previous = getattr(frappe.local, attribute, False)
        setattr(frappe.local, attribute, True)
        try:
            yield
        finally:
            if previous:
                setattr(frappe.local, attribute, previous)
            else:
                try:
                    delattr(frappe.local, attribute)
                except AttributeError:
                    pass

    return context()


def ensure_employee_meal_entrypoint_allowed(payload: Mapping[str, Any] | None) -> None:
    """Reject non-idempotent routes that would otherwise ignore meal metadata."""
    if not has_employee_meal_payload(payload):
        return
    import frappe

    if not getattr(frappe.local, "_restaurant_employee_meal_idempotent_create", False):
        frappe.throw(
            "Employee meal orders must use the idempotent management POS endpoint.",
            frappe.PermissionError,
        )


def _frappe_module():
    import frappe

    return frappe


def _meal_fields_ready(frappe) -> bool:
    return bool(
        frappe.db.exists("DocType", "Meal Reservation")
        and frappe.db.has_column("Meal Reservation", "restaurant_pos_sales_order")
        and frappe.db.has_column("Sales Order", "restaurant_employee_meal_employee")
        and frappe.db.has_column("Sales Order", "restaurant_employee_meal_reservation")
        and frappe.db.has_column("Sales Order Item", "restaurant_employee_meal_reservation")
    )


def _active_pos_company(legacy, payload: Mapping[str, Any]) -> str:
    frappe = _frappe_module()
    profile = (legacy._management_pos_profile_summary() or {})
    company = _text(profile.get("company"))
    if not company or not frappe.db.exists("Company", company):
        frappe.throw("An active POS Profile with a valid company is required for employee meals.", frappe.ValidationError)
    profile_name = _text(profile.get("name"))
    if profile_name and frappe.db.has_column("POS Profile", "disabled") and int(
        frappe.db.get_value("POS Profile", profile_name, "disabled") or 0
    ):
        frappe.throw("The active POS Profile is disabled.", frappe.PermissionError)
    order_context = payload.get("order_context") or {}
    if isinstance(order_context, str):
        order_context = frappe.parse_json(order_context) or {}
    if not isinstance(order_context, Mapping):
        frappe.throw("POS order context is invalid.", frappe.ValidationError)
    for key in ("company", "branch"):
        requested_company = _text(order_context.get(key))
        if requested_company and requested_company != company:
            frappe.throw("Employee meal company must match the active POS Profile.", frappe.PermissionError)
    return company


def lock_and_validate_employee_meal_order(payload: Mapping[str, Any], *, client_order_key: str, legacy) -> dict[str, Any] | None:
    """Lock and validate the HRMS reservation before creating its POS order.

    The caller must keep this transaction open through Sales Order creation and
    call :func:`link_employee_meal_order` before committing it.
    """
    if not has_employee_meal_payload(payload):
        return None

    frappe = _frappe_module()
    employee_id = _text(payload.get("employee"))
    reservation_name = _text(payload.get("reservation"))
    if not employee_id or not reservation_name:
        frappe.throw("Both employee and reservation are required for an employee meal.", frappe.ValidationError)
    if not client_order_key:
        frappe.throw("Employee meal orders require a client order key.", frappe.ValidationError)
    if not _meal_fields_ready(frappe):
        frappe.throw("Employee meal POS fields are not installed; apply the Restaurant schema patch first.", frappe.ValidationError)

    company = _active_pos_company(legacy, payload)
    frappe.db.sql("select name from `tabMeal Reservation` where name=%s for update", reservation_name)
    reservation = frappe.db.get_value(
        "Meal Reservation",
        reservation_name,
        ["name", "meal_plan", "company", "employee", "reservation_date", "meal_type", "meal_item", "reservation_status", "restaurant_pos_sales_order"],
        as_dict=True,
    )
    employee = frappe.db.get_value(
        "Employee", employee_id, ["name", "company", "status"], as_dict=True
    )
    if not reservation or not employee:
        frappe.throw("Employee or meal reservation was not found.", frappe.DoesNotExistError)

    plan = frappe.db.get_value(
        "Meal Weekly Plan", reservation.get("meal_plan"), ["company", "status"], as_dict=True
    )
    if not plan or plan.get("status") != "Published" or _text(plan.get("company")) != company:
        frappe.throw("Employee meal reservation must belong to a published plan for the active POS company.", frappe.ValidationError)

    linked_order = _text(reservation.get("restaurant_pos_sales_order"))
    linked_order_key = ""
    if linked_order:
        linked_order_key = _text(
            frappe.db.get_value("Sales Order", linked_order, "restaurant_pos_client_order_key")
        )

    rows = payload.get("items") or []
    if not isinstance(rows, list):
        frappe.throw("POS items must be a list.", frappe.ValidationError)
    resolved_rows = []
    for row in rows:
        if not isinstance(row, Mapping):
            resolved_rows.append(row)
            continue
        customization = legacy._extract_customization(row.get("customization") or row.get("config"))
        if has_employee_meal_customization(customization):
            frappe.throw("Employee meal orders must contain the exact reserved item without customization.", frappe.ValidationError)
        item_doc = legacy._get_item_doc_by_payload(row)
        resolved_rows.append({**dict(row), "item_code": item_doc.item_code or item_doc.name})

    try:
        validated = validate_employee_meal_order(
            employee=employee,
            reservation=reservation,
            company=company,
            today=frappe.utils.nowdate(),
            items=resolved_rows,
            requested_employee=employee_id,
            client_order_key=client_order_key,
            price_overrides=any(bool(row.get("custom_price_overrides")) for row in resolved_rows if isinstance(row, Mapping)),
            financial_modifiers=payload.get("financial_modifiers"),
            totals=payload.get("totals"),
            linked_order_client_key=linked_order_key,
            linked_order_name=linked_order,
        )
    except EmployeeMealValidationError as exc:
        frappe.throw(str(exc), frappe.ValidationError)

    order_context = payload.get("order_context") or {}
    if isinstance(order_context, str):
        order_context = frappe.parse_json(order_context) or {}
    order_context = dict(order_context)
    order_context["company"] = company
    payload["order_context"] = order_context
    return {**validated, "company": company}


def link_employee_meal_order(claim: Mapping[str, Any] | None, order_name: str) -> None:
    """Persist both order-to-reservation links in the caller's open transaction."""
    if not claim or claim.get("idempotent_replay"):
        return
    frappe = _frappe_module()
    order_name = _text(order_name)
    reservation_name = _text(claim.get("reservation"))
    employee = _text(claim.get("employee"))
    item_code = _text(claim.get("item_code"))
    if not order_name or not reservation_name or not item_code:
        frappe.throw("Employee meal order link is incomplete.", frappe.ValidationError)

    rows = frappe.get_all(
        "Sales Order Item",
        filters={"parent": order_name, "item_code": item_code},
        fields=["name", "qty"],
        limit_page_length=2,
        ignore_permissions=True,
    )
    if len(rows) != 1 or _decimal(rows[0].get("qty")) != Decimal("1"):
        frappe.throw("The created POS order does not contain exactly one reserved meal item.", frappe.ValidationError)

    frappe.db.set_value(
        "Sales Order",
        order_name,
        {
            "restaurant_employee_meal_employee": employee,
            "restaurant_employee_meal_reservation": reservation_name,
        },
        update_modified=False,
    )
    frappe.db.set_value(
        "Sales Order Item",
        rows[0]["name"],
        "restaurant_employee_meal_reservation",
        reservation_name,
        update_modified=False,
    )
    frappe.db.set_value(
        "Meal Reservation",
        reservation_name,
        "restaurant_pos_sales_order",
        order_name,
        update_modified=False,
    )


def release_employee_meal_order(order_doc) -> bool:
    """Clear only this cancelled order's undelivered reservation claim."""
    frappe = _frappe_module()
    if not frappe.db.has_column("Sales Order", "restaurant_employee_meal_reservation"):
        return False
    reservation_name = _text(order_doc.get("restaurant_employee_meal_reservation"))
    if not reservation_name or not frappe.db.has_column("Meal Reservation", "restaurant_pos_sales_order"):
        return False
    frappe.db.sql("select name from `tabMeal Reservation` where name=%s for update", reservation_name)
    linked_order = frappe.db.get_value(
        "Meal Reservation", reservation_name, "restaurant_pos_sales_order"
    )
    reservation_status = frappe.db.get_value(
        "Meal Reservation", reservation_name, "reservation_status"
    )
    delivered = is_employee_meal_order_delivered(
        order_doc.get("restaurant_status"), order_doc.get("per_delivered")
    )
    if not can_release_reservation(
        linked_order,
        order_doc.name,
        delivered=delivered,
        reservation_status=reservation_status,
    ):
        return False
    frappe.db.set_value(
        "Meal Reservation", reservation_name, "restaurant_pos_sales_order", None, update_modified=False
    )
    return True


def list_today_employee_meal_reservations(*, legacy, limit: Any = 100) -> dict[str, Any]:
    """Read a bounded list of unclaimed, active-company reservations for POS."""
    frappe = _frappe_module()
    legacy._ensure_management_access()
    if not frappe.db.exists("DocType", "Meal Reservation") or not _meal_fields_ready(frappe):
        frappe.throw("HRMS employee meal POS fields are not installed.", frappe.ValidationError)
    roles = set(frappe.get_roles(frappe.session.user))
    allowed_roles = {"System Manager", "Restaurant Manager", "Desk User", "HR Manager", "HR User", "Meal Coordinator", "Chef"}
    if not roles.intersection(allowed_roles):
        frappe.throw("You are not allowed to read employee meal reservations in POS.", frappe.PermissionError)
    company = _active_pos_company(legacy, {})
    from hrms.hr.doctype.meal_weekly_plan.meal_weekly_plan import is_company_meal_enabled

    if not is_company_meal_enabled(company):
        return {"company": company, "meal_date": frappe.utils.nowdate(), "reservations": []}
    try:
        page_size = max(1, min(int(limit or 100), 100))
    except (TypeError, ValueError):
        page_size = 100
    from hrms.api.meal import get_today_pos_meal_reservations

    return get_today_pos_meal_reservations(company=company, limit=page_size)
