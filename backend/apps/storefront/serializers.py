from rest_framework import serializers

from apps.catalog import selectors
from apps.catalog.serializers import ProductListSerializer

from .models import HeroBanner, HomeSection


class HeroBannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroBanner
        fields = ["id", "image_desktop", "image_mobile", "heading", "subheading", "button_text", "button_link"]


class HomeSectionSerializer(serializers.ModelSerializer):
    banners = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    view_all_link = serializers.SerializerMethodField()

    class Meta:
        model = HomeSection
        fields = ["id", "type", "title", "view_all_link", "banners", "products"]

    def get_banners(self, obj):
        if obj.type != HomeSection.SectionType.HERO:
            return []
        active = [b for b in obj.banners.all() if b.is_active]
        return HeroBannerSerializer(active, many=True, context=self.context).data

    def get_products(self, obj):
        if obj.type != HomeSection.SectionType.PRODUCT_CAROUSEL or not obj.collection:
            return []
        qs = selectors.apply_ordering(selectors.collection_products(obj.collection), "featured", in_collection=True)
        return ProductListSerializer(qs[: obj.max_products], many=True, context=self.context).data

    def get_view_all_link(self, obj):
        if obj.view_all_link:
            return obj.view_all_link
        return f"/collections/{obj.collection.slug}" if obj.collection else ""
