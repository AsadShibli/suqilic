from django.urls import path

from . import views

urlpatterns = [
    path("payments/config/", views.PaymentConfigView.as_view(), name="payment-config"),
    path("payments/sslcommerz/start/", views.StartPaymentView.as_view(), name="payment-start"),
    path("payments/sslcommerz/return/", views.GatewayReturnView.as_view(), name="payment-return"),
    path("payments/sslcommerz/ipn/", views.GatewayIpnView.as_view(), name="payment-ipn"),
]
