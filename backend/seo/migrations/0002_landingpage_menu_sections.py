import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("seo", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="landingpage",
            name="page_type",
            field=models.CharField(
                choices=[
                    ("service", "Услуга"),
                    ("size", "Размер"),
                    ("material", "Материал"),
                    ("region", "Регион"),
                    ("delivery", "Доставка"),
                    ("production", "Производство"),
                    ("company", "О компании"),
                    ("guide", "Справочник"),
                    ("custom", "Произвольная"),
                ],
                default="custom",
                max_length=30,
                verbose_name="Тип страницы",
            ),
        ),
        migrations.CreateModel(
            name="LandingPageImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(upload_to="seo/pages/", verbose_name="Изображение"),
                ),
                ("alt_text", models.CharField(blank=True, max_length=255, verbose_name="Alt-текст")),
                ("caption", models.CharField(blank=True, max_length=255, verbose_name="Подпись")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                (
                    "landing_page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="seo.landingpage",
                        verbose_name="SEO-страница",
                    ),
                ),
            ],
            options={
                "verbose_name": "Изображение SEO-страницы",
                "verbose_name_plural": "Изображения SEO-страниц",
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
