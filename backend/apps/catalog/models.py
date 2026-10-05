from django.apps import apps
from django.db import models, transaction
from django.db.models import Min, OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from apps.core.images import optimize_uploads
from apps.core.models import TimeStampedModel
from apps.core.validators import IMAGE_VALIDATORS


class SeoFields(models.Model):
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=160, blank=True)

    class Meta:
        abstract = True


class Collection(TimeStampedModel, SeoFields):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    description = models.TextField(blank=True)
    banner_image = models.ImageField(upload_to="collections/", blank=True, validators=IMAGE_VALIDATORS)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField("Product", through="CollectionProduct", related_name="collections")

    class Meta:
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        optimize_uploads(self, "banner_image")
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Product.Status.ACTIVE)

    def with_listing_data(self):
        active_variants = Q(variants__is_active=True)
        return self.annotate(
            price_from=Min("variants__price", filter=active_variants),
            total_stock=Sum("variants__stock_quantity", filter=active_variants),
        )

    def with_sales(self):
        order_items = apps.get_model("orders", "OrderItem").objects.filter(variant__product=OuterRef("pk"))
        units = order_items.values("variant__product").annotate(total=Sum("quantity")).values("total")
        return self.annotate(units_sold=Coalesce(Subquery(units), 0))


class Product(TimeStampedModel, SeoFields):
    class Status(models.TextChoices):
        ACTIVE = "active"
        DRAFT = "draft"
        ARCHIVED = "archived"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True)
    video_url = models.URLField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class CollectionProduct(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="collection_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="collection_products")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [models.UniqueConstraint(fields=["collection", "product"], name="uniq_collection_product")]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/", validators=IMAGE_VALIDATORS)
    thumbnail = models.ImageField(upload_to="products/thumbs/", blank=True, editable=False)
    alt_text = models.CharField(max_length=200, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_main", "position", "id"]

    def __str__(self):
        return f"{self.product} image #{self.pk}"

    def save(self, *args, **kwargs):
        # The full-size WebP is made inline (the editor shows it right away); the thumbnail is a background task.
        if optimize_uploads(self, "image"):
            self.thumbnail = ""
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)
        if self.image and not self.thumbnail:
            from apps.core.tasks import dispatch

            from .tasks import build_product_thumbnail

            transaction.on_commit(lambda: dispatch(build_product_thumbnail, self.pk))


class ProductOption(models.Model):
    product = models.ForeignKey(Product, related_name="options", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [models.UniqueConstraint(fields=["product", "name"], name="uniq_product_option")]

    def __str__(self):
        return f"{self.product}: {self.name}"


class ProductOptionValue(models.Model):
    option = models.ForeignKey(ProductOption, related_name="values", on_delete=models.CASCADE)
    value = models.CharField(max_length=80)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [models.UniqueConstraint(fields=["option", "value"], name="uniq_option_value")]

    def __str__(self):
        return self.value


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField(max_length=64, unique=True, null=True, blank=True)
    title = models.CharField(max_length=150, default="Default")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    option_values = models.ManyToManyField(ProductOptionValue, blank=True, related_name="variants")

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.product} — {self.title}"

    @property
    def in_stock(self):
        return self.is_active and self.stock_quantity > 0
