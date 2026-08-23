# POS Offline, Printing, Overlay, and Quick-Edit Reliability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make management POS thermal printing width-safe, add real offline read/order-queue support, fix overlay stacking, and make POS quick-edit/out-of-stock behavior reliable.

**Architecture:** Keep large existing POS files stable by extending the existing Vite pre-transform for `ManagementPosPage.vue`, add focused browser modules for offline data and reliability API calls, and add a focused backend module `restaurant/api_pos_reliability.py` instead of modifying the 800KB legacy API file. IndexedDB owns business-data cache/queue, while the service worker only owns shell/static cache. Backend idempotency and atomic quick edit live in the new reliability API module.

**Tech Stack:** Vue 3, Vite 4, native IndexedDB, Service Worker Cache API, Node `node:test`, Frappe/ERPNext Python APIs.

**Spec:** `docs/superpowers/specs/2026-08-23-pos-offline-print-ui-reliability-design.md`

## Global Constraints

- No new frontend runtime dependency for offline storage.
- Thermal receipts remain continuous-roll friendly; do not introduce `page-break-*` or pagination rules.
- Administrative changes such as price/out-of-stock must require live server confirmation and must not be queued offline.
- Only plain order creation without settlement/payment is eligible for offline queueing.
- Queued orders use a unique client idempotency key and replay must not create duplicate Sales Orders.
- Preserve current 58/80mm per-device print width behavior and secondary-customer printing.
- Full-screen/nested POS overlays must have deterministic body-level stacking.
- Do not globally change public-menu out-of-stock filtering; management POS gets its own include-unavailable behavior.

---

## File Structure

### New files

- `frontend/src/utils/posOfflineStore.js` — IndexedDB adapter plus pure normalization/search/queue helpers.
- `frontend/src/utils/posReliabilityApi.js` — calls the new backend reliability endpoints through existing `callMethodByPath`.
- `frontend/tests/pos-offline-store.test.mjs` — pure helper tests and injectable adapter tests.
- `frontend/tests/pos-reliability-transform.test.mjs` — source-transform assertions for offline fallback, queue guards, Teleport, z-index, and unavailable-item behavior.
- `restaurant/api_pos_reliability.py` — reliable POS boot supplement, idempotent queued-order replay endpoint, atomic quick-edit endpoint.
- `restaurant/patches/v2_12/__init__.py` — patch package.
- `restaurant/patches/v2_12/ensure_pos_reliability_fields.py` — Sales Order client idempotency custom field patch.
- `restaurant/tests/test_api_pos_reliability.py` — backend helper/unit-oriented tests where Frappe test runner is available.

### Modified files

- `frontend/scripts/pos-print-transform.mjs` — print width fix plus POS reliability source transforms.
- `frontend/tests/pos-print-transform.test.mjs` — print regression assertions.
- `frontend/vite.config.js` — keep the transform registered; only update if a new export is required.
- `frontend/public/sw.js` — POS shell/static offline cache version and navigation strategy.
- `frontend/package.json` — current `node --test tests/*.test.mjs` already covers new frontend tests; change only if necessary.
- `restaurant/patches.txt` — register v2_12 patch.

---

### Task 1: Thermal receipt physical-width containment

**Files:**
- Modify: `frontend/scripts/pos-print-transform.mjs`
- Modify: `frontend/tests/pos-print-transform.test.mjs`

**Interfaces:**
- Consumes: existing `transformManagementPosPage(source: string): string`.
- Produces: transformed receipt CSS where physical width includes padding and long content cannot expand the roll.

- [ ] **Step 1: Add failing receipt-width tests**

Extend the existing thermal test with assertions equivalent to:

```js
assert.match(transformed, /\*, \*::before, \*::after \{ box-sizing: border-box; \}/)
assert.match(transformed, /\.receipt \{[^}]*width: \$\{paperWidthMm\}mm[^}]*max-width: 100%/s)
assert.match(transformed, /overflow-wrap: anywhere/)
assert.match(transformed, /table[^}]*max-width: 100%/s)
assert.doesNotMatch(transformed, /page-break|break-before|break-after|break-inside/)
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
cd frontend
node --test tests/pos-print-transform.test.mjs
```

Expected: FAIL because border-box/wrapping safeguards are absent.

- [ ] **Step 3: Implement minimal print CSS containment**

Update the transformed receipt CSS so it injects these semantics:

