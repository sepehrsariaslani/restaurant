# POS Workspace Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the restaurant management POS page so desktop always shows the cart beside products, while operational tabs move into an overlay panel and the whole workspace gets a cleaner, more coordinated visual system.

**Architecture:** Keep all POS state and business handlers inside `ManagementPosPage.vue`, but change the page composition into a desktop workspace with a fixed cart column and an overlay operations layer. Reuse `PosCartPanel.vue` and `PosProductPanel.vue` for behavior, limiting the change to layout, presentation, and interaction wiring so existing APIs, totals, table flows, and payment flows remain intact.

**Tech Stack:** Vue 3 SFCs, Vite 4, existing local CSS inside single-file components, `lucide-vue-next` for any new structural icons, existing POS API/state utilities.

## Global Constraints

- Keep cart visible as a fixed adjacent column beside products on desktop.
- Move operational tabs into an overlay panel that opens over the page.
- Preserve drawer/sheet behavior for cart and secondary panels on mobile.
- Use a minimal, warm, and professional visual direction.
- Use a lighter surface hierarchy with consistent spacing, radius, border, and shadow system.
- Keep business behavior intact; no backend/API changes are in scope.
- Existing modified frontend files are already dirty in the worktree, so implementation must edit carefully and avoid reverting unrelated changes.
- The redesign should reuse current state and handlers rather than re-architecting POS state.

---

### Task 1: Recompose the POS shell around a persistent desktop cart and operations overlay

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/pages/management/ManagementPosPage.vue:22-340`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/pages/management/ManagementPosPage.vue:620-760`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/pages/management/ManagementPosPage.vue:3880-4525`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/package.json`

**Interfaces:**
- Consumes: existing refs and handlers including `leftPanelTab`, `loadPOSBoot`, `loadOpenInvoices`, `loadTodayTransactions`, `loadRecentOrders`, `selectDineInTable`, `selectOpenInvoice`, `openOrderDetailModal`, `setOrderMode`, `setCartQty`, `submitPOSOrder`, `openPrintEditor`
- Produces:
  - `const operationsOverlayOpen = ref(false)`
  - `const isDesktopCartVisible = computed(() => true)` or equivalent responsive class-driven desktop placement
  - `function openOperationsOverlay(tab = leftPanelTab.value) => void`
  - `function closeOperationsOverlay() => void`
  - desktop layout wrappers: `.pos-workspace-head`, `.pos-main-grid`, `.pos-operations-overlay`, `.cart-desktop-col`

- [ ] **Step 1: Write the failing verification target**

Document the target markup change inside `ManagementPosPage.vue`:

```vue
<section class="pos-shell" dir="rtl">
  <header class="pos-workspace-head">
    <button type="button" class="ops-trigger">عملیات POS</button>
  </header>

  <div class="pos-main-grid">
    <PosProductPanel class="products-col" />
    <aside class="cart-desktop-col">
      <PosCartPanel />
    </aside>
  </div>

  <Transition name="ops-overlay">
    <div v-if="operationsOverlayOpen" class="pos-operations-overlay">...</div>
  </Transition>
</section>
```

- [ ] **Step 2: Run build to verify the old implementation does not satisfy the new structure**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS build, but manual source inspection still shows:
- fixed desktop `left-col`
- floating desktop `cart-fab`
- cart only inside `cart-drawer`

- [ ] **Step 3: Write the minimal implementation**

Update the template so the desktop shell becomes:

