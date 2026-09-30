from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from . import selectors
from .filters import ProductFilter
from .models import Collection, Tag
from .serializers import (
    CollectionRefSerializer,
    CollectionSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    TagSerializer,
)


class CollectionListView(generics.ListAPIView):
    queryset = Collection.objects.filter(is_active=True)
    serializer_class = CollectionSerializer
    pagination_class = None


class CollectionDetailView(generics.RetrieveAPIView):
    queryset = Collection.objects.filter(is_active=True)
    serializer_class = CollectionSerializer
    lookup_field = "slug"


class ProductListView(generics.ListAPIView):
    """Active products. Supports ProductFilter params and `?ordering=` (see PRODUCT_ORDERINGS)."""

    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    in_collection = False

    def get_queryset(self):
        return selectors.product_list_queryset()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        return selectors.apply_ordering(queryset, self.request.query_params.get("ordering"), self.in_collection)


class CollectionProductListView(ProductListView):
    in_collection = True

    def get_queryset(self):
        collection = get_object_or_404(Collection, slug=self.kwargs["slug"], is_active=True)
        return selectors.collection_products(collection)


class ProductDetailView(generics.RetrieveAPIView):
    queryset = selectors.product_detail_queryset()
    serializer_class = ProductDetailSerializer
    lookup_field = "slug"


class RelatedProductsView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    pagination_class = None

    def get_queryset(self):
        product = get_object_or_404(selectors.product_list_queryset(), slug=self.kwargs["slug"])
        return selectors.related_products(product)


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.filter(products__status="active").distinct()
    serializer_class = TagSerializer
    pagination_class = None


class SearchView(ProductListView):
    def get_queryset(self):
        term = self.request.query_params.get("q", "").strip()
        if not term:
            return selectors.product_list_queryset().none()
        return selectors.search_products(term)


class SearchSuggestView(APIView):
    def get(self, request):
        term = request.query_params.get("q", "").strip()
        if len(term) < 2:
            return Response({"products": [], "collections": []})
        products = selectors.search_products(term).order_by("title")[:6]
        collections = Collection.objects.filter(is_active=True, title__icontains=term)[:3]
        return Response({
            "products": ProductListSerializer(products, many=True, context={"request": request}).data,
            "collections": CollectionRefSerializer(collections, many=True).data,
        })
