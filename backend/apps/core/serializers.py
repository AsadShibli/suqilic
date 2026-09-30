from rest_framework import serializers

from .models import ContactMessage, HowToVideo, MenuItem, NewsletterSubscriber, Page, SiteSettings


class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        exclude = ["id"]


class MenuItemSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "label", "url", "children"]

    def get_children(self, obj):
        children = self.context["children_by_parent"].get(obj.id, [])
        return MenuItemSerializer(children, many=True, context=self.context).data


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["title", "slug", "page_type", "body", "updated_at"]


class HowToVideoSerializer(serializers.ModelSerializer):
    product_slug = serializers.SlugRelatedField(source="product", slug_field="slug", read_only=True)

    class Meta:
        model = HowToVideo
        fields = ["id", "title", "video_url", "thumbnail", "product_slug"]


class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "phone", "message"]


class NewsletterSubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()


class NewsletterUnsubscribeSerializer(NewsletterSubscribeSerializer):
    token = serializers.CharField()
