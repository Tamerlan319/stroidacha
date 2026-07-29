from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from catalog.models import BuildPackage, CostRate, FoundationType, Material, RoofCovering
from catalog.rate_service import CostRateService


class Command(BaseCommand):
    help = "Проверяет, хватает ли действующих сметных ставок для V4 калькулятора."

    def add_arguments(self, parser):
        parser.add_argument("--date", dest="rate_date", help="Дата YYYY-MM-DD; по умолчанию сегодня")

    def handle(self, *args, **options):
        rate_date = options.get("rate_date")
        if rate_date:
            from datetime import date
            rate_date = date.fromisoformat(rate_date)
        else:
            rate_date = timezone.localdate()
        service = CostRateService(rate_date)
        missing = []

        packages = list(BuildPackage.objects.filter(is_active=True))
        materials = list(Material.objects.filter(is_active=True))

        for material in materials:
            for component, unit in (
                (CostRate.Component.WALL_MATERIAL, CostRate.Unit.M3),
                (CostRate.Component.PARTITION_MATERIAL, CostRate.Unit.M3),
                (CostRate.Component.WALL_PROCESSING, CostRate.Unit.M3),
            ):
                if service.get(component, material=material, expected_unit=unit) is None:
                    missing.append(f"{component}: {material}")

        for package in packages:
            for component, unit in (
                (CostRate.Component.BEAMS_LUMBER, CostRate.Unit.M3),
                (CostRate.Component.RAFTERS_LUMBER, CostRate.Unit.M3),
                (CostRate.Component.LATHING_LUMBER, CostRate.Unit.M3),
                (CostRate.Component.OTHER_LUMBER, CostRate.Unit.M3),
                (CostRate.Component.GABLE, CostRate.Unit.M2),
                (CostRate.Component.TEMPORARY_ROOF, CostRate.Unit.M2),
                (CostRate.Component.CONSUMABLES, CostRate.Unit.M3),
                (CostRate.Component.ASSEMBLY_FIRST, CostRate.Unit.M2),
                (CostRate.Component.ASSEMBLY_MANSARD, CostRate.Unit.M2),
                (CostRate.Component.ASSEMBLY_SECOND, CostRate.Unit.M2),
                (CostRate.Component.TERRACE, CostRate.Unit.M2),
                (CostRate.Component.DELIVERY, CostRate.Unit.FIXED),
                (CostRate.Component.DOCUMENTATION, CostRate.Unit.FIXED),
            ):
                if service.get(component, package=package, expected_unit=unit) is None:
                    missing.append(f"{component}: {package}")

        for foundation in FoundationType.objects.filter(is_active=True):
            component = {
                FoundationType.PricingMethod.PER_UNIT: CostRate.Component.FOUNDATION_UNIT,
                FoundationType.PricingMethod.PER_FOOTPRINT: CostRate.Component.FOUNDATION_FOOTPRINT,
                FoundationType.PricingMethod.FIXED: CostRate.Component.FOUNDATION_FIXED,
            }.get(foundation.pricing_method)
            unit = {
                FoundationType.PricingMethod.PER_UNIT: CostRate.Unit.UNIT,
                FoundationType.PricingMethod.PER_FOOTPRINT: CostRate.Unit.M2,
                FoundationType.PricingMethod.FIXED: CostRate.Unit.FIXED,
            }.get(foundation.pricing_method)
            if component and service.get(component, foundation=foundation, expected_unit=unit, allow_fallback=False) is None:
                missing.append(f"{component}: {foundation}")

        for covering in RoofCovering.objects.filter(is_active=True):
            if service.get(
                CostRate.Component.ROOF_COVERING,
                roof_covering=covering,
                expected_unit=CostRate.Unit.M2,
                allow_fallback=False,
            ) is None:
                missing.append(f"roof_covering: {covering}")

        self.stdout.write(f"Дата ставок: {rate_date:%d.%m.%Y}")
        self.stdout.write(f"Активных строк CostRate: {CostRate.objects.filter(is_active=True).count()}")
        if missing:
            self.stdout.write(self.style.ERROR(f"Не хватает ставок: {len(missing)}"))
            for item in missing:
                self.stdout.write(f"  - {item}")
            raise CommandError("Заполните отсутствующие ставки в Django Admin.")
        self.stdout.write(self.style.SUCCESS("Все обязательные ставки V4 настроены."))
