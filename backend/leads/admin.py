from django.contrib import admin
from django.utils.html import format_html

from .models import Lead, LeadAttachment


class LeadAttachmentInline(admin.TabularInline):
    model = LeadAttachment
    extra = 0
    fields = (
        "file_link",
        "original_name",
        "content_type",
        "size_display",
        "created_at",
    )
    readonly_fields = fields
    can_delete = True

    @admin.display(description="Файл")
    def file_link(self, attachment):
        if not attachment.pk or not attachment.file:
            return "—"

        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Открыть</a>',
            attachment.file.url,
        )

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
        "id",
        "source",
        "phone",
        "project",
        "attachment_count",
        "consent_version",
        "is_processed",
        "created_at",
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
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Файлы")
    def attachment_count(self, lead):
        return lead.attachments.count()


@admin.register(LeadAttachment)
class LeadAttachmentAdmin(admin.ModelAdmin):
    list_display = (
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
        "file",
        "original_name",
        "content_type",
        "size",
        "created_at",
    )
