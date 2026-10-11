# Food Partner Approval Production and Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a Food Partner order is approved in POS Operations, automatically create its production and Delivery Note along with the existing Sales Invoice flow.

**Architecture:** Keep the current approval endpoint and invoice creation path. Add a persisted Food Partner setting and a toggle to the integration settings page. When enabled, approved snapp_food Sales Orders reuse Restaurant's existing deliver_invoice_only operation; return its Delivery Note and production outcome, and update the POS confirmation toast. Leave invoice behavior, other order sources, and rejection unchanged.

**Tech Stack:** Python, Frappe, Vue 3.

## Global Constraints

- Only approved orders whose source is snapp_food use the additional fulfillment flow, and only when its setting is enabled.
- Add a Food Partner setting for automatic production and Delivery Note creation; its initial value is off.
- No per-order action button is added.
- Use the existing production and delivery flow, preserve its duplicate protection, and leave the Sales Invoice open.
- Submitted delivery follows the existing flow's delivered order status.
- Partial production errors must be surfaced in the POS response and must not be reported as full success.
- Do not add or run automated tests for this request; inspect changes and run git diff --check only.

---

### Task 1: Run production and delivery during Food Partner approval

**Files:**
- Modify: `restaurant/api_order_review.py`

**Interfaces:**
- Consumes: existing `_ensure_food_partner_sales_invoice(order_name, order)` and `restaurant.api.deliver_invoice_only(order_name)`.
- Produces: approval results with `fulfillment_status`, `delivery_note`, and `production_errors` for snapp_food orders.

- [x] Add a helper that calls the existing delivery operation and returns the data needed by POS:

```python
def _ensure_food_partner_production_and_delivery(order_name):
	from restaurant.api import deliver_invoice_only

	result = deliver_invoice_only(order_name)
	auto_flow = result.get("auto_flow") or {}
	errors = auto_flow.get("errors") or []
	return {
		"fulfillment_status": "partial" if errors else "success",
		"delivery_note": result.get("delivery_note") or auto_flow.get("delivery_note") or "",
		"production_errors": errors,
	}
```

- [x] In the pending approval path, after the Sales Order is submitted and its Food Partner Sales Invoice is ensured, call the helper only when `restaurant_external_source` equals `snapp_food`; add a distinct stage label before the call so terminal failures remain identifiable. This call is now gated by the new setting.
- [x] In the already-approved idempotent path, ensure a missing invoice as today, then run the same helper for snapp_food orders so a retry can finish missing production or delivery without duplicating completed documents, when the setting is enabled.
- [x] Include the helper fields in both approval responses. Keep rejection and non-Food Partner response shapes unchanged.
- [x] Commit only this file with a Persian message that describes the automatic fulfillment behavior and its reason.

### Task 2: Show the fulfillment result in POS Operations

**Files:**
- Modify: `frontend/src/pages/restaurant/RestaurantPosPage.vue`

**Interfaces:**
- Consumes: `fulfillment_status`, `delivery_note`, and `production_errors` returned by the approval endpoint.
- Produces: a success toast naming the Sales Invoice and Delivery Note when available, or a warning toast when production reports partial errors.

- [x] Keep the current approval call and rejection behavior. When the result includes Food Partner fulfillment data, build the approval message from the Sales Invoice and Delivery Note identifiers; if `fulfillment_status` is `partial`, include the number of production errors and use the existing warning toast tone.
- [x] Preserve the current approval message for non-Food Partner orders and for responses that do not contain fulfillment data.
- [x] Commit only this file with a Persian message explaining that POS confirmation now reports the generated invoice and delivery.

### Task 3: Review the two repository changes

**Files:**
- Review: `restaurant/api_order_review.py`
- Review: `frontend/src/pages/restaurant/RestaurantPosPage.vue`

- [x] Run `git diff --check` in each repository.
- [x] Confirm the backend only starts fulfillment for snapp_food approval, the idempotent path retries missing fulfillment, and reject/non-Food Partner paths are unchanged.
- [x] Confirm the POS reports partial production errors as a warning and does not claim full success.
- [x] Confirm each code commit contains only its intended file and all unrelated working changes remain untouched.

### Task 4: Add the automatic production and delivery setting

**Files:**
- Modify: `restaurant/patches/v2_22/ensure_food_partner_approval_fulfillment_setting.py`
- Modify: `restaurant/patches.txt`
- Modify: `restaurant/snapp_sync.py`
- Modify: `restaurant/api.py`
- Modify: `restaurant/api_order_review.py`
- Modify: Accounts `frontend/src/pages/restaurant/RestaurantFoodPartnerPage.vue`

- [x] Persist the setting as an off-by-default Restaurant Web Settings field and expose it through status and save APIs.
- [x] Show the switch on the Food Partner connection settings page beside the existing automation switches.
- [x] Gate production and Delivery Note creation in both approval paths on the persisted setting; if the field is absent or unreadable, leave the invoice path working and treat fulfillment as off.
- [x] Review both worktrees, run `git diff --check`, and commit the backend and UI changes with Persian messages.
