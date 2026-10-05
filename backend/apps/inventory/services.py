"""The only code allowed to change ProductVariant.stock_quantity. Every change writes a StockMovement."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.catalog.models import ProductVariant
from apps.core.cache import invalidate_public_cache

from .models import PurchaseOrder, StockMovement

Reason = StockMovement.Reason


def move_stock(variant_id: int, change: int, reason: str, *, user=None, order=None, purchase_order=None,
               note: str = "") -> StockMovement:
    """Apply a signed stock change under a row lock and record it. Must run inside a transaction."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("move_stock() must be called inside transaction.atomic()")
    variant = ProductVariant.objects.select_for_update().get(pk=variant_id)
    new_balance = variant.stock_quantity + change
    if new_balance < 0:
        raise ValidationError({"stock": f"Not enough stock for {variant} (have {variant.stock_quantity})."})
    ProductVariant.objects.filter(pk=variant_id).update(stock_quantity=new_balance)
    transaction.on_commit(invalidate_public_cache)
    return StockMovement.objects.create(
        variant_id=variant_id, quantity_change=change, balance_after=new_balance, reason=reason,
        order=order, purchase_order=purchase_order, note=note[:255], created_by=user,
    )


@transaction.atomic
def set_stock(variant_id: int, new_quantity: int, *, user=None, note: str = "") -> StockMovement | None:
    """A manual stock count or edit from the admin, recorded as an adjustment of the difference."""
    current = ProductVariant.objects.select_for_update().values_list("stock_quantity", flat=True).get(pk=variant_id)
    if new_quantity == current:
        return None
    return move_stock(variant_id, new_quantity - current, Reason.ADJUSTMENT, user=user, note=note or "Manual edit")


@transaction.atomic
def mark_ordered(po: PurchaseOrder) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(pk=po.pk)
    if po.status != PurchaseOrder.Status.DRAFT:
        raise ValidationError({"status": "Only a draft purchase order can be marked as ordered."})
    if not po.lines.exists():
        raise ValidationError({"lines": "Add at least one line first."})
    po.status, po.ordered_at = PurchaseOrder.Status.ORDERED, timezone.now()
    po.save(update_fields=["status", "ordered_at", "updated_at"])
    return po


@transaction.atomic
def receive_purchase_order(po: PurchaseOrder, quantities: dict[int, int], *, user=None) -> PurchaseOrder:
    """Book delivered goods into stock. `quantities` maps line id -> units received now (partial deliveries ok).

    The PO row is locked first, so two staff submitting the same delivery at once can't double-count it.
    """
    po = PurchaseOrder.objects.select_for_update().select_related("supplier").get(pk=po.pk)
    if po.status not in (PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED):
        raise ValidationError({"status": f"Cannot receive a {po.get_status_display().lower()} purchase order."})
    lines = {line.id: line for line in po.lines.select_related("variant__product")}
    errors = {}
    for line_id, qty in quantities.items():
        line = lines.get(line_id)
        if line is None:
            errors[str(line_id)] = "Not a line on this purchase order."
        elif qty > line.quantity_outstanding:
            errors[str(line_id)] = f"Only {line.quantity_outstanding} outstanding for {line.variant}."
    if errors:
        raise ValidationError({"lines": errors})
    if not any(quantities.values()):
        raise ValidationError({"lines": "Enter a received quantity for at least one line."})

    for line_id, qty in quantities.items():
        if qty:
            line = lines[line_id]
            move_stock(line.variant_id, qty, Reason.PURCHASE_RECEIVED, user=user, purchase_order=po,
                       note=f"{po.number} from {po.supplier}")
            line.quantity_received += qty
            line.save(update_fields=["quantity_received"])

    fully_received = all(line.quantity_outstanding == 0 for line in lines.values())
    po.status = PurchaseOrder.Status.RECEIVED if fully_received else PurchaseOrder.Status.PARTIALLY_RECEIVED
    po.received_at = timezone.now() if fully_received else None
    po.save(update_fields=["status", "received_at", "updated_at"])
    return po


@transaction.atomic
def cancel_purchase_order(po: PurchaseOrder) -> PurchaseOrder:
    po = PurchaseOrder.objects.select_for_update().get(pk=po.pk)
    if po.status not in (PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.ORDERED):
        raise ValidationError({"status": "Only a draft or ordered purchase order (nothing received) can be cancelled."})
    po.status = PurchaseOrder.Status.CANCELLED
    po.save(update_fields=["status", "updated_at"])
    return po
