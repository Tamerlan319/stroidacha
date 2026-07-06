from django.db import models
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

    area = models.DecimalField(
        "Площадь, м²",
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    floors = models.DecimalField(
        "Этажность числом",
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Например: 1, 1.5, 2",
    )

    floor_label = models.CharField(
        "Этажность текстом",
        max_length=100,
        blank=True,
        help_text="Например: Полутораэтажный, Одноэтажный, Двухэтажный",
    )

    bedrooms = models.PositiveSmallIntegerField(
        "Спальни",
        null=True,
        blank=True,
    )

    width = models.DecimalField(
        "Ширина, м",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    length = models.DecimalField(
        "Длина, м",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    size_text = models.CharField(
        "Размер текстом",
        max_length=50,
        blank=True,
        help_text="Например: 6х6, 6х8, 8х9",
    )

    price_from = models.PositiveIntegerField(
        "Цена от, ₽",
        null=True,
        blank=True,
    )

    build_days_from = models.PositiveSmallIntegerField(
        "Срок строительства от, дней",
        null=True,
        blank=True,
    )

    build_days_to = models.PositiveSmallIntegerField(
        "Срок строительства до, дней",
        null=True,
        blank=True,
    )

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

        if not self.size_text and self.width and self.length:
            self.size_text = f"{self.width:g}х{self.length:g}"

        super().save(*args, **kwargs)


class ProjectImage(models.Model):
    class ImageType(models.TextChoices):
        FACADE = "facade", "Фасад"
        GALLERY = "gallery", "Галерея"
        DETAIL = "detail", "Деталь"
        INTERIOR = "interior", "Интерьер"
        OTHER = "other", "Другое"

    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="images",
        on_delete=models.CASCADE,
    )

    image = models.ImageField("Изображение", upload_to="projects/gallery/")
    image_type = models.CharField(
        "Тип изображения",
        max_length=30,
        choices=ImageType.choices,
        default=ImageType.GALLERY,
    )
    caption = models.CharField("Подпись", max_length=255, blank=True)
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото проекта"
        verbose_name_plural = "Фото проекта"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Фото: {self.project.title}"


class ProjectPlan(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="plans",
        on_delete=models.CASCADE,
    )

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


class ProjectPriceOption(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="price_options",
        on_delete=models.CASCADE,
    )

    group_title = models.CharField(
        "Группа",
        max_length=255,
        help_text="Например: Обычный брус, Профилированный брус",
    )
    title = models.CharField(
        "Название варианта",
        max_length=255,
        help_text="Например: Обычный брус 150х150",
    )
    price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True)
    note = models.CharField("Примечание", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Цена по материалу"
        verbose_name_plural = "Цены по материалам"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.title}"


class ProjectAddon(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        related_name="addons",
        on_delete=models.CASCADE,
    )

    group_title = models.CharField(
        "Группа",
        max_length=255,
        help_text="Например: Фундамент, Кровля",
    )
    title = models.CharField("Название опции", max_length=255)
    price = models.PositiveIntegerField("Цена, ₽", null=True, blank=True)
    description = models.TextField("Описание", blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Дополнительная опция"
        verbose_name_plural = "Дополнительные опции"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.project.title} — {self.group_title} — {self.title}"


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
    price_from = models.PositiveIntegerField("Цена от, ₽", null=True, blank=True)
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