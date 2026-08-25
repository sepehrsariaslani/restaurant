---
name: Site Settings field patterns
description: How to add new fields to ManagementSiteSettingsPage.vue that persist correctly
---

## Rule
Any new field must be added in **4 places** in ManagementSiteSettingsPage.vue:
1. `webSettings` reactive object (initial default value)
2. `loadSettings()` function — explicit assignment with default fallback
3. Save payload object (inside `saveSettings()`)
4. UI section in the appropriate tab (components/content/branding)

**Why:** `writeReactive()` deletes all keys from the target before assigning from the server response. If the server doesn't have a key (e.g., first load), the reactive field becomes undefined after load. Explicit assignment in `loadSettings()` with a fallback prevents this.

**How to apply:** Every time you add a new site settings field, follow all 4 steps above.
