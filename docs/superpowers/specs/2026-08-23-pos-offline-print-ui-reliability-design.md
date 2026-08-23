# POS Offline, Printing, Overlay, and Quick-Edit Reliability Design

Date: 2026-08-23
Branch: `fix/pos-thermal-printing`
Repository: `sepehrsariaslani/restaurant`

## Goal

Make the management POS reliable in four areas without changing the existing product workflow more than necessary:

1. Thermal receipt output must stay inside the physical roll width for both 58mm and 80mm printers and remain continuous-roll friendly with no page-break behavior.
2. POS must remain useful when internet connectivity is lost, including customer search and access to the most recently synced products/categories/config needed for selling.
3. POS overlays/modals must always render above the operations panel and other application chrome with deterministic z-index behavior.
4. Product quick edit and out-of-stock controls from the POS must behave consistently, including being able to mark an item unavailable and later make it available again from the same POS interface.

## Current Problems and Root Causes

### Thermal receipt overflow

The transformed receipt CSS currently sets the receipt element width to the full configured paper width and also adds horizontal padding. Without `box-sizing: border-box`, the rendered outer width becomes larger than the selected roll width. Long strings/table content can also expand child elements beyond the intended width.

### Offline behavior is only partial

The POS currently tracks `navigator.onLine` and shows an offline banner, but customer loading still calls the server directly. The existing service worker caches GET requests, while key management POS APIs are called through POST requests. There is no persistent POS data store containing customers, POS boot data, or an offline order queue.

### Overlay stacking is inconsistent

The page uses several independent z-index values. Some UI surfaces are teleported to `body`, while the order-detail overlay is still rendered inside the POS component tree. This allows stacking contexts from parent elements/operations overlay to interfere with order detail and other dialogs.

### Out-of-stock edit loop is incomplete

Quick edit writes `restaurant_out_of_stock`, but POS boot uses core item filters that exclude items marked out of stock. Once an item is made unavailable, it may disappear from the POS product list and therefore cannot reliably be re-opened from the same POS page to mark it available again.

## Design Principles

- No new frontend runtime dependency for offline storage.
- Use browser-native IndexedDB for POS data because customer/product data and queued orders can exceed practical localStorage use.
- Keep service worker responsibilities focused on application shell/assets and safe GET caching. Business data persistence belongs in the POS offline store.
- Never silently queue administrative mutations such as price changes or out-of-stock edits while offline; these require live server confirmation to avoid management conflicts.
- Offline order creation may be queued only with an idempotency key and explicit sync state.
- Existing online behavior remains the primary path; offline data is fallback-first and refresh-on-success.
- Thermal printing stays continuous roll, with no page-break declarations introduced.

## Architecture

### 1. POS Offline Store

Create a small browser-native module, for example:

`frontend/src/utils/posOfflineStore.js`

IndexedDB database name:

`restaurant-pos-offline-v1`

Object stores:

- `snapshots`
  - `pos_boot` keyed by branch/device context
  - metadata: `updated_at`, schema version
- `customers`
  - keyed by a normalized customer key
  - indexed/searchable in memory after read
  - fields required by POS customer dropdown: name/label, mobile, customer id/name, order count, total sales, timestamps
- `order_queue`
  - queued offline orders only
  - key: generated UUID/idempotency key
  - payload, created time, status, retry count, last error

The module exposes narrow functions rather than leaking IndexedDB details into the POS page:

- `savePosBootSnapshot(branch, payload)`
- `loadPosBootSnapshot(branch)`
- `replaceCustomerCache(customers)` / `mergeCustomerCache(customers)`
- `searchCachedCustomers(query, limit)`
- `enqueueOfflineOrder(record)`
- `listPendingOfflineOrders()`
- `markOfflineOrderSynced(id)`
- `markOfflineOrderFailed(id, error)`
- optional cache version/clear helpers

All APIs must safely no-op/fallback if IndexedDB is unavailable.

### 2. POS Boot Offline Fallback

`loadPOSBoot()` remains network-first while online:

1. Call server.
2. On success, populate existing reactive POS state.
3. Persist a sanitized boot snapshot to IndexedDB.
4. Refresh customer cache separately.

If the request fails due to connectivity or the browser is offline:

1. Load the latest boot snapshot for the current branch.
2. Populate the same existing state mapping used by the online response.
3. Show an offline/fallback notice that includes cache freshness.
4. Do not treat cached fallback as a normal server success for write operations.

The cached snapshot must include enough data for browsing/searching products, categories, print/profile display settings required for local POS use, and other non-sensitive read-only data already exposed to the client. It must not invent server-only values.

### 3. Customer Search Offline

Customer search becomes local-first with online refresh:

- On POS load, read cached customers and show them immediately.
- When the user types, filter the local cache instantly by normalized name/mobile/customer identifier.
- If online, debounce a server search and merge returned rows into the local cache and current dropdown.
- If offline or the server call fails, keep local results instead of clearing `customerOptions`.
- A successful broad/default customer fetch replaces or refreshes the local customer cache.
- Newly created customers are added to the cache after a successful online create.

