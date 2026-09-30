import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price_from", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price_from", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")
    tag = django_filters.CharFilter(field_name="tags__slug")
    collection = django_filters.CharFilter(field_name="collections__slug")

    class Meta:
        model = Product
        fields = ["min_price", "max_price", "in_stock", "tag", "collection"]

    def filter_in_stock(self, queryset, name, value):
        return queryset.filter(total_stock__gt=0) if value else queryset.filter(total_stock__lte=0)


# Public `?ordering=` values → ORM expressions.
PRODUCT_ORDERINGS = {
    "featured": None,  # collection position (or newest outside a collection)
    "best_selling": ["-units_sold", "-created_at"],
    "title": ["title"],
    "-title": ["-title"],
    "price": ["price_from"],
    "-price": ["-price_from"],
    "-created_at": ["-created_at"],
}
