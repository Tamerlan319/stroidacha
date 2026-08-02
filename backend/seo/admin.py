from django.contrib import admin

from .models import LandingPage, LandingPageFAQ, LandingPageImage


class LandingPageFAQInline(admin.TabularInline):
    model = LandingPageFAQ
    extra = 1


class LandingPageImageInline(admin.TabularInline):
    model = LandingPageImage
    extra = 1
    fields = ("image", "alt_text", "caption", "sort_order")


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "page_type",
        "category",
        "is_active",
        "sort_order",
        "updated_at",
    )

    list_filter = (
        "page_type",
        "category",
        "is_active",
    )

    search_fields = (
        "title",
        "slug",
        "h1",
        "intro_text",
        "main_text",
        "seo_title",
        "seo_description",
    )

    list_editable = (
        "is_active",
        "sort_order",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    filter_horizontal = (
        "related_projects",
    )

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "title",
                    "slug",
                    "page_type",
                    "h1",
                    "category",
                    "related_projects",
                )
            },
        ),
        (
            "Контент",
            {
                "fields": (
                    "intro_text",
                    "main_text",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                )
            },
        ),
        (
            "Публикация",
            {
                "fields": (
                    "is_active",
                    "sort_order",
                )
            },
        ),
    )

    inlines = [
        LandingPageFAQInline,
        LandingPageImageInline,
    ]


@admin.register(LandingPageFAQ)
class LandingPageFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "landing_page", "sort_order")
    list_filter = ("landing_page",)
    search_fields = ("question", "answer", "landing_page__title")


@admin.register(LandingPageImage)
class LandingPageImageAdmin(admin.ModelAdmin):
    list_display = ("landing_page", "caption", "sort_order")
    list_filter = ("landing_page",)
    search_fields = ("landing_page__title", "caption", "alt_text")