```css
*, *::before, *::after { box-sizing: border-box; }
html, body { width: ${paperWidthMm}mm; max-width: ${paperWidthMm}mm; overflow-x: hidden; }
.receipt {
  width: ${paperWidthMm}mm;
  max-width: 100%;
  padding: 2mm ${horizontalPaddingMm}mm 3mm;
  overflow: hidden;
}
.receipt table, .receipt img, .receipt svg { max-width: 100%; }
.receipt td, .receipt th, .receipt span, .receipt p { overflow-wrap: anywhere; word-break: break-word; min-width: 0; }
```

Keep `@page { margin: 0; }` and do not add pagination rules.

- [ ] **Step 4: Re-run print tests and syntax check**

```bash
node --check scripts/pos-print-transform.mjs
node --test tests/pos-print-transform.test.mjs
```

Expected: PASS.

- [ ] **Step 5: Commit Task 1**

Commit message:

```text
fix(pos): contain thermal receipts within roll width
```

---

### Task 2: Native POS offline store

**Files:**
- Create: `frontend/src/utils/posOfflineStore.js`
- Create: `frontend/tests/pos-offline-store.test.mjs`

**Interfaces:**
- Produces:
  - `normalizePosSearchText(value: unknown): string`
  - `searchCustomersInRows(rows: Array, query: string, limit?: number): Array`
  - `createOfflineOrderRecord(payload: object, id?: string): object`
  - `createPosOfflineStore(options?: { indexedDB?: IDBFactory, now?: Function }): object`
  - store methods: `savePosBootSnapshot`, `loadPosBootSnapshot`, `replaceCustomerCache`, `mergeCustomerCache`, `searchCachedCustomers`, `enqueueOfflineOrder`, `listPendingOfflineOrders`, `markOfflineOrderSynced`, `markOfflineOrderNeedsAttention`, `pendingOrderCount`.

- [ ] **Step 1: Write pure failing tests**

Cover Persian/Arabic normalization and mobile matching:

```js
assert.equal(normalizePosSearchText('  ياسر  '), 'یاسر')
assert.equal(normalizePosSearchText('۰۹۱۲ ۱۲۳ ۴۵۶۷'), '09121234567')
const rows = [{ key: 'c1', label: 'یاسر رضایی', mobile: '09121234567' }]
assert.equal(searchCustomersInRows(rows, 'ياسر').length, 1)
assert.equal(searchCustomersInRows(rows, '۱۲۳۴۵۶۷').length, 1)
```

Cover queue record identity/state:

```js
const record = createOfflineOrderRecord({ items: [{ item_name: 'A', qty: 1 }] }, 'pos-test-1')
assert.equal(record.id, 'pos-test-1')
assert.equal(record.status, 'pending')
assert.equal(record.payload.client_order_key, 'pos-test-1')
```

- [ ] **Step 2: Run the test and confirm RED**

```bash
cd frontend
node --test tests/pos-offline-store.test.mjs
```

Expected: module/function missing.

- [ ] **Step 3: Implement pure helpers first**

Implement digit normalization for Persian/Arabic numerals, `ي` -> `ی`, `ك` -> `ک`, whitespace normalization, and stable customer key generation.

- [ ] **Step 4: Add an IndexedDB adapter with safe fallback**

Database:

```js
const DB_NAME = 'restaurant-pos-offline-v1'
const DB_VERSION = 1
```

Stores:

```text
snapshots: keyPath "key"
customers: keyPath "key"
order_queue: keyPath "id"
```

The public store factory must return safe rejected/empty results when IndexedDB is absent rather than crashing Vue initialization.

- [ ] **Step 5: Test adapter-independent behavior and duplicate queue identity**

Use an injectable in-memory adapter in tests or exported pure queue merger; do not add `fake-indexeddb` dependency.

Expected assertions:

```js
assert.equal(mergeQueueRecords([record], [record]).length, 1)
assert.equal(next.status, 'needs_attention')
```

- [ ] **Step 6: Run all frontend tests**

```bash
npm test
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

```text
feat(pos): add native offline data store
```

---

### Task 3: Backend reliability API, idempotency field, and atomic quick edit

**Files:**
- Create: `restaurant/api_pos_reliability.py`
- Create: `restaurant/patches/v2_12/__init__.py`
- Create: `restaurant/patches/v2_12/ensure_pos_reliability_fields.py`
- Modify: `restaurant/patches.txt`
- Create: `restaurant/tests/test_api_pos_reliability.py`

**Interfaces:**
- Produces whitelisted endpoints:
  - `restaurant.api_pos_reliability.get_management_pos_boot_reliable(branch=None)`
  - `restaurant.api_pos_reliability.replay_offline_pos_order(payload=None)`
  - `restaurant.api_pos_reliability.update_pos_product_atomic(payload=None)`
- Adds Sales Order custom field `restaurant_pos_client_order_key` (`Data`, unique, read-only/no-copy preferred).

- [ ] **Step 1: Add failing backend helper tests**

Test pure/helper behavior without requiring DB where possible:

```python
def test_normalize_client_order_key():
    assert api_pos_reliability._normalize_client_order_key(' pos-abc ') == 'pos-abc'


