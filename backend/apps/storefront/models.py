from django.core.exceptions import ValidationError
from django.db import models

from apps.core.images import optimize_uploads
from apps.core.validators import IMAGE_VALIDATORS


class HomeSection(models.Model):
    class SectionType(models.TextChoices):
        HERO = "hero"
        PRODUCT_CAROUSEL = "product_carousel"

    type = models.CharField(max_length=20, choices=SectionType.choices)
    title = models.CharField(max_length=120, blank=True)
    collection = models.ForeignKey(
        "catalog.Collection", null=True, blank=True, related_name="home_sections", on_delete=models.SET_NULL
    )
    view_all_link = models.CharField(max_length=255, blank=True)
    max_products = models.PositiveSmallIntegerField(default=25)
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.title or self.get_type_display()

    def clean(self):
        if self.type == self.SectionType.PRODUCT_CAROUSEL and not self.collection_id:
            raise ValidationError({"collection": "A product carousel needs a collection."})


class HeroBanner(models.Model):
    section = models.ForeignKey(HomeSection, related_name="banners", on_delete=models.CASCADE)
    image_desktop = models.ImageField(upload_to="banners/", validators=IMAGE_VALIDATORS)
    image_mobile = models.ImageField(upload_to="banners/", blank=True, validators=IMAGE_VALIDATORS)
    heading = models.CharField(max_length=120, blank=True)
    subheading = models.CharField(max_length=255, blank=True)
    button_text = models.CharField(max_length=40, blank=True)
    button_link = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.heading or f"Banner #{self.pk}"

    def save(self, *args, **kwargs):
        optimize_uploads(self, "image_desktop", "image_mobile")
        super().save(*args, **kwargs)
