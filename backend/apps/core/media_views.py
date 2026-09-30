from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from .models import StoredFile


@require_GET
def serve_media(request, path):
    """Serve a DatabaseStorage file. Names are unique per upload, so responses are cached as immutable."""
    file = StoredFile.objects.filter(name=path).values("content", "content_type").first()
    if file is None:
        raise Http404
    response = HttpResponse(bytes(file["content"]), content_type=file["content_type"])
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
