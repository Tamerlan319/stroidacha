from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

from catalog.models import Material


ZERO = Decimal("0")
ONE = Decimal("1")


@dataclass(frozen=True)
class HouseTakeoff:
    footprint_m2: Decimal
    first_floor_area_m2: Decimal
    mansard_area_m2: Decimal
    second_floor_area_m2: Decimal

    external_wall_length_m: Decimal
    external_wall_height_m: Decimal
    external_wall_area_gross_m2: Decimal
    external_openings_area_m2: Decimal
    external_wall_area_net_m2: Decimal
    external_wall_volume_m3: Decimal

    internal_wall_length_m: Decimal
    internal_wall_height_m: Decimal
    internal_openings_area_m2: Decimal
    internal_wall_area_net_m2: Decimal
    internal_wall_volume_m3: Decimal

    roof_area_m2: Decimal
    roof_slope_length_m: Decimal
    gable_area_m2: Decimal

    beams_volume_m3: Decimal
    rafters_volume_m3: Decimal
    lathing_volume_m3: Decimal
    other_structural_lumber_volume_m3: Decimal
    generic_structural_lumber_volume_m3: Decimal

    terrace_area_m2: Decimal
    estimated_bedrooms: int

    @property
    def upper_floor_area_m2(self) -> Decimal:
        return self.mansard_area_m2 + self.second_floor_area_m2

    @property
    def total_wall_volume_m3(self) -> Decimal:
        return self.external_wall_volume_m3 + self.internal_wall_volume_m3

    @property
    def structural_lumber_volume_m3(self) -> Decimal:
        return (
            self.beams_volume_m3
            + self.rafters_volume_m3
            + self.lathing_volume_m3
            + self.other_structural_lumber_volume_m3
            + self.generic_structural_lumber_volume_m3
        )


@dataclass(frozen=True)
class PileGrid:
    rows_x: int
    rows_y: int
    base_count: int
    additional_count: int

    @property
    def total_count(self) -> int:
        return self.base_count + self.additional_count


def _ceil_count(length: Decimal, spacing: Decimal) -> int:
    if spacing <= 0:
        raise ValueError("Шаг конструкции должен быть больше нуля.")
    return max(2, int((length / spacing).to_integral_value(rounding=ROUND_CEILING)) + 1)


