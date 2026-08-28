from django.db import models


class LandingPage(models.Model):
    class PageType(models.TextChoices):
        SERVICE = "service", "Услуга"
        SIZE = "size", "Размер"
        MATERIAL = "material", "Материал"
        REGION = "region", "Регион"
        DELIVERY = "delivery", "Доставка"
        PRODUCTION = "production", "Производство"
        COMPANY = "company", "О компании"
        GUIDE = "guide", "Справочник"
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
        help_text="Если выбрать категорию, можно связать страницу с домами или банями",
    )

    related_projects = models.ManyToManyField(
        "catalog.Project",
        verbose_name="Связанные проекты",
        related_name="landing_pages",
        blank=True,
        help_text="Проекты, которые нужно показать на странице",
    )

    filter_width = models.DecimalField(
        "Фильтр по ширине, м",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=(
            "Заполните вместе с «Фильтр по длине», чтобы каталог на странице "
            "показывал только проекты этого размера (например, 6х6). "
            "Если оставить пустым, каталог покажет все проекты выбранной "
            "категории — это годится для страниц-хабов вроде «Дома из бруса», "
            "но не для размерных страниц (иначе размерная страница дублирует хаб)."
        ),
    )
    filter_length = models.DecimalField(
        "Фильтр по длине, м",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="См. подсказку у поля «Фильтр по ширине».",
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


class LandingPageImage(models.Model):
    landing_page = models.ForeignKey(
        LandingPage,
        verbose_name="SEO-страница",
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField("Изображение", upload_to="seo/pages/")
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    caption = models.CharField("Подпись", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Изображение SEO-страницы"
        verbose_name_plural = "Изображения SEO-страниц"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.caption or self.alt_text or f"Изображение для {self.landing_page}"
