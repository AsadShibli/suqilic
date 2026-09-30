# Suqilic — Project Requirements

A sticker and card-skin storefront modeled on the structure and features of https://www.stickiemart.com/, rebranded as **Suqilic**. The design comes from the Suqilic logo in `logo/`. There is **no online payment**: customers send an order request and the admin follows up.

---

## 1. Decisions

| Topic | Decision |
|---|---|
| Brand name | **Suqilic** (as shown in the logo image) |
| Backend | Django 5 + Django REST Framework |
| Frontend | React (Vite) SPA that uses the DRF API |
| Database | SQLite in development, PostgreSQL in production |
| Payments | **None.** Cart leads to an order request form (cash on delivery or manual follow-up) |
| Admin | Custom React admin dashboard at a separate secret URL, backed by staff-only DRF endpoints |
| Admin scope | Everything the reference site can manage (see §6) |
| Content | Product images and names downloaded from the reference site, used as seed data |

---

## 2. Brand & Design System (based on the logo)

The logo shows white **blackletter / gothic** lettering ("Suqilic") with sharp flourishes and faint white smoke on a near-black background.

### 2.1 Colors
| Token | Value | Use |
|---|---|---|
| `--bg` | `#0B0A0F` | Page background (logo black) |
| `--surface` | `#15141B` | Cards, header, drawers |
| `--surface-2` | `#1E1D26` | Hover states, inputs |
| `--border` | `#2A2933` | Dividers, card outlines |
| `--text` | `#F5F5F7` | Primary text (logo white) |
| `--text-muted` | `#9A99A6` | Secondary text, prices ("Regular price") |
| `--accent` | `#FFFFFF` | Buttons and highlights: white on black, reversed on hover |
| `--danger` | `#E5484D` | Errors, delete actions in the admin |
| `--success` | `#3DD68C` | Success toasts, "order received" |

The site is dark-only by default to match the logo. A light theme is out of scope.

### 2.2 Typography
- **Display / headings:** *Anton* (bold condensed sans, uppercase) for readability. The blackletter look lives only in the logo.
- **Body / UI:** a clean sans-serif such as *Inter* or *Manrope*.
- Keep the reference site's quirky casing style (for example "TRENDiNG", with lowercase "i") as an option. It is stored as plain text, so the admin controls it.

### 2.3 Visual motifs
- Faint animated smoke or grain overlay in the hero and on section dividers, echoing the smoke in the logo.
- Sharp, thin white borders. Small radii (2–4px) to match the angular lettering.
- Product cards: dark surface; on hover the image scales slightly and a white border glows.
- Buttons: solid white with black text. On hover they invert to a transparent background with a white border.

### 2.4 Logo usage
- Source: `logo/change-the-word-from--suqilic--to--suqulic---keepi (1).png`
- Produce a transparent-background PNG/SVG version for the header, plus a favicon and apple-touch-icon.
- Header logo height is about 40px on desktop and 32px on mobile.

---

## 3. Public Site: Pages & Features

Mirrors the reference site's structure.

### 3.1 Global layout
- **Announcement bar** (optional, admin-editable text and link).
- **Header:** logo in the center or left, navigation menu, search icon, account icon, and cart icon with an item count.
- **Navigation menu** (admin-managed; defaults taken from the reference site):
  Card Skins, Best Sellers, Chip Toof, Jesus Pieces, Money Gun, Bumper Stickers, Light Switch Stickers, Greeting Cards, Animated Products, Contact Us, How-To Videos.
- **Footer:** social links (Instagram, TikTok), policy links (Refund, Privacy, Terms, Shipping, Contact info), newsletter signup, and copyright line.
- Responsive: mobile gets a slide-out hamburger menu and a cart drawer.

### 3.2 Home page (`/`)
Built from **admin-managed sections**, in order:
1. Hero banner(s): image, heading, subheading, and CTA button ("Shop all Card Skins").
2. Product carousels, one per featured collection:
   - TRENDING (card skins)
   - BUMPER STICKERS
   - LIGHT SWITCH STICKERS
   - EZ-APPLY™ STICKERS
   - AS SEEN ON TIKTOK
   - GREETING CARDS
3. Each carousel has a title, horizontally scrollable product cards, a "1 / of N" pager, and a "View all" link.

### 3.3 Collection page (`/collections/:slug`)
- Collection title, description, and banner image.
- Product grid with pagination or "load more".
- Sorting: featured, best selling, A–Z, Z–A, price low to high, price high to low, newest.
- Filters: availability (in stock), price range, and product type/tag.
- Product count.

### 3.4 Product page (`/products/:slug`)
- Image gallery with thumbnails and zoom/lightbox.
- Title and price, showing "From $X" when variants have different prices.
- Variant selector (size, finish, and so on). For example, bumper stickers come in several sizes.
- Quantity selector.
- **Add to cart** button, with a sold-out state.
- Rich-text description.
- Optional embedded how-to video.
- "You may also like" related products.

