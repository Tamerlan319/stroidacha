from django.contrib import admin

from .models import Advantage, FAQ, Review, WorkStep, ContactLocation, PortfolioProject, PortfolioImage


@admin.register(Advantage)
class AdvantageAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("title", "description")


@admin.register(WorkStep)
class WorkStepAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("title", "description")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("question", "answer")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "author_name",
        "city",
        "project_name",
        "rating",
        "is_active",
        "sort_order",
    )
    list_editable = ("is_active", "sort_order")
    list_filter = ("rating", "is_active", "city")
    search_fields = ("author_name", "city", "text", "project_name")

@admin.register(ContactLocation)
class ContactLocationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "location_type",
        "address",
        "phone",
        "email",
        "is_active",
        "sort_order",
    )
    list_filter = (
        "location_type",
        "is_active",
    )
    search_fields = (
        "title",
        "address",
        "phone",
        "email",
    )
    list_editable = (
        "is_active",
        "sort_order",
    )


class PortfolioImageInline(admin.TabularInline):
    model = PortfolioImage
    extra = 1
    fields = (
        "image",
        "caption",
        "alt_text",
        "sort_order",
    )


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "location",
        "area",
        "size_text",
        "price",
        "is_active",
        "sort_order",
        "created_at",
    )
    list_filter = (
        "is_active",
        "created_at",
    )
    search_fields = (
        "title",
        "location",
        "short_description",
        "description",
    )
    list_editable = (
        "is_active",
        "sort_order",
    )
    prepopulated_fields = {
        "slug": ("title",),
    }
    inlines = [
        PortfolioImageInline,
    ]


@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = (
        "portfolio_project",
        "caption",
        "sort_order",
    )
    search_fields = (
        "portfolio_project__title",
        "caption",
        "alt_text",
    )