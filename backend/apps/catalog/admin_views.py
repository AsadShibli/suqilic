from itertools import product as cartesian

from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core.mixins import AdminModelViewSet, IdListSerializer, ReorderMixin
from apps.core.slugs import unique_slug

from .admin_serializers import (
    BulkStatusSerializer,
    CollectionAdminSerializer,
    CollectionProductsSerializer,
    ProductAdminListSerializer,
    ProductAdminSerializer,
    ProductImageAdminSerializer,
    ProductOptionAdminSerializer,
    ProductVariantAdminSerializer,
    TagAdminSerializer,
)
from .models import Collection, CollectionProduct, Product, ProductImage, ProductOption, ProductVariant, Tag

LOW_STOCK_THRESHOLD = 5
UPLOAD_PARSERS = [MultiPartParser, FormParser, JSONParser]


class TagAdminViewSet(AdminModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagAdminSerializer
    search_fields = ["name"]
    pagination_class = None


class CollectionAdminViewSet(ReorderMixin, AdminModelViewSet):
    queryset = Collection.objects.annotate(product_count=Count("collection_products")).order_by("sort_order", "title")
    serializer_class = CollectionAdminSerializer
    parser_classes = UPLOAD_PARSERS
    search_fields = ["title"]
    filterset_fields = ["is_active"]
    ordering_fields = ["sort_order", "title", "created_at"]
    position_field = "sort_order"

    @action(detail=True, methods=["get", "post"])
    def products(self, request, pk=None):
        collection = self.get_object()
        if request.method == "POST":
            s = CollectionProductsSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            s.save(collection)
        products = (
            Product.objects.filter(collection_products__collection=collection)
            .order_by("collection_products__position")
            .with_listing_data()
            .annotate(variant_count=Count("variants", distinct=True))
            .prefetch_related("images")
        )
        return Response(ProductAdminListSerializer(products, many=True, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="products/reorder")
    def reorder_products(self, request, pk=None):
        collection = self.get_object()
        s = IdListSerializer(data={"ids": request.data.get("product_ids")})
        s.is_valid(raise_exception=True)
        with transaction.atomic():
            for position, product_id in enumerate(s.validated_data["ids"]):
                CollectionProduct.objects.filter(collection=collection, product_id=product_id).update(position=position)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductAdminViewSet(AdminModelViewSet):
    search_fields = ["title", "variants__sku"]
    filterset_fields = {"status": ["exact"], "collection_products__collection": ["exact"], "tags": ["exact"]}
    ordering_fields = ["title", "created_at", "updated_at", "price_from", "total_stock"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Product.objects.with_listing_data().annotate(
            variant_count=Count("variants", filter=Q(variants__is_active=True), distinct=True)
        )
        if self.request.query_params.get("low_stock") == "true":
            qs = qs.filter(total_stock__lte=LOW_STOCK_THRESHOLD)
        if self.action == "list":
            return qs.prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "position")))
        return qs.prefetch_related("images", "tags", "options__values", "variants__option_values")

    def get_serializer_class(self):
        return ProductAdminListSerializer if self.action == "list" else ProductAdminSerializer

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        source = self.get_object()
        copy = Product.objects.get(pk=source.pk)
        copy.pk = None
        copy.title = f"{source.title} (copy)"
        copy.slug = unique_slug(Product, copy.title)
        copy.status = Product.Status.DRAFT
        copy.save()
        copy.tags.set(source.tags.all())
        value_map = {}
        for option in source.options.prefetch_related("values"):
            new_option = ProductOption.objects.create(product=copy, name=option.name, position=option.position)
            for value in option.values.all():
                value_map[value.id] = new_option.values.create(value=value.value, position=value.position)
        for variant in source.variants.prefetch_related("option_values"):
            new_variant = ProductVariant.objects.create(
                product=copy, title=variant.title, price=variant.price, stock_quantity=0,
                is_active=variant.is_active, position=variant.position,
            )
            new_variant.option_values.set([value_map[v.id] for v in variant.option_values.all()])
        for image in source.images.all():
            ProductImage.objects.create(
                product=copy, image=image.image.name, alt_text=image.alt_text,
                position=image.position, is_main=image.is_main,
            )
        for membership in source.collection_products.all():
            CollectionProduct.objects.create(
                collection_id=membership.collection_id, product=copy,
                position=CollectionProduct.objects.filter(collection_id=membership.collection_id).count(),
            )
        return Response(ProductAdminSerializer(self.get_queryset().get(pk=copy.pk), context=self.get_serializer_context()).data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-status")
    def bulk_status(self, request):
        s = BulkStatusSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        updated = Product.objects.filter(id__in=s.validated_data["ids"]).update(status=s.validated_data["status"])
        return Response({"updated": updated})


class ProductChildViewSet(AdminModelViewSet):
    """Base for resources nested under /admin/products/{product_pk}/."""

    pagination_class = None
    model = None

    def get_product(self):
        return get_object_or_404(Product, pk=self.kwargs["product_pk"])

    def get_queryset(self):
        return self.model.objects.filter(product_id=self.kwargs["product_pk"])

    def perform_create(self, serializer):
        serializer.save(product=self.get_product())


class ProductImageAdminViewSet(ReorderMixin, ProductChildViewSet):
    model = ProductImage
    serializer_class = ProductImageAdminSerializer
    parser_classes = UPLOAD_PARSERS

    @action(detail=True, methods=["post"], url_path="set-main")
    def set_main(self, request, product_pk=None, pk=None):
        image = self.get_object()
        image.is_main = True
        image.save(update_fields=["is_main"])
        return Response(self.get_serializer(image).data)


class ProductOptionAdminViewSet(ReorderMixin, ProductChildViewSet):
    model = ProductOption
    serializer_class = ProductOptionAdminSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related("values")


class ProductVariantAdminViewSet(ReorderMixin, ProductChildViewSet):
    model = ProductVariant
    serializer_class = ProductVariantAdminSerializer

    def get_queryset(self):
        return super().get_queryset().prefetch_related("option_values")

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def generate(self, request, product_pk=None):
        """Create a variant for every combination of option values that doesn't have one yet."""
        product = self.get_product()
        options = list(product.options.prefetch_related("values"))
        if not options:
            return Response({"detail": "Add at least one option first."}, status=status.HTTP_400_BAD_REQUEST)
        existing = {
            frozenset(v.option_values.values_list("id", flat=True)) for v in product.variants.prefetch_related("option_values")
        }
        created = 0
        position = product.variants.count()
        for combo in cartesian(*[list(o.values.all()) for o in options]):
            key = frozenset(v.id for v in combo)
            if key in existing:
                continue
            variant = ProductVariant.objects.create(
                product=product, title=" / ".join(v.value for v in combo), price=product.base_price, position=position
            )
            variant.option_values.set(combo)
            created, position = created + 1, position + 1
        product.variants.filter(option_values__isnull=True, title="Default").delete()
        return Response({"created": created}, status=status.HTTP_201_CREATED)
