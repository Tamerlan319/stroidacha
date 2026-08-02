from django.db import migrations, models


def seed_steps_and_merge_foundations(apps, schema_editor):
    ConstructionStep = apps.get_model("catalog", "ConstructionStep")
    FoundationType = apps.get_model("catalog", "FoundationType")
    ProjectFoundation = apps.get_model("catalog", "ProjectFoundation")

    steps = (
        ("project", "Согласовываем проект", "Выберите готовый проект или пришлите свой.", "blueprint", 10),
        ("contract", "Подписываем договор", "Фиксируем стоимость, комплектацию и сроки.", "contract", 20),
        ("delivery", "Доставляем материалы", "Привозим домокомплект и бригаду на участок.", "truck", 30),
        ("construction", "Строим объект", "Собираем дом или баню по проекту и технологии.", "house", 40),
        ("handover", "Принимаете работу", "Осматриваете объект и подписываете акт.", "shield", 50),
    )
    for code, title, description, icon, sort_order in steps:
        ConstructionStep.objects.update_or_create(
            code=code,
            defaults={
                "title": title,
                "description": description,
                "icon": icon,
                "sort_order": sort_order,
                "is_active": True,
            },
        )

    def normalized(value):
        return " ".join(
            str(value or "")
            .casefold()
            .replace("(", " ")
            .replace(")", " ")
            .replace("гост", "гост")
            .split()
        )

    candidates = [
        item
        for item in FoundationType.objects.all()
        if item.code == "reinforced-piles"
        or normalized(item.title) in {"жб сваи гост", "железобетонные сваи гост"}
    ]
    if not candidates:
        return

    canonical = next((item for item in candidates if item.code == "reinforced-piles"), None)
    if canonical is None:
        canonical = next((item for item in candidates if item.image), candidates[0])
        canonical.code = "reinforced-piles"

    for duplicate in candidates:
        if duplicate.pk == canonical.pk:
            continue

        if not canonical.image and duplicate.image:
            canonical.image = duplicate.image
        if not canonical.description and duplicate.description:
            canonical.description = duplicate.description

        for relation in ProjectFoundation.objects.filter(foundation_id=duplicate.pk):
            existing = ProjectFoundation.objects.filter(
                project_id=relation.project_id,
                foundation_id=canonical.pk,
            ).first()
            if existing:
                changed = []
                if existing.base_price_override is None and relation.base_price_override is not None:
                    existing.base_price_override = relation.base_price_override
                    changed.append("base_price_override")
                if not existing.image_override and relation.image_override:
                    existing.image_override = relation.image_override
                    changed.append("image_override")
                if not existing.description and relation.description:
                    existing.description = relation.description
                    changed.append("description")
                if changed:
                    existing.save(update_fields=changed)
                relation.delete()
            else:
                relation.foundation_id = canonical.pk
                relation.save(update_fields=["foundation"])
        duplicate.delete()

    canonical.title = "ЖБ сваи (ГОСТ)"
    canonical.is_active = True
    canonical.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_exact_cost_domain")]

    operations = [
        migrations.CreateModel(
            name="ConstructionStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("icon", models.CharField(choices=[("blueprint", "Проект"), ("contract", "Договор"), ("truck", "Доставка"), ("house", "Строительство"), ("shield", "Приёмка")], default="blueprint", max_length=30, verbose_name="Иконка")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
            ],
            options={
                "verbose_name": "Этап работы",
                "verbose_name_plural": "Этапы работы",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="SitePromotion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=255, verbose_name="Название")),
                ("description", models.TextField(blank=True, verbose_name="Условия")),
                ("image", models.ImageField(blank=True, upload_to="catalog/promotions/", verbose_name="Изображение")),
                ("button_label", models.CharField(blank=True, default="Узнать подробнее", max_length=80, verbose_name="Текст кнопки")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
            ],
            options={
                "verbose_name": "Акция на странице проекта",
                "verbose_name_plural": "Акции на страницах проектов",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.RunPython(seed_steps_and_merge_foundations, noop_reverse),
    ]
