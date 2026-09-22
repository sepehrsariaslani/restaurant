# Home Builder Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the dynamic home-page Builder and its desktop/mobile previews reliable for full-screen Hero, real menu categories, standard image uploads, and Persian feature editing.

**Architecture:** Keep the existing block registry and public page renderer as the single rendering path. Add a small pure authoring-data utility for merging management settings with menu boot data and normalizing legacy text, then connect the management page and block property form to existing API and upload components.

**Tech Stack:** Vue 3, Vite, lucide-vue-next, existing Frappe upload API, Node test runner.

## Global Constraints

- Keep all visible management UI Persian and RTL.
- Reuse `ManagementImageDropzone`, `SearchableDropdown`, existing theme tokens, and `RestaurantLandingPage` preview.
- Do not hardcode restaurant categories, products, or uploaded image URLs.
- Do not add a backend endpoint when `getMenuBoot()` and `uploadFileToFrappe()` already provide the required data flow.

### Task 1: Add failing authoring-data tests

**Files:**
- Create: `frontend/tests/home-builder-authoring.test.mjs`
- Create: `frontend/src/utils/homeBuilder.js`

**Interfaces:**
- Produce `mergeBuilderBoot({ baseBoot, settings, heroSlides, aboutSections, faqItems, menuBoot })`.
- Produce `decodeEscapedUnicode(value)` and `normalizeFeatureItems(items)`.
- Produce `normalizeBuilderCategories(categories)`.

- [ ] **Step 1: Write failing tests** for escaped Persian text, category normalization, and menu data merging.
- [ ] **Step 2: Run `npm test -- tests/home-builder-authoring.test.mjs`** and confirm the new imports/functions fail because the utility does not exist.
- [ ] **Step 3: Implement only the pure utility needed by the tests.** Preserve unrelated boot fields and prefer `menuBoot.categories` when present.
- [ ] **Step 4: Run the focused test and then the full frontend test suite.**
- [ ] **Step 5: Commit the utility and tests with a Persian message.**

### Task 2: Make Builder boot data real and preview-safe

**Files:**
- Modify: `frontend/src/pages/management/ManagementSiteSettingsPage.vue`
- Modify: `frontend/src/utils/api.js` only if the existing `getMenuBoot()` response needs a narrow normalization fix.
- Test: `frontend/tests/home-builder-authoring.test.mjs`

**Interfaces:**
- Load management settings and `getMenuBoot()` together.
- Feed the merged result to `ManagementPageBuilderWorkspace` through `builderBoot`.

- [ ] **Step 1: Add a failing assertion** that merged builder boot contains menu categories and preserves draft branding/content.
- [ ] **Step 2: Verify the assertion fails** against the current `builderBoot`, which only reads `window._BOOT.categories`.
- [ ] **Step 3: Import `getMenuBoot`, store the loaded menu payload, and build `builderBoot` through `mergeBuilderBoot`.** Keep settings failure and menu failure independent so the Builder remains usable.
- [ ] **Step 4: Load the menu payload during the existing settings load lifecycle and show a Persian non-blocking status/error when categories cannot be loaded.**
- [ ] **Step 5: Run the focused data tests and the existing frontend tests.**
- [ ] **Step 6: Commit the data-flow change with a Persian message.**

### Task 3: Repair Hero full-screen rendering and responsive Preview

**Files:**
- Modify: `frontend/src/components/blocks/HeroBlock.vue`
- Modify: `frontend/src/components/blocks/blocks.css`
- Modify: `frontend/src/pages/management/ManagementSiteSettingsPage.vue`
- Modify: `frontend/src/components/management/ManagementPageBuilderWorkspace.vue` only if the device viewport needs a focused responsive fix.

**Interfaces:**
- Preserve public `HeroBlock` props and registry Variant values.
- Keep `preview-mode` and desktop/mobile device controls compatible.

- [ ] **Step 1: Add a failing structural test** that asserts the hero registry exposes the `fullscreen` Variant and the full-bleed class contract.
- [ ] **Step 2: Run the test and confirm it fails for the missing/insufficient full-bleed contract.**
- [ ] **Step 3: Make `fullscreen` full width, viewport-height aware, and mobile-safe using existing block tokens; retain readable overlay and CTA focus states.**
- [ ] **Step 4: Route the visual settings preview for `fullscreen` to the same Hero component path instead of the empty fallback.**
- [ ] **Step 5: Keep the Builder phone viewport at a real narrow width with vertical scrolling and responsive block styles.**
- [ ] **Step 6: Run build and focused tests.**
- [ ] **Step 7: Commit the Hero and Preview changes with a Persian message.**

### Task 4: Use the canonical image dropzone everywhere

**Files:**
- Modify: `frontend/src/components/management/builder/BlockPropsForm.vue`
- Modify: `frontend/src/pages/management/ManagementSiteSettingsPage.vue`
- Modify: `frontend/src/components/management/ManagementEditableTable.vue` only if its slot contract needs an upload-safe editor hook.

**Interfaces:**
- Reuse `ManagementImageDropzone` and `uploadFileToFrappe()`.
- Continue emitting block prop updates through the existing `update` event.

- [ ] **Step 1: Add a failing source-level test** confirming image fields and content editors are wired to `ManagementImageDropzone` rather than direct `FileReader` data URLs.
- [ ] **Step 2: Run the test and confirm current raw text/file inputs fail the contract.**
- [ ] **Step 3: Replace generic block image inputs with `ManagementImageDropzone`, forwarding update and upload errors without breaking draft updates.**
- [ ] **Step 4: Replace Hero, slide, About, and FAQ image controls in site settings with the same dropzone while preserving manual URL entry and preview.**
- [ ] **Step 5: Verify upload success stores a server file URL, and upload failure leaves the previous value unchanged.**
- [ ] **Step 6: Run the frontend build and focused tests.**
- [ ] **Step 7: Commit the upload integration with a Persian message.**

### Task 5: Fix feature editor text and icon selection

**Files:**
- Modify: `frontend/src/components/management/builder/BlockPropsForm.vue`
- Modify: `frontend/src/utils/homeBuilder.js`
- Modify: `frontend/src/components/blocks/FeaturesBlock.vue` only if icon normalization needs a shared fallback.
- Test: `frontend/tests/home-builder-authoring.test.mjs`

**Interfaces:**
- Feature rows remain `{ icon, title, description }`.
- Existing saved layouts remain readable.

- [ ] **Step 1: Add failing tests** for converting escaped labels and preserving valid icon keys.
- [ ] **Step 2: Run the tests and confirm the legacy escaped values are not normalized.**
- [ ] **Step 3: Replace literal escaped template labels with Persian text, add a Design System-backed icon selector, and normalize legacy rows before rendering.**
- [ ] **Step 4: Keep add/remove/update row behavior and make the controls touch-safe on mobile.**
- [ ] **Step 5: Run focused tests, full tests, and production build.**
- [ ] **Step 6: Commit the feature editor fix with a Persian message.**

### Task 6: Full verification and handoff

**Files:**
- Modify: only if verification exposes a regression.

- [ ] **Step 1: Run `npm test` from `frontend/`.**
- [ ] **Step 2: Run `npm run build` from `frontend/`.**
- [ ] **Step 3: Inspect `git diff --check`, branch status, and the final diff for unintended files or raw escaped Persian labels.**
- [ ] **Step 4: Push the completed branch to GitHub.**
- [ ] **Step 5: Report the branch, commits, verification results, and any limitation requiring live browser/backend data.**
