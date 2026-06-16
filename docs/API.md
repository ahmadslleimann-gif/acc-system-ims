# API Reference (summary)

Base URL: `/api`. Auth: `Authorization: Bearer <access>`. Interactive docs: `/api/docs/`.

## Auth
| Method | Path | Notes |
|--------|------|-------|
| POST | `/auth/login/` | returns `access`, `refresh`, `user` |
| POST | `/auth/refresh/` | rotate access token |
| GET | `/auth/me/` | current user + roles + permissions |
| POST | `/auth/change-password/` | |
| CRUD | `/auth/users/` | admin only |
| GET | `/auth/roles/`, `/auth/permissions/` | |

## Company
- `GET/PUT /company/profile/` · CRUD `/company/tax-rates/` · CRUD `/company/fiscal-periods/`

## Chart of Accounts
- CRUD `/coa/accounts/` · `GET /coa/accounts/tree/` · `GET /coa/accounts/{id}/balance/`
- CRUD `/coa/system-accounts/`

## Journal
- CRUD `/journal/entries/` (create = DRAFT)
- `POST /journal/entries/{id}/post_entry/` · `POST /journal/entries/{id}/reverse/`

## Sales
- CRUD `/sales/quotations/`, `/sales/invoices/`, `/sales/payments/`, `/sales/credit-notes/`
- `POST /sales/invoices/{id}/post_invoice/` · `GET /sales/invoices/{id}/pdf/`
- `POST /sales/payments/{id}/post_payment/` · `POST /sales/credit-notes/{id}/post_note/`

## Purchases
- CRUD `/purchases/invoices/`, `/purchases/payments/`, `/purchases/debit-notes/`
- `POST /purchases/invoices/{id}/post_invoice/` etc.

## Cash & Banks
- CRUD `/cashbanks/accounts/`, `/cashbanks/transactions/`
- `POST /cashbanks/transactions/{id}/post_tx/`

## Expenses
- CRUD `/expenses/categories/`, `/expenses/`
- Workflow: `POST /expenses/{id}/submit|approve|reject|post_expense/`

## Customers / Suppliers
- CRUD `/customers/`, `/suppliers/`
- `GET /customers/{id}/ledger/?from=&to=` (statement) — same for suppliers

## Reports
- `GET /reports/trial-balance/`, `/income-statement/`, `/balance-sheet/`,
  `/general-ledger/?account=`, `/cash-flow/` — all accept `?from=&to=`
- `GET /reports/trial-balance/export/?format=excel|pdf`

## Dashboard / Audit
- `GET /dashboard/summary/`
- `GET /audit/logs/` (admin)
