from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import BuildPackage, CostRate, FoundationType, RoofCovering
from calculator.models import CalculatorMaterial, HouseCostProfile


class Command(BaseCommand):
    help = (
        "Показывает/переносит положительные legacy V3 ставки в исторический справочник CostRate. "
        "Используйте --apply только если старые значения являются реальным офисным прайсом, а не калибровкой."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--date", dest="rate_date", help="Дата начала YYYY-MM-DD; по умолчанию сегодня")

    def handle(self, *args, **options):
        rate_date = date.fromisoformat(options["rate_date"]) if options.get("rate_date") else timezone.localdate()
        apply = options["apply"]
        rows = []

        for cfg in CalculatorMaterial.objects.select_related("material").filter(is_active=True):
            if Decimal(cfg.wall_rate_per_m3) > 0:
                rows.append((
                    CostRate.Component.WALL_MATERIAL,
                    f"{cfg.material.title} — наружные стены",
                    CostRate.Unit.M3,
                    Decimal(cfg.wall_rate_per_m3),
                    {"material": cfg.material},
                ))
            if Decimal(cfg.partition_rate_per_m3) > 0:
                rows.append((
                    CostRate.Component.PARTITION_MATERIAL,
                    f"{cfg.material.title} — перегородки",
                    CostRate.Unit.M3,
                    Decimal(cfg.partition_rate_per_m3),
                    {"material": cfg.material},
                ))

        for profile in HouseCostProfile.objects.select_related("package").filter(is_active=True):
            package = profile.package
            mapping = [
                (CostRate.Component.STRUCTURAL_LUMBER, "Конструкционный пиломатериал", CostRate.Unit.M3, profile.structural_lumber_rate_per_m3),
                (CostRate.Component.GABLE, "Фронтоны", CostRate.Unit.M2, profile.gable_cladding_rate_per_m2),
                (CostRate.Component.TEMPORARY_ROOF, "Временная кровля / мембрана", CostRate.Unit.M2, profile.temporary_roof_rate_per_m2),
                (CostRate.Component.CONSUMABLES, "Расходники", CostRate.Unit.M3, profile.consumables_rate_per_wall_m3),
                (CostRate.Component.ASSEMBLY_FIRST, "Сборка 1-го этажа", CostRate.Unit.M2, profile.first_floor_assembly_rate_per_m2),
                (CostRate.Component.ASSEMBLY_MANSARD, "Сборка мансарды", CostRate.Unit.M2, profile.mansard_assembly_rate_per_m2),
                (CostRate.Component.ASSEMBLY_SECOND, "Сборка 2-го этажа", CostRate.Unit.M2, profile.second_floor_assembly_rate_per_m2),
                (CostRate.Component.TERRACE, "Терраса", CostRate.Unit.M2, profile.terrace_rate_per_m2),
            ]
            for component, title, unit, value in mapping:
                if Decimal(value) > 0:
                    rows.append((component, f"{package.title} — {title}", unit, Decimal(value), {"package": package}))
            if Decimal(profile.fixed_package_cost) > 0:
                rows.append((
                    CostRate.Component.DELIVERY,
                    f"{package.title} — legacy фиксированная часть",
                    CostRate.Unit.FIXED,
                    Decimal(profile.fixed_package_cost),
                    {"package": package},
                ))
                rows.append((
                    CostRate.Component.DOCUMENTATION,
                    f"{package.title} — документация (legacy: не выделена)",
                    CostRate.Unit.FIXED,
                    Decimal("0"),
                    {"package": package},
                ))

        for foundation in FoundationType.objects.filter(is_active=True):
            if foundation.base_rate is None or Decimal(foundation.base_rate) <= 0:
                continue
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
            if component and unit:
                rows.append((component, foundation.title, unit, Decimal(foundation.base_rate), {"foundation": foundation}))

        for covering in RoofCovering.objects.filter(is_active=True):
            if covering.rate_per_m2 is not None and Decimal(covering.rate_per_m2) > 0:
                rows.append((
                    CostRate.Component.ROOF_COVERING,
                    covering.title,
                    CostRate.Unit.M2,
                    Decimal(covering.rate_per_m2),
                    {"roof_covering": covering},
                ))

        self.stdout.write(self.style.WARNING(
            "ВАЖНО: эта команда не проверяет экономическую корректность legacy-ставок. "
            "Если они получены регрессией/калибровкой, не применяйте их как офисный прайс."
        ))
        self.stdout.write(f"Кандидатов: {len(rows)}; дата начала: {rate_date}")

        for component, title, unit, rate, target in rows:
            target_label = next((str(v) for v in target.values() if v is not None), "Общая")
            self.stdout.write(f"  {component:24} {target_label:35} {rate:>12,.2f} ₽/{unit}")
            if apply:
                lookup = {
                    "component": component,
                    "valid_from": rate_date,
                    "material": target.get("material"),
                    "package": target.get("package"),
                    "foundation": target.get("foundation"),
                    "roof_covering": target.get("roof_covering"),
                }
                CostRate.objects.update_or_create(
                    **lookup,
                    defaults={
                        "title": title,
                        "unit": unit,
                        "rate": rate,
                        "source": CostRate.Source.IMPORT,
                        "note": "Перенесено из legacy V3. Требует ручной проверки.",
                        "is_active": True,
                    },
                )

        if apply:
            self.stdout.write(self.style.SUCCESS("Ставки перенесены. Проверьте их в Каталог → Сметные ставки."))
        else:
            self.stdout.write("Dry-run. Добавьте --apply только после ручной проверки.")
