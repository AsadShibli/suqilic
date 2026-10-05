from django.conf import settings


def noindex_middleware(get_response):
    """On staging (NOINDEX=true) tell crawlers not to index any response, including media."""

    def middleware(request):
        response = get_response(request)
        if settings.NOINDEX:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return middleware


def public_cache_invalidation_middleware(get_response):
    """Any successful write through the staff API may change what shoppers see, including bulk
    `.update()` calls that skip model signals, so drop the public response cache."""
    from .cache import invalidate_public_cache

    def middleware(request):
        response = get_response(request)
        if request.method not in ("GET", "HEAD", "OPTIONS") and request.path.startswith("/api/v1/admin/") \
                and response.status_code < 400:
            invalidate_public_cache()
        return response

    return middleware