```vue
<section class="pos-shell" dir="rtl">
  <header class="pos-workspace-head">
    <div class="pos-workspace-tools">
      <button type="button" class="ops-trigger" @click="openOperationsOverlay()">
        عملیات POS
      </button>
      <button type="button" class="kbd-help-btn" title="میانبرهای کیبورد (?)" @click="showKeyboardMap = true">⌨</button>
    </div>
  </header>

  <div class="pos-main-grid">
    <PosProductPanel class="products-col" ... />

    <aside class="cart-desktop-col">
      <PosCartPanel
        ref="cartPanelRef"
        :cart-lines="cart"
        :selected-line-id="selectedCartLineId"
        :currency="currency"
        :order-mode="form.order_mode"
        :place="form.place"
        :place-options="placeOptions"
        :table-orders="selectedDineInOrders"
        :table-preview-loading="tablePreviewLoading"
        :selected-table-label="selectedDineInTable?.label || ''"
        :can-print-table-orders="confirmedDineInOrders.length > 0"
        :note="form.note"
        :payment-method="payment.method"
        :payment-reference="payment.reference_no"
        :payment-rrn="payment.rrn"
        :payment-boot="paymentBoot"
        :financial="financial"
        :totals="totals"
        :submitting="submitting"
        :undo-line="lastRemovedLine"
        @update:selected-line-id="selectedCartLineId = $event"
        @update:order-mode="setOrderMode"
        @update:place="form.place = $event"
        @update:note="form.note = $event"
        @update:payment-method="payment.method = $event"
        @update:payment-reference="payment.reference_no = $event"
        @update:payment-rrn="payment.rrn = $event"
        @patch-financial="patchFinancial"
        @increment-line="setCartQty($event, Number($event.qty || 0) + 1)"
        @decrement-line="setCartQty($event, Number($event.qty || 0) - 1)"
        @remove-line="setCartQty($event, 0)"
        @undo-last-line="undoLastRemoval"
        @edit-line-note="editLineNote"
        @edit-line-customization="openLineCustomizationEditor"
        @clear-cart="clearCart"
        @verify-credit="verifyCreditCard"
        @verify-coupon="verifyCoupon"
        @update-table-order-item="changeTableOrderItemQty($event.order, $event.item, $event.delta)"
        @print-confirmed-table="printConfirmedTableOrders"
        @submit-order="submitPOSOrder(false)"
        @submit-and-pay="submitPOSOrder(true)"
        @print-ticket="openPrintEditor"
      />
    </aside>
  </div>
```

Add overlay state and keyboard-safe closing:

```js
const operationsOverlayOpen = ref(false)

function openOperationsOverlay(tab = leftPanelTab.value) {
  leftPanelTab.value = tab
  operationsOverlayOpen.value = true
}

function closeOperationsOverlay() {
  operationsOverlayOpen.value = false
}
```

Render the former `left-col` panels inside the overlay container and keep the old cart drawer only for narrow breakpoints.

- [ ] **Step 4: Run build to verify it passes**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS with Vite production bundle output and no Vue template errors.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add frontend/src/pages/management/ManagementPosPage.vue
git commit -m "feat: restructure desktop POS workspace"
```

### Task 2: Restyle the cart panel for persistent desktop use

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/components/management/pos/PosCartPanel.vue:1-350`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/components/management/pos/PosCartPanel.vue:430-980`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/package.json`

**Interfaces:**
- Consumes: existing props `cartLines`, `financial`, `totals`, `submitting`, `orderMode`, `note`, `undoLine`
- Produces:
  - persistent desktop cart layout with stable internal sections
  - cleaner row classes such as `.cart-shell`, `.cart-scroll`, `.cart-summary-sticky`, `.cart-financial-card`
  - no structural emoji dependency for empty state or actions

- [ ] **Step 1: Write the failing verification target**

Document the target section structure:

```vue
<section class="cart-panel cart-shell">
  <div class="cart-scroll">
    <div class="cart-section">...</div>
    <div class="fin-section cart-financial-card">...</div>
  </div>

  <div class="cart-summary-sticky">
    <div class="summary-box">...</div>
    <footer class="checkout-actions">...</footer>
  </div>
</section>
```

- [ ] **Step 2: Run build to verify the current panel still reflects the old noisy layout**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS build, but source still shows:
- single uninterrupted panel flow
- emoji empty-state cart icon
- lightweight drawer-oriented structure instead of persistent-column structure

- [ ] **Step 3: Write the minimal implementation**

Rework the cart template around a scroll region plus sticky summary/actions:

```vue
<section class="cart-panel cart-shell">
  <div class="cart-panel-head">
    <div>
      <p class="cart-eyebrow">سفارش فعال</p>
      <h3>سبد خرید</h3>
    </div>
    <div class="cart-head-actions">...</div>
  </div>

  <div class="cart-scroll">
    <div class="place-field">...</div>
    <div class="cart-section">...</div>
    <div class="fin-section cart-financial-card">...</div>
  </div>

  <div class="cart-summary-sticky">
    <div class="summary-box">...</div>
    <footer class="checkout-actions">...</footer>
  </div>
</section>
```

Update the empty state and row actions to quieter, consistent controls:

```vue
<div class="cart-empty" v-else>
  <div class="cart-empty-mark" aria-hidden="true"></div>
  <p>سبد خرید هنوز آیتمی ندارد</p>
</div>
```

