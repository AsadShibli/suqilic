# Suqilic

Sticker and card-skin storefront: **Django + DRF** API, **React (Vite) + Tailwind** SPA, and a staff dashboard at a secret URL. Customers send order requests; there is no online payment.

Docs: [REQUIREMENTS.md](REQUIREMENTS.md) · [docs/API.md](docs/API.md) · [docs/erd.png](docs/erd.png) · [docs/PLAN.md](docs/PLAN.md)

## Local development

```bash
# Backend (http://127.0.0.1:8000)
cd backend
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt   # macOS/Linux: .venv/bin/pip
cp .env.example .env            # set SECRET_KEY
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py import_reference_content   # demo catalog + menus, pages, home sections
.venv/Scripts/python manage.py runserver

# Frontend (http://localhost:5173); Vite proxies /api and /media to Django
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

- Store: http://localhost:5173
- Admin dashboard: http://localhost:5173/suqilic-control (set by `VITE_ADMIN_PATH`, which must match the backend's `ADMIN_URL_PATH`). Only staff accounts can sign in.
- Fallback Django admin: http://127.0.0.1:8000/django-admin/ (`DJANGO_ADMIN_PATH`)
- API docs (dev only): http://127.0.0.1:8000/api/docs/

## Tests

```bash
cd backend && .venv/Scripts/python -m pytest
cd frontend && npm run build   # type-check + production build
```

## Production (Docker Compose)

```bash
# backend/.env needs: SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, FRONTEND_URL, email settings
POSTGRES_PASSWORD=... docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
```

nginx serves the SPA and `/media`, and proxies `/api`, `/django-admin`, `/sitemap.xml` and `/robots.txt` to gunicorn. If you change `DJANGO_ADMIN_PATH`, update `frontend/nginx.conf` to match.

## Content notice

`import_reference_content` downloads product images and text from stickiemart.com. That material belongs to its owners (and many designs show copyrighted characters and real people). Use it only as placeholder content during development, and replace it with your own designs before launch.
