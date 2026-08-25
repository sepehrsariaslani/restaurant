---
name: Hero cover variant pattern
description: The 'cover' hero_section_variant replaces both header and hero using SiteHeaderHero
---

## Rule
When `hero_section_variant === 'cover'`, `RestaurantLandingPage.vue` should:
1. Hide `PublicHeader` (use `v-if="siteComponents.hero_section_variant !== 'cover'"`)
2. Show `SiteHeaderHero` (which includes its own navbar + full-screen background image)
3. Skip all other hero sections (fullscreen, banner) using `v-else-if`

**Why:** `SiteHeaderHero` has a built-in navigation bar. Showing PublicHeader alongside it creates duplicate navbars.

**How to apply:** When adding new hero variants that include built-in navbars, apply the same pattern.
