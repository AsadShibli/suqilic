"""
Seed the store from the reference Shopify storefront (placeholder/demo content only).

    python manage.py import_reference_content
    python manage.py import_reference_content --collections bumper-stickers --max-images 1
    python manage.py import_reference_content --skip-images

Idempotent: products and collections are upserted by slug.
"""

import logging
import shutil
from decimal import Decimal
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import (
    Collection,
    CollectionProduct,
    Product,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    ProductVariant,
    Tag,
)
from apps.core.models import MenuItem, Page, SiteSettings
from apps.storefront.models import HeroBanner, HomeSection

logger = logging.getLogger(__name__)

SOURCE = "https://www.stickiemart.com"
DEFAULT_STOCK = 25
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SuqilicSeeder/1.0)"}

# (shopify handle, sort order). Titles come from the source.
COLLECTIONS = [
    ("card-skins", 0), ("best-sellers", 1), ("chip-toof", 2), ("jesus-pieces", 3), ("money-gun", 4),
    ("bumper-stickers", 5), ("light-switch-stickers", 6), ("greeting-cards", 7), ("animated-products", 8),
    ("ez-apply™-stickers", 9), ("as-seen-on-tiktok", 10), ("new", 11),
]

HOME_CAROUSELS = [
    ("TRENDiNG", "card-skins"),
    ("BUMPER STiCKERS", "bumper-stickers"),
    ("LiGHT SWiTCH STiCKERS", "light-switch-stickers"),
    ("EZ-APPLY™ STiCKERS", "ez-apply-stickers"),
    ("AS SEEN ON TiKTOK", "as-seen-on-tiktok"),
    ("GREETiNG CARDS", "greeting-cards"),
]

HEADER_MENU = [
    ("Card Skins", "/collections/card-skins"), ("Best Sellers", "/collections/best-sellers"),
    ("Chip Toof", "/collections/chip-toof"), ("Jesus Pieces", "/collections/jesus-pieces"),
    ("Money Gun", "/collections/money-gun"), ("Bumper Stickers", "/collections/bumper-stickers"),
    ("Light Switch Stickers", "/collections/light-switch-stickers"),
    ("Greeting Cards", "/collections/greeting-cards"), ("Animated Products", "/collections/animated-products"),
    ("Contact Us", "/pages/contact-us"), ("How-To Videos", "/pages/how-to-videos"),
]

POLICIES = [
    ("Refund policy", "refund-policy"), ("Privacy policy", "privacy-policy"),
    ("Terms of service", "terms-of-service"), ("Shipping policy", "shipping-policy"),
    ("Contact information", "contact-information"),
]


