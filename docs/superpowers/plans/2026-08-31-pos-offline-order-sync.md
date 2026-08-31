# POS Offline Order Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** POS مدیریت را پس از یک بار استفادهٔ آنلاین، با cache محلی و صف قابل‌اعتماد برای سفارش‌های بدون پرداخت بیرون‌بر و ارسال آماده کند.

**Architecture:** IndexedDB مالک snapshot، مشتری‌ها و سفارش‌های unsent است. یک موتور مستقل، سفارش‌ها را به‌ترتیب به API idempotent Frappe بازپخش می‌کند. صفحهٔ Vue فقط وضعیت این دو لایه و فرآیند فعلی checkout را به هم متصل می‌کند.

**Tech Stack:** Vue 3، Vite، IndexedDB، Service Worker، Node `node:test`، Frappe/ERPNext.

## Global Constraints

- فقط سفارش بدون پرداختِ `takeaway` و `delivery` در حالت آفلاین صف می‌شود.
- سفارش میز، پرداخت، تسویه، بررسی اعتبار و تغییرات مدیریتی اتصال می‌خواهند.
- هر payload صف‌شده یک `client_order_key` ثابت دارد و replay از `restaurant.api_pos_reliability.replay_offline_pos_order` استفاده می‌کند.
- پاسخ `created` یا `existing` موفق است و فقط آن زمان رکورد حذف می‌شود.
- خطای کسب‌وکاری `needs_attention` می‌شود؛ خطای شبکه pending می‌ماند.
- هیچ وابستگی runtime جدیدی اضافه نمی‌شود و POST API در service worker cache نمی‌شود.

---

## File structure

- `frontend/src/utils/posOfflineStore.js`: عملیات پایدار IndexedDB و وضعیت صف.
- `frontend/src/utils/offlineSyncEngine.js`: بازپخش ترتیبی، بدون وابستگی Vue.
- `frontend/src/utils/api.js`: wrapperهای boot قابل‌اعتماد و replay.
- `frontend/src/pages/management/ManagementPosPage.vue`: fallback، checkout آفلاین و status UI.
- `frontend/tests/pos-offline-store.test.mjs`: تست state و metadata صف.
- `frontend/tests/offline-sync-engine.test.mjs`: ترتیب، retry و conflict.
- `frontend/tests/pos-offline-wiring.test.mjs`: قرارداد اتصال POS.
- `frontend/tests/service-worker-pos-offline.test.mjs`: قرارداد cache پوسته.
- `restaurant/tests/test_api_pos_reliability.py`: regression idempotency سمت سرور.

### Task 1: Complete persistent queue state

**Files:**
- Modify: `frontend/src/utils/posOfflineStore.js`
- Modify: `frontend/tests/pos-offline-store.test.mjs`

**Interfaces:**
- Produces `listOfflineOrders()`, `needsAttentionOrderCount()`, and `markOfflineOrderPending(id, error)`.
- Both state mutations return `false` if IndexedDB is unavailable.

- [ ] **Step 1: Write failing queue-state tests.**

```js
test('keeps a network failure pending and separates attention records', async () => {
  const store = createPosOfflineStore({ indexedDB: fakeIndexedDB, now: () => 200 })
  await store.enqueueOfflineOrder({ items: [{ item_slug: 'tea', qty: 1 }] }, 'pos-1')
  await store.markOfflineOrderPending('pos-1', 'network timeout')
  await store.markOfflineOrderNeedsAttention('pos-1', 'price changed')
  assert.equal(await store.pendingOrderCount(), 0)
  assert.equal(await store.needsAttentionOrderCount(), 1)
  assert.equal((await store.listOfflineOrders())[0].last_error, 'price changed')
})
```

- [ ] **Step 2: Verify red.**

Run: `cd frontend && node --test tests/pos-offline-store.test.mjs`

Expected: FAIL because the new store methods do not exist.

- [ ] **Step 3: Implement the smallest state-update helper.**

