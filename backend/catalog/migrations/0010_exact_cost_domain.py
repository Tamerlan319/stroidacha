from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_primary_image_constraint"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="projecttechnicaldata",
            options={
                "verbose_name": "Технический паспорт проекта",
                "verbose_name_plural": "Технические паспорта проектов",
            },
        ),
        migrations.AlterField(
            model_name="projecttechnicaldata",
            name="roof_complexity_factor",
            field=models.DecimalField(
                decimal_places=3, default=Decimal("1.000"), max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(Decimal("0.5")),
                    django.core.validators.MaxValueValidator(Decimal("3")),
                ],
                help_text="1.000 — без дополнительной надбавки. Используется для чистового покрытия.",
                verbose_name="Коэффициент сложности кровли",
            ),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata",
            name="data_source",
            field=models.CharField(
                choices=[
                    ("calculated", "Рассчитано автоматически"),
                    ("manual", "Внесено вручную"),
                    ("plan", "Получено из планировки"),
                    ("estimate", "Из рабочей сметы"),
                    ("import", "Импортировано"),
                ],
                default="calculated",
                max_length=20,
                verbose_name="Источник данных",
            ),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata",
            name="is_verified",
            field=models.BooleanField(
                default=False,
                help_text="Включайте после проверки менеджером/инженером.",
                verbose_name="Технические данные проверены",
            ),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata",
            name="verified_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Проверено"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="first_floor_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь 1-го этажа, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="mansard_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь мансарды, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="second_floor_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь 2-го этажа, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="external_wall_length_m",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Длина наружных стен, м"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="external_wall_height_m",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Расчётная высота наружных стен, м"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="external_openings_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Окна и двери наружных стен, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="internal_wall_length_m",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Длина внутренних перегородок, м"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="internal_wall_height_m",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True, verbose_name="Средняя высота перегородок, м"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="internal_openings_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Проёмы внутренних перегородок, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="beams_volume_m3",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="Балки/лаги, м³"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="rafters_volume_m3",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="Стропила/ригели, м³"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="lathing_volume_m3",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="Обрешётка/контробрешётка, м³"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="other_structural_lumber_volume_m3",
            field=models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True, verbose_name="Прочий конструкционный пиломатериал, м³"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="gable_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь фронтонов, м²"),
        ),
        migrations.AddField(
            model_name="projecttechnicaldata", name="terrace_area_m2",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь террас в комплектации, м²"),
        ),
        migrations.CreateModel(
            name="ProjectMaterialTakeoff",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_wall_volume_m3", models.DecimalField(decimal_places=3, max_digits=10, verbose_name="Наружные стены, м³")),
                ("internal_wall_volume_m3", models.DecimalField(decimal_places=3, default=Decimal("0"), max_digits=10, verbose_name="Перегородки, м³")),
                ("includes_waste", models.BooleanField(default=True, help_text="Если включено, калькулятор не добавляет процент запаса CalculatorMaterial повторно.", verbose_name="Запас уже включён в объём")),
                ("data_source", models.CharField(choices=[("calculated", "Рассчитано автоматически"), ("manual", "Внесено вручную"), ("plan", "Получено из планировки"), ("estimate", "Из рабочей сметы"), ("import", "Импортировано")], default="estimate", max_length=20, verbose_name="Источник данных")),
                ("is_verified", models.BooleanField(default=False, verbose_name="Проверено")),
                ("verified_at", models.DateTimeField(blank=True, null=True, verbose_name="Проверено")),
                ("notes", models.TextField(blank=True, verbose_name="Примечание")),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_takeoffs", to="catalog.material", verbose_name="Материал")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="material_takeoffs", to="catalog.project", verbose_name="Проект")),
            ],
            options={
                "verbose_name": "Кубатура стен по материалу",
                "verbose_name_plural": "Кубатура стен по материалам",
            },
        ),
        migrations.AddConstraint(
            model_name="projectmaterialtakeoff",
            constraint=models.UniqueConstraint(fields=("project", "material"), name="uniq_project_material_takeoff"),
        ),
        migrations.CreateModel(
            name="CostRate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("component", models.CharField(choices=[
                    ("wall_material", "Наружные стены — материал"),
                    ("partition_material", "Перегородки — материал"),
                    ("wall_processing", "Обработка стенового комплекта"),
                    ("structural_lumber", "Конструкционный пиломатериал — общий"),
                    ("beams_lumber", "Балки/лаги — пиломатериал"),
                    ("rafters_lumber", "Стропила/ригели — пиломатериал"),
                    ("lathing_lumber", "Обрешётка/контробрешётка — пиломатериал"),
                    ("other_lumber", "Прочий конструкционный пиломатериал"),
                    ("gable", "Фронтоны"),
                    ("temporary_roof", "Временная кровля / мембрана"),
                    ("consumables", "Расходники"),
                    ("assembly_first", "Сборка 1-го этажа"),
                    ("assembly_mansard", "Сборка мансарды"),
                    ("assembly_second", "Сборка 2-го этажа"),
                    ("terrace", "Терраса"),
                    ("delivery", "Доставка"),
                    ("documentation", "Проектная документация / подготовка"),
                    ("foundation_unit", "Фундамент — единица"),
                    ("foundation_footprint", "Фундамент — м² пятна"),
                    ("foundation_fixed", "Фундамент — фиксированная часть"),
                    ("roof_covering", "Чистовое кровельное покрытие"),
                ], max_length=40, verbose_name="Компонент")),
                ("title", models.CharField(max_length=180, verbose_name="Название ставки")),
                ("unit", models.CharField(choices=[("m3", "м³"), ("m2", "м²"), ("unit", "шт."), ("fixed", "фиксированная сумма")], max_length=10, verbose_name="Единица")),
                ("rate", models.DecimalField(decimal_places=2, max_digits=14, verbose_name="Ставка, ₽")),
                ("valid_from", models.DateField(default=django.utils.timezone.localdate, verbose_name="Действует с")),
                ("valid_to", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("source", models.CharField(choices=[
                    ("manual", "Внесено вручную"), ("office", "Офисный прайс"),
                    ("supplier", "Прайс поставщика"), ("contract", "Договор / подрядчик"),
                    ("import", "Импорт"), ("calibrated", "Расчётная калибровка"),
                ], default="manual", max_length=20, verbose_name="Источник")),
                ("note", models.TextField(blank=True, verbose_name="Примечание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлена")),
                ("foundation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cost_rates", to="catalog.foundationtype", verbose_name="Фундамент")),
                ("material", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cost_rates", to="catalog.material", verbose_name="Материал")),
                ("package", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cost_rates", to="catalog.buildpackage", verbose_name="Комплектация")),
                ("roof_covering", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cost_rates", to="catalog.roofcovering", verbose_name="Кровельное покрытие")),
            ],
            options={
                "verbose_name": "Сметная ставка",
                "verbose_name_plural": "Сметные ставки",
                "ordering": ["component", "-valid_from", "id"],
            },
        ),
        migrations.AddIndex(
            model_name="costrate",
            index=models.Index(fields=["component", "valid_from"], name="costrate_component_date_idx"),
        ),
        migrations.AddIndex(
            model_name="costrate",
            index=models.Index(fields=["is_active", "valid_from"], name="costrate_active_date_idx"),
        ),
    ]
