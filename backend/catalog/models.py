from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class ProjectCategory(models.Model):
    title = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL-ключ", unique=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категория проекта"
        verbose_name_plural = "Категории проектов"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class Material(models.Model):
    class Kind(models.TextChoices):
        REGULAR = "regular", "Обычный брус"
        PROFILED = "profiled", "Профилированный брус"
        DRY = "dry", "Брус камерной сушки"
        OTHER = "other", "Другое"

    code = models.SlugField("Код", max_length=80, unique=True)
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.OTHER)
    group_title = models.CharField("Группа", max_length=120)
    title = models.CharField("Название", max_length=180)
    section_width_mm = models.PositiveSmallIntegerField("Сечение, ширина, мм", null=True, blank=True)
    section_height_mm = models.PositiveSmallIntegerField("Сечение, высота, мм", null=True, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class BuildPackage(models.Model):
    """Глобальный вид комплектации.

    Это идентичность комплектации (например «Под усадку»), а не цена конкретного
    проекта. Стоимость хранится только в ProjectOffer.
    """

    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Комплектация"
        verbose_name_plural = "Комплектации"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class BuildPackageSection(models.Model):
    package = models.ForeignKey(
        BuildPackage,
        verbose_name="Комплектация",
        related_name="sections",
        on_delete=models.CASCADE,
    )
    title = models.CharField("Раздел", max_length=255)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Раздел комплектации"
        verbose_name_plural = "Разделы комплектации"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["package", "title"], name="uniq_build_package_section")
        ]

    def __str__(self):
        return f"{self.package.title} — {self.title}"


class BuildPackageItem(models.Model):
    section = models.ForeignKey(
        BuildPackageSection,
        verbose_name="Раздел",
        related_name="items",
        on_delete=models.CASCADE,
    )
    title = models.CharField("Параметр", max_length=255)
    value = models.TextField("Значение", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Пункт комплектации"
        verbose_name_plural = "Пункты комплектации"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.title}: {self.value[:50]}"


