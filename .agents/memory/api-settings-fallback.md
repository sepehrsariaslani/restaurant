---
name: API settings fallback + CSRF fix
description: getManagementSiteSettings never throws; setManagementSiteSettings falls back to localStorage; CSRF token is auto-refreshed on 400/403
---

## Settings fallback
When the Frappe backend is unavailable (Replit environment), `getManagementSiteSettings` catches the API error, tries localStorage, and if that also fails returns `{ ...DEFAULT_SITE_SETTINGS }` (empty object). `setManagementSiteSettings` also never throws — it silently saves to localStorage when the API call fails.

## CSRF token fix (critical)
In the Vite dev-server proxy setup, `window.csrf_token` and `window.frappe.csrf_token` are never set (Frappe only injects them in its own rendered HTML). This caused ALL POST requests to fail with 400 BAD REQUEST.

**Fix layers in `getCSRFToken()`:**
1. `window.csrf_token`
2. `window.frappe.csrf_token`
3. **Cookie fallback** — Frappe stores the CSRF token as a non-httpOnly cookie named `csrf_token`; read via `document.cookie.match(/csrf_token=([^;]+)/)`

**Auto-refresh on 400/403:**
`callMethodByPath` now catches 400 or 403, calls `refreshCsrfToken()` (GET `/api/method/frappe.utils.get_csrf_token`), and retries once with the fresh token.

**After login:**
`loginManagementUser` calls `refreshCsrfToken()` after successful login so all subsequent POST calls get a valid CSRF token immediately.

**Why:** Vite serves the HTML, not Frappe, so Frappe's JS boot never runs, leaving `window.csrf_token` empty.

**How to apply:** Any new POST API helpers should use `getCSRFToken()`. Do not bypass `callMethodByPath`. If seeing 400s on authenticated management routes, check CSRF token is resolving.
