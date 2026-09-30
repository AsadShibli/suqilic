from django.urls import path

from . import views

urlpatterns = [
    path("cart/", views.CartView.as_view(), name="cart"),
    path("cart/items/", views.CartItemListView.as_view(), name="cart-items"),
    path("cart/items/<int:pk>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/merge/", views.CartMergeView.as_view(), name="cart-merge"),
    path("orders/", views.OrderCreateView.as_view(), name="order-create"),
    path("orders/track/", views.OrderTrackView.as_view(), name="order-track"),
]
