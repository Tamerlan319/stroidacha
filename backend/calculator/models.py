from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from catalog.models import (
    BuildPackage,
    ConstructionOption,
    FoundationType,
    Material,
    RoofCovering,
)


class CalculatorSettings(models.Model):
    title = models.CharField("Название профиля", max_length=120, default="Основной калькулятор")
    min_area = models.PositiveIntegerField("Минимальная площадь, м²", default=20)
    max_area = models.PositiveIntegerField("Максимальная площадь, м²", default=600)
    price_range_percent = models.DecimalField(
        "Диапазон результата, ±%",
        max_digits=5,
        decimal_places=2,
        default=8,
        help_text="Маркетинговый диапазон вокруг расчётной точки.",
    )
    max_references = models.PositiveSmallIntegerField(
        "Legacy: проектов для сравнения", default=5,
        help_text="Больше не участвует в цене. Оставлено до cleanup-миграции.",
    )
    default_package = models.ForeignKey(
        BuildPackage,
        verbose_name="Комплектация по умолчанию",
        related_name="calculator_profiles",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField("Активен", default=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Настройка калькулятора"
        verbose_name_plural = "Настройки калькулятора"
        ordering = ["id"]

    def __str__(self):
        return self.title


class HouseCostProfile(models.Model):
    """Сметная модель базовой комплектации дома.

    Runtime-цена считается из ведомости объёмов (BOQ). ProjectOffer используется
    только для офлайн-калибровки и контрольного сравнения.
    """

    title = models.CharField("Название", max_length=120, default="Под усадку — сметная модель")
    package = models.OneToOneField(
        BuildPackage,
        verbose_name="Комплектация",
        related_name="cost_profile",
        on_delete=models.PROTECT,
    )

    # Геометрия стен и перегородок.
    first_floor_height_m = models.DecimalField(
        "Высота 1-го этажа, м", max_digits=4, decimal_places=2, default=Decimal("2.70")
    )
    second_floor_height_m = models.DecimalField(
        "Высота 2-го этажа, м", max_digits=4, decimal_places=2, default=Decimal("2.50")
    )
    mansard_knee_wall_height_m = models.DecimalField(
        "Добавочная высота брусовой стены мансарды, м",
        max_digits=4,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Фронтоны считаются отдельно как каркасно-щитовые; сюда ставится только реальная брусовая коленная стена, если она есть.",
    )
    external_openings_ratio = models.DecimalField(
        "Проёмы наружных стен, доля",
        max_digits=4,
        decimal_places=3,
        default=Decimal("0.120"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("0.5"))],
    )
    internal_wall_length_per_m2 = models.DecimalField(
        "Перегородки: м длины на 1 м² площади",
        max_digits=5,
        decimal_places=3,
        default=Decimal("0.150"),
    )
    internal_wall_length_per_bedroom_m = models.DecimalField(
        "Доп. перегородки на спальню, м",
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.50"),
    )
    partition_height_m = models.DecimalField(
        "Средняя высота перегородок, м", max_digits=4, decimal_places=2, default=Decimal("2.60")
    )
    internal_openings_ratio = models.DecimalField(
        "Проёмы перегородок, доля",
        max_digits=4,
        decimal_places=3,
        default=Decimal("0.080"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("0.5"))],
    )

    # Конструктив из пиломатериала. Значения по умолчанию соответствуют опубликованной
    # базовой комплектации старого сайта: балки 100x150 и стропила 50x150 с шагом 590 мм.
    joist_spacing_m = models.DecimalField(
        "Шаг балок, м", max_digits=4, decimal_places=3, default=Decimal("0.590")
    )
    joist_section_width_mm = models.PositiveSmallIntegerField("Балка: ширина, мм", default=100)
    joist_section_height_mm = models.PositiveSmallIntegerField("Балка: высота, мм", default=150)
    joist_systems_one_floor = models.DecimalField(
        "Комплектов балок: 1 этаж", max_digits=3, decimal_places=1, default=Decimal("1.0")
    )
    joist_systems_mansard = models.DecimalField(
        "Комплектов балок: 1,5 этажа", max_digits=3, decimal_places=1, default=Decimal("2.0")
    )
    joist_systems_two_floor = models.DecimalField(
        "Комплектов балок: 2 этажа", max_digits=3, decimal_places=1, default=Decimal("2.0")
    )

    rafter_spacing_m = models.DecimalField(
        "Шаг стропил, м", max_digits=4, decimal_places=3, default=Decimal("0.590")
    )
    rafter_section_width_mm = models.PositiveSmallIntegerField("Стропила: ширина, мм", default=50)
    rafter_section_height_mm = models.PositiveSmallIntegerField("Стропила: высота, мм", default=150)
    tie_section_width_mm = models.PositiveSmallIntegerField("Ригель: ширина, мм", default=50)
    tie_section_height_mm = models.PositiveSmallIntegerField("Ригель: высота, мм", default=150)
    tie_length_factor = models.DecimalField(
        "Длина ригеля к пролёту, коэффициент", max_digits=4, decimal_places=2, default=Decimal("1.00")
    )
    counter_batten_width_mm = models.PositiveSmallIntegerField("Контробрешётка: ширина, мм", default=50)
    counter_batten_height_mm = models.PositiveSmallIntegerField("Контробрешётка: высота, мм", default=50)
    lathing_volume_per_roof_m2 = models.DecimalField(
        "Обрешётка: м³ на 1 м² кровли",
        max_digits=6,
        decimal_places=4,
        default=Decimal("0.0060"),
        help_text="Эквивалентный расход доски обрешётки на квадратный метр ската.",
    )

    default_roof_pitch_deg = models.DecimalField(
        "Угол двускатной крыши по умолчанию, °", max_digits=5, decimal_places=2, default=Decimal("35")
    )
    default_roof_overhang_m = models.DecimalField(
        "Свес кровли по умолчанию, м", max_digits=4, decimal_places=2, default=Decimal("0.50")
    )

    # Денежные ставки. Нулевые значения намеренны: после миграции их нужно получить
    # калибровкой или внести из реального офисного прайса.
    structural_lumber_rate_per_m3 = models.DecimalField(
        "Пиломатериал конструкций, ₽/м³", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    gable_cladding_rate_per_m2 = models.DecimalField(
        "Фронтоны (каркас + имитация), ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    temporary_roof_rate_per_m2 = models.DecimalField(
        "Временная кровля/мембрана, ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    consumables_rate_per_wall_m3 = models.DecimalField(
        "Джут, нагели, крепёж и обработка, ₽/м³ стен", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    first_floor_assembly_rate_per_m2 = models.DecimalField(
        "Сборка: 1-й этаж, ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    mansard_assembly_rate_per_m2 = models.DecimalField(
        "Сборка: мансарда, ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    second_floor_assembly_rate_per_m2 = models.DecimalField(
        "Сборка: 2-й этаж, ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    terrace_rate_per_m2 = models.DecimalField(
        "Терраса в базовой комплектации, ₽/м²", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    fixed_package_cost = models.DecimalField(
        "Фиксированная часть, ₽",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        help_text="Доставка, проектная документация и прочие условно-постоянные расходы.",
    )

    calibration_samples = models.PositiveIntegerField("Выборка калибровки", default=0)
    calibration_mape = models.DecimalField(
        "Средняя ошибка калибровки, %", max_digits=6, decimal_places=2, null=True, blank=True
    )
    calibrated_at = models.DateTimeField("Последняя калибровка", null=True, blank=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Сметная модель дома"
        verbose_name_plural = "Сметные модели дома"
        ordering = ["id"]

    def __str__(self):
        return self.title


class CalculatorMaterial(models.Model):
    material = models.OneToOneField(
        Material,
        verbose_name="Материал каталога",
        related_name="calculator_config",
        on_delete=models.CASCADE,
    )
    # Legacy fallback оставлен для совместимости, но V3 не использует его для цены дома.
    fallback_price_per_m2 = models.PositiveIntegerField("Legacy: резервная цена за м², ₽", default=0)

    wall_thickness_mm = models.PositiveSmallIntegerField("Толщина наружной стены, мм", default=150)
    partition_thickness_mm = models.PositiveSmallIntegerField("Толщина перегородки, мм", default=100)
    wall_rate_per_m3 = models.DecimalField(
        "Стеновой материал, ₽/м³", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    partition_rate_per_m3 = models.DecimalField(
        "Материал перегородок, ₽/м³", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    wall_waste_percent = models.DecimalField(
        "Запас материала, %", max_digits=5, decimal_places=2, default=Decimal("5")
    )

    description = models.CharField("Подсказка", max_length=255, blank=True)
    source_note = models.CharField("Источник ставки", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Материал калькулятора"
        verbose_name_plural = "Материалы калькулятора"
        ordering = ["sort_order", "id"]

    @property
    def code(self):
        return self.material.code

    @property
    def title(self):
        return self.material.title

    def __str__(self):
        return self.material.title


class CalculatorFoundation(models.Model):
    foundation = models.OneToOneField(
        FoundationType,
        verbose_name="Фундамент каталога",
        related_name="calculator_config",
        on_delete=models.CASCADE,
    )
    fallback_price_per_footprint_m2 = models.PositiveIntegerField("Legacy fallback, ₽/м²", default=0)
    minimum_price = models.PositiveIntegerField("Резервный минимум, ₽", default=0)
    pile_spacing_m = models.DecimalField(
        "Максимальный шаг свай, м", max_digits=4, decimal_places=2, default=Decimal("2.50")
    )
    base_extra_price = models.DecimalField(
        "Постоянная добавка к фундаменту, ₽", max_digits=12, decimal_places=2, default=Decimal("0")
    )
    source_note = models.CharField("Источник ставки", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Фундамент калькулятора"
        verbose_name_plural = "Фундаменты калькулятора"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.foundation.title


class CalculatorRoofCovering(models.Model):
    covering = models.OneToOneField(
        RoofCovering,
        verbose_name="Покрытие каталога",
        related_name="calculator_config",
        on_delete=models.CASCADE,
    )
    fallback_price_per_footprint_m2 = models.PositiveIntegerField("Legacy fallback, ₽/м²", default=0)
    minimum_price = models.PositiveIntegerField("Резервный минимум, ₽", default=0)
    source_note = models.CharField("Источник ставки", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Чистовая кровля калькулятора"
        verbose_name_plural = "Чистовая кровля калькулятора"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.covering.title


# LEGACY: физически остаётся до cleanup после audit_catalog_v2.
class CalculatorExtraOption(models.Model):
    construction_option = models.OneToOneField(
        ConstructionOption,
        verbose_name="Опция каталога",
        related_name="calculator_config",
        on_delete=models.CASCADE,
    )
    fallback_price_per_footprint_m2 = models.PositiveIntegerField("Legacy fallback, ₽/м²", default=0)
    minimum_price = models.PositiveIntegerField("Минимальная цена, ₽", default=0)
    source_note = models.CharField("Источник резервной цены", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Доп. опция калькулятора"
        verbose_name_plural = "Доп. опции калькулятора"
        ordering = ["construction_option__kind", "sort_order", "id"]