def gable_roof_geometry(
    width: Decimal,
    length: Decimal,
    pitch_deg: Decimal,
    overhang_m: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """(площадь двух скатов, длина ската, площадь двух фронтонов)."""
    span = min(width, length)
    ridge = max(width, length)
    angle = math.radians(float(pitch_deg))
    cosine = Decimal(str(math.cos(angle)))
    tangent = Decimal(str(math.tan(angle)))
    if cosine <= Decimal("0.01"):
        raise ValueError("Некорректный угол кровли.")

    half_run_with_overhang = span / Decimal("2") + overhang_m
    slope = half_run_with_overhang / cosine
    roof_length = ridge + overhang_m * Decimal("2")
    roof_area = slope * roof_length * Decimal("2")

    rise = (span / Decimal("2")) * tangent
    gables = span * rise  # два треугольника
    return roof_area, slope, gables


def estimate_bedrooms(area: Decimal) -> int:
    return max(1, min(12, int((area / Decimal("28")).to_integral_value(rounding=ROUND_CEILING))))


def material_wall_thickness_m(material_cfg) -> Decimal:
    if material_cfg.wall_thickness_mm:
        return Decimal(material_cfg.wall_thickness_mm) / Decimal("1000")
    material: Material = material_cfg.material
    candidates = [v for v in (material.section_width_mm, material.section_height_mm) if v]
    if not candidates:
        raise ValueError(f"Для материала «{material.title}» не задана толщина стены.")
    return Decimal(max(candidates)) / Decimal("1000")


def material_partition_thickness_m(material_cfg) -> Decimal:
    if material_cfg.partition_thickness_mm:
        return Decimal(material_cfg.partition_thickness_mm) / Decimal("1000")
    return Decimal("0.100") if material_cfg.material.kind == Material.Kind.REGULAR else Decimal("0.095")


def _floor_areas(
    *, area: Decimal, footprint: Decimal, floors: Decimal,
    first_floor_area_m2: Decimal | None,
    mansard_area_m2: Decimal | None,
    second_floor_area_m2: Decimal | None,
) -> tuple[Decimal, Decimal, Decimal]:
    if first_floor_area_m2 is not None:
        first = first_floor_area_m2
    else:
        first = min(area, footprint)

    if floors == Decimal("1"):
        return first, ZERO, ZERO

    remaining = max(ZERO, area - first)
    if floors == Decimal("1.5"):
        mansard = mansard_area_m2 if mansard_area_m2 is not None else remaining
        return first, mansard, ZERO
    if floors == Decimal("2"):
        second = second_floor_area_m2 if second_floor_area_m2 is not None else remaining
        return first, ZERO, second
    raise ValueError("Неподдерживаемая этажность.")


def build_house_takeoff(
    *,
    area: Decimal,
    width: Decimal,
    length: Decimal,
    floors: Decimal,
    profile,
    material_cfg,
    bedrooms: int | None = None,
    first_floor_area_m2: Decimal | None = None,
    mansard_area_m2: Decimal | None = None,
    second_floor_area_m2: Decimal | None = None,
    external_wall_length_m: Decimal | None = None,
    external_wall_height_m: Decimal | None = None,
    external_openings_area_m2: Decimal | None = None,
    external_wall_volume_m3: Decimal | None = None,
    internal_wall_length_m: Decimal | None = None,
    internal_wall_height_m: Decimal | None = None,
    internal_openings_area_m2: Decimal | None = None,
    internal_wall_volume_m3: Decimal | None = None,
    beams_volume_m3: Decimal | None = None,
    rafters_volume_m3: Decimal | None = None,
    lathing_volume_m3: Decimal | None = None,
    other_structural_lumber_volume_m3: Decimal | None = None,
    structural_lumber_volume_m3: Decimal | None = None,  # legacy aggregate override
    terrace_area_m2: Decimal | None = None,
    roof_area_m2: Decimal | None = None,
    roof_pitch_deg: Decimal | None = None,
    roof_overhang_m: Decimal | None = None,
    gable_area_m2: Decimal | None = None,
) -> HouseTakeoff:
    footprint = width * length
    first_floor_area, mansard_area, second_floor_area = _floor_areas(
        area=area,
        footprint=footprint,
        floors=floors,
        first_floor_area_m2=first_floor_area_m2,
        mansard_area_m2=mansard_area_m2,
        second_floor_area_m2=second_floor_area_m2,
    )

    if external_wall_height_m is not None:
        wall_height = external_wall_height_m
    elif floors == Decimal("1"):
        wall_height = Decimal(profile.first_floor_height_m)
    elif floors == Decimal("1.5"):
        wall_height = Decimal(profile.first_floor_height_m) + Decimal(profile.mansard_knee_wall_height_m)
    elif floors == Decimal("2"):
        wall_height = Decimal(profile.first_floor_height_m) + Decimal(profile.second_floor_height_m)
    else:
        raise ValueError("Неподдерживаемая этажность.")

    wall_length = external_wall_length_m if external_wall_length_m is not None else Decimal("2") * (width + length)
    gross_external_area = wall_length * wall_height
    if external_openings_area_m2 is None:
        external_openings = gross_external_area * Decimal(profile.external_openings_ratio)
    else:
        external_openings = min(external_openings_area_m2, gross_external_area * Decimal("0.80"))
    net_external_area = max(ZERO, gross_external_area - external_openings)

    bedroom_count = bedrooms or estimate_bedrooms(area)
    if internal_wall_length_m is None:
        internal_length = (
            area * Decimal(profile.internal_wall_length_per_m2)
            + Decimal(bedroom_count) * Decimal(profile.internal_wall_length_per_bedroom_m)
        )
    else:
        internal_length = internal_wall_length_m
    partition_height = internal_wall_height_m if internal_wall_height_m is not None else Decimal(profile.partition_height_m)
    internal_gross_area = internal_length * partition_height
    if internal_openings_area_m2 is None:
        internal_openings = internal_gross_area * Decimal(profile.internal_openings_ratio)
    else:
        internal_openings = min(internal_openings_area_m2, internal_gross_area * Decimal("0.80"))
    internal_net_area = max(ZERO, internal_gross_area - internal_openings)

    waste_multiplier = ONE + Decimal(material_cfg.wall_waste_percent) / Decimal("100")
    calc_external_volume = net_external_area * material_wall_thickness_m(material_cfg) * waste_multiplier
    calc_partition_volume = internal_net_area * material_partition_thickness_m(material_cfg) * waste_multiplier
    external_volume = external_wall_volume_m3 if external_wall_volume_m3 is not None else calc_external_volume
    partition_volume = internal_wall_volume_m3 if internal_wall_volume_m3 is not None else calc_partition_volume

    pitch = roof_pitch_deg if roof_pitch_deg is not None else Decimal(profile.default_roof_pitch_deg)
    overhang = roof_overhang_m if roof_overhang_m is not None else Decimal(profile.default_roof_overhang_m)
    geom_roof_area, slope_length, geom_gables = gable_roof_geometry(width, length, pitch, overhang)
    roof_area = roof_area_m2 if roof_area_m2 is not None else geom_roof_area
    gable_area = gable_area_m2 if gable_area_m2 is not None else geom_gables

    short_span = min(width, length)
    long_run = max(width, length)
    if floors == Decimal("1"):
        joist_systems = Decimal(profile.joist_systems_one_floor)
    elif floors == Decimal("1.5"):
        joist_systems = Decimal(profile.joist_systems_mansard)
    else:
        joist_systems = Decimal(profile.joist_systems_two_floor)

    joist_count = _ceil_count(long_run, Decimal(profile.joist_spacing_m))
    joist_cross = Decimal(profile.joist_section_width_mm) * Decimal(profile.joist_section_height_mm) / Decimal("1000000")
    calc_beams = Decimal(joist_count) * short_span * joist_cross * joist_systems

    rafter_pair_count = _ceil_count(long_run + overhang * Decimal("2"), Decimal(profile.rafter_spacing_m))
    rafter_cross = Decimal(profile.rafter_section_width_mm) * Decimal(profile.rafter_section_height_mm) / Decimal("1000000")
    rafter_main = Decimal(rafter_pair_count) * Decimal("2") * slope_length * rafter_cross
    tie_cross = Decimal(profile.tie_section_width_mm) * Decimal(profile.tie_section_height_mm) / Decimal("1000000")
    ties = Decimal(rafter_pair_count) * short_span * Decimal(profile.tie_length_factor) * tie_cross
    calc_rafters = rafter_main + ties

    counter_cross = Decimal(profile.counter_batten_width_mm) * Decimal(profile.counter_batten_height_mm) / Decimal("1000000")
    counter = Decimal(rafter_pair_count) * Decimal("2") * slope_length * counter_cross
    board_lathing = roof_area * Decimal(profile.lathing_volume_per_roof_m2)
    calc_lathing = counter + board_lathing

    # Legacy aggregate override означает: точная общая кубатура известна, но разбивка нет.
    if structural_lumber_volume_m3 is not None:
        beams = ZERO
        rafters = ZERO
        lathing = ZERO
        other = ZERO
        generic_structural = structural_lumber_volume_m3
    else:
        beams = beams_volume_m3 if beams_volume_m3 is not None else calc_beams
        rafters = rafters_volume_m3 if rafters_volume_m3 is not None else calc_rafters
        lathing = lathing_volume_m3 if lathing_volume_m3 is not None else calc_lathing
        other = other_structural_lumber_volume_m3 or ZERO
        generic_structural = ZERO

    terrace = terrace_area_m2 or ZERO

    return HouseTakeoff(
        footprint_m2=footprint,
        first_floor_area_m2=first_floor_area,
        mansard_area_m2=mansard_area,
        second_floor_area_m2=second_floor_area,
        external_wall_length_m=wall_length,
        external_wall_height_m=wall_height,
        external_wall_area_gross_m2=gross_external_area,
        external_openings_area_m2=external_openings,
        external_wall_area_net_m2=net_external_area,
        external_wall_volume_m3=external_volume,
        internal_wall_length_m=internal_length,
        internal_wall_height_m=partition_height,
        internal_openings_area_m2=internal_openings,
        internal_wall_area_net_m2=internal_net_area,
        internal_wall_volume_m3=partition_volume,
        roof_area_m2=roof_area,
        roof_slope_length_m=slope_length,
        gable_area_m2=gable_area,
        beams_volume_m3=beams,
        rafters_volume_m3=rafters,
        lathing_volume_m3=lathing,
        other_structural_lumber_volume_m3=other,
        generic_structural_lumber_volume_m3=generic_structural,
        terrace_area_m2=terrace,
        estimated_bedrooms=bedroom_count,
    )


def estimate_pile_grid(
    *, width: Decimal, length: Decimal, spacing_m: Decimal, additional_count: int = 0
) -> PileGrid:
    rows_x = _ceil_count(width, spacing_m)
    rows_y = _ceil_count(length, spacing_m)
    return PileGrid(
        rows_x=rows_x,
        rows_y=rows_y,
        base_count=rows_x * rows_y,
        additional_count=max(0, int(additional_count)),
    )
