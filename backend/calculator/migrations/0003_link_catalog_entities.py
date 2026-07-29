import hashlib
import re

from django.db import migrations, models
import django.db.models.deletion


def normalize(value):
    value = str(value or "").casefold().replace("×", "x").replace("х", "x")
    return re.sub(r"\s+", " ", value).strip()


def fallback_code(prefix, value):
    return f"{prefix}-{hashlib.sha1(normalize(value).encode('utf-8')).hexdigest()[:10]}"


def link_catalog_entities(apps, schema_editor):
    CalculatorMaterial = apps.get_model("calculator", "CalculatorMaterial")
    CalculatorExtraOption = apps.get_model("calculator", "CalculatorExtraOption")
    Material = apps.get_model("catalog", "Material")
    ConstructionOption = apps.get_model("catalog", "ConstructionOption")

    for item in CalculatorMaterial.objects.all():
        material = Material.objects.filter(code=item.code).first()
        if material is None:
            group = normalize(item.group_match)
            if "камер" in group or "суш" in group:
                kind = "dry"
            elif "проф" in group:
                kind = "profiled"
            elif "брус" in group:
                kind = "regular"
            else:
                kind = "other"
            material = Material.objects.create(
                code=item.code or fallback_code("material", item.title),
                kind=kind,
                group_title=item.group_match or "Другое",
                title=item.title,
                sort_order=item.sort_order,
                is_active=item.is_active,
            )
        item.material_id = material.id
        item.save(update_fields=["material"])

    for item in CalculatorExtraOption.objects.all():
        option = ConstructionOption.objects.filter(code=item.code).first()
        if option is None:
            kind = item.kind if item.kind in {"foundation", "roof"} else "other"
            option = ConstructionOption.objects.create(
                code=item.code or fallback_code("option", item.title),
                kind=kind,
                title=item.title,
                sort_order=item.sort_order,
                is_active=item.is_active,
            )
        item.construction_option_id = option.id
        item.save(update_fields=["construction_option"])


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0007_normalize_catalog_pricing"),
        ("calculator", "0002_seed_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="calculatormaterial",
            name="material",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config_tmp", to="catalog.material", verbose_name="Материал каталога"),
        ),
        migrations.AddField(
            model_name="calculatorextraoption",
            name="construction_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config_tmp", to="catalog.constructionoption", verbose_name="Опция каталога"),
        ),
        migrations.RunPython(link_catalog_entities, migrations.RunPython.noop),
        migrations.RemoveField(model_name="calculatormaterial", name="code"),
        migrations.RemoveField(model_name="calculatormaterial", name="title"),
        migrations.RemoveField(model_name="calculatormaterial", name="group_match"),
        migrations.RemoveField(model_name="calculatormaterial", name="title_match"),
        migrations.RemoveField(model_name="calculatorextraoption", name="kind"),
        migrations.RemoveField(model_name="calculatorextraoption", name="code"),
        migrations.RemoveField(model_name="calculatorextraoption", name="title"),
        migrations.RemoveField(model_name="calculatorextraoption", name="group_match"),
        migrations.RemoveField(model_name="calculatorextraoption", name="title_match"),
        migrations.AlterField(
            model_name="calculatormaterial",
            name="material",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config", to="catalog.material", verbose_name="Материал каталога"),
        ),
        migrations.AlterField(
            model_name="calculatorextraoption",
            name="construction_option",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="calculator_config", to="catalog.constructionoption", verbose_name="Опция каталога"),
        ),
        migrations.AlterModelOptions(
            name="calculatormaterial",
            options={"ordering": ["sort_order", "id"], "verbose_name": "Материал калькулятора", "verbose_name_plural": "Материалы калькулятора"},
        ),
        migrations.AlterModelOptions(
            name="calculatorextraoption",
            options={"ordering": ["construction_option__kind", "sort_order", "id"], "verbose_name": "Доп. опция калькулятора", "verbose_name_plural": "Доп. опции калькулятора"},
        ),
    ]
