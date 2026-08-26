from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db import transaction

from .models import Review

try:
    from bs4 import BeautifulSoup
except ImportError as exc:  # pragma: no cover
    BeautifulSoup = None
    _BS4_IMPORT_ERROR = exc
else:
    _BS4_IMPORT_ERROR = None


REVIEWS_URL = "https://stroydacha.online/otzyvy/"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
    "StroidachaReviewsMigration/1.0"
)


class OldSiteReviewsImportError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParsedReview:
    author_name: str
    city: str
    text: str
    project_name: str


class OldSiteReviewsImporter:
    def __init__(self, *, timeout: int = 30):
        if BeautifulSoup is None:
            raise OldSiteReviewsImportError(
                "Для импорта нужен пакет beautifulsoup4. "
                "Установи его: pip install beautifulsoup4"
            ) from _BS4_IMPORT_ERROR
        self.timeout = timeout

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

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
            raise OldSiteReviewsImportError(
                f"Не удалось загрузить {url}: {exc}"
            ) from exc

    def parse(self, url: str = REVIEWS_URL) -> list[ParsedReview]:
        soup = BeautifulSoup(self._request_bytes(url), "html.parser")

        parsed: list[ParsedReview] = []
        for quote in soup.select("blockquote"):
            text = self._clean(quote.get_text(" ", strip=True))
            author_tag = quote.find_next_sibling("p")
            author_line = self._clean(
                author_tag.get_text(" ", strip=True) if author_tag else ""
            )
            if not text or not author_line:
                continue

            pieces = [piece.strip() for piece in author_line.split(",") if piece.strip()]
            author_name = pieces[0]
            date = pieces[-1] if pieces and re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", pieces[-1]) else ""
            location_end = -1 if date else None
            location = ", ".join(pieces[1:location_end])
            city = " · ".join(part for part in (location, date) if part)
            lower_text = text.casefold()
            project_name = "Баня из бруса" if "бан" in lower_text else "Дом из бруса"

            parsed.append(
                ParsedReview(
                    author_name=author_name,
                    city=city,
                    text=text,
                    project_name=project_name,
                )
            )

        if not parsed:
            raise OldSiteReviewsImportError("На странице не найдено ни одного отзыва")
        return parsed

    @transaction.atomic
    def save(self, reviews: list[ParsedReview], *, overwrite: bool = False) -> tuple[int, int]:
        created_count = 0
        updated_count = 0
        for index, item in enumerate(reviews, start=1):
            review = Review.objects.filter(
                author_name=item.author_name,
                text=item.text,
            ).first()
            if review is None:
                Review.objects.create(
                    author_name=item.author_name,
                    city=item.city,
                    text=item.text,
                    project_name=item.project_name,
                    # Старый сайт не хранил числовую оценку по отзыву — это
                    # текстовые истории клиентов, которые компания сама
                    # отобрала и опубликовала (то есть заведомо
                    # положительные). 5 — тот же дефолт, что и у модели
                    # Review.rating для новых отзывов, добавляемых вручную;
                    # 0 здесь был плейсхолдером, который ломал агрегированный
                    # рейтинг сайта (AggregateRating из 0 звёзд читается как
                    # "плохо", а не "оценка не указана").
                    rating=5,
                    is_active=True,
                    sort_order=index * 10,
                )
                created_count += 1
                continue

            if overwrite:
                review.city = item.city
                review.project_name = item.project_name
                review.sort_order = index * 10
                review.is_active = True
                review.save(
                    update_fields=("city", "project_name", "sort_order", "is_active")
                )
            updated_count += 1

        return created_count, updated_count
