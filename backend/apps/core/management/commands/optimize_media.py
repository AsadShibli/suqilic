"""Re-encode existing uploads as web-sized WebP (and rebuild product thumbnails).

    python manage.py optimize_media
"""

from django.core.management.base import BaseCommand

from apps.catalog.models import Collection, ProductImage
from apps.core.images import FULL_SIZE, make_thumbnail, to_webp
from apps.storefront.models import HeroBanner

TARGETS = [(ProductImage, ["image"]), (HeroBanner, ["image_desktop", "image_mobile"]), (Collection, ["banner_image"])]


class Command(BaseCommand):
    help = "Convert stored images to WebP (max 1600px) and delete the originals."

    def handle(self, *args, **options):
        converted = 0
        for model, fields in TARGETS:
            for obj in model.objects.iterator():
                for name in fields:
                    field = getattr(obj, name)
                    if not field or field.name.endswith(".webp"):
                        continue
                    stale = [field.name]
                    optimized = to_webp(field, FULL_SIZE, quality=85)
                    field.save(optimized.name, optimized, save=False)
                    updates = {name: field.name}
                    if model is ProductImage:
                        stale.append(obj.thumbnail.name)
                        thumb = make_thumbnail(field)
                        obj.thumbnail.save(thumb.name, thumb, save=False)
                        updates["thumbnail"] = obj.thumbnail.name
                    # Bypass model.save() so the new file isn't processed again.
                    model.objects.filter(pk=obj.pk).update(**updates)
                    for old in filter(None, stale):
                        field.storage.delete(old)
                    converted += 1
        self.stdout.write(self.style.SUCCESS(f"Converted {converted} images."))
