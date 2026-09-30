from rest_framework import serializers

from .models import Collection, Product, ProductImage, ProductOption, ProductVariant, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["id", "title", "slug", "description", "banner_image", "seo_title", "seo_description"]


class CollectionRefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = ["title", "slug"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "thumbnail", "alt_text", "is_main", "position"]


class ProductOptionSerializer(serializers.ModelSerializer):
    values = serializers.SlugRelatedField(many=True, read_only=True, slug_field="value")

    class Meta:
        model = ProductOption
        fields = ["name", "values"]


class ProductVariantSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProductVariant
        fields = ["id", "title", "sku", "price", "stock_quantity", "in_stock", "options"]

    def get_options(self, obj):
        return {v.option.name: v.value for v in obj.option_values.all()}


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight card representation; expects `with_listing_data()` annotations."""

    price_from = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_price_range = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "slug", "price_from", "has_price_range", "compare_at_price", "in_stock", "image"]

    def get_has_price_range(self, obj):
        prices = {v.price for v in obj.variants.all() if v.is_active}
        return len(prices) > 1

    def get_in_stock(self, obj):
        return bool(obj.total_stock)

    def get_image(self, obj):
        images = list(obj.images.all())
        if not images:
            return None
        return ProductImageSerializer(images[0], context=self.context).data


class ProductDetailSerializer(ProductListSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    options = ProductOptionSerializer(many=True, read_only=True)
    variants = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    collections = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            "description", "video_url", "images", "options", "variants", "tags", "collections",
            "seo_title", "seo_description",
        ]

    def get_variants(self, obj):
        active = [v for v in obj.variants.all() if v.is_active]
        return ProductVariantSerializer(active, many=True, context=self.context).data

    def get_collections(self, obj):
        active = [c for c in obj.collections.all() if c.is_active]
        return CollectionRefSerializer(active, many=True).data
