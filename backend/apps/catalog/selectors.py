from django.db.models import OuterRef, Prefetch, Q, QuerySet, Subquery

from .filters import PRODUCT_ORDERINGS
from .models import Collection, CollectionProduct, Product, ProductImage, ProductOption, ProductVariant


def product_list_queryset() -> QuerySet[Product]:
    return (
        Product.objects.active()
        .with_listing_data()
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("-is_main", "position", "id")),
            Prefetch("variants", queryset=ProductVariant.objects.only("id", "product_id", "price", "is_active")),
        )
    )


def product_detail_queryset() -> QuerySet[Product]:
    return (
        Product.objects.active()
        .with_listing_data()
        .prefetch_related(
            "images",
            "tags",
            "collections",
            Prefetch("options", queryset=ProductOption.objects.prefetch_related("values")),
            Prefetch("variants", queryset=ProductVariant.objects.prefetch_related("option_values__option")),
        )
    )


def collection_products(collection: Collection) -> QuerySet[Product]:
    memberships = CollectionProduct.objects.filter(collection=collection)
    position = memberships.filter(product=OuterRef("pk")).values("position")[:1]
    return product_list_queryset().filter(pk__in=memberships.values("product")).annotate(collection_position=Subquery(position))


def apply_ordering(queryset: QuerySet[Product], ordering: str | None, in_collection: bool = False):
    ordering = ordering if ordering in PRODUCT_ORDERINGS else "featured"
    if ordering == "featured":
        return queryset.order_by("collection_position", "id") if in_collection else queryset.order_by("-created_at")
    if ordering == "best_selling":
        queryset = queryset.with_sales()
    return queryset.order_by(*PRODUCT_ORDERINGS[ordering])


def search_products(term: str) -> QuerySet[Product]:
    matches = Product.objects.filter(
        Q(title__icontains=term) | Q(tags__name__icontains=term) | Q(collections__title__icontains=term)
    )
    return product_list_queryset().filter(pk__in=matches.values("pk"))


def related_products(product: Product, limit: int = 8) -> QuerySet[Product]:
    collection_ids = product.collections.values_list("id", flat=True)
    tag_ids = product.tags.values_list("id", flat=True)
    matches = Product.objects.filter(Q(collections__in=collection_ids) | Q(tags__in=tag_ids))
    return product_list_queryset().filter(pk__in=matches.values("pk")).exclude(pk=product.pk).order_by("?")[:limit]
