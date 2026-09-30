from django.contrib import admin

from .models import ContactMessage, HowToVideo, MenuItem, NewsletterSubscriber, Page, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["label", "menu", "parent", "position", "is_active"]
    list_filter = ["menu"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "page_type", "is_published"]
    prepopulated_fields = {"slug": ["title"]}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "is_read", "created_at"]
    list_filter = ["is_read"]


admin.site.register(HowToVideo)
admin.site.register(NewsletterSubscriber)
