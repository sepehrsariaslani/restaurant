# Management Tables Redesign Design

Date: 2026-07-16
Target: `/management/tables`
Primary file today: `frontend/src/pages/management/ManagementTablesPage.vue`

## Goal

Redesign the management tables page from a record-editing screen into a modern live hall-control surface for restaurant operations, while preserving the existing management capability for tables, reservations, and active sessions.

The page should become useful for real-time floor management first, without losing data-editing access.

## Problem Statement

The current page is operationally correct but structurally weak:

- it behaves like three editable grids stacked together
- the most important real-time object, the table itself, is buried inside a data table
- there is no strong “floor view” for quick scanning of occupied, waiting, and empty tables
- reservations and sessions are visually equal to tables, even though their workflows differ
- inline editing inside dense tables increases noise and reduces clarity
- the page does not match the stronger design language now used in management product and POS screens

## Success Criteria

The redesign is successful when:

- a manager can understand hall status in under 5 seconds
- a cashier or floor manager can identify occupied, waiting, and empty tables without reading rows
- a user can open one table and immediately see customer, session, reservation, totals, and actions
- reservations and sessions are separated into their own operational views
- the page feels visually aligned with the newer management and POS surfaces
- dark mode remains usable and complete
- the redesign does not break existing table update, reservation update, or session update flows

## Scope

This redesign includes:

- new page structure
- new live summary header
- new tab system
- new floor-card layout for tables
- new detail drawer for table inspection and actions
- redesigned reservations view
- redesigned sessions view
- visual polish, responsive behavior, and dark mode alignment

This redesign does not include:

- backend workflow changes for table service logic
- new reservation creation workflow
- new analytics endpoints
- drag-and-drop floor map editing
- graphical restaurant map with arbitrary geometry

## Design Direction

Recommended direction: `Floor-first operational console`

Rationale:

- the page belongs to active restaurant operations, not only record maintenance
- table state is the primary object, so it should be the first visual layer
- reservations and sessions are supporting layers and should be separated into dedicated tabs
- this direction fits the existing POS improvements already made in the codebase

## Information Architecture

The page will have four vertical layers:

1. page header
2. live summary and global controls
3. primary tabs
4. tab-specific content

### Primary Tabs

The page will expose three tabs:

1. `نمای سالن`
2. `رزروها`
3. `سشن‌ها`

Default tab: `نمای سالن`

Reasoning:

- tables need a spatial or card-based operational view
- reservations need a list-management view
- sessions need a monitoring and audit-oriented view

## Screen Structure

### 1. Page Header

Keep the existing page scaffold title and subtitle, but tune subtitle copy to operational language.

Proposed subtitle:

`کنترل زنده سالن، رزروها و نشست‌های فعال`

### 2. Live Summary Strip

Top summary cards will remain, but become more actionable and visually clearer.

Metrics:

- کل میزها
- آزاد
- در انتظار
- اشغال
- رزروها
- سشن‌های فعال

Optional computed metrics if data is already available or cheap to derive:

- مجموع مبلغ سشن‌های فعال
- تعداد میزهای دارای مشتری ثبت‌شده

Controls next to summary:

- global search
- refresh button
- tab selector remains below, not mixed into summary cards

### 3. Tab Bar

Use the same family of tabs already used in management product detail:

- soft surface wrapper
- compact operational tabs
- count badge where helpful

Badge behavior:

- `نمای سالن`: total tables
- `رزروها`: reservations count
- `سشن‌ها`: sessions count

## Tab 1: Floor View (`نمای سالن`)

### Purpose

Enable immediate operational understanding of hall state.

### Layout

Two-column desktop layout:

- main area: responsive grid of table cards
- side area: detail drawer/panel for selected table

On smaller screens:

- table cards remain first
- detail becomes a slide-over or stacked panel

### Table Card Content

Each card shows:

