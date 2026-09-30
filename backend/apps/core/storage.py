import mimetypes
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Store uploaded media in Postgres (`StoredFile`), served by `core.media_views.serve_media`.

    Meant for small catalogs on hosts with an ephemeral filesystem; images are optimized to WebP on upload.
    """

    @staticmethod
    def _model():
        from .models import StoredFile

        return StoredFile

    def _open(self, name, mode="rb"):
        return ContentFile(bytes(self._model().objects.values_list("content", flat=True).get(name=name)), name=name)

    def _save(self, name, content):
        content.seek(0)
        data = content.read()
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        self._model().objects.update_or_create(
            name=name, defaults={"content": data, "content_type": content_type, "size": len(data)}
        )
        return name

    def exists(self, name):
        return self._model().objects.filter(name=name).exists()

    def delete(self, name):
        self._model().objects.filter(name=name).delete()

    def size(self, name):
        return self._model().objects.values_list("size", flat=True).get(name=name)

    def url(self, name):
        return urljoin(settings.MEDIA_URL, name)
