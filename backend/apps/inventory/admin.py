from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderLine, StockMovement, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "contact_name", "email", "phone", "is_active"]
    search_fields = ["name", "contact_name", "email"]


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    readonly_fields = ["quantity_received"]
    raw_id_fields = ["variant"]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["number", "supplier", "status", "expected_date", "created_at"]
    list_filter = ["status"]
    readonly_fields = ["number", "status", "ordered_at", "received_at"]
    inlines = [PurchaseOrderLineInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Read-only: the ledger is written only by apps.inventory.services."""

    list_display = ["created_at", "variant", "quantity_change", "balance_after", "reason", "order", "purchase_order"]
    list_filter = ["reason"]
    search_fields = ["variant__product__title", "variant__sku", "note"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