- table label / number
- location
- status badge
- active session indicator
- customer name if exists
- guest count if exists
- active total amount if exists
- opened time if session exists

### Status Presentation

Status styles:

- `empty`: quiet neutral / soft green edge
- `waiting`: amber warning
- `occupied`: strong darker accent with active emphasis

Status must be readable in light and dark mode without relying on color alone.

### Card Actions

Each card supports:

- select/open details
- quick save status when edited
- jump to POS for the table
- clear table session when allowed

Secondary actions belong in the detail panel, not all on-card.

### Card Editing Strategy

Avoid the current table-grid inline editing model for the floor view.

Instead:

- allow only small direct edits on-card if they are operationally safe
- keep structural edits inside the detail panel

Safe quick edits:

- status
- active/inactive toggle if needed

Everything else:

- table number
- location
- notes
- manual active session reference

should live in the detail panel.

### Table Detail Panel

When one table is selected, open a persistent right-side detail panel on desktop.

Panel sections:

1. table identity
   - table number
   - location
   - status
   - active/inactive

2. customer and session snapshot
   - customer name
   - customer mobile
   - customer type
   - guest count
   - opened at
   - closed at if relevant
   - confirmed amount

3. linked reservation snapshot
   - customer
   - date
   - time
   - guest count
   - reservation status

4. actions
   - save table
   - clear session
   - go to POS
   - if practical, “open reservations tab filtered by this table”

5. notes
   - table notes
   - session note if applicable

### Empty State

If no table is selected:

- show a clean instructional placeholder in the detail panel
- do not show a blank card shell

## Tab 2: Reservations (`رزروها`)

### Purpose

Provide operational reservation management without mixing it with floor state.

### Layout

Single primary list/table with a compact filter row above it.

Filters:

- search
- status
- branch/location if present in data
- linked / unlinked to table

### Editing Model

Move away from heavy inline editing for every cell.

Recommended interaction:

- table rows stay compact and readable
- clicking a row opens an edit drawer or modal

Inside the reservation editor:

- customer name
- mobile
- branch
- linked table
- date
- time
- guest count
- status
- note

### Reservation Row Actions

- edit
- save changes
- jump to linked table
- optional confirm/cancel shortcuts if status model supports it

### Reservation Prioritization

Sort by:

1. upcoming reservations first
2. unresolved statuses before completed/cancelled

If backend already returns unsorted rows, sorting may happen client-side initially.

## Tab 3: Sessions (`سشن‌ها`)

### Purpose

Monitor currently active and historical sessions with financial and operational context.

### Layout

A data-first table remains the right choice here, but with better visual treatment.

### Columns

Keep or improve:

- table
- status
- opened_at
- closed_at
- total_confirmed_amount
- note

Add or display if already available in payload:

- customer name
- guest count

### Interactions

- row click opens session detail drawer
- quick status update remains possible
- clear action only where business logic permits
- deep link to POS or table view if available

### Visual Treatment

- monetary values in stronger emphasis
- status badges instead of raw text
- Persian date/time formatting consistently

## Shared Interaction Rules

### Search

A single global search input can remain at the page level, but tab-specific filtering logic should respect the current tab context.

Behavior:

- floor tab: search by table number, location, customer, mobile
- reservations tab: reservation fields
- sessions tab: table, session note, customer, status

### Refresh

One page-level refresh remains valid.

Behavior:

- reload all three datasets from `getManagementTables()`
- preserve current tab
- preserve selected table if it still exists

### Success and Error Messaging

Use page-level success/error messages for save operations, but do not make them dominate layout.

Preferred behavior:

- small inline banners below summary/tabs
- auto-clearing success messages is acceptable
- destructive errors remain persistent until next action

## Data Model and API Strategy

### Current API

Current page uses:

- `getManagementTables`
- `updateManagementTable`
- `updateManagementTableReservation`
- `updateManagementTableSession`

### Phase 1 Data Rule

Do not introduce new backend endpoints until the redesigned page proves a real payload gap.

