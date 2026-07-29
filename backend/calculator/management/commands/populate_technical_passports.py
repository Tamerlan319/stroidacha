from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Project, ProjectMaterialTakeoff, ProjectTechnicalData
from calculator.cost_engine import build_house_takeoff
from calculator.models import CalculatorMaterial, CalculatorSettings, HouseCostProfile


class Command(BaseCommand):
    help = (
        "Предварительно заполняет технические паспорта и кубатуру стен из геометрической модели V4. "
        "Данные помечаются CALCULATED и НЕ считаются инженерно проверенными. По умолчанию dry-run."
    )

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--force", action="store_true", help="Перезаписывать только непроверенные существующие значения")

    def handle(self, *args, **options):
        settings = (
            CalculatorSettings.objects.filter(is_active=True)
            .select_related("default_package")
            .order_by("id")
            .first()
        )
        if not settings or not settings.default_package_id:
            self.stderr.write("Не настроена комплектация калькулятора по умолчанию.")
            return
        profile = HouseCostProfile.objects.filter(package=settings.default_package, is_active=True).first()
        if not profile:
            self.stderr.write("Не настроена геометрическая модель HouseCostProfile.")
            return

        qs = (
            Project.objects.filter(
                is_active=True,
                construction_type=Project.ConstructionType.TIMBER,
                area__isnull=False,
                width__isnull=False,
                length__isnull=False,
                floors__isnull=False,
            )
            .prefetch_related("offers__material")
            .order_by("external_id", "id")
        )
        if options["limit"]:
            qs = qs[: options["limit"]]

        projects = 0
        material_rows = 0
        for project in qs:
            materials = []
            seen = set()
            for offer in project.offers.all():
                if offer.material_id not in seen:
                    seen.add(offer.material_id)
                    materials.append(offer.material)
            if not materials:
                continue

            configs = {
                cfg.material_id: cfg
                for cfg in CalculatorMaterial.objects.filter(material__in=materials, is_active=True).select_related("material")
            }
            first_cfg = next((configs.get(m.id) for m in materials if configs.get(m.id)), None)
            if not first_cfg:
                continue

            common = build_house_takeoff(
                area=Decimal(project.area),
                width=Decimal(project.width),
                length=Decimal(project.length),
                floors=Decimal(project.floors),
                profile=profile,
                material_cfg=first_cfg,
                bedrooms=project.bedrooms,
                terrace_area_m2=Decimal(project.terrace_area) if project.terrace_area is not None else None,
            )
            projects += 1
            self.stdout.write(
                f"{project.external_id or project.slug}: roof={common.roof_area_m2:.1f} м², "
                f"beams={common.beams_volume_m3:.3f} м³, rafters={common.rafters_volume_m3:.3f} м³"
            )

            if options["apply"]:
                technical, created = ProjectTechnicalData.objects.get_or_create(project=project)
                if created or (options["force"] and not technical.is_verified):
                    technical.data_source = ProjectTechnicalData.DataSource.CALCULATED
                    technical.is_verified = False
                    technical.first_floor_area_m2 = common.first_floor_area_m2
                    technical.mansard_area_m2 = common.mansard_area_m2
                    technical.second_floor_area_m2 = common.second_floor_area_m2
                    technical.external_wall_length_m = common.external_wall_length_m
                    technical.external_wall_height_m = common.external_wall_height_m
                    technical.external_openings_area_m2 = common.external_openings_area_m2
                    technical.internal_wall_length_m = common.internal_wall_length_m
                    technical.internal_wall_height_m = common.internal_wall_height_m
                    technical.internal_openings_area_m2 = common.internal_openings_area_m2
                    technical.beams_volume_m3 = common.beams_volume_m3
                    technical.rafters_volume_m3 = common.rafters_volume_m3
                    technical.lathing_volume_m3 = common.lathing_volume_m3
                    technical.gable_area_m2 = common.gable_area_m2
                    technical.roof_area_m2 = common.roof_area_m2
                    technical.terrace_area_m2 = common.terrace_area_m2
                    technical.roof_shape = ProjectTechnicalData.RoofShape.GABLE
                    technical.roof_pitch_deg = Decimal(profile.default_roof_pitch_deg)
                    technical.roof_overhang_m = Decimal(profile.default_roof_overhang_m)
                    technical.notes = "Предварительно рассчитано V4; требуется проверка по плану/смете."
                    technical.save()

            for material in materials:
                cfg = configs.get(material.id)
                if not cfg:
                    continue
                takeoff = build_house_takeoff(
                    area=Decimal(project.area),
                    width=Decimal(project.width),
                    length=Decimal(project.length),
                    floors=Decimal(project.floors),
                    profile=profile,
                    material_cfg=cfg,
                    bedrooms=project.bedrooms,
                    terrace_area_m2=Decimal(project.terrace_area) if project.terrace_area is not None else None,
                    # общая геометрия из первого прохода, чтобы все материалы использовали одинаковую планировку
                    first_floor_area_m2=common.first_floor_area_m2,
                    mansard_area_m2=common.mansard_area_m2,
                    second_floor_area_m2=common.second_floor_area_m2,
                    external_wall_length_m=common.external_wall_length_m,
                    external_wall_height_m=common.external_wall_height_m,
                    external_openings_area_m2=common.external_openings_area_m2,
                    internal_wall_length_m=common.internal_wall_length_m,
                    internal_wall_height_m=common.internal_wall_height_m,
                    internal_openings_area_m2=common.internal_openings_area_m2,
                    roof_area_m2=common.roof_area_m2,
                    gable_area_m2=common.gable_area_m2,
                    beams_volume_m3=common.beams_volume_m3,
                    rafters_volume_m3=common.rafters_volume_m3,
                    lathing_volume_m3=common.lathing_volume_m3,
                )
                material_rows += 1
                if options["apply"]:
                    item, _ = ProjectMaterialTakeoff.objects.get_or_create(
                        project=project,
                        material=material,
                        defaults={
                            "external_wall_volume_m3": takeoff.external_wall_volume_m3,
                            "internal_wall_volume_m3": takeoff.internal_wall_volume_m3,
                            "includes_waste": True,
                            "data_source": ProjectTechnicalData.DataSource.CALCULATED,
                            "is_verified": False,
                            "notes": "Предварительная кубатура V4; требуется проверка по проекту.",
                        },
                    )
                    if not item.is_verified and options["force"]:
                        item.external_wall_volume_m3 = takeoff.external_wall_volume_m3
                        item.internal_wall_volume_m3 = takeoff.internal_wall_volume_m3
                        item.includes_waste = True
                        item.data_source = ProjectTechnicalData.DataSource.CALCULATED
                        item.is_verified = False
                        item.notes = "Предварительная кубатура V4; требуется проверка по проекту."
                        item.save()

        self.stdout.write(f"Проектов: {projects}; материал-проектов: {material_rows}")
        if options["apply"]:
            self.stdout.write(self.style.SUCCESS("Предварительные техпаспорта записаны. Флаг is_verified не установлен."))
        else:
            self.stdout.write("Dry-run. Для записи добавьте --apply.")
