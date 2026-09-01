# POS Offline Invoice Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep up to 200 current-day invoice snapshots on each POS device and queue safe offline invoice edits and provisional settlements.

**Architecture:** Extend the existing IndexedDB POS context with date-scoped invoice list/detail snapshots. Reuse `mutation_queue` and `replay_offline_pos_mutation` for idempotent edits and review-only settlement claims; transformed POS code reads the local projection when offline.

**Tech Stack:** Vue 3, IndexedDB, Node `node:test`, Frappe/ERPNext.

## Global Constraints

- Keep only the 200 newest invoices for the active calendar date on each device.
- Never treat an offline settlement as final before server acceptance.
- Preserve conflicts as `needs_attention`; do not overwrite server state.

---

### Task 1: Date-scoped invoice snapshot store

**Files:** `frontend/src/utils/posOfflineStore.js`, `frontend/tests/pos-offline-store.test.mjs`

- [ ] Write a failing test for `trimDailyInvoiceSnapshots(rows, date, 200)` retaining the newest 200 same-day rows.
- [ ] Run `cd frontend && node --test tests/pos-offline-store.test.mjs` and confirm failure.
- [ ] Implement date-scoped invoice list/detail snapshot helpers in IndexedDB and export the trimming helper.
- [ ] Re-run the focused test and commit `ویژگی: کش روزانه فاکتورهای آفلاین POS`.

### Task 2: Invoice mutation replay contract

**Files:** `restaurant/api_pos_reliability.py`, `restaurant/tests/test_api_pos_reliability.py`

- [ ] Write failing tests for `invoice_edit` normalization and `invoice_settlement_claim` review status.
- [ ] Run `python3 -m unittest restaurant.tests.test_api_pos_reliability` and confirm failure.
- [ ] Dispatch edits through the existing authorized POS update path; record settlement claims as review-only mutations.
- [ ] Re-run the Python tests and commit `ویژگی: بازپخش امن ویرایش فاکتور آفلاین`.

### Task 3: POS offline list, detail, edit, and settlement wiring

**Files:** `frontend/scripts/pos-reliability-transform.mjs`, `frontend/tests/pos-reliability-transform.test.mjs`, `restaurant/public/frontend/assets/index.js`, `restaurant/public/frontend/assets/index.css`

- [ ] Write a failing transform test for cached invoice list/detail fallback and queued edit/settlement calls.
- [ ] Run `cd frontend && node --test tests/pos-reliability-transform.test.mjs` and confirm failure.
- [ ] Cache online invoice reads, use snapshots offline, queue edit/settlement operations, and mark the local view provisional.
- [ ] Run focused tests, `npm test`, and `npm run build`; commit `ویژگی: ویرایش و تسویه موقت آفلاین فاکتور POS`.

### Task 4: Final verification

- [ ] Run `cd frontend && npm test` and `npm run build`.
- [ ] Run Python compile with a temporary bytecode cache and `python3 -m unittest restaurant.tests.test_api_pos_reliability`.
- [ ] Confirm `git diff --check` is empty and leave unrelated `restaurant/www/fonts/` unchanged.
