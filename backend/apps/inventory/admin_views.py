from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

from apps.catalog.models import ProductVariant
from apps.core.mixins import AdminModelViewSet, CsvExportMixin
from apps.core.permissions import IsStaff

from . import services
from .models import PurchaseOrder, StockMovement, Supplier
from .serializers import (
    PurchaseOrderListSerializer,
    PurchaseOrderSerializer,
    ReceiveSerializer,
    StockAdjustSerializer,
    StockMovementSerializer,
    SupplierSerializer,
    VariantOptionSerializer,
)

OPEN_PO_STATUSES = [PurchaseOrder.Status.ORDERED, PurchaseOrder.Status.PARTIALLY_RECEIVED]


class SupplierAdminViewSet(AdminModelViewSet):
    serializer_class = SupplierSerializer
    search_fields = ["name", "contact_name", "email", "phone"]
    filterset_fields = ["is_active"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return Supplier.objects.annotate(
            open_purchase_orders=Count("purchase_orders", filter=Q(purchase_orders__status__in=OPEN_PO_STATUSES))
        )

    def perform_destroy(self, instance):
        if instance.purchase_orders.exists():
            raise ValidationError({"detail": "This supplier has purchase orders; mark it inactive instead."})
        instance.delete()


class PurchaseOrderAdminViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsStaff]
    search_fields = ["number", "supplier__name", "notes"]
    filterset_fields = {"status": ["exact"], "supplier": ["exact"]}
    ordering_fields = ["created_at", "expected_date", "number"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related("supplier", "created_by")
        if self.action == "list":
            money = DecimalField(max_digits=12, decimal_places=2)
            line_cost = ExpressionWrapper(F("lines__quantity_ordered") * F("lines__unit_cost"), output_field=money)
            return qs.annotate(line_count=Count("lines"), cost_total=Coalesce(Sum(line_cost), 0, output_field=money))
        return qs.prefetch_related("lines__variant__product")

    def get_serializer_class(self):
        return PurchaseOrderListSerializer if self.action == "list" else PurchaseOrderSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.status != PurchaseOrder.Status.DRAFT:
            raise ValidationError({"detail": "Only draft purchase orders can be deleted; cancel it instead."})
        instance.delete()

    def _detail(self, po):
        return Response(PurchaseOrderSerializer(self.get_queryset().get(pk=po.pk)).data)

    @action(detail=True, methods=["post"], url_path="mark-ordered")
    def mark_ordered(self, request, pk=None):
        return self._detail(services.mark_ordered(self.get_object()))

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        s = ReceiveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        quantities = {}
        for row in s.validated_data["lines"]:
            quantities[row["line"]] = quantities.get(row["line"], 0) + row["quantity"]
        return self._detail(services.receive_purchase_order(self.get_object(), quantities, user=request.user))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._detail(services.cancel_purchase_order(self.get_object()))


class StockMovementAdminViewSet(CsvExportMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only ledger, plus a manual adjustment endpoint. Rows are never edited or deleted."""

    permission_classes = [IsStaff]
    serializer_class = StockMovementSerializer
    filterset_fields = {
        "reason": ["exact"], "variant": ["exact"], "variant__product": ["exact"], "created_at": ["gte", "lte"],
    }
    search_fields = ["variant__product__title", "variant__sku", "note", "order__order_number", "purchase_order__number"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at", "-id"]
    csv_filename = "stock-movements.csv"
    csv_fields = [
        ("Date", "created_at"), ("Product", lambda m: m.variant.product.title), ("Variant", lambda m: m.variant.title),
        ("SKU", lambda m: m.variant.sku or ""), ("Change", "quantity_change"), ("Balance", "balance_after"),
        ("Reason", "reason"), ("Order", lambda m: m.order.order_number if m.order else ""),
        ("Purchase order", lambda m: m.purchase_order.number if m.purchase_order else ""), ("Note", "note"),
        ("By", lambda m: m.created_by or ""),
    ]

    def get_queryset(self):
        return StockMovement.objects.select_related("variant__product", "order", "purchase_order", "created_by")

    @action(detail=False, methods=["post"])
    def adjust(self, request):
        s = StockAdjustSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        with transaction.atomic():
            movement = services.move_stock(
                s.validated_data["variant"].pk, s.validated_data["quantity_change"], StockMovement.Reason.ADJUSTMENT,
                user=request.user, note=s.validated_data["note"],
            )
        data = StockMovementSerializer(self.get_queryset().get(pk=movement.pk)).data
        return Response(data, status=status.HTTP_201_CREATED)


class VariantOptionsView(ListAPIView):
    """Searchable variant picker for purchase-order lines and stock adjustments."""

    permission_classes = [IsStaff]
    serializer_class = VariantOptionSerializer
    search_fields = ["product__title", "title", "sku"]
    filterset_fields = []
    ordering_fields = ["stock_quantity"]
    ordering = ["product__title", "position"]

    def get_queryset(self):
        return ProductVariant.objects.select_related("product").exclude(product__status="archived")
