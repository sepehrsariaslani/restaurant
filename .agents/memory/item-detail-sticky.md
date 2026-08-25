---
name: Item detail page sticky bar
description: Product detail page hides global MobileBottomNav and renders its own sticky add-to-cart + wishlist bar
---

`App.vue` adds `v-if="page !== 'item'"` to `MobileBottomNav` so it does not render on the item/product detail page.

`ItemDetailPage.vue` has its own `.sticky-bottom-bar` (fixed, bottom 0, z-index 120) containing:
1. Wishlist toggle button (heart icon, stores slugs in `restaurant_wishlist_v1` localStorage)
2. Qty control (qty +/−)
3. Price + "افزودن به سبد" button

The page also includes: swipe-able image gallery (dots + prev/next arrows), customer reviews section (list + add-review form, using reviewsStore.js), star ratings summary.

**Why:** Users wanted: no bottom nav on item page, wishlist button, reviews, multi-image gallery.

**How to apply:** Keep `v-if="page !== 'item'"` on MobileBottomNav; do not add a separate nav inside ItemDetailPage.
