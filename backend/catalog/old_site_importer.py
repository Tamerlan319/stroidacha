from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify

from .models import (
    BuildPackageItem,
    BuildPackageSection,
    Project,
    ProjectCategory,
    ProjectContentSection,
    ProjectExtraOption,
    ProjectFoundation,
    ProjectImage,
    ProjectOffer,
    ProjectPackageOverride,
    ProjectPlan,
    ProjectRoofCovering,
)
from .importers import (
    get_or_create_build_package,
    get_or_create_extra_option,
    get_or_create_foundation,
    get_or_create_material,
    get_or_create_roof_covering,
)

try:
    from bs4 import BeautifulSoup, Tag
except ImportError as exc:  # pragma: no cover - checked by management command at runtime
    BeautifulSoup = None
    Tag = object
    _BS4_IMPORT_ERROR = exc
else:
    _BS4_IMPORT_ERROR = None


DEFAULT_BASE_URL = "https://stroydacha.online"
DEFAULT_HOUSES_PATH = "/doma-iz-brusa/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "StroidachaCatalogMigration/1.0"
)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

MATERIAL_SPECS = (
    ("ordinary-150x150", "Обычный брус", "Обычный брус 150х150", r"Обычный\s+брус\s+150[хx×]150\s*:?\s*([\d\s]+)\s*руб"),
    ("ordinary-150x200", "Обычный брус", "Обычный брус 150х200", r"Обычный\s+брус\s+150[хx×]200\s*:?\s*([\d\s]+)\s*руб"),
    (
        "profiled-145x145",
        "Профилированный брус",
        "Профилированный брус 145х145",
        r"Профилированный\s+брус\s+145[хx×]145\s*:?\s*([\d\s]+)\s*руб",
    ),
    (
        "profiled-145x195",
        "Профилированный брус",
        "Профилированный брус 145х195",
        r"Профилированный\s+брус\s+145[хx×]195\s*:?\s*([\d\s]+)\s*руб",
    ),
    (
        "dry-140x140",
        "Брус камерной сушки",
        "Брус камерной сушки 140х140",
        r"Брус\s+камерной\s+сушки\s+140[хx×]140\s*:?\s*([\d\s]+)\s*руб",
    ),
    (
        "dry-140x190",
        "Брус камерной сушки",
        "Брус камерной сушки 140х190",
        r"Брус\s+камерной\s+сушки\s+140[хx×]190\s*:?\s*([\d\s]+)\s*руб",
    ),
)

ADDON_SPECS = (
    ("screw-piles", "Фундамент", "Свайный фундамент", r"Свайный\s+фундамент\s*([\d\s]+)\s*руб"),
    ("reinforced-piles", "Фундамент", "ЖБ сваи (ГОСТ)", r"ЖБ\s+сваи\s*\(ГОСТ\)\s*([\d\s]+)\s*руб"),
    ("metal-tile", "Кровля", "Металлочерепица", r"Металлочерепица\s*([\d\s]+)\s*руб"),
    ("ondulin", "Кровля", "Ондулин", r"Ондулин\s*([\d\s]+)\s*руб"),
    ("flexible-shingles", "Кровля", "Гибкая черепица", r"Гибкая\s+черепица\s*([\d\s]+)\s*руб"),
    ("metal-profile", "Кровля", "Металлопрофиль", r"Металлопрофиль\s*([\d\s]+)\s*руб"),
)


class OldSiteImportError(RuntimeError):
    pass


@dataclass
class IndexProject:
    url: str
    external_id: str
    bedrooms: int | None = None
    floors: Decimal | None = None


@dataclass
class MediaItem:
    url: str
    alt: str = ""
    is_plan: bool = False


@dataclass
class ParsedProject:
    source_url: str
    source_slug: str
    external_id: str
    title: str
    area: Decimal | None
    floors: Decimal | None
    floor_label: str
    bedrooms: int | None
    width: Decimal | None
    length: Decimal | None
    size_text: str
    price_options: list[dict] = field(default_factory=list)
    addons: list[dict] = field(default_factory=list)
    package_title: str = ""
    package_description: str = ""
    package_items: list[tuple[str, str]] = field(default_factory=list)
    description: str = ""
    content_sections: list[tuple[str, str]] = field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    media: list[MediaItem] = field(default_factory=list)

    @property
    def price_from(self) -> int | None:
        values = [item["price"] for item in self.price_options if item.get("price")]
        return min(values) if values else None


