import hashlib
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
from django.db.models import Q


def _norm(value):
    value = str(value or "").casefold().replace("×", "x").replace("х", "x")
    return re.sub(r"\s+", " ", value).strip()


def _stable_code(prefix, title):
    key = _norm(title)
    known = {
        "комплектация дома из бруса \"под усадку\"": "pod-usadku",
        "комплектация дома из бруса 'под усадку'": "pod-usadku",
        "комплектация дома из бруса под усадку": "pod-usadku",
        "под усадку": "pod-usadku",
        "базовая комплектация": "pod-usadku",
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


def _package_spec(package):
    sections = []
    for section in package.sections.all().order_by("sort_order", "id"):
        items = []
        for item in section.items.all().order_by("sort_order", "id"):
            items.append(
                {
                    "title": item.title,
                    "value": item.value,
                    "sort_order": item.sort_order,
                }
            )
        sections.append(
            {
                "title": section.title,
                "sort_order": section.sort_order,
                "items": items,
            }
        )
    return {
        "description": package.description or "",
        "sections": sections,
    }


def _spec_hash(spec):
    raw = json.dumps(spec, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def forwards(apps, schema_editor):
    Project = apps.get_model("catalog", "Project")
    ProjectImage = apps.get_model("catalog", "ProjectImage")
    LegacyPackage = apps.get_model("catalog", "ProjectPackage")
    ProjectOffer = apps.get_model("catalog", "ProjectOffer")
    BuildPackage = apps.get_model("catalog", "BuildPackage")
    BuildPackageSection = apps.get_model("catalog", "BuildPackageSection")
    BuildPackageItem = apps.get_model("catalog", "BuildPackageItem")
    ProjectPackageOverride = apps.get_model("catalog", "ProjectPackageOverride")

    ConstructionOption = apps.get_model("catalog", "ConstructionOption")
    LegacyOptionPrice = apps.get_model("catalog", "ProjectOptionPrice")
    LegacyIllustrated = apps.get_model("catalog", "ProjectIllustratedOption")
    FoundationType = apps.get_model("catalog", "FoundationType")
    RoofCovering = apps.get_model("catalog", "RoofCovering")
    ExtraOption = apps.get_model("catalog", "ExtraOption")
    ProjectFoundation = apps.get_model("catalog", "ProjectFoundation")
    ProjectRoofCovering = apps.get_model("catalog", "ProjectRoofCovering")
    ProjectExtraOption = apps.get_model("catalog", "ProjectExtraOption")
    PricingSettings = apps.get_model("catalog", "PricingSettings")
    PricingRule = apps.get_model("catalog", "PricingRule")

    # 1. Разделяем старый общий флаг индексации допов на три доменных флага.
    Project.objects.filter(addon_price_indexing_disabled=True).update(
        foundation_price_indexing_disabled=True,
        roof_price_indexing_disabled=True,
        extra_price_indexing_disabled=True,
    )

    # 2. Главное изображение становится обычным ProjectImage с is_primary=True.
    for project in Project.objects.all().iterator():
        primary = None
        main_name = getattr(project.main_image, "name", "") if project.main_image else ""
        if main_name:
            primary = ProjectImage.objects.filter(project_id=project.id, image=main_name).first()
            if primary is None:
                primary = ProjectImage.objects.create(
                    project_id=project.id,
                    image=main_name,
                    image_type="facade",
                    is_primary=True,
                    alt_text=project.title,
                    sort_order=0,
                )
            elif not primary.is_primary:
                primary.is_primary = True
                primary.save(update_fields=["is_primary"])
        if primary is None:
            primary = ProjectImage.objects.filter(project_id=project.id).order_by("sort_order", "id").first()
            if primary and not primary.is_primary:
                primary.is_primary = True
                primary.save(update_fields=["is_primary"])
        if primary:
            ProjectImage.objects.filter(project_id=project.id, is_primary=True).exclude(pk=primary.pk).update(
                is_primary=False
            )

    # 3. Глобализируем комплектации. Самый частый состав становится шаблоном,
    #    отличия сохраняются как редкие ProjectPackageOverride.
    groups = defaultdict(list)
    legacy_packages = list(
        LegacyPackage.objects.prefetch_related("sections__items").order_by("id")
    )
    for legacy in legacy_packages:
        groups[_stable_code("package", legacy.title)].append(legacy)

    package_by_legacy_id = {}
    for code, packages in groups.items():
        specs = [(_spec_hash(_package_spec(item)), _package_spec(item)) for item in packages]
        counts = Counter(signature for signature, _ in specs)
        canonical_hash, _ = counts.most_common(1)[0]
        canonical_spec = next(spec for signature, spec in specs if signature == canonical_hash)
        canonical_legacy = next(
            item for item in packages if _spec_hash(_package_spec(item)) == canonical_hash
        )

        package, _ = BuildPackage.objects.update_or_create(
            code=code,
            defaults={
                "title": canonical_legacy.title,
                "description": canonical_spec.get("description", ""),
                "sort_order": canonical_legacy.sort_order,
                "is_active": True,
            },
        )
        BuildPackageSection.objects.filter(package_id=package.id).delete()
        for section_data in canonical_spec.get("sections", []):
            section = BuildPackageSection.objects.create(
                package_id=package.id,
                title=section_data["title"],
                sort_order=section_data.get("sort_order", 0),
            )
            for item_data in section_data.get("items", []):
                BuildPackageItem.objects.create(
                    section_id=section.id,
                    title=item_data["title"],
                    value=item_data.get("value", ""),
                    sort_order=item_data.get("sort_order", 0),
                )

        for legacy in packages:
            package_by_legacy_id[legacy.id] = package.id
            spec = _package_spec(legacy)
            signature = _spec_hash(spec)
            if signature != canonical_hash:
                ProjectPackageOverride.objects.update_or_create(
                    project_id=legacy.project_id,
                    package_id=package.id,
                    defaults={
                        "description": spec.get("description", ""),
                        "sections": spec.get("sections", []),
                        "source_hash": signature,
                    },
                )

    for offer in ProjectOffer.objects.all().iterator():
        package_id = package_by_legacy_id.get(offer.package_id)
        if package_id:
            duplicate = ProjectOffer.objects.filter(
                project_id=offer.project_id,
                material_id=offer.material_id,
                build_package_id=package_id,
            ).exclude(pk=offer.pk).first()
            if duplicate:
                # Предпочитаем непустую/более свежую запись, но не оставляем две
                # одинаковые цены после схлопывания package identity.
                if duplicate.base_price is None and offer.base_price is not None:
                    duplicate.base_price = offer.base_price
                    duplicate.is_price_fixed = offer.is_price_fixed
                    duplicate.note = offer.note
                    duplicate.sort_order = offer.sort_order
                    duplicate.save(update_fields=["base_price", "is_price_fixed", "note", "sort_order"])
                offer.delete()
                continue
            offer.build_package_id = package_id
            offer.save(update_fields=["build_package"])

    default_package = BuildPackage.objects.filter(code="pod-usadku").first()
    if default_package is None and ProjectOffer.objects.filter(build_package__isnull=True).exists():
        default_package = BuildPackage.objects.create(
            code="pod-usadku", title="Под усадку", description="Базовая комплектация", sort_order=10
        )
    if default_package:
        ProjectOffer.objects.filter(build_package__isnull=True, project__construction_type="timber").update(
            build_package_id=default_package.id
        )

    # 4. Разделяем универсальную ConstructionOption на отдельные доменные справочники.
    foundation_by_legacy = {}
    roof_by_legacy = {}
    extra_by_legacy = {}
    for option in ConstructionOption.objects.all().iterator():
        if option.kind == "foundation":
            target, _ = FoundationType.objects.update_or_create(
                code=option.code,
                defaults={"title": option.title, "sort_order": option.sort_order, "is_active": option.is_active},
            )
            foundation_by_legacy[option.id] = target.id
        elif option.kind == "roof":
            target, _ = RoofCovering.objects.update_or_create(
                code=option.code,
                defaults={"title": option.title, "sort_order": option.sort_order, "is_active": option.is_active},
            )
            roof_by_legacy[option.id] = target.id
        else:
            target, _ = ExtraOption.objects.update_or_create(
                code=option.code,
                defaults={"title": option.title, "sort_order": option.sort_order, "is_active": option.is_active},
            )
            extra_by_legacy[option.id] = target.id

    for legacy in LegacyOptionPrice.objects.select_related("option").all().iterator():
        if legacy.option_id in foundation_by_legacy:
            ProjectFoundation.objects.update_or_create(
                project_id=legacy.project_id,
                foundation_id=foundation_by_legacy[legacy.option_id],
                defaults={
                    "base_price_override": legacy.base_price,
                    "is_price_fixed": legacy.is_price_fixed,
                    "description": legacy.description,
                    "sort_order": legacy.sort_order,
                },
            )
        elif legacy.option_id in roof_by_legacy:
            ProjectRoofCovering.objects.update_or_create(
                project_id=legacy.project_id,
                covering_id=roof_by_legacy[legacy.option_id],
                defaults={
                    "base_price_override": legacy.base_price,
                    "is_price_fixed": legacy.is_price_fixed,
                    "description": legacy.description,
                    "sort_order": legacy.sort_order,
                },
            )
        else:
            ProjectExtraOption.objects.update_or_create(
                project_id=legacy.project_id,
                option_id=extra_by_legacy[legacy.option_id],
                defaults={
                    "base_price_override": legacy.base_price,
                    "is_price_fixed": legacy.is_price_fixed,
                    "description": legacy.description,
                    "sort_order": legacy.sort_order,
                },
            )

    # 5. Иллюстрированные опции больше не отдельный ценовой слой: переносим их
    #    картинку/описание в соответствующую связь проекта и справочник.
    for item in LegacyIllustrated.objects.filter(is_active=True).iterator():
        group = _norm(item.group_title)
        code = _stable_code("option", item.title)
        if "фундамент" in group:
            target, _ = FoundationType.objects.get_or_create(code=code, defaults={"title": item.title})
            relation, _ = ProjectFoundation.objects.get_or_create(
                project_id=item.project_id, foundation_id=target.id
            )
            if item.price is not None and relation.base_price_override is None:
                relation.base_price_override = int(item.price)
            if item.description and not relation.description:
                relation.description = item.description
            if item.image and not relation.image_override:
                relation.image_override = item.image.name
            relation.sort_order = item.sort_order
            relation.save()
            if item.image and not target.image:
                target.image = item.image.name
                target.save(update_fields=["image"])
        elif "кров" in group:
            target, _ = RoofCovering.objects.get_or_create(code=code, defaults={"title": item.title})
            relation, _ = ProjectRoofCovering.objects.get_or_create(
                project_id=item.project_id, covering_id=target.id
            )
            if item.price is not None and relation.base_price_override is None:
                relation.base_price_override = int(item.price)
            if item.description and not relation.description:
                relation.description = item.description
            if item.image and not relation.image_override:
                relation.image_override = item.image.name
            relation.sort_order = item.sort_order
            relation.save()
            if item.image and not target.image:
                target.image = item.image.name
                target.save(update_fields=["image"])
        else:
            target, _ = ExtraOption.objects.get_or_create(code=code, defaults={"title": item.title})
            relation, _ = ProjectExtraOption.objects.get_or_create(project_id=item.project_id, option_id=target.id)
            if item.price is not None and relation.base_price_override is None:
                relation.base_price_override = int(item.price)
            if item.description and not relation.description:
                relation.description = item.description
            if item.image and not relation.image_override:
                relation.image_override = item.image.name
            relation.sort_order = item.sort_order
            relation.save()
            if item.image and not target.image:
                target.image = item.image.name
                target.save(update_fields=["image"])

    # 6. Общую индексацию допов размножаем по новым доменным корзинам.
    for settings in PricingSettings.objects.all().iterator():
        settings.foundation_percent = settings.addon_percent
        settings.roof_covering_percent = settings.addon_percent
        settings.extra_percent = settings.addon_percent
        settings.save(update_fields=["foundation_percent", "roof_covering_percent", "extra_percent"])

    for rule in PricingRule.objects.select_related("construction_option").all().iterator():
        option = rule.construction_option
        if not option:
            continue
        if option.kind == "foundation" and option.id in foundation_by_legacy:
            rule.kind = "foundation"
            rule.foundation_id = foundation_by_legacy[option.id]
        elif option.kind == "roof" and option.id in roof_by_legacy:
            rule.kind = "roof_covering"
            rule.roof_covering_id = roof_by_legacy[option.id]
        elif option.id in extra_by_legacy:
            rule.kind = "extra"
            rule.extra_option_id = extra_by_legacy[option.id]
        rule.save(update_fields=["kind", "foundation", "roof_covering", "extra_option"])


def backwards(apps, schema_editor):
    # Миграция специально обратима по схеме, но данные v2 не удаляются при rollback
    # автоматически. Перед откатом пользователь должен восстановить backup БД.
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_normalize_catalog_pricing")]

    operations = [
        migrations.AddField(
            model_name="project",
            name="bathrooms",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Санузлы"),
        ),
        migrations.AddField(
            model_name="project",
            name="terrace_area",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name="Площадь террасы, м²"),
        ),
        migrations.AddField(model_name="project", name="has_balcony", field=models.BooleanField(default=False, verbose_name="Есть балкон")),
        migrations.AddField(model_name="project", name="has_porch", field=models.BooleanField(default=False, verbose_name="Есть крыльцо")),
        migrations.AddField(model_name="project", name="foundation_price_indexing_disabled", field=models.BooleanField(default=False, verbose_name="Не индексировать фундамент")),
        migrations.AddField(model_name="project", name="roof_price_indexing_disabled", field=models.BooleanField(default=False, verbose_name="Не индексировать чистовую кровлю")),
        migrations.AddField(model_name="project", name="extra_price_indexing_disabled", field=models.BooleanField(default=False, verbose_name="Не индексировать прочие доп. работы")),
        migrations.AddField(model_name="projectimage", name="is_primary", field=models.BooleanField(default=False, verbose_name="Главное изображение")),
        migrations.CreateModel(
            name="BuildPackage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={"verbose_name": "Комплектация", "verbose_name_plural": "Комплектации", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="BuildPackageSection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Раздел")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("package", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sections", to="catalog.buildpackage", verbose_name="Комплектация")),
            ],
            options={"verbose_name": "Раздел комплектации", "verbose_name_plural": "Разделы комплектации", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="BuildPackageItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Параметр")),
                ("value", models.TextField(blank=True, verbose_name="Значение")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("section", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="catalog.buildpackagesection", verbose_name="Раздел")),
            ],
            options={"verbose_name": "Пункт комплектации", "verbose_name_plural": "Пункты комплектации", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProjectPackageOverride",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.TextField(blank=True, verbose_name="Описание для проекта")),
                ("sections", models.JSONField(blank=True, default=list, verbose_name="Разделы для проекта")),
                ("source_hash", models.CharField(blank=True, max_length=64, verbose_name="Контрольный хеш")),
                ("package", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_overrides", to="catalog.buildpackage", verbose_name="Комплектация")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="package_overrides", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Исключение комплектации проекта", "verbose_name_plural": "Исключения комплектаций проектов"},
        ),
        migrations.AddField(
            model_name="projectoffer",
            name="build_package",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="offers", to="catalog.buildpackage", verbose_name="Комплектация"),
        ),
        migrations.CreateModel(
            name="ProjectTechnicalData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("roof_area_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Фактическая площадь кровли, м²")),
                ("roof_shape", models.CharField(blank=True, choices=[("gable", "Двускатная"), ("hip", "Вальмовая"), ("mansard", "Ломаная / мансардная"), ("complex", "Сложная"), ("other", "Другая")], max_length=20, verbose_name="Форма крыши")),
                ("roof_pitch_deg", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name="Угол ската, °")),
                ("roof_overhang_m", models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True, verbose_name="Свес кровли, м")),
                ("roof_complexity_factor", models.DecimalField(decimal_places=3, default=Decimal("1.000"), help_text="1.000 — без дополнительной надбавки. Используется только в формульном расчёте кровли.", max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal("0.5")), django.core.validators.MaxValueValidator(Decimal("3"))], verbose_name="Коэффициент сложности кровли")),
                ("notes", models.TextField(blank=True, verbose_name="Технические примечания")),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="technical", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Технические данные проекта", "verbose_name_plural": "Технические данные проектов"},
        ),
        migrations.CreateModel(
            name="FoundationType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("pricing_method", models.CharField(choices=[("reference", "По ценам похожих проектов"), ("per_unit", "Количество × ставка"), ("per_footprint", "Пятно застройки × ставка"), ("fixed", "Фиксированная ставка")], default="reference", max_length=20, verbose_name="Способ расчёта")),
                ("unit_name", models.CharField(blank=True, default="свая", max_length=50, verbose_name="Единица")),
                ("base_rate", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Базовая ставка, ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Минимальная стоимость, ₽")),
                ("image", models.ImageField(blank=True, upload_to="catalog/foundations/", verbose_name="Изображение")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={"verbose_name": "Тип фундамента", "verbose_name_plural": "Типы фундаментов", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="RoofCovering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("rate_per_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Ставка чистовой кровли за м², ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Минимальная стоимость, ₽")),
                ("image", models.ImageField(blank=True, upload_to="catalog/roof_coverings/", verbose_name="Изображение")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={"verbose_name": "Чистовое кровельное покрытие", "verbose_name_plural": "Чистовые кровельные покрытия", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ExtraOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("pricing_method", models.CharField(choices=[("reference", "По ценам похожих проектов"), ("per_unit", "Количество × ставка"), ("per_m2", "Площадь × ставка"), ("fixed", "Фиксированная ставка")], default="reference", max_length=20, verbose_name="Способ расчёта")),
                ("unit_name", models.CharField(blank=True, max_length=50, verbose_name="Единица")),
                ("base_rate", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Базовая ставка, ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Минимальная стоимость, ₽")),
                ("image", models.ImageField(blank=True, upload_to="catalog/extra_options/", verbose_name="Изображение")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={"verbose_name": "Дополнительная работа", "verbose_name_plural": "Дополнительные работы", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProjectFoundation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Количество единиц")),
                ("base_price_override", models.PositiveIntegerField(blank=True, null=True, verbose_name="Базовая цена проекта, ₽")),
                ("is_price_fixed", models.BooleanField(default=False, verbose_name="Фиксированная цена")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("image_override", models.ImageField(blank=True, upload_to="catalog/project_options/", verbose_name="Изображение для проекта")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("foundation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_prices", to="catalog.foundationtype", verbose_name="Фундамент")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="foundations", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Фундамент проекта", "verbose_name_plural": "Фундаменты проектов", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProjectRoofCovering",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("roof_area_override_m2", models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True, verbose_name="Площадь кровли для этого расчёта, м²")),
                ("base_price_override", models.PositiveIntegerField(blank=True, null=True, verbose_name="Базовая цена проекта, ₽")),
                ("is_price_fixed", models.BooleanField(default=False, verbose_name="Фиксированная цена")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("image_override", models.ImageField(blank=True, upload_to="catalog/project_options/", verbose_name="Изображение для проекта")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("covering", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_prices", to="catalog.roofcovering", verbose_name="Покрытие")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="roof_coverings", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Чистовая кровля проекта", "verbose_name_plural": "Чистовая кровля проектов", "ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="ProjectExtraOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name="Количество")),
                ("base_price_override", models.PositiveIntegerField(blank=True, null=True, verbose_name="Базовая цена проекта, ₽")),
                ("is_price_fixed", models.BooleanField(default=False, verbose_name="Фиксированная цена")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("image_override", models.ImageField(blank=True, upload_to="catalog/project_options/", verbose_name="Изображение для проекта")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("option", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="project_prices", to="catalog.extraoption", verbose_name="Работа")),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="extra_options", to="catalog.project", verbose_name="Проект")),
            ],
            options={"verbose_name": "Дополнительная работа проекта", "verbose_name_plural": "Дополнительные работы проектов", "ordering": ["sort_order", "id"]},
        ),
        migrations.AddField(model_name="pricingsettings", name="foundation_percent", field=models.DecimalField(decimal_places=2, default=0, max_digits=7, validators=[django.core.validators.MinValueValidator(-99), django.core.validators.MaxValueValidator(1000)], verbose_name="Фундаменты, %")),
        migrations.AddField(model_name="pricingsettings", name="roof_covering_percent", field=models.DecimalField(decimal_places=2, default=0, max_digits=7, validators=[django.core.validators.MinValueValidator(-99), django.core.validators.MaxValueValidator(1000)], verbose_name="Чистовая кровля, %")),
        migrations.AddField(model_name="pricingsettings", name="extra_percent", field=models.DecimalField(decimal_places=2, default=0, max_digits=7, validators=[django.core.validators.MinValueValidator(-99), django.core.validators.MaxValueValidator(1000)], verbose_name="Прочие работы, %")),
        migrations.AddField(model_name="pricingrule", name="build_package", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.buildpackage", verbose_name="Комплектация дома")),
        migrations.AddField(model_name="pricingrule", name="foundation", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.foundationtype", verbose_name="Фундамент")),
        migrations.AddField(model_name="pricingrule", name="roof_covering", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.roofcovering", verbose_name="Чистовая кровля")),
        migrations.AddField(model_name="pricingrule", name="extra_option", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="pricing_rules", to="catalog.extraoption", verbose_name="Дополнительная работа")),
        migrations.AlterField(model_name="pricingrule", name="kind", field=models.CharField(choices=[("material", "Материал дома"), ("package", "Комплектация дома"), ("foundation", "Фундамент"), ("roof_covering", "Чистовая кровля"), ("extra", "Прочая работа"), ("addon", "[legacy] Дополнительная опция")], max_length=20, verbose_name="Тип")),
        migrations.RemoveConstraint(model_name="projectoffer", name="uniq_project_material_package_offer"),
        migrations.RemoveConstraint(model_name="projectoffer", name="uniq_project_material_offer_without_package"),
        migrations.AddConstraint(model_name="buildpackagesection", constraint=models.UniqueConstraint(fields=("package", "title"), name="uniq_build_package_section")),
        migrations.AddConstraint(model_name="projectpackageoverride", constraint=models.UniqueConstraint(fields=("project", "package"), name="uniq_project_package_override")),
        migrations.AddConstraint(model_name="projectoffer", constraint=models.UniqueConstraint(condition=Q(build_package__isnull=False), fields=("project", "material", "build_package"), name="uniq_v2_project_material_package_offer")),
        migrations.AddConstraint(model_name="projectoffer", constraint=models.UniqueConstraint(condition=Q(build_package__isnull=True), fields=("project", "material"), name="uniq_v2_project_material_offer_without_package")),
        migrations.AddConstraint(model_name="projectfoundation", constraint=models.UniqueConstraint(fields=("project", "foundation"), name="uniq_project_foundation_v2")),
        migrations.AddConstraint(model_name="projectroofcovering", constraint=models.UniqueConstraint(fields=("project", "covering"), name="uniq_project_roof_covering_v2")),
        migrations.AddConstraint(model_name="projectextraoption", constraint=models.UniqueConstraint(fields=("project", "option"), name="uniq_project_extra_v2")),
        # IMPORTANT: the partial unique index for ProjectImage.is_primary is
        # intentionally created in 0009. forwards() updates ProjectImage rows,
        # and PostgreSQL cannot CREATE INDEX on the same table while deferred
        # trigger events from those updates are still pending in this migration
        # transaction. Splitting the index into the next migration gives PostgreSQL
        # a transaction boundary and avoids ObjectInUse.
        migrations.RunPython(forwards, backwards),
    ]
