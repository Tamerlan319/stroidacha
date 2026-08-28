from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Lead, LeadAttachment


def attachment_file_link(attachment):
    """Ссылка на скачивание вложения через авторизованный view.

    Файл лежит в приватном хранилище (leads/storage.py) и больше не имеет
    публичного URL — attachment.file.url намеренно вызывает исключение,
    поэтому админка отдаёт ссылку на LeadAttachmentDownloadView.
    """
    if not attachment.pk or not attachment.file:
        return "—"

    url = reverse("lead-attachment-download", args=[attachment.pk])
    return format_html(
        '<a href="{}" target="_blank" rel="noopener">Открыть</a>',
        url,
    )


def attachment_image_preview(attachment, size=48):
    """Миниатюра для вложений-картинок (photo/скан от клиента).

    PDF так не отрисовать (браузер не покажет PDF через <img>) — для них
    просто прочерк, открывать по-прежнему через file_link/"Открыть".
    """
    if not attachment.pk or not attachment.file:
        return "—"
    if not (attachment.content_type or "").startswith("image/"):
        return "—"

    url = reverse("lead-attachment-download", args=[attachment.pk])
    return format_html(
        '<a href="{0}" target="_blank" rel="noopener">'
        '<img src="{0}?disposition=inline" class="admin-thumb" '
        'style="width:{1}px;height:{1}px;" loading="lazy" /></a>',
        url,
        size,
    )


class LeadAttachmentInline(admin.TabularInline):
    model = LeadAttachment
    extra = 0
    fields = (
        "preview",
        "file_link",
        "original_name",
        "content_type",
        "size_display",
        "created_at",
    )
    readonly_fields = fields
    can_delete = True

    @admin.display(description="Превью")
    def preview(self, attachment):
        return attachment_image_preview(attachment)

    @admin.display(description="Файл")
    def file_link(self, attachment):
        return attachment_file_link(attachment)

    @admin.display(description="Размер")
    def size_display(self, attachment):
        if not attachment.size:
            return "—"

        megabytes = attachment.size / (1024 * 1024)
        if megabytes >= 1:
            return f"{megabytes:.1f} МБ"

        return f"{max(1, round(attachment.size / 1024))} КБ"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "attachment_preview",
        "id",
        "source",
        "phone",
        "project",
        "attachment_count",
        "consent_version",
        "is_processed",
        "created_at",
        "anonymized_at",
    )
    list_filter = (
        "source",
        "is_processed",
        "created_at",
        "utm_source",
        "utm_medium",
        "utm_campaign",
    )
    search_fields = (
        "phone",
        "message",
        "project__title",
        "manager_comment",
        "attachments__original_name",
    )
    list_select_related = ("project",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "ip_address",
        "user_agent",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_content",
        "utm_term",
        "page_url",
        "consent_version",
        "consent_given_at",
        "anonymized_at",
    )
    inlines = (LeadAttachmentInline,)

    fieldsets = (
        (
            "Заявка",
            {
                "fields": (
                    "source",
                    "project",
                    "phone",
                    "message",
                )
            },
        ),
        (
            "Согласие",
            {
                "fields": (
                    "consent_version",
                    "consent_given_at",
                )
            },
        ),
        (
            "Обработка",
            {
                "fields": (
                    "is_processed",
                    "manager_comment",
                )
            },
        ),
        (
            "Маркетинг",
            {
                "fields": (
                    "page_url",
                    "utm_source",
                    "utm_medium",
                    "utm_campaign",
                    "utm_content",
                    "utm_term",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Техническая информация",
            {
                "fields": (
                    "ip_address",
                    "user_agent",
                    "created_at",
                    "updated_at",
                    "anonymized_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("attachments")

    @admin.display(description="Файлы")
    def attachment_count(self, lead):
        return len(lead.attachments.all())

    @admin.display(description="Фото")
    def attachment_preview(self, lead):
        image_attachment = next(
            (a for a in lead.attachments.all() if (a.content_type or "").startswith("image/")),
            None,
        )
        if not image_attachment:
            return "—"
        return attachment_image_preview(image_attachment)


@admin.register(LeadAttachment)
class LeadAttachmentAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "id",
        "original_name",
        "lead",
        "content_type",
        "size",
        "created_at",
    )
    list_select_related = ("lead",)
    search_fields = (
        "original_name",
        "lead__phone",
    )
    readonly_fields = (
        "lead",
        "preview",
        "file_link",
        "original_name",
        "content_type",
        "size",
        "created_at",
    )

    @admin.display(description="Превью")
    def preview(self, attachment):
        return attachment_image_preview(attachment)

    @admin.display(description="Файл")
    def file_link(self, attachment):
        return attachment_file_link(attachment)
