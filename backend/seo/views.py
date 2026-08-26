from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import LandingPage
from .serializers import LandingPageDetailSerializer, LandingPageListSerializer


class LandingPageListAPIView(ListAPIView):
    serializer_class = LandingPageListSerializer

    def get_queryset(self):
        queryset = (
            LandingPage.objects
            .filter(is_active=True)
            .select_related("category")
            .order_by("sort_order", "title")
        )

        # Используется блоком "Смотрите также" на страницах каталога
        # (frontend/app/[slug]/page.tsx), чтобы показать соседние SEO-страницы
        # того же раздела (хаб, размеры, регион) без хардкода списка ссылок.
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)

        return queryset


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
                "images",
                "related_projects__category",
            )
        )
