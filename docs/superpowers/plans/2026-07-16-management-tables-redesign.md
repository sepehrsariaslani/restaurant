# Management Tables Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild `/management/tables` into a floor-first operational management page with live hall cards, reservations and sessions tabs, and a focused table detail panel.

**Architecture:** Keep the existing `getManagementTables` and update APIs, but move rendering logic out of the monolithic page into focused table-management UI components. Add one pure utility module for derived state, filtering, and formatting-oriented data shaping so key behavior can be tested without adding a new test framework.

**Tech Stack:** Vue 3, Vite, existing management UI components, Lucide Vue, plain Node assertion script for utility-level TDD, existing frontend build pipeline.

## Global Constraints

- Keep `/management/tables` centered on live hall control, not raw record editing.
- Default tab must be `نمای سالن`.
- Use Lucide icons only.
- Preserve current table, reservation, and session update flows.
- Do not add new backend endpoints unless a real payload gap blocks the UI.
- Dark mode parity is required in the same implementation pass.
- Numbers and dates shown to users must remain Persian-formatted where applicable.

---

### Task 1: Add testable table-management state utilities

**Files:**
- Create: `frontend/src/utils/managementTables.js`
- Create: `frontend/scripts/test-management-tables.mjs`

**Interfaces:**
- Consumes: raw `tables`, `reservations`, `sessions`, `search`, and selected identifiers from the management tables page
- Produces:
  - `buildTableLabelMap(tables)`
  - `buildTablesSummary({ tables, reservations, sessions })`
  - `filterTablesBySearch(tables, sessions, reservations, search)`
  - `filterReservationsBySearch(reservations, tables, search)`
  - `filterSessionsBySearch(sessions, tables, reservations, search)`
  - `sortReservations(rows)`
  - `buildFloorTableCards({ tables, sessions, reservations })`
  - `buildSelectedTableDetail({ table, session, reservation })`

- [ ] **Step 1: Write the failing utility test script**

```js
import assert from 'node:assert/strict'
import {
  buildTableLabelMap,
  buildTablesSummary,
  filterTablesBySearch,
  filterReservationsBySearch,
  filterSessionsBySearch,
  sortReservations,
  buildFloorTableCards,
  buildSelectedTableDetail,
} from '../src/utils/managementTables.js'

const tables = [
  { name: 'TBL-1', table_number: 'T01', location: 'سالن اصلی', status: 'occupied', is_active: 1, notes: '' },
  { name: 'TBL-2', table_number: 'T02', location: 'تراس', status: 'empty', is_active: 1, notes: '' },
]

const reservations = [
  { name: 'RES-2', customer_name: 'زهرا', mobile: '0912', branch: 'A', table: 'TBL-2', reservation_date: '2026-07-17', reservation_time: '20:00', guest_count: 2, status: 'pending', note: '' },
  { name: 'RES-1', customer_name: 'علی', mobile: '0935', branch: 'A', table: 'TBL-1', reservation_date: '2026-07-16', reservation_time: '18:00', guest_count: 4, status: 'confirmed', note: '' },
]

const sessions = [
  { name: 'SES-1', table: 'TBL-1', status: 'active', note: 'VIP', total_confirmed_amount: 3500000, opened_at: '2026-07-16 12:00:00', closed_at: '', customer_name: 'علی', customer_mobile: '0935', guest_count: 4 },
]

assert.deepEqual(buildTableLabelMap(tables), { 'TBL-1': 'T01', 'TBL-2': 'T02' })

assert.deepEqual(buildTablesSummary({ tables, reservations, sessions }), {
  totalTables: 2,
  emptyTables: 1,
  waitingTables: 0,
  occupiedTables: 1,
  reservations: 2,
  activeSessions: 1,
})

assert.equal(filterTablesBySearch(tables, sessions, reservations, 'علی').length, 1)
assert.equal(filterReservationsBySearch(reservations, tables, 'تراس').length, 1)
assert.equal(filterSessionsBySearch(sessions, tables, reservations, 'vip').length, 1)

assert.deepEqual(
  sortReservations(reservations).map((row) => row.name),
  ['RES-1', 'RES-2'],
)

const cards = buildFloorTableCards({ tables, sessions, reservations })
assert.equal(cards[0].name, 'TBL-1')
assert.equal(cards[0].session?.name, 'SES-1')
assert.equal(cards[0].reservation?.name, 'RES-1')

const detail = buildSelectedTableDetail({
  table: tables[0],
  session: sessions[0],
  reservation: reservations[1 - 1],
})
assert.equal(detail.table.table_number, 'T01')
assert.equal(detail.session.customer_name, 'علی')
assert.equal(detail.reservation.customer_name, 'علی')

console.log('management tables utility tests: PASS')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: FAIL with module export or file-not-found error

- [ ] **Step 3: Write minimal utility implementation**

Create the utility module with the exact exported function names above, implementing:
- normalized lowercase search matching
- summary counts
- reservation sorting by date/time ascending
- floor card mapping from table to active session and first linked reservation
- selected table detail packaging

- [ ] **Step 4: Run test to verify it passes**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: `management tables utility tests: PASS`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/managementTables.js frontend/scripts/test-management-tables.mjs
git commit -m "test: add management tables state utilities"
```

