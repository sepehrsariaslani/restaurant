# Product Reference Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** قالب فهرست و جزئیات محصول را به shellهای قابل استفاده‌ی مجدد تبدیل کنیم و همان قرارداد را در Design System و routeهای محصول نمایش دهیم.

**Architecture:** دو کامپوننت presentation-only در `components/management/catalog/` ساخته می‌شوند. صفحات محصول transport و منطق دامنه را نگه می‌دارند و فقط composition موجود را داخل slotهای shell قرار می‌دهند؛ Design System همان shellها را با fixture ثابت نمایش می‌دهد.

**Tech Stack:** Vue 3 SFC، Composition API، CSS semantic tokens، Node test runner، `@vue/compiler-sfc`.

**Spec:** `docs/superpowers/specs/2026-09-15-product-reference-components-design.md`

## Global Constraints

- از API، DocType، payload، query parameter و lifecycle فعلی استفاده شود.
- هیچ raw hex جدیدی در style کامپوننت‌ها اضافه نشود.
- build، restart، migrate و Graphify اجرا نشود.
- فایل‌های dirty تولیدشده در `restaurant/public/frontend/assets/` خارج از scope بمانند.

---

### Task 1: ثبت قرارداد کامپوننت‌ها

**Files:**
- Modify: `frontend/tests/management-data-components.test.mjs`

**Interfaces:**
- Consumes: source strings for catalog, product list page, product detail page, and future shell paths.
- Produces: failing contract assertions for shell props/slots, catalog references, and route usage.

- [ ] **Step 1: Write the failing test**

  تستی اضافه شود که دو shell را با نام فایل مشخص پیدا کند، `defineProps` مربوط به title/subtitle/loading/error و slotهای قراردادی را بررسی کند، catalog را برای component/pattern/template reference بررسی کند و دو صفحه‌ی محصول را برای import و template usage بررسی کند.

- [ ] **Step 2: Run test to verify it fails**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: FAIL چون shellها و catalog entries هنوز وجود ندارند.

- [ ] **Step 3: Commit**

  این task با task بعدی commit می‌شود تا test و implementation یک تغییر قابل بازبینی بسازند.

### Task 2: ساخت Collection Shell

**Files:**
- Create: `frontend/src/components/management/catalog/ManagementProductCollectionShell.vue`
- Modify: `frontend/src/pages/management/catalog/ManagementProductsPage.vue`

**Interfaces:**
- Consumes: `title`, `subtitle`, `tone`, `loading`, `error`, `retryLabel`, `@retry`, and slots `toolbar`, `status`, `default`, `overlays`.
- Produces: reusable collection frame with semantic loading/error regions and slot-based view content.

- [ ] **Step 1: Write the failing test**

  از قرارداد Task 1 استفاده شود.

- [ ] **Step 2: Run test to verify it fails**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: FAIL on missing collection shell/import/usage.

- [ ] **Step 3: Write minimal implementation**

  shell را با `ManagementSurfaceCard`، slotهای قراردادی، `aria-live` برای status و خطای semantic پیاده‌سازی کن. صفحه‌ی محصولات فقط toolbar، پیام‌ها، بدنه‌ی نماها و popupهای فعلی را به slotهای shell منتقل کند.

- [ ] **Step 4: Run test to verify it passes**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: PASS for collection shell and route usage.

### Task 3: ساخت Detail Shell

**Files:**
- Create: `frontend/src/components/management/catalog/ManagementProductDetailShell.vue`
- Modify: `frontend/src/pages/management/catalog/ManagementProductDetailPage.vue`

**Interfaces:**
- Consumes: `title`, `subtitle`, `loading`, `error`, `retryLabel`, `@retry`, and slots `breadcrumb`, `hero`, `navigation`, `status`, `default`, `overlays`.
- Produces: reusable detail frame that preserves product-specific hero, tabs, forms, tables, and dialogs through slots.

- [ ] **Step 1: Write the failing test**

  از قرارداد Task 1 استفاده شود.

- [ ] **Step 2: Run test to verify it fails**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: FAIL on missing detail shell/import/usage.

- [ ] **Step 3: Write minimal implementation**

  shell را با slotهای بالا و status/error قابل دسترس بساز. صفحه‌ی جزئیات فقط قاب بیرونی، breadcrumb، کارت اطلاعات کلی، section picker، پیام‌ها، محتوای tab و popupهای فعلی را به shell بدهد.

- [ ] **Step 4: Run test to verify it passes**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: PASS for both shells and both product routes.

### Task 4: نمایش زنده در Design System

**Files:**
- Modify: `frontend/src/design-system/catalog.js`
- Modify: `frontend/src/pages/management/design-system/ManagementDesignSystemPage.vue`

**Interfaces:**
- Consumes: both shells and existing deterministic `referenceProduct` fixture.
- Produces: live component, pattern, and template specimens linked to real product routes.

- [ ] **Step 1: Write the failing test**

  catalog assertions از Task 1 باید idهای collection/detail shell و patternهای `product-collection-shell` و `product-detail-shell` را انتظار داشته باشند.

- [ ] **Step 2: Run test to verify it fails**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: FAIL until catalog and live specimens are added.

- [ ] **Step 3: Write minimal implementation**

  entries را در catalog اضافه کن، importهای shell را در صفحه‌ی Design System اضافه کن و در components/templates یک specimen با toolbar, status, empty/loading and detail slots نمایش بده.

- [ ] **Step 4: Run test to verify it passes**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: PASS.

### Task 5: Regression verification and documentation

**Files:**
- Modify: `docs/restaurant-management-coverage.md`
- Verify: `frontend/tests/management-data-components.test.mjs`

**Interfaces:**
- Consumes: final shell ownership and product route usage.
- Produces: documented canonical ownership and verified source contract.

- [ ] **Step 1: Run focused tests**

  Run: `npm test -- --test-name-pattern="product reference shell"`
  Expected: all focused assertions pass.

- [ ] **Step 2: Run full frontend tests**

  Run: `npm test`
  Expected: zero failures.

- [ ] **Step 3: Compile management SFC templates**

  Run the repository’s existing parser/compiler check for all management Vue files and confirm zero template errors.

- [ ] **Step 4: Check diff and status**

  Run: `git diff --check` and `git status --short --branch`.
  Expected: no whitespace errors; generated asset changes remain unstaged.

- [ ] **Step 5: Commit**

  Commit the source, tests, docs, spec, and plan with a Persian message explaining the new reusable product shells and Design System references.
