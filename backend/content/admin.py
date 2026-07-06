from django.contrib import admin

from .models import Advantage, FAQ, Review, WorkStep


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