from decimal import Decimal

import pytest

from apps.orders.models import Order, OrderStatusHistory
from apps.payments import sslcommerz
from apps.payments.models import Payment

from .test_orders import CUSTOMER, add_to_cart

pytestmark = pytest.mark.django_db

START = "/api/v1/payments/sslcommerz/start/"
RETURN = "/api/v1/payments/sslcommerz/return/"
IPN = "/api/v1/payments/sslcommerz/ipn/"


@pytest.fixture
def gateway(settings, monkeypatch):
    """Configured sandbox credentials, with the two HTTP calls to SSLCommerz faked."""
    settings.SSLCOMMERZ_STORE_ID, settings.SSLCOMMERZ_STORE_PASSWORD = "teststore", "secret"
    settings.FRONTEND_URL = "https://shop.test"
    fake = {"validations": {}, "validate_calls": 0}

    def create_session(*, tran_id, amount, order, callback_base):
        fake["session"] = {"tran_id": tran_id, "amount": amount, "callback_base": callback_base}
        return f"https://sandbox.sslcommerz.com/pay/{tran_id}"

    def validate(val_id):
        fake["validate_calls"] += 1
        status, tran_id, amount = fake["validations"][val_id]
        return sslcommerz.Validation(
            valid=status == "VALID", tran_id=tran_id, amount=Decimal(amount), currency="BDT",
            bank_tran_id="BANK1", card_type="BKASH-BKash", raw={"status": status, "tran_id": tran_id},
        )

    monkeypatch.setattr(sslcommerz, "create_session", create_session)
    monkeypatch.setattr(sslcommerz, "validate", validate)
    return fake


@pytest.fixture
def online_order(api, make_product, gateway):
    variant = make_product(prices=(Decimal("279.00"),), stock=5).variants.get()
    cart_id = add_to_cart(api, variant.id, 2)["X-Cart-Id"]
    res = api.post("/api/v1/orders/", {**CUSTOMER, "payment_method": "online"}, format="json", HTTP_X_CART_ID=cart_id)
    assert res.status_code == 201, res.data
    assert res.data["payment_status"] == "unpaid"
    return Order.objects.get(order_number=res.data["order_number"])


def start(api, order):
    res = api.post(START, {"order_number": order.order_number, "email": order.email}, format="json")
    assert res.status_code == 200, res.data
    return Payment.objects.get(order=order, status="initiated")


def test_successful_payment_redirects_back_and_marks_order_paid(api, online_order, gateway):
    payment = start(api, online_order)
    assert payment.amount == Decimal("558.00") and gateway["session"]["callback_base"].endswith("/payments/sslcommerz")
    gateway["validations"]["VAL1"] = ("VALID", payment.tran_id, "558.00")

    res = api.post(RETURN, {"status": "VALID", "tran_id": payment.tran_id, "val_id": "VAL1"})

    assert res.status_code == 302
    assert res["Location"] == f"https://shop.test/payment/result?result=paid&order={online_order.order_number}"
    online_order.refresh_from_db()
    assert online_order.payment_status == "paid"
    payment.refresh_from_db()
    assert payment.status == "paid" and payment.val_id == "VAL1" and payment.paid_at


def test_repeated_callbacks_settle_only_once(api, online_order, gateway):
    payment = start(api, online_order)
    gateway["validations"]["VAL1"] = ("VALID", payment.tran_id, "558.00")
    body = {"status": "VALID", "tran_id": payment.tran_id, "val_id": "VAL1"}

    api.post(RETURN, body)
    for _ in range(3):  # gateway retries the IPN, customer refreshes the return page...
        assert api.post(IPN, body).status_code == 200
    api.post(RETURN, body)

    assert Payment.objects.filter(status="paid").count() == 1
    assert OrderStatusHistory.objects.filter(order=online_order, note__startswith="Paid online").count() == 1


def test_amount_mismatch_is_rejected(api, online_order, gateway):
    payment = start(api, online_order)
    gateway["validations"]["VAL1"] = ("VALID", payment.tran_id, "1.00")

    res = api.post(IPN, {"status": "VALID", "tran_id": payment.tran_id, "val_id": "VAL1"})

    assert res.status_code == 200
    assert Payment.objects.get(pk=payment.pk).status == "failed"
    assert Order.objects.get(pk=online_order.pk).payment_status == "unpaid"


def test_forged_callback_cannot_mark_paid(api, online_order, gateway):
    """Callback POST data is only a hint: the gateway says this val_id belongs to another, failed transaction."""
    payment = start(api, online_order)
    gateway["validations"]["FAKE"] = ("INVALID_TRANSACTION", payment.tran_id, "558.00")

    res = api.post(RETURN, {"status": "VALID", "tran_id": payment.tran_id, "val_id": "FAKE"})

    assert "result=failed" in res["Location"]
    assert Order.objects.get(pk=online_order.pk).payment_status == "unpaid"


def test_one_validation_cannot_settle_two_payments(api, online_order, gateway):
    first = start(api, online_order)
    gateway["validations"]["VAL1"] = ("VALID", first.tran_id, "558.00")
    api.post(IPN, {"status": "VALID", "tran_id": first.tran_id, "val_id": "VAL1"})

    Order.objects.filter(pk=online_order.pk).update(payment_status="unpaid")  # pretend it needs paying again
    second = start(api, online_order)
    gateway["validations"]["VAL1"] = ("VALID", second.tran_id, "558.00")  # replay the same val_id
    api.post(IPN, {"status": "VALID", "tran_id": second.tran_id, "val_id": "VAL1"})

    assert Payment.objects.get(pk=second.pk).status == "initiated"


def test_cancel_then_retry(api, online_order, gateway):
    payment = start(api, online_order)
    res = api.post(RETURN, {"status": "CANCELLED", "tran_id": payment.tran_id})
    assert "result=cancelled" in res["Location"] and Payment.objects.get(pk=payment.pk).status == "cancelled"

    retry = start(api, online_order)
    assert retry.pk != payment.pk


def test_start_requires_matching_email_and_online_order(api, online_order, make_product, gateway):
    res = api.post(START, {"order_number": online_order.order_number, "email": "x@example.com"}, format="json")
    assert res.status_code == 404

    variant = make_product(title="Other").variants.get()
    cart_id = add_to_cart(api, variant.id)["X-Cart-Id"]
    cod = api.post("/api/v1/orders/", CUSTOMER, format="json", HTTP_X_CART_ID=cart_id).data
    assert cod["payment_method"] == "cod"
    res = api.post(START, {"order_number": cod["order_number"], "email": CUSTOMER["email"]}, format="json")
    assert res.status_code == 400


def test_online_payment_unavailable_without_credentials(api, make_product):
    assert api.get("/api/v1/payments/config/").data == {"online_payments": False}
    variant = make_product().variants.get()
    cart_id = add_to_cart(api, variant.id)["X-Cart-Id"]
    res = api.post("/api/v1/orders/", {**CUSTOMER, "payment_method": "online"}, format="json", HTTP_X_CART_ID=cart_id)
    assert res.status_code == 400 and "payment_method" in res.data
