from django.contrib import admin

from .models import HeroBanner, HomeSection


class HeroBannerInline(admin.StackedInline):
    model = HeroBanner
    extra = 0


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "type", "collection", "position", "is_visible"]
    list_editable = ["position", "is_visible"]
    inlines = [HeroBannerInline]
