# System Architecture

## Stack
- **Backend:** Django 5 + Django REST Framework, SimpleJWT, PostgreSQL
- **Frontend:** React + TypeScript + Vite + Tailwind (RTL/LTR, i18next)
- **Infra:** Docker Compose (db, redis, backend, frontend)

## The core rule
No business module writes to the ledger. Sales / Purchases / Expenses / Cash & Banks
build a `PostingEvent` and call `apps.accounting_engine.services.PostingService.post(...)`,
which is the only code that creates `JournalEntry` + `JournalLine` rows. It runs inside
`@transaction.atomic`, so a document and its ledger entry commit together or not at all.

```
React SPA ──JWT/REST──▶ DRF API
                         │ guards: JWTAuth → IsAuthenticated → HasModelPermission (granular RBAC)
                         │ cross-cutting: throttling, validation, audit middleware, exception handler
   business apps ────────┼────▶ accounting_engine (PostingService / numbering / period)
   (sales, purchases,    │            │  validates: balanced, period open, postable leaf accounts
    expenses, cashbanks) │            ▼
                         └────▶ PostgreSQL  (money = NUMERIC(19,4); CHECK constraints on lines)
```

## App map (Django apps = modules)
| App | Responsibility |
|-----|----------------|
| `common` | base models, money type, RBAC permission class, exception handler |
| `users_auth` | custom User, JWT login/refresh, roles (Groups), user mgmt |
| `company` | singleton CompanyProfile, TaxRate (VAT), FiscalPeriod (period lock) |
| `accounts_coa` | Chart of Accounts tree, SystemAccount key mapping |
| `accounting_engine` | **PostingService** (post/reverse), numbering, period checks |
| `journal` | JournalEntry / JournalLine, manual entries, post & reverse endpoints |
| `customers` / `suppliers` | partners + document-based sub-ledgers & statements |
| `sales` | quotations, invoices, customer payments, credit notes |
| `purchases` | purchase invoices, supplier payments, debit notes |
| `cashbanks` | cash/bank accounts, deposits, withdrawals, transfers |
| `expenses` | categories + expense approval workflow |
| `reports` | trial balance, P&L, balance sheet, GL, cash flow, statements, PDF/Excel |
| `audit` | current-user middleware + append-only AuditLog via signals |
| `dashboard` | KPI summary endpoint |

## Posting rules (auto-generated entries)
| Document | Debit | Credit |
|----------|-------|--------|
| Sales invoice | AR | Sales (+ VAT Payable) |
| Customer payment | Cash/Bank | AR |
| Credit note | Sales Returns (+ VAT Payable) | AR |
| Purchase invoice | Expense/Inventory (+ VAT Receivable) | AP |
| Supplier payment | AP | Cash/Bank |
| Debit note | AP | Purchase Returns (+ VAT Receivable) |
| Cash transfer | Destination cash/bank | Source cash/bank |
| Expense | Expense (+ VAT Receivable) | Cash/Bank or AP |
