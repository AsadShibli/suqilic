# Suqilic — API Design (v1)

Base URL: `/api/v1/`   ·   Format: JSON   ·   Auth: JWT (`Authorization: Bearer <access>`)

**Access levels**
- 🌐 **Public**: anyone
- 👤 **Customer**: a logged-in user
- 🛡️ **Admin**: `is_staff=True`
- 👑 **Super**: `is_superuser=True`

**Conventions**
- Lists are paginated: `?page=1&page_size=24` returns `{count, next, previous, results}`.
- Filtering: `?field=value`. Search: `?search=`. Ordering: `?ordering=-created_at`.
- Public detail routes use a `slug`. Admin routes use an `id`.
- Errors come back as `{ "detail": "..."}` or `{ "field": ["msg"] }`, with codes 400, 401, 403, 404, or 429.
- Throttled endpoints are marked ⏱.
- The admin dashboard URL (frontend) comes from the `ADMIN_URL_PATH` env var, e.g. `/suqilic-control/`. The API prefix `/api/v1/admin/` is protected by permissions, not by being hidden.

---

## 1. Auth — `accounts`

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/auth/register/` | 🌐 ⏱ | Create a customer account `{email, password, first_name, last_name}` |
| POST | `/auth/login/` | 🌐 ⏱ | Get a JWT pair `{email, password}` → `{access, refresh, user}` |
| POST | `/auth/refresh/` | 🌐 | `{refresh}` → `{access}` |
| POST | `/auth/logout/` | 👤 | Blacklist the refresh token |
| POST | `/auth/password-reset/` | 🌐 ⏱ | Send a reset email `{email}` |
| POST | `/auth/password-reset/confirm/` | 🌐 | `{uid, token, new_password}` |
| POST | `/auth/admin/login/` | 🌐 ⏱ | Staff-only login: rejects non-staff users; stricter throttle and lockout |

## 2. Customer — `me`

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET / PATCH | `/me/` | 👤 | View or update the profile |
| POST | `/me/change-password/` | 👤 | `{old_password, new_password}` |
| GET / POST | `/me/addresses/` | 👤 | List or add addresses |
| GET / PATCH / DELETE | `/me/addresses/{id}/` | 👤 | Manage one address |
| GET | `/me/orders/` | 👤 | The customer's order request history |
| GET | `/me/orders/{order_number}/` | 👤 | One order's details |

---

## 3. Catalog — public

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/collections/` | 🌐 | Active collections |
| GET | `/collections/{slug}/` | 🌐 | Collection details (title, description, banner, SEO) |
| GET | `/collections/{slug}/products/` | 🌐 | Products in the collection. Filters: `in_stock`, `min_price`, `max_price`, `tag`. Ordering: `featured`, `best_selling`, `title`, `-title`, `price`, `-price`, `-created_at` |
| GET | `/products/` | 🌐 | All active products (same filters as above plus `collection`) |
| GET | `/products/{slug}/` | 🌐 | Product with images, options, variants (price, stock, option values), tags, and video |
| GET | `/products/{slug}/related/` | 🌐 | "You may also like" (same collection or tags) |
| GET | `/tags/` | 🌐 | Tags used for filters |
| GET | `/search/?q=` | 🌐 | Full search across product title, tags, and collection |
| GET | `/search/suggest/?q=` | 🌐 | Fast header dropdown: top 6 products and top 3 collections |

## 4. Storefront — public

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/home/` | 🌐 | Visible home sections in order. Hero sections include banners; carousel sections include the first N products and a "view all" link |
| GET | `/settings/` | 🌐 | Public site settings (store name, logo, announcement bar, social links, currency, SEO defaults) |
| GET | `/menus/{menu}/` | 🌐 | Menu tree for `header`, `footer`, or `policies` |
| GET | `/pages/{slug}/` | 🌐 | A published page, e.g. `contact-us` |
| GET | `/policies/{slug}/` | 🌐 | A policy page (refund, privacy, terms, shipping, contact info) |
| GET | `/videos/` | 🌐 | How-to videos |

## 5. Cart & Order Requests — public / customer

Guest carts are identified by the `X-Cart-Id: <uuid>` header, which the server returns the first time a cart is used. When a user logs in, the guest cart is merged into their account cart.

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/cart/` | 🌐 | Current cart with items and subtotal |
| POST | `/cart/items/` | 🌐 | Add an item `{variant_id, quantity}` (stock is checked) |
| PATCH | `/cart/items/{id}/` | 🌐 | Change the quantity `{quantity}` |
| DELETE | `/cart/items/{id}/` | 🌐 | Remove an item |
| DELETE | `/cart/` | 🌐 | Empty the cart |
| POST | `/cart/merge/` | 👤 | Merge a guest cart after login `{cart_id}` |
| POST | `/orders/` | 🌐 ⏱ | **Place an order request (no payment).** `{full_name, email, phone, line1, line2, city, region, postal_code, country, customer_note}`. Uses the current cart, re-checks stock, copies product details into the order items, sends emails, clears the cart → `{order_number, status:"pending"}` |
| GET | `/orders/track/?order_number=&email=` | 🌐 ⏱ | Guests look up their order status |

