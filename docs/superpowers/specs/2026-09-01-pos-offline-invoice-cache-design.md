# POS Offline Invoice Cache Design

## Goal

Allow a cashier to open and safely edit invoices that have previously been loaded on the same POS device, while offline. Keep the current day's most recent 200 invoices available locally.

## Scope

- Cache the current day's open-invoice list, capped at 200 invoices per device.
- Cache a full invoice snapshot whenever an invoice detail view is opened online.
- Serve the list and cached detail view while offline.
- Queue offline invoice edits and provisional settlement claims with idempotency keys.
- Apply a local optimistic projection for queued edits, keeping an explicit pending marker.

## Safety Rules

- An invoice not previously cached on this device is unavailable offline.
- A cached invoice is never treated as finally settled while offline.
- Settlement is stored as a provisional claim and must be accepted or reviewed by the server after reconnecting.
- Server validation failures such as changed price, stock, status, or a closed invoice become `needs_attention`; they are never discarded or overwritten.
- The daily list is retained only for its source date and is trimmed to the latest 200 invoices.

## Data Flow

1. Online list/detail reads update IndexedDB snapshots.
2. Offline list/detail reads use those snapshots and show their cached/pending state.
3. Offline edits enqueue `invoice_edit` mutations. Provisional settlements enqueue `invoice_settlement_claim` mutations.
4. On reconnect, normal order replay completes first, then mutations replay FIFO through the idempotent mutation API.
5. A successful replay refreshes the invoice cache; a conflict remains visible for review.

## Server Boundary

`invoice_edit` delegates to the existing authorized order-update path. `invoice_settlement_claim` never creates a final accounting record by itself; it becomes a server-side review record until a connected cashier confirms it.

## Verification

- Unit tests cover daily 200-item trimming, offline detail fallback, queued invoice edit, and provisional settlement review.
- Frontend test suite and production build pass.
- Python reliability tests cover supported mutation validation and replay dispatch.
