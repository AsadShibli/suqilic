from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.mixins import AdminModelViewSet, ReorderMixin

from .models import HeroBanner, HomeSection


class HeroBannerAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroBanner
        fields = "__all__"


class HomeSectionAdminSerializer(serializers.ModelSerializer):
    collection_title = serializers.CharField(source="collection.title", read_only=True, default=None)
    banner_count = serializers.IntegerField(source="banners.count", read_only=True)

    class Meta:
        model = HomeSection
        fields = "__all__"

    def validate(self, attrs):
        section_type = attrs.get("type", getattr(self.instance, "type", None))
        collection = attrs.get("collection", getattr(self.instance, "collection", None))
        if section_type == HomeSection.SectionType.PRODUCT_CAROUSEL and not collection:
            raise serializers.ValidationError({"collection": "A product carousel needs a collection."})
        return attrs


class HomeSectionAdminViewSet(ReorderMixin, AdminModelViewSet):
    queryset = HomeSection.objects.select_related("collection")
    serializer_class = HomeSectionAdminSerializer
    pagination_class = None

    @action(detail=True, methods=["post"], url_path="toggle-visibility")
    def toggle_visibility(self, request, pk=None):
        section = self.get_object()
        section.is_visible = not section.is_visible
        section.save(update_fields=["is_visible"])
        return Response(self.get_serializer(section).data)


class HeroBannerAdminViewSet(ReorderMixin, AdminModelViewSet):
    queryset = HeroBanner.objects.all()
    serializer_class = HeroBannerAdminSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["section", "is_active"]
    pagination_class = None
