from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source",
        "name",
        "phone",
        "email",
        "project",
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
        "name",
        "phone",
        "email",
        "message",
        "project__title",
        "manager_comment",
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
    )

    fieldsets = (
        (
            "Заявка",
            {
                "fields": (
                    "source",
                    "project",
                    "name",
                    "phone",
                    "email",
                    "message",
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