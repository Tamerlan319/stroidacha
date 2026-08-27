from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from catalog.models import (
    BuildPackage,
    CostRate,
    FoundationType,
    Material,
    PricingRule,
    PricingSettings,
    Project,
    ProjectCategory,
    ProjectOffer,
    ProjectTechnicalData,
    ProjectMaterialTakeoff,
    RoofCovering,
)
from calculator.models import (
    CalculatorFoundation,
    CalculatorMaterial,
    CalculatorRoofCovering,
    CalculatorSettings,
    HouseCostProfile,
)


class CalculatorV4ApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        PricingRule.objects.all().delete()
        pricing, _ = PricingSettings.objects.update_or_create(
            title="Основная индексация",
            defaults={
                "house_percent": 0,
                "addon_percent": 0,
                "foundation_percent": 0,
                "roof_covering_percent": 0,
                "extra_percent": 0,
                "rounding_step": 1,
                "is_active": True,
            },
        )
        PricingSettings.objects.exclude(pk=pricing.pk).update(is_active=False)

        self.package, _ = BuildPackage.objects.update_or_create(
            code="pod-usadku", defaults={"title": "Под усадку", "is_active": True}
        )
        settings, _ = CalculatorSettings.objects.update_or_create(
            title="Основной калькулятор",
            defaults={
                "min_area": 20,
                "max_area": 600,
                "price_range_percent": 8,
                "default_package": self.package,
                "is_active": True,
            },
        )
        CalculatorSettings.objects.exclude(pk=settings.pk).update(is_active=False)

        HouseCostProfile.objects.update_or_create(
            package=self.package,
            defaults={
                "title": "Геометрия теста",
                "first_floor_height_m": Decimal("2.7"),
                "second_floor_height_m": Decimal("2.5"),
                "mansard_knee_wall_height_m": Decimal("0"),
                "external_openings_ratio": Decimal("0.12"),
                "internal_wall_length_per_m2": Decimal("0.15"),
                "internal_wall_length_per_bedroom_m": Decimal("1.5"),
                "partition_height_m": Decimal("2.6"),
                "internal_openings_ratio": Decimal("0.08"),
                "joist_spacing_m": Decimal("0.59"),
                "joist_section_width_mm": 100,
                "joist_section_height_mm": 150,
                "joist_systems_one_floor": Decimal("1"),
                "joist_systems_mansard": Decimal("2"),
                "joist_systems_two_floor": Decimal("2"),
                "rafter_spacing_m": Decimal("0.59"),
                "rafter_section_width_mm": 50,
                "rafter_section_height_mm": 150,
                "tie_section_width_mm": 50,
                "tie_section_height_mm": 150,
                "tie_length_factor": Decimal("1"),
                "counter_batten_width_mm": 50,
                "counter_batten_height_mm": 50,
                "lathing_volume_per_roof_m2": Decimal("0.006"),
                "default_roof_pitch_deg": Decimal("35"),
                "default_roof_overhang_m": Decimal("0.5"),
                "is_active": True,
            },
        )

        self.material, _ = Material.objects.update_or_create(
            code="ordinary-150x150",
            defaults={
                "kind": Material.Kind.REGULAR,
                "group_title": "Обычный брус",
                "title": "Обычный брус 150×150",
                "section_width_mm": 150,
                "section_height_mm": 150,
                "is_active": True,
            },
        )
        CalculatorMaterial.objects.update_or_create(
            material=self.material,
            defaults={
                "wall_thickness_mm": 150,
                "partition_thickness_mm": 100,
                "wall_waste_percent": 0,
                "is_active": True,
            },
        )

        self.category, _ = ProjectCategory.objects.update_or_create(
            slug="houses", defaults={"title": "Дома", "is_active": True}
        )
        self.project = Project.objects.create(
            external_id="DB-TEST-V4",
            title="Тестовый дом V4",
            slug="db-test-v4",
            category=self.category,
            construction_type=Project.ConstructionType.TIMBER,
            area=52,
            floors=Decimal("1.5"),
            width=6,
            length=6,
            bedrooms=2,
        )

        self.today = timezone.localdate()
        self._rate(CostRate.Component.WALL_MATERIAL, CostRate.Unit.M3, 10000, material=self.material)
        self._rate(CostRate.Component.PARTITION_MATERIAL, CostRate.Unit.M3, 8000, material=self.material)
        self._rate(CostRate.Component.WALL_PROCESSING, CostRate.Unit.M3, 500, material=self.material)
        self._rate(CostRate.Component.STRUCTURAL_LUMBER, CostRate.Unit.M3, 5000, package=self.package)
        self._rate(CostRate.Component.GABLE, CostRate.Unit.M2, 100, package=self.package)
        self._rate(CostRate.Component.TEMPORARY_ROOF, CostRate.Unit.M2, 50, package=self.package)
        self._rate(CostRate.Component.CONSUMABLES, CostRate.Unit.M3, 0, package=self.package)
        self._rate(CostRate.Component.ASSEMBLY_FIRST, CostRate.Unit.M2, 100, package=self.package)
        self._rate(CostRate.Component.ASSEMBLY_MANSARD, CostRate.Unit.M2, 200, package=self.package)
        self._rate(CostRate.Component.ASSEMBLY_SECOND, CostRate.Unit.M2, 300, package=self.package)
        self._rate(CostRate.Component.TERRACE, CostRate.Unit.M2, 0, package=self.package)
        self._rate(CostRate.Component.DELIVERY, CostRate.Unit.FIXED, 1000, package=self.package)
        self._rate(CostRate.Component.DOCUMENTATION, CostRate.Unit.FIXED, 500, package=self.package)

    def _rate(self, component, unit, rate, **target):
        return CostRate.objects.create(
            component=component,
            title=f"test {component}",
            unit=unit,
            rate=Decimal(rate),
            valid_from=self.today,
            source=CostRate.Source.OFFICE,
            **target,
        )

    def payload(self, **kwargs):
        data = {
            "area": "52",
            "width": "6",
            "length": "6",
            "floors": "1.5",
            "material": self.material.code,
            "package": self.package.code,
        }
        data.update(kwargs)
        return data

    def test_runtime_does_not_need_project_offer(self):
        ProjectOffer.objects.all().delete()
        response = self.client.post("/api/calculator/calculate/", self.payload(), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["method"], "exact_quantity_rate_v4")
        # Без ProjectOffer у "похожих проектов" нет цены (и, значит, нет и
        # самих карточек) — но расчёт основной цены это не должно ломать.
        self.assertEqual(response.data["similar_projects"], [])
        self.assertEqual(response.data["calculation_mode"], "quick")

    def test_similar_projects_shown_and_self_excluded(self):
        close_match = Project.objects.create(
            external_id="DB-TEST-CLOSE",
            title="Похожий тестовый дом",
            slug="db-test-close",
            category=self.category,
            construction_type=Project.ConstructionType.TIMBER,
            area=55,
            floors=Decimal("1.5"),
            width=6,
            length=6,
        )
        ProjectOffer.objects.create(
            project=close_match, material=self.material, build_package=self.package,
            base_price=900_000,
        )
        far_match = Project.objects.create(
            external_id="DB-TEST-FAR",
            title="Непохожий тестовый дом",
            slug="db-test-far",
            category=self.category,
            construction_type=Project.ConstructionType.TIMBER,
            area=400,
            floors=Decimal("1.5"),
            width=20,
            length=20,
        )
        ProjectOffer.objects.create(
            project=far_match, material=self.material, build_package=self.package,
            base_price=9_000_000,
        )

        response = self.client.post(
            "/api/calculator/calculate/", self.payload(project="DB-TEST-V4"), format="json"
        )
        self.assertEqual(response.status_code, 200)
        slugs = [item["slug"] for item in response.data["similar_projects"]]
        # Сам запрошенный проект (project=DB-TEST-V4) не должен предлагаться
        # как "похожий на самого себя".
        self.assertNotIn("db-test-v4", slugs)
        # Ближайший по площади (55 против 400) должен идти первым.
        self.assertEqual(slugs[0], "db-test-close")
        self.assertEqual(response.data["similar_projects"][0]["price_from"], 900_000)

    def test_verified_technical_passport_overrides_quick_takeoff(self):
        ProjectTechnicalData.objects.create(
            project=self.project,
            data_source=ProjectTechnicalData.DataSource.ESTIMATE,
            is_verified=True,
            beams_volume_m3=Decimal("1"),
            rafters_volume_m3=Decimal("1"),
            lathing_volume_m3=Decimal("1"),
            other_structural_lumber_volume_m3=Decimal("0"),
            gable_area_m2=Decimal("10"),
            roof_area_m2=Decimal("60"),
            first_floor_area_m2=Decimal("36"),
            mansard_area_m2=Decimal("16"),
        )
        ProjectMaterialTakeoff.objects.create(
            project=self.project, material=self.material,
            external_wall_volume_m3=Decimal("20"), internal_wall_volume_m3=Decimal("5"),
            data_source=ProjectTechnicalData.DataSource.ESTIMATE, is_verified=True,
        )
        response = self.client.post(
            "/api/calculator/calculate/",
            self.payload(project=self.project.external_id),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["calculation_mode"], "verified_project")
        lines = {line["code"]: line for line in response.data["component_details"]["house"]["lines"]}
        self.assertEqual(lines["external_walls"]["quantity"], 20.0)
        self.assertEqual(lines["partitions"]["quantity"], 5.0)
        self.assertEqual(lines["beams"]["quantity"], 1.0)

    def test_historical_rate_date_is_used(self):
        current = CostRate.objects.get(component=CostRate.Component.WALL_MATERIAL, material=self.material)
        old_day = self.today - timedelta(days=30)
        CostRate.objects.exclude(pk=current.pk).update(valid_from=old_day)
        current.valid_from = self.today
        current.save(update_fields=["valid_from"])
        CostRate.objects.create(
            component=CostRate.Component.WALL_MATERIAL,
            title="old wall",
            unit=CostRate.Unit.M3,
            rate=Decimal("5000"),
            material=self.material,
            valid_from=old_day,
            valid_to=self.today - timedelta(days=1),
            source=CostRate.Source.OFFICE,
        )
        current_response = self.client.post("/api/calculator/calculate/", self.payload(), format="json")
        old_response = self.client.post(
            "/api/calculator/calculate/",
            self.payload(price_date=old_day.isoformat()),
            format="json",
        )
        self.assertEqual(current_response.status_code, 200)
        self.assertEqual(old_response.status_code, 200)
        self.assertLess(old_response.data["total"], current_response.data["total"])

    def test_one_floor_36m_is_cheaper_than_52m_mansard(self):
        one = self.client.post(
            "/api/calculator/calculate/", self.payload(area="36", floors="1", bedrooms=1), format="json"
        )
        mansard = self.client.post("/api/calculator/calculate/", self.payload(), format="json")
        self.assertEqual(one.status_code, 200)
        self.assertEqual(mansard.status_code, 200)
        self.assertLess(one.data["total"], mansard.data["total"])

    def test_impossible_one_floor_geometry_is_rejected(self):
        response = self.client.post(
            "/api/calculator/calculate/", self.payload(floors="1"), format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_foundation_exact_quantity_x_historical_rate(self):
        foundation, _ = FoundationType.objects.update_or_create(
            code="screw-piles",
            defaults={
                "title": "Свайно-винтовой",
                "pricing_method": FoundationType.PricingMethod.PER_UNIT,
                "unit_name": "свая",
                "is_active": True,
            },
        )
        CalculatorFoundation.objects.update_or_create(
            foundation=foundation,
            defaults={"pile_spacing_m": Decimal("3"), "minimum_price": 0, "is_active": True},
        )
        self._rate(CostRate.Component.FOUNDATION_UNIT, CostRate.Unit.UNIT, 10000, foundation=foundation)
        base = self.client.post("/api/calculator/calculate/", self.payload(), format="json")
        response = self.client.post(
            "/api/calculator/calculate/",
            self.payload(foundation=foundation.code, foundation_pile_count=12),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"] - base.data["total"], 120000)
        self.assertEqual(response.data["component_details"]["foundation"]["quantity_source"], "explicit")

    def test_roof_exact_area_x_historical_rate(self):
        covering, _ = RoofCovering.objects.update_or_create(
            code="metal-tile", defaults={"title": "Металлочерепица", "is_active": True}
        )
        CalculatorRoofCovering.objects.update_or_create(
            covering=covering, defaults={"minimum_price": 0, "is_active": True}
        )
        self._rate(CostRate.Component.ROOF_COVERING, CostRate.Unit.M2, 2000, roof_covering=covering)
        base = self.client.post("/api/calculator/calculate/", self.payload(roof_area="70"), format="json")
        response = self.client.post(
            "/api/calculator/calculate/",
            self.payload(roof=covering.code, roof_area="70"),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"] - base.data["total"], 140000)

    def test_missing_required_rate_is_explicit_error(self):
        CostRate.objects.filter(component=CostRate.Component.WALL_MATERIAL, material=self.material).delete()
        response = self.client.post("/api/calculator/calculate/", self.payload(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Сметные ставки", response.data["detail"])

    def test_config_declares_v4(self):
        response = self.client.get("/api/calculator/config/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["engine"], "exact_quantity_rate_v4")
        self.assertTrue(response.data["rate_history"])
