from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import combinations
from statistics import median

from catalog.models import Project, ProjectOffer

from .cost_engine import build_house_takeoff


@dataclass(frozen=True)
class OfferObservation:
    project_id: int
    material_id: int
    material_code: str
    price: float
    wall_volume_m3: float
    structural_lumber_volume_m3: float
    roof_area_m2: float
    first_floor_area_m2: float
    upper_floor_area_m2: float
    floors: Decimal
    gable_area_m2: float
    terrace_area_m2: float


@dataclass(frozen=True)
class CalibrationDiagnostics:
    family_priors: dict[str, float]
    family_samples: dict[str, int]
    material_pair_mape: float
    common_samples: int


FAMILY_PAIRS = {
    "ordinary": ("ordinary-150x150", "ordinary-150x200"),
    "profiled": ("profiled-145x145", "profiled-145x195"),
    "dry": ("dry-140x140", "dry-140x190"),
}


def calibrate_house_from_catalog(*, package, profile, material_cfgs, ridge: float = 0.50) -> dict:
    """Two-stage calibration for the deterministic BOQ engine.

    Stage 1 estimates wall-material rates only from price *differences inside the same
    project*. This cancels assembly, roof structure, delivery and all other common
    package costs. It avoids the identifiability problem of fitting every coefficient
    from final package prices at once.

    Stage 2 subtracts the calibrated wall cost from each project's offers and fits the
    remaining common package cost to structural lumber, temporary roof, floor assembly
    and a fixed part.

    Gable/consumables/terrace rates are intentionally NOT inferred from final offer
    prices because those components cannot be uniquely identified from the catalog.
    Existing manually entered values are treated as fixed known rates.
    """
    material_cfgs = list(material_cfgs)
    if not material_cfgs:
        raise ValueError("Нет материалов калькулятора для калибровки.")

    material_index = {cfg.material_id: i for i, cfg in enumerate(material_cfgs)}
    code_to_cfg = {cfg.material.code: cfg for cfg in material_cfgs}

    observations_by_project: dict[int, list[OfferObservation]] = {}
    offers = (
        ProjectOffer.objects.filter(
            build_package=package,
            base_price__isnull=False,
            project__is_active=True,
            project__construction_type=Project.ConstructionType.TIMBER,
            project__area__isnull=False,
            project__width__isnull=False,
            project__length__isnull=False,
            project__floors__isnull=False,
            material_id__in=material_index,
        )
        .select_related("project", "material")
        .order_by("project_id", "material_id")
    )

    for offer in offers.iterator():
        project = offer.project
        cfg = material_cfgs[material_index[offer.material_id]]
        takeoff = build_house_takeoff(
            area=Decimal(project.area),
            width=Decimal(project.width),
            length=Decimal(project.length),
            floors=Decimal(project.floors),
            profile=profile,
            material_cfg=cfg,
            bedrooms=project.bedrooms,
            terrace_area_m2=(Decimal(project.terrace_area) if project.terrace_area is not None else None),
            roof_area_m2=_project_roof_area(project),
        )
        observations_by_project.setdefault(project.id, []).append(
            OfferObservation(
                project_id=project.id,
                material_id=offer.material_id,
                material_code=offer.material.code,
                price=float(offer.base_price),
                wall_volume_m3=float(takeoff.total_wall_volume_m3),
                structural_lumber_volume_m3=float(takeoff.structural_lumber_volume_m3),
                roof_area_m2=float(takeoff.roof_area_m2),
                first_floor_area_m2=float(takeoff.first_floor_area_m2),
                upper_floor_area_m2=float(takeoff.upper_floor_area_m2),
                floors=Decimal(project.floors),
                gable_area_m2=float(takeoff.gable_area_m2),
                terrace_area_m2=float(takeoff.terrace_area_m2),
            )
        )

    if len(observations_by_project) < 20:
        raise ValueError(f"Недостаточно проектов для калибровки: {len(observations_by_project)}")

    family_priors, family_samples = _family_rate_priors(observations_by_project)
    priors = _material_priors(material_cfgs, family_priors)

    pair_rows: list[list[float]] = []
    pair_targets: list[float] = []
    for project_obs in observations_by_project.values():
        # All pairwise differences are useful here because project-common costs cancel.
        for left, right in combinations(project_obs, 2):
            target = right.price - left.price
            if abs(target) < 1.0:
                continue
            row = [0.0] * len(material_cfgs)
            row[material_index[right.material_id]] = right.wall_volume_m3
            row[material_index[left.material_id]] = -left.wall_volume_m3
            pair_rows.append(row)
            pair_targets.append(target)

    if len(pair_rows) < len(material_cfgs) * 8:
        raise ValueError(f"Недостаточно пар цен материалов: {len(pair_rows)}")

    wall_beta = _ridge_toward_prior(
        pair_rows,
        pair_targets,
        priors=priors,
        ridge=max(0.05, float(ridge)),
        nonnegative=True,
    )

    # Robust second pass removes corrupted/legacy price rows while keeping the fit based
    # on within-project deltas only.
    pair_errors = _relative_delta_errors(pair_rows, pair_targets, wall_beta)
    keep = [idx for idx, error in enumerate(pair_errors) if error <= 0.22]
    if len(keep) >= max(len(material_cfgs) * 8, int(len(pair_rows) * 0.60)):
        wall_beta = _ridge_toward_prior(
            [pair_rows[i] for i in keep],
            [pair_targets[i] for i in keep],
            priors=priors,
            ridge=max(0.05, float(ridge)),
            nonnegative=True,
        )

    # Hard data-driven safety ceiling: a wall rate cannot reasonably exceed the lower
    # tail of total package price / wall volume because the package contains many other
    # paid components as well.
    material_rates: dict[str, float] = {}
    for idx, cfg in enumerate(material_cfgs):
        observed = [
            obs.price / obs.wall_volume_m3
            for items in observations_by_project.values()
            for obs in items
            if obs.material_id == cfg.material_id and obs.wall_volume_m3 > 0
        ]
        upper = _percentile(observed, 0.15) * 0.95 if observed else float("inf")
        prior = priors[idx]
        rate = max(0.0, wall_beta[idx])
        if prior > 0:
            # Pair-derived family rate is the most interpretable anchor. Let the full
            # pair system move away from it, but not collapse to an arbitrary solution.
            rate = max(prior * 0.55, min(rate, prior * 1.65))
        rate = min(rate, upper)
        material_rates[cfg.material.code] = max(0.0, rate)

    # Common project cost should be the same regardless of selected wall material.
    # Use median residual across materials for each project to suppress single bad prices.
    common_rows: list[list[float]] = []
    common_targets: list[float] = []
    manual_gable = float(profile.gable_cladding_rate_per_m2 or 0)
    manual_consumables = float(profile.consumables_rate_per_wall_m3 or 0)
    manual_terrace = float(profile.terrace_rate_per_m2 or 0)

    for items in observations_by_project.values():
        residuals = []
        for obs in items:
            wall_rate = material_rates[obs.material_code]
            known_manual = (
                obs.gable_area_m2 * manual_gable
                + obs.wall_volume_m3 * manual_consumables
                + obs.terrace_area_m2 * manual_terrace
            )
            residuals.append(obs.price - obs.wall_volume_m3 * wall_rate - known_manual)
        target = float(median(residuals))
        if target <= 0:
            continue
        sample = items[0]
        mansard_area = sample.upper_floor_area_m2 if sample.floors == Decimal("1.5") else 0.0
        second_area = sample.upper_floor_area_m2 if sample.floors == Decimal("2") else 0.0
        common_rows.append(
            [
                sample.structural_lumber_volume_m3,
                sample.roof_area_m2,
                sample.first_floor_area_m2,
                mansard_area,
                second_area,
                1.0,
            ]
        )
        common_targets.append(target)

    if len(common_rows) < 20:
        raise ValueError(f"Недостаточно проектов для общей части комплектации: {len(common_rows)}")

    common_priors = [
        float(profile.structural_lumber_rate_per_m3 or 0),
        float(profile.temporary_roof_rate_per_m2 or 0),
        float(profile.first_floor_assembly_rate_per_m2 or 0),
        float(profile.mansard_assembly_rate_per_m2 or 0),
        float(profile.second_floor_assembly_rate_per_m2 or 0),
        float(profile.fixed_package_cost or 0),
    ]
    common_beta = _ridge_toward_prior(
        common_rows,
        common_targets,
        priors=common_priors,
        ridge=0.08,
        nonnegative=True,
    )
    common_errors = _relative_errors(common_rows, common_targets, common_beta)
    common_keep = [idx for idx, error in enumerate(common_errors) if error <= 0.30]
    if len(common_keep) >= max(20, int(len(common_rows) * 0.65)):
        common_beta = _ridge_toward_prior(
            [common_rows[i] for i in common_keep],
            [common_targets[i] for i in common_keep],
            priors=common_priors,
            ridge=0.08,
            nonnegative=True,
        )

    total_errors: list[float] = []
    by_material: dict[str, list[float]] = {cfg.material.code: [] for cfg in material_cfgs}
    for items in observations_by_project.values():
        for obs in items:
            mansard_area = obs.upper_floor_area_m2 if obs.floors == Decimal("1.5") else 0.0
            second_area = obs.upper_floor_area_m2 if obs.floors == Decimal("2") else 0.0
            common = (
                obs.structural_lumber_volume_m3 * common_beta[0]
                + obs.roof_area_m2 * common_beta[1]
                + obs.first_floor_area_m2 * common_beta[2]
                + mansard_area * common_beta[3]
                + second_area * common_beta[4]
                + common_beta[5]
            )
            manual = (
                obs.gable_area_m2 * manual_gable
                + obs.wall_volume_m3 * manual_consumables
                + obs.terrace_area_m2 * manual_terrace
            )
            predicted = obs.wall_volume_m3 * material_rates[obs.material_code] + common + manual
            error = abs(predicted - obs.price) / max(obs.price, 1.0)
            total_errors.append(error)
            by_material[obs.material_code].append(error)

    ordered = sorted(error * 100 for error in total_errors)
    p90 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.90))]
    material_mape = {
        code: (sum(values) / len(values) * 100 if values else 0.0)
        for code, values in by_material.items()
    }
    pair_final_errors = _relative_delta_errors(pair_rows, pair_targets, [material_rates[cfg.material.code] for cfg in material_cfgs])

    return {
        "samples": len(total_errors),
        "projects": len(observations_by_project),
        "mape": sum(total_errors) / len(total_errors) * 100,
        "p90": p90,
        "material_rates": material_rates,
        "material_mape": material_mape,
        "structural_lumber_rate": max(0.0, common_beta[0]),
        "temporary_roof_rate": max(0.0, common_beta[1]),
        "first_floor_assembly_rate": max(0.0, common_beta[2]),
        "mansard_assembly_rate": max(0.0, common_beta[3]),
        "second_floor_assembly_rate": max(0.0, common_beta[4]),
        "fixed_cost": max(0.0, common_beta[5]),
        # These are deliberately manual. Final package prices cannot uniquely identify
        # them separately from the other components.
        "gable_rate": manual_gable,
        "consumables_rate": manual_consumables,
        "terrace_rate": manual_terrace,
        "diagnostics": CalibrationDiagnostics(
            family_priors=family_priors,
            family_samples=family_samples,
            material_pair_mape=(sum(pair_final_errors) / len(pair_final_errors) * 100),
            common_samples=len(common_rows),
        ),
    }


