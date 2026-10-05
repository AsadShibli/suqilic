from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.throttles import PaymentThrottle
from apps.orders.models import Order

from . import services, sslcommerz
from .models import Payment


class PaymentConfigView(APIView):
    def get(self, request):
        return Response({"online_payments": sslcommerz.is_configured()})


class StartPaymentSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    email = serializers.EmailField()


class StartPaymentView(APIView):
    """Begin (or retry) online payment for an order. The customer proves ownership with order number + email."""

    throttle_classes = [PaymentThrottle]

    def post(self, request):
        if not sslcommerz.is_configured():
            return Response({"detail": "Online payment is not available."}, status=status.HTTP_400_BAD_REQUEST)
        s = StartPaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        order = get_object_or_404(
            Order, order_number__iexact=s.validated_data["order_number"], email__iexact=s.validated_data["email"]
        )
        callback_base = request.build_absolute_uri("/api/v1/payments/sslcommerz").rstrip("/")
        return Response({"redirect_url": services.start_payment(order, callback_base)})


class GatewayCallbackView(APIView):
    """Base for endpoints SSLCommerz POSTs form data to. No auth: the payload is verified with the gateway."""

    authentication_classes = []
    permission_classes = []


class GatewayReturnView(GatewayCallbackView):
    """Where the customer's browser lands after paying, failing, or cancelling. Redirects back to the storefront."""

    def post(self, request):
        data = request.data
        tran_id, val_id, gateway_status = data.get("tran_id", ""), data.get("val_id", ""), data.get("status", "")
        payment = None
        if gateway_status in ("VALID", "VALIDATED") and val_id:
            try:
                payment = services.settle_payment(val_id, tran_id)
            except sslcommerz.GatewayError:
                payment = None
        elif tran_id:
            outcome = Payment.Status.CANCELLED if gateway_status == "CANCELLED" else Payment.Status.FAILED
            payment = services.mark_unsuccessful(tran_id, outcome)

        if payment is None:
            payment = Payment.objects.filter(tran_id=tran_id).select_related("order").first()
        result = payment.status if payment else "failed"
        if result == Payment.Status.INITIATED:  # validation was unreachable; the IPN will settle it
            result = "pending"
        query = {"result": result, **({"order": payment.order.order_number} if payment else {})}
        return HttpResponseRedirect(f"{settings.FRONTEND_URL.rstrip('/')}/payment/result?{urlencode(query)}")


class GatewayIpnView(GatewayCallbackView):
    """Server-to-server notification. It may arrive before, after, or instead of the browser return."""

    def post(self, request):
        val_id, tran_id = request.data.get("val_id", ""), request.data.get("tran_id", "")
        if request.data.get("status") in ("VALID", "VALIDATED") and val_id:
            services.settle_payment(val_id, tran_id)
        elif tran_id:
            services.mark_unsuccessful(tran_id, Payment.Status.FAILED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response({"received": True})
