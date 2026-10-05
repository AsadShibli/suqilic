from rest_framework import serializers

from apps.catalog.models import Product, ProductVariant

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory


class CartItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source="variant.product.title", read_only=True)
    product_slug = serializers.CharField(source="variant.product.slug", read_only=True)
    variant_title = serializers.CharField(source="variant.title", read_only=True)
    unit_price = serializers.DecimalField(source="variant.price", max_digits=10, decimal_places=2, read_only=True)
    stock_quantity = serializers.IntegerField(source="variant.stock_quantity", read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id", "variant", "quantity", "product_title", "product_slug", "variant_title",
            "unit_price", "stock_quantity", "line_total", "image",
        ]

    def get_image(self, obj):
        images = list(obj.variant.product.images.all())
        if not images:
            return None
        request = self.context.get("request")
        url = (images[0].thumbnail or images[0].image).url
        return request.build_absolute_uri(url) if request else url


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="session_key", read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "subtotal", "item_count"]

    def get_item_count(self, obj):
        return sum(i.quantity for i in obj.items.all())


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.PrimaryKeyRelatedField(
        source="variant",
        queryset=ProductVariant.objects.filter(is_active=True, product__status=Product.Status.ACTIVE),
    )
    quantity = serializers.IntegerField(min_value=1, max_value=99, default=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class CartMergeSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            "full_name", "email", "phone", "line1", "line2", "city", "region", "postal_code", "country",
            "customer_note", "payment_method",
        ]

    def validate_payment_method(self, value):
        from apps.payments import sslcommerz

        if value == Order.PaymentMethod.ONLINE and not sslcommerz.is_configured():
            raise serializers.ValidationError("Online payment is not available right now.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    product_slug = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product_title", "product_slug", "variant_title", "sku", "unit_price", "quantity", "line_total"]

    def get_product_slug(self, obj):
        return obj.variant.product.slug if obj.variant else None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_number", "status", "full_name", "email", "phone", "line1", "line2", "city", "region",
            "postal_code", "country", "customer_note", "subtotal", "payment_method", "payment_status", "items",
            "created_at",
        ]


class OrderTrackSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    email = serializers.EmailField()


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()

    class Meta:
        model = OrderStatusHistory
        fields = ["from_status", "to_status", "note", "changed_by", "changed_at"]
