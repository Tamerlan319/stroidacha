from decimal import Decimal

from django.test import SimpleTestCase, TestCase

from .models import PortfolioProject
from .old_site_portfolio_importer import (
    BeautifulSoup,
    OldSitePortfolioImporter,
    ParsedPortfolioProject,
)
from .old_site_reviews_importer import OldSiteReviewsImporter


class StubReviewsImporter(OldSiteReviewsImporter):
    def _request_bytes(self, url: str) -> bytes:
        return """
        <div class=\"_cont\">
          <blockquote>Построили хороший дом точно в срок.</blockquote>
          <hr>
          <p>Иван Петрович, Московская область, Чехов, 13.08.2020</p>
          <blockquote>Баня получилась тёплой и аккуратной.</blockquote>
          <hr>
          <p>Анна Сергеевна, Тверская область, 21.10.2022</p>
        </div>
        """.encode()


class OldSiteReviewsImporterTests(SimpleTestCase):
    def test_reviews_keep_author_location_date_and_object_type(self):
        reviews = StubReviewsImporter().parse()

        self.assertEqual(len(reviews), 2)
        self.assertEqual(reviews[0].author_name, "Иван Петрович")
        self.assertEqual(
            reviews[0].city,
            "Московская область, Чехов · 13.08.2020",
        )
        self.assertEqual(reviews[0].project_name, "Дом из бруса")
        self.assertEqual(reviews[1].project_name, "Баня из бруса")


class OldSitePortfolioImporterTests(SimpleTestCase):
    def setUp(self):
        self.importer = OldSitePortfolioImporter(pause=0)

    def test_gallery_uses_original_images_and_removes_duplicates(self):
        soup = BeautifulSoup(
            """
            <div class="_cont">
              <div class="gallery">
                <a href="/media/house-01.jpg"><img src="/media/house-01-small.jpg"></a>
                <a href="/media/house-01.jpg"><img src="/media/house-01-small.jpg"></a>
                <a href="/attachment/photo-two/"><img src="/media/house-02.jpg"></a>
              </div>
            </div>
            """,
            "html.parser",
        )

        media = self.importer._extract_gallery(
            soup.select_one("._cont"),
            "https://stroydacha.online/object/",
            "Дом",
        )

        self.assertEqual(len(media), 2)
        self.assertEqual(media[0].url, "https://stroydacha.online/media/house-01.jpg")
        self.assertEqual(media[1].url, "https://stroydacha.online/media/house-02.jpg")

    def test_material_typo_is_normalized(self):
        self.assertEqual(
            self.importer._normalize_material("Брус проффилированный 140х140"),
            "Брус профилированный 140х140",
        )

    def test_location_is_removed_from_long_card_title(self):
        self.assertEqual(
            self.importer._display_title(
                "Дом из бруса 121 м2 — Московская область. Истринский район"
            ),
            "Дом из бруса 121 м²",
        )


class OldSitePortfolioDeduplicationTests(TestCase):
    def test_same_area_and_price_are_merged_into_oldest_record(self):
        original = PortfolioProject.objects.create(
            title="Дом из бруса 121 м²",
            slug="dom-121",
            area="121 м²",
            size_text="9×9 м",
            price=Decimal("2000000"),
        )
        PortfolioProject.objects.create(
            title="Длинный импортированный заголовок",
            slug="dom-iz-brusa-121-m2-moskovskaya-oblast-istrinskij-rajon-d-alyohnovo",
            area="121 м²",
            size_text="9×9 м",
            price=Decimal("2000000"),
        )
        data = ParsedPortfolioProject(
            source_url="https://stroydacha.online/object/",
            slug="dom-iz-brusa-121-m2-moskovskaya-oblast-istrinskij-rajon-d-alyohnovo",
            title="Дом из бруса 121 м²",
            area="121 м²",
            size_text="9×9 м",
            price=Decimal("2000000"),
        )

        project, created = OldSitePortfolioImporter(pause=0).save(
            data,
            skip_media=True,
        )

        self.assertFalse(created)
        self.assertEqual(project.pk, original.pk)
        self.assertEqual(PortfolioProject.objects.count(), 1)
