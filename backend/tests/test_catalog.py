from decimal import Decimal

import pytest

from apps.catalog.models import Product
from apps.storefront.models import HomeSection

pytestmark = pytest.mark.django_db


def test_product_list_hides_drafts_and_reports_price_range(api, make_product):
    make_product("Private Property", prices=(Decimal("8.99"), Decimal("12.99")))
    make_product("Hidden", status=Product.Status.DRAFT)

    res = api.get("/api/v1/products/")

    assert res.status_code == 200
    assert [p["title"] for p in res.data["results"]] == ["Private Property"]
    card = res.data["results"][0]
    assert card["price_from"] == "8.99" and card["has_price_range"] is True and card["in_stock"] is True


def test_collection_products_featured_order_and_filters(api, make_product, collection):
    make_product("B", prices=(Decimal("5"),), collection=collection)
    make_product("A", prices=(Decimal("9"),), stock=0, collection=collection)
    url = "/api/v1/collections/bumper-stickers/products/"

    assert [p["title"] for p in api.get(url).data["results"]] == ["B", "A"]
    assert [p["title"] for p in api.get(f"{url}?ordering=-price").data["results"]] == ["A", "B"]
    assert [p["title"] for p in api.get(f"{url}?in_stock=true").data["results"]] == ["B"]
    assert api.get(f"{url}?ordering=best_selling").status_code == 200


def test_product_detail_and_search(api, make_product, collection):
    make_product("Luigi", collection=collection)

    detail = api.get("/api/v1/products/luigi/")
    search = api.get("/api/v1/search/?q=bumper")
    suggest = api.get("/api/v1/search/suggest/?q=lu")

    assert detail.status_code == 200 and len(detail.data["variants"]) == 1
    assert detail.data["collections"] == [{"title": "Bumper Stickers", "slug": "bumper-stickers"}]
    assert search.data["count"] == 1
    assert suggest.data["products"][0]["slug"] == "luigi"


def test_home_returns_carousel_products(api, make_product, collection):
    make_product("Luigi", collection=collection)
    HomeSection.objects.create(type="product_carousel", title="BUMPER STiCKERS", collection=collection)

    res = api.get("/api/v1/home/")

    assert res.data[0]["products"][0]["title"] == "Luigi"
    assert res.data[0]["view_all_link"] == "/collections/bumper-stickers"
