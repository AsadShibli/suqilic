from decimal import Decimal

import pytest

from apps.catalog.models import ProductVariant

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db

ADMIN_ENDPOINTS = [
    "/api/v1/admin/products/", "/api/v1/admin/collections/", "/api/v1/admin/orders/",
    "/api/v1/admin/customers/", "/api/v1/admin/messages/", "/api/v1/admin/settings/",
    "/api/v1/admin/dashboard/stats/", "/api/v1/admin/home-sections/", "/api/v1/admin/menu-items/",
    "/api/v1/admin/pages/", "/api/v1/admin/subscribers/", "/api/v1/admin/tags/",
]


@pytest.mark.parametrize("url", ADMIN_ENDPOINTS)
def test_admin_endpoints_reject_anonymous_and_customers(api, customer_api, staff_api, url):
    assert api.get(url).status_code == 401
    assert customer_api.get(url).status_code == 403
    assert staff_api.get(url).status_code == 200


def test_staff_cannot_manage_staff(staff_api):
    assert staff_api.get("/api/v1/admin/staff/").status_code == 403


def test_admin_login_rejects_customers(api, customer, staff):
    assert api.post("/api/v1/auth/admin/login/", {"email": customer.email, "password": PASSWORD}).status_code == 401
    assert api.post("/api/v1/auth/admin/login/", {"email": staff.email, "password": PASSWORD}).status_code == 200


def test_product_crud_with_options_variants_and_images(staff_api, collection, image_file):
    res = staff_api.post("/api/v1/admin/products/", {
        "title": "Why Would I Brake Check You", "base_price": "8.99", "status": "active",
        "collection_ids": [collection.id],
    }, format="json")
    assert res.status_code == 201, res.data
    pid = res.data["id"]
    assert res.data["slug"] == "why-would-i-brake-check-you" and res.data["collection_ids"] == [collection.id]

    base = f"/api/v1/admin/products/{pid}"
    assert staff_api.post(f"{base}/options/", {"name": "Size", "values": ["S", "L"]}, format="json").status_code == 201
    assert staff_api.post(f"{base}/variants/generate/").data == {"created": 2}
    assert list(ProductVariant.objects.filter(product_id=pid).values_list("title", flat=True)) == ["S", "L"]

    img = staff_api.post(f"{base}/images/", {"image": image_file, "is_main": True}, format="multipart")
    assert img.status_code == 201 and img.data["thumbnail"]

    dup = staff_api.post(f"{base}/duplicate/")
    assert dup.status_code == 201 and dup.data["status"] == "draft" and len(dup.data["variants"]) == 2

    renamed = staff_api.patch(f"{base}/", {"title": "Renamed"}, format="json")
    assert renamed.data["slug"] == "why-would-i-brake-check-you"
    assert staff_api.get(f"/api/v1/admin/collections/{collection.id}/products/").data[0]["id"] == pid
    assert staff_api.post("/api/v1/admin/products/bulk-delete/", {"ids": [pid]}, format="json").data["deleted"] >= 1


def test_order_status_change_and_cancel_restocks(api, staff_api, make_product):
    variant = make_product(prices=(Decimal("5"),), stock=3).variants.get()
    cart_id = api.post("/api/v1/cart/items/", {"variant_id": variant.id, "quantity": 2}, format="json")["X-Cart-Id"]
    api.post("/api/v1/orders/", {
        "full_name": "A", "email": "a@a.com", "phone": "1", "line1": "x", "city": "y", "country": "z",
    }, format="json", HTTP_X_CART_ID=cart_id)
    order_id = staff_api.get("/api/v1/admin/orders/").data["results"][0]["id"]

    res = staff_api.post(f"/api/v1/admin/orders/{order_id}/status/", {"status": "cancelled"}, format="json")

    assert res.data["status"] == "cancelled" and len(res.data["status_history"]) == 1
    assert ProductVariant.objects.get(pk=variant.pk).stock_quantity == 3
    reopen = staff_api.post(f"/api/v1/admin/orders/{order_id}/status/", {"status": "pending"}, format="json")
    assert reopen.status_code == 400
    assert staff_api.get("/api/v1/admin/orders/export/").status_code == 200
