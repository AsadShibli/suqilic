import pytest
from django.core.files.base import ContentFile
from django.test import RequestFactory, override_settings

from apps.core.media_views import serve_media
from apps.core.storage import DatabaseStorage

pytestmark = pytest.mark.django_db


def test_database_storage_roundtrip():
    storage = DatabaseStorage()
    name = storage.save("products/a.webp", ContentFile(b"RIFFdata", name="a.webp"))

    assert storage.exists(name) and storage.size(name) == 8
    assert storage.open(name).read() == b"RIFFdata"
    assert storage.url(name) == "/media/products/a.webp"
    assert storage.get_available_name(name) != name  # never overwrites an existing upload
    storage.delete(name)
    assert not storage.exists(name)


def test_media_view_serves_stored_file():
    DatabaseStorage().save("x/pic.webp", ContentFile(b"abc", name="pic.webp"))

    response = serve_media(RequestFactory().get("/media/x/pic.webp"), "x/pic.webp")

    assert response.content == b"abc" and response["Content-Type"] == "image/webp"
    assert "immutable" in response["Cache-Control"]


@override_settings(NOINDEX=True)
def test_noindex_headers_and_robots(api):
    res = api.get("/robots.txt")

    assert res.content.decode() == "User-agent: *\nDisallow: /"
    assert res["X-Robots-Tag"] == "noindex, nofollow"
