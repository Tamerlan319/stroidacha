from collections import defaultdict
from decimal import Decimal
from statistics import median

from django.core.management.base import BaseCommand

from catalog.models import (
    BuildPackage,
    ConstructionOption,
    Project,
    ProjectFoundation,
    ProjectExtraOption,
    ProjectIllustratedOption,
    ProjectOffer,
    ProjectOptionPrice,
    ProjectPackage,
    ProjectPackageOverride,
    ProjectRoofCovering,
)


class Command(BaseCommand):
    help = "Проверяет перенос Catalog v2 и отмечает подозрительные цены без изменения БД."

    def handle(self, *args, **options):
        houses = Project.objects.filter(construction_type=Project.ConstructionType.TIMBER)
        self.stdout.write(self.style.MIGRATE_HEADING("Catalog v2 audit"))
        self.stdout.write(f"Проектов из бруса: {houses.count()}")
        self.stdout.write(f"Глобальных комплектаций: {BuildPackage.objects.count()}")
        self.stdout.write(f"ProjectOffer: {ProjectOffer.objects.count()}")
        self.stdout.write(f"Фундаментов проектов v2: {ProjectFoundation.objects.count()}")
        self.stdout.write(f"Чистовых кровель проектов v2: {ProjectRoofCovering.objects.count()}")
        self.stdout.write(f"Прочих доп. работ проектов v2: {ProjectExtraOption.objects.count()}")
        self.stdout.write(f"Редких package override: {ProjectPackageOverride.objects.count()}")

        problems = 0
        no_offers = houses.filter(offers__isnull=True).distinct()
        if no_offers.exists():
            problems += no_offers.count()
            self.stdout.write(self.style.WARNING(f"Домов без ProjectOffer: {no_offers.count()}"))
            for item in no_offers[:20]:
                self.stdout.write(f"  - {item.external_id or item.title}")
        else:
            self.stdout.write(self.style.SUCCESS("Все дома имеют ProjectOffer."))

        no_package = ProjectOffer.objects.filter(build_package__isnull=True)
        if no_package.exists():
            problems += no_package.count()
            self.stdout.write(self.style.WARNING(f"Offer без BuildPackage: {no_package.count()}"))
        else:
            self.stdout.write(self.style.SUCCESS("Все ProjectOffer привязаны к глобальной комплектации."))

        no_primary = houses.exclude(images__is_primary=True).distinct()
        if no_primary.exists():
            problems += no_primary.count()
            self.stdout.write(self.style.WARNING(f"Домов без primary ProjectImage: {no_primary.count()}"))
        else:
            self.stdout.write(self.style.SUCCESS("У всех домов есть главное изображение в ProjectImage."))

        # Сверяем количество legacy доп. цен и v2. Это не обязано быть 1:1, если
        # illustrated_options создавали новые позиции, но v2 не должен быть меньше.
        legacy_option_count = ProjectOptionPrice.objects.count()
        v2_option_count = (
            ProjectFoundation.objects.count()
            + ProjectRoofCovering.objects.count()
            + ProjectExtraOption.objects.count()
        )
        self.stdout.write(
            f"Legacy ProjectOptionPrice: {legacy_option_count}; все дополнительные позиции v2: {v2_option_count}"
        )
        if v2_option_count < legacy_option_count:
            problems += 1
            self.stdout.write(self.style.ERROR("v2 содержит меньше фундамент/кровля записей, чем legacy. Проверь миграцию."))

        self.stdout.write(
            f"Legacy ProjectPackage: {ProjectPackage.objects.count()}; глобальных BuildPackage: {BuildPackage.objects.count()}"
        )
        self.stdout.write(
            f"Legacy illustrated options: {ProjectIllustratedOption.objects.count()} (новый API их уже не использует)"
        )
        self.stdout.write(
            f"Legacy ConstructionOption: {ConstructionOption.objects.count()} (новый API их уже не использует)"
        )

        problems += self._audit_outliers(ProjectFoundation.objects.select_related("project", "foundation"), "foundation")
        problems += self._audit_outliers(ProjectRoofCovering.objects.select_related("project", "covering"), "roof")

        if problems:
            self.stdout.write(self.style.WARNING(f"Audit завершён: найдено предупреждений/аномалий: {problems}"))
            self.stdout.write("Legacy-таблицы пока НЕ удаляй. Сначала проверь перечисленные записи.")
        else:
            self.stdout.write(self.style.SUCCESS("Audit завершён без проблем. Catalog v2 готов к cleanup legacy-таблиц."))

    def _audit_outliers(self, queryset, kind):
        grouped = defaultdict(list)
        for item in queryset:
            project = item.project
            if not project.footprint_area or item.base_price_override is None:
                continue
            key = item.foundation_id if kind == "foundation" else item.covering_id
            grouped[key].append((item, Decimal(item.base_price_override) / project.footprint_area))

        warnings = 0
        for _, rows in grouped.items():
            if len(rows) < 4:
                continue
            med = Decimal(str(median(float(rate) for _, rate in rows)))
            if med <= 0:
                continue
            for item, rate in rows:
                ratio = rate / med
                if ratio < Decimal("0.35") or ratio > Decimal("2.8"):
                    warnings += 1
                    title = item.foundation.title if kind == "foundation" else item.covering.title
                    self.stdout.write(
                        self.style.WARNING(
                            f"Подозрительная цена: {item.project.external_id or item.project.title} / {title} / "
                            f"{item.base_price_override:,} ₽ (ставка к медиане ×{ratio:.2f})"
                        )
                    )
        return warnings
