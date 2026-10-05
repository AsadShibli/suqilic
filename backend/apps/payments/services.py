import logging
import secrets

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.orders.models import Order, OrderStatusHistory

from . import sslcommerz
from .models import Payment

logger = logging.getLogger(__name__)


def start_payment(order: Order, callback_base: str) -> str:
    """Create a Payment attempt for `order` and return the hosted checkout URL."""
    if order.payment_method != Order.PaymentMethod.ONLINE:
        raise ValidationError({"detail": "This order is cash on delivery."})
    if order.payment_status == Order.PaymentStatus.PAID:
        raise ValidationError({"detail": "This order is already paid."})
    if order.status == Order.Status.CANCELLED:
        raise ValidationError({"detail": "This order was cancelled."})

    payment = Payment.objects.create(
        order=order, tran_id=f"{order.order_number}-{secrets.token_hex(6)}", amount=order.subtotal
    )
    try:
        return sslcommerz.create_session(
            tran_id=payment.tran_id, amount=payment.amount, order=order, callback_base=callback_base
        )
    except sslcommerz.GatewayError as exc:
        payment.status = Payment.Status.FAILED
        payment.gateway_response = {"error": str(exc)}
        payment.save(update_fields=["status", "gateway_response", "updated_at"])
        raise ValidationError({"detail": str(exc)}) from exc


def settle_payment(val_id: str, claimed_tran_id: str = "") -> Payment | None:
    """Mark a payment paid after the gateway confirms it. Safe to call any number of times for the same payment.

    Called from both the browser return and the server-to-server IPN, which usually race each other.
    The gateway validation call happens before taking any lock; the payment row is then locked so only
    one caller can flip it to PAID, and a payment that's already PAID is returned untouched.
    """
    result = sslcommerz.validate(val_id)
    if claimed_tran_id and claimed_tran_id != result.tran_id:
        logger.warning("Payment callback tran_id %s does not match validated %s", claimed_tran_id, result.tran_id)
        return None

    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(tran_id=result.tran_id).first()
        if payment is None:
            logger.warning("Validated payment for unknown tran_id %s", result.tran_id)
            return None
        if payment.status == Payment.Status.PAID:
            return payment

        problem = None
        if not result.valid:
            problem = f"gateway status {result.raw.get('status')!r}"
        elif result.amount != payment.amount or result.currency != payment.currency:
            problem = f"paid {result.amount} {result.currency}, expected {payment.amount} {payment.currency}"
        if problem:
            logger.warning("Rejecting payment %s: %s", payment.tran_id, problem)
            payment.status = Payment.Status.FAILED
            payment.gateway_response = result.raw
            payment.save(update_fields=["status", "gateway_response", "updated_at"])
            return payment

        payment.status = Payment.Status.PAID
        payment.val_id = val_id
        payment.bank_tran_id = result.bank_tran_id
        payment.card_type = result.card_type
        payment.gateway_response = result.raw
        payment.paid_at = timezone.now()
        try:
            with transaction.atomic():
                payment.save()
        except IntegrityError:  # this val_id already settled a different payment
            logger.warning("val_id %s reused for %s", val_id, payment.tran_id)
            return None

        order = Order.objects.select_for_update().get(pk=payment.order_id)
        if order.payment_status != Order.PaymentStatus.PAID:
            order.payment_status = Order.PaymentStatus.PAID
            order.save(update_fields=["payment_status", "updated_at"])
            OrderStatusHistory.objects.create(
                order=order, from_status=order.status, to_status=order.status,
                note=f"Paid online: {payment.amount} {payment.currency} via {payment.card_type or 'SSLCommerz'} "
                     f"(transaction {payment.tran_id})",
            )
        return payment


@transaction.atomic
def mark_unsuccessful(tran_id: str, status: str) -> Payment | None:
    """Record a failed or cancelled attempt. Never downgrades a payment that's already been settled."""
    payment = Payment.objects.select_for_update().filter(tran_id=tran_id).first()
    if payment and payment.status == Payment.Status.INITIATED:
        payment.status = status
        payment.save(update_fields=["status", "updated_at"])
    return payment