```js
async function markOfflineOrderPending(id, error = '') {
  return updateQueueRecord(id, (row) => ({
    ...row, status: 'pending',
    retry_count: Number(row.retry_count || 0) + 1,
    last_error: String(error || '').trim(),
    updated_at: Number(now()) || Date.now(),
  }))
}
async function needsAttentionOrderCount() {
  return (await listOfflineOrders()).filter((row) => row.status === 'needs_attention').length
}
```

Use one internal read-modify-write `updateQueueRecord` helper for pending and needs-attention transitions. Keep existing fallback behavior.

- [ ] **Step 4: Verify green.**

Run: `cd frontend && node --test tests/pos-offline-store.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/utils/posOfflineStore.js frontend/tests/pos-offline-store.test.mjs
git commit -m "ویژگی: تکمیل وضعیت صف سفارش آفلاین POS"
```

### Task 2: Add sequential replay engine

**Files:**
- Create: `frontend/src/utils/offlineSyncEngine.js`
- Create: `frontend/tests/offline-sync-engine.test.mjs`

**Interfaces:**
- Produces `createOfflineSyncEngine({ store, replayOrder, isOnline, isBusinessError })`.
- Its `syncPendingOrders()` returns `{ synced, pending, needsAttention, skipped }`; `isSyncing()` reports a shared in-flight run.

- [ ] **Step 1: Write failing engine tests.**

```js
test('replays oldest pending records once and accepts created or existing', async () => {
  const calls = []
  const engine = createOfflineSyncEngine({
    store: fakeStore([{ id: 'a', created_at: 1 }, { id: 'b', created_at: 2 }]),
    replayOrder: async (payload) => {
      calls.push(payload.client_order_key)
      return { status: payload.client_order_key === 'a' ? 'created' : 'existing' }
    },
    isOnline: () => true,
  })
  assert.deepEqual(await engine.syncPendingOrders(), { synced: 2, pending: 0, needsAttention: 0, skipped: false })
  assert.deepEqual(calls, ['a', 'b'])
})
test('preserves network failures but marks a 422 error as needs_attention', async () => {
  const store = fakeStore([{ id: 'a', created_at: 1 }])
  const network = createOfflineSyncEngine({ store, replayOrder: async () => { throw new TypeError('network failed') }, isOnline: () => true })
  assert.equal((await network.syncPendingOrders()).pending, 1)
  assert.deepEqual(store.pending, ['a'])
  const conflict = createOfflineSyncEngine({ store, replayOrder: async () => { throw { status: 422, message: 'price changed' } }, isOnline: () => true })
  assert.equal((await conflict.syncPendingOrders()).needsAttention, 1)
  assert.deepEqual(store.attention, ['a'])
})
test('shares an in-flight run so a second call cannot replay records twice', async () => {
  let release
  let calls = 0
  const engine = createOfflineSyncEngine({
    store: fakeStore([{ id: 'a', created_at: 1 }]),
    replayOrder: () => { calls += 1; return new Promise((resolve) => { release = () => resolve({ status: 'created' }) }) },
    isOnline: () => true,
  })
  const first = engine.syncPendingOrders()
  const second = engine.syncPendingOrders()
  release()
  await Promise.all([first, second])
  assert.equal(calls, 1)
})
```

- [ ] **Step 2: Verify red.**

Run: `cd frontend && node --test tests/offline-sync-engine.test.mjs`

Expected: FAIL because module is absent.

- [ ] **Step 3: Implement no-Vue engine.**

```js
export function createOfflineSyncEngine({ store, replayOrder, isOnline = () => true, isBusinessError = defaultBusinessError } = {}) {
  let inFlight = null
  async function syncPendingOrders() {
    if (inFlight) return inFlight
    inFlight = runSequentially()
    try { return await inFlight } finally { inFlight = null }
  }
  return { syncPendingOrders, isSyncing: () => Boolean(inFlight) }
}
```

Sort by `created_at`; overwrite each replay payload key with `row.id`. Mark only `created`/ `existing` synced. Classify HTTP 400/409/422 and Frappe validation errors as business errors, all other failures as pending.