Normalization must handle Persian/Arabic character variants where practical and strip whitespace from mobile searches. The existing `PosProductPanel` filtering behavior remains compatible.

### 4. Offline Order Queue

Offline order submission is allowed only for order creation paths that can be safely replayed.

Each queued order gets a client-generated idempotency key. The backend order creation API must accept/store/check this key before creating a new Sales Order so retrying the same queued record cannot duplicate an order.

When offline:

- Validate the cart and required local fields using the same client validation as online.
- Save the full request payload to `order_queue` with the idempotency key.
- Mark the ticket as locally queued and present a clear success state such as “ذخیره آفلاین شد”.
- Do not claim server-side payment/settlement succeeded while offline.
- Card verification, credit validation, server settlement, stock mutation, and other server-dependent operations remain unavailable offline unless their current logic explicitly supports deferred processing.

When connectivity returns:

- A sync action processes pending records sequentially.
- Each successful API response marks/removes the queued record.
- Transient failures remain pending with retry metadata.
- Validation/business-rule failures become “needs attention” and are not retried in a tight loop.
- The existing reconnect reminder can be upgraded to expose pending queue count and a Sync action.

Automatic sync may run on reconnect, but the UI must still expose status and a manual retry entry point.

### 5. Service Worker / App Shell

Upgrade the service worker cache version and include the management POS shell route(s) and built frontend assets needed to reopen POS offline after at least one successful online visit.

Rules:

- Navigation: network-first with cached navigation fallback when available, then the generic offline page.
- Static frontend assets: stale-while-revalidate or cache-first where safe.
- API POST requests are not intercepted as a fake cache layer.
- Business data continues to come from IndexedDB fallback in the application.

This avoids mixing HTTP cache semantics with mutable POS business data.

### 6. Thermal Print Layout Fix

Update the print transform so the isolated receipt document uses:

- `box-sizing: border-box` globally for receipt content.
- `html, body` and `.receipt` fixed/max width equal to the selected 58mm/80mm width.
- Padding included inside the width.
- `max-width: 100%` for tables/rows/media.
- `overflow-wrap: anywhere` / safe word breaking for long invoice codes, customer names, notes, references, and item names.
- Table cells and flex children with `min-width: 0` where needed.
- Images/logos constrained to receipt width.
- No `page-break-*`, `break-*` pagination rules.
- `@page { margin: 0; }` retained for thermal roll printing.

Tests must explicitly assert that padding does not increase the total physical width and that no page-break rule is generated.

### 7. Overlay and z-index System

Define semantic POS overlay levels instead of unrelated magic numbers. Example scale:

- base POS content: normal document flow
- floating controls/toasts: 10xxx
- operations overlay: 12000
- standard dialogs/drawers: 13000
- nested/action dialogs such as settlement/quick edit/BOM: 14000
- order detail / confirmation surfaces: 15000
- print target/editor or emergency top-level dialog: 16000

Exact numbers may differ, but they must be centralized as CSS custom properties or a clearly documented scale.

All full-screen POS dialogs that can be opened while another POS overlay is active should use `<Teleport to="body">`, including the order-detail modal. Backdrops must cover the full viewport and dialog click handling must stop propagation correctly.

Opening order detail from “عملیات POS” should either:

- close the operations sheet first and open order detail, or
- intentionally keep operations open underneath while order detail is above it.

Preferred behavior: keep underlying POS state intact but ensure the detail modal is always visually above the operations overlay. Escape/backdrop closes only the topmost relevant surface.

### 8. Product Quick Edit / Out-of-Stock

Backend POS boot must return items relevant to POS management even when marked `restaurant_out_of_stock = 1`.

Do not globally remove the existing public-menu out-of-stock filtering. Instead, adjust the management POS boot query specifically so unavailable items are included with their state flags.

Frontend behavior:

- Out-of-stock products remain visible in management POS.
- Their cards have an obvious unavailable state.
- Increment/add-to-cart controls are disabled/guarded for unavailable items.
- Quick-edit remains available.
- Saving quick edit updates price/settings online, reloads/reconciles the POS boot data, and preserves the card in the list.
- Clearing out-of-stock makes the item immediately sellable again after successful server response.
- If `out_of_stock_until` is used, UI and backend state remain consistent; expired dates must not create a permanent unavailable state accidentally.

Offline behavior for quick edit:

- Opening cached detail may be allowed only if sufficient local data exists.
- Save is disabled while offline with a clear message: management changes require connection.
- No offline queue for price/availability/admin settings.

### 9. Existing Edit Logic Validation

Audit quick-edit fields end-to-end:

- item identifier
- current price source
- short/long description
- item group
- out-of-stock toggle
- out-of-stock-until date

