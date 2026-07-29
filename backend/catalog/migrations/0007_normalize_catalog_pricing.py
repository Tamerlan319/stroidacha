import hashlib
import re

from django.db import migrations, models
import django.db.models.deletion


MATERIALS = [
    ("ordinary-150x150", "regular", "Обычный брус", "Обычный брус 150×150", 150, 150, 10),
    ("ordinary-150x200", "regular", "Обычный брус", "Обычный брус 150×200", 150, 200, 20),
    ("profiled-145x145", "profiled", "Профилированный брус", "Профилированный брус 145×145", 145, 145, 30),
    ("profiled-145x195", "profiled", "Профилированный брус", "Профилированный брус 145×195", 145, 195, 40),
    ("dry-140x140", "dry", "Брус камерной сушки", "Брус камерной сушки 140×140", 140, 140, 50),
    ("dry-140x190", "dry", "Брус камерной сушки", "Брус камерной сушки 140×190", 140, 190, 60),
]

OPTIONS = [
    ("screw-piles", "foundation", "Свайный фундамент", 10),
    ("reinforced-piles", "foundation", "ЖБ сваи (ГОСТ)", 20),
    ("metal-tile", "roof", "Металлочерепица", 10),
    ("ondulin", "roof", "Ондулин", 20),
    ("flexible-shingles", "roof", "Гибкая черепица", 30),
    ("metal-profile", "roof", "Металлопрофиль", 40),
]


def normalize(value):
    value = str(value or "").casefold().replace("×", "x").replace("х", "x")
    return re.sub(r"\s+", " ", value).strip()


def stable_code(prefix, title):
    key = normalize(title)
    known = {
        "обычный брус 150x150": "ordinary-150x150",
        "обычный брус 150x200": "ordinary-150x200",
        "профилированный брус 145x145": "profiled-145x145",
        "профилированный брус 145x195": "profiled-145x195",
        "брус камерной сушки 140x140": "dry-140x140",
        "брус камерной сушки 140x190": "dry-140x190",
        "свайный фундамент": "screw-piles",
        "свайно-винтовой фундамент": "screw-piles",
        "жб сваи (гост)": "reinforced-piles",
        "металлочерепица": "metal-tile",
        "ондулин": "ondulin",
        "гибкая черепица": "flexible-shingles",
        "металлопрофиль": "metal-profile",
    }
    if key in known:
        return known[key]
    return f"{prefix}-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:10]}"


def material_kind(group_title):
    group = normalize(group_title)
    if "камер" in group or "суш" in group:
        return "dry"
    if "проф" in group:
        return "profiled"
    if "брус" in group:
        return "regular"
    return "other"


def option_kind(group_title):
    group = normalize(group_title)
    if "фундамент" in group:
        return "foundation"
    if "кров" in group:
        return "roof"
    return "other"


def section(title):
    match = re.search(r"(\d{2,3})\s*x\s*(\d{2,3})", normalize(title))
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def migrate_pricing_data(apps, schema_editor):
    Material = apps.get_model("catalog", "Material")
    ConstructionOption = apps.get_model("catalog", "ConstructionOption")
    Project = apps.get_model("catalog", "Project")
    ProjectPackage = apps.get_model("catalog", "ProjectPackage")
    LegacyPrice = apps.get_model("catalog", "ProjectPriceOption")
    LegacyAddon = apps.get_model("catalog", "ProjectAddon")
    ProjectOffer = apps.get_model("catalog", "ProjectOffer")
    ProjectOptionPrice = apps.get_model("catalog", "ProjectOptionPrice")
    PricingRule = apps.get_model("catalog", "PricingRule")

    for code, kind, group, title, width, height, sort_order in MATERIALS:
        Material.objects.update_or_create(
            code=code,
            defaults={
                "kind": kind,
                "group_title": group,
                "title": title,
                "section_width_mm": width,
                "section_height_mm": height,
                "sort_order": sort_order,
                "is_active": True,
            },
        )

    for code, kind, title, sort_order in OPTIONS:
        ConstructionOption.objects.update_or_create(
            code=code,
            defaults={"kind": kind, "title": title, "sort_order": sort_order, "is_active": True},
        )

    for legacy in LegacyPrice.objects.all().iterator():
        code = stable_code("material", legacy.title)
        width, height = section(legacy.title)
        material, _ = Material.objects.update_or_create(
            code=code,
            defaults={
                "kind": material_kind(legacy.group_title),
                "group_title": legacy.group_title or "Другое",
                "title": legacy.title,
                "section_width_mm": width,
                "section_height_mm": height,
                "sort_order": legacy.sort_order,
                "is_active": True,
            },
        )
        package = (
            ProjectPackage.objects.filter(project_id=legacy.project_id)
            .order_by("sort_order", "id")
            .first()
        )
        ProjectOffer.objects.update_or_create(
            project_id=legacy.project_id,
            material_id=material.id,
            package_id=package.id if package else None,
            defaults={
                "base_price": legacy.price,
                "is_price_fixed": legacy.is_price_fixed,
                "note": legacy.note,
                "sort_order": legacy.sort_order,
            },
        )

    for legacy in LegacyAddon.objects.all().iterator():
        code = stable_code("option", legacy.title)
        option, _ = ConstructionOption.objects.update_or_create(
            code=code,
            defaults={
                "kind": option_kind(legacy.group_title),
                "title": legacy.title,
                "sort_order": legacy.sort_order,
                "is_active": True,
            },
        )
        ProjectOptionPrice.objects.update_or_create(
            project_id=legacy.project_id,
            option_id=option.id,
            defaults={
                "base_price": legacy.price,
                "is_price_fixed": legacy.is_price_fixed,
                "description": legacy.description,
                "sort_order": legacy.sort_order,
            },
        )

    # Сохраняем старое поведение проектов с полностью фиксированными ценами.
    Project.objects.filter(price_indexing_disabled=True).update(addon_price_indexing_disabled=True)

    materials = list(Material.objects.all())
    options = list(ConstructionOption.objects.all())
    for rule in PricingRule.objects.all():
        if rule.kind == "material":
            for material in materials:
                if (
                    normalize(rule.group_match) in normalize(material.group_title)
                    and normalize(rule.title_match) in normalize(material.title)
                ):
                    rule.material_id = material.id
                    rule.construction_option_id = None
                    rule.save(update_fields=["material", "construction_option"])
                    break
        elif rule.kind == "addon":
            for option in options:
                group = {"foundation": "Фундамент", "roof": "Кровля", "other": "Другое"}.get(option.kind, "")
                if (
                    normalize(rule.group_match) in normalize(group)
                    and normalize(rule.title_match) in normalize(option.title)
                ):
                    rule.material_id = None
                    rule.construction_option_id = option.id
                    rule.save(update_fields=["material", "construction_option"])
                    break


