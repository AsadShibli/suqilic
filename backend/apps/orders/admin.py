from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["variant", "product_title", "variant_title", "sku", "unit_price", "quantity", "line_total"]


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "note", "changed_by", "changed_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "full_name", "email", "status", "subtotal", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "full_name", "email", "phone"]
    readonly_fields = ["order_number", "subtotal", "created_at", "updated_at"]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
