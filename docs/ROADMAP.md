# Development Roadmap

## ✅ Phase 1 — Delivered (this build)
- Double-entry accounting engine (post / reverse, atomic, balanced-only) + tests
- Chart of Accounts (tree, system accounts, seeded standard CoA with Arabic names)
- Journal entries (draft → post → reverse)
- Sales (quotation, invoice, payment, credit note) with VAT auto-posting + PDF
- Purchases (invoice, payment, debit note) with VAT
- Cash & Banks (deposit / withdrawal / transfer)
- Expenses with approval workflow (draft→pending→approved→posted)
- Customers / Suppliers with document-based sub-ledgers & statements
- Reports: trial balance, income statement, balance sheet, general ledger, cash flow (+ Excel/PDF)
- RBAC (4 seeded roles, granular model permissions), JWT auth + refresh
- Audit log (append-only via signals), fiscal-period locking
- Dashboard KPIs
- React/TS/Tailwind SPA (RTL/LTR), Docker Compose

## 🔜 Phase 2 — Hardening & depth
- DB triggers enforcing posted-entry immutability + balance at the database layer
- Invoice ↔ payment allocation (apply receipts to specific invoices, aging buckets)
- Bank reconciliation UI (clear lines against statements)
- Inventory valuation (FIFO / weighted average) feeding COGS
- Recurring journals, multi-currency, budgets
- Per-report PDF/Excel for every statement; scheduled email reports
- Soft-delete + change-diff capture in audit log
- Full test coverage across business modules; CI pipeline

## 🔭 Phase 3 — Scale & ops
- Background jobs (Celery) for heavy reports & exports
- Read replicas / materialized views for large GLs
- Sentry error tracking, structured JSON logging, metrics
- Automated nightly PG backups + point-in-time recovery (WAL archiving)
- E-invoicing / tax-authority integration (e.g. ZATCA) where required
