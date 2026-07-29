from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from catalog.models import (
    BuildPackage,
    CostRate,
    FoundationType,
    Project,
    RoofCovering,
)
from catalog.pricing import PricingService
from catalog.rate_service import CostRateService

from .cost_engine import build_house_takeoff, estimate_pile_grid
from .models import (
    CalculatorFoundation,
    CalculatorMaterial,
    CalculatorRoofCovering,
    CalculatorSettings,
    HouseCostProfile,
)


DEFAULT_RANGE_PERCENT = Decimal("8")


class HouseCalculatorService:
    """V4: quantity × historical rate.

    Catalog ProjectOffer is never used to determine runtime price. It is only a
    commercial benchmark for offline comparison. Runtime money comes from CostRate;
    runtime quantities come from explicit input, verified ProjectTechnicalData, or
    clearly labelled quick-mode assumptions.
    """

    TECHNICAL_PAYLOAD_MAP = {
        "first_floor_area_m2": "first_floor_area_m2",
        "mansard_area_m2": "mansard_area_m2",
        "second_floor_area_m2": "second_floor_area_m2",
        "external_wall_length_m": "external_wall_length_m",
        "external_wall_height_m": "external_wall_height_m",
        "external_openings_area_m2": "external_openings_area_m2",
        "internal_wall_length_m": "internal_wall_length_m",
        "internal_wall_height_m": "internal_wall_height_m",
        "internal_openings_area_m2": "internal_openings_area_m2",
        "beams_volume_m3": "beams_volume_m3",
        "rafters_volume_m3": "rafters_volume_m3",
        "lathing_volume_m3": "lathing_volume_m3",
        "other_structural_lumber_volume_m3": "other_structural_lumber_volume_m3",
        "terrace_area": "terrace_area_m2",
        "roof_area": "roof_area_m2",
        "gable_area": "gable_area_m2",
        "roof_pitch_deg": "roof_pitch_deg",
        "roof_overhang_m": "roof_overhang_m",
        "roof_complexity_factor": "roof_complexity_factor",
    }

    def __init__(self):
        self.settings = (
            CalculatorSettings.objects.filter(is_active=True)
            .select_related("default_package")
            .order_by("id")
            .first()
        )
        self.pricing = PricingService()

    def get_config(self) -> dict:
        materials = (
            CalculatorMaterial.objects.filter(is_active=True, material__is_active=True)
            .select_related("material")
            .order_by("sort_order", "id")
        )
        foundations = (
            CalculatorFoundation.objects.filter(is_active=True, foundation__is_active=True)
            .select_related("foundation")
            .order_by("sort_order", "id")
        )
        roofs = (
            CalculatorRoofCovering.objects.filter(is_active=True, covering__is_active=True)
            .select_related("covering")
            .order_by("sort_order", "id")
        )
        packages = BuildPackage.objects.filter(is_active=True).order_by("sort_order", "id")
        default_package = self._default_package()

        return {
            "area": {
                "min": self.settings.min_area if self.settings else 20,
                "max": self.settings.max_area if self.settings else 600,
            },
            "floors": [
                {"value": "1", "label": "1 этаж"},
                {"value": "1.5", "label": "1,5 этажа / мансарда"},
                {"value": "2", "label": "2 этажа"},
            ],
            "materials": [
                {
                    "code": item.material.code,
                    "title": item.material.title,
                    "description": item.description,
                }
                for item in materials
            ],
            "packages": [
                {
                    "code": item.code,
                    "title": item.title,
                    "is_default": bool(default_package and item.id == default_package.id),
                }
                for item in packages
            ],
            "foundations": [
                {"code": item.foundation.code, "title": item.foundation.title}
                for item in foundations
            ],
            "roofs": [
                {"code": item.covering.code, "title": item.covering.title}
                for item in roofs
            ],
            "requires_dimensions": True,
            "engine": "exact_quantity_rate_v4",
            "rate_history": True,
            "pricing_basis": (
                "Цена считается как сумма точных/оценочных количеств, умноженных на действующие на дату сметные ставки. "
                "Коммерческие цены проектов каталога в runtime-формуле не используются."
            ),
            "package_label": f"Базовая комплектация «{default_package.title}»" if default_package else "Базовая комплектация",
            "disclaimer": (
                "Быстрый режим оценивает неизвестные количества геометрически. Для офисной точности заполните "
                "технический паспорт проекта или передайте точные объёмы/площади/количества."
            ),
        }

    def calculate(self, payload: dict) -> dict:
        payload, project, passport_fields = self._merge_project_technical(dict(payload))

        area = Decimal(payload["area"])
        floors = Decimal(str(payload["floors"]))
        width = Decimal(payload["width"])
        length = Decimal(payload["length"])
        self._validate_area(area)

        material_cfg = self._get_material(payload["material"])
        payload, material_fields, material_takeoff_verified = self._merge_project_material_takeoff(
            payload, project, material_cfg
        )
        passport_fields.update(material_fields)
        package = self._get_package(payload.get("package"))
        profile = self._profile(package)
        price_date = payload.get("price_date") or timezone.localdate()
        rates = CostRateService(as_of=price_date)

        takeoff = build_house_takeoff(
            area=area,
            width=width,
            length=length,
            floors=floors,
            profile=profile,
            material_cfg=material_cfg,
            bedrooms=payload.get("bedrooms"),
            first_floor_area_m2=self._decimal(payload.get("first_floor_area_m2")),
            mansard_area_m2=self._decimal(payload.get("mansard_area_m2")),
            second_floor_area_m2=self._decimal(payload.get("second_floor_area_m2")),
            external_wall_length_m=self._decimal(payload.get("external_wall_length_m")),
            external_wall_height_m=self._decimal(payload.get("external_wall_height_m")),
            external_openings_area_m2=self._decimal(payload.get("external_openings_area_m2")),
            external_wall_volume_m3=self._decimal(payload.get("external_wall_volume_m3")),
            internal_wall_length_m=self._decimal(payload.get("internal_wall_length_m")),
            internal_wall_height_m=self._decimal(payload.get("internal_wall_height_m")),
            internal_openings_area_m2=self._decimal(payload.get("internal_openings_area_m2")),
            internal_wall_volume_m3=self._decimal(payload.get("internal_wall_volume_m3")),
            beams_volume_m3=self._decimal(payload.get("beams_volume_m3")),
            rafters_volume_m3=self._decimal(payload.get("rafters_volume_m3")),
            lathing_volume_m3=self._decimal(payload.get("lathing_volume_m3")),
            other_structural_lumber_volume_m3=self._decimal(payload.get("other_structural_lumber_volume_m3")),
            structural_lumber_volume_m3=self._decimal(payload.get("structural_lumber_volume_m3")),
            terrace_area_m2=self._decimal(payload.get("terrace_area")),
            roof_area_m2=self._decimal(payload.get("roof_area")),
            roof_pitch_deg=self._decimal(payload.get("roof_pitch_deg")),
            roof_overhang_m=self._decimal(payload.get("roof_overhang_m")),
            gable_area_m2=self._decimal(payload.get("gable_area")),
        )

        house = self._calculate_house(
            floors=floors,
            material_cfg=material_cfg,
            package=package,
            takeoff=takeoff,
            rates=rates,
        )

        total = house["price"]
        breakdown = [
            {
                "code": "house",
                "title": f"Дом — {material_cfg.material.title}",
                "price": house["price"],
                "note": f"Комплектация «{package.title}» · количество × ставка",
            }
        ]
        component_results = {"house": house}

        if payload.get("foundation"):
            foundation_cfg = self._get_foundation(payload["foundation"])
            explicit_piles = payload.get("foundation_pile_count")
            if explicit_piles is None and project is not None:
                item = project.foundations.filter(foundation=foundation_cfg.foundation).first()
                if item and item.quantity is not None:
                    explicit_piles = int(Decimal(item.quantity))
                    passport_fields.add("foundation_pile_count")
            foundation = self._calculate_foundation(
                width=width,
                length=length,
                config=foundation_cfg,
                explicit_pile_count=explicit_piles,
                rates=rates,
            )
            total += foundation["price"]
            component_results["foundation"] = foundation
            breakdown.append(
                {
                    "code": foundation_cfg.foundation.code,
                    "title": foundation_cfg.foundation.title,
                    "price": foundation["price"],
                    "note": foundation["note"],
                }
            )

        if payload.get("roof"):
            roof_cfg = self._get_roof(payload["roof"])
            roof = self._calculate_roof(
                takeoff=takeoff,
                config=roof_cfg,
                complexity_factor=self._decimal(payload.get("roof_complexity_factor")) or Decimal("1"),
                rates=rates,
            )
            total += roof["price"]
            component_results["roof"] = roof
            breakdown.append(
                {
                    "code": roof_cfg.covering.code,
                    "title": f"Чистовая кровля — {roof_cfg.covering.title}",
                    "price": roof["price"],
                    "note": roof["note"],
                }
            )

        range_percent = self.settings.price_range_percent if self.settings else DEFAULT_RANGE_PERCENT
        delta = Decimal(total) * Decimal(range_percent) / Decimal("100")
        price_min = self.pricing.round_money(Decimal(total) - delta)
        price_max = self.pricing.round_money(Decimal(total) + delta)

        mode = self._calculation_mode(payload, project, passport_fields, material_takeoff_verified)
        confidence = "high" if mode == "verified_project" else ("medium" if mode == "explicit" else "preliminary")

        return {
            "total": total,
            "price_min": max(price_min, 0),
            "price_max": max(price_max, 0),
            "range_percent": float(range_percent),
            "price_date": price_date.isoformat() if isinstance(price_date, date) else str(price_date),
            "input": {
                "area": float(area),
                "width": float(width),
                "length": float(length),
                "footprint": float(takeoff.footprint_m2),
                "floors": float(floors),
                "material": material_cfg.material.code,
                "material_title": material_cfg.material.title,
                "package": package.code,
                "package_title": package.title,
                "project": project.external_id if project else None,
            },
            "breakdown": breakdown,
            "method": "exact_quantity_rate_v4",
            "calculation_mode": mode,
            "component_methods": {key: value["method"] for key, value in component_results.items()},
            "component_details": {key: value.get("details", {}) for key, value in component_results.items()},
            "confidence": confidence,
            "confidence_label": self._confidence_label(mode, project),
            "references": [],
            "assumptions": self._assumptions(payload, takeoff, passport_fields),
            "disclaimer": (
                "Расчёт не ищет похожий дом. Цена складывается из количества материалов/работ и ставок на выбранную дату. "
                "Поля, которых нет в техническом паспорте или запросе, быстрый режим оценивает геометрически."
            ),
        }

    def calculate_project_offer(self, offer, *, price_date: date | None = None) -> dict:
        """Контрольная смета существующего ProjectOffer для audit-команд."""
        project = offer.project
        payload = {
            "area": project.area,
            "width": project.width,
            "length": project.length,
            "floors": str(project.floors),
            "material": offer.material.code,
            "package": offer.build_package.code if offer.build_package else "",
            "project": project.external_id or project.slug,
            "price_date": price_date,
        }
        return self.calculate(payload)

    def _calculate_house(self, *, floors, material_cfg, package, takeoff, rates: CostRateService):
        lines = []

        def add_line(code, title, quantity, unit, resolved, *, component=None):
            quantity = Decimal(quantity)
            amount = quantity * Decimal(resolved.rate)
            lines.append(
                {
                    "code": code,
                    "title": title,
                    "quantity": float(quantity),
                    "unit": unit,
                    "rate": float(resolved.rate),
                    "base_amount": float(amount),
                    "rate_meta": resolved.as_dict(),
                    "component": component or resolved.component,
                }
            )
            return amount

        raw = Decimal("0")
        wall_rate = rates.require(
            CostRate.Component.WALL_MATERIAL,
            material=material_cfg.material,
            expected_unit=CostRate.Unit.M3,
        )
        raw += add_line(
            "external_walls", "Наружные стены", takeoff.external_wall_volume_m3, "м³", wall_rate
        )

        partition_rate = rates.require(
            CostRate.Component.PARTITION_MATERIAL,
            material=material_cfg.material,
            expected_unit=CostRate.Unit.M3,
        )
        raw += add_line(
            "partitions", "Внутренние перегородки", takeoff.internal_wall_volume_m3, "м³", partition_rate
        )

        processing_rate = rates.require(
            CostRate.Component.WALL_PROCESSING,
            material=material_cfg.material,
            expected_unit=CostRate.Unit.M3,
            allow_fallback=False,
        )
        raw += add_line(
            "wall_processing", "Обработка стенового комплекта",
            takeoff.total_wall_volume_m3, "м³ стен", processing_rate,
        )

        if takeoff.generic_structural_lumber_volume_m3 > 0:
            structural = rates.require(
                CostRate.Component.STRUCTURAL_LUMBER,
                package=package,
                expected_unit=CostRate.Unit.M3,
            )
            raw += add_line(
                "structural_lumber", "Конструкционный пиломатериал (общая кубатура)",
                takeoff.generic_structural_lumber_volume_m3, "м³", structural,
            )
        else:
            for code, title, qty, component in (
                ("beams", "Балки и лаги", takeoff.beams_volume_m3, CostRate.Component.BEAMS_LUMBER),
                ("rafters", "Стропила и ригели", takeoff.rafters_volume_m3, CostRate.Component.RAFTERS_LUMBER),
                ("lathing", "Обрешётка и контробрешётка", takeoff.lathing_volume_m3, CostRate.Component.LATHING_LUMBER),
                ("other_lumber", "Прочий конструкционный пиломатериал", takeoff.other_structural_lumber_volume_m3, CostRate.Component.OTHER_LUMBER),
            ):
                if qty <= 0:
                    continue
                rate = rates.require(component, package=package, expected_unit=CostRate.Unit.M3)
                raw += add_line(code, title, qty, "м³", rate)

        if takeoff.gable_area_m2 > 0:
            rate = rates.require(CostRate.Component.GABLE, package=package, expected_unit=CostRate.Unit.M2)
            raw += add_line("gables", "Фронтоны", takeoff.gable_area_m2, "м²", rate)

        if takeoff.roof_area_m2 > 0:
            rate = rates.require(CostRate.Component.TEMPORARY_ROOF, package=package, expected_unit=CostRate.Unit.M2)
            raw += add_line("temporary_roof", "Временная кровля / мембрана", takeoff.roof_area_m2, "м²", rate)

        if takeoff.total_wall_volume_m3 > 0:
            rate = rates.require(CostRate.Component.CONSUMABLES, package=package, expected_unit=CostRate.Unit.M3)
            raw += add_line(
                "consumables", "Джут, нагели, крепёж, обработка",
                takeoff.total_wall_volume_m3, "м³ стен", rate,
            )

        rate = rates.require(CostRate.Component.ASSEMBLY_FIRST, package=package, expected_unit=CostRate.Unit.M2)
        raw += add_line("assembly_first", "Сборка первого этажа", takeoff.first_floor_area_m2, "м²", rate)

        if takeoff.mansard_area_m2 > 0:
            rate = rates.require(CostRate.Component.ASSEMBLY_MANSARD, package=package, expected_unit=CostRate.Unit.M2)
            raw += add_line("assembly_mansard", "Сборка мансарды", takeoff.mansard_area_m2, "м²", rate)
        if takeoff.second_floor_area_m2 > 0:
            rate = rates.require(CostRate.Component.ASSEMBLY_SECOND, package=package, expected_unit=CostRate.Unit.M2)
            raw += add_line("assembly_second", "Сборка второго этажа", takeoff.second_floor_area_m2, "м²", rate)

        if takeoff.terrace_area_m2 > 0:
            rate = rates.require(CostRate.Component.TERRACE, package=package, expected_unit=CostRate.Unit.M2)
            raw += add_line("terrace", "Терраса", takeoff.terrace_area_m2, "м²", rate)

        for code, title, component in (
            ("delivery", "Доставка", CostRate.Component.DELIVERY),
            ("documentation", "Проектная документация и подготовка", CostRate.Component.DOCUMENTATION),
        ):
            rate = rates.require(component, package=package, expected_unit=CostRate.Unit.FIXED)
            raw += add_line(code, title, Decimal("1"), "компл.", rate)

        price = self.pricing.adjust_house_price(
            raw, material=material_cfg.material, package=package
        ) or 0
        return {
            "price": int(price),
            "method": "quantity_x_historical_rate",
            "details": {
                "base_before_indexation": float(raw),
                "pricing_multiplier": float(self.pricing.house_multiplier(material_cfg.material, package)),
                "footprint_m2": float(takeoff.footprint_m2),
                "first_floor_area_m2": float(takeoff.first_floor_area_m2),
                "mansard_area_m2": float(takeoff.mansard_area_m2),
                "second_floor_area_m2": float(takeoff.second_floor_area_m2),
                "external_wall_volume_m3": float(takeoff.external_wall_volume_m3),
                "internal_wall_volume_m3": float(takeoff.internal_wall_volume_m3),
                "beams_volume_m3": float(takeoff.beams_volume_m3),
                "rafters_volume_m3": float(takeoff.rafters_volume_m3),
                "lathing_volume_m3": float(takeoff.lathing_volume_m3),
                "other_structural_lumber_volume_m3": float(takeoff.other_structural_lumber_volume_m3),
                "roof_area_m2": float(takeoff.roof_area_m2),
                "gable_area_m2": float(takeoff.gable_area_m2),
                "bedrooms_used": takeoff.estimated_bedrooms,
                "lines": lines,
            },
        }

    def _calculate_foundation(self, *, width, length, config, explicit_pile_count, rates: CostRateService):
        foundation = config.foundation
        fixed_rate = rates.get(
            CostRate.Component.FOUNDATION_FIXED,
            foundation=foundation,
            expected_unit=CostRate.Unit.FIXED,
            allow_fallback=False,
        )
        fixed_amount = Decimal(fixed_rate.rate) if fixed_rate else Decimal("0")

        if foundation.pricing_method == FoundationType.PricingMethod.PER_UNIT:
            unit_rate = rates.require(
                CostRate.Component.FOUNDATION_UNIT,
                foundation=foundation,
                expected_unit=CostRate.Unit.UNIT,
                allow_fallback=False,
            )
            if explicit_pile_count is not None:
                count = int(explicit_pile_count)
                grid = None
                quantity_source = "explicit"
            else:
                grid = estimate_pile_grid(
                    width=width,
                    length=length,
                    spacing_m=Decimal(config.pile_spacing_m),
                )
                count = grid.total_count
                quantity_source = "estimated_grid"
            raw = Decimal(count) * Decimal(unit_rate.rate) + fixed_amount
            note = f"{count} {foundation.unit_name or 'ед.'} × {unit_rate.rate:g} ₽"
            details = {
                "quantity": count,
                "quantity_source": quantity_source,
                "unit_name": foundation.unit_name or "ед.",
                "rate": float(unit_rate.rate),
                "rate_meta": unit_rate.as_dict(),
                "fixed_rate_meta": fixed_rate.as_dict() if fixed_rate else None,
                "fixed_amount": float(fixed_amount),
                "pile_grid": (
                    {"rows_x": grid.rows_x, "rows_y": grid.rows_y, "base_count": grid.base_count}
                    if grid else None
                ),
            }
            method = "foundation_quantity_x_rate"
        elif foundation.pricing_method == FoundationType.PricingMethod.PER_FOOTPRINT:
            area_rate = rates.require(
                CostRate.Component.FOUNDATION_FOOTPRINT,
                foundation=foundation,
                expected_unit=CostRate.Unit.M2,
                allow_fallback=False,
            )
            footprint = width * length
            raw = footprint * Decimal(area_rate.rate) + fixed_amount
            note = f"{footprint:g} м² × {area_rate.rate:g} ₽"
            details = {
                "footprint_m2": float(footprint),
                "rate": float(area_rate.rate),
                "rate_meta": area_rate.as_dict(),
                "fixed_rate_meta": fixed_rate.as_dict() if fixed_rate else None,
                "fixed_amount": float(fixed_amount),
            }
            method = "foundation_footprint_x_rate"
        elif foundation.pricing_method == FoundationType.PricingMethod.FIXED:
            required_fixed = fixed_rate or rates.require(
                CostRate.Component.FOUNDATION_FIXED,
                foundation=foundation,
                expected_unit=CostRate.Unit.FIXED,
                allow_fallback=False,
            )
            raw = Decimal(required_fixed.rate)
            note = "Фиксированная ставка"
            details = {"rate": float(required_fixed.rate), "rate_meta": required_fixed.as_dict()}
            method = "foundation_fixed_rate"
        else:
            raise ValueError(
                f"Для фундамента «{foundation.title}» выберите формульный способ расчёта в Каталоге. "
                "Режим REFERENCE в V4 не используется."
            )

        price = self.pricing.adjust_foundation_price(raw, foundation=foundation) or 0
        minimum = self.pricing.adjust_foundation_price(
            max(config.minimum_price, foundation.minimum_price), foundation=foundation
        ) or 0
        return {
            "price": max(int(price), int(minimum)),
            "method": method,
            "note": note,
            "details": {**details, "base_before_indexation": float(raw)},
        }

    def _calculate_roof(self, *, takeoff, config, complexity_factor, rates: CostRateService):
        covering: RoofCovering = config.covering
        rate = rates.require(
            CostRate.Component.ROOF_COVERING,
            roof_covering=covering,
            expected_unit=CostRate.Unit.M2,
            allow_fallback=False,
        )
        raw = takeoff.roof_area_m2 * Decimal(rate.rate) * complexity_factor
        price = self.pricing.adjust_roof_price(raw, covering=covering) or 0
        minimum = self.pricing.adjust_roof_price(
            max(config.minimum_price, covering.minimum_price), covering=covering
        ) or 0
        return {
            "price": max(int(price), int(minimum)),
            "method": "roof_area_x_rate",
            "note": f"{takeoff.roof_area_m2:.1f} м² × {rate.rate:g} ₽ × K={complexity_factor:g}",
            "details": {
                "roof_area_m2": float(takeoff.roof_area_m2),
                "rate_per_m2": float(rate.rate),
                "rate_meta": rate.as_dict(),
                "complexity_factor": float(complexity_factor),
                "base_before_indexation": float(raw),
            },
        }

    def _merge_project_technical(self, payload: dict):
        ref = (payload.get("project") or "").strip()
        if not ref:
            return payload, None, set()
        project = (
            Project.objects.select_related("technical")
            .filter(Q(slug=ref) | Q(external_id__iexact=ref))
            .first()
        )
        if not project:
            raise ValueError(f"Проект «{ref}» не найден.")

        # Техпаспорт относится к конкретной геометрии. Не позволяем случайно
        # применить количества ДБ-01 к произвольному дому с другим размером.
        comparisons = (
            ("area", project.area, Decimal("0.5")),
            ("width", project.width, Decimal("0.15")),
            ("length", project.length, Decimal("0.15")),
            ("floors", project.floors, Decimal("0.1")),
        )
        for key, expected, tolerance in comparisons:
            if expected is None or payload.get(key) is None:
                continue
            actual = Decimal(str(payload[key]))
            if abs(actual - Decimal(expected)) > tolerance:
                raise ValueError(
                    f"Техпаспорт {project.external_id or project.slug} нельзя применить: "
                    f"параметр {key} отличается от проекта ({actual:g} вместо {Decimal(expected):g})."
                )

        used = set()
        try:
            technical = project.technical
        except ObjectDoesNotExist:
            technical = None
        if technical:
            for payload_key, technical_field in self.TECHNICAL_PAYLOAD_MAP.items():
                if payload.get(payload_key) is None:
                    value = getattr(technical, technical_field, None)
                    if value is not None:
                        payload[payload_key] = value
                        used.add(payload_key)
        if payload.get("bedrooms") is None and project.bedrooms:
            payload["bedrooms"] = project.bedrooms
            used.add("bedrooms")
        if payload.get("terrace_area") is None and project.terrace_area is not None:
            payload["terrace_area"] = project.terrace_area
            used.add("terrace_area")
        return payload, project, used

    @staticmethod
    def _merge_project_material_takeoff(payload: dict, project, material_cfg):
        if project is None:
            return payload, set(), False
        item = project.material_takeoffs.filter(material=material_cfg.material).first()
        if item is None:
            return payload, set(), False
        used = set()
        waste = Decimal("1")
        if not item.includes_waste:
            waste += Decimal(material_cfg.wall_waste_percent) / Decimal("100")
        if payload.get("external_wall_volume_m3") is None:
            payload["external_wall_volume_m3"] = Decimal(item.external_wall_volume_m3) * waste
            used.add("external_wall_volume_m3")
        if payload.get("internal_wall_volume_m3") is None:
            payload["internal_wall_volume_m3"] = Decimal(item.internal_wall_volume_m3) * waste
            used.add("internal_wall_volume_m3")
        return payload, used, bool(item.is_verified)

    def _default_package(self):
        if self.settings and self.settings.default_package_id:
            return self.settings.default_package
        return (
            BuildPackage.objects.filter(is_active=True, code="pod-usadku").first()
            or BuildPackage.objects.filter(is_active=True).order_by("sort_order", "id").first()
        )

    def _get_package(self, code):
        if code:
            package = BuildPackage.objects.filter(code=code, is_active=True).first()
            if not package:
                raise ValueError("Выбранная комплектация недоступна.")
            return package
        package = self._default_package()
        if not package:
            raise ValueError("В каталоге не настроена комплектация дома.")
        return package

    @staticmethod
    def _get_material(code):
        try:
            return CalculatorMaterial.objects.select_related("material").get(
                material__code=code, material__is_active=True, is_active=True
            )
        except CalculatorMaterial.DoesNotExist as exc:
            raise ValueError("Выбранный материал недоступен.") from exc

    @staticmethod
    def _get_foundation(code):
        try:
            return CalculatorFoundation.objects.select_related("foundation").get(
                foundation__code=code, foundation__is_active=True, is_active=True
            )
        except CalculatorFoundation.DoesNotExist as exc:
            raise ValueError("Выбранный фундамент недоступен.") from exc

    @staticmethod
    def _get_roof(code):
        try:
            return CalculatorRoofCovering.objects.select_related("covering").get(
                covering__code=code, covering__is_active=True, is_active=True
            )
        except CalculatorRoofCovering.DoesNotExist as exc:
            raise ValueError("Выбранное кровельное покрытие недоступно.") from exc

    @staticmethod
    def _profile(package, required=True):
        profile = HouseCostProfile.objects.filter(package=package, is_active=True).first()
        if required and not profile:
            raise ValueError(f"Для комплектации «{package.title}» не настроена геометрическая модель.")
        return profile

    def _validate_area(self, area):
        min_area = Decimal(self.settings.min_area if self.settings else 20)
        max_area = Decimal(self.settings.max_area if self.settings else 600)
        if area < min_area or area > max_area:
            raise ValueError(f"Площадь должна быть от {min_area:g} до {max_area:g} м².")

    @staticmethod
    def _decimal(value):
        return Decimal(value) if value is not None else None

    @staticmethod
    def _calculation_mode(payload, project, passport_fields, material_takeoff_verified=False):
        if project is not None:
            try:
                if project.technical.is_verified and material_takeoff_verified and passport_fields:
                    return "verified_project"
            except ObjectDoesNotExist:
                pass
        exact_keys = {
            "external_wall_volume_m3", "internal_wall_volume_m3",
            "beams_volume_m3", "rafters_volume_m3", "lathing_volume_m3",
            "structural_lumber_volume_m3", "roof_area", "foundation_pile_count",
        }
        if len([k for k in exact_keys if payload.get(k) is not None]) >= 3:
            return "explicit"
        return "quick"

    @staticmethod
    def _confidence_label(mode, project):
        if mode == "verified_project":
            return "Высокая — использован проверенный технический паспорт проекта"
        if mode == "explicit":
            return "Повышенная — ключевые количества переданы явно"
        return "Предварительная — часть количеств рассчитана по типовым геометрическим допущениям"

    @staticmethod
    def _assumptions(payload, takeoff, passport_fields):
        assumptions = []
        if passport_fields:
            assumptions.append(
                "Из технического паспорта проекта использованы: " + ", ".join(sorted(passport_fields)) + "."
            )
        checks = (
            ("external_wall_volume_m3", f"Объём наружных стен рассчитан: {takeoff.external_wall_volume_m3:.3f} м³."),
            ("internal_wall_volume_m3", f"Объём перегородок рассчитан: {takeoff.internal_wall_volume_m3:.3f} м³."),
            ("beams_volume_m3", f"Балки/лаги рассчитаны: {takeoff.beams_volume_m3:.3f} м³."),
            ("rafters_volume_m3", f"Стропила/ригели рассчитаны: {takeoff.rafters_volume_m3:.3f} м³."),
            ("lathing_volume_m3", f"Обрешётка рассчитана: {takeoff.lathing_volume_m3:.3f} м³."),
            ("roof_area", f"Площадь двускатной крыши рассчитана: {takeoff.roof_area_m2:.2f} м²."),
        )
        for key, text in checks:
            if payload.get(key) is None and key not in passport_fields and payload.get("structural_lumber_volume_m3") is None:
                assumptions.append(text)
        if not assumptions:
            assumptions.append("Ключевые количества переданы явно или взяты из технического паспорта.")
        return assumptions