class Migration(migrations.Migration):
    dependencies = [("catalog", "0006_seed_pricing_defaults")]

    operations = [
        migrations.CreateModel(
            name="Material",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("kind", models.CharField(choices=[("regular", "Обычный брус"), ("profiled", "Профилированный брус"), ("dry", "Брус камерной сушки"), ("other", "Другое")], default="other", max_length=20, verbose_name="Тип")),
                ("group_title", models.CharField(max_length=120, verbose_name="Группа")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("section_width_mm", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Сечение, ширина, мм")),
                ("section_height_mm", models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Сечение, высота, мм")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"verbose_name": "Материал", "verbose_name_plural": "Материалы", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ConstructionOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("kind", models.CharField(choices=[("foundation", "Фундамент"), ("roof", "Кровля"), ("other", "Другое")], default="other", max_length=20, verbose_name="Тип")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={"verbose_name": "Строительная опция", "verbose_name_plural": "Строительные опции", "ordering": ["kind", "sort_order", "id"]},
        ),
        migrations.AddField(
            model_name="project",
            name="addon_price_indexing_disabled",
            field=models.BooleanField(default=False, help_text="Отдельно фиксирует фундамент, кровлю и другие дополнительные опции проекта.", verbose_name="Не индексировать дополнительные опции"),
        ),
        migrations.AlterField(
            model_name="project",
            name="price_indexing_disabled",
            field=models.BooleanField(default=False, help_text="Не применять индексацию к стоимости дома и материалам этого проекта.", verbose_name="Не индексировать цены дома"),
        ),
        migrations.CreateModel(
            name="ProjectOffer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_price", models.PositiveIntegerField(blank=True, null=True, verbose_name="Базовая цена, ₽")),
                ("is_price_fixed", models.BooleanField(default=False, help_text="Не применять индексацию к этой цене.", verbose_name="Фиксированная цена")),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="Примечание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("material", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_offers", to="catalog.material", verbose_name="Материал")),
                ("package", models.ForeignKey(blank=True, help_text="Можно оставить пустым, если цена не привязана к конкретной комплектации.", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="offers", to="catalog.projectpackage", verbose_name="Комплектация")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="offers", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Предложение проекта", "verbose_name_plural": "Цены по материалам и комплектациям", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProjectOptionPrice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("base_price", models.PositiveIntegerField(blank=True, null=True, verbose_name="Базовая цена, ₽")),
                ("is_price_fixed", models.BooleanField(default=False, help_text="Не применять индексацию к этой опции.", verbose_name="Фиксированная цена")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("option", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_prices", to="catalog.constructionoption", verbose_name="Опция")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="option_prices", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Цена дополнительной опции", "verbose_name_plural": "Цены дополнительных опций", "ordering": ["sort_order", "id"]},
        ),
        migrations.AddField(
            model_name="pricingrule",
            name="construction_option",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.constructionoption", verbose_name="Дополнительная опция"),
        ),
        migrations.AddField(
            model_name="pricingrule",
            name="material",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.material", verbose_name="Материал"),
        ),
        migrations.RunPython(migrate_pricing_data, migrations.RunPython.noop),
        migrations.RemoveField(model_name="pricingrule", name="group_match"),
        migrations.RemoveField(model_name="pricingrule", name="title_match"),
        migrations.DeleteModel(name="ProjectAddon"),
        migrations.DeleteModel(name="ProjectPriceOption"),
        migrations.AddConstraint(
            model_name="projectoffer",
            constraint=models.UniqueConstraint(condition=models.Q(("package__isnull", False)), fields=("project", "material", "package"), name="uniq_project_material_package_offer"),
        ),
        migrations.AddConstraint(
            model_name="projectoffer",
            constraint=models.UniqueConstraint(condition=models.Q(("package__isnull", True)), fields=("project", "material"), name="uniq_project_material_offer_without_package"),
        ),
        migrations.AddConstraint(
            model_name="projectoptionprice",
            constraint=models.UniqueConstraint(fields=("project", "option"), name="uniq_project_construction_option_price"),
        ),
    ]
