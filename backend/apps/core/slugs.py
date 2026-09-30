from django.utils.text import slugify


def unique_slug(model, value: str, instance=None) -> str:
    base = slugify(value)[:200] or "item"
    slug, n = base, 2
    qs = model.objects.exclude(pk=instance.pk) if instance else model.objects.all()
    while qs.filter(slug=slug).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


class AutoSlugMixin:
    """Generate `slug` from `slug_source` on create, or on update when explicitly sent blank."""

    slug_source = "title"

    def get_extra_kwargs(self):
        return {**super().get_extra_kwargs(), "slug": {"required": False, "allow_blank": True}}

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get("slug") and (self.instance is None or "slug" in attrs):
            source = attrs.get(self.slug_source) or getattr(self.instance, self.slug_source, "")
            attrs["slug"] = unique_slug(self.Meta.model, source, self.instance)
        return attrs