class Command(BaseCommand):
    help = "Import demo catalog content from the reference storefront and seed menus, pages and home sections."

    def add_arguments(self, parser):
        parser.add_argument("--collections", nargs="*", help="Shopify collection handles to import (default: all).")
        parser.add_argument("--max-images", type=int, default=3, help="Max images per product.")
        parser.add_argument("--skip-images", action="store_true")

    def handle(self, *args, **opts):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.max_images = 0 if opts["skip_images"] else opts["max_images"]

        handles = opts["collections"] or [h for h, _ in COLLECTIONS]
        self.source_collections = {c["handle"]: c for c in self.get_json("/collections.json?limit=250")["collections"]}
        order = dict(COLLECTIONS)
        for handle in handles:
            self.import_collection(handle, order.get(handle, 99))

        self.seed_site()
        self.stdout.write(self.style.SUCCESS(
            f"Done: {Product.objects.count()} products, {Collection.objects.count()} collections."
        ))

    # --- HTTP -------------------------------------------------------------------------------------

    def get_json(self, path):
        res = self.session.get(f"{SOURCE}{path}", timeout=30)
        res.raise_for_status()
        return res.json()

    def download(self, url) -> ContentFile | None:
        try:
            res = self.session.get(url, timeout=60)
            res.raise_for_status()
        except requests.RequestException as exc:
            self.stderr.write(f"  image failed: {url} ({exc})")
            return None
        return ContentFile(res.content, name=Path(urlparse(url).path).name)

    # --- Catalog ----------------------------------------------------------------------------------

    def import_collection(self, handle, sort_order):
        meta = self.source_collections.get(handle)
        if meta is None:
            self.stderr.write(f"Collection '{handle}' not found, skipping.")
            return
        collection, _ = Collection.objects.update_or_create(
            slug=slugify(handle),
            defaults={"title": meta["title"], "description": meta.get("description") or "", "sort_order": sort_order},
        )
        self.stdout.write(f"Collection {collection.title}")

        position, page = 0, 1
        while products := self.get_json(f"/collections/{quote(handle)}/products.json?limit=250&page={page}")["products"]:
            for data in products:
                product = self.import_product(data)
                CollectionProduct.objects.update_or_create(
                    collection=collection, product=product, defaults={"position": position}
                )
                position += 1
            page += 1

    def import_product(self, data) -> Product:
        with transaction.atomic():
            product, created = self.upsert_product(data)
        if created or not product.images.exists():  # network I/O stays outside the transaction
            self.import_images(product, data)
            self.stdout.write(f"  + {product.title}")
        return product

    def upsert_product(self, data) -> tuple[Product, bool]:
        prices = [Decimal(v["price"]) for v in data["variants"]]
        compare = [Decimal(v["compare_at_price"]) for v in data["variants"] if v.get("compare_at_price")]
        product, created = Product.objects.update_or_create(
            slug=slugify(data["handle"]),
            defaults={
                "title": data["title"],
                "description": data.get("body_html") or "",
                "base_price": min(prices),
                "compare_at_price": max(compare) if compare and max(compare) > min(prices) else None,
                "status": Product.Status.ACTIVE,
            },
        )
        product.tags.set([self.tag(t) for t in data.get("tags", []) if t.strip()])
        if created:
            self.import_variants(product, data)
        return product, created

    @staticmethod
    def tag(name) -> Tag:
        return Tag.objects.get_or_create(slug=slugify(name)[:70] or "tag", defaults={"name": name.strip()[:60]})[0]

    @staticmethod
    def import_variants(product, data):
        values = {}  # (option position, value) -> ProductOptionValue
        has_options = not (len(data["options"]) == 1 and data["options"][0]["values"] == ["Default Title"])
        if has_options:
            for opt in data["options"]:
                option = ProductOption.objects.create(product=product, name=opt["name"], position=opt["position"])
                for i, value in enumerate(opt["values"]):
                    values[(opt["position"], value)] = ProductOptionValue.objects.create(
                        option=option, value=value, position=i
                    )
        for i, v in enumerate(data["variants"]):
            sku = v.get("sku") or None
            if sku and ProductVariant.objects.filter(sku=sku).exists():
                sku = None
            variant = ProductVariant.objects.create(
                product=product,
                sku=sku,
                title="Default" if v["title"] == "Default Title" else v["title"],
                price=Decimal(v["price"]),
                stock_quantity=DEFAULT_STOCK if v.get("available", True) else 0,
                position=i,
            )
            if has_options:
                variant.option_values.set([
                    values[(n, v[f"option{n}"])] for n in (1, 2, 3) if v.get(f"option{n}") and (n, v[f"option{n}"]) in values
                ])

    def import_images(self, product, data):
        for i, img in enumerate(data.get("images", [])[: self.max_images]):
            file = self.download(img["src"])
            if file:
                image = ProductImage(product=product, alt_text=product.title[:200], position=i, is_main=i == 0)
                image.image.save(f"{product.slug}-{i}{Path(file.name).suffix or '.jpg'}", file, save=False)
                image.save()

    # --- Site content -----------------------------------------------------------------------------

    def seed_site(self):
        site = SiteSettings.load()
        site.store_name = "Suqilic"
        site.announcement_text = site.announcement_text or "Free shipping on orders over $35"
        site.announcement_active = True
        site.seo_default_title = site.seo_default_title or "Suqilic — Card Skins & Stickers"
        site.seo_default_description = site.seo_default_description or "Card skins, bumper stickers and more."
        logo = Path(settings.BASE_DIR).parent / "frontend" / "public" / "logo.png"
        if not site.logo and logo.exists():
            site.logo.save("logo.png", ContentFile(logo.read_bytes()), save=False)
        site.save()

        if not MenuItem.objects.exists():
            MenuItem.objects.bulk_create(
                [MenuItem(menu="header", label=l, url=u, position=i) for i, (l, u) in enumerate(HEADER_MENU)]
                + [MenuItem(menu="policies", label=l, url=f"/policies/{s}", position=i) for i, (l, s) in enumerate(POLICIES)]
            )

        for title, slug in POLICIES:
            Page.objects.get_or_create(
                slug=slug,
                defaults={"title": title, "page_type": Page.PageType.POLICY, "body": f"<p>{title} — edit this in the admin panel.</p>"},
            )
        Page.objects.get_or_create(
            slug="contact-us", defaults={"title": "Contact Us", "body": "<p>Questions? Send us a message below.</p>"}
        )

        if not HomeSection.objects.exists():
            self.seed_home()

    def seed_home(self):
        hero = HomeSection.objects.create(type=HomeSection.SectionType.HERO, position=0)
        banner_source = ProductImage.objects.filter(product__collections__slug="card-skins", is_main=True).first()
        if banner_source:
            banner = HeroBanner(
                section=hero, heading="SHOP ALL CARD SKiNS", subheading="Skins for the cards you actually use.",
                button_text="Shop all Card Skins", button_link="/collections/card-skins",
            )
            banner.image_desktop.save(Path(banner_source.image.name).name, ContentFile(banner_source.image.read()), save=False)
            banner.save()
        for i, (title, slug) in enumerate(HOME_CAROUSELS, start=1):
            collection = Collection.objects.filter(slug=slug).first()
            if collection:
                HomeSection.objects.create(
                    type=HomeSection.SectionType.PRODUCT_CAROUSEL, title=title, collection=collection, position=i
                )
