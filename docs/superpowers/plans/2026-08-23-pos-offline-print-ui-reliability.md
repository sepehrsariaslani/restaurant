# POS Offline, Printing, Overlay, and Quick-Edit Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make management POS thermal printing width-safe, add real offline read/order-queue support, fix overlay stacking, and make POS quick-edit/out-of-stock behavior reliable.

**Architecture:** Keep the 300KB Vue POS page and 800KB legacy backend API stable. Extend the existing Vite source transform for page-level integration, add focused frontend offline/API modules, and add `restaurant/api_pos_reliability.py` for backend reliability operations. IndexedDB stores business-data snapshots and queued plain orders; the service worker only stores shell/static navigation assets.

**Tech Stack:** Vue 3, Vite 4, native IndexedDB, Service Worker Cache API, Node `node:test`, Frappe/ERPNext Python APIs.

**Spec:** `docs/superpowers/specs/2026-08-23-pos-offline-print-ui-reliability-design.md`

## Global Constraints

- No new frontend runtime dependency.
- No thermal `page-break-*`, `break-before`, `break-after`, or `break-inside` rules.
- Preserve 58/80mm per-device width selection and secondary-customer printing.
- Only `create_pos_order` semantics (Sales Order only, no settlement/payment) are queueable offline.
- Payment, settlement, credit verification, price edits, and availability edits require connectivity.
- Every queued order contains `client_order_key`; server replay is idempotent.
- Public-menu out-of-stock filtering is unchanged; only management POS boot is supplemented.
- All GitHub writes target `fix/pos-thermal-printing`.

---

### Task 1: Fix thermal roll overflow

**Files:**
- Modify: `frontend/tests/pos-print-transform.test.mjs`
- Modify: `frontend/scripts/pos-print-transform.mjs`

**Interfaces:** existing `transformManagementPosPage(source)`.

- [ ] Write a failing test requiring `box-sizing:border-box`, `.receipt max-width:100%`, wrapping for long content, constrained tables/images, and zero pagination rules.
- [ ] Run `cd frontend && node --test tests/pos-print-transform.test.mjs`; verify RED for missing containment rules.
- [ ] Inject the minimal CSS:

```css
*, *::before, *::after { box-sizing: border-box; }
html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; overflow-x: hidden; }
.receipt { width: ${paperWidthMm}mm; max-width: 100%; overflow: hidden; }
.receipt table, .receipt img, .receipt svg { max-width: 100%; }
.receipt td, .receipt th, .receipt span, .receipt p { min-width: 0; overflow-wrap: anywhere; word-break: break-word; }
```

- [ ] Run `node --check scripts/pos-print-transform.mjs && npm test`; verify GREEN.
- [ ] Commit `fix(pos): contain thermal receipts within roll width`.

---

### Task 2: Add native offline POS store

**Files:**
- Create: `frontend/tests/pos-offline-store.test.mjs`
- Create: `frontend/src/utils/posOfflineStore.js`

**Interfaces:**

```js
normalizePosSearchText(value)
searchCustomersInRows(rows, query, limit = 20)
createOfflineOrderRecord(payload, id)
mergeQueueRecords(current, incoming)
createPosOfflineStore({ indexedDB, now } = {})
```

Store methods: `savePosBootSnapshot`, `loadPosBootSnapshot`, `replaceCustomerCache`, `mergeCustomerCache`, `searchCachedCustomers`, `enqueueOfflineOrder`, `listPendingOfflineOrders`, `markOfflineOrderSynced`, `markOfflineOrderNeedsAttention`, `pendingOrderCount`.

- [ ] Write failing tests for Persian/Arabic normalization (`ي→ی`, `ك→ک`, Persian/Arabic digits→ASCII), name/mobile search, stable queue identity, duplicate queue merge, and `pending→needs_attention` transitions.
- [ ] Run `node --test tests/pos-offline-store.test.mjs`; verify RED because module is absent.
- [ ] Implement pure helpers first, then IndexedDB database `restaurant-pos-offline-v1` version 1 with stores `snapshots`, `customers`, `order_queue`.
- [ ] Make missing/unavailable IndexedDB degrade to empty cache results instead of throwing during POS boot.
- [ ] Run `npm test`; verify GREEN.
- [ ] Commit `feat(pos): add native offline data store`.

