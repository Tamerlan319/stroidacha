from django.db.models import Case, IntegerField, Prefetch, When
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import CatalogQuery, build_facets, matching_project_ids
from .models import (
    Project,
    ProjectCategory,
    ProjectContentSection,
    ProjectExtraOption,
    ProjectFoundation,
    ProjectOffer,
    ProjectRoofCovering,
)
from .pricing import PricingService
from .serializers import ProjectCategorySerializer, ProjectDetailSerializer, ProjectListSerializer


OFFER_LIST_QS = ProjectOffer.objects.select_related("material", "build_package")
OFFER_DETAIL_QS = OFFER_LIST_QS.prefetch_related("build_package__sections__items")


class OptionalProjectPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        # Старые внутренние запросы продолжают получать обычный массив.
        # Пагинация включается явно каталогом через page/page_size.
        if "page" not in request.query_params and "page_size" not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)


class ProjectCategoryListAPIView(ListAPIView):
    serializer_class = ProjectCategorySerializer

    def get_queryset(self):
        return ProjectCategory.objects.filter(is_active=True).order_by("sort_order", "title")


class ProjectListAPIView(ListAPIView):
    serializer_class = ProjectListSerializer
    pagination_class = OptionalProjectPagination

    def get_queryset(self):
        # Категория, featured и точный размер посадочной страницы (width/length)
        # ограничивают саму выборку — см. CatalogQuery.base_queryset.
        query = CatalogQuery.from_params(self.request.query_params)
        queryset = (
            query.base_queryset()
            .select_related("category")
            .prefetch_related("images", "plans", Prefetch("offers", queryset=OFFER_LIST_QS))
            .order_by("sort_order", "-created_at")
        )
        ordering = self.request.query_params.get("ordering", "default")

        # Фильтры посетителя (тип, этажность, материал, размер, площадь, цена)
        # отбираются той же функцией, что считает цифры в панели фильтров
        # (/api/projects/facets/), — иначе цифра и выдача могли бы разойтись.
        if query.has_visitor_filters:
            queryset = queryset.filter(pk__in=matching_project_ids(query))

        ordering_fields = {
            "default": ("sort_order", "-created_at"),
            "newest": ("-created_at", "id"),
            "area_asc": ("area", "sort_order"),
            "area_desc": ("-area", "sort_order"),
            "title": ("title", "id"),
        }
        if ordering in {"price_asc", "price_desc"}:
            pricing = PricingService()
            priced_projects = [
                (project.pk, pricing.get_project_price_from(project))
                for project in queryset
            ]
            available_prices = [item for item in priced_projects if item[1] is not None]
            unavailable_prices = [item for item in priced_projects if item[1] is None]
            available_prices.sort(
                key=lambda item: item[1],
                reverse=ordering == "price_desc",
            )
            priced_projects = available_prices + unavailable_prices
            ordered_ids = [project_id for project_id, _ in priced_projects]
            if ordered_ids:
                preserved_order = Case(
                    *[
                        When(pk=project_id, then=position)
                        for position, project_id in enumerate(ordered_ids)
                    ],
                    output_field=IntegerField(),
                )
                queryset = queryset.filter(pk__in=ordered_ids).order_by(preserved_order)
            else:
                queryset = queryset.none()
        else:
            queryset = queryset.order_by(*ordering_fields.get(ordering, ordering_fields["default"]))

        return queryset


class ProjectFacetsAPIView(APIView):
    """Варианты фильтров каталога и сколько проектов найдётся с каждым из них.

    Параметры те же, что у списка проектов. Панель фильтров запрашивает их при
    каждом изменении, ещё до «Показать»: цифры напротив вариантов, число на
    кнопке и границы ползунков размера, площади и цены.
    """

    def get(self, request):
        return Response(build_facets(CatalogQuery.from_params(request.query_params)))


class ProjectDetailAPIView(RetrieveAPIView):
    serializer_class = ProjectDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Project.objects.filter(is_active=True)
            .select_related("category", "technical")
            .prefetch_related(
                "images",
                "plans",
                Prefetch("offers", queryset=OFFER_DETAIL_QS),
                "package_overrides",
                Prefetch(
                    "foundations",
                    queryset=ProjectFoundation.objects.select_related("foundation"),
                ),
                Prefetch(
                    "roof_coverings",
                    queryset=ProjectRoofCovering.objects.select_related("covering"),
                ),
                Prefetch(
                    "extra_options",
                    queryset=ProjectExtraOption.objects.select_related("option"),
                ),
                Prefetch(
                    "content_sections",
                    queryset=ProjectContentSection.objects.filter(is_active=True),
                ),
            )
        )