class OldSiteHouseImporter:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 30,
        pause: float = 0.15,
        stdout=None,
    ):
        if BeautifulSoup is None:
            raise OldSiteImportError(
                "Для импорта нужен пакет beautifulsoup4. "
                "Установи его: pip install beautifulsoup4"
            ) from _BS4_IMPORT_ERROR

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.pause = max(pause, 0)
        self.stdout = stdout

    def _log(self, message: str):
        if self.stdout:
            self.stdout.write(message)

    def _request_bytes(self, url: str) -> bytes:
        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.6",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise OldSiteImportError(f"Не удалось загрузить {url}: {exc}") from exc

    def _fetch_soup(self, url: str):
        html = self._request_bytes(url)
        if self.pause:
            time.sleep(self.pause)
        return BeautifulSoup(html, "html.parser")

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _money(value: str | None) -> int | None:
        if not value:
            return None
        digits = re.sub(r"\D", "", value)
        return int(digits) if digits else None

    @staticmethod
    def _decimal(value: str | None) -> Decimal | None:
        if not value:
            return None
        normalized = value.strip().replace(" ", "").replace(",", ".")
        try:
            return Decimal(normalized)
        except InvalidOperation:
            return None

    @staticmethod
    def _external_id(url: str, text: str = "") -> str | None:
        match = re.search(r"dom-db-(\d+)", url, flags=re.IGNORECASE)
        if not match:
            match = re.search(r"(?:ДБ|DB)[-\s]?(\d+)", text, flags=re.IGNORECASE)
        if not match:
            return None
        return f"DB-{int(match.group(1)):02d}"

    @staticmethod
    def _sort_order(external_id: str) -> int:
        match = re.search(r"(\d+)$", external_id)
        return int(match.group(1)) if match else 0

    def discover_projects(self, *, limit: int | None = None, max_pages: int = 20) -> list[IndexProject]:
        discovered: dict[str, IndexProject] = {}

        for page_number in range(1, max_pages + 1):
            path = DEFAULT_HOUSES_PATH if page_number == 1 else f"{DEFAULT_HOUSES_PATH}page/{page_number}/"
            url = urljoin(f"{self.base_url}/", path.lstrip("/"))
            self._log(f"Каталог, страница {page_number}: {url}")
            try:
                soup = self._fetch_soup(url)
            except OldSiteImportError as exc:
                # Pagination on the old WooCommerce site ends with a normal 404.
                # Treat that as the end of the catalog instead of aborting the whole import.
                if page_number > 1 and "HTTP Error 404" in str(exc):
                    self._log(f"Каталог закончился на странице {page_number - 1}.")
                    break
                raise

            cards = soup.select("ul.products li.product, li.product")
            page_items: list[IndexProject] = []

            for card in cards:
                link = card.find("a", href=re.compile(r"/proekt/dom-db-\d+/?", re.IGNORECASE))
                if not link:
                    continue
                href = urljoin(self.base_url, link.get("href"))
                card_text = self._clean_text(card.get_text(" ", strip=True))
                external_id = self._external_id(href, card_text)
                if not external_id:
                    continue

                bedrooms = None
                bedroom_match = re.search(r"(\d+)\s+спальн", card_text, flags=re.IGNORECASE)
                if bedroom_match:
                    bedrooms = int(bedroom_match.group(1))

                floors = None
                floor_match = re.search(
                    r"Этаж(?:ей|а|ность)?\s*:?\s*([12](?:[.,]5)?)",
                    card_text,
                    flags=re.IGNORECASE,
                )
                if floor_match:
                    floors = self._decimal(floor_match.group(1))

                page_items.append(IndexProject(href, external_id, bedrooms, floors))

            # Fallback for themes where WooCommerce cards do not use li.product.
            if not page_items:
                for link in soup.find_all("a", href=re.compile(r"/proekt/dom-db-\d+/?", re.IGNORECASE)):
                    href = urljoin(self.base_url, link.get("href"))
                    external_id = self._external_id(href, link.get_text(" ", strip=True))
                    if external_id:
                        page_items.append(IndexProject(href, external_id))

            new_count = 0
            for item in page_items:
                if item.external_id in discovered:
                    continue
                discovered[item.external_id] = item
                new_count += 1
                if limit and len(discovered) >= limit:
                    return list(discovered.values())

            if not page_items or new_count == 0:
                break

        return list(discovered.values())

    def parse_project(self, index: IndexProject) -> ParsedProject:
        soup = self._fetch_soup(index.url)
        main = soup.select_one("main, #main, .site-main") or soup.body or soup

        h1 = main.find("h1") or soup.find("h1")
        if not h1:
            raise OldSiteImportError(f"Не найден H1 проекта: {index.url}")
        title = self._clean_text(h1.get_text(" ", strip=True))

        full_text = main.get_text("\n", strip=True)
        # We only parse project-specific content before the related-products block.
        project_text = re.split(r"\n\s*Похожие\s+проекты\s*\n", full_text, maxsplit=1, flags=re.IGNORECASE)[0]

        area_match = re.search(r"Площадь\s*:?\s*([\d.,]+)\s*м", project_text, flags=re.IGNORECASE)
        area = self._decimal(area_match.group(1)) if area_match else None

        size_match = re.search(
            r"Размер\s*:?\s*([\d.,]+)\s*[хx×]\s*([\d.,]+)",
            project_text,
            flags=re.IGNORECASE,
        )
        width = self._decimal(size_match.group(1)) if size_match else None
        length = self._decimal(size_match.group(2)) if size_match else None
        size_text = ""
        if width is not None and length is not None:
            size_text = f"{width:g}х{length:g}".replace(".", ",")

        floor_label = ""
        floor_label_match = re.search(r"Этажность\s*:?\s*([^\n]+)", project_text, flags=re.IGNORECASE)
        if floor_label_match:
            floor_label = self._clean_text(floor_label_match.group(1))

        floors = index.floors or self._floors_from_label(floor_label)

        price_options = []
        for sort_order, (code, group_title, option_title, pattern) in enumerate(MATERIAL_SPECS, start=1):
            match = re.search(pattern, project_text, flags=re.IGNORECASE)
            if match:
                price_options.append(
                    {
                        "code": code,
                        "group_title": group_title,
                        "title": option_title,
                        "price": self._money(match.group(1)),
                        "sort_order": sort_order,
                    }
                )

        addons = []
        for sort_order, (code, group_title, addon_title, pattern) in enumerate(ADDON_SPECS, start=1):
            match = re.search(pattern, project_text, flags=re.IGNORECASE)
            if match:
                addons.append(
                    {
                        "code": code,
                        "group_title": group_title,
                        "title": addon_title,
                        "price": self._money(match.group(1)),
                        "sort_order": sort_order,
                    }
                )

        # The old site has a very different page layout. Free-form text blocks are
        # intentionally NOT imported: they easily capture unrelated page content.
        # We only migrate structured data (characteristics, prices, options, package rows, media).
        description, content_sections = "", []
        package_title, package_description, package_items = self._extract_package(main)
        media = self._extract_gallery(soup)

        page_title = ""
        if soup.title:
            page_title = self._clean_text(soup.title.get_text(" ", strip=True))
        meta_description = soup.find("meta", attrs={"name": re.compile(r"^description$", re.IGNORECASE)})
        seo_description = ""
        if meta_description and meta_description.get("content"):
            seo_description = self._clean_text(meta_description.get("content"))

        source_slug = Path(urlparse(index.url).path.rstrip("/")).name or slugify(index.external_id)

        return ParsedProject(
            source_url=index.url,
            source_slug=source_slug,
            external_id=index.external_id,
            title=title,
            area=area,
            floors=floors,
            floor_label=floor_label,
            bedrooms=index.bedrooms,
            width=width,
            length=length,
            size_text=size_text,
            price_options=price_options,
            addons=addons,
            package_title=package_title,
            package_description=package_description,
            package_items=package_items,
            description=description,
            content_sections=content_sections,
            seo_title=page_title,
            seo_description=seo_description,
            media=media,
        )

    @staticmethod
    def _floors_from_label(label: str) -> Decimal | None:
        normalized = (label or "").casefold()
        if "полутора" in normalized or "1,5" in normalized or "1.5" in normalized:
            return Decimal("1.5")
        if "двух" in normalized or normalized.startswith("2"):
            return Decimal("2")
        if "одно" in normalized or normalized.startswith("1"):
            return Decimal("1")
        return None

    def _extract_content(self, main) -> tuple[str, list[tuple[str, str]]]:
        headings = [
            tag
            for tag in main.find_all(["h2", "h3"])
            if self._clean_text(tag.get_text(" ", strip=True))
        ]
        description_heading = next(
            (
                h
                for h in headings
                if self._clean_text(h.get_text(" ", strip=True)).casefold() == "описание проекта"
            ),
            None,
        )
        if not description_heading:
            return "", []

        start_index = headings.index(description_heading)
        relevant = []
        for heading in headings[start_index:]:
            title = self._clean_text(heading.get_text(" ", strip=True))
            if title.casefold() == "похожие проекты":
                break
            relevant.append(heading)

        sections: list[tuple[str, str]] = []
        description = ""
        for position, heading in enumerate(relevant):
            next_heading = relevant[position + 1] if position + 1 < len(relevant) else None
            body = self._text_until_heading(heading, next_heading)
            heading_title = self._clean_text(heading.get_text(" ", strip=True))
            if heading_title.casefold() == "описание проекта":
                description = body
            elif body:
                sections.append((heading_title, body))

        return description, sections

    def _extract_package(self, main) -> tuple[str, str, list[tuple[str, str]]]:
        """Extract only structured package table rows.

        The legacy page contains promotional and cross-page text around this block,
        so free-form paragraphs/lists are deliberately ignored.
        """
        headings = [tag for tag in main.find_all(["h2", "h3"])]
        package_heading = next(
            (
                h
                for h in headings
                if "базовая комплектация" in self._clean_text(h.get_text(" ", strip=True)).casefold()
            ),
            None,
        )
        if not package_heading:
            return "", "", []

        stop_heading = next(
            (
                h
                for h in package_heading.find_all_next(["h2", "h3"])
                if self._clean_text(h.get_text(" ", strip=True)).casefold() == "описание проекта"
            ),
            None,
        )

        rows: list[tuple[str, str]] = []
        for element in package_heading.find_all_next():
            if stop_heading is not None and element is stop_heading:
                break
            if not isinstance(element, Tag) or element.name != "tr":
                continue
            cells = [self._clean_text(cell.get_text(" ", strip=True)) for cell in element.find_all(["th", "td"])]
            cells = [cell for cell in cells if cell]
            if len(cells) >= 2:
                row = (cells[0], " — ".join(cells[1:]))
                if row not in rows:
                    rows.append(row)

        package_title = 'Комплектация дома из бруса "ПОД УСАДКУ"'
        return package_title, "", rows

    def _text_until_heading(self, heading, stop_heading) -> str:
        parts: list[str] = []
        for element in heading.find_all_next():
            if stop_heading is not None and element is stop_heading:
                break
            if not isinstance(element, Tag):
                continue
            if element.name in {"p", "li"}:
                text = self._clean_text(element.get_text(" ", strip=True))
                if text and text not in parts:
                    parts.append(text)
        return "\n\n".join(parts)

    def _extract_gallery(self, soup) -> list[MediaItem]:
        gallery = soup.select_one(".woocommerce-product-gallery")
        if gallery is None:
            return []

        result: list[MediaItem] = []
        seen: set[str] = set()

        # Prefer original-size URLs in anchor hrefs / data-large_image.
        for image in gallery.find_all("img"):
            candidates = [
                image.get("data-large_image"),
                image.get("data-src"),
                image.get("src"),
            ]
            parent = image.find_parent("a")
            if parent is not None:
                candidates.insert(0, parent.get("href"))

            url = next((candidate for candidate in candidates if self._looks_like_image(candidate)), None)
            if not url:
                continue
            url = urljoin(self.base_url, url)
            if url in seen:
                continue
            seen.add(url)

            alt = self._clean_text(image.get("alt") or image.get("title") or "")
            filename = Path(urlparse(url).path).name.casefold()
            marker = f"{alt} {filename}".casefold()
            is_plan = any(token in marker for token in ("план", "plan", "планиров"))
            result.append(MediaItem(url=url, alt=alt, is_plan=is_plan))

        return result

    @staticmethod
    def _looks_like_image(value: str | None) -> bool:
        if not value:
            return False
        path = urlparse(value).path
        return Path(path).suffix.casefold() in IMAGE_EXTENSIONS

    @staticmethod
    def _floor_word(floors: Decimal | None, floor_label: str = "") -> str:
        label = (floor_label or "").casefold()
        if "полутора" in label or floors == Decimal("1.5"):
            return "Полутораэтажный"
        if "двух" in label or floors == Decimal("2"):
            return "Двухэтажный"
        if "одно" in label or floors == Decimal("1"):
            return "Одноэтажный"
        return "Дом"

    def _compact_short_description(self, data: ParsedProject) -> str:
        parts: list[str] = []
        floor_word = self._floor_word(data.floors, data.floor_label)
        parts.append(f"{floor_word} дом из бруса")
        if data.size_text:
            parts.append(f"размером {data.size_text} м")
        if data.area is not None:
            area = f"{data.area:g}".replace(".", ",")
            parts.append(f"площадью {area} м²")

        text = ", ".join(parts) + "."
        if data.bedrooms:
            word = "спальня" if data.bedrooms == 1 else ("спальни" if 2 <= data.bedrooms <= 4 else "спален")
            text += f" {data.bedrooms} {word}."
        return text[:220]

    @staticmethod
    def _short_description_looks_imported(project: Project) -> bool:
        short = (project.short_description or "").strip()
        full = (project.description or "").strip()
        return (
            not short
            or len(short) > 240
            or (bool(full) and short == full[:600])
        )

    def save_project(
        self,
        data: ParsedProject,
        *,
        skip_media: bool = False,
        prune_related: bool = False,
        replace_media: bool = False,
        clean_imported_text: bool = False,
    ) -> tuple[Project, bool]:
        category, _ = ProjectCategory.objects.get_or_create(
            slug="houses",
            defaults={
                "title": "Дома",
                "sort_order": 10,
                "is_active": True,
            },
        )

        existing = Project.objects.filter(external_id=data.external_id).first()
        created = existing is None
        project = existing or Project(external_id=data.external_id)

        project.title = data.title
        if created and not project.slug:
            project.slug = data.source_slug
        project.category = category
        project.construction_type = Project.ConstructionType.TIMBER
        project.area = data.area
        project.floors = data.floors
        if data.bedrooms is not None:
            project.bedrooms = data.bedrooms
        project.width = data.width
        project.length = data.length
        project.price_from = data.price_from  # legacy fallback only

        # Keep cards compact. Do not overwrite a concise description written manually
        # in Django Admin, but replace blank/legacy-imported long text.
        if created or self._short_description_looks_imported(project):
            project.short_description = self._compact_short_description(data)

        # Optional one-time cleanup for projects already polluted by the first importer.
        if clean_imported_text:
            project.description = ""
        if data.seo_title:
            project.seo_title = data.seo_title[:255]
        if data.seo_description:
            project.seo_description = data.seo_description
        project.is_active = True
        project.sort_order = self._sort_order(data.external_id)
        project.save()

        package = self._sync_package(project, data, prune=prune_related)
        self._sync_prices(project, data.price_options, package=package, prune=prune_related)
        self._sync_addons(project, data.addons, prune=prune_related)
        if clean_imported_text:
            project.content_sections.all().delete()

        if not skip_media:
            self._sync_media(project, data.media, replace=replace_media)

        return project, created

    def _sync_prices(self, project: Project, items: list[dict], *, package, prune: bool):
        seen_codes: set[str] = set()
        for item in items:
            material = get_or_create_material(item["group_title"], item["title"])
            seen_codes.add(material.code)
            ProjectOffer.objects.update_or_create(
                project=project,
                material=material,
                build_package=package,
                defaults={
                    "base_price": item["price"],
                    "sort_order": item["sort_order"],
                    "note": "Импортировано со старого сайта",
                },
            )
        if prune and seen_codes:
            project.offers.filter(build_package=package).exclude(material__code__in=seen_codes).delete()

    def _sync_addons(self, project: Project, items: list[dict], *, prune: bool):
        seen_foundations: set[str] = set()
        seen_roofs: set[str] = set()
        seen_extras: set[str] = set()
        for item in items:
            group = str(item.get("group_title") or "").casefold()
            if "фундамент" in group:
                option = get_or_create_foundation(item["title"])
                seen_foundations.add(option.code)
                ProjectFoundation.objects.update_or_create(
                    project=project,
                    foundation=option,
                    defaults={
                        "base_price_override": item["price"],
                        "description": "Импортировано со старого сайта",
                        "sort_order": item["sort_order"],
                    },
                )
            elif "кров" in group:
                option = get_or_create_roof_covering(item["title"])
                seen_roofs.add(option.code)
                ProjectRoofCovering.objects.update_or_create(
                    project=project,
                    covering=option,
                    defaults={
                        "base_price_override": item["price"],
                        "description": "Импортировано со старого сайта",
                        "sort_order": item["sort_order"],
                    },
                )
            else:
                option = get_or_create_extra_option(item["title"])
                seen_extras.add(option.code)
                ProjectExtraOption.objects.update_or_create(
                    project=project,
                    option=option,
                    defaults={
                        "base_price_override": item["price"],
                        "description": "Импортировано со старого сайта",
                        "sort_order": item["sort_order"],
                    },
                )

        if prune:
            if seen_foundations:
                project.foundations.exclude(foundation__code__in=seen_foundations).delete()
            if seen_roofs:
                project.roof_coverings.exclude(covering__code__in=seen_roofs).delete()
            if seen_extras:
                project.extra_options.exclude(option__code__in=seen_extras).delete()

    def _sync_content(self, project: Project, sections: Iterable[tuple[str, str]], *, prune: bool):
        seen_titles: set[str] = set()
        for sort_order, (title, body) in enumerate(sections, start=1):
            seen_titles.add(title)
            ProjectContentSection.objects.update_or_create(
                project=project,
                title=title,
                defaults={
                    "body": body,
                    "sort_order": sort_order,
                    "is_active": True,
                },
            )
        if prune and seen_titles:
            project.content_sections.exclude(title__in=seen_titles).delete()

    def _sync_package(self, project: Project, data: ParsedProject, *, prune: bool):
        title = data.package_title or 'Комплектация дома из бруса "ПОД УСАДКУ"'
        package = get_or_create_build_package(title)

        spec = []
        if data.package_items:
            spec = [
                {
                    "title": "Состав комплектации",
                    "sort_order": 0,
                    "items": [
                        {"title": item_title, "value": value, "sort_order": index}
                        for index, (item_title, value) in enumerate(data.package_items, start=1)
                    ],
                }
            ]

        # Первый импорт формирует глобальный шаблон. Если конкретный проект
        # отличается, сохраняем только его override, не дублируя весь шаблон 119 раз.
        existing_sections = list(package.sections.prefetch_related("items").all())
        if spec and not existing_sections:
            for section_data in spec:
                section = BuildPackageSection.objects.create(
                    package=package,
                    title=section_data["title"],
                    sort_order=section_data["sort_order"],
                )
                for item in section_data["items"]:
                    BuildPackageItem.objects.create(section=section, **item)
        elif spec:
            current = [
                {
                    "title": section.title,
                    "sort_order": section.sort_order,
                    "items": [
                        {"title": item.title, "value": item.value, "sort_order": item.sort_order}
                        for item in section.items.all()
                    ],
                }
                for section in existing_sections
            ]
            if current != spec:
                ProjectPackageOverride.objects.update_or_create(
                    project=project,
                    package=package,
                    defaults={
                        "description": data.package_description,
                        "sections": spec,
                    },
                )
            else:
                ProjectPackageOverride.objects.filter(project=project, package=package).delete()

        if data.package_description and not package.description:
            package.description = data.package_description
            package.save(update_fields=["description"])

        return package

    def _sync_media(self, project: Project, media: list[MediaItem], *, replace: bool):
        if not media:
            return

        if replace:
            project.images.all().delete()
            project.plans.all().delete()

        existing_names = {
            Path(item.image.name).name.casefold()
            for item in project.images.all()
            if item.image and item.image.name
        }
        existing_names.update(
            Path(item.image.name).name.casefold()
            for item in project.plans.all()
            if item.image and item.image.name
        )

        gallery_order = project.images.filter(is_primary=False).count()
        plan_order = project.plans.count()
        main_saved = project.images.filter(is_primary=True).exists()

        for item in media:
            filename = Path(urlparse(item.url).path).name or "image.jpg"
            if filename.casefold() in existing_names:
                continue
            content = ContentFile(self._request_bytes(item.url))

            if item.is_plan:
                plan_order += 1
                plan = ProjectPlan(
                    project=project,
                    title=f"Планировка {plan_order}",
                    floor=plan_order,
                    alt_text=item.alt,
                    sort_order=plan_order,
                )
                plan.image.save(filename, content, save=True)
            else:
                image = ProjectImage(
                    project=project,
                    image_type=ProjectImage.ImageType.FACADE if not main_saved else ProjectImage.ImageType.GALLERY,
                    is_primary=not main_saved,
                    alt_text=item.alt,
                    sort_order=0 if not main_saved else gallery_order + 1,
                )
                image.image.save(filename, content, save=True)
                if not main_saved:
                    main_saved = True
                else:
                    gallery_order += 1

            existing_names.add(filename.casefold())
            if self.pause:
                time.sleep(self.pause)


@transaction.atomic
def save_parsed_project(importer: OldSiteHouseImporter, data: ParsedProject, **kwargs):
    return importer.save_project(data, **kwargs)
