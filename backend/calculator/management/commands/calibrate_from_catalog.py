from __future__ import annotations

from datetime import date
from decimal import Decimal
from statistics import median

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from calculator.calibration import calibrate_house_from_catalog
from calculator.cost_engine import estimate_pile_grid, gable_roof_geometry
from calculator.models import (
    CalculatorFoundation,
    CalculatorMaterial,
    CalculatorRoofCovering,
    CalculatorSettings,
    HouseCostProfile,
)
from catalog.models import (
    BuildPackage,
    CostRate,
    FoundationType,
    ProjectFoundation,
    ProjectRoofCovering,
)

HOUSE_PACKAGE_CODE = "pod-usadku"


class Command(BaseCommand):
    help = (
        "Заполняет отсутствующие сметные ставки калькулятора (CostRate), выводя их "
        "статистически из реальных цен каталога — ProjectOffer.base_price для дома, "
        "base_price_override для фундамента и кровли. Это НЕ замена реальному "
        "офисному прайсу: строки помечаются source=calibrated и текстовой пометкой "
        "«требует проверки», чтобы их нельзя было спутать с вручную внесёнными "
        "ставками. Без --apply — только печатает, что будет записано."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--date", dest="rate_date", help="YYYY-MM-DD, по умолчанию сегодня")

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        rate_date = (
            date.fromisoformat(options["rate_date"])
            if options.get("rate_date")
            else timezone.localdate()
        )

        try:
            package = BuildPackage.objects.get(code=HOUSE_PACKAGE_CODE, is_active=True)
        except BuildPackage.DoesNotExist as exc:
            raise CommandError(f"Комплектация «{HOUSE_PACKAGE_CODE}» не найдена.") from exc

        profile = HouseCostProfile.objects.filter(package=package, is_active=True).first()
        if not profile:
            raise CommandError(f"Для «{package.title}» не настроена геометрическая модель (HouseCostProfile).")

        material_cfgs = list(
            CalculatorMaterial.objects.select_related("material").filter(
                is_active=True, material__is_active=True
            )
        )
        if not material_cfgs:
            raise CommandError("Нет активных материалов калькулятора.")

        note = (
            f"Откалибровано {rate_date.isoformat()} по реальным ценам действующих "
            "проектов каталога. Не является введённым вручную офисным прайсом — "
            "проверьте и при возможности замените на реальные закупочные/трудовые ставки."
        )

        rows: list[dict] = []

        # 1) Дом: материалы стен + общие статьи комплектации — регрессия по 129
        # реальным проектам (calculator/calibration.py, ранее отключённая для
        # получения "официального" прайса, но валидная для этой задачи).
        self.stdout.write(self.style.MIGRATE_HEADING(f'1) Комплектация "{package.title}"'))
        result = calibrate_house_from_catalog(package=package, profile=profile, material_cfgs=material_cfgs)
        self.stdout.write(
            f"   Проектов: {result['projects']}, наблюдений: {result['samples']}, "
            f"MAPE калибровки: {result['mape']:.2f}%, p90: {result['p90']:.2f}%"
        )

        for cfg in material_cfgs:
            code = cfg.material.code
            rate = Decimal(str(result["material_rates"].get(code, 0)))
            rows.append(dict(
                component=CostRate.Component.WALL_MATERIAL, material=cfg.material,
                unit=CostRate.Unit.M3, rate=rate,
                title=f"{cfg.material.title} — наружные стены", note=note,
            ))
            rows.append(dict(
                component=CostRate.Component.WALL_PROCESSING, material=cfg.material,
                unit=CostRate.Unit.M3, rate=Decimal("0"),
                title=f"{cfg.material.title} — обработка стенового комплекта",
                note=(
                    "Отдельно не выделяется: калибровка подгоняется под фактическую "
                    "итоговую цену проекта, поэтому стоимость обработки уже учтена "
                    "внутри калиброванной ставки материала наружных стен."
                ),
            ))

        package_lines = [
            (CostRate.Component.STRUCTURAL_LUMBER, "Конструкционный пиломатериал (балки/стропила/обрешётка)",
             CostRate.Unit.M3, result["structural_lumber_rate"]),
            (CostRate.Component.TEMPORARY_ROOF, "Временная кровля / мембрана",
             CostRate.Unit.M2, result["temporary_roof_rate"]),
            (CostRate.Component.ASSEMBLY_FIRST, "Сборка первого этажа",
             CostRate.Unit.M2, result["first_floor_assembly_rate"]),
            (CostRate.Component.ASSEMBLY_MANSARD, "Сборка мансарды",
             CostRate.Unit.M2, result["mansard_assembly_rate"]),
            (CostRate.Component.ASSEMBLY_SECOND, "Сборка второго этажа",
             CostRate.Unit.M2, result["second_floor_assembly_rate"]),
            (CostRate.Component.DELIVERY, "Доставка (документация отдельно не выделена — см. ниже)",
             CostRate.Unit.FIXED, result["fixed_cost"]),
        ]
        for component, title, unit, value in package_lines:
            rows.append(dict(
                component=component, package=package, unit=unit,
                rate=Decimal(str(value)), title=f"{package.title} — {title}", note=note,
            ))

        absorbed_note = (
            "Не выделяется отдельно калибровкой конечных цен — реальная стоимость "
            "(если есть) уже поглощена другими откалиброванными позициями комплектации."
        )
        for component, title, unit in (
            (CostRate.Component.GABLE, "Фронтоны", CostRate.Unit.M2),
            (CostRate.Component.CONSUMABLES, "Джут, нагели, крепёж, обработка", CostRate.Unit.M3),
            (CostRate.Component.TERRACE, "Терраса в комплектации", CostRate.Unit.M2),
            (CostRate.Component.DOCUMENTATION, "Проектная документация и подготовка", CostRate.Unit.FIXED),
        ):
            rows.append(dict(
                component=component, package=package, unit=unit, rate=Decimal("0"),
                title=f"{package.title} — {title}", note=absorbed_note,
            ))

        # 2) Фундаменты: своей ставки за сваю нет, зато на 134-135 проектах есть
        # реальная цена фундамента целиком (base_price_override). Число свай для
        # этих проектов не внесено — оцениваем его той же геометрией, что и сам
        # калькулятор, и делим реальную цену на неё.
        self.stdout.write(self.style.MIGRATE_HEADING("2) Фундаменты (реальная цена / геометрическая оценка свай)"))
        for cfg in CalculatorFoundation.objects.select_related("foundation").filter(is_active=True, foundation__is_active=True):
            foundation = cfg.foundation
            observed = []
            qs = (
                ProjectFoundation.objects.filter(
                    foundation=foundation,
                    base_price_override__isnull=False,
                    project__is_active=True,
                    project__width__isnull=False,
                    project__length__isnull=False,
                )
                .select_related("project")
            )
            for item in qs:
                grid = estimate_pile_grid(
                    width=Decimal(item.project.width),
                    length=Decimal(item.project.length),
                    spacing_m=Decimal(cfg.pile_spacing_m),
                )
                if grid.total_count > 0:
                    observed.append(float(item.base_price_override) / grid.total_count)
            if not observed:
                self.stdout.write(self.style.WARNING(f"   {foundation.code}: нет данных с ценой, пропущено"))
                continue
            rate = Decimal(str(round(median(observed), 2)))
            self.stdout.write(f"   {foundation.code:20} {len(observed):3} проектов -> {rate:>12,.0f} ₽/свая")
            rows.append(dict(
                component=CostRate.Component.FOUNDATION_UNIT, foundation=foundation,
                unit=CostRate.Unit.UNIT, rate=rate, title=f"{foundation.title} — свая",
                note=(
                    f"Откалибровано {rate_date.isoformat()} по {len(observed)} реальным ценам "
                    "проектов (base_price_override); количество свай для этих проектов не "
                    "внесено и оценено геометрически (тем же способом, что и в самом "
                    "калькуляторе). Проверьте и при возможности замените реальным прайсом."
                ),
            ))

        # 3) Кровля: аналогично — реальная цена есть, площадь ската не внесена в
        # технический паспорт (его нет вообще ни у одного проекта), оцениваем
        # геометрией по умолчаниям профиля комплектации.
        self.stdout.write(self.style.MIGRATE_HEADING("3) Кровельные покрытия (реальная цена / геометрическая оценка площади)"))
        for cfg in CalculatorRoofCovering.objects.select_related("covering").filter(is_active=True, covering__is_active=True):
            covering = cfg.covering
            observed = []
            qs = (
                ProjectRoofCovering.objects.filter(
                    covering=covering,
                    base_price_override__isnull=False,
                    project__is_active=True,
                    project__width__isnull=False,
                    project__length__isnull=False,
                )
                .select_related("project")
            )
            for item in qs:
                roof_area, _slope, _gables = gable_roof_geometry(
                    Decimal(item.project.width),
                    Decimal(item.project.length),
                    Decimal(profile.default_roof_pitch_deg),
                    Decimal(profile.default_roof_overhang_m),
                )
                if roof_area > 0:
                    observed.append(float(item.base_price_override) / float(roof_area))
            if not observed:
                self.stdout.write(self.style.WARNING(f"   {covering.code}: нет данных с ценой, пропущено"))
                continue
            rate = Decimal(str(round(median(observed), 2)))
            self.stdout.write(f"   {covering.code:20} {len(observed):3} проектов -> {rate:>12,.0f} ₽/м²")
            rows.append(dict(
                component=CostRate.Component.ROOF_COVERING, roof_covering=covering,
                unit=CostRate.Unit.M2, rate=rate, title=covering.title,
                note=(
                    f"Откалибровано {rate_date.isoformat()} по {len(observed)} реальным ценам "
                    "проектов (base_price_override); площадь ската оценена геометрически "
                    "(нет ни одного заполненного технического паспорта с реальной площадью). "
                    "Проверьте и при возможности замените реальным прайсом."
                ),
            ))

        self.stdout.write(self.style.MIGRATE_HEADING(f"Итого строк CostRate к записи: {len(rows)}"))
        for row in rows:
            target = row.get("material") or row.get("package") or row.get("foundation") or row.get("roof_covering")
            self.stdout.write(f"   {row['component']:22} {str(target)[:38]:38} {row['rate']:>14,.2f} ₽/{row['unit']}")

        if not apply_changes:
            self.stdout.write("\nDry-run. Запустите с --apply, чтобы записать эти ставки в Каталог → Сметные ставки.")
            return

        for row in rows:
            CostRate.objects.update_or_create(
                component=row["component"],
                valid_from=rate_date,
                material=row.get("material"),
                package=row.get("package"),
                foundation=row.get("foundation"),
                roof_covering=row.get("roof_covering"),
                defaults=dict(
                    title=row["title"],
                    unit=row["unit"],
                    rate=row["rate"],
                    source=CostRate.Source.CALIBRATED,
                    note=row["note"],
                    is_active=True,
                ),
            )

        changed = FoundationType.objects.filter(
            code__in=["screw-piles", "reinforced-piles"],
        ).update(pricing_method=FoundationType.PricingMethod.PER_UNIT)

        # Проекты с одинаковыми шириной/длиной/этажностью в каталоге реально
        # продаются с разбросом цены в 60-260% (разная планировка, которую
        # калькулятор по трём числам не видит) — честный диапазон результата
        # должен отражать это, а не косметические ±8%.
        settings_obj = CalculatorSettings.objects.filter(is_active=True).first()
        range_note = ""
        if settings_obj and settings_obj.price_range_percent < 20:
            settings_obj.price_range_percent = Decimal("20")
            settings_obj.save(update_fields=["price_range_percent"])
            range_note = " Диапазон результата (±%) увеличен до 20 — см. вывод команды выше про реальный разброс цен."

        self.stdout.write(self.style.SUCCESS(
            f"Записано {len(rows)} ставок CostRate (source=calibrated). "
            f"pricing_method переключён на PER_UNIT у {changed} фундаментов "
            "(было настроено на «по ценам похожих проектов», в V4 не поддерживается)."
            f"{range_note}"
        ))
