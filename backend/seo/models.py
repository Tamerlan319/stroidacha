from django.db import models


class LandingPage(models.Model):
    class PageType(models.TextChoices):
        SERVICE = "service", "Услуга"
        SIZE = "size", "Размер"
        MATERIAL = "material", "Материал"
        REGION = "region", "Регион"
        DELIVERY = "delivery", "Доставка"
        PRODUCTION = "production", "Производство"
        CUSTOM = "custom", "Произвольная"

    title = models.CharField(
        "Внутреннее название",
        max_length=255,
        help_text="Например: Дома из бруса 6х6",
    )

    slug = models.SlugField(
        "URL-ключ",
        max_length=255,
        unique=True,
        help_text="Например: doma-iz-brusa-6x6",
    )

    page_type = models.CharField(
        "Тип страницы",
        max_length=30,
        choices=PageType.choices,
        default=PageType.CUSTOM,
    )

    h1 = models.CharField(
        "H1",
        max_length=255,
        help_text="Главный заголовок страницы",
    )

    intro_text = models.TextField(
        "Вводный текст",
        blank=True,
        help_text="Короткий текст под первым экраном",
    )

    main_text = models.TextField(
        "Основной текст",
        blank=True,
        help_text="Основной SEO/коммерческий текст страницы",
    )

    category = models.ForeignKey(
        "catalog.ProjectCategory",
        verbose_name="Категория проектов",
        related_name="landing_pages",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Если выбрать категорию, можно связать страницу с домами/банями/гаражами",
    )

    related_projects = models.ManyToManyField(
        "catalog.Project",
        verbose_name="Связанные проекты",
        related_name="landing_pages",
        blank=True,
        help_text="Проекты, которые нужно показать на странице",
    )

    seo_title = models.CharField("SEO title", max_length=255, blank=True)
    seo_description = models.TextField("SEO description", blank=True)

    is_active = models.BooleanField("Показывать", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "SEO-страница"
        verbose_name_plural = "SEO-страницы"
        ordering = ["sort_order", "title"]

    def __str__(self):
        return self.title


class LandingPageFAQ(models.Model):
    landing_page = models.ForeignKey(
        LandingPage,
        verbose_name="SEO-страница",
        related_name="faqs",
        on_delete=models.CASCADE,
    )

    question = models.CharField("Вопрос", max_length=500)
    answer = models.TextField("Ответ")
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "FAQ SEO-страницы"
        verbose_name_plural = "FAQ SEO-страницы"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.question