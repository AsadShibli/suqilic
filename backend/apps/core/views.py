from collections import defaultdict

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .cache import cache_public
from .emails import check_unsubscribe_token, send_templated_email
from .models import HowToVideo, MenuItem, NewsletterSubscriber, Page, SiteSettings
from .serializers import (
    ContactMessageSerializer,
    HowToVideoSerializer,
    MenuItemSerializer,
    NewsletterSubscribeSerializer,
    NewsletterUnsubscribeSerializer,
    PageSerializer,
    SiteSettingsSerializer,
)
from .throttles import FormThrottle


class SiteSettingsView(APIView):
    @cache_public
    def get(self, request):
        return Response(SiteSettingsSerializer(SiteSettings.load(), context={"request": request}).data)


class MenuView(APIView):
    @cache_public
    def get(self, request, menu):
        if menu not in MenuItem.Menu.values:
            return Response(status=status.HTTP_404_NOT_FOUND)
        items = list(MenuItem.objects.filter(menu=menu, is_active=True))
        children_by_parent = defaultdict(list)
        for item in items:
            children_by_parent[item.parent_id].append(item)
        roots = children_by_parent.pop(None, [])
        return Response(MenuItemSerializer(roots, many=True, context={"children_by_parent": children_by_parent}).data)


class PageDetailView(generics.RetrieveAPIView):
    serializer_class = PageSerializer
    lookup_field = "slug"
    page_type = Page.PageType.PAGE

    def get_queryset(self):
        return Page.objects.filter(is_published=True, page_type=self.page_type)


class PolicyDetailView(PageDetailView):
    page_type = Page.PageType.POLICY


class HowToVideoListView(generics.ListAPIView):
    queryset = HowToVideo.objects.filter(is_active=True).select_related("product")
    serializer_class = HowToVideoSerializer
    pagination_class = None


class ContactView(generics.CreateAPIView):
    serializer_class = ContactMessageSerializer
    throttle_classes = [FormThrottle]

    def perform_create(self, serializer):
        message = serializer.save()
        send_templated_email(
            "contact_admin", {"message": message}, [settings.STORE_ADMIN_EMAIL], f"New contact message from {message.name}"
        )


class NewsletterSubscribeView(APIView):
    throttle_classes = [FormThrottle]

    def post(self, request):
        s = NewsletterSubscribeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        NewsletterSubscriber.objects.update_or_create(email=s.validated_data["email"].lower(), defaults={"is_active": True})
        return Response({"detail": "Subscribed."}, status=status.HTTP_201_CREATED)


class NewsletterUnsubscribeView(APIView):
    def post(self, request):
        s = NewsletterUnsubscribeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        email = s.validated_data["email"].lower()
        if not check_unsubscribe_token(email, s.validated_data["token"]):
            return Response({"detail": "Invalid unsubscribe link."}, status=status.HTTP_400_BAD_REQUEST)
        subscriber = get_object_or_404(NewsletterSubscriber, email=email)
        subscriber.is_active = False
        subscriber.save(update_fields=["is_active"])
        return Response({"detail": "Unsubscribed."})
