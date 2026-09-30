import pytest

from apps.catalog.models import ProductVariant
from apps.orders.models import Order

pytestmark = pytest.mark.django_db

CUSTOMER = {
    "full_name": "Ada Lovelace", "email": "ada@example.com", "phone": "123",
    "line1": "1 Road", "city": "London", "country": "UK",
}


def add_to_cart(client, variant_id, quantity=1):
    return client.post("/api/v1/cart/items/", {"variant_id": variant_id, "quantity": quantity}, format="json")


def test_guest_cart_to_order_request(api, make_product, mailoutbox, django_capture_on_commit_callbacks):
    variant = make_product(stock=5).variants.get()

    res = add_to_cart(api, variant.id, 2)
    cart_id = res["X-Cart-Id"]
    assert res.status_code == 201 and res.data["item_count"] == 2

    with django_capture_on_commit_callbacks(execute=True):
        order = api.post("/api/v1/orders/", CUSTOMER, format="json", HTTP_X_CART_ID=cart_id)

    assert order.status_code == 201, order.data
    assert order.data["order_number"].startswith("SQ-") and order.data["subtotal"] == "17.98"
    assert ProductVariant.objects.get(pk=variant.pk).stock_quantity == 3
    assert api.get("/api/v1/cart/", HTTP_X_CART_ID=cart_id).data["item_count"] == 0
    assert len(mailoutbox) == 2

    track = api.get("/api/v1/orders/track/", {"order_number": order.data["order_number"], "email": "ADA@example.com"})
    assert track.status_code == 200


def test_cannot_add_more_than_stock(api, make_product):
    variant = make_product(stock=1).variants.get()
    assert add_to_cart(api, variant.id, 2).status_code == 400


def test_order_rejected_when_stock_ran_out(api, make_product):
    variant = make_product(stock=2).variants.get()
    cart_id = add_to_cart(api, variant.id, 2)["X-Cart-Id"]
    ProductVariant.objects.filter(pk=variant.pk).update(stock_quantity=1)

    res = api.post("/api/v1/orders/", CUSTOMER, format="json", HTTP_X_CART_ID=cart_id)

    assert res.status_code == 400 and Order.objects.count() == 0


def test_guest_cart_merges_into_user_cart(api, customer_api, make_product):
    variant = make_product().variants.get()
    cart_id = add_to_cart(api, variant.id, 1)["X-Cart-Id"]
    add_to_cart(customer_api, variant.id, 1)

    res = customer_api.post("/api/v1/cart/merge/", {"cart_id": cart_id}, format="json")

    assert res.data["item_count"] == 2
    assert customer_api.get("/api/v1/me/orders/").status_code == 200