### 3.5 Cart (`/cart` plus a slide-out drawer)
- Line items: image, title, variant, quantity +/-, remove, and line total.
- Subtotal.
- Optional order note.
- **"Place Order Request"** button (no payment).
- Cart is kept in `localStorage` for guests and synced to the server for logged-in users.

### 3.6 Order request (`/checkout`), with no payment
- Form fields: full name, email, phone, shipping address (line 1, line 2, city, state/region, postal code, country), and an optional note.
- Submitting creates an **Order** with status `pending` and shows a confirmation page with the order number.
- A confirmation email goes to the customer and a notification email goes to the admin (console email backend in development).
- Stock is checked when the form is submitted.

### 3.7 Search (`/search?q=`)
- Searches product title, tags, and collection name.
- Instant search dropdown in the header, plus a full results page.

### 3.8 Customer accounts (optional; the reference site has a "Log in" link)
- Register, log in, log out, and password reset by email.
- Account page shows order request history and saved addresses.
- Guests can place order requests without an account.

### 3.9 Static & content pages
- **Contact Us** (`/pages/contact-us`): contact form. Messages are saved to the database and emailed to the admin.
- **How-To Videos** (`/pages/how-to-videos`): list of embedded videos (YouTube/TikTok links).
- **Policies** (`/policies/:slug`): refund, privacy, terms of service, shipping, and contact information.
- Other generic pages the admin creates, served from `/pages/:slug`.

### 3.10 Newsletter
- Email signup in the footer, stored as subscribers the admin can export as CSV.

### 3.11 Not included
- Payment gateways, discounts or coupon codes applied at checkout, gift cards, multi-currency, and country/region switching. Prices are shown in one currency, **USD** by default; the admin can change the currency symbol in settings.

---

## 4. Admin Panel

### 4.1 Access
- Separate URL, **not** linked anywhere on the public site, for example `/suqilic-control/`. The path is set by the environment variable `ADMIN_URL_PATH`.
- Only users with `is_staff=True` can log in. JWT auth (access + refresh tokens) through `djangorestframework-simplejwt`.
- Login rate limiting (DRF throttling or django-axes).
- The built-in Django admin (`/django-admin/`, also renamed through an environment variable) stays enabled as a fallback for superusers.

### 4.2 Dashboard home
- Stat cards: pending orders, orders this week, total products, low-stock products, new messages.
- Table of recent orders.

### 4.3 Management modules (full CRUD for each)
| Module | Features |
|---|---|
| **Products** | Create, edit, delete, duplicate. Title, slug, description (rich text), price, compare-at price, status (active/draft/archived), tags, collections, SEO title and description |
| **Product images** | Upload several images, drag to reorder, set the main image, add alt text, delete |
| **Variants** | Options (for example Size or Finish), and per-variant price, SKU, and stock quantity |
| **Collections** | Title, slug, description, banner image, sort order, manual product assignment and ordering |
| **Home page sections** | Add, remove, and reorder sections; pick section type (hero banner or product carousel); link a collection; set title and "View all" link; toggle visibility |
| **Hero banners** | Image (desktop and mobile versions), heading, subheading, button text and link, active flag |
| **Navigation menus** | Header and footer menus: add, edit, and reorder links |
| **Orders** | List with filters (status, date) and search. Detail view with items and customer info. Update status: pending, confirmed, shipped, delivered, or cancelled. Internal notes. Print or export CSV |
| **Customers** | List, view details and order history, activate or deactivate |
| **Pages & policies** | CRUD for static pages (rich text) |
| **How-to videos** | Title, video URL, thumbnail, order |
| **Contact messages** | Inbox with read/unread status, reply via mailto link, delete |
| **Newsletter subscribers** | List, delete, export CSV |
| **Site settings** | Store name, logo, favicon, announcement bar, social links, contact email, currency symbol, SEO defaults |
| **Staff users** | Superusers only: add or remove staff, reset passwords |

### 4.4 Admin UX
- Dark theme that matches the brand.
- Data tables with search, sort, pagination, and bulk actions (delete, change status).
- Confirmation dialog before any delete.
- Toast notifications and form validation messages.
- Image upload with preview and drag-and-drop.

---

## 5. Backend (Django + DRF)

### 5.1 Django apps
| App | Responsibility |
|---|---|
| `core` | Site settings, navigation menus, pages, how-to videos, contact messages, newsletter |
| `catalog` | Products, variants, images, collections, tags |
| `storefront` | Home page sections and hero banners |
| `orders` | Cart and order requests |
| `accounts` | Custom user model, customer profiles, addresses, JWT auth |

