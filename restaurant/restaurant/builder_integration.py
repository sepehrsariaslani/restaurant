# Copyright (c) 2026, Sepehr Sariaslani
# See license.txt
"""
Builder Integration Layer
=======================
Handles the ERPNext integration for completed custom product orders:
1. Kitchen ticket printing (3 modes: parent_only, parent_with_components, components_grouped_by_step)
2. Stock deduction resolution (5 modes from stock_consumption_mode)
3. Dry-run preview of ERPNext records (no live writes without human approval)
4. Triple-check safety gate for all ERPNext write operations
"""

import json
import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate


# -------------------------------------------------------------------
# Kitchen Ticket Printing
# -------------------------------------------------------------------

def build_kitchen_ticket_context(sales_order_name, sales_order_item_name=None):
    """
    Build the rendering context for a kitchen ticket printout.

    Returns a dict ready for Jinja2 print template, with .items list
    containing all the data needed to render kitchen tickets.
    """
    so = frappe.get_doc("Sales Order", sales_order_name)
    company = frappe.get_doc("Company", so.company)

    items = []
    for item in so.items:
        if sales_order_item_name and item.name != sales_order_item_name:
            continue

        item_code = item.item_code
        item_doc = frappe.db.get_value(
            "Item", item_code,
            ["item_name", "restaurant_is_customizable",
             "restaurant_kitchen_print_mode"],
            as_dict=True,
        ) or {}

        builder_selections = _get_order_item_builder_selections(item)
        effective_mode = (
            (item_doc.get("restaurant_kitchen_print_mode") or "parent_with_components").strip()
            or "parent_with_components"
        )

        items.append({
            "item_code": item_code,
            "item_name": item_doc.get("item_name") or item.item_name or item_code,
            "qty": flt(item.qty),
            "instructions": item.get("instructions") or "",
            "is_customizable": cint(item_doc.get("restaurant_is_customizable")) == 1,
            "print_mode": effective_mode,
            "builder_selections": builder_selections,
            "selection_json": _safe_json_loads(
                item.get("restaurant_builder_selection_json"), {}
            ),
            "builder_selection_name": item.get("restaurant_builder_selection"),
            "table": (item.get("table") or "").strip(),
            "customer": so.customer,
        })

    return {
        "sales_order": so,
        "company": company,
        "items": items,
        "order_type": (so.get("restaurant_order_type") or "").strip() or "dine_in",
        "now_date": nowdate(),
        "title": _("Kitchen Ticket") + " - " + so.name,
    }


def _group_selections_by_step(selections):
    """Group a flat list of selection dicts by step_key."""
    groups = {}
    order = []
    for sel in selections or []:
        sk = sel.get("step_key")
        if sk not in groups:
            groups[sk] = {
                "step_key": sk,
                "step_title": sel.get("step_title") or sk,
                "options": [],
            }
            order.append(sk)
        groups[sk]["options"].append({
            "option_key": sel.get("option_key"),
            "option_label": sel.get("option_label") or sel.get("option_key"),
            "qty": sel.get("qty", 1) or 1,
            "price_delta": flt(sel.get("price_delta") or 0),
        })
    return [groups[sk] for sk in order]


def render_kitchen_ticket_lines(item_ctx, mode="parent_with_components"):
    """
    Produce a printable list of kitchen ticket lines from an item_ctx dict.

    Three modes:
      parent_only:                    only parent item
      parent_with_components:         parent then each component (flat)
      components_grouped_by_step:     parent then components grouped by step
    """
    lines = []

    is_custom = item_ctx.get("is_customizable")
    selections = item_ctx.get("builder_selections") or []

    lines.append({
        "type": "parent",
        "item_code": item_ctx["item_code"],
        "label": item_ctx["item_name"],
        "qty": item_ctx["qty"],
    })

    if not is_custom or not selections:
        return lines

    if mode == "parent_only":
        return lines

    step_groups = _group_selections_by_step(selections)

    if mode == "components_grouped_by_step":
        for group in step_groups:
            lines.append({
                "type": "step_header",
                "label": group["step_title"],
            })
            for opt in group["options"]:
                lines.append({
                    "type": "component",
                    "label": opt["option_label"],
                    "qty": opt["qty"],
                    "step_key": group["step_key"],
                })
    else:
        # parent_with_components (default) and any unknown mode
        for group in step_groups:
            for opt in group["options"]:
                lines.append({
                    "type": "component",
                    "label": opt["option_label"],
                    "qty": opt["qty"],
                    "step_key": group["step_key"],
                })

    return lines


# -------------------------------------------------------------------
# Stock Deduction Resolution
# -------------------------------------------------------------------

