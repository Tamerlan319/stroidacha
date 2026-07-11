from django.db import models
from django.utils.text import slugify

class Advantage(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)
    icon = models.CharField(
        "Иконка",
        max_length=50,
        blank=True,
        help_text="Например: factory, truck, warranty, price",
    )
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Преимущество"
        verbose_name_plural = "Преимущества"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class WorkStep(models.Model):
    title = models.CharField("Заголовок", max_length=255)
    description = models.TextField("Описание", blank=True)
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Этап работы"
        verbose_name_plural = "Этапы работы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField("Вопрос", max_length=500)
    answer = models.TextField("Ответ")
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQ"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question


class Review(models.Model):
    author_name = models.CharField("Имя клиента", max_length=255)
    city = models.CharField("Город", max_length=255, blank=True)
    text = models.TextField("Отзыв")
    project_name = models.CharField("Проект/объект", max_length=255, blank=True)
    rating = models.PositiveSmallIntegerField("Оценка", default=5)
    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.author_name} — {self.rating}/5"
    
class ContactLocation(models.Model):
    class LocationType(models.TextChoices):
        OFFICE = "office", "Офис"
        PRODUCTION = "production", "Производство"
        WAREHOUSE = "warehouse", "Склад"
        SHOWROOM = "showroom", "Шоурум"
        OTHER = "other", "Другое"

    title = models.CharField("Название", max_length=255)
    location_type = models.CharField(
        "Тип точки",
        max_length=32,
        choices=LocationType.choices,
        default=LocationType.OFFICE,
    )
    address = models.CharField("Адрес", max_length=500)
    short_description = models.TextField("Краткое описание", blank=True)

    phone = models.CharField("Телефон", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    work_hours = models.CharField("Режим работы", max_length=255, blank=True)

    map_embed_url = models.URLField(
        "Ссылка для встраивания карты",
        max_length=1000,
        blank=True,
        help_text="URL из iframe Яндекс.Карт. Например: https://yandex.ru/map-widget/v1/?...",
    )
    map_link_url = models.URLField(
        "Ссылка открыть карту",
        max_length=1000,
        blank=True,
        help_text="Обычная ссылка на Яндекс.Карты или Google Maps.",
    )

    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Контактная точка"
        verbose_name_plural = "Контактные точки"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.title


class PortfolioProject(models.Model):
    title = models.CharField("Название объекта", max_length=255)
    slug = models.SlugField(
        "Slug",
        max_length=255,
        unique=True,
        blank=True,
        allow_unicode=True,
    )

    location = models.CharField("Локация", max_length=255, blank=True)
    area = models.CharField("Площадь", max_length=100, blank=True)
    size_text = models.CharField("Размер", max_length=100, blank=True)
    material = models.CharField("Материал", max_length=255, blank=True)
    price = models.DecimalField(
        "Стоимость",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    short_description = models.TextField("Краткое описание", blank=True)
    description = models.TextField("Подробное описание", blank=True)

    main_image = models.ImageField(
        "Главное изображение",
        upload_to="portfolio/main/",
        blank=True,
    )

    is_active = models.BooleanField("Активен", default=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Объект портфолио"
        verbose_name_plural = "Портфолио"
        ordering = ["sort_order", "-created_at", "id"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)

        super().save(*args, **kwargs)


class PortfolioImage(models.Model):
    portfolio_project = models.ForeignKey(
        PortfolioProject,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Объект портфолио",
    )
    image = models.ImageField(
        "Изображение",
        upload_to="portfolio/gallery/",
    )
    caption = models.CharField("Подпись", max_length=255, blank=True)
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Сортировка", default=0)

    class Meta:
        verbose_name = "Фото портфолио"
        verbose_name_plural = "Фото портфолио"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or f"Фото для {self.portfolio_project.title}"