Verify request field names match backend expectations and that partial failure is not hidden. Because the current save uses `Promise.all` for price and product settings, a failure can produce partial server mutation. Replace with a safer backend transaction endpoint if practical, or at minimum execute with clear reconciliation/error handling so UI never reports full success after only one mutation succeeded.

Preferred implementation: add a dedicated atomic management POS quick-edit backend method that updates permitted fields and price in one server transaction, then returns the canonical updated item state.

## Error Handling

### Offline reads

If cache exists, render cached data and show an offline freshness indicator. If no cache exists, show a clear first-use message explaining that the POS needs one successful online load before offline use.

### Offline writes

Queued order creation shows local queue status. Administrative edits and settlement-dependent operations show a connection-required error instead of pretending to succeed.

### Sync conflicts

A queued order rejected by current server business rules is marked “needs attention” with the server message and remains inspectable. It is not silently discarded.

### Storage failure

If IndexedDB is unavailable/full/corrupt, fall back to current online behavior and surface a non-blocking warning. The POS must not crash.

## Security and Data Boundaries

- Cache only customer fields already delivered to the authenticated POS client and necessary for POS search/use.
- Do not cache CSRF tokens, session ids, passwords, payment secrets, or unnecessary sensitive fields in the POS offline database.
- Queued order payloads may contain customer/order information; data is device-local and must be clearable from browser storage.
- Backend idempotency key is generated client-side but validated/stored server-side per order creation workflow.
- Existing HTML escaping in receipt generation remains mandatory.

## Testing Strategy

### Unit/source-transform tests

Extend existing Node tests for:

- receipt border-box width behavior
- safe wrapping rules
- 58mm and 80mm width selection
- continuous-roll rule: no page-break declarations
- existing secondary-customer print coverage remains green

### Offline-store tests

Add isolated tests for:

- storing/loading POS boot snapshots
- customer merge/search normalization
- empty-cache behavior
- queue lifecycle: pending -> synced / needs-attention
- duplicate idempotency key handling on client store

Use a small injectable storage adapter or testable pure helper layer so Node tests do not require a real browser IndexedDB implementation unless already supported by the environment.

### POS behavior tests

Cover source/component behavior for:

- cached customers remain after server search failure
- offline customer search uses cache
- successful online search refreshes cache
- POS boot falls back to cache when network fails
- unavailable products remain visible but cannot be added
- quick edit is blocked offline
- order detail is teleported and assigned the top overlay level

### Backend tests

Where the repository has Frappe test infrastructure, cover:

- management POS boot includes out-of-stock items while public menu behavior remains unchanged
- atomic quick-edit updates permitted fields correctly
- idempotency key prevents duplicate offline-order replay
- replay of the same client order key returns/resolves the existing order rather than creating a second one

### Build verification

Before completion:

- run Node test suite
- run syntax checks for transform/config files
- run frontend production build if repository/dependencies are available in the execution environment
- if possible, run relevant backend/Frappe tests
- verify PR remains mergeable

## Rollout and Migration

- IndexedDB schema starts at version 1 and can be upgraded without deleting valid queues.
- Service-worker cache version is bumped so old cached shell files are cleaned up.
- No database migration is required unless a new backend custom field is needed for the POS client idempotency key. Prefer an explicit custom field on Sales Order, created through the project’s normal schema/patch mechanism, rather than runtime schema mutation on every request.
- Existing per-device print-width localStorage remains compatible.

## Acceptance Criteria

1. A 58mm or 80mm receipt never renders wider than its configured physical width because padding/content are contained inside that width.
2. No page-break/pagination behavior is added to thermal receipt CSS.
3. After at least one successful online POS load, reopening/using POS offline can display the cached product/category data required for order entry.
4. Customer name/mobile search works from the local cache while offline and does not clear previous results when the network fails.
5. Offline-created orders are queued with unique idempotency keys and can be synchronized without duplicate server orders.
6. Server-dependent settlement and administrative changes never falsely report success offline.
7. Clicking an invoice/order from POS operations always opens its detail modal visibly above the operations overlay.
8. POS overlays use a consistent documented z-index scale and full-screen dialogs use body teleport when necessary.
9. Marking an item out of stock keeps it visible in management POS, prevents selling it, and still allows quick edit so it can be restored to available.
10. Quick-edit saves are either atomic or have explicit reconciliation that prevents partial-success UI states.
11. Existing receipt features from the current branch, including 58/80mm selection and secondary customer printing, remain covered by tests.
12. Targeted tests pass before the branch is presented as complete.

## Non-Goals

- Silent direct hardware-printer selection from a normal browser; browser `window.print()` limitations remain.
- Full offline card payment authorization or online credit verification.
- Offline administrative pricing/inventory mutation queue.
- Replacing the entire current POS UI architecture.
- Adding a third-party PWA or IndexedDB library unless implementation evidence shows the native approach is insufficient.