### 5.2 Main models (summary)
- `SiteSettings` (singleton), `MenuItem`, `Page`, `HowToVideo`, `ContactMessage`, `NewsletterSubscriber`
- `Collection`, `Product`, `ProductImage`, `ProductOption`, `ProductVariant`, `Tag`, `CollectionProduct` (ordering through-table)
- `HomeSection`, `HeroBanner`
- `Cart`, `CartItem`, `Order`, `OrderItem`, which snapshots the title, variant, and price at the time of the order
- `User` (custom, email login), `Address`

### 5.3 API layout
- Public, read-only: `/api/v1/…` for products, collections, home, search, pages, menus, and settings.
- Public, write: `/api/v1/orders/` (create an order request), `/api/v1/contact/`, `/api/v1/newsletter/`, and `/api/v1/auth/…`.
- Customer (authenticated): `/api/v1/me/…` for profile, addresses, orders, and cart.
- Admin (`IsAdminUser`): `/api/v1/admin/…` with full CRUD `ModelViewSet`s for every module in §4.3.
- Filtering, search, and ordering through `django-filter` and the DRF filter backends. Paginated responses.
- API docs generated with `drf-spectacular` (Swagger UI in development only).

### 5.4 Key packages
`djangorestframework`, `djangorestframework-simplejwt`, `django-filter`, `django-cors-headers`, `drf-spectacular`, `Pillow`, `django-environ`, `django-storages` (production media), `whitenoise`, and optionally `django-axes`.

### 5.5 Media
- Development: local `media/` folder.
- Production: S3-compatible storage or Cloudinary.
- Thumbnails are generated automatically on upload (card size and full size).

---

## 6. Content Seeding from the Reference Site

- A management command, `python manage.py import_reference_content`, does the following:
  1. Downloads product images, titles, prices, variants, and collections from stickiemart.com. Because the site runs on Shopify, the public `/products.json` and `/collections/<slug>/products.json` endpoints can be used.
  2. Saves images into `media/products/…` and creates the matching Product, Variant, Image, and Collection records.
  3. Builds the default home sections and navigation menu to mirror the reference site.
- The command can be run again safely: it upserts by slug.

> ⚠️ **Legal note:** The downloaded images and designs belong to StickieMart, and many show copyrighted characters and real people. Use them as **placeholder or demo content only** during development, and replace them with your own designs before going live.

---

## 7. Frontend (React + Vite)

- **Stack:** React 18, Vite, React Router, TanStack Query (API data), Zustand (cart state), Tailwind CSS set up with the design tokens in §2, React Hook Form + Zod (forms), Swiper or Embla (carousels), and a rich-text editor for the admin such as TipTap.
- **Structure:** one Vite app with two route trees:
  - `/` for the public storefront
  - `/<ADMIN_URL_PATH>/` for the admin dashboard, lazy-loaded so it never appears in the public bundle
- **SEO:** `react-helmet-async` for per-page title and meta tags; sitemap.xml and robots.txt generated by Django. Robots.txt disallows the admin path.
- **Accessibility:** keyboard-navigable carousels and menus, alt text on all images, and color contrast of at least AA.

---

## 8. Non-Functional Requirements

- **Security:** CSRF/CORS configured, secrets kept in `.env`, HTTPS in production, staff-only admin endpoints, upload type and size validation, and throttling on the order, contact, and login endpoints.
- **Performance:** lazy-loaded images, WebP thumbnails, API pagination, and `select_related`/`prefetch_related` on list endpoints.
- **Responsive:** tested at 375px, 768px, 1024px, and 1440px.
- **Testing:** pytest + pytest-django for models and APIs, including permission tests that confirm non-staff users cannot reach admin endpoints. Vitest for key frontend components.
- **Deployment:** Docker Compose (Django + Postgres + Nginx serving the React build). Can also be deployed to Render or Railway.

---

## 9. Project Structure (planned)

```
drf/
├── logo/
├── backend/
│   ├── config/            # settings, urls, wsgi
│   ├── core/  catalog/  storefront/  orders/  accounts/
│   ├── media/
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── storefront/    # public pages & components
│   │   ├── admin/         # admin dashboard (lazy-loaded)
│   │   ├── api/  store/  components/  styles/
│   └── vite.config.ts
├── docker-compose.yml
└── REQUIREMENTS.md
```

---

## 10. Build Phases

1. **Setup:** backend and frontend scaffolding, env config, design tokens, logo assets.
2. **Catalog backend:** models, public API, and the reference content import command.
3. **Storefront UI:** layout, home sections, collection, product, and search pages.
4. **Cart & order requests:** cart, checkout form, emails.
5. **Admin panel:** auth at the secret URL, then CRUD for every module in §4.3.
6. **Accounts & content pages:** customer auth, pages, videos, contact, newsletter.
7. **Polish & deploy:** SEO, performance, tests, Docker, production config.
