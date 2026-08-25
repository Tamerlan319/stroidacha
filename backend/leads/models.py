from django.db import models

from .storage import PrivateLeadAttachmentStorage

private_attachment_storage = PrivateLeadAttachmentStorage()


class Lead(models.Model):
    class Source(models.TextChoices):
        CALLBACK = "callback", "Заказать звонок"
        PROJECT_ORDER = "project_order", "Заказать проект"
        PROJECT_CHANGES = "project_changes", "Внести правки в проект"
        OWN_PROJECT = "own_project", "Прислать свой проект"
        CALCULATOR = "calculator", "Калькулятор"
        CONTACT_FORM = "contact_form", "Форма обратной связи"
        HOME_PHONE_CONSULTATION = (
            "home_phone_consultation",
            "Консультация с главной страницы",
        )

    name = models.CharField("Имя", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    region = models.CharField(
        "Регион строительства",
        max_length=255,
        blank=True,
    )
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

    consent_version = models.CharField(
        "Версия согласия",
        max_length=50,
        blank=True,
    )
    consent_given_at = models.DateTimeField(
        "Дата согласия",
        null=True,
        blank=True,
    )

    is_processed = models.BooleanField("Обработана", default=False)
    manager_comment = models.TextField("Комментарий менеджера", blank=True)

    anonymized_at = models.DateTimeField(
        "Обезличена",
        null=True,
        blank=True,
        editable=False,
        help_text=(
            "Заполняется автоматически командой anonymize_old_leads "
            "(см. LEAD_RETENTION_MONTHS). После обезличивания телефон, "
            "комментарий, IP, user-agent и вложения удалены — запись "
            "оставлена только для статистики по источникам обращений."
        ),
    )

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_source_display()} — {self.phone}"


class LeadAttachment(models.Model):
    lead = models.ForeignKey(
        Lead,
        verbose_name="Заявка",
        related_name="attachments",
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        "Файл",
        upload_to="leads/attachments/%Y/%m/%d",
        storage=private_attachment_storage,
    )
    original_name = models.CharField("Исходное имя", max_length=255)
    content_type = models.CharField("Тип файла", max_length=100, blank=True)
    size = models.PositiveIntegerField("Размер, байт", default=0)
    created_at = models.DateTimeField("Загружен", auto_now_add=True)

    class Meta:
        verbose_name = "Файл заявки"
        verbose_name_plural = "Файлы заявки"
        ordering = ["id"]

    def __str__(self):
        return self.original_name