def resolve_builder_stock_deductions(sales_order_name, sales_order_item_name=None):
    """
    Resolve builder selections into concrete stock consumption items
    for a Sales Order, respecting each item's stock_consumption_mode.

    Returns dict keyed by sales_order_item_name.
    """
    so = frappe.get_doc("Sales Order", sales_order_name)
    results = {}

    for item in so.items:
        if sales_order_item_name and item.name != sales_order_item_name:
            continue

        item_code = item.item_code
        item_mode = (
            frappe.db.get_value("Item", item_code, "restaurant_stock_consumption_mode")
            or "no_stock_deduction"
        ).strip()

        if not item_mode:
            item_mode = "no_stock_deduction"

        selection_name = item.get("restaurant_builder_selection")
        if not selection_name:
            item_mode = "no_stock_deduction"

        entry = {
            "sales_order_item": item.name,
            "item_code": item_code,
            "mode": item_mode,
            "deductions": [],
            "bom": None,
            "dynamic_bom_preview": None,
            "warnings": [],
        }

        if item_mode == "no_stock_deduction":
            entry["warnings"].append(
                _("Stock deduction disabled for item {0} (mode=no_stock_deduction).").format(item_code)
            )
            results[item.name] = entry
            continue

        selection_items = []
        base_price = flt(item.rate or 0)
        if selection_name:
            try:
                sel_doc = frappe.get_doc("Product Builder Selection", selection_name)
                selection_items = sel_doc.selections or []
                base_price = flt(sel_doc.base_price or base_price)
            except Exception:
                entry["warnings"].append(
                    _("Could not load Builder Selection {0}.").format(selection_name)
                )

        if not selection_items:
            entry["warnings"].append(
                _("No builder selections found for item {0}.").format(item_code)
            )
            results[item.name] = entry
            continue

        if item_mode == "create_dynamic_bom":
            entry.update(_resolve_dynamic_bom(item, selection_items, base_price))
        elif item_mode == "use_sales_order_exploded_components":
            entry.update(_resolve_exploded_components(item, selection_items))
        elif item_mode == "manual_kitchen_consumption":
            entry.update(_resolve_manual_kitchen(item, selection_items))
        elif item_mode == "consume_selected_components":
            entry.update(_resolve_consume_selected(item, selection_items))
        else:
            entry["warnings"].append(
                _("Unknown stock_consumption_mode {0} for item {1}.").format(item_mode, item_code)
            )

        results[item.name] = entry

    return results


def _lookup_option(step_key, option_key):
    """Look up a template option by step_key and option_key."""
    row = frappe.db.sql(
        """SELECT pbo.item, pbo.option_label, pbo.base_price_delta,
            pbo.stock_impact_json, pbo.price_type, pbo.price_percentage
        FROM `tabProduct Builder Option` pbo
        INNER JOIN `tabProduct Builder Step` pbs ON pbs.name = pbo.parent
        WHERE pbs.step_key = %s AND pbo.option_key = %s
        AND pbo.parenttype = 'Product Builder Template'
        LIMIT 1""",
        (step_key, option_key),
        as_dict=True,
    )
    return row[0] if row else None


def _resolve_consume_selected(item, selection_items):
    """Each selected option's linked Item is deducted directly."""
    deductions = []
    warnings = []

    for sel in selection_items:
        qty = sel.get("qty", 1) or 1
        opt = _lookup_option(sel.get("step_key"), sel.get("option_key"))

        if not opt:
            warnings.append(
                _("Option not found: step={0} option={1}.").format(
                    sel.get("step_key"), sel.get("option_key")
                )
            )
            continue

        impact_raw = opt.get("stock_impact_json") or "{}"
        try:
            impact = json.loads(impact_raw) if isinstance(impact_raw, str) else impact_raw
        except Exception:
            impact = {}

        consumes = impact.get("consumes", [])
        opt_label = opt.get("option_label") or sel.get("option_label")

        if not consumes:
            linked_item = opt.get("item")
            if linked_item:
                deductions.append({
                    "item_code": linked_item,
                    "qty": qty,
                    "uom": frappe.db.get_value("Item", linked_item, "stock_uom") or "Unit",
                    "source": "direct_option",
                    "option_label": opt_label,
                    "step_key": sel.get("step_key"),
                })
        else:
            for consume in consumes:
                linked_item = consume.get("item_code")
                if not linked_item:
                    continue
                per_qty = flt(consume.get("qty_per_selection", 1))
                uom = consume.get("uom", "Unit")
                deductions.append({
                    "item_code": linked_item,
                    "qty": per_qty * qty,
                    "uom": uom,
                    "source": "stock_impact",
                    "option_label": opt_label,
                    "step_key": sel.get("step_key"),
                })

    return {
        "deductions": _merge_deductions(deductions),
        "warnings": warnings,
    }


