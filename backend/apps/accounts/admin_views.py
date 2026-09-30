from django.contrib.auth import get_user_model, password_validation
from django.db.models import Count, Sum
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.mixins import AdminModelViewSet
from apps.core.permissions import IsStaff, IsSuperUser
from apps.orders.admin_views import OrderAdminListSerializer

User = get_user_model()


class CustomerAdminSerializer(serializers.ModelSerializer):
    order_count = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "phone", "is_active", "date_joined", "last_login",
            "order_count", "total_spent",
        ]
        read_only_fields = ["email", "first_name", "last_name", "phone", "date_joined", "last_login"]


class StaffAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active", "is_superuser", "last_login", "password"]
        read_only_fields = ["last_login"]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        if "password" not in validated_data:
            raise serializers.ValidationError({"password": "Required for new staff."})
        return User.objects.create_user(is_staff=True, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class CustomerAdminViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    permission_classes = [IsStaff]
    serializer_class = CustomerAdminSerializer
    http_method_names = ["get", "patch"]
    filterset_fields = ["is_active"]
    search_fields = ["email", "first_name", "last_name", "phone"]
    ordering_fields = ["date_joined", "order_count", "total_spent"]
    ordering = ["-date_joined"]

    def get_queryset(self):
        return User.objects.filter(is_staff=False).annotate(
            order_count=Count("orders", distinct=True), total_spent=Sum("orders__subtotal")
        )

    @action(detail=True, methods=["get"])
    def orders(self, request, pk=None):
        orders = self.get_object().orders.annotate(item_count=Sum("items__quantity"))
        return Response(OrderAdminListSerializer(orders, many=True).data)


class StaffAdminViewSet(AdminModelViewSet):
    permission_classes = [IsSuperUser]
    serializer_class = StaffAdminSerializer
    queryset = User.objects.filter(is_staff=True)
    search_fields = ["email", "first_name", "last_name"]

    def perform_destroy(self, instance):
        if instance == self.request.user:
            raise serializers.ValidationError({"detail": "You cannot delete your own account."})
        instance.delete()

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        user = self.get_object()
        s = ResetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user.set_password(s.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated."})
