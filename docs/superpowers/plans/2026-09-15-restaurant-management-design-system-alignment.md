# Restaurant Management Design-System Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** یکدست‌سازی صفحات مدیریت رستوران با استفاده از دیزاین‌سیستم Restaurant و حفظ ERPNext به‌عنوان منبع اصلی داده و چرخه‌ی اسناد.

**Architecture:** صفحات مدیریت workflow را compose می‌کنند و منطق داده در APIهای فعلی Restaurant/ERPNext می‌ماند. `ManagementPageScaffold`، `ManagementSurfaceCard`، `ManagementListView` و tokenهای `--ds-*` لایه‌ی مشترک هستند؛ دامنه‌های خاص مثل میز، پیک، آشپزخانه و منو facade عملیاتی Restaurant باقی می‌مانند.

**Tech Stack:** Vue 3, Vite, Composition API, `lucide-vue-next`, Node test runner, Frappe website route rules, ERPNext DocTypes.

**Spec:** `docs/superpowers/specs/2026-09-15-restaurant-management-design-system-alignment-design.md`

## Global Constraints

- صفحات `ManagementProductsPage.vue`، `ManagementProductDetailPage.vue` و `ManagementPosPage.vue` در این بازطراحی تغییر بصری یا فرایندی نمی‌کنند.
- تمرکز فعلی روی `ManagementSalesDashboardPage.vue` نیست.
- ERPNext برای User/Role، Item، Item Attribute، اسناد مالی، stock، customer و lifecycle منبع authoritative است.
- UI قابل مشاهده باید فارسی، RTL، Peyda و token-based باشد.
- build، restart، `bench migrate` و Graphify اجرا نمی‌شوند.
- تغییرات موجود کاربر در `public/frontend/assets` stage یا overwrite نمی‌شوند.

---

### Task 1: مسیر و قرارداد shell دیزاین‌سیستم

