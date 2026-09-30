# Suqilic — Implementation Plan

References: [REQUIREMENTS.md](../REQUIREMENTS.md) · [erd.mmd](erd.mmd) · [API.md](API.md)

## Phase 1 — Backend foundation
- [x] `backend/` venv, `requirements.txt`, `.env.example`, split settings (`base/dev/prod`)
- [x] Custom `User` (email login), JWT, CORS, DRF defaults (pagination, throttles, filters), spectacular
- [x] Apps: `accounts`, `catalog`, `storefront`, `orders`, `core`, all with models matching the ERD
- [x] Migrations, Django admin registration on the env-configured path

## Phase 2 — Public + customer API
- [x] Catalog: collections, products, related, tags, search/suggest
- [x] Storefront: home, settings, menus, pages, policies, videos
- [x] Cart (guest `X-Cart-Id` + user), order request, tracking, emails
- [x] Auth: register/login/refresh/logout/password reset, admin login; `/me/*`
- [x] Contact, newsletter

## Phase 3 — Admin API
- [x] ViewSets for every resource in API.md §7 (bulk delete, reorder, status, export CSV, duplicate, variant generation)
- [x] Dashboard stats

## Phase 4 — Seed content
- [x] `import_reference_content` command (Shopify `products.json`), default menus, home sections, pages

## Phase 5 — Frontend (React + Vite + Tailwind)
- [x] Design tokens, logo assets, layout (announcement, header, footer, cart drawer)
- [x] Home, collection, product, cart, checkout, search, pages, account
- [x] Admin dashboard at `VITE_ADMIN_PATH` (lazy-loaded): CRUD screens

## Phase 6 — Quality & deploy
- [x] pytest API and permission tests
- [x] Docker Compose (postgres + django/gunicorn + nginx serving the SPA)
