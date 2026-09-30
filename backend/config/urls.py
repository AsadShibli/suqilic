from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

api_v1 = [
    path("auth/", include("apps.accounts.urls.auth")),
    path("me/", include("apps.accounts.urls.me")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.storefront.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.core.urls")),
    path("admin/", include("config.admin_api_urls")),
]

urlpatterns = [
    path(f"{settings.DJANGO_ADMIN_PATH}/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("", include("apps.core.seo_urls")),
]

if settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "Suqilic Admin"
admin.site.site_title = "Suqilic Admin"
