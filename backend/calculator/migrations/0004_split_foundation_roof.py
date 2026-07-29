from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    CalculatorSettings = apps.get_model("calculator", "CalculatorSettings")
    CalculatorExtraOption = apps.get_model("calculator", "CalculatorExtraOption")
    CalculatorFoundation = apps.get_model("calculator", "CalculatorFoundation")
    CalculatorRoofCovering = apps.get_model("calculator", "CalculatorRoofCovering")
    BuildPackage = apps.get_model("catalog", "BuildPackage")
    FoundationType = apps.get_model("catalog", "FoundationType")
    RoofCovering = apps.get_model("catalog", "RoofCovering")

    default_package = BuildPackage.objects.filter(code="pod-usadku").first()
    if default_package:
        CalculatorSettings.objects.filter(default_package__isnull=True).update(default_package_id=default_package.id)

    foundations = {item.code: item for item in FoundationType.objects.all()}
    roofs = {item.code: item for item in RoofCovering.objects.all()}

    for legacy in CalculatorExtraOption.objects.select_related("construction_option").all().iterator():
        option = legacy.construction_option
        if option.code in foundations:
            CalculatorFoundation.objects.update_or_create(
                foundation_id=foundations[option.code].id,
                defaults={
                    "fallback_price_per_footprint_m2": legacy.fallback_price_per_footprint_m2,
                    "minimum_price": legacy.minimum_price,
                    "source_note": legacy.source_note,
                    "sort_order": legacy.sort_order,
                    "is_active": legacy.is_active,
                },
            )
        elif option.code in roofs:
            CalculatorRoofCovering.objects.update_or_create(
                covering_id=roofs[option.code].id,
                defaults={
                    "fallback_price_per_footprint_m2": legacy.fallback_price_per_footprint_m2,
                    "minimum_price": legacy.minimum_price,
                    "source_note": legacy.source_note,
                    "sort_order": legacy.sort_order,
                    "is_active": legacy.is_active,
                },
            )


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0009_primary_image_constraint"),
        ("calculator", "0003_link_catalog_entities"),
    ]

    operations = [
        migrations.AddField(
            model_name="calculatorsettings",
            name="default_package",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="calculator_profiles",
                to="catalog.buildpackage",
                verbose_name="Комплектация по умолчанию",
            ),
        ),
        migrations.CreateModel(
            name="CalculatorFoundation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fallback_price_per_footprint_m2", models.PositiveIntegerField(help_text="Последний fallback, если нет точной/формульной/исторической цены.", verbose_name="Резервная цена за м² пятна, ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Резервный минимум, ₽")),
                ("source_note", models.CharField(blank=True, max_length=255, verbose_name="Источник резервной цены")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("foundation", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config", to="catalog.foundationtype", verbose_name="Фундамент каталога")),
            ],
            options={"verbose_name": "Фундамент калькулятора", "verbose_name_plural": "Фундаменты калькулятора", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="CalculatorRoofCovering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("fallback_price_per_footprint_m2", models.PositiveIntegerField(help_text="Legacy fallback до заполнения фактических площадей кровли и ставок за м².", verbose_name="Резервная цена за м² пятна, ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Резервный минимум, ₽")),
                ("source_note", models.CharField(blank=True, max_length=255, verbose_name="Источник резервной цены")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("covering", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config", to="catalog.roofcovering", verbose_name="Покрытие каталога")),
            ],
            options={"verbose_name": "Чистовая кровля калькулятора", "verbose_name_plural": "Чистовая кровля калькулятора", "ordering": ["sort_order", "id"]},
        ),
        migrations.RunPython(forwards, backwards),
    ]