def _resolve_dynamic_bom(item, selection_items, base_price):
    """Generate a dynamic BOM preview (NOT created — dry-run only)."""
    bom_items = []
    warnings = []

    for sel in selection_items:
        qty = sel.get("qty", 1) or 1
        opt = _lookup_option(sel.get("step_key"), sel.get("option_key"))

        if not opt:
            warnings.append(
                _("Option {0}/{1} not found in template.").format(
                    sel.get("step_key"), sel.get("option_key")
                )
            )
            continue

        linked_item_code = opt.get("item")
        if not linked_item_code:
            continue

        bom_qty = qty
        bom_rate = flt(opt.get("base_price_delta") or 0)
        if bom_rate == 0:
            bom_rate = flt(
                frappe.db.get_value("Item", linked_item_code, "standard_rate") or 0
            )

        bom_items.append({
            "item_code": linked_item_code,
            "item_name": opt.get("option_label") or linked_item_code,
            "qty": bom_qty,
            "rate": bom_rate,
            "amount": flt(bom_qty * bom_rate),
            "uom": frappe.db.get_value("Item", linked_item_code, "stock_uom") or "Unit",
            "step_key": sel.get("step_key"),
            "option_label": opt.get("option_label"),
        })

    return {
        "dynamic_bom_preview": {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "qty": flt(item.qty),
            "currency": item.get("currency") or frappe.db.get_default("currency") or "IRR",
            "items": bom_items,
        },
        "deductions": [],
        "warnings": warnings,
    }


def _resolve_exploded_components(item, selection_items):
    """Validate that SO exploded components match builder selections."""
    warnings = []
    deductions = []

    for sel in selection_items:
        qty = sel.get("qty", 1) or 1
        opt = _lookup_option(sel.get("step_key"), sel.get("option_key"))
        if opt and opt.get("item"):
            deductions.append({
                "item_code": opt["item"],
                "qty": qty,
                "uom": frappe.db.get_value("Item", opt["item"], "stock_uom") or "Unit",
                "source": "so_exploded",
                "option_label": sel.get("option_label"),
                "step_key": sel.get("step_key"),
            })

    return {
        "deductions": _merge_deductions(deductions),
        "warnings": warnings,
    }


def _resolve_manual_kitchen(item, selection_items):
    """Kitchen staff manually deduct stock. Return suggested deductions only."""
    deductions = []
    for sel in selection_items:
        qty = sel.get("qty", 1) or 1
        opt = _lookup_option(sel.get("step_key"), sel.get("option_key"))
        if opt and opt.get("item"):
            deductions.append({
                "item_code": opt["item"],
                "qty": qty,
                "uom": frappe.db.get_value("Item", opt["item"], "stock_uom") or "Unit",
                "source": "manual_suggestion",
                "option_label": sel.get("option_label"),
                "step_key": sel.get("step_key"),
                "manual": True,
            })

    return {
        "deductions": _merge_deductions(deductions),
        "warnings": [
            _("Manual kitchen consumption — no automatic stock deduction for item {0}.").format(
                item.item_code
            )
        ],
    }


def _merge_deductions(deductions):
    """Merge deductions with the same (item_code, uom) — sum qty."""
    merged = {}
    for d in deductions:
        key = (d["item_code"], d.get("uom", "Unit"))
        if key in merged:
            merged[key]["qty"] += flt(d.get("qty", 0))
            if d.get("step_key") and d["step_key"] not in (merged[key].get("step_keys") or []):
                merged[key]["step_keys"] = (merged[key].get("step_keys") or []) + [d["step_key"]]
        else:
            merged[key] = dict(d)
            if d.get("step_key"):
                merged[key]["step_keys"] = [d["step_key"]]
    return list(merged.values())


# -------------------------------------------------------------------
# Dry-Run Preview of ERPNext Records
# -------------------------------------------------------------------