class Project(models.Model):
    class ConstructionType(models.TextChoices):
        TIMBER = "timber", "Брус"
        FRAME = "frame", "Каркас"
        LOG = "log", "Бревно"
        OTHER = "other", "Другое"

    external_id = models.CharField(
        "Код проекта из Excel",
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Например: DB-01, BATH-02, GARAGE-03",
    )
    title = models.CharField("Название", max_length=255)
    slug = models.SlugField("URL-ключ", unique=True, blank=True, allow_unicode=True)
    category = models.ForeignKey(
        ProjectCategory,
        verbose_name="Категория",
        related_name="projects",
        on_delete=models.PROTECT,
    )
    construction_type = models.CharField(
        "Тип строительства",
        max_length=30,
        choices=ConstructionType.choices,
        default=ConstructionType.TIMBER,
    )
    area = models.DecimalField("Площадь, м²", max_digits=8, decimal_places=2, null=True, blank=True)
    floors = models.DecimalField(
        "Этажность числом",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Например: 1, 1.5, 2",
    )
    # LEGACY: поля ниже пока остаются физически в БД для безопасного отката.
    # API и новый код их не используют как источник истины.
    floor_label = models.CharField(
        "Этажность текстом",
        max_length=100,
        blank=True,
        help_text="Например: Полутораэтажный, Одноэтажный, Двухэтажный",
    )
    bedrooms = models.PositiveSmallIntegerField("Спальни", null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField("Санузлы", null=True, blank=True)
    width = models.DecimalField("Ширина, м", max_digits=6, decimal_places=2, null=True, blank=True)
    length = models.DecimalField("Длина, м", max_digits=6, decimal_places=2, null=True, blank=True)
    size_text = models.CharField(
        "Размер текстом",
        max_length=50,
        blank=True,
        help_text="Например: 6х6, 6х8, 8х9",
    )
    terrace_area = models.DecimalField(
        "Площадь террасы, м²", max_digits=7, decimal_places=2, null=True, blank=True
    )
    has_balcony = models.BooleanField("Есть балкон", default=False)
    has_porch = models.BooleanField("Есть крыльцо", default=False)
    price_from = models.PositiveIntegerField(
        "Базовая цена от, ₽",
        null=True,
        blank=True,
        help_text="Исходная цена. Цена на сайте рассчитывается с учётом индексации.",
    )

    price_indexing_disabled = models.BooleanField(
        "Не индексировать цены дома",
        default=False,
        help_text="Не применять индексацию к стоимости дома и материалам этого проекта.",
    )
    addon_price_indexing_disabled = models.BooleanField(
        "Не индексировать дополнительные опции",
        default=False,
        help_text="Отдельно фиксирует фундамент, кровлю и другие дополнительные опции проекта.",
    )
    foundation_price_indexing_disabled = models.BooleanField(
        "Не индексировать фундамент", default=False
    )
    roof_price_indexing_disabled = models.BooleanField(
        "Не индексировать чистовую кровлю", default=False
    )
    extra_price_indexing_disabled = models.BooleanField(
        "Не индексировать прочие доп. работы", default=False
    )

    build_days_from = models.PositiveSmallIntegerField("Срок строительства от, дней", null=True, blank=True)
    build_days_to = models.PositiveSmallIntegerField("Срок строительства до, дней", null=True, blank=True)
    short_description = models.TextField("Краткое описание", blank=True)
    description = models.TextField("Полное описание", blank=True)
    main_image = models.ImageField(
        "Главное изображение",
        upload_to="projects/main/",
        null=True,
        blank=True,
    )
    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)
    is_active = models.BooleanField("Показывать на сайте", default=True)
    is_featured = models.BooleanField("Рекомендуемый проект", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлён", auto_now=True)

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            source = self.external_id or self.title
            base_slug = slugify(source, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def footprint_area(self) -> Decimal | None:
        if self.width is None or self.length is None:
            return None
        return Decimal(self.width) * Decimal(self.length)

    @property
    def computed_size_text(self) -> str:
        if self.width is None or self.length is None:
            return self.size_text or ""

        # width/length хранятся как NUMERIC(6,2), поэтому Decimal всегда
        # приходит с двумя знаками после точки (Decimal("6.00")). В отличие
        # от float, format(decimal, "g") незначащие нули не убирает — отсюда
        # раньше на карточках отображалось "6.00х7.00" вместо "6х7".
        # normalize() + fixed-point убирает лишние нули и не даёт
        # normalize() уйти в экспоненциальную запись на круглых числах
        # (например, 60.00 → "6E+1" без явного "f").
        def format_dimension(value: Decimal) -> str:
            return format(Decimal(value).normalize(), "f")

        return f"{format_dimension(self.width)}х{format_dimension(self.length)}"

    @property
    def computed_floor_label(self) -> str:
        if self.floors is None:
            return self.floor_label or ""
        floors = Decimal(self.floors)
        if floors == Decimal("1"):
            return "Одноэтажный"
        if floors == Decimal("1.5"):
            return "Полутораэтажный"
        if floors == Decimal("2"):
            return "Двухэтажный"
        if floors == floors.to_integral_value():
            return f"{int(floors)} этажа"
        return f"{floors:g} этажа"


class ProjectTechnicalData(models.Model):
    """Технический паспорт проекта.

    Это источник точных количеств для сметного движка. Поля могут быть заполнены
    вручную менеджером/инженером, извлечены из планировки или рассчитаны как
    предварительные. `is_verified=True` означает, что количествам можно доверять
    при сравнении расчётной сметы с коммерческой ценой каталога.
    """

    class RoofShape(models.TextChoices):
        GABLE = "gable", "Двускатная"
        HIP = "hip", "Вальмовая"
        MANSARD = "mansard", "Ломаная / мансардная"
        COMPLEX = "complex", "Сложная"
        OTHER = "other", "Другая"

    class DataSource(models.TextChoices):
        CALCULATED = "calculated", "Рассчитано автоматически"
        MANUAL = "manual", "Внесено вручную"
        PLAN = "plan", "Получено из планировки"
        ESTIMATE = "estimate", "Из рабочей сметы"
        IMPORT = "import", "Импортировано"

    project = models.OneToOneField(
        Project,
        verbose_name="Проект",
        related_name="technical",
        on_delete=models.CASCADE,
    )
    data_source = models.CharField(
        "Источник данных", max_length=20, choices=DataSource.choices,
        default=DataSource.CALCULATED,
    )
    is_verified = models.BooleanField(
        "Технические данные проверены", default=False,
        help_text="Включайте после проверки менеджером/инженером.",
    )
    verified_at = models.DateTimeField("Проверено", null=True, blank=True)

    # Площади этажей. Если не заданы, быстрый калькулятор распределяет общую
    # площадь по пятну застройки.
    first_floor_area_m2 = models.DecimalField(
        "Площадь 1-го этажа, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    mansard_area_m2 = models.DecimalField(
        "Площадь мансарды, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    second_floor_area_m2 = models.DecimalField(
        "Площадь 2-го этажа, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )

    # Стены и перегородки. Объёмы имеют приоритет над длинами/площадями в точном режиме.
    external_wall_length_m = models.DecimalField(
        "Длина наружных стен, м", max_digits=9, decimal_places=2, null=True, blank=True
    )
    external_wall_height_m = models.DecimalField(
        "Расчётная высота наружных стен, м", max_digits=6, decimal_places=2, null=True, blank=True
    )
    external_openings_area_m2 = models.DecimalField(
        "Окна и двери наружных стен, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    internal_wall_length_m = models.DecimalField(
        "Длина внутренних перегородок, м", max_digits=9, decimal_places=2, null=True, blank=True
    )
    internal_wall_height_m = models.DecimalField(
        "Средняя высота перегородок, м", max_digits=6, decimal_places=2, null=True, blank=True
    )
    internal_openings_area_m2 = models.DecimalField(
        "Проёмы внутренних перегородок, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )

    # Конструкционный пиломатериал. Разделён, чтобы каждая позиция имела свою ставку.
    beams_volume_m3 = models.DecimalField(
        "Балки/лаги, м³", max_digits=10, decimal_places=3, null=True, blank=True
    )
    rafters_volume_m3 = models.DecimalField(
        "Стропила/ригели, м³", max_digits=10, decimal_places=3, null=True, blank=True
    )
    lathing_volume_m3 = models.DecimalField(
        "Обрешётка/контробрешётка, м³", max_digits=10, decimal_places=3, null=True, blank=True
    )
    other_structural_lumber_volume_m3 = models.DecimalField(
        "Прочий конструкционный пиломатериал, м³",
        max_digits=10, decimal_places=3, null=True, blank=True,
    )

    gable_area_m2 = models.DecimalField(
        "Площадь фронтонов, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    roof_area_m2 = models.DecimalField(
        "Фактическая площадь кровли, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    terrace_area_m2 = models.DecimalField(
        "Площадь террас в комплектации, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    roof_shape = models.CharField(
        "Форма крыши", max_length=20, choices=RoofShape.choices, blank=True
    )
    roof_pitch_deg = models.DecimalField(
        "Угол ската, °", max_digits=5, decimal_places=2, null=True, blank=True
    )
    roof_overhang_m = models.DecimalField(
        "Свес кровли, м", max_digits=4, decimal_places=2, null=True, blank=True
    )
    roof_complexity_factor = models.DecimalField(
        "Коэффициент сложности кровли",
        max_digits=5,
        decimal_places=3,
        default=Decimal("1.000"),
        validators=[MinValueValidator(Decimal("0.5")), MaxValueValidator(Decimal("3"))],
        help_text="1.000 — без дополнительной надбавки. Используется для чистового покрытия.",
    )
    notes = models.TextField("Технические примечания", blank=True)

    class Meta:
        verbose_name = "Технический паспорт проекта"
        verbose_name_plural = "Технические паспорта проектов"

    def __str__(self):
        return f"Технический паспорт — {self.project.title}"

    def save(self, *args, **kwargs):
        if self.is_verified and self.verified_at is None:
            self.verified_at = timezone.now()
        elif not self.is_verified:
            self.verified_at = None
        super().save(*args, **kwargs)

    @property
    def structural_lumber_volume_m3(self) -> Decimal | None:
        values = [
            self.beams_volume_m3, self.rafters_volume_m3, self.lathing_volume_m3,
            self.other_structural_lumber_volume_m3,
        ]
        present = [Decimal(v) for v in values if v is not None]
        return sum(present, Decimal("0")) if present else None

    @property
    def completeness_percent(self) -> int:
        fields = (
            "external_wall_length_m", "external_wall_height_m", "external_openings_area_m2",
            "internal_wall_length_m", "internal_wall_height_m",
            "beams_volume_m3", "rafters_volume_m3", "lathing_volume_m3",
            "gable_area_m2", "roof_area_m2",
        )
        filled = sum(getattr(self, name) is not None for name in fields)
        return round(filled / len(fields) * 100)


class ProjectMaterialTakeoff(models.Model):
    """Точная кубатура стен для конкретного материала проекта.

    Кубатуру нельзя хранить только в ProjectTechnicalData: при переходе с 150 мм
    на 200 мм геометрия проекта та же, а объём бруса меняется. Поэтому точные
    объёмы стен привязаны к паре Project + Material.
    """

    project = models.ForeignKey(
        Project, verbose_name="Проект", related_name="material_takeoffs", on_delete=models.CASCADE
    )
    material = models.ForeignKey(
        Material, verbose_name="Материал", related_name="project_takeoffs", on_delete=models.PROTECT
    )
    external_wall_volume_m3 = models.DecimalField(
        "Наружные стены, м³", max_digits=10, decimal_places=3
    )
    internal_wall_volume_m3 = models.DecimalField(
        "Перегородки, м³", max_digits=10, decimal_places=3, default=Decimal("0")
    )
    includes_waste = models.BooleanField(
        "Запас уже включён в объём", default=True,
        help_text="Если включено, калькулятор не добавляет процент запаса CalculatorMaterial повторно.",
    )
    data_source = models.CharField(
        "Источник данных", max_length=20, choices=ProjectTechnicalData.DataSource.choices,
        default=ProjectTechnicalData.DataSource.ESTIMATE,
    )
    is_verified = models.BooleanField("Проверено", default=False)
    verified_at = models.DateTimeField("Проверено", null=True, blank=True)
    notes = models.TextField("Примечание", blank=True)

    class Meta:
        verbose_name = "Кубатура стен по материалу"
        verbose_name_plural = "Кубатура стен по материалам"
        constraints = [
            models.UniqueConstraint(fields=["project", "material"], name="uniq_project_material_takeoff")
        ]

    def __str__(self):
        return f"{self.project.title} — {self.material.title}"

    def save(self, *args, **kwargs):
        if self.is_verified and self.verified_at is None:
            self.verified_at = timezone.now()
        elif not self.is_verified:
            self.verified_at = None
        super().save(*args, **kwargs)


class ProjectImage(models.Model):
    class ImageType(models.TextChoices):
        FACADE = "facade", "Фасад"
        GALLERY = "gallery", "Галерея"
        DETAIL = "detail", "Деталь"
        INTERIOR = "interior", "Интерьер"
        OTHER = "other", "Другое"

    project = models.ForeignKey(Project, verbose_name="Проект", related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("Изображение", upload_to="projects/gallery/")
    image_type = models.CharField(
        "Тип изображения", max_length=30, choices=ImageType.choices, default=ImageType.GALLERY
    )
    is_primary = models.BooleanField("Главное изображение", default=False)
    caption = models.CharField("Подпись", max_length=255, blank=True)
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото проекта"
        verbose_name_plural = "Фото проекта"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project"], condition=Q(is_primary=True), name="uniq_primary_image_per_project"
            )
        ]

    def __str__(self):
        return f"Фото: {self.project.title}"

    def save(self, *args, **kwargs):
        if self.is_primary and self.project_id:
            ProjectImage.objects.filter(project_id=self.project_id, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)


class ProjectPlan(models.Model):
    project = models.ForeignKey(Project, verbose_name="Проект", related_name="plans", on_delete=models.CASCADE)
    title = models.CharField("Название", max_length=255, default="Планировка")
    image = models.ImageField("Планировка", upload_to="projects/plans/")
    floor = models.PositiveSmallIntegerField("Этаж", default=1)
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Планировка"
        verbose_name_plural = "Планировки"
        ordering = ["sort_order", "floor"]

    def __str__(self):
        return f"{self.project.title} — {self.title}"


class ProjectPackageOverride(models.Model):
    """Редкая проектная поправка к глобальной комплектации.

    Большинство проектов используют BuildPackage.sections. JSON хранится только если
    старый каталог содержал отличающийся состав для конкретного проекта.
    """

    project = models.ForeignKey(
        Project, verbose_name="Проект", related_name="package_overrides", on_delete=models.CASCADE
    )
    package = models.ForeignKey(
        BuildPackage, verbose_name="Комплектация", related_name="project_overrides", on_delete=models.CASCADE
    )
    description = models.TextField("Описание для проекта", blank=True)
    sections = models.JSONField("Разделы для проекта", default=list, blank=True)
    source_hash = models.CharField("Контрольный хеш", max_length=64, blank=True)

    class Meta:
        verbose_name = "Исключение комплектации проекта"
        verbose_name_plural = "Исключения комплектаций проектов"
        constraints = [
            models.UniqueConstraint(fields=["project", "package"], name="uniq_project_package_override")
        ]

    def __str__(self):
        return f"{self.project.title} — {self.package.title}"


class ProjectOffer(models.Model):
    project = models.ForeignKey(Project, verbose_name="Проект", related_name="offers", on_delete=models.CASCADE)
    material = models.ForeignKey(
        Material, verbose_name="Материал", related_name="project_offers", on_delete=models.PROTECT
    )
    # Старый FK остаётся только до финальной cleanup-миграции.
    package = models.ForeignKey(
        "ProjectPackage",
        verbose_name="Комплектация",
        related_name="offers",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Можно оставить пустым, если цена не привязана к конкретной комплектации.",
    )
    build_package = models.ForeignKey(
        BuildPackage,
        verbose_name="Комплектация",
        related_name="offers",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    base_price = models.PositiveIntegerField("Базовая цена, ₽", null=True, blank=True)
    is_price_fixed = models.BooleanField(
        "Фиксированная цена",
        default=False,
        help_text="Не применять индексацию к этой цене.",
    )
    note = models.CharField("Примечание", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Предложение проекта"
        verbose_name_plural = "Цены по материалам и комплектациям"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "material", "build_package"],
                condition=Q(build_package__isnull=False),
                name="uniq_v2_project_material_package_offer",
            ),
            models.UniqueConstraint(
                fields=["project", "material"],
                condition=Q(build_package__isnull=True),
                name="uniq_v2_project_material_offer_without_package",
            ),
        ]

    def __str__(self):
        package = self.build_package or (self.package if self.package_id else None)
        suffix = f" / {package.title}" if package else ""
        return f"{self.project.title} — {self.material.title}{suffix}"


class FoundationType(models.Model):
    class PricingMethod(models.TextChoices):
        REFERENCE = "reference", "По ценам похожих проектов"
        PER_UNIT = "per_unit", "Количество × ставка"
        PER_FOOTPRINT = "per_footprint", "Пятно застройки × ставка"
        FIXED = "fixed", "Фиксированная ставка"

    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=180)
    pricing_method = models.CharField(
        "Способ расчёта", max_length=20, choices=PricingMethod.choices, default=PricingMethod.REFERENCE
    )
    unit_name = models.CharField("Единица", max_length=50, blank=True, default="свая")
    base_rate = models.DecimalField(
        "Базовая ставка, ₽", max_digits=12, decimal_places=2, null=True, blank=True
    )
    minimum_price = models.PositiveIntegerField("Минимальная стоимость, ₽", default=0)
    image = models.ImageField("Изображение", upload_to="catalog/foundations/", blank=True)
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Тип фундамента"
        verbose_name_plural = "Типы фундаментов"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class RoofCovering(models.Model):
    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=180)
    rate_per_m2 = models.DecimalField(
        "Ставка чистовой кровли за м², ₽", max_digits=12, decimal_places=2, null=True, blank=True
    )
    minimum_price = models.PositiveIntegerField("Минимальная стоимость, ₽", default=0)
    image = models.ImageField("Изображение", upload_to="catalog/roof_coverings/", blank=True)
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Чистовое кровельное покрытие"
        verbose_name_plural = "Чистовые кровельные покрытия"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class ExtraOption(models.Model):
    class PricingMethod(models.TextChoices):
        REFERENCE = "reference", "По ценам похожих проектов"
        PER_UNIT = "per_unit", "Количество × ставка"
        PER_M2 = "per_m2", "Площадь × ставка"
        FIXED = "fixed", "Фиксированная ставка"

    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=180)
    pricing_method = models.CharField(
        "Способ расчёта", max_length=20, choices=PricingMethod.choices, default=PricingMethod.REFERENCE
    )
    unit_name = models.CharField("Единица", max_length=50, blank=True)
    base_rate = models.DecimalField(
        "Базовая ставка, ₽", max_digits=12, decimal_places=2, null=True, blank=True
    )
    minimum_price = models.PositiveIntegerField("Минимальная стоимость, ₽", default=0)
    image = models.ImageField("Изображение", upload_to="catalog/extra_options/", blank=True)
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Дополнительная работа"
        verbose_name_plural = "Дополнительные работы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class ProjectFoundation(models.Model):
    project = models.ForeignKey(
        Project, verbose_name="Проект", related_name="foundations", on_delete=models.CASCADE
    )
    foundation = models.ForeignKey(
        FoundationType, verbose_name="Фундамент", related_name="project_prices", on_delete=models.PROTECT
    )
    quantity = models.DecimalField(
        "Количество единиц", max_digits=10, decimal_places=2, null=True, blank=True
    )
    base_price_override = models.PositiveIntegerField(
        "Базовая цена проекта, ₽", null=True, blank=True
    )
    is_price_fixed = models.BooleanField("Фиксированная цена", default=False)
    description = models.TextField("Описание", blank=True)
    image_override = models.ImageField("Изображение для проекта", upload_to="catalog/project_options/", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фундамент проекта"
        verbose_name_plural = "Фундаменты проектов"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "foundation"], name="uniq_project_foundation_v2")
        ]

    def __str__(self):
        return f"{self.project.title} — {self.foundation.title}"


