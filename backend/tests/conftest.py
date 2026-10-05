import io
from decimal import Decimal

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.catalog.models import Collection, CollectionProduct, Product, ProductVariant

PASSWORD = "S3cure-pass!"


@pytest.fixture(autouse=True)
def _isolate(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.TASKS_THREAD_FALLBACK = False  # run background tasks inline so tests are deterministic
    cache.clear()


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def customer(db):
    return User.objects.create_user("buyer@example.com", PASSWORD)


@pytest.fixture
def staff(db):
    return User.objects.create_user("staff@example.com", PASSWORD, is_staff=True)


@pytest.fixture
def staff_api(staff):
    client = APIClient()
    client.force_authenticate(staff)
    return client


@pytest.fixture
def customer_api(customer):
    client = APIClient()
    client.force_authenticate(customer)
    return client


@pytest.fixture
def image_file():
    buffer = io.BytesIO()
    Image.new("RGB", (40, 40), "white").save(buffer, "PNG")
    return SimpleUploadedFile("pic.png", buffer.getvalue(), content_type="image/png")


@pytest.fixture
def collection(db):
    return Collection.objects.create(title="Bumper Stickers", slug="bumper-stickers")


@pytest.fixture
def make_product(db):
    def _make(title="Sticker", prices=(Decimal("8.99"),), stock=10, status=Product.Status.ACTIVE, collection=None):
        product = Product.objects.create(
            title=title, slug=title.lower().replace(" ", "-"), base_price=prices[0], status=status
        )
        for i, price in enumerate(prices):
            ProductVariant.objects.create(product=product, title=f"V{i}", price=price, stock_quantity=stock, position=i)
        if collection:
            CollectionProduct.objects.create(
                collection=collection, product=product, position=collection.collection_products.count()
            )
        return product

    return _make
