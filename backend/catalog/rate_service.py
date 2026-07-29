from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from .models import BuildPackage, CostRate, FoundationType, Material, RoofCovering


@dataclass(frozen=True)
class ResolvedCostRate:
    component: str
    rate: Decimal
    unit: str
    title: str
    source: str
    valid_from: date
    valid_to: date | None
    record_id: int
    fallback_component: str | None = None

    def as_dict(self) -> dict:
        return {
            "component": self.component,
            "rate": float(self.rate),
            "unit": self.unit,
            "title": self.title,
            "source": self.source,
            "valid_from": self.valid_from.isoformat(),
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "record_id": self.record_id,
            "fallback_component": self.fallback_component,
        }


class CostRateService:
    """Получает действующую на дату ставку с максимально конкретной целью.

    Приоритет внутри одного компонента:
      material/package/foundation/roof_covering exact > NULL (общая ставка).

    Разрешены только два осознанных fallback:
      - partition_material -> wall_material того же материала;
      - beams/rafters/lathing/other_lumber -> structural_lumber.
    Они возвращаются в метаданных и никогда не скрываются от результата сметы.
    """

    STRUCTURAL_FALLBACKS = {
        CostRate.Component.BEAMS_LUMBER,
        CostRate.Component.RAFTERS_LUMBER,
        CostRate.Component.LATHING_LUMBER,
        CostRate.Component.OTHER_LUMBER,
    }

    def __init__(self, as_of: date | None = None):
        self.as_of = as_of or timezone.localdate()

    def get(
        self,
        component: str,
        *,
        material: Material | None = None,
        package: BuildPackage | None = None,
        foundation: FoundationType | None = None,
        roof_covering: RoofCovering | None = None,
        expected_unit: str | None = None,
        allow_fallback: bool = True,
    ) -> ResolvedCostRate | None:
        resolved = self._find(
            component,
            material=material,
            package=package,
            foundation=foundation,
            roof_covering=roof_covering,
        )
        fallback_component = None

        if resolved is None and allow_fallback:
            if component == CostRate.Component.PARTITION_MATERIAL:
                fallback_component = CostRate.Component.WALL_MATERIAL
            elif component in self.STRUCTURAL_FALLBACKS:
                fallback_component = CostRate.Component.STRUCTURAL_LUMBER

            if fallback_component:
                resolved = self._find(
                    fallback_component,
                    material=material,
                    package=package,
                    foundation=foundation,
                    roof_covering=roof_covering,
                )

        if resolved is None:
            return None
        if expected_unit and resolved.unit != expected_unit:
            raise ValueError(
                f"Ставка «{resolved.title}» имеет единицу {resolved.get_unit_display()}, "
                f"а расчёт ожидает {dict(CostRate.Unit.choices).get(expected_unit, expected_unit)}."
            )
        return ResolvedCostRate(
            component=component,
            rate=Decimal(resolved.rate),
            unit=resolved.unit,
            title=resolved.title,
            source=resolved.source,
            valid_from=resolved.valid_from,
            valid_to=resolved.valid_to,
            record_id=resolved.pk,
            fallback_component=fallback_component,
        )

    def require(self, component: str, **kwargs) -> ResolvedCostRate:
        result = self.get(component, **kwargs)
        if result is None:
            label = dict(CostRate.Component.choices).get(component, component)
            target = (
                kwargs.get("material")
                or kwargs.get("package")
                or kwargs.get("foundation")
                or kwargs.get("roof_covering")
            )
            suffix = f" для «{target}»" if target else ""
            raise ValueError(
                f"Не настроена сметная ставка «{label}»{suffix} на {self.as_of:%d.%m.%Y}. "
                "Добавьте её в Каталог → Сметные ставки."
            )
        return result

    def _find(
        self,
        component: str,
        *,
        material=None,
        package=None,
        foundation=None,
        roof_covering=None,
    ) -> CostRate | None:
        qs = CostRate.objects.filter(
            component=component,
            is_active=True,
            valid_from__lte=self.as_of,
        ).filter(Q(valid_to__isnull=True) | Q(valid_to__gte=self.as_of))

        targets = {
            "material": material,
            "package": package,
            "foundation": foundation,
            "roof_covering": roof_covering,
        }
        # Если конкретная цель передана — допускаем exact или общую строку.
        # Если не передана — специфические строки исключаем.
        for field, value in targets.items():
            if value is None:
                qs = qs.filter(**{f"{field}__isnull": True})
            else:
                qs = qs.filter(Q(**{field: value}) | Q(**{f"{field}__isnull": True}))

        candidates = list(qs.select_related("material", "package", "foundation", "roof_covering"))
        if not candidates:
            return None

        def specificity(row: CostRate) -> tuple[int, date, int]:
            score = 0
            for field, value in targets.items():
                row_id = getattr(row, f"{field}_id")
                if value is not None and row_id == value.pk:
                    score += 1
            # Чем конкретнее и свежее ставка, тем выше приоритет.
            return score, row.valid_from, row.pk

        return max(candidates, key=specificity)