**Files:**
- Modify: `restaurant/hooks.py`
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/management/ManagementLayout.vue`
- Test: `frontend/tests/design-system-contract.test.mjs`

- [x] **Step 1: Write the failing route contract**

Assert that the browser route, management branch, Navbar entry and Frappe `website_route_rules` all contain `/management/design-system`.

- [x] **Step 2: Run the focused contract**

Run: `cd frontend && node --test tests/design-system-contract.test.mjs`

Expected before the route rule exists: the route contract fails on `restaurant/hooks.py`.

- [x] **Step 3: Register both route spellings**

Add `/management/design-system` and `/management/design_system` to `website_route_rules`, targeting `management/design_system`, while retaining the existing App resolver and Navbar entry.

- [x] **Step 4: Run the focused contract again**

Run: `cd frontend && node --test tests/design-system-contract.test.mjs`

Expected: all design-system contract tests pass.

### Task 2: Product-reference shared list contract

**Files:**
- Modify: `frontend/src/pages/management/catalog/ManagementVariantBuilderPage.vue`
- Test: `frontend/tests/design-system-contract.test.mjs`

- [x] **Step 1: Add a failing source contract**

Assert that the Item Attribute catalog imports `ManagementListView`, passes `itemAttributeCatalog` as rows, defines columns and opens the editor on row selection.

- [x] **Step 2: Replace the duplicate table/mobile markup**

Use `ManagementListView` with Persian slots for label, type, value count, status and ERP/edit actions. Keep `loadItemAttributeCatalog`, `openItemAttributeEditor` and all API payloads unchanged.

- [x] **Step 3: Verify**

Run the focused contract and Vue SFC parse/template compilation for `ManagementVariantBuilderPage.vue`.

### Task 3: Orders list-to-detail workflow

**Files:**
- Modify: `frontend/src/pages/management/sales/ManagementOrdersPage.vue`
- Test: `frontend/tests/design-system-contract.test.mjs`

- [x] **Step 1: Add the workflow contract**

Assert that orders use the shared list, pass `displayOrders`, emit `openOrderDetail`, and retain `getManagementOrderDetail` and `selectedOrder`.

- [x] **Step 2: Compose the shared list**

Replace the duplicate order-row list with `ManagementListView`; render Persian status/payment slots, localized amount/date, and a details action. Keep query navigation and detail panel operations unchanged.

- [x] **Step 3: Verify**

Run the focused contract and SFC parse/template compilation for `ManagementOrdersPage.vue`.

### Task 4: Courier list-to-detail workbench

**Files:**
- Modify: `frontend/src/pages/management/operations/ManagementCouriersPage.vue`
- Test: `frontend/tests/design-system-contract.test.mjs`

- [x] **Step 1: Add the workbench contract**

Assert that the courier page uses `ManagementListView`, passes `couriers`, selects `editCourier`, and exposes a product-like `courier-workbench` with Persian detail title.

- [x] **Step 2: Split list and detail responsibilities**

Place the courier list in the left surface and the selected/new courier editor in the right sticky surface. Preserve save/delete APIs, fields, active state, access code, notes and load behavior.

- [x] **Step 3: Verify**

Run the focused contract and SFC parse/template compilation for `ManagementCouriersPage.vue`.

### Task 5: Complete the management coverage audit

**Files:**
- Inspect/modify: `frontend/src/pages/management/**/*.vue`
- Inspect/modify: `frontend/src/components/management/**/*.vue`
- Modify: `frontend/src/design-system/catalog.js`
- Modify: `frontend/tests/*.test.mjs`

- [ ] **Step 1: Build the page coverage matrix**

For each management page record its route, ERPNext source/API, shell, list component, detail component, token usage, Persian copy status, empty/loading/error states and excluded/reference status.

- [ ] **Step 2: Normalize one domain at a time**

Apply the closest existing pattern in this order: inventory materials/purchases/requests, menu groups/modifiers/attributes, customers/club/call center, tables/reservations, reports/accounting, settings/help. Do not alter product detail, products list, POS or sales dashboard scope.

- [ ] **Step 3: Replace duplicate list/table markup**

Use `ManagementListView` for entity lists, `ManagementDataTable` for dense tabular operations, and `InventoryResponsiveList`/`InventorySectionShell` where those are the established domain owners. Preserve row actions and API contracts.

- [ ] **Step 4: Remove visible untranslated UI copy**

Replace user-facing English labels with Persian equivalents while keeping technical identifiers in `dir="ltr"` fields, ERP links, or code labels where necessary.

- [ ] **Step 5: Add focused contracts per domain**

Each normalized domain must have a source/behavior test covering route ownership, shared component usage, preserved API call, and at least one empty/loading/error state.

### Task 6: Define the ERPNext/Restaurant management map

**Files:**
- Create: `docs/restaurant-management-coverage.md`
- Modify: `/Users/sepehr/.codex/skills/restaurant/references/architecture.md`
- Modify: `/Users/sepehr/.codex/skills/restaurant/references/design-system.md`
- Modify: `/Users/sepehr/.codex/skills/restaurant/SKILL.md`

- [x] **Step 1: Map native ERPNext surfaces**

Document Item, Item Attribute, Item Variant, Customer, Supplier, User/Role, Warehouse, Stock Ledger, Sales Order/Invoice, Purchase Order/Invoice, Payment Entry and accounting reports as native sources with Restaurant presentation wrappers.

- [x] **Step 2: Map Restaurant-owned domains**

Document tables, reservations, kitchen display, menu composition, modifiers, restaurant product flags, couriers/fleet/zones, waiter operational context and delivery provider settings.

- [x] **Step 3: Record current route and verification state**

For each domain include route, page owner, API owner, native/custom source, lifecycle actions, permissions and whether authenticated browser verification remains.

### Task 7: Final verification and handoff

**Files:**
- Test: `frontend/tests/*.test.mjs`
- Inspect: `frontend/src/**/*.vue`, `frontend/src/**/*.js`, `restaurant/hooks.py`

- [ ] **Step 1: Run focused tests**

Run the changed domain contract tests and SFC parse/template checks.

- [ ] **Step 2: Run the complete source test suite**

Run: `cd frontend && npm test`

- [ ] **Step 3: Run structural checks**

Run the Restaurant scanner and `git diff --check`; inspect `git status --short` to ensure generated user changes remain unstaged.

- [ ] **Step 4: Report deployment boundary**

Report that build is needed for the frontend bundle, route reload/restart is needed for updated Frappe hooks, migration is not needed unless a DocType/schema change was introduced, and Graphify was not run.
