# Suqilic — Implementation Plan

References: [REQUIREMENTS.md](../REQUIREMENTS.md) · [erd.mmd](erd.mmd) · [API.md](API.md)

## Phase 1 — Backend foundation
- [ ] `backend/` venv, `requirements.txt`, `.env.example`, split settings (`base/dev/prod`)
- [ ] Custom `User` (email login), JWT, CORS, DRF defaults (pagination, throttles, filters), spectacular
- [ ] Apps: `accounts`, `catalog`, `storefront`, `orders`, `core`, all with models matching the ERD
- [ ] Migrations, Django admin registration on the env-configured path

## Phase 2 — Public + customer API
- [ ] Catalog: collections, products, related, tags, search/suggest
- [ ] Storefront: home, settings, menus, pages, policies, videos
- [ ] Cart (guest `X-Cart-Id` + user), order request, tracking, emails
- [ ] Auth: register/login/refresh/logout/password reset, admin login; `/me/*`
- [ ] Contact, newsletter

## Phase 3 — Admin API
- [ ] ViewSets for every resource in API.md §7 (bulk delete, reorder, status, export CSV, duplicate, variant generation)
- [ ] Dashboard stats

## Phase 4 — Seed content
- [ ] `import_reference_content` command (Shopify `products.json`), default menus, home sections, pages

## Phase 5 — Frontend (React + Vite + Tailwind)
- [ ] Design tokens, logo assets, layout (announcement, header, footer, cart drawer)
- [ ] Home, collection, product, cart, checkout, search, pages, account
- [ ] Admin dashboard at `VITE_ADMIN_PATH` (lazy-loaded): CRUD screens

## Phase 6 — Quality & deploy
- [ ] pytest API and permission tests
- [ ] Docker Compose (postgres + django/gunicorn + nginx serving the SPA)