- [ ] **Step 4: Verify green.**

Run: `cd frontend && node --test tests/offline-sync-engine.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/utils/offlineSyncEngine.js frontend/tests/offline-sync-engine.test.mjs
git commit -m "ویژگی: افزودن موتور همگام‌سازی ترتیبی POS"
```

### Task 3: Add frontend API contract

**Files:**
- Modify: `frontend/src/utils/api.js`
- Create: `frontend/tests/pos-offline-wiring.test.mjs`
- Modify: `restaurant/tests/test_api_pos_reliability.py` only if existing helpers lack coverage.

**Interfaces:**
- Produces `getManagementPOSBootReliable({ branch = '' } = {})`.
- Produces `replayOfflinePOSOrder(payload = {})`.

- [ ] **Step 1: Write failing wrapper-source tests.**

```js
assert.match(apiSource, /export function getManagementPOSBootReliable[\s\S]*get_management_pos_boot_reliable/)
assert.match(apiSource, /export function replayOfflinePOSOrder[\s\S]*replay_offline_pos_order/)
```

- [ ] **Step 2: Verify red.**

Run: `cd frontend && node --test tests/pos-offline-wiring.test.mjs`

Expected: FAIL because wrappers are absent.

- [ ] **Step 3: Add exact wrappers.**

```js
export function getManagementPOSBootReliable({ branch = '' } = {}) {
  return callRestaurantAPI('get_management_pos_boot_reliable', { branch })
}
export function replayOfflinePOSOrder(payload = {}) {
  return callRestaurantAPI('replay_offline_pos_order', { payload })
}
```

Keep the existing backend module and field patch: they already provide the server-side transactional idempotency path. Add Python checks only for uncovered key normalization/extraction helpers.

- [ ] **Step 4: Verify API tests.**

Run: `cd frontend && node --test tests/pos-offline-wiring.test.mjs`

Expected: PASS.

Run: `python -m unittest restaurant.tests.test_api_pos_reliability`

