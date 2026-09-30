import uuid
from pathlib import Path

from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .mixins import AdminModelViewSet, CsvExportMixin, IdListSerializer, ReorderMixin
from .models import ContactMessage, HowToVideo, MenuItem, NewsletterSubscriber, Page, SiteSettings
from .permissions import IsStaff
from .serializers import SiteSettingsSerializer
from .slugs import AutoSlugMixin
from .validators import IMAGE_VALIDATORS

UPLOAD_PARSERS = [MultiPartParser, FormParser, JSONParser]


class MenuItemAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        menu = attrs.get("menu", getattr(self.instance, "menu", None))
        if parent and parent.menu != menu:
            raise serializers.ValidationError({"parent": "Parent must belong to the same menu."})
        if parent and self.instance and parent.pk == self.instance.pk:
            raise serializers.ValidationError({"parent": "An item cannot be its own parent."})
        return attrs


class MenuReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    parent_id = serializers.IntegerField(allow_null=True, required=False)
    position = serializers.IntegerField(min_value=0)


class MenuReorderSerializer(serializers.Serializer):
    menu = serializers.ChoiceField(choices=MenuItem.Menu.choices)
    items = MenuReorderItemSerializer(many=True)


class PageAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"


class HowToVideoAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = HowToVideo
        fields = "__all__"


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = "__all__"
        read_only_fields = ["name", "email", "phone", "message", "created_at"]


class SubscriberAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = "__all__"


class MenuItemAdminViewSet(AdminModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemAdminSerializer
    filterset_fields = ["menu", "is_active"]
    pagination_class = None

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        s = MenuReorderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        menu = s.validated_data["menu"]
        items = {i.id: i for i in MenuItem.objects.filter(menu=menu)}
        with transaction.atomic():
            for row in s.validated_data["items"]:
                if item := items.get(row["id"]):
                    parent_id = row.get("parent_id")
                    item.parent_id = parent_id if parent_id in items and parent_id != item.id else None
                    item.position = row["position"]
            MenuItem.objects.bulk_update(items.values(), ["parent", "position"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PageAdminViewSet(AdminModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageAdminSerializer
    filterset_fields = ["page_type", "is_published"]
    search_fields = ["title", "slug"]


class HowToVideoAdminViewSet(ReorderMixin, AdminModelViewSet):
    queryset = HowToVideo.objects.all()
    serializer_class = HowToVideoAdminSerializer
    parser_classes = UPLOAD_PARSERS
    pagination_class = None


class ContactMessageAdminViewSet(AdminModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageAdminSerializer
    filterset_fields = ["is_read"]
    search_fields = ["name", "email", "message"]
    http_method_names = ["get", "patch", "delete", "post"]

    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        message = self.get_object()
        message.is_read = True
        message.save(update_fields=["is_read"])
        return Response(self.get_serializer(message).data)

    @action(detail=False, methods=["post"], url_path="bulk-mark-read")
    def bulk_mark_read(self, request):
        s = IdListSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        return Response({"updated": ContactMessage.objects.filter(id__in=s.validated_data["ids"]).update(is_read=True)})


class SubscriberAdminViewSet(CsvExportMixin, AdminModelViewSet):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = SubscriberAdminSerializer
    filterset_fields = ["is_active"]
    search_fields = ["email"]
    http_method_names = ["get", "patch", "delete", "post"]
    csv_filename = "subscribers.csv"
    csv_fields = [("Email", "email"), ("Active", "is_active"), ("Subscribed at", "subscribed_at")]


class SiteSettingsAdminView(APIView):
    permission_classes = [IsStaff]
    parser_classes = UPLOAD_PARSERS

    def get(self, request):
        return Response(SiteSettingsSerializer(SiteSettings.load(), context={"request": request}).data)

    def patch(self, request):
        s = SiteSettingsSerializer(SiteSettings.load(), data=request.data, partial=True, context={"request": request})
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class UploadSerializer(serializers.Serializer):
    file = serializers.ImageField(validators=IMAGE_VALIDATORS)


class UploadView(APIView):
    """Generic image upload for the rich-text editor."""

    permission_classes = [IsStaff]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        s = UploadSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        file = s.validated_data["file"]
        name = default_storage.save(f"uploads/{uuid.uuid4().hex}{Path(file.name).suffix.lower()}", file)
        return Response({"url": request.build_absolute_uri(default_storage.url(name))}, status=status.HTTP_201_CREATED)