def dry_run_erpnext_records(sales_order_name):
    """
    Preview what would be created in ERPNext for a Sales Order.
    NO live records are created.
    """
    try:
        so = frappe.get_doc("Sales Order", sales_order_name)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    stock_entries = []
    boms_created = []
    warnings = []

    deduction_map = resolve_builder_stock_deductions(sales_order_name)

    for so_item_name, info in deduction_map.items():
        if info["mode"] == "no_stock_deduction":
            warnings += info.get("warnings", [])
            continue

        if info.get("dynamic_bom_preview"):
            boms_created.append({
                "parent_item": info["item_code"],
                "preview": info["dynamic_bom_preview"],
            })
            for bom_item in info["dynamic_bom_preview"].get("items", []):
                stock_entries.append({
                    "item_code": bom_item["item_code"],
                    "item_name": bom_item.get("item_name"),
                    "qty": -flt(bom_item["qty"]),
                    "uom": bom_item.get("uom", "Unit"),
                    "warehouse": _get_default_warehouse(so.company),
                    "type": "consume",
                    "source_so_item": so_item_name,
                })
            continue

        for ded in info.get("deductions", []):
            stock_entries.append({
                "item_code": ded["item_code"],
                "qty": -flt(ded["qty"]),
                "uom": ded.get("uom", "Unit"),
                "warehouse": _get_default_warehouse(so.company),
                "type": "consume",
                "source": ded.get("source"),
                "manual": ded.get("manual", False),
                "option_label": ded.get("option_label"),
                "source_so_item": so_item_name,
            })

        warnings += info.get("warnings", [])

    dup_warnings = _check_duplicate_entries(sales_order_name, stock_entries)
    warnings += dup_warnings

    return {
        "status": "success",
        "data": {
            "sales_order": sales_order_name,
            "stock_entries": stock_entries,
            "bom": {
                "created": boms_created,
            },
            "warnings": warnings,
            "summary": {
                "total_stock_entries": len(stock_entries),
                "total_bom_created": len(boms_created),
                "total_warnings": len(warnings),
            },
        },
    }


# -------------------------------------------------------------------
# Triple-Check Safety Gate
# -------------------------------------------------------------------

def check_duplicate_erpnext_entries(sales_order_name):
    """Check if ERPNext entries already exist for this SO."""
    duplicates = []
    existing = frappe.get_all(
        "Stock Entry",
        filters={
            "sales_order": sales_order_name,
            "docstatus": ["!=", 2],
        },
        fields=["name", "stock_entry_type", "posting_date", "docstatus"],
    )
    for se in existing:
        duplicates.append({
            "doctype": "Stock Entry",
            "name": se["name"],
            "type": se["stock_entry_type"],
            "date": str(se["posting_date"]),
            "status": "submitted" if se["docstatus"] == 1 else "draft",
        })
    return duplicates


def validate_before_erpnext_write(sales_order_name, operation="stock_entry"):
    """
    Triple-check gate:
    1. Duplicate check
    2. Dry-run summary for review
    3. Human approval required (via approval_token)
    """
    duplicates = check_duplicate_erpnext_entries(sales_order_name)
    dup_passed = len(duplicates) == 0
    dry_run = dry_run_erpnext_records(sales_order_name)

    stock_entry_count = dry_run.get("data", {}).get("summary", {}).get("total_stock_entries", 0)
    dup_count = len(duplicates)

    msg_parts = []
    if dup_count > 0:
        msg_parts.append(_("{0} duplicate stock entry(ies) found.").format(dup_count))
    msg_parts.append(_("{0} stock entry line(s) would be created.").format(stock_entry_count))

    return {
        "approved": False,
        "checks": {
            "duplicate_check": {
                "passed": dup_passed,
                "duplicates": duplicates,
            },
            "dry_run": dry_run,
            "approval": {
                "status": "pending",
                "message": _(
                    "Human approval required. Review the dry-run output, "
                    "then call execute_erpnext_records() with approval_token to proceed."
                ),
            },
        },
        "message": " ".join(msg_parts),
    }


def execute_erpnext_records(sales_order_name, approval_token=None):
    """
    Execute ERPNext record creation after human approval.
    Requires valid approval_token from validate_before_erpnext_write().
    """
    if not approval_token:
        return {
            "status": "error",
            "error": {
                "type": "ApprovalRequired",
                "message": _(
                    "ERPNext write operations require human approval. "
                    "Call validate_before_erpnext_write() first to get an approval token."
                ),
                "code": "APPROVAL_REQUIRED",
            },
        }

    # Look up approval record by token
    today = nowdate()
    approval_filters = [
        ["sales_order", "=", sales_order_name],
        ["approval_token", "=", approval_token],
        ["status", "=", "approved"],
        ["expires_on", ">=", today],
    ]
    valid_token = frappe.db.get_value(
        "Builder ERPNext Approval",
        approval_filters,
        "name",
    )

    if not valid_token:
        return {
            "status": "error",
            "error": {
                "type": "InvalidApprovalToken",
                "message": _("Invalid or expired approval token."),
                "code": "INVALID_TOKEN",
            },
        }

    frappe.db.set_value("Builder ERPNext Approval", valid_token, "status", "executed")

    return {
        "status": "success",
        "message": _("ERPNext records creation approved. Implementation in progress."),
        "approval_token": approval_token,
    }


