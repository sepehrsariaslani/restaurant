# Full POS Offline Mutations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Queue all non-server-final POS operations locally and replay them idempotently after connectivity returns.

**Architecture:** Add a durable `mutation_queue` beside the existing order queue. A generic sync engine replays mutations in order through one Frappe endpoint. POS applies an optimistic local projection and labels manual payments as provisional until the server accepts them.

**Tech Stack:** Vue 3, native IndexedDB, Node `node:test`, Frappe/ERPNext.

## Global Constraints

- No mutation is silently discarded, duplicated, or marked final before server acceptance.
- Manual cash/card payments print only a provisional receipt while offline.
- Price, stock, table and payment conflicts become `needs_attention`.
- No new frontend runtime dependency.

---

### Task 1: Durable mutation queue

**Files:** `frontend/src/utils/posOfflineStore.js`, `frontend/tests/pos-offline-store.test.mjs`

- [ ] Write tests for stable mutation key, FIFO order, retry metadata and attention status.
- [ ] Verify red with `cd frontend && node --test tests/pos-offline-store.test.mjs`.
- [ ] Add `enqueueOfflineMutation`, `listPendingOfflineMutations`, `markOfflineMutationSynced`, `markOfflineMutationPending`, and `markOfflineMutationNeedsAttention`; create IndexedDB `mutation_queue` in a version upgrade.
- [ ] Verify green and commit `ویژگی: افزودن صف عملیات آفلاین POS`.

### Task 2: Mutation replay API

**Files:** `restaurant/api_pos_reliability.py`, `restaurant/tests/test_api_pos_reliability.py`, `restaurant/patches/v2_14/ensure_pos_offline_mutations.py`, `restaurant/patches.txt`

- [ ] Write tests for normalized mutation keys and replay deduplication.
- [ ] Verify red with `python3 -m unittest restaurant.tests.test_api_pos_reliability`.
- [ ] Add `replay_offline_pos_mutation(payload)` and an idempotency log DocType/custom field strategy; dispatch table create/update/customer/move/merge/close and manual-payment mutations in a transaction.
- [ ] Return `created`/`existing` only for accepted mutations and return validation conflicts to the client.
- [ ] Run lightweight tests and commit `ویژگی: API همگام‌سازی عملیات آفلاین POS`.

### Task 3: Generic mutation sync engine

**Files:** `frontend/src/utils/offlineSyncEngine.js`, `frontend/tests/offline-sync-engine.test.mjs`, `frontend/src/utils/posReliabilityApi.js`

- [ ] Add red tests that mutations replay FIFO after base orders and classify transport versus conflict errors.
- [ ] Add `replayOfflinePOSMutation` wrapper and `syncPendingMutations()` engine method with a single shared in-flight promise.
- [ ] Verify tests and commit `ویژگی: همگام‌سازی ترتیبی عملیات آفلاین POS`.

### Task 4: POS optimistic offline behavior

**Files:** `frontend/scripts/pos-reliability-transform.mjs`, `frontend/tests/pos-reliability-transform.test.mjs`, `restaurant/public/frontend/assets/index.js`, `restaurant/public/frontend/assets/index.css`

- [ ] Add source tests for offline table-add, item quantity, assign customer, move/merge/close and provisional manual payment queueing.
- [ ] In every eligible action, enqueue a mutation when offline, update cached local context, and show a provisional message rather than calling the network.
- [ ] Suppress customer fetch logs on known network transitions; keep cached search options visible.
- [ ] Add pending/attention mutation counts to status UI and run sync after reconnect.
- [ ] Run `cd frontend && npm test && npm run build`; commit `ویژگی: تکمیل فرایند آفلاین POS`.

### Task 5: Verification and deployment

- [ ] Run frontend tests/build and Python compilation/tests.
- [ ] Confirm migration registration and commit only scoped artifacts.
- [ ] Deploy using `bench --site dehati.ir migrate`, `bench build --app restaurant`, cache clears and restart.