## 6. Engagement — public

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/contact/` | 🌐 ⏱ | `{name, email, phone, message}` → saves the message and emails the admin |
| POST | `/newsletter/subscribe/` | 🌐 ⏱ | `{email}` |
| POST | `/newsletter/unsubscribe/` | 🌐 | `{email, token}` |

---

## 7. Admin API — `/admin/…` (🛡️ staff only)

Every resource is a DRF `ModelViewSet` with the standard routes:

```
GET    /admin/<resource>/          list (search, filter, ordering, pagination)
POST   /admin/<resource>/          create
GET    /admin/<resource>/{id}/     retrieve
PATCH  /admin/<resource>/{id}/     partial update
PUT    /admin/<resource>/{id}/     full update
DELETE /admin/<resource>/{id}/     delete
POST   /admin/<resource>/bulk-delete/   {ids: []}
```

### 7.1 Dashboard
| Method | Endpoint | Description |
|---|---|---|
| GET | `/admin/dashboard/stats/` | Pending orders, orders this week, product count, low-stock count, unread messages |
| GET | `/admin/dashboard/recent-orders/` | The 10 most recent orders |

### 7.2 Catalog
| Resource | Extra routes / notes |
|---|---|
| `/admin/products/` | Filters: `status`, `collection`, `tag`, `low_stock`. Search: title, sku. `POST /{id}/duplicate/` · `POST /bulk-status/ {ids, status}` |
| `/admin/products/{id}/images/` | Nested CRUD. Upload with `multipart/form-data`. `POST /reorder/ {ids:[...]}` · `POST /{img_id}/set-main/` |
| `/admin/products/{id}/options/` | Nested CRUD. Write `{name, values: ["S", "L"]}`; values are synced |
| `/admin/products/{id}/variants/` | Nested CRUD. `POST /generate/` creates every combination of option values. Inline stock/price edits use `PATCH /{variant_id}/` |
| `/admin/collections/` | Banner upload. `GET/POST /{id}/products/` to list or assign products · `POST /{id}/products/reorder/ {product_ids:[...]}` |
| `/admin/tags/` | CRUD |

### 7.3 Storefront
| Resource | Extra routes / notes |
|---|---|
| `/admin/home-sections/` | `POST /reorder/ {ids:[...]}` · `POST /{id}/toggle-visibility/` |
| `/admin/hero-banners/` | Desktop and mobile image upload. `POST /reorder/` |
| `/admin/menu-items/` | Filter by `menu`. `POST /reorder/ {menu, items:[{id, parent_id, position}]}` |
| `/admin/pages/` | Filter by `page_type` (page or policy). Rich-text body |
| `/admin/videos/` | `POST /reorder/` |
| `/admin/settings/` | Singleton: `GET` and `PATCH` only (logo and favicon upload) |

### 7.4 Orders & customers
| Resource | Extra routes / notes |
|---|---|
| `/admin/orders/` | Filters: `status`, `created_at__gte/lte`. Search: order_number, name, email, phone. No POST (orders come from the storefront). `POST /{id}/status/ {status, note}` logs a status-history entry and optionally emails the customer · `PATCH /{id}/` for `internal_note` · `GET /export/` (CSV; honours list filters). Printing is done client-side from the detail view |
| `/admin/customers/` | Read and PATCH only (`is_active`). `GET /{id}/orders/` |

### 7.5 Inbox & marketing
| Resource | Extra routes / notes |
|---|---|
| `/admin/messages/` | Read and delete. `POST /{id}/mark-read/` · `POST /bulk-mark-read/` |
| `/admin/subscribers/` | List and delete. `GET /export/` (CSV) |

### 7.6 Staff (👑 superuser only)
| Resource | Extra routes / notes |
|---|---|
| `/admin/staff/` | CRUD for staff users. `POST /{id}/reset-password/` |

### 7.7 Uploads
| Method | Endpoint | Description |
|---|---|---|
| POST | `/admin/uploads/` | General image upload for the rich-text editor (multipart) → `{url}`. Accepts jpg, png, webp, or gif, up to 5 MB |

---

## 8. Sample payloads

**GET `/products/{slug}/`**
```json
{
  "id": 12, "title": "PRIVATE PROPERTY", "slug": "private-property",
  "description": "<p>…</p>", "price_from": "8.99", "compare_at_price": null,
  "in_stock": true, "video_url": null,
  "images": [{"id": 1, "url": "/media/products/…webp", "thumb": "…", "alt": "…", "is_main": true}],
  "options": [{"name": "Size", "values": ["Small", "Large"]}],
  "variants": [{"id": 31, "title": "Small", "sku": "PP-S", "price": "8.99", "stock": 40, "options": {"Size": "Small"}}],
  "tags": ["bumper", "funny"],
  "collections": [{"title": "Bumper Stickers", "slug": "bumper-stickers"}]
}
```

**POST `/orders/`: response `201`**
```json
{ "order_number": "SQ-000123", "status": "pending", "subtotal": "26.97", "items": [ … ] }
```

---

## 9. Other endpoints (not under `/api/v1`)
| Path | Description |
|---|---|
| `/api/schema/` · `/api/docs/` | OpenAPI schema and Swagger UI (development only) |
| `/sitemap.xml` · `/robots.txt` | SEO. robots.txt disallows the admin path |
| `/<DJANGO_ADMIN_PATH>/` | Fallback Django admin (renamed through an env var) |
| `/media/…` | Uploaded files (served from S3 or Cloudinary in production) |
