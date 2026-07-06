from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import LandingPage
from .serializers import LandingPageDetailSerializer, LandingPageListSerializer


class LandingPageListAPIView(ListAPIView):
    serializer_class = LandingPageListSerializer

    def get_queryset(self):
        return (
            LandingPage.objects
            .filter(is_active=True)
            .select_related("category")
            .order_by("sort_order", "title")
        )


class LandingPageDetailAPIView(RetrieveAPIView):
    serializer_class = LandingPageDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            LandingPage.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                "faqs",
                "related_projects__category",
            )
        )