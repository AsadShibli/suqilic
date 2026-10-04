"""Create a small, original placeholder catalog (generated artwork) for demos, docs and local development.

    python manage.py seed_placeholder_catalog

Safe to re-run: products and collections are upserted by slug.
"""

from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageDraw, ImageFont

from apps.catalog.models import Collection, CollectionProduct, Product, ProductImage, ProductOption, ProductVariant
from apps.core.models import MenuItem, Page, SiteSettings
from apps.storefront.models import HeroBanner, HomeSection

SIZE = 1000
WHITE, INK = (255, 255, 255), (12, 11, 16)

# (collection title, kind, price, [(product title, line 1, line 2, background, foreground)])
CATALOG = [
    ("Card Skins", "card", "9.99", [
        ("Midnight Smoke", "MIDNIGHT", "SMOKE", (24, 22, 32), (245, 245, 247)),
        ("Gold Standard", "GOLD", "STANDARD", (212, 175, 55), INK),
        ("Blood Moon", "BLOOD", "MOON", (150, 20, 30), (255, 235, 220)),
        ("Mint Condition", "MINT", "CONDITION", (60, 214, 140), INK),
        ("Static Noise", "STATIC", "NOISE", (120, 120, 132), WHITE),
        ("Deep Violet", "DEEP", "VIOLET", (84, 44, 160), (240, 230, 255)),
        ("Bone White", "BONE", "WHITE", (236, 232, 220), INK),
        ("Rust Belt", "RUST", "BELT", (176, 86, 40), (255, 240, 225)),
    ]),
    ("Bumper Stickers", "bumper", "8.99", [
        ("Slow Is Smooth", "SLOW IS SMOOTH", "SMOOTH IS FAST", (250, 204, 21), INK),
        ("Powered By Coffee", "POWERED BY", "COFFEE & SPITE", INK, (250, 250, 250)),
        ("Not In A Hurry", "NOT IN A HURRY", "GO AROUND", (230, 57, 70), WHITE),
        ("Mind The Gap", "MIND THE GAP", "THANK YOU", (29, 78, 216), WHITE),
        ("Honk If You Read", "HONK IF YOU", "READ BOOKS", (245, 245, 247), INK),
    ]),
    ("Laptop Stickers", "round", "6.99", [
        ("Ship It", "SHIP", "IT", (60, 214, 140), INK),
        ("Works On My Machine", "WORKS ON", "MY MACHINE", (245, 245, 247), INK),
        ("No Signal", "NO", "SIGNAL", INK, (229, 72, 77)),
        ("Stay Sharp", "STAY", "SHARP", (212, 175, 55), INK),
    ]),
]

HOME_TITLES = {"Card Skins": "TRENDiNG", "Bumper Stickers": "BUMPER STiCKERS", "Laptop Stickers": "LAPTOP STiCKERS"}
POLICIES = ["Refund policy", "Privacy policy", "Terms of service", "Shipping policy"]


def _fit(draw, text, max_width, start):
    size = start
    while size > 20 and draw.textlength(text, font=ImageFont.load_default(size=size)) > max_width:
        size -= 6
    return ImageFont.load_default(size=size)


def _centered(draw, box, lines, fill):
    left, top, right, bottom = box
    fonts = [_fit(draw, line, (right - left) * 0.82, 150) for line in lines]
    total = sum(f.size for f in fonts) + 24 * (len(lines) - 1)
    y = (top + bottom - total) / 2
    for line, font in zip(lines, fonts):
        draw.text(((left + right) / 2, y), line, font=font, fill=fill, anchor="ma")
        y += font.size + 24


def render_art(kind, lines, bg, fg) -> ContentFile:
    """Draw a simple product mock-up: a payment-card skin, a bumper sticker, or a round sticker."""
    img = Image.new("RGB", (SIZE, SIZE), WHITE)
    draw = ImageDraw.Draw(img)
    if kind == "card":
        box = (110, 260, 890, 740)
        draw.rounded_rectangle(box, radius=42, fill=bg, outline=INK, width=4)
        draw.rounded_rectangle((180, 330, 290, 410), radius=14, fill=(214, 190, 120), outline=INK, width=3)
        _centered(draw, (110, 400, 890, 740), lines, fg)
    elif kind == "bumper":
        box = (70, 340, 930, 660)
        draw.rounded_rectangle(box, radius=18, fill=bg, outline=INK, width=6)
        _centered(draw, box, lines, fg)
    else:
        box = (170, 170, 830, 830)
        draw.ellipse(box, fill=bg, outline=INK, width=8)
        _centered(draw, (250, 250, 750, 750), lines, fg)
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return ContentFile(buffer.getvalue())