class ProjectRoofCovering(models.Model):
    project = models.ForeignKey(
        Project, verbose_name="Проект", related_name="roof_coverings", on_delete=models.CASCADE
    )
    covering = models.ForeignKey(
        RoofCovering, verbose_name="Покрытие", related_name="project_prices", on_delete=models.PROTECT
    )
    roof_area_override_m2 = models.DecimalField(
        "Площадь кровли для этого расчёта, м²", max_digits=9, decimal_places=2, null=True, blank=True
    )
    base_price_override = models.PositiveIntegerField(
        "Базовая цена проекта, ₽", null=True, blank=True
    )
    is_price_fixed = models.BooleanField("Фиксированная цена", default=False)
    description = models.TextField("Описание", blank=True)
    image_override = models.ImageField("Изображение для проекта", upload_to="catalog/project_options/", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Чистовая кровля проекта"
        verbose_name_plural = "Чистовая кровля проектов"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["project", "covering"], name="uniq_project_roof_covering_v2")
        ]

    def __str__(self):
        return f"{self.project.title} — {self.covering.title}"


class ProjectExtraOption(models.Model):
    project = models.ForeignKey(Project, verbose_name="Проект", related_name="extra_options", on_delete=models.CASCADE)
    option = models.ForeignKey(
        ExtraOption, verbose_name="Работа", related_name="project_prices", on_delete=models.PROTECT
    )
    quantity = models.DecimalField("Количество", max_digits=10, decimal_places=2, null=True, blank=True)
    base_price_override = models.PositiveIntegerField("Базовая цена проекта, ₽", null=True, blank=True)
    is_price_fixed = models.BooleanField("Фиксированная цена", default=False)
    description = models.TextField("Описание", blank=True)
    image_override = models.ImageField("Изображение для проекта", upload_to="catalog/project_options/", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Дополнительная работа проекта"
        verbose_name_plural = "Дополнительные работы проектов"
        ordering = ["sort_order", "id"]
        constraints = [models.UniqueConstraint(fields=["project", "option"], name="uniq_project_extra_v2")]

    def __str__(self):
        return f"{self.project.title} — {self.option.title}"


class ProjectContentSection(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="content_sections", verbose_name="Проект")
    title = models.CharField("Заголовок", max_length=255)
    body = models.TextField("Текст")
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Текстовый раздел проекта"
        verbose_name_plural = "Текстовые разделы проекта"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.title}"