Implementation should first map the new UI entirely on top of:

- `tables`
- `reservations`
- `sessions`
- `currency`

### Allowed Backend Extensions

If necessary after implementation starts, only small additive backend changes are allowed, such as:

- normalized linked table/session metadata
- customer summary fields already derivable from related records
- server-side sort or filter helpers only if client-side behavior becomes too noisy

## Componentization

To keep the page maintainable, break the redesign into focused components.

Recommended components:

1. `ManagementTablesSummaryStrip`
2. `ManagementTablesFloorGrid`
3. `ManagementTableCard`
4. `ManagementTableDetailPanel`
5. `ManagementReservationsPanel`
6. `ManagementReservationEditor`
7. `ManagementSessionsPanel`
8. `ManagementTableStatusBadge`

The page component should orchestrate state, data loading, selection, and save flows. Rendering details should move into focused child components.

## Responsive Behavior

### Desktop

- floor grid + persistent detail panel
- dense but readable cards

### Tablet

- floor grid remains
- detail panel can collapse below or open as slide-over

### Mobile

- tabs remain horizontally accessible
- cards go single-column
- detail opens as full-width drawer or modal sheet
- avoid wide data tables unless horizontally scrollable and justified

## Visual Design Rules

### Style

Operational SaaS / control-room style:

- restrained
- dense
- clean
- strongly structured

### UI Elements

- Lucide icons only
- no emoji
- card radius at or below current design system standard
- status badges with text + color
- buttons should separate primary operational actions from administrative edits

### Dark Mode

The redesign must ship with dark mode parity from the start.

Do not treat dark mode as polish later.

Specifically verify:

- card surfaces
- badges
- borders
- drawers
- inline fields
- text contrast

## Performance Expectations

The redesign should not make the page slower than the current implementation.

Rules:

- avoid rendering all heavy editors inline by default
- render detailed forms only when user selects a row/card
- preserve existing single-request loading pattern if practical
- use computed views for filtering and counts

## Error Handling

### Loading Errors

- show page-level error state
- keep previous data on screen if refresh fails after initial load

### Save Errors

- preserve the user’s in-progress edits where possible
- show the error inline at page level or inside the drawer/modal

### Missing Linked Data

If a table has no active session or reservation:

- render explicit empty states
- do not show placeholder technical values like `null`, blank timestamps, or raw IDs unless necessary

## Testing Strategy

### UI Verification

Verify:

- tab switching
- floor card selection
- detail panel updates
- reservation edit open/save
- session save flow
- dark mode rendering
- responsive behavior

### Behavioral Verification

Verify that existing flows still work:

- load tables payload
- update table
- update reservation
- update session
- refresh after save
- filter/search on each tab

### Regression Checks

Check:

- Persian number formatting
- money formatting
- date formatting
- selected table persistence after refresh
- no overlap or broken layouts at common desktop and tablet widths

## Implementation Phases

### Phase 1

- create tabs and summary structure
- build floor grid
- build table cards
- keep reservations/sessions functional

### Phase 2

- add detail panel
- move editing from inline-heavy approach into focused panel/editor flows
- improve row/card actions

### Phase 3

- dark mode parity
- responsive polish
- spacing, typography, status styling, interaction polish

## Risks

1. Existing payload may not contain enough linked context for an excellent detail panel.
   - Mitigation: start UI-first, add minimal backend fields only if necessary.

2. Keeping all legacy inline editing while adding new surfaces can create duplicated logic.
   - Mitigation: centralize save handlers in page state and push rendering into components.

3. Responsive behavior can degrade if drawer and data-table views are both forced into small screens.
   - Mitigation: use single-column cards and modal/drawer patterns on mobile.

## Final Recommendation

Implement the redesign as a floor-first operational console, not as a prettier version of the current editable tables.

This is the correct product move because the page’s primary job is live hall control. The data tables should support that job, not define it.
