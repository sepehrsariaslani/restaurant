---
name: Reviews store
description: localStorage-based review system for menu items; persists across sessions
---

Reviews are stored in `localStorage` under key `restaurant_item_reviews_v2`.

Structure: `{ [item_slug]: [{ id, author, rating, comment, date }] }`

API (from `frontend/src/utils/reviewsStore.js`):
- `getItemReviews(slug)` — returns array of reviews
- `addItemReview(slug, { author, rating, comment })` — appends a review (capped at 100 per item)
- `getAverageRating(slug)` — returns 0–5 float rounded to 1 decimal
- `getReviewCount(slug)` — returns number of reviews

**Why:** No Frappe backend available on Replit; localStorage is the persistence layer.

**How to apply:** Import from `@/utils/reviewsStore`. Used in `ItemDetailPage.vue` (full reviews section) and `MenuItemCard.vue` (shows average rating + count on classic variant cards).