def _project_roof_area(project):
    try:
        if project.technical.roof_area_m2 is not None:
            return Decimal(project.technical.roof_area_m2)
    except Exception:
        pass
    return None


def _family_rate_priors(observations_by_project: dict[int, list[OfferObservation]]):
    samples: dict[str, list[float]] = {family: [] for family in FAMILY_PAIRS}
    for items in observations_by_project.values():
        by_code = {item.material_code: item for item in items}
        for family, (thin_code, thick_code) in FAMILY_PAIRS.items():
            thin = by_code.get(thin_code)
            thick = by_code.get(thick_code)
            if not thin or not thick:
                continue
            delta_volume = thick.wall_volume_m3 - thin.wall_volume_m3
            delta_price = thick.price - thin.price
            if delta_volume > 0.05 and delta_price > 0:
                samples[family].append(delta_price / delta_volume)

    priors: dict[str, float] = {}
    counts: dict[str, int] = {}
    for family, values in samples.items():
        clean = _robust_values(values)
        if clean:
            priors[family] = float(median(clean))
            counts[family] = len(clean)
    return priors, counts


def _material_priors(material_cfgs, family_priors: dict[str, float]) -> list[float]:
    result = []
    for cfg in material_cfgs:
        code = cfg.material.code
        family = next((name for name, pair in FAMILY_PAIRS.items() if code in pair), None)
        configured = float(cfg.wall_rate_per_m3 or 0)
        if family and family in family_priors:
            result.append(family_priors[family])
        elif configured > 0:
            result.append(configured)
        else:
            result.append(0.0)
    return result


