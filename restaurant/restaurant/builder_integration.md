# Builder Integration Layer — ERPNext Integration for Custom Product Orders

## Overview

This document describes the integration layer that connects the Product Builder
(customer-facing customization flow) with ERPNext records (Sales Order,
Stock Entries, BOMs).

## Architecture

```
Customer Builder (Vue 3 frontend)
    |
    v
save_builder_selection()  →  Product Builder Selection (DocType)
    |
    v
Sales Order (with builder_selection link on SO Item)
    |
    v
builder_integration.py  →  Kitchen tickets + Stock deduction + Dry-run
    |
    v
ERPNext records (Stock Entry, BOM) — ONLY after human approval
```

## Files

| File | Purpose |
|------|---------|
| `restaurant/restaurant/builder_integration.py` | Core integration logic |
| `restaurant/restaurant/api.py` | API endpoints (appended at end) |
| `restaurant/restaurant/fixtures/product_builder_custom_fields.json` | Updated field options |

## 1. Kitchen Ticket Printing

### Three Print Modes

The `restaurant_kitchen_print_mode` field on Item controls how kitchen tickets
display builder selections:

| Mode | Behavior |
|------|----------|
| `parent_only` | Only the parent product is shown. Components are omitted. |
| `parent_with_components` | Parent product listed first, then each component option (flat list). |
| `components_grouped_by_step` | Parent product listed first, then components grouped under step headings. |

### API Endpoints

- `builder_kitchen_ticket(sales_order_name)` — Full context for print template
- `builder_render_kitchen_lines(sales_order_name)` — Pre-rendered lines ready for printing

### Usage

```python
# Get kitchen ticket context
context = build_kitchen_ticket_context("SO-2026-00001")

# Render lines for a specific item
for item_ctx in context["items"]:
    lines = render_kitchen_ticket_lines(item_ctx, item_ctx["print_mode"])
    # lines = [{"type": "parent", ...}, {"type": "component", ...}, ...]
```

## 2. Stock Deduction Resolution

### Five Consumption Modes

The `restaurant_stock_consumption_mode` field on Item controls how builder
selections translate to stock consumption:

| Mode | Behavior |
|------|----------|
| `no_stock_deduction` | No stock is consumed. For fully-assembled items. |
| `consume_selected_components` | Each selected option's linked Item is deducted directly. Uses `stock_impact_json` if available, otherwise falls back to the option's linked Item. |
| `create_dynamic_bom` | Generates a BOM preview (dry-run only — does NOT create the BOM). Components become Stock Entry lines. |
| `use_sales_order_exploded_components` | Validates that SO child line items match builder selections. |
| `manual_kitchen_consumption` | Returns suggested deductions for kitchen staff to manually confirm. No automatic stock entries. |

### API Endpoint

- `builder_resolve_stock(sales_order_name, sales_order_item_name=None)`

### Response Shape

```json
{
  "SOV-00001": {
    "sales_order_item": "SOV-00001",
    "item_code": "BUILD-PZA-001",
    "mode": "consume_selected_components",
    "deductions": [
      {
        "item_code": "CHEESE-MOZZ",
        "qty": 1.0,
        "uom": "Gram",
        "source": "stock_impact",
        "option_label": "Mozzarella",
        "step_key": "toppings"
      }
    ],
    "warnings": []
  }
}
```

## 3. Dry-Run Preview

### API Endpoint

- `builder_dry_run(sales_order_name)`

### What It Returns

A complete preview of what would be created in ERPNext:
- Stock Entry lines (item, qty, warehouse)
- BOMs that would be created
- Warnings (duplicates, missing data)

**NO live records are created.**

## 4. Triple-Check Safety Gate

All ERPNext write operations go through a mandatory triple-check:

### Step 1: Duplicate Check
```
builder_validate_before_write(sales_order_name)
```
Checks for existing Stock Entries referencing this Sales Order.

### Step 2: Dry-Run Summary
Returns a complete preview of what would be created.

### Step 3: Human Approval
```
builder_execute_records(sales_order_name, approval_token=...)
```
Requires a valid approval token. Without it, the function refuses to execute.

## 5. Sales Order Item Integration

Builder selections are attached to Sales Order Items via custom fields:

| Field | Type | Purpose |
|-------|------|---------|
| `restaurant_builder_selection` | Link | Reference to Product Builder Selection |
| `restaurant_builder_selection_json` | Long Text | Full JSON backup |
| `restaurant_builder_summary` | Long Text | Human-readable summary |
| `restaurant_builder_price_delta` | Currency | Total options price delta |

### API Endpoints

- `builder_attach_selection(sales_order_item_name, selection_name)` — Link selection to SO Item
- `builder_get_selection_for_item(sales_order_item_name)` — Read selection from SO Item

## 6. Data Flow

### Customer Places Order

1. Customer completes builder → `save_builder_selection()` creates Product Builder Selection
2. Cart item includes `builder_selection_id` in customization payload
3. At checkout, `builder_attach_selection_to_so_item()` links selection to SO Item

### Kitchen Prints Ticket

4. Kitchen calls `builder_render_kitchen_lines(SO-name)` → gets structured lines
5. Print template renders lines based on each item's `kitchen_print_mode`

### Stock Deduction

6. Manager calls `builder_dry_run(SO-name)` → reviews what would be created
7. Manager calls `builder_validate_before_write(SO-name)` → gets approval token
8. After review, calls `builder_execute_records(SO-name, token)` → creates records

## 7. Error Handling

All API endpoints return consistent error shapes:
```json
{"status": "error", "error": {"type": "...", "message": "...", "code": "..."}}
```

Common error codes:
- `MISSING_PARAM` — required parameter missing
- `TEMPLATE_NOT_FOUND` — no active builder template
- `APPROVAL_REQUIRED` — missing approval token
- `INVALID_TOKEN` — expired or invalid approval token
- `SERVER_ERROR` — unexpected error (logged)
