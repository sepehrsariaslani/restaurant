# POS Financial And Customization Refinement

## Goal

Refine the management POS so the cashier can access POS actions directly from the invoice tab rail, use tax with the same amount/percent model as discount and service, get a larger and more usable compact product view, and manage product customizations with the same capabilities exposed to customer-facing menu users.

## Approved Direction

- Move `عملیات POS` and `میانبرها` out of the floating stack and into the `ticket-tabs-bar` at the top-left of the POS shell.
- Add a `مبلغ / درصد` switch for tax, matching discount and service behavior.
- Increase the size and usability of compact product cards.
- Expose BOM/customization actions in compact view too.
- Convert all visible numeric output in the POS workspace to Persian digits.
- Fix remaining dark mode gaps, especially interactive surfaces such as dropdowns, compact cards, and financial controls.
- Reuse the same customization capabilities available in the customer menu flow, including related add-ons and substitutions such as syrups when configured for an item.

## Current State

- `ManagementPosPage.vue` still renders `عملیات POS` and `میانبرها` as floating buttons near the lower-left corner.
- `PosCartPanel.vue` supports amount/percent for discount and service, but tax is currently a direct amount with only a tax-exempt checkbox.
- `PosProductPanel.vue` compact mode is text-only, visually dense, and does not expose a BOM/customization action.
- Some numeric displays still render with Latin digits because they use raw string/number output instead of Persian formatting helpers.
- Dark mode variables were improved at the page level, but some nested controls still render light-biased colors.
- POS customization currently opens a POS-specific sheet, but the requested behavior is parity with the customer menu customization flow rather than a reduced editor.

## Recommended Approach

Reuse the existing customer-menu customization model and adapt POS to feed and persist that structure.

Why:

- avoids separate customization rules for cashier vs customer
- reduces future drift in modifier/add-on behavior
- keeps BOM, substitutions, ingredient adjustments, and modifier groups aligned with the public ordering experience

## Layout Changes

### Ticket Rail Actions

`ticket-tabs-bar` should become the single top utility rail for invoice switching plus POS-level actions.

- Keep invoice tabs and `+ فاکتور جدید` in the rail.
- Add a left-side action cluster in the same band for:
  - `عملیات POS`
  - `میانبرها`
- Remove the floating desktop action stack after this move.
- Keep mobile behavior flexible; the floating pattern can remain only where the top rail does not have enough room.

### Compact Product View

Compact mode should remain dense, but not tiny.

- Increase card height and padding.
- Increase product title and price size.
- Keep quantity badge visible and readable.
- Add a dedicated BOM/customization trigger on cards that support customization.
- Preserve quick-add behavior on the main card surface.

## Financial Model

### Tax

Tax should match discount/service interaction semantics.

- Add `taxType` with values:
  - `fixed`
  - `percent`
- Keep `taxExempt` as an override.
- Replace the single tax amount field with:
  - amount/percent toggle
  - numeric value field
- When `taxExempt` is enabled:
  - tax value input is disabled
  - computed tax amount is forced to zero

### Totals Computation

Totals should compute tax exactly like service/discount style computations.

- `fixed`: use value directly
- `percent`: compute from the taxable subtotal used by current POS totals logic
- Persist `taxType` and `taxValue` through:
  - local state serialization
  - open-invoice/session restoration
  - order submission payloads

## Customization Parity

### Expected Behavior

When the cashier opens BOM/customization for a supported product, the POS must allow the same category of actions that customers can do from the public menu flow:

- ingredient adjustments
- related add-ons
- modifier groups
- substitutions/replacements
- variant-like choices where configured

This includes flows such as adding syrups to drinks when those options are configured on the underlying item.

### Integration Direction

- Audit the customer menu customization entry flow and identify the reusable state shape and action handlers.
- Reuse existing customization-fetching and rendering logic where feasible instead of cloning behavior into a new POS-only ruleset.
- Ensure customized POS cart lines preserve:
  - ingredient adjustments
  - selected modifiers
  - selected alternatives
  - note/custom labels already shown in cart summaries

## Persian Number Formatting

All cashier-visible numbers inside POS should use Persian digits, including:

- category/subcategory item counts
- line item quantities
- compact card badges
- table/order counts
- any raw counters or fixed numeric labels rendered outside `formatMoney`

Formatting should be consistent in both light and dark mode and should not break numeric parsing for inputs.

## Dark Mode Fixes

Audit and correct remaining light-biased elements:

- searchable dropdown surfaces and list options
- financial rows and toggles
- compact product cards
- ticket rail action buttons
- modal/sheet surfaces used by customization

The target is token-driven rendering from the management theme rather than one-off hard-coded colors.

## Files Expected To Change

- `frontend/src/pages/management/ManagementPosPage.vue`
- `frontend/src/components/management/pos/PosCartPanel.vue`
- `frontend/src/components/management/pos/PosProductPanel.vue`
- any shared customization component/composable already used by the customer flow
- formatting helpers if raw Persian-number support needs a shared utility

## Testing Strategy

### Behavior

- tax fixed mode computes correctly
- tax percent mode computes correctly
- tax-exempt overrides both
- POS actions and keyboard help open correctly from the ticket rail
- compact cards can still quick-add
- compact cards can open customization where applicable
- customized items retain their summary and editable state in cart

### UI

- desktop no longer shows floating POS action buttons
- compact cards are visibly larger and still fit the layout without overlap
- Persian digits appear in counts/quantities across the page
- dark mode surfaces are visually coherent for dropdowns, cards, and editors

## Scope Boundaries

Included:

- top rail action relocation
- tax toggle model
- compact card enlargement and BOM entry
- Persian digit cleanup in POS
- dark mode cleanup for touched POS surfaces
- customer-flow-equivalent customization behavior inside POS

Not included:

- unrelated POS workflow redesign
- public menu visual redesign
- backend schema changes unless strictly required by existing customization payload expectations
