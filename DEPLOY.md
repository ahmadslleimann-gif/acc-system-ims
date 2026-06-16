# Deployment — Railway (backend) + Cloudflare Pages (frontend)

The app is two pieces deployed separately:

- **Frontend** (React) → Cloudflare Pages (already done)
- **Backend** (Django + PostgreSQL) → Railway

The frontend talks to the backend over HTTPS, so the backend MUST be deployed and
the frontend MUST point at its public URL.

---

## Part 1 — Deploy the backend on Railway

1. Push this repo to GitHub (already at `ahmadslleimann-gif/acc-system-ims`).
2. On https://railway.app → **New Project → Deploy from GitHub repo** → pick the repo.
3. Open the service → **Settings → Root Directory** = `backend`.
   (Railway then finds `requirements.txt`, `Procfile`, and `railway.toml`.)
4. **Add PostgreSQL**: in the project, **New → Database → PostgreSQL**.
   Railway auto-injects `DATABASE_URL` into the backend service.
5. Backend service → **Variables**, add:

   | Variable | Value |
   |----------|-------|
   | `DEBUG` | `False` |
   | `SECRET_KEY` | a long random string |
   | `ALLOWED_HOSTS` | `*.up.railway.app` (and your custom domain if any) |
   | `FRONTEND_ORIGIN` | `https://ims-accounting-system.cc` |
   | `CSRF_TRUSTED_ORIGINS` | `https://ims-accounting-system.cc` |
   | `DJANGO_SUPERUSER_USERNAME` | `admin` |
   | `DJANGO_SUPERUSER_PASSWORD` | a strong password |
   | `DJANGO_SUPERUSER_EMAIL` | your email |

   > `DATABASE_URL` is provided by the Postgres plugin — do **not** set it yourself.
   > Do **not** set `USE_SQLITE` (leave it unset → Postgres is used).

6. Deploy. On start the backend automatically runs:
   `migrate → collectstatic → bootstrap (seed accounts + roles + admin) → gunicorn`.
7. Under **Settings → Networking → Generate Domain** to get a public URL like
   `https://acc-system-ims-production.up.railway.app`. **Copy it.**
8. Test it: open `https://<that-domain>/api/docs/` — you should see the API docs.

---

## Part 2 — Point the frontend at the backend

In **Cloudflare Pages → your project → Settings → Environment variables**, add:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://<your-railway-domain>/api` |

Then **Deployments → Retry deployment** (or push a commit) so it rebuilds with the
new API URL. Vite bakes this in at build time, so a rebuild is required.

> SPA routing: `frontend/public/_redirects` already contains `/*  /index.html  200`
> so deep links / refreshes won't 404.

---

## Part 3 — Verify

1. Open `https://ims-accounting-system.cc`
2. Log in with the `DJANGO_SUPERUSER_USERNAME` / `PASSWORD` you set.
3. Add a product, create a sale — confirm it persists (it's now in Railway Postgres).

---

## Updating later
- **Backend change:** push to GitHub → Railway redeploys automatically.
- **Frontend change:** push to GitHub → Cloudflare rebuilds automatically.

## Notes
- File uploads (company logo via API, attachments) use local disk, which is
  **ephemeral** on Railway. For persistent uploads add a Railway Volume or switch
  `MEDIA` to S3/R2 later. The app works fine without this for core accounting.
- To run a one-off command on Railway: service → **⋯ → Shell**, e.g.
  `python manage.py bootstrap`.