Keep all emits and totals logic untouched while replacing the visual styling blocks to use:
- 8px radius
- lighter borders
- muted neutral backgrounds
- stronger price alignment
- sticky checkout footer on desktop

- [ ] **Step 4: Run build to verify it passes**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS with no template or CSS parsing failures.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add frontend/src/components/management/pos/PosCartPanel.vue
git commit -m "feat: refine persistent POS cart panel"
```

### Task 3: Align the product panel and overlay visuals into a cohesive POS workspace

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/components/management/pos/PosProductPanel.vue`
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/pages/management/ManagementPosPage.vue:3880-4525`
- Optionally Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/components/AmountPercentToggle.vue`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/package.json`

**Interfaces:**
- Consumes: current product search, customer query, scanner input, product view toggles, category rail, quantity map
- Produces:
  - normalized top control sizing between product panel and cart panel
  - overlay visual tokens matching the persistent cart
  - removal of desktop `cart-fab` prominence

- [ ] **Step 1: Write the failing verification target**

Document the intended workspace visual hierarchy:

```css
.pos-main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 20px;
}

.pos-operations-overlay {
  position: fixed;
  inset: 0;
  background: rgba(24, 18, 12, 0.34);
}

.pos-operations-sheet {
  width: min(420px, calc(100vw - 24px));
  border-radius: 8px;
}
```

- [ ] **Step 2: Run build to verify the existing styling baseline**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS build, but source still shows older spacing/tone mismatches between product controls, left sidebar, and cart.

- [ ] **Step 3: Write the minimal implementation**

Apply coordinated styling updates:

```css
.pos-shell {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pos-workspace-head,
.cart-panel-head,
.product-toolbar {
  min-height: 48px;
  border: 1px solid var(--pos-border);
  background: var(--pos-surface);
}

.ops-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
```

Inside `PosProductPanel.vue`, normalize the control rows and card spacing so the products side matches the persistent cart density. If `AmountPercentToggle.vue` visually clashes with the new neutral system, update only its local classes/tokens without changing its emitted values.

- [ ] **Step 4: Run build to verify it passes**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS with final production bundle output and no CSS errors.

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add frontend/src/components/management/pos/PosProductPanel.vue frontend/src/pages/management/ManagementPosPage.vue frontend/src/components/AmountPercentToggle.vue
git commit -m "feat: polish POS workspace visuals"
```

### Task 4: Verify desktop/mobile behavior and preserve operational flows

**Files:**
- Modify: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/src/pages/management/ManagementPosPage.vue`
- Test: `/home/sepehr/den-v16-docker/apps/restaurant/frontend/package.json`

**Interfaces:**
- Consumes: completed desktop layout, overlay controls, persistent cart column, mobile cart drawer
- Produces:
  - responsive guards for desktop-only cart column and mobile-only cart drawer button
  - final smoke-verified POS flow across product/cart/operations interactions

- [ ] **Step 1: Write the failing verification target**

List the required smoke cases:

```text
1. Desktop shows products + persistent cart together
2. Desktop opens and closes operations overlay without affecting cart state
3. Mobile retains drawer access to the cart
4. Table and invoice actions still invoke existing handlers
5. Payment popup and print editor still open from the cart
```

- [ ] **Step 2: Run build before the final responsive pass**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS, establishing the pre-final verification baseline.

- [ ] **Step 3: Write the minimal implementation**

Add or adjust responsive classes/media rules so:

```css
@media (min-width: 1180px) {
  .cart-desktop-col { display: flex; }
  .cart-fab,
  .cart-drawer-backdrop { display: none; }
}

@media (max-width: 1179px) {
  .cart-desktop-col { display: none; }
}
```

Add any missing `Escape` handling and focus-safe close behavior for the operations overlay, keeping the mobile drawer available where desktop cart is hidden.

- [ ] **Step 4: Run final verification**

Run: `cd /home/sepehr/den-v16-docker/apps/restaurant/frontend && npm run build`

Expected: PASS with successful Vite build output.

Manual smoke checklist:
- open `/management/pos`
- confirm desktop cart remains visible while browsing products
- open `عملیات POS`, switch through all four tabs, close with backdrop and `Escape`
- add/remove cart items, edit note, verify totals change
- open payment popup and print editor

- [ ] **Step 5: Commit**

```bash
cd /home/sepehr/den-v16-docker/apps/restaurant
git add frontend/src/pages/management/ManagementPosPage.vue
git commit -m "fix: finalize POS responsive workspace behavior"
```
