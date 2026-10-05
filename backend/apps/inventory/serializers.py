from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import ProductVariant

from .models import PurchaseOrder, PurchaseOrderLine, StockMovement, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    open_purchase_orders = serializers.IntegerField(read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id", "name", "contact_name", "email", "phone", "address", "notes", "is_active",
            "open_purchase_orders", "created_at",
        ]


def variant_label(variant: ProductVariant) -> str:
    title = variant.product.title
    return title if variant.title == "Default" else f"{title} ({variant.title})"


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    variant_label = serializers.SerializerMethodField()
    sku = serializers.CharField(source="variant.sku", read_only=True, default="")
    quantity_outstanding = serializers.IntegerField(read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id", "variant", "variant_label", "sku", "quantity_ordered", "quantity_received",
            "quantity_outstanding", "unit_cost",
        ]
        read_only_fields = ["quantity_received"]

    def get_variant_label(self, obj):
        return variant_label(obj.variant)

    def validate_quantity_ordered(self, value):
        if value < 1:
            raise serializers.ValidationError("Must be at least 1.")
        return value


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    line_count = serializers.IntegerField(read_only=True)
    total_cost = serializers.DecimalField(source="cost_total", max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "number", "supplier", "supplier_name", "status", "expected_date", "line_count", "total_cost",
            "created_at",
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Lines are written as a full list; edits are only allowed while the PO is a draft."""

    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    lines = PurchaseOrderLineSerializer(many=True)
    total_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    created_by = serializers.StringRelatedField()

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "number", "supplier", "supplier_name", "status", "expected_date", "notes", "lines", "total_cost",
            "created_by", "ordered_at", "received_at", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "ordered_at", "received_at"]

    def validate(self, attrs):
        if self.instance and self.instance.status != PurchaseOrder.Status.DRAFT and "lines" in attrs:
            raise serializers.ValidationError({"lines": "Lines can only be changed while the purchase order is a draft."})
        variants = [line["variant"].pk for line in attrs.get("lines", [])]
        if len(variants) != len(set(variants)):
            raise serializers.ValidationError({"lines": "Each variant can only appear once."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop("lines")
        po = PurchaseOrder.objects.create(**validated_data)
        for line in lines:
            line.pop("id", None)
        PurchaseOrderLine.objects.bulk_create([PurchaseOrderLine(purchase_order=po, **line) for line in lines])
        return po

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = validated_data.pop("lines", None)
        po = super().update(instance, validated_data)
        if lines is not None:
            po.lines.all().delete()
            for line in lines:
                line.pop("id", None)
            PurchaseOrderLine.objects.bulk_create([PurchaseOrderLine(purchase_order=po, **line) for line in lines])
        return po


class ReceiveLineSerializer(serializers.Serializer):
    line = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0)


class ReceiveSerializer(serializers.Serializer):
    lines = ReceiveLineSerializer(many=True, allow_empty=False)


class StockMovementSerializer(serializers.ModelSerializer):
    variant_label = serializers.SerializerMethodField()
    sku = serializers.CharField(source="variant.sku", read_only=True, default="")
    product_id = serializers.IntegerField(source="variant.product_id", read_only=True)
    order_number = serializers.CharField(source="order.order_number", read_only=True, default=None)
    purchase_order_number = serializers.CharField(source="purchase_order.number", read_only=True, default=None)
    created_by = serializers.StringRelatedField()

    class Meta:
        model = StockMovement
        fields = [
            "id", "variant", "variant_label", "sku", "product_id", "quantity_change", "balance_after", "reason",
            "order_number", "purchase_order_number", "note", "created_by", "created_at",
        ]

    def get_variant_label(self, obj):
        return variant_label(obj.variant)


class StockAdjustSerializer(serializers.Serializer):
    variant = serializers.PrimaryKeyRelatedField(queryset=ProductVariant.objects.all())
    quantity_change = serializers.IntegerField()
    note = serializers.CharField(max_length=255)

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError("Must not be zero.")
        return value


class VariantOptionSerializer(serializers.ModelSerializer):
    """Compact variant list for pickers (purchase order lines, adjustments)."""

    label = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = ["id", "label", "sku", "stock_quantity"]

    def get_label(self, obj):
        return variant_label(obj)
