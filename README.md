# Cloud Accounting System (IMS)

A professional, production-oriented double-entry accounting web application for a single SMB.
Arabic (RTL) and English (LTR), VAT-enabled, with a strict accounting engine.

## Stack
- **Backend:** Django 5 + Django REST Framework, SimpleJWT, PostgreSQL
- **Frontend:** React + TypeScript + Vite + Tailwind CSS (RTL/LTR)
- **Infra:** Docker + docker-compose, Redis (cache/throttle)

## Architecture rule (non-negotiable)
No business module writes to the ledger. They call `accounting_engine.PostingService.post(...)`,
which is the only code that creates balanced `JournalEntry` + `JournalLine` rows, atomically.

## Quick start (Docker)
```bash
cp backend/.env.example backend/.env
docker compose up --build
# backend  -> http://localhost:8000/api/
# frontend -> http://localhost:5173/
```

## Quick start (local, no Docker)
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_coa      # seed chart of accounts + system accounts
python manage.py createsuperuser
python manage.py runserver
```
### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Default roles
Super Admin, Accountant, Sales Employee, Viewer — seeded with `python manage.py seed_roles`.

See `docs/` for the full design (requirements, architecture, ERD, API, accounting engine, roadmap).
