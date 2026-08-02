from django.test import SimpleTestCase

from .models import LandingPage
from .old_site_page_importer import OldInfoPageSource, OldSitePageImporter


class StubPageImporter(OldSitePageImporter):
    def _request_bytes(self, url: str) -> bytes:
        return b"""
        <html><head><title>Article title</title>
        <meta name="description" content="Article description"></head><body>
        <div class="_cont">
          <h1>Guide heading</h1>
          <p>Useful introduction.</p>
          <h2>Important section</h2>
          <ul>
            <li><strong>First:</strong> useful detail.</li>
            <li>Second detail.</li>
          </ul>
          <img src="/media/article.jpg" alt="Article image">
          <img src="/media/article.jpg" alt="Duplicate">
        </div></body></html>
        """


class OldSitePageImporterTests(SimpleTestCase):
    def test_text_and_unique_images_are_parsed(self):
        source = OldInfoPageSource(
            source_url="https://stroydacha.online/article/",
            slug="article",
            page_type=LandingPage.PageType.GUIDE,
            menu_title="Article",
            sort_order=10,
        )

        data = StubPageImporter(pause=0).parse(source)

        self.assertEqual(data.h1, "Guide heading")
        self.assertEqual(data.intro_text, "Useful introduction.")
        self.assertIn("## Important section", data.main_text)
        self.assertIn("- First: useful detail.\n- Second detail.", data.main_text)
        self.assertEqual(len(data.images), 1)
        self.assertEqual(
            data.images[0][0],
            "https://stroydacha.online/media/article.jpg",
        )
