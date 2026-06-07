---
name: MenuItemCard variants
description: Three card styles for product cards, all using CSS theme variables
---

## Variants
- `classic` — white/cream card, contain image, price badge top-left, category+title+desc, footer row with tags+link+add button
- `dark` — primary color background (`var(--accent-green)`), cover image top, gradient overlay, white text
- `navy` — darkened primary (via `::before` overlay with `rgba(0,0,0,0.38)`), plate image centered, rating, price, arrow button

## Theme compliance
All variants use `var(--accent-green)` as primary color. The navy variant darkens it via a semi-transparent black overlay on `::before`.

**Why:** Colors must respond to user theme changes in the management settings.
