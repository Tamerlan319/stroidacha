"""YML-фид "Недвижимость" для Яндекс.Вебмастера.

Показывает готовые проекты домов/бань в отдельном коммерческом блоке
поисковой выдачи Яндекса (не в органической выдаче) — независимо от
Яндекс Бизнеса и от того, какой сайт сейчас официальный на карточке
организации: это отдельный механизм, привязанный к сайту через
Вебмастер, а не к организации.

Формат по документации:
https://yandex.ru/support/webmaster/ru/search-appearance/realty.html
Категория "Исполнители" не подошла — её поля (рейтинг исполнителя, годы
опыта) заточены под наём конкретного мастера, а не под каталог готовых
проектов с фиксированной ценой и площадью.
"""

from __future__ import annotations

from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.views import View

from .models import Project
from .pricing import PricingService

# id из официального справочника категорий Яндекс.Недвижимости — "Дом".
# Отдельной категории для бань в справочнике нет; ближайшая по смыслу —
# тоже "Дом" (готовая отдельно стоящая постройка, не квартира/участок).
REALTY_CATEGORY_ID = "3"

# slug категории каталога -> (id сета, название сета, страница-хаб)
CATEGORY_SETS: dict[str, tuple[str, str, str]] = {
    "houses": ("s-houses", "Дома из бруса под ключ", "/doma-iz-brusa"),
    "baths": ("s-baths", "Бани из бруса под ключ", "/bani-iz-brusa"),
}

MAX_PICTURES_PER_OFFER = 10


def _format_area(value: Decimal) -> str:
    # Тот же трюк, что и в catalog.Project.computed_size_text: area хранится
    # как NUMERIC, поэтому Decimal приходит с фиксированными знаками после
    # точки (например, "70.00"), а format(decimal, "g") их не убирает.
    return format(Decimal(value).normalize(), "f")


def _add(parent: Element, tag: str, value, **attrib) -> Element | None:
    if value is None or value == "":
        return None
    element = SubElement(parent, tag, attrib)
    element.text = str(value)
    return element


def build_realty_feed(request: HttpRequest) -> bytes:
    site_url = settings.SITE_URL.rstrip("/")
    pricing = PricingService()

    projects = list(
        Project.objects.filter(
            is_active=True,
            category__slug__in=CATEGORY_SETS.keys(),
        )
        .select_related("category")
        .prefetch_related("images", "offers")
        .order_by("category__slug", "sort_order")
    )

    catalog = Element(
        "yml_catalog", {"date": timezone.now().strftime("%Y-%m-%d %H:%M")}
    )
    shop = SubElement(catalog, "shop")
    _add(shop, "name", "Брусодел")
    _add(shop, "company", 'ООО "СтройДача"')
    _add(shop, "url", site_url)

    currencies = SubElement(shop, "currencies")
    SubElement(currencies, "currency", {"id": "RUR", "rate": "1"})

    # Обязательный элемент по спецификации YML — каждый offer/categoryId
    # должен ссылаться на что-то, объявленное здесь, и categories должен
    # идти строго до offers. Раньше этого блока не было вообще: Яндекс
    # ругался и на порядок элементов, и общей ошибкой парсера — categories
    # у него просто не находился.
    categories_el = SubElement(shop, "categories")
    _add(categories_el, "category", "Дом", id=REALTY_CATEGORY_ID)

    used_category_slugs = {project.category.slug for project in projects}
    sets_el = SubElement(shop, "sets")
    for slug, (set_id, name, path) in CATEGORY_SETS.items():
        if slug not in used_category_slugs:
            continue
        set_el = SubElement(sets_el, "set", {"id": set_id})
        _add(set_el, "name", name)
        _add(set_el, "url", f"{site_url}{path}")

    offers_el = SubElement(shop, "offers")
    for project in projects:
        set_info = CATEGORY_SETS.get(project.category.slug)
        if not set_info:
            continue
        set_id = set_info[0]

        price = pricing.get_project_price_from(project)
        if price is None:
            # Без цены предложение не пройдёт модерацию — пропускаем, а не
            # публикуем с пустой/нулевой ценой.
            continue

        offer = SubElement(offers_el, "offer", {"id": project.slug})
        _add(offer, "name", project.seo_title or project.title)
        _add(offer, "url", f"{site_url}/projects/{project.slug}")
        _add(offer, "categoryId", REALTY_CATEGORY_ID)
        _add(offer, "price", price, **{"from": "true"})
        _add(offer, "currencyId", "RUR")
        _add(offer, "set-ids", set_id)
        _add(offer, "param", "1.0", name="Конверсия")
        _add(offer, "param", "Продажа", name="Тип предложения")
        _add(offer, "param", "Под ключ", name="Отделка")
        if project.area is not None:
            _add(offer, "param", _format_area(project.area), name="Площадь")

        description = project.seo_description or project.short_description
        _add(offer, "description", description)

        picture_fields = []
        if project.main_image:
            picture_fields.append(project.main_image)
        picture_fields.extend(
            image.image for image in project.images.all() if image.image
        )
        for picture in picture_fields[:MAX_PICTURES_PER_OFFER]:
            _add(offer, "picture", request.build_absolute_uri(picture.url))

    xml_declaration = b'<?xml version="1.0" encoding="utf-8"?>\n'
    return xml_declaration + tostring(catalog, encoding="utf-8")


class RealtyFeedView(View):
    """GET /api/feeds/realty.yml — публичный, без аутентификации: это ровно
    тот URL, который вручную указывается в Яндекс.Вебмастере при загрузке
    фида (см. DEPLOYMENT.md > "YML-фид Недвижимость для Яндекса")."""

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        xml_bytes = build_realty_feed(request)
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")