def test_duplicate_key_returns_existing(monkeypatch):
    monkeypatch.setattr(api_pos_reliability, '_find_order_by_client_key', lambda key: 'SO-0001')
    result = api_pos_reliability._resolve_existing_client_order('pos-abc')
    assert result == 'SO-0001'
```

- [ ] **Step 2: Confirm RED with Python syntax/test runner available**

Preferred:

```bash
bench --site <site> run-tests --app restaurant --module restaurant.tests.test_api_pos_reliability
```

Fallback if Frappe runtime is unavailable:

```bash
python -m py_compile restaurant/api_pos_reliability.py
```

The test should initially fail because the module is absent.

- [ ] **Step 3: Add idempotency custom-field patch**

Patch helper creates field only if absent:

```python
{
    'doctype': 'Custom Field',
    'dt': 'Sales Order',
    'fieldname': 'restaurant_pos_client_order_key',
    'label': 'POS Client Order Key',
    'fieldtype': 'Data',
    'read_only': 1,
    'no_copy': 1,
    'unique': 1,
    'insert_after': 'restaurant_secondary_customer',
}
```

Register:

```text
restaurant.patches.v2_12.ensure_pos_reliability_fields
```

- [ ] **Step 4: Implement reliable POS boot supplement**

Call existing `restaurant.api.get_management_pos_boot(branch)` for canonical boot data, then query management-only unavailable items by reusing legacy private serialization helpers. Remove only the out-of-stock filter from a copied management filter; keep branch/disabled/menu constraints. Merge by stable item name so normal items are not duplicated.

Return the same payload shape with `items` containing unavailable entries and `out_of_stock: 1`.

- [ ] **Step 5: Implement idempotent replay endpoint**

Pseudo-flow:

```python
@frappe.whitelist()
def replay_offline_pos_order(payload=None):
    data = _parse_payload(payload)
    key = _normalize_client_order_key(data.get('client_order_key'))
    if not key:
        frappe.throw(_('Client order key is required.'))
    existing = _find_order_by_client_key(key)
    if existing:
        return {'status': 'existing', 'order': existing, 'client_order_key': key}
    order_result = legacy.create_pos_order(payload=data)
    order_name = _extract_order_name(order_result)
    if order_name:
        frappe.db.set_value('Sales Order', order_name, 'restaurant_pos_client_order_key', key, update_modified=False)
    return {'status': 'created', 'order': order_name, 'result': order_result, 'client_order_key': key}
```

Use the actual existing POS create function name found during implementation. The key lookup happens before creation and the field write is in the same request transaction.

- [ ] **Step 6: Implement atomic quick edit endpoint**

Validate only allowed fields. Update item settings and selling price in one request. If any operation raises, let Frappe roll back and return an error; do not report partial success. Return canonical product detail after successful mutation.

- [ ] **Step 7: Run Python syntax/tests**

```bash
python -m py_compile restaurant/api_pos_reliability.py restaurant/patches/v2_12/ensure_pos_reliability_fields.py
```

And Frappe tests when environment supports them.

- [ ] **Step 8: Commit Task 3**

```text
feat(pos): add reliable backend for offline replay and quick edit
```

---

### Task 4: POS page offline integration and queue sync

**Files:**
- Create: `frontend/src/utils/posReliabilityApi.js`
- Modify: `frontend/scripts/pos-print-transform.mjs`
- Create: `frontend/tests/pos-reliability-transform.test.mjs`

**Interfaces:**
- `posReliabilityApi.js` exports:
  - `getReliablePOSBoot({ branch })`
  - `replayOfflinePOSOrder(payload)`
  - `updatePOSProductAtomic(payload)`
- Transform imports `createPosOfflineStore` and reliability API functions into `ManagementPosPage.vue`.

- [ ] **Step 1: Write failing source-transform tests**

Use minimal source fixtures containing markers from the real POS page and assert transformed output contains:

```js
assert.match(out, /createPosOfflineStore/)
assert.match(out, /searchCachedCustomers/)
assert.match(out, /savePosBootSnapshot/)
assert.match(out, /loadPosBootSnapshot/)
assert.match(out, /replayOfflinePOSOrder/)
assert.match(out, /pendingOfflineOrderCount/)
assert.match(out, /ذخیره آفلاین شد/)
assert.match(out, /تسویه.*آنلاین|اتصال.*تسویه/s)
```

- [ ] **Step 2: Confirm RED**

```bash
node --test tests/pos-reliability-transform.test.mjs
```

- [ ] **Step 3: Add reliability API wrapper**

Implementation:

```js
import { callMethodByPath } from './api'

