from django.db import models

from apps.core.models import TimeStampedModel


class Payment(TimeStampedModel):
    """One attempt to pay an order online. An order may have several (e.g. a failed card, then a retry)."""

    class Status(models.TextChoices):
        INITIATED = "initiated"
        PAID = "paid"
        FAILED = "failed"
        CANCELLED = "cancelled"

    order = models.ForeignKey("orders.Order", related_name="payments", on_delete=models.PROTECT)
    provider = models.CharField(max_length=20, default="sslcommerz")
    tran_id = models.CharField(max_length=40, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INITIATED, db_index=True)
    # Unique: one gateway validation can settle at most one payment, so a replayed val_id is rejected.
    val_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    bank_tran_id = models.CharField(max_length=80, blank=True)
    card_type = models.CharField(max_length=50, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.tran_id} ({self.status})"
