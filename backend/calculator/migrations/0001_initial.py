from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CalculatorSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Основной калькулятор", max_length=120, verbose_name="Название профиля")),
                ("min_area", models.PositiveIntegerField(default=20, verbose_name="Минимальная площадь, м²")),
                ("max_area", models.PositiveIntegerField(default=600, verbose_name="Максимальная площадь, м²")),
                ("price_range_percent", models.DecimalField(decimal_places=2, default=8, help_text="Например 8 означает, что результат будет показан как ориентир ±8%.", max_digits=5, verbose_name="Диапазон результата, ±%")),
                ("max_references", models.PositiveSmallIntegerField(default=5, verbose_name="Сколько проектов использовать для сравнения")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлён")),
            ],
            options={
                "verbose_name": "Настройка калькулятора",
                "verbose_name_plural": "Настройки калькулятора",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="CalculatorMaterial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("group_match", models.CharField(help_text="Например: Профилированный брус", max_length=180, verbose_name="Фрагмент группы цены")),
                ("title_match", models.CharField(help_text="Например: 145х145", max_length=180, verbose_name="Фрагмент названия цены")),
                ("fallback_price_per_m2", models.PositiveIntegerField(help_text="Используется только если в каталоге не найдено подходящих проектов.", verbose_name="Резервная цена за м², ₽")),
                ("description", models.CharField(blank=True, max_length=255, verbose_name="Подсказка")),
                ("source_note", models.CharField(blank=True, max_length=255, verbose_name="Источник резервной цены")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активен")),
            ],
            options={
                "verbose_name": "Материал калькулятора",
                "verbose_name_plural": "Материалы калькулятора",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="CalculatorExtraOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(choices=[("foundation", "Фундамент"), ("roof", "Кровля")], max_length=20, verbose_name="Тип")),
                ("code", models.SlugField(max_length=80, unique=True, verbose_name="Код")),
                ("title", models.CharField(max_length=180, verbose_name="Название")),
                ("group_match", models.CharField(help_text="Например: Фундамент или Кровля", max_length=180, verbose_name="Фрагмент группы доп. опции")),
                ("title_match", models.CharField(help_text="Например: Свайный или Металлочерепица", max_length=180, verbose_name="Фрагмент названия доп. опции")),
                ("fallback_price_per_footprint_m2", models.PositiveIntegerField(help_text="Используется только если в каталоге нет сопоставимых цен.", verbose_name="Резервная цена за м² пятна застройки, ₽")),
                ("minimum_price", models.PositiveIntegerField(default=0, verbose_name="Минимальная цена, ₽")),
                ("source_note", models.CharField(blank=True, max_length=255, verbose_name="Источник резервной цены")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активна")),
            ],
            options={
                "verbose_name": "Доп. опция калькулятора",
                "verbose_name_plural": "Доп. опции калькулятора",
                "ordering": ["kind", "sort_order", "id"],
            },
        ),
    ]