def _robust_values(values: list[float]) -> list[float]:
    if len(values) < 5:
        return [value for value in values if value > 0]
    positive = [value for value in values if value > 0]
    if not positive:
        return []
    med = float(median(positive))
    deviations = [abs(value - med) for value in positive]
    mad = float(median(deviations))
    if mad <= 1e-9:
        return [value for value in positive if med * 0.50 <= value <= med * 1.50]
    # 1.4826 converts MAD to a robust sigma estimate for approximately normal data.
    limit = max(med * 0.35, mad * 1.4826 * 3.5)
    return [value for value in positive if abs(value - med) <= limit]


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = max(0.0, min(1.0, q)) * (len(ordered) - 1)
    low = int(position)
    high = min(len(ordered) - 1, low + 1)
    fraction = position - low
    return ordered[low] * (1 - fraction) + ordered[high] * fraction


def _relative_errors(rows, targets, beta):
    errors = []
    for row, target in zip(rows, targets):
        prediction = sum(x * b for x, b in zip(row, beta))
        errors.append(abs(prediction - target) / max(abs(target), 1.0))
    return errors


def _relative_delta_errors(rows, targets, beta):
    errors = []
    for row, target in zip(rows, targets):
        prediction = sum(x * b for x, b in zip(row, beta))
        # Small price deltas are noisy and should not dominate the quality metric.
        errors.append(abs(prediction - target) / max(abs(target), 50_000.0))
    return errors