Expected: PASS.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/utils/api.js frontend/tests/pos-offline-wiring.test.mjs restaurant/tests/test_api_pos_reliability.py
git commit -m "ویژگی: اتصال کلاینت POS به API پایدار آفلاین"
```

### Task 4: Wire cache fallback and offline checkout into POS

**Files:**
- Modify: `frontend/src/pages/management/ManagementPosPage.vue`
- Modify: `frontend/tests/pos-offline-wiring.test.mjs`

**Interfaces:**
- Consumes the store, engine and Task 3 wrappers.
- Produces `applyPOSBootPayload(payload)`, `queueOfflinePOSOrder(payload)`, `syncPendingOfflineOrders()`, and reactive counts.

- [ ] **Step 1: Write failing source integration tests.**

```js
assert.match(posSource, /createPosOfflineStore/)
assert.match(posSource, /createOfflineSyncEngine/)
assert.match(posSource, /savePosBootSnapshot/)
assert.match(posSource, /loadPosBootSnapshot/)
assert.match(posSource, /replayOfflinePOSOrder/)
assert.match(posSource, /\['takeaway', 'delivery'\]\.includes\(form\.order_mode\)/)
assert.match(posSource, /پرداخت یا تسویه نیاز به اتصال اینترنت دارد/)
```

- [ ] **Step 2: Verify red.**

Run: `cd frontend && node --test tests/pos-offline-wiring.test.mjs`

Expected: FAIL until imports and guards are present.

- [ ] **Step 3: Add boot and customer-cache integration.**

Extract the current successful boot assignment into `applyPOSBootPayload(payload)`. Use reliable boot online, then call `savePosBootSnapshot(currentBranch, payload)`. On network failure call `loadPosBootSnapshot(currentBranch)`, apply its payload and set offline state. If no snapshot exists, display `برای استفاده آفلاین، ابتدا POS را یک بار با اینترنت باز کنید.`

Before each server customer lookup, show `searchCachedCustomers(search)`. Merge successful search results and replace the cache on the default initial list. Failed lookups must not erase cached options.

- [ ] **Step 4: Add guarded offline submit and auto-sync.**

Immediately after building the existing order payload:

```js
if (isOffline.value) {
  if (payNow) { error.value = 'پرداخت یا تسویه نیاز به اتصال اینترنت دارد.'; return }
  if (form.order_mode === 'dine_in') { error.value = 'سفارش میز نیاز به اتصال اینترنت دارد.'; return }
  if (!['takeaway', 'delivery'].includes(form.order_mode)) {
    error.value = 'ثبت آفلاین فقط برای بیرون‌بر و ارسال فعال است.'; return
  }
  await queueOfflinePOSOrder(payload)
  return
}
```

Queue only after IndexedDB persists; otherwise retain the cart. A persisted record resets the current ticket and says `سفارش ذخیره آفلاین شد؛ هنگام اتصال ارسال می‌شود.` Run `syncPendingOfflineOrders` after a successful boot and the existing online-event transition.

- [ ] **Step 5: Add operational status UI.**

Near the existing offline banner render an aria-live status containing online/offline, syncing, pending and needs-attention counts. Show a manual `همگام‌سازی` button only online with pending rows; disable it while syncing. Preserve attention records and display their last error without destructive actions.

- [ ] **Step 6: Verify all frontend tests.**

Run: `cd frontend && node --test tests/pos-offline-wiring.test.mjs && npm test`

Expected: PASS.

- [ ] **Step 7: Commit.**

```bash
git add frontend/src/pages/management/ManagementPosPage.vue frontend/tests/pos-offline-wiring.test.mjs
git commit -m "ویژگی: فعال‌سازی ثبت و همگام‌سازی آفلاین سفارش POS"
```

### Task 5: Verify service-worker boundary and release

**Files:**
- Modify: `frontend/tests/service-worker-pos-offline.test.mjs`
- Modify: `frontend/public/sw.js` only when the test proves a mismatch.

**Interfaces:**
- Successful GET navigation to `/management/pos` is runtime-cached.
- All non-GET requests remain untouched.

- [ ] **Step 1: Add the shell contract test.**

```js
assert.match(source, /isManagementPOSNavigation\(url\)/)
assert.match(source, /networkFirst\(request, \{ navigationAlias: isManagementPOSNavigation\(url\) \}\)/)
assert.match(source, /if \(request\.method !== ["']GET["']\) return/)
assert.doesNotMatch(source, /request\.method\s*===\s*["']POST["'][\s\S]*cache\.put/)
```

- [ ] **Step 2: Run it.**

Run: `cd frontend && node --test tests/service-worker-pos-offline.test.mjs`

Expected: PASS with the present v4 worker. If it fails, correct only the failed policy; never precache protected POS navigation or intercept POST.

- [ ] **Step 3: Run full release verification.**

Run: `cd frontend && npm test && npm run build`

Expected: PASS.

Run: `python -m py_compile restaurant/api_pos_reliability.py restaurant/patches/v2_12/ensure_pos_reliability_fields.py && python -m unittest restaurant.tests.test_api_pos_reliability`

Expected: PASS.

- [ ] **Step 4: Commit only changed files.**

```bash
git add frontend/public/sw.js frontend/tests/service-worker-pos-offline.test.mjs
git commit -m "آزمون: تثبیت قرارداد پوسته آفلاین POS"
```

### Task 6: Deployment handoff

**Files:** none.

- [ ] **Step 1: Inspect final commits and migration.**

Run: `git status --short && git log --oneline -6 && rg -n 'ensure_pos_reliability_fields' restaurant/patches.txt`

Expected: only scoped files changed and the reliability field patch is registered.

- [ ] **Step 2: Use the production procedure.**

```bash
bench --site dehati.ir migrate
bench build --app restaurant
bench --site dehati.ir clear-cache
bench --site dehati.ir clear-website-cache
bench restart
```

Refresh each POS terminal after deployment so the v4 service worker activates.
