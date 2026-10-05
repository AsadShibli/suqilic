from django.conf import settings
from django.db import models
from django.db.models import F, Sum

from apps.core.models import TimeStampedModel


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    contact_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(TimeStampedModel):
    """Stock bought from a supplier. Draft -> ordered -> (partially) received; stock only moves on receipt."""

    class Status(models.TextChoices):
        DRAFT = "draft"
        ORDERED = "ordered"
        PARTIALLY_RECEIVED = "partially_received"
        RECEIVED = "received"
        CANCELLED = "cancelled"

    number = models.CharField(max_length=20, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, related_name="purchase_orders", on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ordered_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            self.number = f"PO-{self.pk:06d}"
            super().save(update_fields=["number"])

    @property
    def total_cost(self):
        return self.lines.aggregate(total=Sum(F("quantity_ordered") * F("unit_cost")))["total"] or 0


class PurchaseOrderLine(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name="lines", on_delete=models.CASCADE)
    variant = models.ForeignKey("catalog.ProductVariant", related_name="purchase_lines", on_delete=models.PROTECT)
    quantity_ordered = models.PositiveIntegerField()
    quantity_received = models.PositiveIntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(fields=["purchase_order", "variant"], name="uniq_po_variant"),
            models.CheckConstraint(
                condition=models.Q(quantity_received__lte=F("quantity_ordered")), name="po_line_not_over_received"
            ),
        ]

    def __str__(self):
        return f"{self.quantity_ordered} x {self.variant}"

    @property
    def quantity_outstanding(self):
        return self.quantity_ordered - self.quantity_received


class StockMovement(models.Model):
    """Append-only ledger: one row per stock change, with the resulting balance. Never edited or deleted."""

    class Reason(models.TextChoices):
        SALE = "sale"
        ORDER_CANCELLED = "order_cancelled"
        PURCHASE_RECEIVED = "purchase_received"
        ADJUSTMENT = "adjustment"

    variant = models.ForeignKey("catalog.ProductVariant", related_name="stock_movements", on_delete=models.CASCADE)
    quantity_change = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=20, choices=Reason.choices, db_index=True)
    order = models.ForeignKey(
        "orders.Order", null=True, blank=True, related_name="stock_movements", on_delete=models.SET_NULL
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder, null=True, blank=True, related_name="stock_movements", on_delete=models.SET_NULL
    )
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["variant", "-created_at"])]

    def __str__(self):
        return f"{self.quantity_change:+d} {self.variant} ({self.reason})"
