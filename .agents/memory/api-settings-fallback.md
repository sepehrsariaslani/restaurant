---
name: API settings fallback
description: getManagementSiteSettings never throws — returns empty defaults when both API and localStorage are unavailable
---

When the Frappe backend is unavailable (Replit environment), `getManagementSiteSettings` catches the API error, tries localStorage, and if that also fails returns `{ ...DEFAULT_SITE_SETTINGS }` (empty object with web_settings, hero_slides, about_sections, faq_items). `setManagementSiteSettings` also never throws — it silently saves to localStorage when the API call fails.

**Why:** The backend doesn't run on Replit. Throwing caused the management settings page to show an error and refuse to load. Returning defaults lets the page initialize cleanly and the user can configure settings that persist in localStorage.

**How to apply:** Any new "get" API that wraps a Frappe backend call should follow this pattern: try API → try localStorage → return safe default.
