from decimal import Decimal

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


MATERIAL_DEFAULTS = {
    "ordinary-150x150": (150, 100),
    "ordinary-150x200": (200, 100),
    "profiled-145x145": (145, 95),
    "profiled-145x195": (195, 95),
    "dry-140x140": (140, 95),
    "dry-140x190": (190, 95),
}


def forwards(apps, schema_editor):
    BuildPackage = apps.get_model("catalog", "BuildPackage")
    CalculatorMaterial = apps.get_model("calculator", "CalculatorMaterial")
    HouseCostProfile = apps.get_model("calculator", "HouseCostProfile")

    package = BuildPackage.objects.filter(code="pod-usadku").first()
    if package:
        HouseCostProfile.objects.get_or_create(
            package_id=package.id,
            defaults={"title": "Под усадку — сметная модель", "is_active": True},
        )

    for cfg in CalculatorMaterial.objects.select_related("material").all().iterator():
        values = MATERIAL_DEFAULTS.get(cfg.material.code)
        if not values:
            continue
        wall_mm, partition_mm = values
        cfg.wall_thickness_mm = wall_mm
        cfg.partition_thickness_mm = partition_mm
        cfg.wall_rate_per_m3 = Decimal("0")
        cfg.partition_rate_per_m3 = Decimal("0")
        cfg.wall_waste_percent = Decimal("5")
        cfg.source_note = "V3 BOQ: денежные ставки задаются калибровкой или вручную"
        cfg.save(update_fields=[
            "wall_thickness_mm", "partition_thickness_mm", "wall_rate_per_m3",
            "partition_rate_per_m3", "wall_waste_percent", "source_note",
        ])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("calculator", "0004_split_foundation_roof"),
    ]

    operations = [
        migrations.CreateModel(
            name="HouseCostProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Под усадку — сметная модель", max_length=120, verbose_name="Название")),
                ("first_floor_height_m", models.DecimalField(decimal_places=2, default=Decimal("2.70"), max_digits=4, verbose_name="Высота 1-го этажа, м")),
                ("second_floor_height_m", models.DecimalField(decimal_places=2, default=Decimal("2.50"), max_digits=4, verbose_name="Высота 2-го этажа, м")),
                ("mansard_knee_wall_height_m", models.DecimalField(decimal_places=2, default=Decimal("0.00"), help_text="Фронтоны считаются отдельно как каркасно-щитовые; сюда ставится только реальная брусовая коленная стена, если она есть.", max_digits=4, verbose_name="Добавочная высота брусовой стены мансарды, м")),
                ("external_openings_ratio", models.DecimalField(decimal_places=3, default=Decimal("0.120"), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal("0")), django.core.validators.MaxValueValidator(Decimal("0.5"))], verbose_name="Проёмы наружных стен, доля")),
                ("internal_wall_length_per_m2", models.DecimalField(decimal_places=3, default=Decimal("0.150"), max_digits=5, verbose_name="Перегородки: м длины на 1 м² площади")),
                ("internal_wall_length_per_bedroom_m", models.DecimalField(decimal_places=2, default=Decimal("1.50"), max_digits=5, verbose_name="Доп. перегородки на спальню, м")),
                ("partition_height_m", models.DecimalField(decimal_places=2, default=Decimal("2.60"), max_digits=4, verbose_name="Средняя высота перегородок, м")),
                ("internal_openings_ratio", models.DecimalField(decimal_places=3, default=Decimal("0.080"), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal("0")), django.core.validators.MaxValueValidator(Decimal("0.5"))], verbose_name="Проёмы перегородок, доля")),

                ("joist_spacing_m", models.DecimalField(decimal_places=3, default=Decimal("0.590"), max_digits=4, verbose_name="Шаг балок, м")),
                ("joist_section_width_mm", models.PositiveSmallIntegerField(default=100, verbose_name="Балка: ширина, мм")),
                ("joist_section_height_mm", models.PositiveSmallIntegerField(default=150, verbose_name="Балка: высота, мм")),
                ("joist_systems_one_floor", models.DecimalField(decimal_places=1, default=Decimal("1.0"), max_digits=3, verbose_name="Комплектов балок: 1 этаж")),
                ("joist_systems_mansard", models.DecimalField(decimal_places=1, default=Decimal("2.0"), max_digits=3, verbose_name="Комплектов балок: 1,5 этажа")),
                ("joist_systems_two_floor", models.DecimalField(decimal_places=1, default=Decimal("2.0"), max_digits=3, verbose_name="Комплектов балок: 2 этажа")),
                ("rafter_spacing_m", models.DecimalField(decimal_places=3, default=Decimal("0.590"), max_digits=4, verbose_name="Шаг стропил, м")),
                ("rafter_section_width_mm", models.PositiveSmallIntegerField(default=50, verbose_name="Стропила: ширина, мм")),
                ("rafter_section_height_mm", models.PositiveSmallIntegerField(default=150, verbose_name="Стропила: высота, мм")),
                ("tie_section_width_mm", models.PositiveSmallIntegerField(default=50, verbose_name="Ригель: ширина, мм")),
                ("tie_section_height_mm", models.PositiveSmallIntegerField(default=150, verbose_name="Ригель: высота, мм")),
                ("tie_length_factor", models.DecimalField(decimal_places=2, default=Decimal("1.00"), max_digits=4, verbose_name="Длина ригеля к пролёту, коэффициент")),
                ("counter_batten_width_mm", models.PositiveSmallIntegerField(default=50, verbose_name="Контробрешётка: ширина, мм")),
                ("counter_batten_height_mm", models.PositiveSmallIntegerField(default=50, verbose_name="Контробрешётка: высота, мм")),
                ("lathing_volume_per_roof_m2", models.DecimalField(decimal_places=4, default=Decimal("0.0060"), help_text="Эквивалентный расход доски обрешётки на квадратный метр ската.", max_digits=6, verbose_name="Обрешётка: м³ на 1 м² кровли")),
                ("default_roof_pitch_deg", models.DecimalField(decimal_places=2, default=Decimal("35"), max_digits=5, verbose_name="Угол двускатной крыши по умолчанию, °")),
                ("default_roof_overhang_m", models.DecimalField(decimal_places=2, default=Decimal("0.50"), max_digits=4, verbose_name="Свес кровли по умолчанию, м")),

                ("structural_lumber_rate_per_m3", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Пиломатериал конструкций, ₽/м³")),
                ("gable_cladding_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Фронтоны (каркас + имитация), ₽/м²")),
                ("temporary_roof_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Временная кровля/мембрана, ₽/м²")),
                ("consumables_rate_per_wall_m3", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Джут, нагели, крепёж и обработка, ₽/м³ стен")),
                ("first_floor_assembly_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Сборка: 1-й этаж, ₽/м²")),
                ("mansard_assembly_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Сборка: мансарда, ₽/м²")),
                ("second_floor_assembly_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Сборка: 2-й этаж, ₽/м²")),
                ("terrace_rate_per_m2", models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Терраса в базовой комплектации, ₽/м²")),
                ("fixed_package_cost", models.DecimalField(decimal_places=2, default=Decimal("0"), help_text="Доставка, проектная документация и прочие условно-постоянные расходы.", max_digits=12, verbose_name="Фиксированная часть, ₽")),

                ("calibration_samples", models.PositiveIntegerField(default=0, verbose_name="Выборка калибровки")),
                ("calibration_mape", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Средняя ошибка калибровки, %")),
                ("calibrated_at", models.DateTimeField(blank=True, null=True, verbose_name="Последняя калибровка")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("package", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="cost_profile", to="catalog.buildpackage", verbose_name="Комплектация")),
            ],
            options={"verbose_name": "Сметная модель дома", "verbose_name_plural": "Сметные модели дома", "ordering": ["id"]},
        ),
        migrations.AddField(
            model_name="calculatormaterial",
            name="wall_thickness_mm",
            field=models.PositiveSmallIntegerField(default=150, verbose_name="Толщина наружной стены, мм"),
        ),
        migrations.AddField(
            model_name="calculatormaterial",
            name="partition_thickness_mm",
            field=models.PositiveSmallIntegerField(default=100, verbose_name="Толщина перегородки, мм"),
        ),
        migrations.AddField(
            model_name="calculatormaterial",
            name="wall_rate_per_m3",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Стеновой материал, ₽/м³"),
        ),
        migrations.AddField(
            model_name="calculatormaterial",
            name="partition_rate_per_m3",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Материал перегородок, ₽/м³"),
        ),
        migrations.AddField(
            model_name="calculatormaterial",
            name="wall_waste_percent",
            field=models.DecimalField(decimal_places=2, default=Decimal("5"), max_digits=5, verbose_name="Запас материала, %"),
        ),
        migrations.AddField(
            model_name="calculatorfoundation",
            name="pile_spacing_m",
            field=models.DecimalField(decimal_places=2, default=Decimal("2.50"), max_digits=4, verbose_name="Максимальный шаг свай, м"),
        ),
        migrations.AddField(
            model_name="calculatorfoundation",
            name="base_extra_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Постоянная добавка к фундаменту, ₽"),
        ),
        migrations.AlterField(
            model_name="calculatormaterial",
            name="fallback_price_per_m2",
            field=models.PositiveIntegerField(default=0, verbose_name="Legacy: резервная цена за м², ₽"),
        ),
        migrations.AlterField(
            model_name="calculatorfoundation",
            name="fallback_price_per_footprint_m2",
            field=models.PositiveIntegerField(default=0, verbose_name="Legacy fallback, ₽/м²"),
        ),
        migrations.AlterField(
            model_name="calculatorroofcovering",
            name="fallback_price_per_footprint_m2",
            field=models.PositiveIntegerField(default=0, verbose_name="Legacy fallback, ₽/м²"),
        ),
        migrations.AlterField(
            model_name="calculatorextraoption",
            name="fallback_price_per_footprint_m2",
            field=models.PositiveIntegerField(default=0, verbose_name="Legacy fallback, ₽/м²"),
        ),
        migrations.RunPython(forwards, backwards),
    ]
