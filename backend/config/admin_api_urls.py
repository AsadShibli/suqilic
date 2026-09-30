"""Staff-only API mounted at /api/v1/admin/."""

from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.accounts.admin_views import CustomerAdminViewSet, StaffAdminViewSet
from apps.catalog.admin_views import (
    CollectionAdminViewSet,
    ProductAdminViewSet,
    ProductImageAdminViewSet,
    ProductOptionAdminViewSet,
    ProductVariantAdminViewSet,
    TagAdminViewSet,
)
from apps.core.admin_views import (
    ContactMessageAdminViewSet,
    HowToVideoAdminViewSet,
    MenuItemAdminViewSet,
    PageAdminViewSet,
    SiteSettingsAdminView,
    SubscriberAdminViewSet,
    UploadView,
)
from apps.orders.admin_views import DashboardStatsView, OrderAdminViewSet, RecentOrdersView
from apps.storefront.admin_views import HeroBannerAdminViewSet, HomeSectionAdminViewSet

router = SimpleRouter()
router.register("products", ProductAdminViewSet, basename="admin-product")
router.register(r"products/(?P<product_pk>\d+)/images", ProductImageAdminViewSet, basename="admin-product-image")
router.register(r"products/(?P<product_pk>\d+)/options", ProductOptionAdminViewSet, basename="admin-product-option")
router.register(r"products/(?P<product_pk>\d+)/variants", ProductVariantAdminViewSet, basename="admin-product-variant")
router.register("collections", CollectionAdminViewSet, basename="admin-collection")
router.register("tags", TagAdminViewSet, basename="admin-tag")
router.register("home-sections", HomeSectionAdminViewSet, basename="admin-home-section")
router.register("hero-banners", HeroBannerAdminViewSet, basename="admin-hero-banner")
router.register("menu-items", MenuItemAdminViewSet, basename="admin-menu-item")
router.register("pages", PageAdminViewSet, basename="admin-page")
router.register("videos", HowToVideoAdminViewSet, basename="admin-video")
router.register("orders", OrderAdminViewSet, basename="admin-order")
router.register("customers", CustomerAdminViewSet, basename="admin-customer")
router.register("messages", ContactMessageAdminViewSet, basename="admin-message")
router.register("subscribers", SubscriberAdminViewSet, basename="admin-subscriber")
router.register("staff", StaffAdminViewSet, basename="admin-staff")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="admin-dashboard-stats"),
    path("dashboard/recent-orders/", RecentOrdersView.as_view(), name="admin-dashboard-recent-orders"),
    path("settings/", SiteSettingsAdminView.as_view(), name="admin-settings"),
    path("uploads/", UploadView.as_view(), name="admin-uploads"),
    *router.urls,
]
