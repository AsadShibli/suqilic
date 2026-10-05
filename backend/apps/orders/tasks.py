from celery import shared_task
from django.conf import settings

from apps.core.emails import send_templated_email

from .models import Order


@shared_task
def send_order_emails(order_id: int) -> None:
    """Confirmation to the customer and a heads-up to the shop. Takes an id: tasks must not carry model instances."""
    order = Order.objects.filter(pk=order_id).prefetch_related("items").first()
    if order is None:
        return
    context = {"order": order, "items": order.items.all()}
    send_templated_email("order_customer", context, [order.email], f"We received your order {order.order_number}")
    send_templated_email("order_admin", context, [settings.STORE_ADMIN_EMAIL], f"New order request {order.order_number}")
