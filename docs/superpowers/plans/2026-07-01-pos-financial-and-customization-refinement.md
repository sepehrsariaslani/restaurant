# POS Financial And Customization Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move POS utility actions into the ticket rail, add amount/percent tax controls, enlarge compact product cards with BOM entry, normalize Persian digits across POS, close dark-mode gaps, and reuse customer-grade customization behavior inside POS.

**Architecture:** Keep the existing POS page as the orchestration layer, extend the pricing engine to support tax type/value semantics, and reuse shared customization components (`MenuQuickAddSheet`, `IngredientQuantityEditor`, `ModifierRecipeImpactSelector`, `itemConfig`) instead of maintaining a reduced POS-only customization editor. The product panel remains the main catalog surface, while the cart panel owns financial input controls and the POS page owns state persistence, totals, and cart mutation.

**Tech Stack:** Vue 3 Composition API, Vite, existing restaurant frontend shared components/composables, local POS pricing engine in `src/utils/posPricingEngine.js`

## Global Constraints

- Move `عملیات POS` and `میانبرها` into `ticket-tabs-bar` and remove floating desktop action buttons.
- Tax must support the same `fixed` / `percent` toggle model as discount and service.
- Compact cards must be larger, keep quick-add behavior, and expose BOM/customization when available.
- All visible POS numeric output should render with Persian digits.
- Dark mode fixes must use existing management theme tokens rather than ad hoc new colors.
- Product customization in POS should match the capability level of the customer menu flow, including modifiers, add-ons, substitutions, and related options such as syrups when configured.

---

### Task 1: Extend Pricing And POS Financial State For Tax Type

**Files:**
- Modify: `frontend/src/utils/posPricingEngine.js`
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`
- Modify: `frontend/src/components/management/pos/PosCartPanel.vue`

**Interfaces:**
- Consumes: `calculatePosTotals({ cartLines, discountType, discountValue, serviceType, serviceValue, taxAmount, tipAmount, useWallet, walletBalance })`
- Produces: `calculatePosTotals({ cartLines, discountType, discountValue, serviceType, serviceValue, taxType, taxValue, tipAmount, useWallet, walletBalance })`

- [ ] **Step 1: Write the failing test**

Add a focused unit test file for `calculatePosTotals` covering:

```js
import { describe, expect, it } from 'vitest'
import { calculatePosTotals } from '@/utils/posPricingEngine'

