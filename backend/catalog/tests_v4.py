from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalog.models import BuildPackage, CostRate, Material
from catalog.rate_service import CostRateService


class CostRateTests(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.material, _ = Material.objects.update_or_create(
            code="rate-test-material",
            defaults={
                "kind": Material.Kind.REGULAR,
                "group_title": "Тест",
                "title": "Тестовый материал",
                "is_active": True,
            },
        )
        self.package, _ = BuildPackage.objects.update_or_create(
            code="rate-test-package", defaults={"title": "Тестовая комплектация", "is_active": True}
        )

    def test_specific_rate_wins_over_generic(self):
        CostRate.objects.create(
            component=CostRate.Component.STRUCTURAL_LUMBER,
            title="generic",
            unit=CostRate.Unit.M3,
            rate=Decimal("100"),
            valid_from=self.today,
        )
        CostRate.objects.create(
            component=CostRate.Component.STRUCTURAL_LUMBER,
            title="package",
            unit=CostRate.Unit.M3,
            rate=Decimal("200"),
            package=self.package,
            valid_from=self.today,
        )
        resolved = CostRateService(self.today).require(
            CostRate.Component.STRUCTURAL_LUMBER,
            package=self.package,
            expected_unit=CostRate.Unit.M3,
        )
        self.assertEqual(resolved.rate, Decimal("200"))

    def test_structural_specific_component_can_fallback_to_generic(self):
        CostRate.objects.create(
            component=CostRate.Component.STRUCTURAL_LUMBER,
            title="generic",
            unit=CostRate.Unit.M3,
            rate=Decimal("250"),
            package=self.package,
            valid_from=self.today,
        )
        resolved = CostRateService(self.today).require(
            CostRate.Component.BEAMS_LUMBER,
            package=self.package,
            expected_unit=CostRate.Unit.M3,
        )
        self.assertEqual(resolved.rate, Decimal("250"))
        self.assertEqual(resolved.fallback_component, CostRate.Component.STRUCTURAL_LUMBER)

    def test_partition_can_fallback_to_wall_material(self):
        CostRate.objects.create(
            component=CostRate.Component.WALL_MATERIAL,
            title="wall",
            unit=CostRate.Unit.M3,
            rate=Decimal("300"),
            material=self.material,
            valid_from=self.today,
        )
        resolved = CostRateService(self.today).require(
            CostRate.Component.PARTITION_MATERIAL,
            material=self.material,
            expected_unit=CostRate.Unit.M3,
        )
        self.assertEqual(resolved.rate, Decimal("300"))
        self.assertEqual(resolved.fallback_component, CostRate.Component.WALL_MATERIAL)

    def test_newer_rate_closes_previous_open_period(self):
        first = CostRate.objects.create(
            component=CostRate.Component.WALL_MATERIAL,
            title="first",
            unit=CostRate.Unit.M3,
            rate=Decimal("100"),
            material=self.material,
            valid_from=self.today,
        )
        next_day = self.today + timedelta(days=5)
        second = CostRate(
            component=CostRate.Component.WALL_MATERIAL,
            title="second",
            unit=CostRate.Unit.M3,
            rate=Decimal("110"),
            material=self.material,
            valid_from=next_day,
        )
        second.full_clean()
        second.save()
        first.refresh_from_db()
        self.assertEqual(first.valid_to, next_day - timedelta(days=1))

    def test_same_date_overlap_is_rejected(self):
        CostRate.objects.create(
            component=CostRate.Component.WALL_MATERIAL,
            title="first",
            unit=CostRate.Unit.M3,
            rate=Decimal("100"),
            material=self.material,
            valid_from=self.today,
        )
        duplicate = CostRate(
            component=CostRate.Component.WALL_MATERIAL,
            title="second",
            unit=CostRate.Unit.M3,
            rate=Decimal("110"),
            material=self.material,
            valid_from=self.today,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

