from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.cache import cache_public

from .models import HomeSection
from .serializers import HomeSectionSerializer


class HomeView(APIView):
    @cache_public
    def get(self, request):
        sections = HomeSection.objects.filter(is_visible=True).select_related("collection").prefetch_related("banners")
        return Response(HomeSectionSerializer(sections, many=True, context={"request": request}).data)
