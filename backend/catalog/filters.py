"""Фильтры каталога проектов и счётчики вариантов для панели фильтров.

Список проектов (ProjectListAPIView) и цифры напротив вариантов
(ProjectFacetsAPIView) отбирают проекты одной функцией matches(): иначе
«2 этажа — 10» в панели расходилось бы с тем, что каталог покажет после выбора.

Варианты «Тип», «Этажность» и «Материал» берутся из самих проектов, а не из
списка в коде: появится дом на 3 этажа или материал с группой «Клеёный брус» —
он сам окажется в фильтре. Проектов в каталоге сотни, поэтому отбор идёт в
Python по заранее загруженным проектам — цену и раньше можно было узнать только
через PricingService, а одна функция отбора надёжнее двух (ORM + Python).
"""

from collections import Counter
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation

from django.db.models import Prefetch
from django.utils.text import slugify

from .models import Material, Project, ProjectOffer
from .pricing import PricingService

_CYRILLIC_TO_LATIN = str.maketrans(
    {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
)  # fmt: skip

# Раньше ?material= принимал Material.kind (regular, profiled, dry) — такие
# ссылки продолжают работать.
LEGACY_MATERIAL_KINDS = frozenset(Material.Kind.values)


def material_group_value(group_title: str) -> str:
    """Ключ группы материалов для адреса: «Клеёный брус» → kleenyy-brus."""
    return slugify(group_title.lower().translate(_CYRILLIC_TO_LATIN))


def floors_value(floors: Decimal) -> str:
    return format(Decimal(floors).normalize(), "f")


def floors_label(floors: Decimal) -> str:
    floors = Decimal(floors)
    whole = int(floors)
    if floors == whole:
        return f"{whole} {_plural(whole, 'этаж', 'этажа', 'этажей')}"
    if floors - whole == Decimal("0.5"):
        return f"{whole} + мансарда"
    return f"{floors_value(floors)} этажа"


def _plural(number: int, one: str, few: str, many: str) -> str:
    if number % 10 == 1 and number % 100 != 11:
        return one
    if number % 10 in (2, 3, 4) and number % 100 not in (12, 13, 14):
        return few
    return many


def _split(raw) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def _decimal(raw) -> Decimal | None:
    if raw is None:
        return None
    try:
        value = Decimal(str(raw).strip().replace(" ", "").replace(",", "."))
    except InvalidOperation:
        return None
    return value if value.is_finite() else None


def _number(value: Decimal) -> int | float:
    value = Decimal(value)
    return int(value) if value == value.to_integral_value() else float(value)


@dataclass
class CatalogQuery:
    category: str = ""
    featured: bool = False
    # Размер посадочной страницы (/doma-iz-brusa-6x6) — не выбор посетителя, а
    # граница самой выборки: в счётчиках и диапазонах тоже.
    width: Decimal | None = None
    length: Decimal | None = None

    construction_types: list[str] = field(default_factory=list)
    floors: list[Decimal] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    size_min: Decimal | None = None
    size_max: Decimal | None = None
    area_min: Decimal | None = None
    area_max: Decimal | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None

    @classmethod
    def from_params(cls, params) -> "CatalogQuery":
        floors = (_decimal(value) for value in _split(params.get("floors")))
        return cls(
            category=(params.get("category") or "").strip(),
            featured=params.get("featured") in ("1", "true", "yes", "да"),
            width=_decimal(params.get("width")),
            length=_decimal(params.get("length")),
            construction_types=_split(params.get("construction_type")),
            floors=[value for value in floors if value is not None],
            materials=_split(params.get("material")),
            size_min=_decimal(params.get("size_min")),
            size_max=_decimal(params.get("size_max")),
            area_min=_decimal(params.get("area_min")),
            area_max=_decimal(params.get("area_max")),
            price_min=_decimal(params.get("price_min")),
            price_max=_decimal(params.get("price_max")),
        )

    @property
    def has_visitor_filters(self) -> bool:
        ranges = (self.size_min, self.size_max, self.area_min, self.area_max, self.price_min, self.price_max)
        return bool(self.construction_types or self.floors or self.materials) or any(
            value is not None for value in ranges
        )

    @property
    def filters_by_price(self) -> bool:
        return self.price_min is not None or self.price_max is not None

    def base_queryset(self):
        queryset = Project.objects.filter(is_active=True)
        if self.category:
            queryset = queryset.filter(category__slug=self.category)
        if self.featured:
            queryset = queryset.filter(is_featured=True)
        if self.width is not None:
            queryset = queryset.filter(width=self.width)
        if self.length is not None:
            queryset = queryset.filter(length=self.length)
        return queryset


@dataclass(frozen=True)
class ProjectFacts:
    pk: int
    construction_type: str
    floors: Decimal | None
    width: Decimal | None
    length: Decimal | None
    area: Decimal | None
    material_groups: frozenset[str]
    material_kinds: frozenset[str]
    price: int | None


@dataclass
class CatalogSnapshot:
    projects: list[ProjectFacts]
    material_titles: dict[str, str]
    material_order: dict[str, tuple[int, int]]


def load_snapshot(query: CatalogQuery, *, with_prices: bool) -> CatalogSnapshot:
    offers = ProjectOffer.objects.select_related("material", "build_package")
    projects = query.base_queryset().select_related("category").prefetch_related(Prefetch("offers", queryset=offers))
    pricing = PricingService() if with_prices else None

    facts, titles, order = [], {}, {}
    for project in projects:
        groups, kinds = set(), set()
        for offer in project.offers.all():
            material = offer.material
            if not material.is_active:
                continue
            value = material_group_value(material.group_title) or f"material-{material.pk}"
            groups.add(value)
            kinds.add(material.kind)
            titles.setdefault(value, material.group_title or material.title)
            position = (material.sort_order, material.pk)
            order[value] = min(order.get(value, position), position)

        facts.append(
            ProjectFacts(
                pk=project.pk,
                construction_type=project.construction_type,
                floors=project.floors,
                width=project.width,
                length=project.length,
                area=project.area,
                material_groups=frozenset(groups),
                material_kinds=frozenset(kinds),
                price=pricing.get_project_price_from(project) if pricing else None,
            )
        )
    return CatalogSnapshot(facts, titles, order)


def _within(value, minimum, maximum) -> bool:
    if minimum is None and maximum is None:
        return True
    if value is None:
        return False
    return (minimum is None or value >= minimum) and (maximum is None or value <= maximum)


def matches(query: CatalogQuery, facts: ProjectFacts, skip: str | None = None) -> bool:
    """Подходит ли проект под фильтры; skip — группа, которую не учитывать.

    Цифра напротив варианта считается без выбора в его собственной группе:
    внутри группы варианты складываются («1 этаж» или «2 этажа»), и отмеченный
    «1 этаж» не должен обнулять «2 этажа».
    """
    if skip != "construction_type" and query.construction_types:
        if facts.construction_type not in query.construction_types:
            return False
    if skip != "floors" and query.floors:
        if facts.floors is None or facts.floors not in query.floors:
            return False
    if skip != "material" and query.materials:
        wanted = set(query.materials)
        if not (wanted & facts.material_groups or wanted & facts.material_kinds):
            return False
    # «Размер» — один диапазон и для ширины, и для длины: 6–10 м покажет 6х8 и
    # 7х9, но не 5х12.
    if skip != "size" and not (
        _within(facts.width, query.size_min, query.size_max) and _within(facts.length, query.size_min, query.size_max)
    ):
        return False
    if skip != "area" and not _within(facts.area, query.area_min, query.area_max):
        return False
    if skip != "price" and not _within(facts.price, query.price_min, query.price_max):
        return False
    return True


def matching_project_ids(query: CatalogQuery) -> list[int]:
    snapshot = load_snapshot(query, with_prices=query.filters_by_price)
    return [facts.pk for facts in snapshot.projects if matches(query, facts)]


def _bounds(values, quantum: str, *, start: str | None = None):
    values = [Decimal(value) for value in values if value is not None]
    if not values:
        return None
    step = Decimal(quantum)
    low = (min(values) / step).to_integral_value(ROUND_FLOOR) * step
    high = (max(values) / step).to_integral_value(ROUND_CEILING) * step
    # Шкала размера и площади начинается с 1, а не с самого маленького проекта:
    # «от 6» и «от 32» в пустом фильтре читались как уже заданное ограничение.
    # Единственное значение (страница 6х6) шкалы не получает — ползунок скрыт.
    if start is not None and high > low:
        low = min(low, Decimal(start))
    return {"min": _number(low), "max": _number(high), "step": _number(step)}


def build_facets(query: CatalogQuery) -> dict:
    snapshot = load_snapshot(query, with_prices=True)
    projects = snapshot.projects

    def options(group, values_of, label_of, sort_key, selected, count_values_of=None):
        count_values_of = count_values_of or values_of
        pool = [facts for facts in projects if matches(query, facts, skip=group)]
        counts = Counter(value for facts in pool for value in count_values_of(facts))
        present = {value for facts in projects for value in values_of(facts)}
        # Отмеченное, но отсутствующее в выборке (например, по старой ссылке)
        # тоже попадает в список — иначе галочку было бы не снять.
        missing = [value for value in dict.fromkeys(selected) if value not in present]
        return [
            {"value": value, "label": label_of(value), "count": counts.get(value, 0)}
            for value in sorted(present, key=sort_key) + missing
        ]

    construction_order = list(Project.ConstructionType.values)
    construction_types = options(
        "construction_type",
        values_of=lambda facts: [facts.construction_type],
        label_of=lambda value: (
            Project.ConstructionType(value).label if value in Project.ConstructionType.values else value
        ),
        sort_key=lambda value: construction_order.index(value) if value in construction_order else len(construction_order),
        selected=query.construction_types,
    )

    floors = options(
        "floors",
        values_of=lambda facts: [] if facts.floors is None else [floors_value(facts.floors)],
        label_of=lambda value: floors_label(Decimal(value)),
        sort_key=Decimal,
        selected=[floors_value(value) for value in query.floors],
    )

    def material_label(value):
        if value in snapshot.material_titles:
            return snapshot.material_titles[value]
        if value in LEGACY_MATERIAL_KINDS:
            return Material.Kind(value).label
        return value

    materials = options(
        "material",
        values_of=lambda facts: facts.material_groups,
        count_values_of=lambda facts: facts.material_groups | facts.material_kinds,
        label_of=material_label,
        sort_key=lambda value: (snapshot.material_order.get(value, (0, 0)), material_label(value)),
        selected=query.materials,
    )

    # Шкалы ползунков — по всей выборке, а не по уже отфильтрованной: иначе
    # при каждом клике границы прыгали бы вместе с бегунками.
    sized = [facts for facts in projects if facts.width is not None and facts.length is not None]
    ranges = {
        "size": _bounds(
            [min(f.width, f.length) for f in sized] + [max(f.width, f.length) for f in sized], "0.5", start="1"
        ),
        "area": _bounds([facts.area for facts in projects], "1", start="1"),
        "price": _bounds([facts.price for facts in projects], "10000"),
    }

    return {
        "total": sum(1 for facts in projects if matches(query, facts)),
        "construction_types": construction_types,
        "floors": floors,
        "materials": materials,
        "ranges": ranges,
    }
