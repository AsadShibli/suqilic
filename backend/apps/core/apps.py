from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        from django.apps import apps
        from django.db.models.signals import m2m_changed, post_delete, post_save

        from .cache import invalidate_public_cache

        # Anything a shopper can see; leave out private records like messages and subscribers.
        public = [*apps.get_app_config("catalog").get_models(), *apps.get_app_config("storefront").get_models()]
        public += [apps.get_model("core", name) for name in ("SiteSettings", "MenuItem", "Page", "HowToVideo")]
        for model in public:
            label = model._meta.label
            post_save.connect(invalidate_public_cache, sender=model, dispatch_uid=f"public-cache-save-{label}")
            post_delete.connect(invalidate_public_cache, sender=model, dispatch_uid=f"public-cache-del-{label}")
        m2m_changed.connect(invalidate_public_cache, dispatch_uid="public-cache-m2m")
