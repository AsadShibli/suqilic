"""Load the bundled demo catalog (seed/catalog.json + seed/media) into an empty database.

    python manage.py seed_demo            # no-op if any product exists
    python manage.py seed_demo --export   # (dev) regenerate the bundle from the current database

Runs on every boot in staging; it only does work the first time.
"""

import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.catalog.models import Product

SEED_DIR = Path(settings.BASE_DIR) / "seed"
FIXTURE = SEED_DIR / "catalog.json"
MEDIA = SEED_DIR / "media"
# Catalog + storefront content only; never users, carts, orders, messages or stored files.
EXPORT = ["catalog", "storefront", "core.sitesettings", "core.menuitem", "core.page", "core.howtovideo"]


class Command(BaseCommand):
    help = "Load (or with --export, build) the bundled demo catalog."

    def add_arguments(self, parser):
        parser.add_argument("--export", action="store_true")

    def handle(self, *args, export, **options):
        if export:
            return self.export()
        if Product.objects.exists():
            self.stdout.write("Catalog present; skipping demo seed.")
            return
        if not FIXTURE.exists():
            self.stdout.write("No demo bundle found; skipping.")
            return
        call_command("loaddata", str(FIXTURE))
        call_command("copy_media", source=str(MEDIA))
        self.stdout.write(self.style.SUCCESS("Demo catalog loaded."))

    def export(self):
        SEED_DIR.mkdir(exist_ok=True)
        call_command("dumpdata", *EXPORT, indent=1, output=str(FIXTURE))
        shutil.rmtree(MEDIA, ignore_errors=True)
        media_root = Path(settings.MEDIA_ROOT)
        for sub in ("products", "banners", "collections", "site", "videos"):
            if (media_root / sub).exists():
                shutil.copytree(media_root / sub, MEDIA / sub)
        self.stdout.write(self.style.SUCCESS(f"Exported demo bundle to {SEED_DIR}"))
