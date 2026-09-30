from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductImage
from apps.core.throttles import OrderThrottle, TrackThrottle

from .cart import CART_HEADER, get_cart, merge_guest_cart
from .models import CartItem, Order
from .serializers import (
    AddCartItemSerializer,
    CartMergeSerializer,
    CartSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderTrackSerializer,
    UpdateCartItemSerializer,
)
from .services import place_order

CART_ITEMS_PREFETCH = Prefetch(
    "items",
    queryset=CartItem.objects.select_related("variant__product").prefetch_related(
        Prefetch("variant__product__images", queryset=ProductImage.objects.order_by("-is_main", "position", "id"))
    ),
)


def cart_response(request, cart, status_code=status.HTTP_200_OK):
    if cart is None:
        return Response({"id": None, "items": [], "subtotal": "0.00", "item_count": 0})
    cart = type(cart).objects.prefetch_related(CART_ITEMS_PREFETCH).get(pk=cart.pk)
    response = Response(CartSerializer(cart, context={"request": request}).data, status=status_code)
    response[CART_HEADER] = str(cart.session_key)
    return response


class CartView(APIView):
    def get(self, request):
        return cart_response(request, get_cart(request))

    def delete(self, request):
        if cart := get_cart(request):
            cart.items.all().delete()
        return cart_response(request, cart)


class CartItemListView(APIView):
    def post(self, request):
        s = AddCartItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        variant, quantity = s.validated_data["variant"], s.validated_data["quantity"]
        cart = get_cart(request, create=True)
        item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={"quantity": quantity})
        if not created:
            item.quantity += quantity
        if item.quantity > variant.stock_quantity:
            return Response(
                {"quantity": [f"Only {variant.stock_quantity} in stock."]}, status=status.HTTP_400_BAD_REQUEST
            )
        item.save()
        return cart_response(request, cart, status.HTTP_201_CREATED)


class CartItemDetailView(APIView):
    def get_item(self, request, pk):
        cart = get_cart(request)
        return cart, get_object_or_404(CartItem.objects.select_related("variant"), pk=pk, cart=cart)

    def patch(self, request, pk):
        cart, item = self.get_item(request, pk)
        s = UpdateCartItemSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if s.validated_data["quantity"] > item.variant.stock_quantity:
            return Response(
                {"quantity": [f"Only {item.variant.stock_quantity} in stock."]}, status=status.HTTP_400_BAD_REQUEST
            )
        item.quantity = s.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        return cart_response(request, cart)

    def delete(self, request, pk):
        cart, item = self.get_item(request, pk)
        item.delete()
        return cart_response(request, cart)


class CartMergeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = CartMergeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return cart_response(request, merge_guest_cart(request.user, str(s.validated_data["cart_id"])))


class OrderCreateView(APIView):
    throttle_classes = [OrderThrottle]

    def post(self, request):
        s = OrderCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        cart = get_cart(request)
        if cart is None:
            return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None
        order = place_order(cart, s.validated_data, user=user)
        order = Order.objects.prefetch_related("items__variant__product").get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderTrackView(APIView):
    throttle_classes = [TrackThrottle]

    def get(self, request):
        s = OrderTrackSerializer(data=request.query_params)
        s.is_valid(raise_exception=True)
        order = get_object_or_404(
            Order.objects.prefetch_related("items__variant__product"),
            order_number__iexact=s.validated_data["order_number"],
            email__iexact=s.validated_data["email"],
        )
        return Response(OrderSerializer(order).data)
