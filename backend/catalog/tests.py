from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import (
    BuildPackage,
    CostRate,
    FoundationType,
    Material,
    PricingRule,
    PricingSettings,
    Project,
    ProjectCategory,
    ProjectFoundation,
    ProjectOffer,
    ProjectRoofCovering,
    ProjectTechnicalData,
    RoofCovering,
)
from .pricing import PricingService


class CatalogV4PricingTests(TestCase):
    """Проверки ценового ядра Catalog v4.

    Seed-миграции уже создают некоторые справочники, поэтому тесты переиспользуют
    строки по уникальным ``code``. Денежные формулы V4 используют CostRate;
    legacy-поля ``base_rate``/``rate_per_m2`` не являются источником сметы.
    """

    def setUp(self):
        PricingRule.objects.all().delete()
        CostRate.objects.all().delete()

        self.settings, _ = PricingSettings.objects.update_or_create(
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
        PricingSettings.objects.exclude(pk=self.settings.pk).update(is_active=False)

        self.category = ProjectCategory.objects.create(title="Дома", slug="houses-v4")
        self.project = Project.objects.create(
            external_id="DB-TEST-CATALOG-V4",
            title="ДБ Test Catalog V4",
            slug="db-test-catalog-v4",
            category=self.category,
            construction_type=Project.ConstructionType.TIMBER,
            area=52,
            floors=Decimal("1.5"),
            width=6,
            length=6,
        )
        self.material, _ = Material.objects.update_or_create(
            code="ordinary-150x150",
            defaults={
                "kind": Material.Kind.REGULAR,
                "group_title": "Обычный брус",
                "title": "Обычный брус 150×150",
                "is_active": True,
            },
        )
        self.package, _ = BuildPackage.objects.update_or_create(
            code="pod-usadku",
            defaults={"title": "Под усадку", "is_active": True},
        )
        self.offer = ProjectOffer.objects.create(
            project=self.project,
            material=self.material,
            build_package=self.package,
            base_price=685000,
        )
        self.today = timezone.localdate()

    def _rate(self, component, unit, rate, **target):
        return CostRate.objects.create(
            component=component,
            title=f"test {component}",
            unit=unit,
            rate=Decimal(str(rate)),
            valid_from=self.today,
            source=CostRate.Source.OFFICE,
            **target,
        )

    def test_house_and_addons_have_separate_indexation(self):
        foundation, _ = FoundationType.objects.update_or_create(
            code="screw-piles", defaults={"title": "Свайный фундамент", "is_active": True}
        )
        foundation_price = ProjectFoundation.objects.create(
            project=self.project, foundation=foundation, base_price_override=107000
        )
        roof, _ = RoofCovering.objects.update_or_create(
            code="metal-tile", defaults={"title": "Металлочерепица", "is_active": True}
        )
        roof_price = ProjectRoofCovering.objects.create(
            project=self.project, covering=roof, base_price_override=134000
        )
        self.settings.house_percent = 10
        self.settings.foundation_percent = 20
        self.settings.roof_covering_percent = 30
        self.settings.save()

        service = PricingService()
        self.assertEqual(service.get_offer_price(self.offer), 754000)
        self.assertEqual(service.get_foundation_price(foundation_price), 128000)
        self.assertEqual(service.get_roof_covering_price(roof_price), 174000)

    def test_package_rule_is_independent_from_material_rule(self):
        PricingRule.objects.create(
            settings=self.settings,
            kind=PricingRule.Kind.PACKAGE,
            title="Под усадку +10%",
            build_package=self.package,
            percent_change=10,
        )
        self.assertEqual(PricingService().get_offer_price(self.offer), 754000)

    def test_material_rule_uses_fk_not_title(self):
        PricingRule.objects.create(
            settings=self.settings,
            kind=PricingRule.Kind.MATERIAL,
            title="Материал +5%",
            material=self.material,
            percent_change=5,
        )
        self.material.title = "Материал переименован"
        self.material.save(update_fields=["title"])
        self.assertEqual(PricingService().get_offer_price(self.offer), 719000)

    def test_foundation_formula_uses_cost_rate_quantity(self):
        foundation, _ = FoundationType.objects.update_or_create(
            code="screw-piles",
            defaults={
                "title": "Свайный фундамент",
                "pricing_method": FoundationType.PricingMethod.PER_UNIT,
                "unit_name": "свая",
                "is_active": True,
            },
        )
        self._rate(
            CostRate.Component.FOUNDATION_UNIT,
            CostRate.Unit.UNIT,
            5500,
            foundation=foundation,
        )
        item = ProjectFoundation.objects.create(project=self.project, foundation=foundation, quantity=20)
        self.assertEqual(PricingService().get_foundation_price(item), 110000)

    def test_roof_formula_uses_cost_rate_and_real_roof_area(self):
        ProjectTechnicalData.objects.create(
            project=self.project,
            roof_area_m2=Decimal("77.2"),
            roof_complexity_factor=Decimal("1.000"),
        )
        covering, _ = RoofCovering.objects.update_or_create(
            code="metal-tile",
            defaults={"title": "Металлочерепица", "is_active": True},
        )
        self._rate(
            CostRate.Component.ROOF_COVERING,
            CostRate.Unit.M2,
            2730,
            roof_covering=covering,
        )
        item = ProjectRoofCovering.objects.create(project=self.project, covering=covering)
        self.assertEqual(PricingService().get_roof_covering_price(item), 211000)

    def test_project_price_from_is_minimum_offer(self):
        second, _ = Material.objects.update_or_create(
            code="profiled-145x195",
            defaults={
                "kind": Material.Kind.PROFILED,
                "group_title": "Профилированный брус",
                "title": "Профилированный брус 145×195",
                "is_active": True,
            },
        )
        ProjectOffer.objects.create(
            project=self.project,
            material=second,
            build_package=self.package,
            base_price=900000,
        )
        self.assertEqual(PricingService().get_project_price_from(self.project), 685000)
