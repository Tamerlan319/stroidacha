from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Project, ProjectCategory

from .models import LandingPage


class GenerateSeoLandingPagesTests(TestCase):
    def setUp(self):
        self.houses = ProjectCategory.objects.create(title="Дома", slug="houses")
        self.baths = ProjectCategory.objects.create(title="Бани", slug="baths")

        # Два активных проекта 6х6 — должны сгруппироваться в одну страницу.
        Project.objects.create(
            title="Дом шесть на шесть, первый",
            category=self.houses,
            width=Decimal("6"),
            length=Decimal("6"),
            is_active=True,
        )
        Project.objects.create(
            title="Дом шесть на шесть, второй",
            category=self.houses,
            width=Decimal("6"),
            length=Decimal("6"),
            is_active=True,
        )
        # Единственный проект 7х7 — по умолчанию (--min-projects=2) страница
        # под него создаваться не должна: почти пустой каталог вредит SEO.
        Project.objects.create(
            title="Дом семь на семь",
            category=self.houses,
            width=Decimal("7"),
            length=Decimal("7"),
            is_active=True,
        )
        # Два проекта 8х8, но неактивные — не должны учитываться при подсчёте.
        Project.objects.create(
            title="Дом восемь на восемь, первый",
            category=self.houses,
            width=Decimal("8"),
            length=Decimal("8"),
            is_active=False,
        )
        Project.objects.create(
            title="Дом восемь на восемь, второй",
            category=self.houses,
            width=Decimal("8"),
            length=Decimal("8"),
            is_active=False,
        )

    def call(self, *args):
        out, err = StringIO(), StringIO()
        call_command("generate_seo_landing_pages", *args, stdout=out, stderr=err)
        return out.getvalue()

    def test_creates_size_page_for_group_reaching_threshold(self):
        self.call()

        page = LandingPage.objects.get(slug="doma-iz-brusa-6x6")
        self.assertEqual(page.page_type, LandingPage.PageType.SIZE)
        self.assertEqual(page.category_id, self.houses.id)
        self.assertEqual(page.filter_width, Decimal("6"))
        self.assertEqual(page.filter_length, Decimal("6"))
        self.assertIn("6х6", page.h1)
        self.assertEqual(page.faqs.count(), 3)

    def test_skips_groups_below_threshold(self):
        self.call()

        self.assertFalse(LandingPage.objects.filter(slug="doma-iz-brusa-7x7").exists())
        self.assertFalse(LandingPage.objects.filter(slug="doma-iz-brusa-8x8").exists())

    def test_region_pages_do_not_claim_a_moscow_office(self):
        self.call()

        page = LandingPage.objects.get(slug="doma-iz-brusa-moskva")
        self.assertEqual(page.page_type, LandingPage.PageType.REGION)
        self.assertEqual(page.category_id, self.houses.id)
        self.assertIsNone(page.filter_width)

        combined_text = (
            page.main_text
            + " ".join(f"{faq.question} {faq.answer}" for faq in page.faqs.all())
        ).lower()
        # Ключевое требование: страница честно говорит, что офиса в Москве
        # нет, а не подразумевает обратное.
        self.assertIn("офиса", combined_text)
        self.assertIn("пока нет", combined_text)

        bath_page = LandingPage.objects.get(slug="bani-iz-brusa-moskva")
        self.assertEqual(bath_page.category_id, self.baths.id)

    def test_is_idempotent_without_overwrite(self):
        self.call()
        page = LandingPage.objects.get(slug="doma-iz-brusa-6x6")
        page.h1 = "Отредактировано вручную"
        page.save()

        self.call()

        page.refresh_from_db()
        self.assertEqual(page.h1, "Отредактировано вручную")

    def test_overwrite_regenerates_content(self):
        self.call()
        page = LandingPage.objects.get(slug="doma-iz-brusa-6x6")
        page.h1 = "Отредактировано вручную"
        page.save()

        self.call("--overwrite")

        page.refresh_from_db()
        self.assertNotEqual(page.h1, "Отредактировано вручную")

    def test_dry_run_does_not_touch_database(self):
        self.call("--dry-run")

        self.assertEqual(LandingPage.objects.count(), 0)

    def test_only_sizes_skips_region_pages(self):
        self.call("--only-sizes")

        self.assertTrue(LandingPage.objects.filter(slug="doma-iz-brusa-6x6").exists())
        self.assertFalse(LandingPage.objects.filter(slug="doma-iz-brusa-moskva").exists())

    def test_only_region_skips_size_pages(self):
        self.call("--only-region")

        self.assertFalse(LandingPage.objects.filter(slug="doma-iz-brusa-6x6").exists())
        self.assertTrue(LandingPage.objects.filter(slug="doma-iz-brusa-moskva").exists())
