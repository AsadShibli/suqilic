"""Versioned cache for public, user-independent GET endpoints.

Every key embeds a global version number; any catalog/content write bumps it, which orphans all cached
responses at once (they then expire by TTL). This avoids tracking which URLs a given change affects.
"""

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from rest_framework.response import Response

VERSION_KEY = "public-cache:version"


def current_version() -> int:
    return cache.get_or_set(VERSION_KEY, 1, timeout=None)


def invalidate_public_cache(*_args, **_kwargs) -> None:
    try:
        cache.incr(VERSION_KEY)
    except ValueError:  # key missing or evicted
        cache.set(VERSION_KEY, 2, timeout=None)


def cache_public(view_method):
    """Cache a successful GET response's data, keyed by host, full path and renderer format."""

    @wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        key = (
            f"public-cache:{current_version()}:{request.get_host()}:"
            f"{request.accepted_renderer.format}:{request.get_full_path()}"
        )
        data = cache.get(key)
        if data is not None:
            return Response(data, headers={"X-Cache": "HIT"})
        response = view_method(self, request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(key, response.data, settings.PUBLIC_CACHE_TIMEOUT)
            response["X-Cache"] = "MISS"
        return response

    return wrapper
