from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

FULL_SIZE = (1600, 1600)
THUMB_SIZE = (600, 600)


def to_webp(image_field, size, quality=82, suffix="") -> ContentFile:
    """Return `image_field` downscaled to fit `size` as a WebP ContentFile named after the source."""
    with image_field.open("rb"), Image.open(image_field) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=quality, method=6)
    return ContentFile(buffer.getvalue(), name=f"{Path(image_field.name).stem}{suffix}.webp")


def make_thumbnail(image_field) -> ContentFile:
    return to_webp(image_field, THUMB_SIZE, suffix="_thumb")


def optimize_uploads(instance, *field_names: str) -> list[str]:
    """Re-encode newly assigned (uncommitted) images as web-sized WebP before saving.

    Returns the names of the fields that changed.
    """
    changed = []
    for name in field_names:
        field = getattr(instance, name)
        if field and not field._committed:
            optimized = to_webp(field, FULL_SIZE, quality=85)
            field.save(optimized.name, optimized, save=False)
            changed.append(name)
    return changed
