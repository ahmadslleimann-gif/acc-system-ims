# Deploying to a DigitalOcean droplet (web console only)

You have: the project on your **PC**, and only the **web console** for the droplet.
Strategy: push the code to **GitHub** from your PC, then **clone + run with Docker** on the droplet.

The whole app runs as one Docker stack (nginx + Django + PostgreSQL) reachable at
`http://YOUR_SERVER_IP`.

---

## Part A — on your PC (once): push the code to GitHub
```bash
cd "A:\accounting system-IMS"
git add -A
git commit -m "Production Docker deployment"
git push origin main
```
(Repo: https://github.com/ahmadslleimann-gif/acc-system-ims)

---

## Part B — on the droplet (DigitalOcean web console)

### 1. Install Docker (Ubuntu droplet)
```bash
curl -fsSL https://get.docker.com | sh
```

### 2. Get the code
```bash
cd /opt
git clone https://github.com/ahmadslleimann-gif/acc-system-ims.git
cd acc-system-ims
```
> Private repo? When prompted for a password, use a GitHub **Personal Access Token**
> (GitHub → Settings → Developer settings → Tokens), not your account password.

### 3. Create the environment file
```bash
cp .env.prod.example .env
nano .env
```
Set at least: `SECRET_KEY`, `DB_PASSWORD`, `DJANGO_SUPERUSER_PASSWORD`,
and put your droplet's IP in `FRONTEND_ORIGIN` and `CSRF_TRUSTED_ORIGINS`
(e.g. `http://203.0.113.10`). Save with `Ctrl+O`, `Enter`, then `Ctrl+X`.

### 4. Build & start
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
First build takes a few minutes. It automatically migrates the database, seeds the
chart of accounts + roles, and creates your admin user.

### 5. Open it
Browse to **`http://YOUR_SERVER_IP`** and log in with the admin username/password
from your `.env`.

---

## Everyday commands (on the droplet)
| Task | Command |
|------|---------|
| See logs | `docker compose -f docker-compose.prod.yml logs -f` |
| Stop | `docker compose -f docker-compose.prod.yml down` |
| Update after pushing new code | `git pull && docker compose -f docker-compose.prod.yml up -d --build` |
| Reset all data to zero | `docker compose -f docker-compose.prod.yml exec backend python manage.py reset_data --yes` |
| Run any manage.py command | `docker compose -f docker-compose.prod.yml exec backend python manage.py <cmd>` |

---

## Firewall
Make sure the droplet allows inbound **port 80** (DigitalOcean → Networking →
Firewalls, or `ufw allow 80`).

## Adding a domain + HTTPS (later, optional)
1. Point your domain's A-record to the droplet IP.
2. In `.env` set `ALLOWED_HOSTS=yourdomain.com`, `FRONTEND_ORIGIN=https://yourdomain.com`,
   `CSRF_TRUSTED_ORIGINS=https://yourdomain.com`, `SECURE_SSL_REDIRECT=True`.
3. Put a TLS proxy (Caddy or nginx + certbot) in front, or use DigitalOcean's load balancer.
   Ask and I'll add a ready-made HTTPS Caddy service to the compose file.