def _ridge_toward_prior(
    rows,
    targets,
    *,
    priors,
    ridge: float = 0.1,
    nonnegative: bool = True,
    max_iter: int = 8000,
    tolerance: float = 1e-7,
):
    """Coordinate-descent ridge regression around interpretable priors.

    Unlike ordinary ridge-to-zero, this keeps an underidentified cost decomposition near
    rates that are independently observed (for wall families) or already entered by the
    estimator in the admin. No numpy/scipy dependency is required.
    """
    n = len(rows)
    p = len(rows[0])
    if len(priors) != p:
        raise ValueError("Количество priors не совпадает с количеством коэффициентов.")

    scales = []
    for j in range(p):
        norm = sum(rows[i][j] ** 2 for i in range(n)) ** 0.5
        scales.append(norm if norm > 1e-12 else 1.0)

    z = [[rows[i][j] / scales[j] for j in range(p)] for i in range(n)]
    prior_scaled = [float(priors[j]) * scales[j] for j in range(p)]
    beta_scaled = prior_scaled.copy()
    prediction = [sum(z[i][j] * beta_scaled[j] for j in range(p)) for i in range(n)]

    for _ in range(max_iter):
        max_change = 0.0
        for j in range(p):
            old = beta_scaled[j]
            numerator = ridge * prior_scaled[j]
            denominator = ridge
            for i in range(n):
                residual_without_j = targets[i] - (prediction[i] - z[i][j] * old)
                numerator += z[i][j] * residual_without_j
                denominator += z[i][j] * z[i][j]
            new = numerator / denominator if denominator else 0.0
            if nonnegative:
                new = max(0.0, new)
            change = new - old
            if change:
                for i in range(n):
                    prediction[i] += z[i][j] * change
            beta_scaled[j] = new
            max_change = max(max_change, abs(change))
        if max_change < tolerance:
            break

    return [beta_scaled[j] / scales[j] for j in range(p)]
