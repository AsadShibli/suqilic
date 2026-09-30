from django.urls import path

from . import views

urlpatterns = [
    path("settings/", views.SiteSettingsView.as_view(), name="site-settings"),
    path("menus/<str:menu>/", views.MenuView.as_view(), name="menu"),
    path("pages/<slug:slug>/", views.PageDetailView.as_view(), name="page-detail"),
    path("policies/<slug:slug>/", views.PolicyDetailView.as_view(), name="policy-detail"),
    path("videos/", views.HowToVideoListView.as_view(), name="video-list"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("newsletter/subscribe/", views.NewsletterSubscribeView.as_view(), name="newsletter-subscribe"),
    path("newsletter/unsubscribe/", views.NewsletterUnsubscribeView.as_view(), name="newsletter-unsubscribe"),
]
