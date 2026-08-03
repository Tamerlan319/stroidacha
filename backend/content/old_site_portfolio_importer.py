from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q

from .models import PortfolioImage, PortfolioProject

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    BeautifulSoup = None
    _BS4_IMPORT_ERROR = exc
else:
    _BS4_IMPORT_ERROR = None


DEFAULT_PORTFOLIO_URLS = (
    "https://stroydacha.online/dom-iz-brusa-121-m2-moskovskaya-oblast-istrinskij-rajon-d-alyohnovo/",
    "https://stroydacha.online/banya-45m2-individualnyj-proekt-moskovskaya-oblast-istrinskij-rajon-derevnya-sinyovo/",
    "https://stroydacha.online/banya-5h6-monino/",
    "https://stroydacha.online/dom-iz-profilirovannogo-brusa-11h11-mozhajskij-rajon/",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "StroidachaPortfolioMigration/1.0"
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

KNOWN_PORTFOLIO_FACTS = {
    "dom-iz-brusa-121-m2-moskovskaya-oblast-istrinskij-rajon-d-alyohnovo": {
        "size_text": "9×9 м",
        "match_term": "Алёхнов",
    },
    "banya-45m2-individualnyj-proekt-moskovskaya-oblast-istrinskij-rajon-derevnya-sinyovo": {
        "match_term": "Синёво",
    },
    "banya-5h6-monino": {"match_term": "Монино"},
    "dom-iz-profilirovannogo-brusa-11h11-mozhajskij-rajon": {
        "match_term": "Можайск",
    },
}


class OldSitePortfolioImportError(RuntimeError):
    pass


@dataclass
class PortfolioMedia:
    url: str
    alt_text: str = ""


@dataclass
class ParsedPortfolioProject:
    source_url: str
    slug: str
    title: str
    location: str = ""
    area: str = ""
    size_text: str = ""
    material: str = ""
    price: Decimal | None = None
    short_description: str = ""
    description: str = ""
    media: list[PortfolioMedia] = field(default_factory=list)


class OldSitePortfolioImporter:
    def __init__(self, *, timeout: int = 30, pause: float = 0.15, stdout=None):
        if BeautifulSoup is None:
            raise OldSitePortfolioImportError(
                "Для импорта нужен пакет beautifulsoup4. "
                "Установи его: pip install beautifulsoup4"
            ) from _BS4_IMPORT_ERROR
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
            raise OldSitePortfolioImportError(
                f"Не удалось загрузить {url}: {exc}"
            ) from exc

    def _fetch_soup(self, url: str):
        soup = BeautifulSoup(self._request_bytes(url), "html.parser")
        if self.pause:
            time.sleep(self.pause)
        return soup

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _looks_like_image(value: str | None) -> bool:
        if not value:
            return False
        return Path(urlparse(value).path).suffix.casefold() in IMAGE_EXTENSIONS

    @staticmethod
    def _money(value: str | None) -> Decimal | None:
        digits = re.sub(r"\D", "", value or "")
        return Decimal(digits) if digits else None

    @staticmethod
    def _normalize_material(value: str) -> str:
        value = re.sub(r"^Использовался\s+", "", value, flags=re.IGNORECASE)
        value = re.sub(r"проффилированн", "профилированн", value, flags=re.IGNORECASE)
        value = re.sub(r"(\d)мм\b", r"\1 мм", value, flags=re.IGNORECASE)
        return value.strip(" .")

    @staticmethod
    def _display_title(value: str) -> str:
        # Локация уже показывается отдельным полем, поэтому не дублируем её
        # длинным хвостом в заголовке карточки.
        title = value.split("—", 1)[0].strip()
        title = re.sub(r"(\d)\s*м2\b", r"\1 м²", title, flags=re.IGNORECASE)
        title = re.sub(r"\s*[хx×]\s*", "×", title)
        return title

    def parse(self, url: str) -> ParsedPortfolioProject:
        soup = self._fetch_soup(url)
        h1 = soup.find("h1")
        if h1 is None:
            raise OldSitePortfolioImportError(f"Не найден H1 объекта: {url}")

        root = h1.find_parent("div", class_="_cont") or h1.parent
        source_title = self._clean_text(h1.get_text(" ", strip=True))
        title = self._display_title(source_title)
        raw_lines = [
            self._clean_text(line)
            for line in root.get_text("\n", strip=True).splitlines()
        ]
        lines = [line for line in raw_lines if line and line != source_title]
        facts_text = "\n".join(lines)

        area_match = re.search(
            r"Площадь\s*:?[ \t]*(\d+(?:[.,]\d+)?)\s*м(?:2|²)",
            facts_text,
            re.IGNORECASE,
        )
        area = f"{area_match.group(1).replace('.', ',')} м²" if area_match else ""

        size_match = re.search(
            r"(?:Габариты|Размер(?:\s+дома)?)\s*:?[ \t]*(\d+(?:[.,]\d+)?\s*[хx×]\s*\d+(?:[.,]\d+)?)",
            facts_text,
            re.IGNORECASE,
        )
        size_text = ""
        if size_match:
            size_text = re.sub(r"\s*[x×х]\s*", "×", size_match.group(1), flags=re.IGNORECASE)
            size_text = size_text.replace(".", ",") + " м"

        location_match = re.search(
            r"Место\s+(?:строительства|постройки)\s*:\s*([^\n]+)",
            facts_text,
            re.IGNORECASE,
        )
        location = self._clean_text(location_match.group(1)).strip(" .") if location_match else ""
        if not location and "—" in source_title:
            location = self._clean_text(source_title.split("—", 1)[1]).strip(" .")
        if not location:
            location_line = next(
                (
                    line
                    for line in lines
                    if "московск" in line.casefold() and not line.casefold().startswith("стоимость")
                ),
                "",
            )
            location = re.sub(
                r"^(?:Дом|Баня)\s+из\s+бруса\.\s*",
                "",
                location_line,
                flags=re.IGNORECASE,
            ).strip(" .")

        material_line = next(
            (
                line
                for line in lines
                if re.search(r"\bбрус\b", line, re.IGNORECASE)
                and re.search(r"\d{2,3}\s*[хx×]\s*\d{2,3}", line)
            ),
            "",
        )
        material = self._normalize_material(material_line)

        price_match = re.search(
            r"(?:Стоимость(?:\s+строительства)?|Цена)\s*:?\s*([\d\s]+)",
            facts_text,
            re.IGNORECASE,
        )
        price = self._money(price_match.group(1)) if price_match else None

        media = self._extract_gallery(root, url, title)
        slug = Path(urlparse(url).path.rstrip("/")).name
        known_facts = KNOWN_PORTFOLIO_FACTS.get(slug, {})
        size_text = size_text or known_facts.get("size_text", "")

        kind = "Баня" if title.casefold().startswith("баня") else "Дом"
        short_parts = [f"{kind}, реализованный компанией «Брусодел»"]
        if location:
            short_parts.append(location)
        if size_text:
            short_parts.append(f"размер {size_text}")
        short_description = ". ".join(short_parts).rstrip(".") + "."

        return ParsedPortfolioProject(
            source_url=url,
            slug=slug,
            title=title,
            location=location,
            area=area,
            size_text=size_text,
            material=material,
            price=price,
            short_description=short_description,
            description="\n".join(lines),
            media=media,
        )

    def _extract_gallery(self, root, page_url: str, title: str) -> list[PortfolioMedia]:
        gallery = root.select_one(".gallery")
        if gallery is None:
            return []

        result: list[PortfolioMedia] = []
        seen: set[str] = set()
        for image in gallery.find_all("img"):
            parent = image.find_parent("a")
            candidates = [
                parent.get("href") if parent is not None else None,
                image.get("data-large_image"),
                image.get("data-src"),
                image.get("src"),
            ]
            source = next(
                (candidate for candidate in candidates if self._looks_like_image(candidate)),
                None,
            )
            if source is None:
                continue
            image_url = urljoin(page_url, source)
            if image_url in seen:
                continue
            seen.add(image_url)
            alt = self._clean_text(image.get("alt") or image.get("title") or "")
            result.append(
                PortfolioMedia(
                    url=image_url,
                    alt_text=alt or f"{title} — фото {len(result) + 1}",
                )
            )
        return result

    @transaction.atomic
    def save(
        self,
        data: ParsedPortfolioProject,
        *,
        overwrite_text: bool = False,
        skip_media: bool = False,
        replace_media: bool = False,
        sort_order: int = 0,
    ) -> tuple[PortfolioProject, bool]:
        candidates_query = Q(slug=data.slug)
        match_term = KNOWN_PORTFOLIO_FACTS.get(data.slug, {}).get("match_term")
        if match_term:
            candidates_query |= Q(title__icontains=match_term) | Q(
                location__icontains=match_term
            )
        # Старый объект Алёхново был заведён без названия деревни. Площадь и
        # фактическая стоимость дают устойчивый отпечаток для его объединения.
        if data.area and data.price is not None:
            candidates_query |= Q(area=data.area, price=data.price)

        candidates = list(
            PortfolioProject.objects.filter(candidates_query).order_by(
                "created_at", "id"
            )
        )
        project = candidates[0] if candidates else None
        created = project is None
        project = project or PortfolioProject(slug=data.slug)

        project.title = data.title
        project.location = data.location
        project.area = data.area
        project.size_text = data.size_text
        project.material = data.material
        project.price = data.price
        if created or overwrite_text or not project.short_description:
            project.short_description = data.short_description
        if created or overwrite_text or not project.description:
            project.description = data.description
        project.is_active = True
        project.sort_order = sort_order
        project.save()

        if len(candidates) > 1:
            self._merge_duplicates(project, candidates[1:])

        if not skip_media:
            self._sync_media(project, data.media, replace=replace_media)
        return project, created

    def _merge_duplicates(
        self,
        canonical: PortfolioProject,
        duplicates: list[PortfolioProject],
    ):
        next_order = canonical.images.count()
        existing_names = {
            Path(item.image.name).name.casefold()
            for item in canonical.images.all()
            if item.image and item.image.name
        }

        for duplicate in duplicates:
            duplicate_pk = duplicate.pk
            if not canonical.main_image and duplicate.main_image:
                canonical.main_image = duplicate.main_image.name
                canonical.save(update_fields=["main_image"])
            elif duplicate.main_image:
                duplicate.main_image.delete(save=False)

            for image in duplicate.images.all().order_by("sort_order", "id"):
                filename = Path(image.image.name).name.casefold() if image.image else ""
                if filename and filename in existing_names:
                    image.image.delete(save=False)
                    image.delete()
                    continue
                next_order += 1
                image.portfolio_project = canonical
                image.sort_order = next_order
                image.save(update_fields=["portfolio_project", "sort_order"])
                if filename:
                    existing_names.add(filename)

            duplicate.delete()
            self._log(
                f"  объединён дубликат портфолио #{duplicate_pk} с записью #{canonical.pk}"
            )

    def _sync_media(
        self,
        project: PortfolioProject,
        media: list[PortfolioMedia],
        *,
        replace: bool,
    ):
        if not media:
            return

        if replace:
            if project.main_image:
                project.main_image.delete(save=False)
                project.main_image = ""
            for item in project.images.all():
                item.image.delete(save=False)
            project.images.all().delete()

        existing_names = {
            Path(item.image.name).name.casefold()
            for item in project.images.all()
            if item.image and item.image.name
        }
        if project.main_image and project.main_image.name:
            existing_names.add(Path(project.main_image.name).name.casefold())

        start = 0
        if not project.main_image:
            first = media[0]
            filename = Path(urlparse(first.url).path).name or f"{project.slug}-main.jpg"
            project.main_image.save(
                filename,
                ContentFile(self._request_bytes(first.url)),
                save=True,
            )
            existing_names.add(filename.casefold())
            start = 1

        next_order = project.images.count()
        for media_item in media[start:]:
            filename = Path(urlparse(media_item.url).path).name or f"{project.slug}-{next_order + 1}.jpg"
            if filename.casefold() in existing_names:
                continue
            next_order += 1
            gallery_image = PortfolioImage(
                portfolio_project=project,
                alt_text=media_item.alt_text[:255],
                caption="",
                sort_order=next_order,
            )
            gallery_image.image.save(
                filename,
                ContentFile(self._request_bytes(media_item.url)),
                save=True,
            )
            existing_names.add(filename.casefold())
            if self.pause:
                time.sleep(self.pause)