class SitePromotion(models.Model):
    """Акция, показываемая на карточках проектов.

    Акции общие для каталога и редактируются один раз в Django Admin.
    """

    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=255)
    description = models.TextField("Условия", blank=True)
    image = models.ImageField("Изображение", upload_to="catalog/promotions/", blank=True)
    button_label = models.CharField("Текст кнопки", max_length=80, blank=True, default="Узнать подробнее")
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Акция на странице проекта"
        verbose_name_plural = "Акции на страницах проектов"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class ConstructionStep(models.Model):
    """Редактируемый этап работы, общий для карточек проектов."""

    class Icon(models.TextChoices):
        BLUEPRINT = "blueprint", "Проект"
        CONTRACT = "contract", "Договор"
        TRUCK = "truck", "Доставка"
        HOUSE = "house", "Строительство"
        SHIELD = "shield", "Приёмка"

    code = models.SlugField("Код", max_length=80, unique=True)
    title = models.CharField("Название", max_length=180)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField("Иконка", max_length=30, choices=Icon.choices, default=Icon.BLUEPRINT)
    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Этап работы"
        verbose_name_plural = "Этапы работы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class CostRate(models.Model):
    """Историческая ставка сметного движка.

    Деньги хранятся здесь, количества — в техническом паспорте/параметрах расчёта.
    Новая ставка создаётся новой строкой с `valid_from`; старую строку не нужно
    перезаписывать, поэтому можно воспроизводить смету на выбранную дату.
    """

    class Component(models.TextChoices):
        WALL_MATERIAL = "wall_material", "Наружные стены — материал"
        PARTITION_MATERIAL = "partition_material", "Перегородки — материал"
        WALL_PROCESSING = "wall_processing", "Обработка стенового комплекта"
        STRUCTURAL_LUMBER = "structural_lumber", "Конструкционный пиломатериал — общий"
        BEAMS_LUMBER = "beams_lumber", "Балки/лаги — пиломатериал"
        RAFTERS_LUMBER = "rafters_lumber", "Стропила/ригели — пиломатериал"
        LATHING_LUMBER = "lathing_lumber", "Обрешётка/контробрешётка — пиломатериал"
        OTHER_LUMBER = "other_lumber", "Прочий конструкционный пиломатериал"
        GABLE = "gable", "Фронтоны"
        TEMPORARY_ROOF = "temporary_roof", "Временная кровля / мембрана"
        CONSUMABLES = "consumables", "Расходники"
        ASSEMBLY_FIRST = "assembly_first", "Сборка 1-го этажа"
        ASSEMBLY_MANSARD = "assembly_mansard", "Сборка мансарды"
        ASSEMBLY_SECOND = "assembly_second", "Сборка 2-го этажа"
        TERRACE = "terrace", "Терраса"
        DELIVERY = "delivery", "Доставка"
        DOCUMENTATION = "documentation", "Проектная документация / подготовка"
        FOUNDATION_UNIT = "foundation_unit", "Фундамент — единица"
        FOUNDATION_FOOTPRINT = "foundation_footprint", "Фундамент — м² пятна"
        FOUNDATION_FIXED = "foundation_fixed", "Фундамент — фиксированная часть"
        ROOF_COVERING = "roof_covering", "Чистовое кровельное покрытие"

    class Unit(models.TextChoices):
        M3 = "m3", "м³"
        M2 = "m2", "м²"
        UNIT = "unit", "шт."
        FIXED = "fixed", "фиксированная сумма"

    class Source(models.TextChoices):
        MANUAL = "manual", "Внесено вручную"
        OFFICE = "office", "Офисный прайс"
        SUPPLIER = "supplier", "Прайс поставщика"
        CONTRACT = "contract", "Договор / подрядчик"
        IMPORT = "import", "Импорт"
        CALIBRATED = "calibrated", "Расчётная калибровка"

    component = models.CharField("Компонент", max_length=40, choices=Component.choices)
    title = models.CharField("Название ставки", max_length=180)
    unit = models.CharField("Единица", max_length=10, choices=Unit.choices)
    rate = models.DecimalField("Ставка, ₽", max_digits=14, decimal_places=2)

    # Цель ставки. Незаполненная цель означает общую ставку компонента.
    material = models.ForeignKey(
        Material, verbose_name="Материал", related_name="cost_rates",
        on_delete=models.PROTECT, null=True, blank=True,
    )
    package = models.ForeignKey(
        BuildPackage, verbose_name="Комплектация", related_name="cost_rates",
        on_delete=models.PROTECT, null=True, blank=True,
    )
    foundation = models.ForeignKey(
        FoundationType, verbose_name="Фундамент", related_name="cost_rates",
        on_delete=models.PROTECT, null=True, blank=True,
    )
    roof_covering = models.ForeignKey(
        RoofCovering, verbose_name="Кровельное покрытие", related_name="cost_rates",
        on_delete=models.PROTECT, null=True, blank=True,
    )

    valid_from = models.DateField("Действует с", default=timezone.localdate)
    valid_to = models.DateField("Действует по", null=True, blank=True)
    source = models.CharField("Источник", max_length=20, choices=Source.choices, default=Source.MANUAL)
    note = models.TextField("Примечание", blank=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Сметная ставка"
        verbose_name_plural = "Сметные ставки"
        ordering = ["component", "-valid_from", "id"]
        indexes = [
            models.Index(fields=["component", "valid_from"], name="costrate_component_date_idx"),
            models.Index(fields=["is_active", "valid_from"], name="costrate_active_date_idx"),
        ]

    def __str__(self):
        return f"{self.title}: {self.rate:g} ₽/{self.get_unit_display()}"

    @property
    def target_label(self) -> str:
        return str(self.material or self.package or self.foundation or self.roof_covering or "Общая")

    def clean(self):
        super().clean()
        if self.valid_to and self.valid_to < self.valid_from:
            raise ValidationError({"valid_to": "Дата окончания не может быть раньше даты начала."})

        required_target = {
            self.Component.WALL_MATERIAL: "material",
            self.Component.PARTITION_MATERIAL: "material",
            self.Component.WALL_PROCESSING: "material",
            self.Component.FOUNDATION_UNIT: "foundation",
            self.Component.FOUNDATION_FOOTPRINT: "foundation",
            self.Component.FOUNDATION_FIXED: "foundation",
            self.Component.ROOF_COVERING: "roof_covering",
        }.get(self.component)
        if required_target and not getattr(self, f"{required_target}_id"):
            raise ValidationError({required_target: "Для этого компонента нужно выбрать объект ставки."})

        material_components = {self.Component.WALL_MATERIAL, self.Component.PARTITION_MATERIAL, self.Component.WALL_PROCESSING}
        package_components = {
            self.Component.STRUCTURAL_LUMBER, self.Component.BEAMS_LUMBER,
            self.Component.RAFTERS_LUMBER, self.Component.LATHING_LUMBER,
            self.Component.OTHER_LUMBER, self.Component.GABLE, self.Component.TEMPORARY_ROOF,
            self.Component.CONSUMABLES, self.Component.ASSEMBLY_FIRST,
            self.Component.ASSEMBLY_MANSARD, self.Component.ASSEMBLY_SECOND,
            self.Component.TERRACE, self.Component.DELIVERY, self.Component.DOCUMENTATION,
        }
        foundation_components = {
            self.Component.FOUNDATION_UNIT, self.Component.FOUNDATION_FOOTPRINT, self.Component.FOUNDATION_FIXED
        }
        if self.component in material_components and (self.foundation_id or self.roof_covering_id or self.package_id):
            raise ValidationError("Материальная ставка может быть привязана только к Material.")
        if self.component in package_components and (self.material_id or self.foundation_id or self.roof_covering_id):
            raise ValidationError("Ставка комплектации может быть общей или привязанной только к BuildPackage.")
        if self.component in foundation_components and (self.material_id or self.package_id or self.roof_covering_id):
            raise ValidationError("Ставка фундамента может быть привязана только к FoundationType.")
        if self.component == self.Component.ROOF_COVERING and (self.material_id or self.package_id or self.foundation_id):
            raise ValidationError("Ставка чистовой кровли может быть привязана только к RoofCovering.")

        # Неактивные исторические/черновые строки не участвуют в проверке пересечений.
        if not self.is_active:
            return

        # Не допускаем два перекрывающихся периода для одного и того же компонента/цели.
        qs = CostRate.objects.filter(
            component=self.component,
            material_id=self.material_id,
            package_id=self.package_id,
            foundation_id=self.foundation_id,
            roof_covering_id=self.roof_covering_id,
            is_active=True,
        ).exclude(pk=self.pk)
        if self.valid_to:
            qs = qs.filter(valid_from__lte=self.valid_to).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gte=self.valid_from)
            )
        else:
            qs = qs.filter(Q(valid_to__isnull=True) | Q(valid_to__gte=self.valid_from))
        overlaps = list(qs)
        if overlaps:
            # Удобный сценарий обновления прайса: новая ставка с более поздней датой
            # может заменить только открытые предыдущие периоды. save() закроет их
            # днём перед valid_from новой ставки.
            can_roll_forward = all(
                row.valid_from < self.valid_from and row.valid_to is None
                for row in overlaps
            )
            if not can_roll_forward:
                raise ValidationError(
                    "Для этого компонента и объекта уже есть ставка с пересекающимся периодом. "
                    "Исправьте даты или создайте новую ставку после текущей."
                )

    def save(self, *args, **kwargs):
        if self.is_active and self.valid_from:
            previous = CostRate.objects.filter(
                component=self.component,
                material_id=self.material_id,
                package_id=self.package_id,
                foundation_id=self.foundation_id,
                roof_covering_id=self.roof_covering_id,
                is_active=True,
                valid_from__lt=self.valid_from,
            ).exclude(pk=self.pk).filter(
                Q(valid_to__isnull=True) | Q(valid_to__gte=self.valid_from)
            )
            previous.update(valid_to=self.valid_from - timedelta(days=1))
        super().save(*args, **kwargs)