def render_banner() -> ContentFile:
    img = Image.new("RGB", (1920, 900), INK)
    draw = ImageDraw.Draw(img)
    for i, color in enumerate([(84, 44, 160), (150, 20, 30), (212, 175, 55), (60, 214, 140), (29, 78, 216)]):
        x = 180 + i * 330
        draw.rounded_rectangle((x, 260 + (i % 2) * 90, x + 260, 420 + (i % 2) * 90), radius=22, fill=color)
    buffer = BytesIO()
    img.save(buffer, "PNG")
    return ContentFile(buffer.getvalue(), name="hero.png")


class Command(BaseCommand):
    help = "Seed an original placeholder catalog with generated artwork."

    @transaction.atomic
    def handle(self, *args, **options):
        for order, (title, kind, price, items) in enumerate(CATALOG):
            collection, _ = Collection.objects.update_or_create(
                slug=slugify(title), defaults={"title": title.upper(), "sort_order": order}
            )
            for position, item in enumerate(items):
                product = self.product(kind, Decimal(price), *item)
                CollectionProduct.objects.update_or_create(
                    collection=collection, product=product, defaults={"position": position}
                )
        self.site()
        self.stdout.write(self.style.SUCCESS(f"Placeholder catalog ready: {Product.objects.count()} products."))

    def product(self, kind, price, title, line1, line2, bg, fg) -> Product:
        product, created = Product.objects.update_or_create(
            slug=slugify(title),
            defaults={
                "title": title.upper(),
                "base_price": price,
                "status": Product.Status.ACTIVE,
                "description": "<p>Placeholder product with generated artwork. Replace it with your own design.</p>",
            },
        )
        if not created:
            return product
        if kind == "bumper":
            option = ProductOption.objects.create(product=product, name="Type")
            for i, (value, extra) in enumerate([("Sticker", 0), ("Magnet", 2)]):
                variant = ProductVariant.objects.create(
                    product=product, title=value, price=price + extra, stock_quantity=25, position=i
                )
                variant.option_values.add(option.values.create(value=value, position=i))
        else:
            ProductVariant.objects.create(product=product, price=price, stock_quantity=25)
        art = render_art(kind, [line1, line2], bg, fg)
        art.name = f"{product.slug}.png"
        ProductImage.objects.create(product=product, image=art, alt_text=title, is_main=True)
        return product

    def site(self):
        site = SiteSettings.load()
        site.announcement_text = site.announcement_text or "Free shipping on orders over ৳500"
        site.announcement_active = True
        site.seo_default_title = site.seo_default_title or "Suqilic — Card Skins & Stickers"
        site.save()

        if not MenuItem.objects.exists():
            links = [(c[0], f"/collections/{slugify(c[0])}") for c in CATALOG] + [("Contact Us", "/pages/contact-us")]
            MenuItem.objects.bulk_create(
                [MenuItem(menu="header", label=label, url=url, position=i) for i, (label, url) in enumerate(links)]
                + [
                    MenuItem(menu="policies", label=p, url=f"/policies/{slugify(p)}", position=i)
                    for i, p in enumerate(POLICIES)
                ]
            )
        for title in POLICIES:
            Page.objects.get_or_create(
                slug=slugify(title),
                defaults={"title": title, "page_type": Page.PageType.POLICY, "body": f"<p>{title} goes here.</p>"},
            )
        Page.objects.get_or_create(
            slug="contact-us", defaults={"title": "Contact Us", "body": "<p>Questions? Send us a message below.</p>"}
        )

        if not HomeSection.objects.exists():
            hero = HomeSection.objects.create(type=HomeSection.SectionType.HERO, position=0)
            HeroBanner.objects.create(
                section=hero, image_desktop=render_banner(), heading="SKiNS & STiCKERS",
                subheading="Make the everyday stuff yours.", button_text="Shop card skins",
                button_link="/collections/card-skins",
            )
            for position, (title, heading) in enumerate(HOME_TITLES.items(), start=1):
                HomeSection.objects.create(
                    type=HomeSection.SectionType.PRODUCT_CAROUSEL, title=heading,
                    collection=Collection.objects.get(slug=slugify(title)), position=position,
                )