describe('calculatePosTotals tax modes', () => {
  it('computes percent tax from the discounted subtotal', () => {
    const result = calculatePosTotals({
      cartLines: [{ unit_price: 100000, qty: 2 }],
      discountType: 'percent',
      discountValue: 10,
      serviceType: 'fixed',
      serviceValue: 0,
      taxType: 'percent',
      taxValue: 9,
    })
    expect(result.discountAmount).toBe(20000)
    expect(result.taxAmount).toBe(16200)
    expect(result.payableAmount).toBe(196200)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/utils/posPricingEngine.test.js`

Expected: FAIL because `taxType` / `taxValue` are ignored by current implementation.

- [ ] **Step 3: Write minimal implementation**

Update `calculatePosTotals` so:

```js
const fixedTax = taxType === 'fixed' ? cleanTaxValue : 0
const percentTax = taxType === 'percent' ? (taxableBase * cleanTaxValue) / 100 : 0
const tax = Math.max(fixedTax + percentTax, 0)
```

Also update POS financial state defaults and persistence keys:

```js
taxType: 'fixed',
taxValue: 0,
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/utils/posPricingEngine.test.js`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/posPricingEngine.js frontend/src/pages/management/ManagementPosPage.vue frontend/src/components/management/pos/PosCartPanel.vue frontend/src/utils/posPricingEngine.test.js
git commit -m "feat: support percent tax in POS totals"
```

### Task 2: Move POS Utility Actions Into The Ticket Rail

**Files:**
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`

**Interfaces:**
- Consumes: `openOperationsOverlay()`, `showKeyboardMap`
- Produces: top-rail utility action cluster rendered inside `ticket-tabs-bar`

- [ ] **Step 1: Write the failing test**

Add a component-level test for the ticket rail asserting:

```js
expect(screen.getByRole('button', { name: /عملیات pos/i })).toBeInTheDocument()
expect(screen.getByRole('button', { name: /میانبرها/i })).toBeInTheDocument()
expect(screen.queryByTestId('pos-floating-actions')).not.toBeInTheDocument()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/management/ManagementPosPage.test.js`

Expected: FAIL because the buttons are still rendered in the floating stack.

- [ ] **Step 3: Write minimal implementation**

Move the trigger buttons into the `ticket-tabs-bar` template, add a `ticket-rail-actions` wrapper, and remove the desktop floating action stack.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/management/ManagementPosPage.test.js`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/management/ManagementPosPage.vue frontend/src/pages/management/ManagementPosPage.test.js
git commit -m "feat: move POS actions into ticket rail"
```

### Task 3: Upgrade Cart Financial Controls And Persian Number Output

**Files:**
- Modify: `frontend/src/components/management/pos/PosCartPanel.vue`
- Modify: `frontend/src/components/AmountPercentToggle.vue`
- Modify: `frontend/src/utils/format.js`
- Modify: `frontend/src/components/management/pos/PosProductPanel.vue`
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`

**Interfaces:**
- Consumes: `patchFinancial(partial)`, `formatMoney()`
- Produces: `toPersianNumber(value, options?)` helper and POS-wide Persian numeric rendering

- [ ] **Step 1: Write the failing test**

Cover:

```js
expect(renderedTaxToggle).toBeVisible()
expect(screen.getByText('۵')).toBeInTheDocument()
expect(screen.getByText(/۲۵ آیتم/)).toBeInTheDocument()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/management/pos/PosCartPanel.test.js src/components/management/pos/PosProductPanel.test.js`

Expected: FAIL because tax has no toggle and some raw counts/qty values still render in Latin digits.

- [ ] **Step 3: Write minimal implementation**

Implement:

```js
export function toPersianNumber(value, options = {}) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric)) return '۰'
  return numeric.toLocaleString('fa-IR', options)
}
```

Then wire it into:
- quantity text in `PosCartPanel`
- compact-card badge text
- category/subcategory counts
- ticket/order/table counters still rendered raw in POS
- tax controls in cart panel with `AmountPercentToggle`

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/management/pos/PosCartPanel.test.js src/components/management/pos/PosProductPanel.test.js`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/management/pos/PosCartPanel.vue frontend/src/components/management/pos/PosProductPanel.vue frontend/src/components/AmountPercentToggle.vue frontend/src/utils/format.js
git commit -m "feat: refine POS financial controls and Persian numbers"
```

### Task 4: Enlarge Compact Cards And Add BOM Entry

**Files:**
- Modify: `frontend/src/components/management/pos/PosProductPanel.vue`

**Interfaces:**
- Consumes: `increment-product`, `open-bom`, `quantityMap`
- Produces: larger compact cards with separate quick-add and customization affordances

- [ ] **Step 1: Write the failing test**

Add assertions that compact cards render:

```js
expect(screen.getByRole('button', { name: /سفارشی سازی/i })).toBeInTheDocument()
expect(screen.getByRole('button', { name: /افزودن سریع/i })).toBeInTheDocument()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/management/pos/PosProductPanel.test.js`

Expected: FAIL because compact cards are text-only and have no BOM trigger.

- [ ] **Step 3: Write minimal implementation**

Refactor compact-card markup into:
- main info block
- quantity badge
- action row with:
  - quick-add button
  - BOM/customization button when `has_customization` or modifiers exist

Increase compact card padding, min-height, title size, and numeric rhythm.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/management/pos/PosProductPanel.test.js`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/management/pos/PosProductPanel.vue frontend/src/components/management/pos/PosProductPanel.test.js
git commit -m "feat: enlarge compact POS cards with BOM actions"
```

### Task 5: Reuse Customer Customization Sheet In POS

**Files:**
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`
- Modify: `frontend/src/components/MenuQuickAddSheet.vue` (only if a POS mode prop is needed)
- Modify: `frontend/src/components/CartToppingSheet.vue` or replace its usage
- Modify: `frontend/src/utils/itemConfig.js` (only if missing normalization must be shared)

**Interfaces:**
- Consumes: `getItemDetail()`, `createDefaultCustomization()`, `sanitizeCustomization()`, `estimateLine()`
- Produces: POS add/edit customization flow using the same ingredient/modifier/alternative model as the menu flow

- [ ] **Step 1: Write the failing test**

Add a POS customization integration test asserting:

```js
await user.click(screen.getByRole('button', { name: /bom/i }))
expect(screen.getByText(/افزودن به سبد|اعمال تغییرات/)).toBeInTheDocument()
expect(screen.getByText(/برای این آیتم تنظیم قابل تغییر تعریف نشده است|سفارشی سازی/)).toBeInTheDocument()
```

Add a second assertion that applying customization persists a `selected_modifiers` payload into the cart line.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/pages/management/ManagementPosPage.test.js`

Expected: FAIL because POS still uses its reduced customization editor.

- [ ] **Step 3: Write minimal implementation**

Replace the reduced POS-only edit flow with a shared sheet-backed flow that:
- loads `ingredients` and `modifier_groups`
- uses `createDefaultCustomization()` for new lines
- uses existing cart-line customization payload for editing
- writes back:
  - `customization`
  - `customization_ingredients`
  - `modifier_groups_catalog`
  - computed unit/line pricing from `estimateLine()`

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/pages/management/ManagementPosPage.test.js`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/management/ManagementPosPage.vue frontend/src/components/MenuQuickAddSheet.vue frontend/src/components/CartToppingSheet.vue frontend/src/utils/itemConfig.js frontend/src/pages/management/ManagementPosPage.test.js
git commit -m "feat: reuse menu customization flow in POS"
```

### Task 6: Dark Mode Cleanup And Final Verification

**Files:**
- Modify: `frontend/src/components/management/pos/PosCartPanel.vue`
- Modify: `frontend/src/components/management/pos/PosProductPanel.vue`
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`
- Modify: any shared sheet component touched during Task 5

**Interfaces:**
- Consumes: management theme tokens in `ManagementLayout.vue`
- Produces: POS surfaces that respect dark mode consistently

- [ ] **Step 1: Write the failing test**

Add assertions for dark-mode class rendering on:
- dropdown surfaces
- compact cards
- customization sheet surface
- tax/service/discount controls

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- src/components/management/pos/PosCartPanel.test.js src/components/management/pos/PosProductPanel.test.js src/pages/management/ManagementPosPage.test.js`

Expected: FAIL because dark-mode surfaces still contain light-biased colors or missing theme hooks.

- [ ] **Step 3: Write minimal implementation**

Replace remaining hard-coded light backgrounds/borders with POS theme tokens and verify dropdown and sheet layers inherit the correct dark palette.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- src/components/management/pos/PosCartPanel.test.js src/components/management/pos/PosProductPanel.test.js src/pages/management/ManagementPosPage.test.js`

Expected: PASS

- [ ] **Step 5: Run build verification**

Run: `npm run build`

Expected: Vite build completes successfully.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/management/pos/PosCartPanel.vue frontend/src/components/management/pos/PosProductPanel.vue frontend/src/pages/management/ManagementPosPage.vue restaurant/public/frontend/assets
git commit -m "feat: finalize POS refinement dark mode and customization"
```
