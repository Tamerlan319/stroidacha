from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.db import transaction

from .models import LandingPage, LandingPageImage

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    BeautifulSoup = None
    _BS4_IMPORT_ERROR = exc
else:
    _BS4_IMPORT_ERROR = None


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "StroidachaInfoMigration/1.0"
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@dataclass(frozen=True)
class OldInfoPageSource:
    source_url: str
    slug: str
    page_type: str
    menu_title: str
    sort_order: int


DEFAULT_INFO_PAGES = (
    OldInfoPageSource(
        "https://stroydacha.online/o-direktore/",
        "o-direktore",
        LandingPage.PageType.COMPANY,
        "О директоре",
        110,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/vypiska-iz-egryul/",
        "vypiska-iz-egryul",
        LandingPage.PageType.COMPANY,
        "Выписка из ЕГРЮЛ",
        120,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/nashe-proizvodstvo-brusa/",
        "proizvodstvo",
        LandingPage.PageType.COMPANY,
        "Производство",
        130,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/dostavka/",
        "dostavka",
        LandingPage.PageType.COMPANY,
        "Доставка",
        135,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/materinskij-kapital-dlya-stroitelstva-derevyannogo-doma/",
        "materinskij-kapital",
        LandingPage.PageType.COMPANY,
        "Маткапитал",
        140,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/ipoteka-na-doma-iz-brusa/",
        "ipoteka",
        LandingPage.PageType.COMPANY,
        "Ипотека",
        150,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/plyusy-i-minusy-doma-iz-brusa/",
        "plyusy-i-minusy-doma-iz-brusa",
        LandingPage.PageType.GUIDE,
        "Плюсы и минусы дома из бруса",
        210,
    ),
    OldInfoPageSource(
        "https://stroydacha.online/sravnivaem-profilirovannyj-i-obychnyj/",
        "profilirovannyj-ili-obychnyj-brus",
        LandingPage.PageType.GUIDE,
        "Профилированный или обычный брус",
        220,
    ),
)


class OldSitePageImportError(RuntimeError):
    pass


@dataclass
class ParsedInfoPage:
    source: OldInfoPageSource
    h1: str
    intro_text: str
    main_text: str
    seo_title: str
    seo_description: str
    images: list[tuple[str, str]]


