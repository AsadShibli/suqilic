from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path

from apps.catalog.models import Collection, Product

from .models import Page


class FrontendSitemap(Sitemap):
    """Sitemap whose URLs point at the SPA routes (FRONTEND_URL), not at Django."""

    def get_urls(self, page=1, site=None, protocol=None):
        base = settings.FRONTEND_URL.rstrip("/")
        return [{"location": f"{base}{self.location(item)}", "lastmod": self.lastmod(item), "item": item}
                for item in self.paginator.page(page).object_list]

    def lastmod(self, obj):
        return getattr(obj, "updated_at", None)


class ProductSitemap(FrontendSitemap):
    def items(self):
        return Product.objects.active().order_by("id")

    def location(self, obj):
        return f"/products/{obj.slug}"


class CollectionSitemap(FrontendSitemap):
    def items(self):
        return Collection.objects.filter(is_active=True).order_by("id")

    def location(self, obj):
        return f"/collections/{obj.slug}"


class PageSitemap(FrontendSitemap):
    def items(self):
        return Page.objects.filter(is_published=True).order_by("id")

    def location(self, obj):
        prefix = "policies" if obj.page_type == Page.PageType.POLICY else "pages"
        return f"/{prefix}/{obj.slug}"


def robots_txt(request):
    if settings.NOINDEX:
        return HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")
    lines = [
        "User-agent: *",
        f"Disallow: /{settings.ADMIN_URL_PATH}/",
        f"Disallow: /{settings.DJANGO_ADMIN_PATH}/",
        "Disallow: /api/",
        "Disallow: /cart",
        "Disallow: /checkout",
        "Disallow: /account",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


sitemaps = {"products": ProductSitemap, "collections": CollectionSitemap, "pages": PageSitemap}

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
]
