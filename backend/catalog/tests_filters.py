from decimal import Decimal

from django.test import TestCase

from .filters import floors_label, material_group_value
from .models import (
    CostRate,
    Material,
    PricingRule,
    PricingSettings,
    Project,
    ProjectCategory,
    ProjectOffer,
)


class CatalogFiltersTests(TestCase):
    """Фильтры каталога и счётчики вариантов (/api/projects/facets/)."""

    def setUp(self):
        PricingRule.objects.all().delete()
        CostRate.objects.all().delete()
        settings, _ = PricingSettings.objects.update_or_create(
            title="Основная индексация",
            defaults={
                "house_percent": 0,
                "addon_percent": 0,
                "foundation_percent": 0,
                "roof_covering_percent": 0,
                "extra_percent": 0,
                "rounding_step": 1000,
                "is_active": True,
            },
        )
        PricingSettings.objects.exclude(pk=settings.pk).update(is_active=False)

        self.category = ProjectCategory.objects.create(title="Дома", slug="houses-filters-test")
        other_category = ProjectCategory.objects.create(title="Бани", slug="baths-filters-test")

        ordinary = self._material("ordinary-150x150", Material.Kind.REGULAR, "Обычный брус", sort_order=2)
        profiled = self._material("profiled-145x145", Material.Kind.PROFILED, "Профилированный брус", sort_order=4)
        glued = self._material("glued-200x200-filters-test", Material.Kind.OTHER, "Клеёный брус", sort_order=50)

        self._project("DB-F-1", floors="1", width=6, length=6, area=36, offers={ordinary: 1_000_000, profiled: 1_200_000})
        self._project("DB-F-2", floors="1.5", width=8, length=10, area=120, offers={ordinary: 2_000_000, glued: 2_500_000})
        self._project("DB-F-3", floors="2", width=10, length=12, area=200, offers={profiled: 3_000_000})
        self._project("DB-F-4", floors="3", width=12, length=12, area=300, offers={glued: 5_000_000}, is_active=False)
        self._project(
            "BB-F-1", floors="1", width=4, length=5, area=20, offers={ordinary: 500_000}, category=other_category
        )

    def _material(self, code, kind, group_title, *, sort_order):
        material, _ = Material.objects.update_or_create(
            code=code,
            defaults={
                "kind": kind,
                "group_title": group_title,
                "title": f"{group_title} ({code})",
                "sort_order": sort_order,
                "is_active": True,
            },
        )
        return material

    def _project(self, external_id, *, floors, width, length, area, offers, is_active=True, category=None):
        project = Project.objects.create(
            external_id=external_id,
            title=f"Проект {external_id}",
            slug=external_id.lower(),
            category=category or self.category,
            floors=Decimal(floors),
            width=width,
            length=length,
            area=area,
            is_active=is_active,
        )
        for material, price in offers.items():
            ProjectOffer.objects.create(project=project, material=material, base_price=price)
        return project

    def _facets(self, **params):
        response = self.client.get("/api/projects/facets/", {"category": self.category.slug, **params})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _list_slugs(self, **params):
        response = self.client.get("/api/projects/", {"category": self.category.slug, **params})
        self.assertEqual(response.status_code, 200)
        return sorted(item["slug"] for item in response.json())

    @staticmethod
    def _options(options):
        return [(option["value"], option["label"], option["count"]) for option in options]

    @staticmethod
    def _counts(options):
        return {option["value"]: option["count"] for option in options}

    def test_options_come_from_active_projects_of_the_category(self):
        facets = self._facets()

        self.assertEqual(facets["total"], 3)
        self.assertEqual(
            self._options(facets["floors"]),
            [("1", "1 этаж", 1), ("1.5", "1 + мансарда", 1), ("2", "2 этажа", 1)],
        )
        self.assertEqual(
            self._options(facets["materials"]),
            [
                ("obychnyy-brus", "Обычный брус", 2),
                ("profilirovannyy-brus", "Профилированный брус", 2),
                ("kleenyy-brus", "Клеёный брус", 1),
            ],
        )
        self.assertEqual(self._options(facets["construction_types"]), [("timber", "Брус", 3)])

    def test_option_counts_ignore_own_group_but_respect_the_others(self):
        facets = self._facets(floors="1.5", material="kleenyy-brus")

        self.assertEqual(facets["total"], 1)
        self.assertEqual(self._counts(facets["floors"]), {"1": 0, "1.5": 1, "2": 0})
        self.assertEqual(
            self._counts(facets["materials"]),
            {"obychnyy-brus": 1, "profilirovannyy-brus": 0, "kleenyy-brus": 1},
        )

    def test_filters_select_expected_projects(self):
        self.assertEqual(self._list_slugs(floors="1,2"), ["db-f-1", "db-f-3"])
        self.assertEqual(self._list_slugs(material="kleenyy-brus"), ["db-f-2"])
        self.assertEqual(self._list_slugs(material="profiled"), ["db-f-1", "db-f-3"])
        self.assertEqual(self._list_slugs(size_min="7", size_max="12"), ["db-f-2", "db-f-3"])
        self.assertEqual(self._list_slugs(area_min="100", area_max="150"), ["db-f-2"])
        self.assertEqual(self._list_slugs(price_min="1500000", price_max="2000000"), ["db-f-2"])

    def test_list_and_facet_total_agree(self):
        cases = [
            {},
            {"floors": "1,2"},
            {"material": "profilirovannyy-brus"},
            {"material": "profiled"},
            {"size_min": "7"},
            {"size_max": "10"},
            {"area_min": "100", "area_max": "150"},
            {"price_min": "1500000"},
            {"price_max": "2000000", "floors": "1,1.5"},
            {"construction_type": "timber", "material": "obychnyy-brus", "size_min": "6", "size_max": "10"},
        ]
        for params in cases:
            with self.subTest(params=params):
                self.assertEqual(len(self._list_slugs(**params)), self._facets(**params)["total"])

    def test_invalid_numbers_are_ignored(self):
        self.assertEqual(len(self._list_slugs(price_min="abc", area_max="")), 3)
        self.assertEqual(self._facets(price_min="abc")["total"], 3)

    def test_ranges_cover_the_whole_selection_regardless_of_other_filters(self):
        ranges = self._facets(floors="2")["ranges"]

        # Размер и площадь — от 1, а не от самого маленького проекта.
        self.assertEqual(ranges["size"], {"min": 1, "max": 12, "step": 0.5})
        self.assertEqual(ranges["area"], {"min": 1, "max": 200, "step": 1})
        self.assertEqual(ranges["price"], {"min": 1_000_000, "max": 3_000_000, "step": 10000})

    def test_locked_size_page_limits_options_and_ranges(self):
        facets = self._facets(width="6", length="6")

        self.assertEqual(facets["total"], 1)
        self.assertEqual(self._counts(facets["floors"]), {"1": 1})
        self.assertEqual(facets["ranges"]["size"], {"min": 6, "max": 6, "step": 0.5})

    def test_selected_value_missing_from_selection_is_still_listed(self):
        facets = self._facets(floors="3")

        self.assertEqual(facets["total"], 0)
        self.assertIn(("3", "3 этажа", 0), self._options(facets["floors"]))

    def test_labels_and_values(self):
        self.assertEqual(floors_label(Decimal("1.0")), "1 этаж")
        self.assertEqual(floors_label(Decimal("2.5")), "2 + мансарда")
        self.assertEqual(floors_label(Decimal("5")), "5 этажей")
        self.assertEqual(material_group_value("Брус камерной сушки"), "brus-kamernoy-sushki")
        self.assertEqual(material_group_value("Клеёный брус"), "kleenyy-brus")
