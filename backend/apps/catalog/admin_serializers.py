from django.db import transaction
from rest_framework import serializers

from apps.core.slugs import AutoSlugMixin

from .models import (
    Collection,
    CollectionProduct,
    Product,
    ProductImage,
    ProductOption,
    ProductOptionValue,
    ProductVariant,
    Tag,
)


class TagAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source = "name"

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class CollectionAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    product_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id", "title", "slug", "description", "banner_image", "sort_order", "is_active",
            "seo_title", "seo_description", "product_count", "created_at", "updated_at",
        ]


class CollectionProductsSerializer(serializers.Serializer):
    product_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all())

    def save(self, collection):
        products = self.validated_data["product_ids"]
        with transaction.atomic():
            collection.collection_products.exclude(product__in=products).delete()
            existing = set(collection.collection_products.values_list("product_id", flat=True))
            start = collection.collection_products.count()
            CollectionProduct.objects.bulk_create([
                CollectionProduct(collection=collection, product=p, position=start + i)
                for i, p in enumerate(p for p in products if p.id not in existing)
            ])


class ProductImageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "thumbnail", "alt_text", "position", "is_main"]
        read_only_fields = ["thumbnail"]


class ProductOptionValueAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductOptionValue
        fields = ["id", "value", "position"]


class ProductOptionAdminSerializer(serializers.ModelSerializer):
    """Options are written with their full list of values: {name, values: ["S", "M"]}."""

    values = serializers.ListField(child=serializers.CharField(max_length=80), write_only=True, required=False)
    value_list = ProductOptionValueAdminSerializer(source="values", many=True, read_only=True)

    class Meta:
        model = ProductOption
        fields = ["id", "name", "position", "values", "value_list"]

    @transaction.atomic
    def save(self, **kwargs):
        values = self.validated_data.pop("values", None)
        option = super().save(**kwargs)
        if values is not None:
            option.values.exclude(value__in=values).delete()
            for position, value in enumerate(values):
                ProductOptionValue.objects.update_or_create(option=option, value=value, defaults={"position": position})
        return option

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["values"] = data.pop("value_list")
        return data


class ProductVariantAdminSerializer(serializers.ModelSerializer):
    option_value_ids = serializers.PrimaryKeyRelatedField(
        source="option_values", many=True, queryset=ProductOptionValue.objects.all(), required=False
    )

    class Meta:
        model = ProductVariant
        fields = ["id", "title", "sku", "price", "stock_quantity", "is_active", "position", "option_value_ids"]

    def validate_option_value_ids(self, values):
        product_id = self.context["view"].kwargs["product_pk"]
        if any(str(v.option.product_id) != str(product_id) for v in values):
            raise serializers.ValidationError("Option values must belong to this product.")
        return values


class ProductAdminListSerializer(serializers.ModelSerializer):
    price_from = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    variant_count = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "slug", "status", "price_from", "total_stock", "variant_count", "image", "updated_at"]

    def get_image(self, obj):
        images = list(obj.images.all())
        if not images or not images[0].thumbnail:
            return None
        return self.context["request"].build_absolute_uri(images[0].thumbnail.url)


class ProductAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    tag_ids = serializers.PrimaryKeyRelatedField(source="tags", many=True, queryset=Tag.objects.all(), required=False)
    collection_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Collection.objects.all(), required=False, write_only=True
    )
    images = ProductImageAdminSerializer(many=True, read_only=True)
    options = ProductOptionAdminSerializer(many=True, read_only=True)
    variants = ProductVariantAdminSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "title", "slug", "description", "base_price", "compare_at_price", "status", "video_url",
            "seo_title", "seo_description", "tag_ids", "collection_ids", "images", "options", "variants",
            "created_at", "updated_at",
        ]

    @transaction.atomic
    def create(self, validated_data):
        collections = validated_data.pop("collection_ids", [])
        product = super().create(validated_data)
        ProductVariant.objects.create(product=product, title="Default", price=product.base_price)
        self._set_collections(product, collections)
        return product

    @transaction.atomic
    def update(self, instance, validated_data):
        collections = validated_data.pop("collection_ids", None)
        product = super().update(instance, validated_data)
        if collections is not None:
            self._set_collections(product, collections)
        return product

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["collection_ids"] = list(instance.collection_products.values_list("collection_id", flat=True))
        return data

    @staticmethod
    def _set_collections(product, collections):
        product.collection_products.exclude(collection__in=collections).delete()
        existing = set(product.collection_products.values_list("collection_id", flat=True))
        for collection in collections:
            if collection.id not in existing:
                position = collection.collection_products.count()
                CollectionProduct.objects.create(collection=collection, product=product, position=position)


class BulkStatusSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)
    status = serializers.ChoiceField(choices=Product.Status.choices)
