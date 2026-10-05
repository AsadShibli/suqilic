from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["tran_id", "order", "amount", "status", "card_type", "paid_at", "created_at"]
    list_filter = ["status", "provider"]
    search_fields = ["tran_id", "val_id", "bank_tran_id", "order__order_number"]
    readonly_fields = [f.name for f in Payment._meta.fields]

    def has_add_permission(self, request):
        return False
