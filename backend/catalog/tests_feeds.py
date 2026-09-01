from decimal import Decimal
from xml.etree import ElementTree

from django.test import TestCase

from .models import PricingSettings, Project, ProjectCategory


class RealtyFeedTests(TestCase):
    def setUp(self):
        # Ядро цен не должно ничего индексировать в этих тестах — иначе
        # price_from в проверках "плывёт" вместе с текущей активной
        # индексацией, которую могли настроить более ранние тесты/миграции.
        PricingSettings.objects.all().update(is_active=False)

        self.houses = ProjectCategory.objects.create(title="Дома", slug="houses")
        self.baths = ProjectCategory.objects.create(title="Бани", slug="baths")
        self.garages = ProjectCategory.objects.create(title="Гаражи", slug="garages")

        self.house = Project.objects.create(
            title="Проект дома из бруса ДБ-01",
            category=self.houses,
            area=Decimal("70.00"),
            width=Decimal("6"),
            length=Decimal("7"),
            price_from=916000,
            is_active=True,
        )
        self.bath = Project.objects.create(
            title="Проект бани из бруса Б-01",
            category=self.baths,
            area=Decimal("30.00"),
            price_from=450000,
            is_active=True,
        )
        # Не должны попасть в фид ни при каких условиях:
        self.inactive_house = Project.objects.create(
            title="Снятый с продажи дом",
            category=self.houses,
            price_from=500000,
            is_active=False,
        )
        self.garage = Project.objects.create(
            title="Гараж на два авто",
            category=self.garages,
            price_from=300000,
            is_active=True,
        )
        self.priceless_house = Project.objects.create(
            title="Дом без цены",
            category=self.houses,
            price_from=None,
            is_active=True,
        )

    def fetch_feed(self):
        response = self.client.get("/api/feeds/realty.yml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"])
        return ElementTree.fromstring(response.content)

    def test_feed_is_well_formed_xml_with_expected_shape(self):
        root = self.fetch_feed()

        self.assertEqual(root.tag, "yml_catalog")
        shop = root.find("shop")
        self.assertIsNotNone(shop)
        self.assertEqual(shop.findtext("name"), "Брусодел")

        offer_ids = {offer.get("id") for offer in shop.findall("offers/offer")}
        self.assertIn(self.house.slug, offer_ids)
        self.assertIn(self.bath.slug, offer_ids)

    def test_excludes_inactive_and_priceless_and_other_categories(self):
        root = self.fetch_feed()
        offer_ids = {offer.get("id") for offer in root.findall("shop/offers/offer")}

        self.assertNotIn(self.inactive_house.slug, offer_ids)
        self.assertNotIn(self.garage.slug, offer_ids)
        self.assertNotIn(self.priceless_house.slug, offer_ids)

    def test_house_offer_fields(self):
        root = self.fetch_feed()
        offer = root.find(f"shop/offers/offer[@id='{self.house.slug}']")

        self.assertEqual(offer.findtext("categoryId"), "3")
        self.assertEqual(offer.findtext("currencyId"), "RUR")
        self.assertEqual(offer.findtext("set-ids"), "s-houses")
        self.assertEqual(offer.find("price").get("from"), "true")
        self.assertEqual(offer.findtext("price"), "916000")
        self.assertEqual(
            offer.findtext("url"), f"https://brusodel.ru/projects/{self.house.slug}"
        )

        params = {p.get("name"): p.text for p in offer.findall("param")}
        # Площадь хранится как NUMERIC(...) → приходит Decimal("70.00") — в
        # фиде должно быть "70", а не "70.00" (та же ловушка, что и в
        # Project.computed_size_text).
        self.assertEqual(params["Площадь"], "70")
        self.assertEqual(params["Тип предложения"], "Продажа")
        self.assertEqual(params["Отделка"], "Под ключ")

    def test_bath_offer_uses_bath_set(self):
        root = self.fetch_feed()
        offer = root.find(f"shop/offers/offer[@id='{self.bath.slug}']")

        self.assertEqual(offer.findtext("set-ids"), "s-baths")

    def test_categories_element_present_and_before_offers(self):
        root = self.fetch_feed()
        shop = root.find("shop")

        category = shop.find("categories/category")
        self.assertIsNotNone(category)
        self.assertEqual(category.get("id"), "3")
        self.assertEqual(category.text, "Дом")

        # Яндекс отдельно проверяет порядок: categories должен идти раньше
        # offers, иначе фид не проходит валидацию целиком.
        children = list(shop)
        tags = [child.tag for child in children]
        self.assertLess(tags.index("categories"), tags.index("offers"))

    def test_sets_declared_for_used_categories_only(self):
        root = self.fetch_feed()
        set_ids = {s.get("id") for s in root.findall("shop/sets/set")}

        self.assertEqual(set_ids, {"s-houses", "s-baths"})

    def test_picture_urls_are_absolute(self):
        root = self.fetch_feed()
        # ни у одного тестового проекта нет реального файла картинки —
        # проверяем только то, что фид не падает без main_image/галереи.
        offer = root.find(f"shop/offers/offer[@id='{self.house.slug}']")
        self.assertIsNone(offer.find("picture"))
