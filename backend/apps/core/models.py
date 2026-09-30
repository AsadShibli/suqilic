from django.core.exceptions import ValidationError
from django.db import models

from .validators import IMAGE_VALIDATORS


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteSettings(models.Model):
    store_name = models.CharField(max_length=100, default="Suqilic")
    logo = models.ImageField(upload_to="site/", blank=True, validators=IMAGE_VALIDATORS)
    favicon = models.ImageField(upload_to="site/", blank=True, validators=IMAGE_VALIDATORS)
    announcement_text = models.CharField(max_length=255, blank=True)
    announcement_link = models.CharField(max_length=255, blank=True)
    announcement_active = models.BooleanField(default=False)
    contact_email = models.EmailField(blank=True)
    currency_symbol = models.CharField(max_length=5, default="$")
    currency_code = models.CharField(max_length=3, default="USD")
    instagram_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    seo_default_title = models.CharField(max_length=70, blank=True)
    seo_default_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.store_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MenuItem(models.Model):
    class Menu(models.TextChoices):
        HEADER = "header"
        FOOTER = "footer"
        POLICIES = "policies"

    menu = models.CharField(max_length=20, choices=Menu.choices, db_index=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)
    label = models.CharField(max_length=80)
    url = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["menu", "position", "id"]

    def __str__(self):
        return f"{self.menu}: {self.label}"

    def clean(self):
        if self.parent and self.parent.menu != self.menu:
            raise ValidationError({"parent": "Parent must belong to the same menu."})


class Page(models.Model):
    class PageType(models.TextChoices):
        PAGE = "page"
        POLICY = "policy"

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    page_type = models.CharField(max_length=10, choices=PageType.choices, default=PageType.PAGE)
    body = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class HowToVideo(models.Model):
    title = models.CharField(max_length=150)
    video_url = models.URLField()
    thumbnail = models.ImageField(upload_to="videos/", blank=True, validators=IMAGE_VALIDATORS)
    product = models.ForeignKey(
        "catalog.Product", null=True, blank=True, related_name="howto_videos", on_delete=models.SET_NULL
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField(max_length=5000)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self):
        return self.email


class StoredFile(models.Model):
    """File bytes for DatabaseStorage (media on hosts without a persistent disk)."""

    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