### Task 2: Build floor-first tables UI and detail panel

**Files:**
- Create: `frontend/src/components/management/tables/ManagementTableStatusBadge.vue`
- Create: `frontend/src/components/management/tables/ManagementTableCard.vue`
- Create: `frontend/src/components/management/tables/ManagementTableDetailPanel.vue`
- Modify: `frontend/src/pages/management/ManagementTablesPage.vue`

**Interfaces:**
- Consumes:
  - utilities from `frontend/src/utils/managementTables.js`
  - page-level save handlers from `ManagementTablesPage.vue`
- Produces:
  - floor cards with select/save/clear/POS actions
  - persistent selected table detail panel
  - tab state with default `floor`

- [ ] **Step 1: Write the failing utility test for floor card mapping used by the page**

Extend `frontend/scripts/test-management-tables.mjs` with:

```js
const floorCards = buildFloorTableCards({ tables, sessions, reservations })
assert.equal(floorCards[0].statusTone, 'occupied')
assert.equal(floorCards[1].statusTone, 'empty')
assert.equal(floorCards[0].customerName, 'علی')
assert.equal(floorCards[0].guestCount, 4)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: FAIL on missing floor-card derived fields

- [ ] **Step 3: Implement the minimal utility additions**

Update `buildFloorTableCards` so each card includes:
- `statusTone`
- `customerName`
- `customerMobile`
- `guestCount`
- `sessionTotal`
- `openedAt`

- [ ] **Step 4: Run test to verify it passes**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: PASS

- [ ] **Step 5: Replace monolithic tables view with tabbed floor-first layout**

In `ManagementTablesPage.vue`:
- add tabs: `floor`, `reservations`, `sessions`
- keep summary strip
- replace main first section with floor cards + selected detail panel
- keep existing save handlers and load flow
- preserve global search and refresh

In `ManagementTableStatusBadge.vue`:
- render readable status chips for `empty`, `waiting`, `occupied`, `active`, `closed`, fallback states

In `ManagementTableCard.vue`:
- show table number, status, location, session/customer snippets, amount, time
- emit:
  - `select`
  - `save`
  - `go-pos`
  - `clear-session`

In `ManagementTableDetailPanel.vue`:
- show table identity, session summary, reservation summary, editable fields, and action buttons

- [ ] **Step 6: Run frontend build to verify the new floor view compiles**

Run: `npm run build`
Expected: successful Vite build

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/management/ManagementTablesPage.vue frontend/src/components/management/tables/ManagementTableStatusBadge.vue frontend/src/components/management/tables/ManagementTableCard.vue frontend/src/components/management/tables/ManagementTableDetailPanel.vue frontend/src/utils/managementTables.js frontend/scripts/test-management-tables.mjs
git commit -m "feat: redesign management tables floor view"
```

### Task 3: Redesign reservations and sessions tabs with responsive polish

**Files:**
- Create: `frontend/src/components/management/tables/ManagementReservationsPanel.vue`
- Create: `frontend/src/components/management/tables/ManagementSessionsPanel.vue`
- Modify: `frontend/src/pages/management/ManagementTablesPage.vue`
- Modify: `frontend/src/utils/managementTables.js`

**Interfaces:**
- Consumes:
  - page-level save handlers
  - filtered reservation/session rows from utilities
- Produces:
  - compact reservations tab
  - improved sessions tab
  - consistent dark-mode and responsive layout behavior

- [ ] **Step 1: Write the failing utility test for reservation sorting and session search**

Extend `frontend/scripts/test-management-tables.mjs` with:

```js
assert.equal(sortReservations(reservations)[0].customer_name, 'علی')
assert.equal(filterSessionsBySearch(sessions, tables, reservations, 'T01')[0].name, 'SES-1')
```

- [ ] **Step 2: Run test to verify it fails if behavior is missing**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: FAIL only if utility behavior is incomplete

- [ ] **Step 3: Finalize reservations and sessions utility shaping**

Ensure utilities support:
- tab-specific search
- table label enrichment
- stable reservation sorting
- session-friendly display derivations without mutating raw API rows

- [ ] **Step 4: Run test to verify it passes**

Run: `node frontend/scripts/test-management-tables.mjs`
Expected: PASS

- [ ] **Step 5: Implement reservations and sessions components**

`ManagementReservationsPanel.vue`:
- compact filter row
- readable table with status badges
- row selection
- edit drawer/modal behavior or embedded focused edit pane

`ManagementSessionsPanel.vue`:
- data-first table
- improved money/time presentation
- status badges
- row-level action affordances

`ManagementTablesPage.vue`:
- mount both panels under tabs
- keep search synchronized with current tab
- preserve save flows and messages
- keep selected table after refresh when possible

- [ ] **Step 6: Run frontend build and utility test**

Run:
- `node frontend/scripts/test-management-tables.mjs`
- `npm run build`

Expected:
- utility test passes
- Vite build succeeds

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/management/tables/ManagementReservationsPanel.vue frontend/src/components/management/tables/ManagementSessionsPanel.vue frontend/src/pages/management/ManagementTablesPage.vue frontend/src/utils/managementTables.js frontend/scripts/test-management-tables.mjs
git commit -m "feat: complete management tables redesign"
```