---

### Task 3: Add backend idempotency, reliable boot, and atomic quick edit

**Files:**
- Create: `restaurant/tests/test_api_pos_reliability.py`
- Create: `restaurant/api_pos_reliability.py`
- Create: `restaurant/patches/v2_12/__init__.py`
- Create: `restaurant/patches/v2_12/ensure_pos_reliability_fields.py`
- Modify: `restaurant/patches.txt`

**Interfaces:**

```python
get_management_pos_boot_reliable(branch=None)
replay_offline_pos_order(payload=None)
update_pos_product_atomic(payload=None)
```

Sales Order field: `restaurant_pos_client_order_key` (`Data`, `unique=1`, `read_only=1`, `no_copy=1`).

- [ ] Write failing backend tests for `_normalize_client_order_key`, duplicate-key lookup, and unavailable-item merge helper.
- [ ] The local harness has no Frappe runtime, so verify RED by importing the absent module in a lightweight test fixture; on the server the exact test command is `bench --site dehati.ir run-tests --app restaurant --module restaurant.tests.test_api_pos_reliability`.
- [ ] Add v2_12 field patch and append `restaurant.patches.v2_12.ensure_pos_reliability_fields` to `restaurant/patches.txt`.
- [ ] Implement reliable boot by calling `restaurant.api.get_management_pos_boot(branch)` and merging management-only out-of-stock items serialized through the existing legacy helpers. Copy `_core_item_filters(branch)` and remove only its `restaurant_out_of_stock` predicate before querying unavailable rows.
- [ ] Implement replay atomically with the existing non-committing helper:

```python
existing = _find_order_by_client_key(key)
if existing:
    return {'status': 'existing', 'order_id': existing, 'client_order_key': key}
result = legacy._create_pos_order_payload(data, commit=False)
order_id = result.get('order_id') or result.get('name')
frappe.db.set_value('Sales Order', order_id, 'restaurant_pos_client_order_key', key, update_modified=False)
frappe.db.commit()
return {'status': 'created', 'order_id': order_id, 'result': result, 'client_order_key': key}
```

- [ ] Implement quick edit directly in the same transaction; do **not** call the two public legacy setters because they can commit independently. Resolve item name with `legacy._management_resolve_item_name`, default selling price list with `legacy._get_default_selling_price_list_name(set_fallback_default=True)`, update/create the matching `Item Price`, update only allowed Item fields, save, then return `legacy.get_management_product_detail(item_name)`. No `frappe.db.commit()` before the whole operation succeeds.
- [ ] Run `python -m py_compile restaurant/api_pos_reliability.py restaurant/patches/v2_12/ensure_pos_reliability_fields.py` in a Python environment containing the files; run the Frappe test command above on deployment/server.
- [ ] Commit `feat(pos): add reliable backend for offline replay and quick edit`.

---

### Task 4: Integrate offline boot, customer search, queue, and sync into POS

**Files:**
- Create: `frontend/tests/pos-reliability-transform.test.mjs`
- Create: `frontend/src/utils/posReliabilityApi.js`
- Modify: `frontend/scripts/pos-print-transform.mjs`

**Interfaces:**

```js
getReliablePOSBoot({ branch })
replayOfflinePOSOrder(payload)
updatePOSProductAtomic(payload)
```