class PricingSettings(models.Model):
    ROUNDING_CHOICES = (
        (100, "до 100 ₽"),
        (500, "до 500 ₽"),
        (1000, "до 1 000 ₽"),
        (5000, "до 5 000 ₽"),
        (10000, "до 10 000 ₽"),
    )
    title = models.CharField("Название", max_length=120, default="Основная индексация")
    house_percent = models.DecimalField(
        "Общее изменение цен домов, %",
        max_digits=7,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
        help_text="Например: 5 = увеличить все базовые цены домов на 5%; -3 = уменьшить на 3%.",
    )
    addon_percent = models.DecimalField(
        "Общее изменение доп. опций, %",
        max_digits=7,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
        help_text="Общая индексация фундаментов, кровли и других дополнительных опций.",
    )
    foundation_percent = models.DecimalField(
        "Фундаменты, %", max_digits=7, decimal_places=2, default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
    )
    roof_covering_percent = models.DecimalField(
        "Чистовая кровля, %", max_digits=7, decimal_places=2, default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
    )
    extra_percent = models.DecimalField(
        "Прочие работы, %", max_digits=7, decimal_places=2, default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
    )
    rounding_step = models.PositiveIntegerField("Округлять итоговые цены", choices=ROUNDING_CHOICES, default=1000)
    is_active = models.BooleanField("Активна", default=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Индексация цен"
        verbose_name_plural = "Индексация цен"
        ordering = ["id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            PricingSettings.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)


# ---------------------------------------------------------------------------
# LEGACY MODELS
# Физически остаются до отдельной cleanup-миграции. Новый API/калькулятор их не
# использует. Это намеренно: сначала пользователь запускает audit_catalog_v2 и
# проверяет перенос данных, затем таблицы можно безопасно удалить.
# ---------------------------------------------------------------------------
class ConstructionOption(models.Model):
    class Kind(models.TextChoices):
        FOUNDATION = "foundation", "Фундамент"
        ROOF = "roof", "Кровля"
        OTHER = "other", "Другое"

    code = models.SlugField("Код", max_length=80, unique=True)
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.OTHER)
    title = models.CharField("Название", max_length=180)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Строительная опция"
        verbose_name_plural = "Строительные опции"
        ordering = ["kind", "sort_order", "id"]

    @property
    def group_title(self):
        return self.get_kind_display()

    def __str__(self):
        return f"{self.get_kind_display()} — {self.title}"

class ProjectPackage(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="packages",
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        "Название комплектации",
        max_length=255,
        help_text='Например: Комплектация дома из бруса "ПОД УСАДКУ"',
    )
    price_from = models.PositiveIntegerField(
        "Базовая цена от, ₽",
        null=True,
        blank=True,
        help_text="Исходная цена до применения индексации.",
    )
    is_price_fixed = models.BooleanField(
        "Фиксированная цена",
        default=False,
        help_text="Не применять индексацию к цене комплектации.",
    )
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Комплектация"
        verbose_name_plural = "Комплектации"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.title}"