class OldSitePageImporter:
    def __init__(self, *, timeout: int = 30, pause: float = 0.15):
        if BeautifulSoup is None:
            raise OldSitePageImportError(
                "Для импорта нужен пакет beautifulsoup4. "
                "Установи его: pip install beautifulsoup4"
            ) from _BS4_IMPORT_ERROR
        self.timeout = timeout
        self.pause = max(pause, 0)

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
            raise OldSitePageImportError(
                f"Не удалось загрузить {url}: {exc}"
            ) from exc

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _looks_like_image(value: str | None) -> bool:
        if not value:
            return False
        return Path(urlparse(value).path).suffix.casefold() in IMAGE_EXTENSIONS

    def parse(self, source: OldInfoPageSource) -> ParsedInfoPage:
        soup = BeautifulSoup(self._request_bytes(source.source_url), "html.parser")
        if self.pause:
            time.sleep(self.pause)

        h1_tag = soup.find("h1")
        if h1_tag is None:
            raise OldSitePageImportError(f"Не найден H1: {source.source_url}")
        h1 = self._clean(h1_tag.get_text(" ", strip=True))
        root = h1_tag.find_parent("div", class_="_cont") or h1_tag.parent

        stop_titles = {
            "построенные дома",
            "порядок работ",
            "действующие акции",
            "похожие проекты",
        }
        parts: list[str] = []
        seen_text: set[str] = set()
        for element in h1_tag.find_all_next(["h2", "h3", "p", "li"]):
            if element is not root and root not in element.parents:
                break
            if element.name == "p" and element.find_parent("li") is not None:
                continue
            if element.name == "li" and element.find("li") is not None:
                # Контейнер вложенного списка иначе дублирует все дочерние пункты
                # одной длинной строкой перед нормальным списком.
                continue
            text = self._clean(element.get_text(" ", strip=True))
            if not text or text == h1:
                continue
            if element.name in {"h2", "h3"} and text.casefold() in stop_titles:
                break
            normalized = text.casefold()
            if normalized in seen_text:
                continue
            seen_text.add(normalized)

            if element.name in {"h2", "h3"}:
                parts.append(f"{'##' if element.name == 'h2' else '###'} {text}")
            elif element.name == "li":
                line = f"- {text}"
                if parts and parts[-1].startswith("- "):
                    parts[-1] = f"{parts[-1]}\n{line}"
                else:
                    parts.append(line)
            else:
                parts.append(text)

        if not parts:
            raw_lines = [
                self._clean(line)
                for line in root.get_text("\n", strip=True).splitlines()
            ]
            parts = [line for line in raw_lines if line and line != h1]

        images = self._extract_images(root, source.source_url)
        intro_text = next(
            (
                part
                for part in parts
                if not part.startswith(("## ", "### ", "- "))
            ),
            "",
        )
        if not intro_text and images:
            intro_text = "Официальные документы и материалы компании."
        main_text = "\n\n".join(parts)

        seo_title = self._clean(soup.title.get_text(" ", strip=True)) if soup.title else h1
        meta = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        seo_description = self._clean(meta.get("content", "")) if meta else intro_text

        return ParsedInfoPage(
            source=source,
            h1=h1,
            intro_text=intro_text,
            main_text=main_text,
            seo_title=seo_title,
            seo_description=seo_description,
            images=images,
        )

    def _extract_images(self, root, page_url: str) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        seen: set[str] = set()
        for image in root.find_all("img"):
            candidates = [
                image.get("data-large_image"),
                image.get("data-src"),
                image.get("src"),
            ]
            source = next(
                (item for item in candidates if self._looks_like_image(item)),
                None,
            )
            if source is None:
                continue
            image_url = urljoin(page_url, source)
            if image_url in seen:
                continue
            seen.add(image_url)
            result.append((image_url, self._clean(image.get("alt") or "")))
        return result

    @transaction.atomic
    def save(
        self,
        data: ParsedInfoPage,
        *,
        overwrite: bool = False,
        skip_media: bool = False,
        replace_media: bool = False,
    ):
        page, created = LandingPage.objects.get_or_create(
            slug=data.source.slug,
            defaults={"title": data.source.menu_title, "h1": data.h1},
        )
        page.title = data.source.menu_title
        page.page_type = data.source.page_type
        page.h1 = data.h1
        if created or overwrite or not page.intro_text:
            page.intro_text = data.intro_text
        if created or overwrite or not page.main_text:
            page.main_text = data.main_text
        if created or overwrite or not page.seo_title:
            page.seo_title = data.seo_title[:255]
        if created or overwrite or not page.seo_description:
            page.seo_description = data.seo_description
        page.is_active = True
        page.sort_order = data.source.sort_order
        page.save()
        if not skip_media:
            self._sync_images(page, data.images, replace=replace_media)
        return page, created

    def _sync_images(
        self,
        page: LandingPage,
        images: list[tuple[str, str]],
        *,
        replace: bool,
    ):
        if replace:
            for item in page.images.all():
                item.image.delete(save=False)
            page.images.all().delete()

        existing_names = {
            Path(item.image.name).name.casefold()
            for item in page.images.all()
            if item.image and item.image.name
        }
        next_order = page.images.count()
        for image_url, alt_text in images:
            filename = Path(urlparse(image_url).path).name
            if not filename or filename.casefold() in existing_names:
                continue
            next_order += 1
            item = LandingPageImage(
                landing_page=page,
                alt_text=alt_text[:255],
                sort_order=next_order,
            )
            item.image.save(
                filename,
                ContentFile(self._request_bytes(image_url)),
                save=True,
            )
            existing_names.add(filename.casefold())
            if self.pause:
                time.sleep(self.pause)
