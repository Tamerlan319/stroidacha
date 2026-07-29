from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_projectcontentsection_projectillustratedoption"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="price_from",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Исходная цена. Цена на сайте рассчитывается с учётом индексации.",
                null=True,
                verbose_name="Базовая цена от, ₽",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="price_indexing_disabled",
            field=models.BooleanField(
                default=False,
                help_text="Включи для акции или проекта с фиксированными ценами.",
                verbose_name="Не применять индексацию цен",
            ),
        ),
        migrations.AlterField(
            model_name="projectpriceoption",
            name="price",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Исходная цена до применения индексации.",
                null=True,
                verbose_name="Базовая цена, ₽",
            ),
        ),
        migrations.AddField(
            model_name="projectpriceoption",
            name="is_price_fixed",
            field=models.BooleanField(
                default=False,
                help_text="Не применять индексацию к этому варианту цены.",
                verbose_name="Фиксированная цена",
            ),
        ),
        migrations.AlterField(
            model_name="projectaddon",
            name="price",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Исходная цена до применения индексации.",
                null=True,
                verbose_name="Базовая цена, ₽",
            ),
        ),
        migrations.AddField(
            model_name="projectaddon",
            name="is_price_fixed",
            field=models.BooleanField(
                default=False,
                help_text="Не применять индексацию к этой опции.",
                verbose_name="Фиксированная цена",
            ),
        ),
        migrations.AlterField(
            model_name="projectpackage",
            name="price_from",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Исходная цена до применения индексации.",
                null=True,
                verbose_name="Базовая цена от, ₽",
            ),
        ),
        migrations.AddField(
            model_name="projectpackage",
            name="is_price_fixed",
            field=models.BooleanField(
                default=False,
                help_text="Не применять индексацию к цене комплектации.",
                verbose_name="Фиксированная цена",
            ),
        ),
        migrations.AlterField(
            model_name="projectillustratedoption",
            name="price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Исходная цена до применения индексации.",
                max_digits=12,
                null=True,
                verbose_name="Базовая цена",
            ),
        ),
        migrations.AddField(
            model_name="projectillustratedoption",
            name="is_price_fixed",
            field=models.BooleanField(
                default=False,
                help_text="Не применять индексацию к этой опции.",
                verbose_name="Фиксированная цена",
            ),
        ),
        migrations.CreateModel(
            name="PricingSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Основная индексация", max_length=120, verbose_name="Название")),
                (
                    "house_percent",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Например: 5 = увеличить все базовые цены домов на 5%; -3 = уменьшить на 3%.",
                        max_digits=7,
                        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
                        verbose_name="Общее изменение цен домов, %",
                    ),
                ),
                (
                    "addon_percent",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Общая индексация фундаментов, кровли и других дополнительных опций.",
                        max_digits=7,
                        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
                        verbose_name="Общее изменение доп. опций, %",
                    ),
                ),
                (
                    "rounding_step",
                    models.PositiveIntegerField(
                        choices=[
                            (100, "до 100 ₽"),
                            (500, "до 500 ₽"),
                            (1000, "до 1 000 ₽"),
                            (5000, "до 5 000 ₽"),
                            (10000, "до 10 000 ₽"),
                        ],
                        default=1000,
                        verbose_name="Округлять итоговые цены",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлена")),
            ],
            options={
                "verbose_name": "Индексация цен",
                "verbose_name_plural": "Индексация цен",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="PricingRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "kind",
                    models.CharField(
                        choices=[("material", "Материал дома"), ("addon", "Дополнительная опция")],
                        max_length=20,
                        verbose_name="Тип",
                    ),
                ),
                ("title", models.CharField(max_length=180, verbose_name="Название правила")),
                (
                    "group_match",
                    models.CharField(
                        blank=True,
                        help_text="Например: Профилированный брус или Фундамент.",
                        max_length=180,
                        verbose_name="Фрагмент группы",
                    ),
                ),
                (
                    "title_match",
                    models.CharField(
                        blank=True,
                        help_text="Например: 145х195 или Свайный.",
                        max_length=180,
                        verbose_name="Фрагмент названия",
                    ),
                ),
                (
                    "percent_change",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=7,
                        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
                        verbose_name="Изменение, %",
                    ),
                ),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                (
                    "settings",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rules",
                        to="catalog.pricingsettings",
                        verbose_name="Профиль индексации",
                    ),
                ),
            ],
            options={
                "verbose_name": "Правило индексации",
                "verbose_name_plural": "Правила индексации",
                "ordering": ["kind", "sort_order", "id"],
            },
        ),
    ]
