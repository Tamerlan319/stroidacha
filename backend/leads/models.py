from django.db import models


class Lead(models.Model):
    class Source(models.TextChoices):
        CALLBACK = "callback", "Заказать звонок"
        PROJECT_ORDER = "project_order", "Заказать проект"
        PROJECT_CHANGES = "project_changes", "Внести правки в проект"
        OWN_PROJECT = "own_project", "Прислать свой проект"
        CALCULATOR = "calculator", "Калькулятор"
        CONTACT_FORM = "contact_form", "Форма обратной связи"

    name = models.CharField("Имя", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=50)
    email = models.EmailField("Email", blank=True)
    message = models.TextField("Комментарий", blank=True)

    source = models.CharField(
        "Источник заявки",
        max_length=50,
        choices=Source.choices,
        default=Source.CONTACT_FORM,
    )

    project = models.ForeignKey(
        "catalog.Project",
        verbose_name="Проект",
        related_name="leads",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    page_url = models.URLField("Страница заявки", blank=True)

    utm_source = models.CharField("UTM source", max_length=255, blank=True)
    utm_medium = models.CharField("UTM medium", max_length=255, blank=True)
    utm_campaign = models.CharField("UTM campaign", max_length=255, blank=True)
    utm_content = models.CharField("UTM content", max_length=255, blank=True)
    utm_term = models.CharField("UTM term", max_length=255, blank=True)

    ip_address = models.GenericIPAddressField("IP-адрес", null=True, blank=True)
    user_agent = models.TextField("User agent", blank=True)

    is_processed = models.BooleanField("Обработана", default=False)
    manager_comment = models.TextField("Комментарий менеджера", blank=True)

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_source_display()} — {self.phone}"