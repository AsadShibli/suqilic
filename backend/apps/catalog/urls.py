from django.urls import path

from . import views

urlpatterns = [
    path("collections/", views.CollectionListView.as_view(), name="collection-list"),
    path("collections/<slug:slug>/", views.CollectionDetailView.as_view(), name="collection-detail"),
    path("collections/<slug:slug>/products/", views.CollectionProductListView.as_view(), name="collection-products"),
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", views.ProductDetailView.as_view(), name="product-detail"),
    path("products/<slug:slug>/related/", views.RelatedProductsView.as_view(), name="product-related"),
    path("tags/", views.TagListView.as_view(), name="tag-list"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("search/suggest/", views.SearchSuggestView.as_view(), name="search-suggest"),
]