- [ ] Write failing transform tests requiring imports/store initialization, cached boot fallback, local-first customer search, queue count, offline plain-order message `ذخیره آفلاین شد`, and online-only settlement guard.
- [ ] Run `node --test tests/pos-reliability-transform.test.mjs`; verify RED.
- [ ] Implement `posReliabilityApi.js` using exported `callMethodByPath` from `@/utils/api` and paths under `restaurant.api_pos_reliability`.
- [ ] Transform `loadPOSBoot()` to call `getReliablePOSBoot`; persist successful boot and load the latest branch snapshot when connectivity fails.
- [ ] Transform `loadCustomers(search)` to show `searchCachedCustomers(search)` immediately, merge successful server results into IndexedDB, and never clear cached options on transport failure.
- [ ] Reuse the existing payload object created inside `submitPOSOrder`. When offline and `payNow/withProduction` is false, enqueue that exact payload with a generated `client_order_key`; when any payment/settlement path is requested offline, stop with `پرداخت یا تسویه نیاز به اتصال اینترنت دارد.`
- [ ] Add sequential `syncPendingOfflineOrders()` on reconnect and a manual retry path; transport failure leaves `pending`, business-rule failure marks `needs_attention`, success marks/removes synced record.
- [ ] Run `npm test`; verify GREEN.
- [ ] Commit `feat(pos): integrate offline cache and order sync`.

---

### Task 5: Fix z-index, Teleport, and unavailable/quick-edit behavior

**Files:**
- Modify: `frontend/tests/pos-reliability-transform.test.mjs`
- Modify: `frontend/scripts/pos-print-transform.mjs`

- [ ] Add failing assertions for semantic levels `--pos-z-operations:12000`, `--pos-z-dialog:14000`, `--pos-z-detail:15000`, order-detail inside `<Teleport to="body">`, unavailable guards, and `updatePOSProductAtomic`.
- [ ] Run the focused test; verify RED.
- [ ] Inject POS z-index variables and replace operations/modal/detail/print-picker magic z-index values with semantic variables. Keep order detail above operations and Teleport it to body.
- [ ] Add `isProductUnavailable(item)` using current out-of-stock flag plus non-expired `out_of_stock_until`; guard product increment/barcode-add paths while keeping quick-edit accessible.
- [ ] Replace current `Promise.all([setManagementProductPrice, updateManagementProductSettings])` quick edit with one `updatePOSProductAtomic` call. Block save when offline and reload reliable POS boot after successful save.
- [ ] Run `npm test`; verify GREEN.
- [ ] Commit `fix(pos): stabilize overlays and unavailable item editing`.

---

### Task 6: Make POS application shell reopen offline

**Files:**
- Create: `frontend/tests/pos-service-worker.test.mjs`
- Modify: `frontend/public/sw.js`

- [ ] Write failing source tests for cache version `veederakht-pwa-v4`, successful runtime caching of `/management/pos` navigation, static asset caching, and no API POST caching.
- [ ] Run the focused test; verify RED.
- [ ] Bump cache version to v4. Do **not** precache the protected `/management/pos` URL during install; instead, when an authenticated GET navigation to `/management/pos` succeeds, store that response in runtime cache and use it as navigation fallback while offline.
- [ ] Keep `/assets/restaurant/frontend/`, fonts, and images on stale-while-revalidate; leave POST requests untouched.
- [ ] Run `npm test`; verify GREEN.
- [ ] Commit `feat(pos): cache POS application shell for offline use`.

---

### Task 7: Final verification and PR refresh

**Files:** PR #10 metadata only; no production change without a new failing test.

- [ ] Run fresh frontend checks in the local harness: `node --check scripts/pos-print-transform.mjs`, checks for new JS modules, then `npm test`.
- [ ] Run Python `py_compile` on the new backend/patch files in the local working copy. If Frappe is unavailable locally, explicitly record that server-side Frappe tests were not runnable here.
- [ ] Run `npm run build` only when the full frontend source/dependencies are available; otherwise explicitly record the limitation.
- [ ] Compare `arena/019fffd4-restaurant...fix/pos-thermal-printing`, verify PR #10 is open/mergeable, and update its body with migration/rebuild requirements.
- [ ] Deployment on the known site uses:

```bash
bench --site dehati.ir migrate
bench build --app restaurant
bench --site dehati.ir clear-cache
bench --site dehati.ir clear-website-cache
bench restart
```

- [ ] POS terminals must refresh after deployment so service-worker v4 activates.
