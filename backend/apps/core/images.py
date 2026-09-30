from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def make_thumbnail(image_field, size=(600, 600), quality=82) -> ContentFile:
    """Return a WebP thumbnail of `image_field` as a ContentFile named after the source."""
    image_field.open()
    with Image.open(image_field) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail(size, Image.Resampling.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=quality, method=6)
    return ContentFile(buffer.getvalue(), name=f"{Path(image_field.name).stem}_thumb.webp")
