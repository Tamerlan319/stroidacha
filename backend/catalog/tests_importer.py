from django.test import SimpleTestCase

from .importers import _stable_code
from .old_site_importer import BeautifulSoup, OldSiteHouseImporter


class OldSiteImporterTests(SimpleTestCase):
    def setUp(self):
        self.importer = OldSiteHouseImporter(pause=0)

    def test_content_sections_stop_before_related_projects(self):
        soup = BeautifulSoup(
            """
            <main>
              <h2>Описание проекта</h2>
              <p>Первый абзац.</p><p>Второй абзац.</p>
              <h2>Виды бруса</h2><p>Текст о материалах.</p>
              <h2>Похожие проекты</h2><p>Этот текст импортировать нельзя.</p>
            </main>
            """,
            "html.parser",
        )

        description, sections = self.importer._extract_content(soup.main)

        self.assertEqual(description, "Первый абзац.\n\nВторой абзац.")
        self.assertEqual(
            sections,
            [
                ("Описание проекта", "Первый абзац.\n\nВторой абзац."),
                ("Виды бруса", "Текст о материалах."),
            ],
        )

    def test_reinforced_pile_titles_share_one_code(self):
        self.assertEqual(_stable_code("foundation", "ЖБ сваи (ГОСТ)"), "reinforced-piles")
        self.assertEqual(_stable_code("foundation", "ЖБ СВАИ ГОСТ"), "reinforced-piles")

    def test_option_image_is_found_in_same_card(self):
        soup = BeautifulSoup(
            """
            <main><article><h3>ЖБ сваи (ГОСТ)</h3>
            <img src="/media/piles.jpg" alt="ЖБ сваи"></article></main>
            """,
            "html.parser",
        )

        self.assertEqual(
            self.importer._find_image_near_text(soup.main, "ЖБ сваи (ГОСТ)"),
            "https://stroydacha.online/media/piles.jpg",
        )

    def test_promotions_are_parsed_outside_project_main(self):
        soup = BeautifulSoup(
            """
            <body>
              <main><h1>Проект дома</h1></main>
              <section><h2>Действующие акции</h2>
                <article><p>Бесплатная доставка до 500 км</p>
                <img src="/media/delivery.jpg" alt="Доставка"></article>
              </section>
            </body>
            """,
            "html.parser",
        )

        promotions = self.importer._extract_promotions(
            soup,
            soup.get_text("\n", strip=True),
        )

        self.assertEqual(len(promotions), 1)
        self.assertEqual(promotions[0].code, "free-delivery")
        self.assertEqual(
            promotions[0].image_url,
            "https://stroydacha.online/media/delivery.jpg",
        )