export const getReliablePOSBoot = ({ branch = '' } = {}) =>
  callMethodByPath('restaurant.api_pos_reliability.get_management_pos_boot_reliable', { branch })

export const replayOfflinePOSOrder = (payload = {}) =>
  callMethodByPath('restaurant.api_pos_reliability.replay_offline_pos_order', { payload })

export const updatePOSProductAtomic = (payload = {}) =>
  callMethodByPath('restaurant.api_pos_reliability.update_pos_product_atomic', { payload })
```

- [ ] **Step 4: Integrate cached boot fallback**

Transform `loadPOSBoot()` to use `getReliablePOSBoot` and persist successful payload. On connectivity failure, call `loadPosBootSnapshot(branch)` and feed the cached payload through the same state-application block. If no snapshot exists, retain a clear first-use offline error.

- [ ] **Step 5: Integrate local-first customer search**

On mount, hydrate `customerOptions` from cache. `loadCustomers(search)` first loads local matches and never clears them on network failure. Successful server results merge into cache and reactive options.

- [ ] **Step 6: Integrate offline plain-order queue**

At the beginning of `submitPOSOrder(shouldPay, ...)`:

```js
if (isOffline.value) {
  if (shouldPay) {
    error.value = 'پرداخت یا تسویه نیاز به اتصال اینترنت دارد.'
    return
  }
  const payload = buildCurrentOrderPayloadUsingExistingLogic()
  const queued = await posOfflineStore.enqueueOfflineOrder(payload)
  successMessage.value = 'سفارش ذخیره آفلاین شد و پس از اتصال همگام می‌شود.'
  pendingOfflineOrderCount.value = await posOfflineStore.pendingOrderCount()
  clear/reset only after queue write succeeds
  return
}
```

Reuse existing payload construction rather than duplicating price/cart calculations.

- [ ] **Step 7: Add reconnect/manual sync loop**

Process `pending` records sequentially with `replayOfflinePOSOrder(record.payload)`. On business validation error mark `needs_attention`; on transport error leave pending and stop current sync pass. Update count and banner state.

- [ ] **Step 8: Guard administrative quick edit while offline**

Opening cached values may remain possible, but save must return a connection-required message and not mutate local product state optimistically.

- [ ] **Step 9: Run frontend tests**

```bash
npm test
```

Expected: existing print tests + offline/transform tests PASS.

- [ ] **Step 10: Commit Task 4**

```text
feat(pos): integrate offline cache and order sync
```

---

### Task 5: Overlay stacking and POS quick-edit/unavailable UX

**Files:**
- Modify: `frontend/scripts/pos-print-transform.mjs`
- Modify: `frontend/tests/pos-reliability-transform.test.mjs`

**Interfaces:**
- Consumes reliable boot with unavailable products from Task 3.
- Produces deterministic CSS overlay scale, Teleported order detail, disabled sale actions for unavailable items, and atomic quick-edit call.

- [ ] **Step 1: Add failing overlay/unavailable source tests**

Assertions:

```js
assert.match(out, /--pos-z-operations:\s*12000/)
assert.match(out, /--pos-z-dialog:\s*14000/)
assert.match(out, /--pos-z-detail:\s*15000/)
assert.match(out, /<Teleport to="body">[\s\S]*orderDetailModal\.open/)
assert.match(out, /isProductUnavailable/)
assert.match(out, /updatePOSProductAtomic/)
```

- [ ] **Step 2: Confirm RED**

```bash
node --test tests/pos-reliability-transform.test.mjs
```

- [ ] **Step 3: Centralize POS overlay z-index variables**

Inject into POS root style:

```css
.pos-theme {
  --pos-z-floating: 11000;
  --pos-z-operations: 12000;
  --pos-z-dialog: 14000;
  --pos-z-detail: 15000;
  --pos-z-top: 16000;
}
```

Replace relevant backdrop z-index values with these variables. Teleport order-detail wrapper to body.

- [ ] **Step 4: Keep unavailable products visible but unsellable**

Add helper:

```js
function isProductUnavailable(item) {
  if (Number(item?.out_of_stock ?? item?.restaurant_out_of_stock ?? 0) === 1) return true
  const until = String(item?.out_of_stock_until || item?.restaurant_out_of_stock_until || '').trim()
  if (!until) return false
  const end = new Date(`${until}T23:59:59`)
  return Number.isFinite(end.getTime()) && end.getTime() >= Date.now()
}
```

Guard `incrementProduct` and barcode-add path so unavailable items cannot enter cart. Preserve quick-edit event access.

Transform product card markup/classes only as needed to expose an unavailable visual state and disabled add button semantics; do not remove the card.

- [ ] **Step 5: Replace two-call quick edit with atomic endpoint**

Instead of `Promise.all([setManagementProductPrice(), updateManagementProductSettings()])`, call:

```js
await updatePOSProductAtomic({
  item_name: quickEditForm.name,
  price_list_rate: Number(quickEditForm.price || 0),
  restaurant_short_desc: quickEditForm.restaurant_short_desc,
  restaurant_long_desc: quickEditForm.restaurant_long_desc,
  item_group: quickEditForm.item_group,
  restaurant_out_of_stock: quickEditForm.out_of_stock ? 1 : 0,
  restaurant_out_of_stock_until: quickEditForm.out_of_stock ? quickEditForm.out_of_stock_until : '',
})
```

Then reload reliable POS boot and keep item visible.

- [ ] **Step 6: Run tests**

```bash
npm test
```

- [ ] **Step 7: Commit Task 5**

```text
fix(pos): stabilize overlays and unavailable item editing
```

---

### Task 6: Service worker POS shell caching

**Files:**
- Modify: `frontend/public/sw.js`
- Create/Modify: `frontend/tests/pos-reliability-transform.test.mjs` or a dedicated `frontend/tests/pos-service-worker.test.mjs`

**Interfaces:**
- Produces an offline-capable management POS application shell after at least one successful visit/build asset cache.

- [ ] **Step 1: Add failing service-worker source test**

Read `public/sw.js` and assert:

```js
assert.match(source, /management\/pos|management-pos/)
assert.match(source, /restaurant-pos|veederakht-pwa-v4/)
assert.doesNotMatch(source, /request\.method[^\n]*POST[\s\S]*cache\.put/)
```

- [ ] **Step 2: Confirm RED**

```bash
node --test tests/pos-service-worker.test.mjs
```

- [ ] **Step 3: Bump cache version and cache POS navigation safely**

Use network-first navigation with cached request fallback. Add the actual management POS route used by the application to precache only if it can be fetched without authentication problems; otherwise cache successful POS navigation requests at runtime. Keep API POST untouched.

- [ ] **Step 4: Ensure built frontend static assets remain stale-while-revalidate**

Keep `/assets/restaurant/frontend/` handling and font/image support.

- [ ] **Step 5: Run frontend tests**

```bash
npm test
```

- [ ] **Step 6: Commit Task 6**

```text
feat(pos): cache POS application shell for offline use
```

---

### Task 7: Verification, PR refresh, and deployment notes

**Files:**
- Modify: PR #10 body if scope/test count changes.

**Interfaces:**
- Produces verified branch state ready for user deployment/merge review.

- [ ] **Step 1: Fresh syntax checks**

```bash
cd frontend
node --check scripts/pos-print-transform.mjs
node --check src/utils/posOfflineStore.js
node --check src/utils/posReliabilityApi.js
node --check vite.config.js
python -m py_compile ../restaurant/api_pos_reliability.py ../restaurant/patches/v2_12/ensure_pos_reliability_fields.py
```

- [ ] **Step 2: Fresh frontend test suite**

```bash
npm test
```

Expected: all tests PASS.

- [ ] **Step 3: Production frontend build when dependencies are available**

```bash
npm run build
```

If the environment cannot run a full build, report that limitation explicitly rather than claiming build verification.

- [ ] **Step 4: Backend/Frappe tests when site runtime is available**

```bash
bench --site <site> run-tests --app restaurant --module restaurant.tests.test_api_pos_reliability
```

If unavailable, retain Python syntax evidence and state the limitation.

- [ ] **Step 5: Compare branch and verify PR #10**

Check `fix/pos-thermal-printing` against `arena/019fffd4-restaurant`, confirm PR remains open/mergeable, and update PR body with new features, migrations, tests, and deployment requirements.

- [ ] **Step 6: Deployment instructions**

Server deployment must include:

```bash
bench --site <site> migrate
bench build --app restaurant
bench --site <site> clear-cache
bench --site <site> clear-website-cache
bench restart
```

A hard refresh/service-worker update may be required on POS terminals after deployment.
