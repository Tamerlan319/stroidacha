from django.db import models

from .crypto import EncryptedPhoneField
from .storage import PrivateLeadAttachmentStorage

private_attachment_storage = PrivateLeadAttachmentStorage()


class Lead(models.Model):
    """Заявка с сайта.

    Хранится только то, что нужно, чтобы связаться с человеком и сделать
    расчёт (152-ФЗ, ст. 5 ч. 5): телефон — зашифрованным (leads/crypto.py),
    комментарий, файлы, форма и страница отправки, версия и время согласия.
    Метки рекламы, IP, данные браузера и идентификаторы Метрики не
    сохраняются: откуда пришёл посетитель, видно в самой Метрике.
    """

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
        HOME_HERO_POPUP = (
            "home_hero_popup",
            "Всплывающая форма в баннере на главной",
        )
        FAQ_PAGE = "faq_page", "Вопрос со страницы FAQ"
        REVIEWS_PAGE = "reviews_page", "Заявка со страницы отзывов"

    # 255, а не длина номера: в базе лежит шифр.
    phone = EncryptedPhoneField("Телефон", max_length=255, blank=True)
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

    # Только адрес страницы: параметры (метки рекламы, yclid, etext)
    # отбрасываются при приёме заявки (LeadCreateSerializer).
    page_url = models.URLField("Страница заявки", max_length=2000, blank=True)

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
            "комментарий, страница и вложения удалены — запись оставлена "
            "только для статистики по формам."
        ),
    )

    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ["-created_at"]

    def __str__(self):
        # Без телефона: админка пишет это название в журнал изменений
        # открытым текстом.
        return f"Заявка №{self.pk} — {self.get_source_display()}"


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
