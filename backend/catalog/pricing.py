from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from .models import (
    CostRate,
    BuildPackage,
    ExtraOption,
    FoundationType,
    Material,
    PricingSettings,
    Project,
    ProjectExtraOption,
    ProjectFoundation,
    ProjectOffer,
    ProjectRoofCovering,
    RoofCovering,
)
from .rate_service import CostRateService


HUNDRED = Decimal("100")
ONE = Decimal("1")


class PricingService:
    """Единое ценовое ядро Catalog v2.

    Разные виды денег больше не смешиваются:
    - ProjectOffer: комплектация самого дома;
    - ProjectFoundation: фундамент;
    - ProjectRoofCovering: только чистовое кровельное покрытие;
    - ProjectExtraOption: остальные дополнительные работы.

    Импортированная цена проекта является override. Если override отсутствует и
    справочник настроен на формульный расчёт, стоимость выводится из количества,
    площади и базовой ставки.
    """

    def __init__(self):
        self.settings = (
            PricingSettings.objects.filter(is_active=True)
            .prefetch_related(
                "rules__material",
                "rules__build_package",
                "rules__foundation",
                "rules__roof_covering",
                "rules__extra_option",
            )
            .order_by("id")
            .first()
        )
        self._material_rules: dict[int, Decimal] = {}
        self._package_rules: dict[int, Decimal] = {}
        self._foundation_rules: dict[int, Decimal] = {}
        self._roof_rules: dict[int, Decimal] = {}
        self._extra_rules: dict[int, Decimal] = {}

        if self.settings:
            for rule in self.settings.rules.all():
                if not rule.is_active:
                    continue
                percent = Decimal(rule.percent_change)
                if rule.kind == rule.Kind.MATERIAL and rule.material_id:
                    self._material_rules[rule.material_id] = percent
                elif rule.kind == rule.Kind.PACKAGE and rule.build_package_id:
                    self._package_rules[rule.build_package_id] = percent
                elif rule.kind == rule.Kind.FOUNDATION and rule.foundation_id:
                    self._foundation_rules[rule.foundation_id] = percent
                elif rule.kind == rule.Kind.ROOF_COVERING and rule.roof_covering_id:
                    self._roof_rules[rule.roof_covering_id] = percent
                elif rule.kind == rule.Kind.EXTRA and rule.extra_option_id:
                    self._extra_rules[rule.extra_option_id] = percent

    @staticmethod
    def _percent_multiplier(percent) -> Decimal:
        return ONE + Decimal(str(percent)) / HUNDRED

    @classmethod
    def _safe_multiplier(cls, percent) -> Decimal:
        return max(Decimal("0.01"), cls._percent_multiplier(percent))

    def round_money(self, amount) -> int:
        amount = Decimal(amount)
        step = Decimal(self.settings.rounding_step if self.settings else 1000)
        if step <= 1:
            return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        return int((amount / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step)

    def house_multiplier(
        self, material: Material | None = None, package: BuildPackage | None = None
    ) -> Decimal:
        value = ONE
        if self.settings:
            value *= self._safe_multiplier(self.settings.house_percent)
        if material and material.pk in self._material_rules:
            value *= self._safe_multiplier(self._material_rules[material.pk])
        if package and package.pk in self._package_rules:
            value *= self._safe_multiplier(self._package_rules[package.pk])
        return value

    def foundation_multiplier(self, foundation: FoundationType | None = None) -> Decimal:
        value = ONE
        if self.settings:
            value *= self._safe_multiplier(self.settings.foundation_percent)
        if foundation and foundation.pk in self._foundation_rules:
            value *= self._safe_multiplier(self._foundation_rules[foundation.pk])
        return value

    def roof_multiplier(self, covering: RoofCovering | None = None) -> Decimal:
        value = ONE
        if self.settings:
            value *= self._safe_multiplier(self.settings.roof_covering_percent)
        if covering and covering.pk in self._roof_rules:
            value *= self._safe_multiplier(self._roof_rules[covering.pk])
        return value

    def extra_multiplier(self, option: ExtraOption | None = None) -> Decimal:
        value = ONE
        if self.settings:
            value *= self._safe_multiplier(self.settings.extra_percent)
        if option and option.pk in self._extra_rules:
            value *= self._safe_multiplier(self._extra_rules[option.pk])
        return value

    def _apply(self, base_price, multiplier: Decimal, *, is_fixed=False, round_result=True):
        if base_price is None:
            return None
        amount = Decimal(base_price)
        if not is_fixed:
            amount *= multiplier
        return self.round_money(amount) if round_result else amount

    def adjust_house_price(
        self,
        base_price,
        *,
        project: Project | None = None,
        material: Material | None = None,
        package: BuildPackage | None = None,
        is_fixed: bool = False,
        round_result: bool = True,
    ):
        fixed = is_fixed or bool(project and project.price_indexing_disabled)
        return self._apply(
            base_price,
            self.house_multiplier(material, package),
            is_fixed=fixed,
            round_result=round_result,
        )

    def adjust_foundation_price(
        self,
        base_price,
        *,
        project: Project | None = None,
        foundation: FoundationType | None = None,
        is_fixed: bool = False,
        round_result: bool = True,
    ):
        fixed = is_fixed or bool(project and project.foundation_price_indexing_disabled)
        return self._apply(
            base_price,
            self.foundation_multiplier(foundation),
            is_fixed=fixed,
            round_result=round_result,
        )

    def adjust_roof_price(
        self,
        base_price,
        *,
        project: Project | None = None,
        covering: RoofCovering | None = None,
        is_fixed: bool = False,
        round_result: bool = True,
    ):
        fixed = is_fixed or bool(project and project.roof_price_indexing_disabled)
        return self._apply(
            base_price,
            self.roof_multiplier(covering),
            is_fixed=fixed,
            round_result=round_result,
        )

    def adjust_extra_price(
        self,
        base_price,
        *,
        project: Project | None = None,
        option: ExtraOption | None = None,
        is_fixed: bool = False,
        round_result: bool = True,
    ):
        fixed = is_fixed or bool(project and project.extra_price_indexing_disabled)
        return self._apply(
            base_price,
            self.extra_multiplier(option),
            is_fixed=fixed,
            round_result=round_result,
        )

    def get_offer_price(self, offer: ProjectOffer) -> int | None:
        return self.adjust_house_price(
            offer.base_price,
            project=offer.project,
            material=offer.material,
            package=offer.build_package,
            is_fixed=offer.is_price_fixed,
        )

    def get_project_price_from(self, project: Project) -> int | None:
        offers = [offer for offer in project.offers.all() if offer.base_price is not None]
        prices = [self.get_offer_price(offer) for offer in offers]
        prices = [price for price in prices if price is not None]
        if prices:
            return min(prices)
        # Только legacy fallback для ещё не нормализованных бань.
        return self.adjust_house_price(project.price_from, project=project)

    def _foundation_formula_base(self, item: ProjectFoundation) -> Decimal | None:
        if item.base_price_override is not None:
            return Decimal(item.base_price_override)

        foundation = item.foundation
        rates = CostRateService()
        if foundation.pricing_method == FoundationType.PricingMethod.PER_UNIT:
            if item.quantity is None:
                return None
            resolved = rates.get(
                CostRate.Component.FOUNDATION_UNIT,
                foundation=foundation,
                expected_unit=CostRate.Unit.UNIT,
                allow_fallback=False,
            )
            if resolved is None:
                return None
            fixed = rates.get(
                CostRate.Component.FOUNDATION_FIXED,
                foundation=foundation,
                expected_unit=CostRate.Unit.FIXED,
                allow_fallback=False,
            )
            return Decimal(item.quantity) * resolved.rate + (fixed.rate if fixed else Decimal("0"))
        if foundation.pricing_method == FoundationType.PricingMethod.PER_FOOTPRINT:
            footprint = item.project.footprint_area
            if footprint is None:
                return None
            resolved = rates.get(
                CostRate.Component.FOUNDATION_FOOTPRINT,
                foundation=foundation,
                expected_unit=CostRate.Unit.M2,
                allow_fallback=False,
            )
            if resolved is None:
                return None
            fixed = rates.get(
                CostRate.Component.FOUNDATION_FIXED,
                foundation=foundation,
                expected_unit=CostRate.Unit.FIXED,
                allow_fallback=False,
            )
            return Decimal(footprint) * resolved.rate + (fixed.rate if fixed else Decimal("0"))
        if foundation.pricing_method == FoundationType.PricingMethod.FIXED:
            resolved = rates.get(
                CostRate.Component.FOUNDATION_FIXED,
                foundation=foundation,
                expected_unit=CostRate.Unit.FIXED,
                allow_fallback=False,
            )
            return resolved.rate if resolved else None
        return None

    def get_foundation_price(self, item: ProjectFoundation) -> int | None:
        base = self._foundation_formula_base(item)
        if base is None:
            return None
        result = self.adjust_foundation_price(
            base,
            project=item.project,
            foundation=item.foundation,
            is_fixed=item.is_price_fixed,
        )
        if result is None:
            return None
        minimum = self.adjust_foundation_price(
            item.foundation.minimum_price,
            project=item.project,
            foundation=item.foundation,
            is_fixed=item.is_price_fixed,
        ) or 0
        return max(int(result), int(minimum))

    @staticmethod
    def roof_area_for_item(item: ProjectRoofCovering) -> Decimal | None:
        if item.roof_area_override_m2 is not None:
            return Decimal(item.roof_area_override_m2)
        try:
            technical = item.project.technical
        except Exception:
            return None
        if technical.roof_area_m2 is None:
            return None
        return Decimal(technical.roof_area_m2)

    def _roof_formula_base(self, item: ProjectRoofCovering) -> Decimal | None:
        if item.base_price_override is not None:
            return Decimal(item.base_price_override)
        area = self.roof_area_for_item(item)
        if area is None:
            return None
        resolved = CostRateService().get(
            CostRate.Component.ROOF_COVERING,
            roof_covering=item.covering,
            expected_unit=CostRate.Unit.M2,
            allow_fallback=False,
        )
        if resolved is None:
            return None
        complexity = Decimal("1")
        try:
            complexity = Decimal(item.project.technical.roof_complexity_factor)
        except Exception:
            pass
        return area * resolved.rate * complexity

    def get_roof_covering_price(self, item: ProjectRoofCovering) -> int | None:
        base = self._roof_formula_base(item)
        if base is None:
            return None
        result = self.adjust_roof_price(
            base,
            project=item.project,
            covering=item.covering,
            is_fixed=item.is_price_fixed,
        )
        if result is None:
            return None
        minimum = self.adjust_roof_price(
            item.covering.minimum_price,
            project=item.project,
            covering=item.covering,
            is_fixed=item.is_price_fixed,
        ) or 0
        return max(int(result), int(minimum))

    def _extra_formula_base(self, item: ProjectExtraOption) -> Decimal | None:
        if item.base_price_override is not None:
            return Decimal(item.base_price_override)
        option = item.option
        if option.base_rate is None:
            return None
        rate = Decimal(option.base_rate)
        if option.pricing_method == ExtraOption.PricingMethod.PER_UNIT:
            return Decimal(item.quantity) * rate if item.quantity is not None else None
        if option.pricing_method == ExtraOption.PricingMethod.PER_M2:
            return Decimal(item.quantity) * rate if item.quantity is not None else None
        if option.pricing_method == ExtraOption.PricingMethod.FIXED:
            return rate
        return None

    def get_extra_price(self, item: ProjectExtraOption) -> int | None:
        base = self._extra_formula_base(item)
        if base is None:
            return None
        result = self.adjust_extra_price(
            base,
            project=item.project,
            option=item.option,
            is_fixed=item.is_price_fixed,
        )
        if result is None:
            return None
        minimum = self.adjust_extra_price(
            item.option.minimum_price,
            project=item.project,
            option=item.option,
            is_fixed=item.is_price_fixed,
        ) or 0
        return max(int(result), int(minimum))
