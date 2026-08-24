# POS Background Operations Completion Note

Date: 2026-08-24
Branch: `feat/pos-background-operations`
Base: `fix/pos-thermal-printing`

This bounded follow-up keeps Sales Order creation on the cashier request path and moves Sales Invoice, Payment Entry, production, stock, and delivery work to Frappe background workers. It also makes POS boot fail-safe when optional unavailable-item enrichment fails, removes stock availability controls from the Quick Edit sidebar, and makes cached product availability expiry-aware.

Deployment still requires the existing reliability migration from the parent branch plus a frontend rebuild and worker restart.
