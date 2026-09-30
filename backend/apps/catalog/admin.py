from django.contrib import admin

from .models import Collection, CollectionProduct, Product, ProductImage, ProductOption, ProductVariant, Tag


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


class ProductOptionInline(admin.TabularInline):
    model = ProductOption
    extra = 0


class CollectionProductInline(admin.TabularInline):
    model = CollectionProduct
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "base_price", "created_at"]
    list_filter = ["status", "collections"]
    search_fields = ["title", "variants__sku"]
    prepopulated_fields = {"slug": ["title"]}
    filter_horizontal = ["tags"]
    inlines = [ProductImageInline, ProductOptionInline, ProductVariantInline]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ["title", "sort_order", "is_active"]
    prepopulated_fields = {"slug": ["title"]}
    inlines = [CollectionProductInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
