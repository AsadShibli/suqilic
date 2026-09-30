from django.conf import settings
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Product, ProductVariant
from apps.core.emails import send_templated_email

from .models import Cart, Order, OrderItem, OrderStatusHistory


@transaction.atomic
def place_order(cart: Cart, customer: dict, user=None) -> Order:
    """Turn a cart into a pending order request: lock stock, snapshot prices, decrement stock, clear cart."""
    items = list(cart.items.select_related("variant__product"))
    if not items:
        raise ValidationError({"detail": "Your cart is empty."})

    variants = ProductVariant.objects.select_for_update(of=("self",)).select_related("product").in_bulk([i.variant_id for i in items])
    errors = []
    for item in items:
        variant = variants[item.variant_id]
        if not variant.is_active or variant.product.status != Product.Status.ACTIVE:
            errors.append(f"{variant.product.title} is no longer available.")
        elif variant.stock_quantity < item.quantity:
            errors.append(f"Only {variant.stock_quantity} left of {variant.product.title} ({variant.title}).")
    if errors:
        raise ValidationError({"items": errors})

    order = Order.objects.create(user=user, **customer)
    order_items = [
        OrderItem(
            order=order,
            variant=item.variant,
            product_title=item.variant.product.title,
            variant_title=item.variant.title,
            sku=item.variant.sku or "",
            unit_price=item.variant.price,
            quantity=item.quantity,
            line_total=item.variant.price * item.quantity,
        )
        for item in items
    ]
    OrderItem.objects.bulk_create(order_items)
    for item in items:
        ProductVariant.objects.filter(pk=item.variant_id).update(stock_quantity=F("stock_quantity") - item.quantity)

    order.subtotal = sum(i.line_total for i in order_items)
    order.save(update_fields=["subtotal"])
    cart.items.all().delete()

    transaction.on_commit(lambda: _send_order_emails(order))
    return order


def _send_order_emails(order: Order) -> None:
    context = {"order": order, "items": order.items.all()}
    send_templated_email("order_customer", context, [order.email], f"We received your order {order.order_number}")
    send_templated_email("order_admin", context, [settings.STORE_ADMIN_EMAIL], f"New order request {order.order_number}")


@transaction.atomic
def change_order_status(order: Order, new_status: str, changed_by, note: str = "", notify: bool = False) -> Order:
    if new_status == order.status:
        return order
    if order.status == Order.Status.CANCELLED:
        raise ValidationError({"status": "A cancelled order cannot be reopened."})
    OrderStatusHistory.objects.create(
        order=order, from_status=order.status, to_status=new_status, note=note, changed_by=changed_by
    )
    if new_status == Order.Status.CANCELLED:
        _restock(order)
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])
    if notify:
        transaction.on_commit(lambda: send_templated_email(
            "order_status", {"order": order, "note": note}, [order.email],
            f"Your order {order.order_number} is {order.get_status_display().lower()}",
        ))
    return order


def _restock(order: Order) -> None:
    for item in order.items.exclude(variant=None):
        ProductVariant.objects.filter(pk=item.variant_id).update(stock_quantity=F("stock_quantity") + item.quantity)
