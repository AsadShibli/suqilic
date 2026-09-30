from django.conf import settings


def noindex_middleware(get_response):
    """On staging (NOINDEX=true) tell crawlers not to index any response, including media."""

    def middleware(request):
        response = get_response(request)
        if settings.NOINDEX:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response

    return middleware