class ProjectPackageSection(models.Model):
    package = models.ForeignKey(
        ProjectPackage,
        verbose_name="Комплектация",
        related_name="sections",
        on_delete=models.CASCADE,
    )

    title = models.CharField(
        "Название раздела",
        max_length=255,
        help_text="Например: Высота, Силовые конструкции, Прочее",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Раздел комплектации"
        verbose_name_plural = "Разделы комплектации"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.package.title} — {self.title}"

class ProjectPackageItem(models.Model):
    section = models.ForeignKey(
        ProjectPackageSection,
        verbose_name="Раздел комплектации",
        related_name="items",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    title = models.CharField("Параметр", max_length=255)
    value = models.TextField("Значение", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Пункт комплектации"
        verbose_name_plural = "Пункты комплектации"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.title}: {self.value[:50]}"

class ProjectOptionPrice(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="option_prices",
        on_delete=models.CASCADE,
    )
    option = models.ForeignKey(
        ConstructionOption,
        verbose_name="Опция",
        related_name="project_prices",
        on_delete=models.PROTECT,
    )
    base_price = models.PositiveIntegerField("Базовая цена, ₽", null=True, blank=True)
    is_price_fixed = models.BooleanField(
        "Фиксированная цена",
        default=False,
        help_text="Не применять индексацию к этой опции.",
    )
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Цена дополнительной опции"
        verbose_name_plural = "Цены дополнительных опций"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "option"],
                name="uniq_project_construction_option_price",
            )
        ]

    def __str__(self):
        return f"{self.project.title} — {self.option}"

