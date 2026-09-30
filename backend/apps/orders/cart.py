import uuid

from django.db import transaction

from .models import Cart

CART_HEADER = "X-Cart-Id"


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    try:
        return uuid.UUID(value) if value else None
    except ValueError:
        return None


def get_cart(request, create: bool = False) -> Cart | None:
    """Resolve the cart for the request: the user's cart if authenticated, else the guest cart from the header."""
    if request.user.is_authenticated:
        if create:
            return Cart.objects.get_or_create(user=request.user)[0]
        return Cart.objects.filter(user=request.user).first()

    session_key = _parse_uuid(request.headers.get(CART_HEADER))
    cart = Cart.objects.filter(session_key=session_key, user__isnull=True).first() if session_key else None
    if cart is None and create:
        cart = Cart.objects.create()
    return cart


@transaction.atomic
def merge_guest_cart(user, session_key: str) -> Cart:
    """Move items from a guest cart into the user's cart, summing quantities, then delete the guest cart."""
    user_cart, _ = Cart.objects.get_or_create(user=user)
    guest = Cart.objects.filter(session_key=_parse_uuid(session_key), user__isnull=True).first()
    if guest is None:
        return user_cart
    existing = {item.variant_id: item for item in user_cart.items.all()}
    for item in guest.items.all():
        if target := existing.get(item.variant_id):
            target.quantity += item.quantity
            target.save(update_fields=["quantity"])
        else:
            item.cart = user_cart
            item.save(update_fields=["cart"])
    guest.delete()
    return user_cart
