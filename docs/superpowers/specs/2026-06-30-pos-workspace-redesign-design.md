# POS Workspace Redesign

## Goal

Redesign the management POS workspace so the operator can always see the product grid and shopping cart at the same time on desktop, while moving the operational panels (`میزها`, `فاکتورهای باز`, `تراکنش‌های امروز`, `سفارش‌های اخیر`) into an on-demand overlay. The redesign should also improve visual consistency, reduce noise, and make the page feel more professional, minimal, and coordinated.

## Current State

- `ManagementPosPage.vue` renders the operational tabs in a fixed sidebar (`left-col`).
- `PosProductPanel.vue` renders the product search, customer search, scanner, category controls, and product grid.
- `PosCartPanel.vue` is only visible inside a cart drawer opened by the floating `🛒` button.
- Desktop hierarchy is inverted for cashier work:
  - operational data is permanently visible
  - cart is hidden behind a secondary action
  - the product workspace competes with multiple side surfaces
- Visual language is inconsistent:
  - floating action button and emoji-based controls lower the perceived quality
  - panel densities and spacing vary between product area, operational tabs, and cart
  - sticky action hierarchy is weak, especially around checkout

## User-Approved Direction

- Desktop:
  - keep cart visible as a fixed adjacent column beside products
  - move operational tabs into an overlay panel that opens over the page
- Mobile:
  - preserve drawer/sheet behavior for cart and secondary panels to avoid squeezing the viewport
- Visual direction:
  - minimal, warm, and professional
  - lighter surface hierarchy
  - consistent spacing, radius, border, and shadow system
  - quieter controls with one clear primary action family

## Design System

### Product fit

This is not a marketing page. It is a high-frequency cashier/admin workspace. The design should optimize scanning, quick item selection, quantity adjustment, table handling, and payment flow.

### Visual direction

- Mode: light-first
- Tone: warm neutral, restaurant-aligned, low-noise
- Style: minimal operations UI, not glassy, not decorative
- Surfaces:
  - background slightly tinted neutral
  - panels in soft white or warm off-white
  - borders light but explicit
  - shadows shallow and sparse

### Color roles

- Primary action: muted olive/brown from current brand family
- Secondary action: neutral surface with border
- Active state: soft filled tint plus stronger text
- Destructive: restrained red only where needed
- Text:
  - primary dark neutral
  - secondary muted neutral
  - monetary values slightly stronger than body text

### Component rhythm

- Border radius: 8px
- Dense but readable spacing based on 8px increments
- Control heights normalized across search, select, numeric, and action controls
- Sticky checkout area visually separated from editable cart content

## Proposed Layout

### Desktop structure

Use a three-part workspace:

1. Product workspace
   - occupies the main width
   - includes customer search, product search, scanner input, category rail, and product grid

2. Fixed cart column
   - always visible on desktop
   - placed adjacent to the product workspace inside the main POS shell
   - includes order mode, place selector, cart lines, financial controls, totals, and checkout actions

3. Operational overlay
   - hidden by default
   - opened by a dedicated `عملیات POS` trigger in the header area
   - contains the existing operational tabs:
     - `میزها`
     - `فاکتورهای باز`
     - `تراکنش‌های امروز`
     - `سفارش‌های اخیر`

### Overlay behavior

- Opens over the page with backdrop
- Anchors from the left side of the workspace
- Does not reflow the product or cart columns
- Can be dismissed by:
  - close button
  - clicking the backdrop
  - `Escape`
- Preserves the last selected tab between open/close cycles

### Mobile/tablet behavior

- Keep a compact product-first layout
- Cart remains drawer/sheet driven
- Operations remain overlay/drawer driven
- Avoid rendering three columns at medium and small breakpoints

## Component Changes

### `ManagementPosPage.vue`

- Replace fixed `left-col` rendering with:
  - a compact operations trigger in the top workspace controls
  - an `operationsOverlayOpen` state
  - an overlay container for the existing tab panels
- Embed `PosCartPanel` directly into the desktop `pos-shell`
- Restrict the old cart drawer and floating cart trigger to smaller breakpoints only
- Introduce clearer layout wrappers:
  - workspace header actions
  - operations overlay
  - product column
  - cart column

### `PosCartPanel.vue`

- Keep business behavior intact
- Restyle for persistent desktop presence:
  - quieter header
  - clearer line-item rows
  - normalized actions
  - better separation between editable cart content and checkout summary
- Remove emoji dependence from structural UI where possible
- Make footer actions feel anchored and stable

### `PosProductPanel.vue`

- Minor alignment cleanup only
- Normalize search/control row sizing and spacing
- Ensure the product grid aligns visually with the cart column

## Interaction Model

### Primary workflow

1. Search/select customer and products in the main workspace
2. Review and edit cart in the always-visible cart column
3. Use `عملیات POS` only when table/invoice/history context is needed
4. Complete submit/payment from the sticky cart footer

### Secondary workflow

- Table management and recent-order lookup happen inside the overlay
- Selecting a table or invoice updates the main cart/order state without navigating away

## Visual Improvements

### Professional cleanup

- Remove floating desktop cart affordance
- Replace structurally meaningful emoji affordances with text/icon controls where feasible
- Reduce the number of simultaneously loud visual elements
- Unify badge, tab, and button styling
- Make empty states and loading states match the rest of the system

### Hierarchy fixes

- Products are the dominant workspace
- Cart is the constant working memory
- Operations are secondary context

### Readability fixes

- Stable widths for price/total rows
- Better scanability of cart line controls
- Cleaner grouping of discount/service/tax fields
- Improved spacing around totals and final actions

## Accessibility

- Keep visible focus states on overlay trigger, tab buttons, cart actions, and checkout buttons
- Ensure overlay dismissal is keyboard accessible
- Maintain sufficient contrast in light theme
- Avoid icon-only critical actions without labels or tooltips
- Preserve meaningful hover/pressed/disabled states

## Error Handling

- Existing inline errors and success messages remain in place
- Overlay panel states (`loading`, `error`, `empty`) remain per-tab
- No business logic or API changes are required for this redesign

## Testing Strategy

### Regression checks

- Product add/remove/increment/decrement still works
- Cart line note/customization edit still works
- Table assignment, open invoice selection, and recent order modal flows still work
- Submit order and payment popup still work
- Print editor still opens and reads the current cart state

### Layout checks

- Desktop:
  - cart is always visible
  - operations overlay layers above page cleanly
  - product grid remains usable with the new cart column
- Tablet/mobile:
  - no horizontal overflow
  - cart drawer remains reachable
  - overlay does not trap content behind safe areas

## Scope Boundaries

Included:

- POS desktop layout restructure
- operational panel overlay
- cart persistence on desktop
- visual cleanup of POS workspace surfaces and controls

Not included:

- backend/API changes
- pricing engine changes
- order submission logic changes
- table/invoice business rule changes

## Implementation Notes

- Existing modified frontend files are already dirty in the worktree, so implementation must edit carefully and avoid reverting unrelated changes.
- The redesign should reuse current state and handlers rather than re-architecting POS state.
