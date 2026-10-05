from celery import shared_task

from apps.core.cache import invalidate_public_cache
from apps.core.images import make_thumbnail

from .models import ProductImage


@shared_task
def build_product_thumbnail(image_id: int) -> None:
    """Generate the 600px WebP thumbnail off the request path (the slowest part of an upload)."""
    image = ProductImage.objects.filter(pk=image_id).first()
    if image is None or not image.image:
        return
    thumb = make_thumbnail(image.image)
    image.thumbnail.save(thumb.name, thumb, save=False)
    # update() rather than save(): don't re-trigger save() side effects or overwrite concurrent edits.
    ProductImage.objects.filter(pk=image_id).update(thumbnail=image.thumbnail.name)
    invalidate_public_cache()
