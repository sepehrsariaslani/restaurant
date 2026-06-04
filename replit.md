# Restaurant & Coffee Shop Management System

A restaurant and coffee shop management system built for the Iranian market, featuring a Vue.js 3 frontend and a Frappe Framework backend.

## Tech Stack

- **Frontend**: Vue.js 3 + Vite (served on port 5000 in dev)
- **Backend**: Frappe Framework (Python) — requires a separate Frappe/bench environment
- **Local Hardware Node**: FastAPI app for POS hardware integration (optional, runs locally at restaurant)
- **Database**: MariaDB (managed by Frappe bench)

## Project Structure

- `frontend/` — Vue.js 3 SPA (Vite, Pinia, Persian calendar support)
- `restaurant/` — Frappe app (doctypes, API, scheduled tasks, Jinja templates)
- `restaurant/local_hardware_node/` — Standalone FastAPI app for on-premise hardware

## Running on Replit

The **frontend dev server** runs automatically via the `Start application` workflow:
```bash
cd frontend && npm run dev
```
This starts Vite on port 5000. The frontend proxies API calls to `http://localhost:8000` (a Frappe backend), which is not included in this Replit environment. To use the full backend, you need a running Frappe bench instance.

## Key Notes

- The app is fully localized for Persian/Farsi (Jalali calendar, RTL UI)
- SnappFood integration token is stored in Frappe's `Restaurant Web Settings` doctype
- Authentication is handled by Frappe's native session system (cookies + CSRF)

## User Preferences

- Preserve the existing codebase structure; do not rewrite from scratch
