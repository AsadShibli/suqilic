from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product, ProductVariant
from apps.core.mixins import BulkDeleteMixin, CsvExportMixin
from apps.core.models import ContactMessage
from apps.core.permissions import IsStaff

from .models import Order
from .serializers import OrderItemSerializer, OrderStatusHistorySerializer
from .services import change_order_status

LOW_STOCK_THRESHOLD = 5


class OrderAdminListSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "order_number", "status", "full_name", "email", "phone", "subtotal", "item_count", "created_at"]


class OrderAdminSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [f.name for f in Order._meta.fields if f.name != "internal_note"]


class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")
    notify_customer = serializers.BooleanField(default=False)


class OrderAdminViewSet(
    CsvExportMixin,
    BulkDeleteMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Orders are created from the storefront; staff can view, annotate, change status, export."""

    permission_classes = [IsStaff]
    http_method_names = ["get", "patch", "delete", "post"]
    filterset_fields = {"status": ["exact"], "created_at": ["gte", "lte"]}
    search_fields = ["order_number", "full_name", "email", "phone"]
    ordering_fields = ["created_at", "subtotal", "status"]
    ordering = ["-created_at"]
    csv_filename = "orders.csv"
    csv_fields = [
        ("Order", "order_number"), ("Status", "status"), ("Date", "created_at"), ("Name", "full_name"),
        ("Email", "email"), ("Phone", "phone"),
        ("Address", lambda o: ", ".join(filter(None, [o.line1, o.line2, o.city, o.region, o.postal_code, o.country]))),
        ("Items", lambda o: "; ".join(f"{i.quantity}x {i.product_title} ({i.variant_title})" for i in o.items.all())),
        ("Subtotal", "subtotal"), ("Customer note", "customer_note"),
    ]

    def get_queryset(self):
        qs = Order.objects.all()
        if self.action == "list":
            return qs.annotate(item_count=Sum("items__quantity"))
        return qs.prefetch_related("items__variant__product", "status_history__changed_by")

    def get_serializer_class(self):
        return OrderAdminListSerializer if self.action == "list" else OrderAdminSerializer

    @action(detail=True, methods=["post"])
    def status(self, request, pk=None):
        order = self.get_object()
        s = OrderStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        change_order_status(
            order, s.validated_data["status"], request.user,
            note=s.validated_data["note"], notify=s.validated_data["notify_customer"],
        )
        return Response(OrderAdminSerializer(self.get_queryset().get(pk=order.pk)).data)


class DashboardStatsView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        orders = Order.objects.aggregate(
            pending=Count("id", filter=Q(status=Order.Status.PENDING)),
            this_week=Count("id", filter=Q(created_at__gte=week_ago)),
            revenue_this_week=Sum("subtotal", filter=Q(created_at__gte=week_ago) & ~Q(status=Order.Status.CANCELLED)),
        )
        return Response({
            "pending_orders": orders["pending"],
            "orders_this_week": orders["this_week"],
            "revenue_this_week": orders["revenue_this_week"] or 0,
            "total_products": Product.objects.exclude(status=Product.Status.ARCHIVED).count(),
            "low_stock_variants": ProductVariant.objects.filter(
                is_active=True, product__status=Product.Status.ACTIVE, stock_quantity__lte=LOW_STOCK_THRESHOLD
            ).count(),
            "unread_messages": ContactMessage.objects.filter(is_read=False).count(),
        })


class RecentOrdersView(APIView):
    permission_classes = [IsStaff]

    def get(self, request):
        orders = Order.objects.annotate(item_count=Sum("items__quantity")).order_by("-created_at")[:10]
        return Response(OrderAdminListSerializer(orders, many=True).data)

