from django.db.models import Case, IntegerField, Prefetch, When
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

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
        queryset = (
            Project.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("images", Prefetch("offers", queryset=OFFER_LIST_QS))
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
        material = self.request.query_params.get("material")
        size_min = self.request.query_params.get("size_min")
        size_max = self.request.query_params.get("size_max")
        width = self.request.query_params.get("width")
        length = self.request.query_params.get("length")
        ordering = self.request.query_params.get("ordering", "default")

        def split_values(raw):
            return [item.strip() for item in raw.split(",") if item.strip()]

        if category:
            queryset = queryset.filter(category__slug=category)
        if construction_type:
            # Поддерживает несколько значений через запятую — фильтр каталога
            # позволяет отметить сразу "Брус" и "Каркас" галочками.
            queryset = queryset.filter(construction_type__in=split_values(construction_type))
        if featured in ("1", "true", "yes", "да"):
            queryset = queryset.filter(is_featured=True)
        if area_min:
            queryset = queryset.filter(area__gte=area_min)
        if area_max:
            queryset = queryset.filter(area__lte=area_max)
        if floors:
            queryset = queryset.filter(floors__in=split_values(floors))
        if material:
            # У проекта нет прямого поля material — материал приходит через
            # ProjectOffer (проект может продаваться в нескольких материалах).
            # distinct() нужен, чтобы проект с несколькими подходящими
            # предложениями не задваивался в выдаче.
            queryset = queryset.filter(
                offers__material__kind__in=split_values(material)
            ).distinct()
        # "Размер" в фильтре каталога — один диапазон, применяется и к ширине,
        # и к длине (например, 6–10 м покажет 6х8, 7х9, но не 5х12).
        if size_min:
            queryset = queryset.filter(width__gte=size_min, length__gte=size_min)
        if size_max:
            queryset = queryset.filter(width__lte=size_max, length__lte=size_max)
        # Точный фильтр по размеру footprint (например, "6x6"). Используется
        # размерными SEO-страницами (LandingPage.filter_width/filter_length),
        # чтобы каталог на такой странице показывал только проекты этого
        # размера, а не весь каталог категории.
        if width:
            queryset = queryset.filter(width=width)
        if length:
            queryset = queryset.filter(length=length)

        # Эффективная цена зависит от нескольких коэффициентов и может быть
        # вычислена только единым PricingService. Для текущего каталога (~сотни
        # проектов) этот проход предсказуем и исключает рассинхрон с калькулятором.
        if price_min or price_max:
            try:
                min_value = int(price_min) if price_min else None
                max_value = int(price_max) if price_max else None
            except (TypeError, ValueError):
                return queryset

            pricing = PricingService()
            matching_ids = []
            for project in queryset:
                effective = pricing.get_project_price_from(project)
                if effective is None:
                    continue
                if min_value is not None and effective < min_value:
                    continue
                if max_value is not None and effective > max_value:
                    continue
                matching_ids.append(project.pk)
            queryset = queryset.filter(pk__in=matching_ids)

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