class ProjectIllustratedOption(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="illustrated_options",
        verbose_name="Проект",
    )
    group_title = models.CharField(
        "Группа",
        max_length=255,
        blank=True,
        default="",
        help_text="Например: Фундамент, Кровля, Материалы",
    )
    title = models.CharField("Название", max_length=255)
    price = models.DecimalField(
        "Базовая цена",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Исходная цена до применения индексации.",
    )
    is_price_fixed = models.BooleanField(
        "Фиксированная цена",
        default=False,
        help_text="Не применять индексацию к этой опции.",
    )
    image = models.ImageField(
        "Изображение",
        upload_to="catalog/project_options/",
        blank=True,
    )
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Иллюстрированная опция проекта"
        verbose_name_plural = "Иллюстрированные опции проекта"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.title}"

class PricingRule(models.Model):
    class Kind(models.TextChoices):
        MATERIAL = "material", "Материал дома"
        PACKAGE = "package", "Комплектация дома"
        FOUNDATION = "foundation", "Фундамент"
        ROOF_COVERING = "roof_covering", "Чистовая кровля"
        EXTRA = "extra", "Прочая работа"
        ADDON = "addon", "[legacy] Дополнительная опция"

    settings = models.ForeignKey(PricingSettings, verbose_name="Профиль индексации", related_name="rules", on_delete=models.CASCADE)
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices)
    title = models.CharField("Название правила", max_length=180)
    material = models.ForeignKey(Material, verbose_name="Материал", related_name="pricing_rules", on_delete=models.CASCADE, null=True, blank=True)
    build_package = models.ForeignKey(
        BuildPackage, verbose_name="Комплектация дома", related_name="pricing_rules",
        on_delete=models.CASCADE, null=True, blank=True
    )
    construction_option = models.ForeignKey(
        ConstructionOption,
        verbose_name="Дополнительная опция",
        related_name="pricing_rules",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    foundation = models.ForeignKey(
        FoundationType, verbose_name="Фундамент", related_name="pricing_rules", on_delete=models.CASCADE, null=True, blank=True
    )
    roof_covering = models.ForeignKey(
        RoofCovering, verbose_name="Чистовая кровля", related_name="pricing_rules", on_delete=models.CASCADE, null=True, blank=True
    )
    extra_option = models.ForeignKey(
        ExtraOption, verbose_name="Дополнительная работа", related_name="pricing_rules", on_delete=models.CASCADE, null=True, blank=True
    )
    percent_change = models.DecimalField(
        "Изменение, %", max_digits=7, decimal_places=2, default=0,
        validators=[MinValueValidator(-99), MaxValueValidator(1000)],
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "Правило индексации"
        verbose_name_plural = "Правила индексации"
        ordering = ["kind", "sort_order", "id"]

    def clean(self):
        super().clean()
        targets = {
            self.Kind.MATERIAL: self.material_id,
            self.Kind.PACKAGE: self.build_package_id,
            self.Kind.FOUNDATION: self.foundation_id,
            self.Kind.ROOF_COVERING: self.roof_covering_id,
            self.Kind.EXTRA: self.extra_option_id,
        }
        if self.kind in targets and not targets[self.kind]:
            raise ValidationError("Выбери объект, соответствующий типу правила.")

        selected = sum(
            bool(value)
            for value in (
                self.material_id,
                self.build_package_id,
                self.foundation_id,
                self.roof_covering_id,
                self.extra_option_id,
            )
        )
        if self.kind != self.Kind.ADDON and selected != 1:
            raise ValidationError("У правила должен быть выбран ровно один объект индексации.")

    def __str__(self):
        return f"{self.title}: {self.percent_change}%"
