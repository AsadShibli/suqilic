from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.accounts import views

router = SimpleRouter()
router.register("addresses", views.AddressViewSet, basename="me-address")
router.register("orders", views.MyOrderViewSet, basename="me-order")

urlpatterns = [
    path("", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    *router.urls,
]