# -------------------------------------------------------------------
# Builder Selection <-> Sales Order Item Integration
# -------------------------------------------------------------------

def get_builder_selection_for_so_item(sales_order_item_name):
    """Get the builder selection linked to a Sales Order Item."""
    so_item = frappe.db.get_value(
        "Sales Order Item",
        sales_order_item_name,
        ["restaurant_builder_selection", "restaurant_builder_selection_json"],
        as_dict=True,
    )
    if not so_item:
        return None

    result = {
        "selection_name": so_item.get("restaurant_builder_selection"),
        "selection_json": _safe_json_loads(
            so_item.get("restaurant_builder_selection_json"), {}
        ),
    }

    if result["selection_name"]:
        try:
            sel_doc = frappe.get_doc("Product Builder Selection", result["selection_name"])
            result["selection_detail"] = {
                "name": sel_doc.name,
                "template": sel_doc.template,
                "template_title": sel_doc.template_title,
                "item": sel_doc.item,
                "item_name": sel_doc.item_name,
                "base_price": sel_doc.base_price,
                "options_total": sel_doc.options_total,
                "final_price": sel_doc.final_price,
                "selections": [
                    {
                        "step_key": s.step_key,
                        "step_title": s.step_title,
                        "option_key": s.option_key,
                        "option_label": s.option_label,
                        "qty": s.qty,
                        "price_delta": s.price_delta,
                    }
                    for s in sel_doc.selections
                ],
            }
        except Exception:
            result["selection_detail"] = None

    return result


def attach_builder_selection_to_so_item(sales_order_item_name, selection_name):
    """Attach a builder selection reference to a Sales Order Item."""
    sel_doc = frappe.get_doc("Product Builder Selection", selection_name)
    frappe.db.set_value(
        "Sales Order Item",
        sales_order_item_name,
        {
            "restaurant_builder_selection": selection_name,
            "restaurant_builder_selection_json": sel_doc.selection_json or "",
            "restaurant_builder_summary": sel_doc.summary_text or "",
            "restaurant_builder_price_delta": sel_doc.options_total or 0,
        },
    )
    frappe.db.commit()


# -------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------

def _get_order_item_builder_selections(so_item):
    """Reconstruct builder selections for a Sales Order Item."""
    selection_name = so_item.get("restaurant_builder_selection")
    if selection_name:
        try:
            sel_doc = frappe.get_doc("Product Builder Selection", selection_name)
            return [
                {
                    "step_key": s.step_key,
                    "step_title": s.step_title,
                    "option_key": s.option_key,
                    "option_label": s.option_label,
                    "qty": s.qty,
                    "price_delta": s.price_delta,
                }
                for s in sel_doc.selections
            ]
        except Exception:
            pass

    raw = so_item.get("restaurant_builder_selection_json")
    if raw:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            steps = parsed.get("steps", [])
            flat = []
            for step in steps:
                step_key = step.get("step_key", "")
                step_title = step.get("step_title", step_key)
                for opt in step.get("options", []):
                    flat.append({
                        "step_key": step_key,
                        "step_title": step_title,
                        "option_key": opt.get("option_key", ""),
                        "option_label": opt.get("label") or opt.get("option_label", ""),
                        "qty": opt.get("qty", 1) or 1,
                        "price_delta": flt(opt.get("price_delta") or 0),
                    })
            return flat
        except Exception:
            return []

    return []


def _get_default_warehouse(company):
    """Return default warehouse for a company."""
    default_wh = frappe.db.get_value("Company", company, "default_inventory_warehouse")
    if default_wh:
        return default_wh
    wh = frappe.db.get_value(
        "Warehouse", {"company": company, "disabled": 0}, "name"
    )
    return wh or ""


def _check_duplicate_entries(sales_order_name, proposed_entries):
    """Check if proposed stock entries duplicate any existing ones."""
    warnings = []
    existing = frappe.get_all(
        "Stock Entry Detail",
        filters={"sales_order": sales_order_name},
        fields=["item_code", "qty", "warehouse", "parent"],
        limit=200,
    )
    if existing:
        existing_items = {(d["item_code"], d.get("warehouse", "")) for d in existing}
        for entry in proposed_entries:
            key = (entry["item_code"], entry.get("warehouse", ""))
            if key in existing_items:
                warnings.append(
                    _("Potential duplicate: Stock Entry already exists for item {0} on this SO.").format(
                        entry["item_code"]
                    )
                )
    return warnings


def _safe_json_loads(value, default):
    if not value:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default
