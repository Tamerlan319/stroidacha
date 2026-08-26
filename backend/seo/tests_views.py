from django.test import TestCase
from rest_framework.test import APIClient

from catalog.models import ProjectCategory

from .models import LandingPage


class LandingPageListCategoryFilterTests(TestCase):
    """Фильтр ?category= используется блоком "Смотрите также" на страницах
    каталога (frontend/app/[slug]/page.tsx), чтобы показать соседние
    SEO-страницы того же раздела."""

    def setUp(self):
        self.client = APIClient()
        self.houses = ProjectCategory.objects.create(title="Дома", slug="houses")
        self.baths = ProjectCategory.objects.create(title="Бани", slug="baths")

        self.house_hub = LandingPage.objects.create(
            title="Дома из бруса",
            slug="doma-iz-brusa",
            h1="Дома из бруса",
            category=self.houses,
        )
        self.house_size = LandingPage.objects.create(
            title="Дома из бруса 6х6",
            slug="doma-iz-brusa-6x6",
            h1="Дома из бруса 6х6",
            category=self.houses,
        )
        self.bath_hub = LandingPage.objects.create(
            title="Бани из бруса",
            slug="bani-iz-brusa",
            h1="Бани из бруса",
            category=self.baths,
        )
        self.no_category_page = LandingPage.objects.create(
            title="Доставка по России",
            slug="dostavka-po-rossii",
            h1="Доставка по России",
        )

    def test_without_filter_returns_all_active_pages(self):
        response = self.client.get("/api/landing-pages/")

        self.assertEqual(response.status_code, 200)
        slugs = {item["slug"] for item in response.data}
        self.assertEqual(
            slugs,
            {"doma-iz-brusa", "doma-iz-brusa-6x6", "bani-iz-brusa", "dostavka-po-rossii"},
        )

    def test_category_filter_returns_only_matching_pages(self):
        response = self.client.get("/api/landing-pages/", {"category": "houses"})

        self.assertEqual(response.status_code, 200)
        slugs = {item["slug"] for item in response.data}
        self.assertEqual(slugs, {"doma-iz-brusa", "doma-iz-brusa-6x6"})

    def test_category_filter_excludes_inactive_pages(self):
        self.house_size.is_active = False
        self.house_size.save()

        response = self.client.get("/api/landing-pages/", {"category": "houses"})

        slugs = {item["slug"] for item in response.data}
        self.assertEqual(slugs, {"doma-iz-brusa"})

    def test_unknown_category_returns_empty_list(self):
        response = self.client.get("/api/landing-pages/", {"category": "does-not-exist"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.data), [])
