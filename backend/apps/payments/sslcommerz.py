"""Thin client for the SSLCommerz v4 hosted-checkout API (sandbox or live)."""

from dataclasses import dataclass
from decimal import Decimal

import requests
from django.conf import settings

TIMEOUT = 20


class GatewayError(Exception):
    pass


def _base_url() -> str:
    return "https://sandbox.sslcommerz.com" if settings.SSLCOMMERZ_SANDBOX else "https://securepay.sslcommerz.com"


def is_configured() -> bool:
    return bool(settings.SSLCOMMERZ_STORE_ID and settings.SSLCOMMERZ_STORE_PASSWORD)


def create_session(*, tran_id: str, amount: Decimal, order, callback_base: str) -> str:
    """Open a hosted checkout session and return the gateway page URL to redirect the customer to."""
    payload = {
        "store_id": settings.SSLCOMMERZ_STORE_ID,
        "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
        "total_amount": f"{amount:.2f}",
        "currency": "BDT",
        "tran_id": tran_id,
        "success_url": f"{callback_base}/return/",
        "fail_url": f"{callback_base}/return/",
        "cancel_url": f"{callback_base}/return/",
        "ipn_url": f"{callback_base}/ipn/",
        "value_a": order.order_number,
        "cus_name": order.full_name,
        "cus_email": order.email,
        "cus_phone": order.phone,
        "cus_add1": order.line1,
        "cus_city": order.city,
        "cus_postcode": order.postal_code or "0000",
        "cus_country": order.country,
        "shipping_method": "Courier",
        "ship_name": order.full_name,
        "ship_add1": order.line1,
        "ship_city": order.city,
        "ship_postcode": order.postal_code or "0000",
        "ship_country": order.country,
        "product_name": f"Order {order.order_number}",
        "product_category": "Stickers",
        "product_profile": "physical-goods",
    }
    try:
        res = requests.post(f"{_base_url()}/gwprocess/v4/api.php", data=payload, timeout=TIMEOUT)
        data = res.json()
    except (requests.RequestException, ValueError) as exc:
        raise GatewayError("Payment gateway is unreachable.") from exc
    if data.get("status") != "SUCCESS" or not data.get("GatewayPageURL"):
        raise GatewayError(data.get("failedreason") or "Payment gateway rejected the request.")
    return data["GatewayPageURL"]


@dataclass
class Validation:
    valid: bool
    tran_id: str
    amount: Decimal
    currency: str
    bank_tran_id: str
    card_type: str
    raw: dict


def validate(val_id: str) -> Validation:
    """Ask SSLCommerz whether `val_id` is a genuine, completed payment. Never trust callback POST data alone."""
    params = {
        "val_id": val_id,
        "store_id": settings.SSLCOMMERZ_STORE_ID,
        "store_passwd": settings.SSLCOMMERZ_STORE_PASSWORD,
        "format": "json",
    }
    try:
        res = requests.get(f"{_base_url()}/validator/api/validationserverAPI.php", params=params, timeout=TIMEOUT)
        data = res.json()
    except (requests.RequestException, ValueError) as exc:
        raise GatewayError("Could not validate the payment.") from exc
    return Validation(
        valid=data.get("status") in ("VALID", "VALIDATED"),
        tran_id=data.get("tran_id", ""),
        amount=Decimal(str(data.get("currency_amount") or data.get("amount") or "0")),
        currency=data.get("currency_type") or data.get("currency") or "",
        bank_tran_id=data.get("bank_tran_id", ""),
        card_type=data.get("card_type", ""),
        raw=data,
    )
