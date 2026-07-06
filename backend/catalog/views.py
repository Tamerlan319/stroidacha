from rest_framework.generics import ListAPIView, RetrieveAPIView

from .models import Project, ProjectCategory
from .serializers import (
    ProjectCategorySerializer,
    ProjectDetailSerializer,
    ProjectListSerializer,
)


class ProjectCategoryListAPIView(ListAPIView):
    serializer_class = ProjectCategorySerializer

    def get_queryset(self):
        return ProjectCategory.objects.filter(is_active=True).order_by(
            "sort_order",
            "title",
        )


class ProjectListAPIView(ListAPIView):
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        queryset = (
            Project.objects
            .filter(is_active=True)
            .select_related("category")
            .order_by("sort_order", "-created_at")
        )

        category = self.request.query_params.get("category")
        construction_type = self.request.query_params.get("construction_type")
        featured = self.request.query_params.get("featured")
        area_min = self.request.query_params.get("area_min")
        area_max = self.request.query_params.get("area_max")
        price_min = self.request.query_params.get("price_min")
        price_max = self.request.query_params.get("price_max")
        floors = self.request.query_params.get("floors")

        if category:
            queryset = queryset.filter(category__slug=category)

        if construction_type:
            queryset = queryset.filter(construction_type=construction_type)

        if featured in ("1", "true", "yes", "да"):
            queryset = queryset.filter(is_featured=True)

        if area_min:
            queryset = queryset.filter(area__gte=area_min)

        if area_max:
            queryset = queryset.filter(area__lte=area_max)

        if price_min:
            queryset = queryset.filter(price_from__gte=price_min)

        if price_max:
            queryset = queryset.filter(price_from__lte=price_max)

        if floors:
            queryset = queryset.filter(floors=floors)

        return queryset


class ProjectDetailAPIView(RetrieveAPIView):
    serializer_class = ProjectDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Project.objects
            .filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                "images",
                "plans",
                "price_options",
                "addons",
                "packages__sections__items",
            )
        )