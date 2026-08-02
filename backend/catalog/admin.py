from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path

from .forms import CatalogExcelImportForm
from .importers import CatalogImportError, import_catalog_excel
from .models import (
    BuildPackage,
    ConstructionStep,
    CostRate,
    BuildPackageItem,
    BuildPackageSection,
    ExtraOption,
    FoundationType,
    Material,
    PricingRule,
    PricingSettings,
    Project,
    ProjectCategory,
    ProjectContentSection,
    ProjectExtraOption,
    ProjectFoundation,
    ProjectImage,
    ProjectMaterialTakeoff,
    ProjectOffer,
    ProjectPackageOverride,
    ProjectPlan,
    ProjectRoofCovering,
    ProjectTechnicalData,
    RoofCovering,
    SitePromotion,
)
from .pricing import PricingService


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "kind", "section_width_mm", "section_height_mm", "sort_order", "is_active")
    list_filter = ("kind", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("title", "code", "group_title")


class BuildPackageItemInline(admin.TabularInline):
    model = BuildPackageItem
    extra = 1


@admin.register(BuildPackageSection)
class BuildPackageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "package", "sort_order")
    list_filter = ("package",)
    search_fields = ("title", "package__title")
    inlines = [BuildPackageItemInline]


class BuildPackageSectionInline(admin.TabularInline):
    model = BuildPackageSection
    extra = 1


@admin.register(BuildPackage)
class BuildPackageAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("title", "code")
    prepopulated_fields = {"code": ("title",)}
    inlines = [BuildPackageSectionInline]


@admin.register(FoundationType)
class FoundationTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "pricing_method", "unit_name", "minimum_price", "is_active", "sort_order")
    list_editable = ("pricing_method", "minimum_price", "is_active", "sort_order")
    search_fields = ("title", "code")
    list_filter = ("pricing_method", "is_active")
    fieldsets = (
        ("Фундамент", {"fields": ("code", "title", "pricing_method", "unit_name", "minimum_price", "image", "description", "sort_order", "is_active")}),
        ("Legacy", {"fields": ("base_rate",), "classes": ("collapse",), "description": "Поле оставлено для совместимости. Новые ставки ведутся в разделе «Сметные ставки»."}),
    )


@admin.register(RoofCovering)
class RoofCoveringAdmin(admin.ModelAdmin):
    list_display = ("title", "minimum_price", "is_active", "sort_order")
    list_editable = ("minimum_price", "is_active", "sort_order")
    search_fields = ("title", "code")
    fieldsets = (
        ("Покрытие", {"fields": ("code", "title", "minimum_price", "image", "description", "sort_order", "is_active")}),
        ("Legacy", {"fields": ("rate_per_m2",), "classes": ("collapse",), "description": "Ставка оставлена для совместимости. Новые цены за м² ведутся в «Сметных ставках»."}),
    )


@admin.register(ExtraOption)
class ExtraOptionAdmin(admin.ModelAdmin):
    list_display = ("title", "pricing_method", "base_rate", "unit_name", "minimum_price", "is_active", "sort_order")
    list_editable = ("pricing_method", "base_rate", "minimum_price", "is_active", "sort_order")
    list_filter = ("pricing_method", "is_active")
    search_fields = ("title", "code")


class ProjectTechnicalDataInline(admin.StackedInline):
    model = ProjectTechnicalData
    extra = 1
    max_num = 1
    can_delete = False
    fieldsets = (
        ("Статус", {"fields": ("data_source", "is_verified", "verified_at")}),
        ("Площади этажей", {"fields": ("first_floor_area_m2", "mansard_area_m2", "second_floor_area_m2")}),
        ("Наружные стены", {"fields": (
            "external_wall_length_m", "external_wall_height_m", "external_openings_area_m2",
        )}),
        ("Внутренние перегородки", {"fields": (
            "internal_wall_length_m", "internal_wall_height_m", "internal_openings_area_m2",
        )}),
        ("Пиломатериал конструкций", {"fields": (
            "beams_volume_m3", "rafters_volume_m3", "lathing_volume_m3", "other_structural_lumber_volume_m3",
        )}),
        ("Кровля и террасы", {"fields": (
            "gable_area_m2", "roof_area_m2", "terrace_area_m2", "roof_shape", "roof_pitch_deg",
            "roof_overhang_m", "roof_complexity_factor",
        )}),
        ("Примечания", {"fields": ("notes",), "classes": ("collapse",)}),
    )
    readonly_fields = ("verified_at",)


class ProjectMaterialTakeoffInline(admin.TabularInline):
    model = ProjectMaterialTakeoff
    extra = 0
    fields = (
        "material", "external_wall_volume_m3", "internal_wall_volume_m3",
        "includes_waste", "data_source", "is_verified", "verified_at", "notes",
    )
    readonly_fields = ("verified_at",)
    autocomplete_fields = ("material",)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ("image", "is_primary", "image_type", "caption", "alt_text", "sort_order")


class ProjectPlanInline(admin.TabularInline):
    model = ProjectPlan
    extra = 1


class ProjectOfferInline(admin.TabularInline):
    model = ProjectOffer
    extra = 1
    fields = ("material", "build_package", "base_price", "is_price_fixed", "note", "sort_order")
    autocomplete_fields = ("material", "build_package")


class ProjectFoundationInline(admin.TabularInline):
    model = ProjectFoundation
    extra = 0
    fields = ("foundation", "quantity", "base_price_override", "is_price_fixed", "description", "image_override", "sort_order")
    autocomplete_fields = ("foundation",)


class ProjectRoofCoveringInline(admin.TabularInline):
    model = ProjectRoofCovering
    extra = 0
    fields = ("covering", "roof_area_override_m2", "base_price_override", "is_price_fixed", "description", "image_override", "sort_order")
    autocomplete_fields = ("covering",)


class ProjectExtraOptionInline(admin.TabularInline):
    model = ProjectExtraOption
    extra = 0
    fields = ("option", "quantity", "base_price_override", "is_price_fixed", "description", "image_override", "sort_order")
    autocomplete_fields = ("option",)


class ProjectContentSectionInline(admin.TabularInline):
    model = ProjectContentSection
    extra = 1
    fields = ("title", "body", "is_active", "sort_order")


@admin.register(SitePromotion)
class SitePromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("title", "code", "description")
    prepopulated_fields = {"code": ("title",)}
    fieldsets = (
        ("Акция", {"fields": ("title", "code", "description", "image", "button_label")}),
        ("Публикация", {"fields": ("is_active", "sort_order")}),
    )


@admin.register(ConstructionStep)
class ConstructionStepAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "icon", "is_active", "sort_order")
    list_editable = ("icon", "is_active", "sort_order")
    search_fields = ("title", "code", "description")
    prepopulated_fields = {"code": ("title",)}


class ProjectPackageOverrideInline(admin.StackedInline):
    model = ProjectPackageOverride
    extra = 0
    fields = ("package", "description", "sections", "source_hash")
    readonly_fields = ("source_hash",)
    autocomplete_fields = ("package",)
    classes = ("collapse",)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "external_id",
        "title",
        "category",
        "construction_type",
        "area",
        "floor_display",
        "size_display",
        "effective_price_from",
        "is_active",
        "is_featured",
        "sort_order",
    )
    list_filter = ("category", "construction_type", "is_active", "is_featured")
    search_fields = ("external_id", "title", "short_description", "description")
    list_editable = ("is_active", "is_featured", "sort_order")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("Основное", {"fields": ("external_id", "title", "slug", "category", "construction_type")}),
        (
            "Характеристики",
            {"fields": ("area", "floors", "bedrooms", "bathrooms", "width", "length", "terrace_area", "has_balcony", "has_porch", "build_days_from", "build_days_to")},
        ),
        (
            "Индексация",
            {"fields": ("price_indexing_disabled", "foundation_price_indexing_disabled", "roof_price_indexing_disabled", "extra_price_indexing_disabled")},
        ),
        ("Описание", {"fields": ("short_description", "description")}),
        ("SEO", {"fields": ("seo_title", "seo_description"), "classes": ("collapse",)}),
        ("Публикация", {"fields": ("is_active", "is_featured", "sort_order")}),
    )
    inlines = [
        ProjectTechnicalDataInline,
        ProjectMaterialTakeoffInline,
        ProjectImageInline,
        ProjectPlanInline,
        ProjectOfferInline,
        ProjectFoundationInline,
        ProjectRoofCoveringInline,
        ProjectExtraOptionInline,
        ProjectContentSectionInline,
        ProjectPackageOverrideInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("offers__material", "images")

    @admin.display(description="Этажность")
    def floor_display(self, obj):
        return obj.computed_floor_label

    @admin.display(description="Размер")
    def size_display(self, obj):
        return obj.computed_size_text

    @admin.display(description="Цена на сайте")
    def effective_price_from(self, obj):
        value = PricingService().get_project_price_from(obj)
        return f"{value:,} ₽".replace(",", " ") if value is not None else "—"

    def get_urls(self):
        return [
            path("import-excel-v2/", self.admin_site.admin_view(self.import_excel_v2_view), name="catalog_project_import_excel_v2")
        ] + super().get_urls()

    def import_excel_v2_view(self, request):
        if request.method == "POST":
            form = CatalogExcelImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    result = import_catalog_excel(form.cleaned_data["file"])
                except CatalogImportError as error:
                    self.message_user(request, str(error), level=messages.ERROR)
                except Exception as error:
                    self.message_user(request, f"Неожиданная ошибка импорта: {error}", level=messages.ERROR)
                else:
                    self.message_user(
                        request,
                        (
                            "Импорт завершён. "
                            f"Проекты созданы: {result['projects_created']}. "
                            f"Проекты обновлены: {result['projects_updated']}. "
                            f"Предложения дома: {result['price_options_created']}. "
                            f"Доп. позиции: {result['addons_created']}."
                        ),
                        level=messages.SUCCESS,
                    )
                    return redirect("..")
        else:
            form = CatalogExcelImportForm()
        context = {**self.admin_site.each_context(request), "title": "Импорт проектов из Excel v2", "form": form}
        return render(request, "admin/catalog/project/import_excel_v2.html", context)


@admin.register(ProjectOffer)
class ProjectOfferAdmin(admin.ModelAdmin):
    list_display = ("project", "material", "build_package", "base_price", "effective_price", "is_price_fixed", "sort_order")
    list_filter = ("material", "build_package", "is_price_fixed")
    list_editable = ("is_price_fixed", "sort_order")
    search_fields = ("project__title", "project__external_id", "material__title")
    autocomplete_fields = ("project", "material", "build_package")
    list_select_related = ("project", "material", "build_package")

    @admin.display(description="Цена на сайте")
    def effective_price(self, obj):
        value = PricingService().get_offer_price(obj)
        return f"{value:,} ₽".replace(",", " ") if value is not None else "—"


@admin.register(ProjectFoundation)
class ProjectFoundationAdmin(admin.ModelAdmin):
    list_display = ("project", "foundation", "quantity", "base_price_override", "effective_price", "is_price_fixed")
    list_filter = ("foundation", "is_price_fixed")
    search_fields = ("project__title", "project__external_id", "foundation__title")
    autocomplete_fields = ("project", "foundation")

    @admin.display(description="Цена на сайте")
    def effective_price(self, obj):
        value = PricingService().get_foundation_price(obj)
        return f"{value:,} ₽".replace(",", " ") if value is not None else "—"


@admin.register(ProjectRoofCovering)
class ProjectRoofCoveringAdmin(admin.ModelAdmin):
    list_display = ("project", "covering", "roof_area_override_m2", "base_price_override", "effective_price", "is_price_fixed")
    list_filter = ("covering", "is_price_fixed")
    search_fields = ("project__title", "project__external_id", "covering__title")
    autocomplete_fields = ("project", "covering")

    @admin.display(description="Цена на сайте")
    def effective_price(self, obj):
        value = PricingService().get_roof_covering_price(obj)
        return f"{value:,} ₽".replace(",", " ") if value is not None else "—"


@admin.register(ProjectExtraOption)
class ProjectExtraOptionAdmin(admin.ModelAdmin):
    list_display = ("project", "option", "quantity", "base_price_override", "effective_price", "is_price_fixed")
    list_filter = ("option", "is_price_fixed")
    search_fields = ("project__title", "project__external_id", "option__title")
    autocomplete_fields = ("project", "option")

    @admin.display(description="Цена на сайте")
    def effective_price(self, obj):
        value = PricingService().get_extra_price(obj)
        return f"{value:,} ₽".replace(",", " ") if value is not None else "—"


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("project", "is_primary", "image_type", "caption", "sort_order")
    list_filter = ("is_primary", "image_type")
    search_fields = ("project__title", "caption", "alt_text")


@admin.register(ProjectPlan)
class ProjectPlanAdmin(admin.ModelAdmin):
    list_display = ("project", "title", "floor", "sort_order")
    list_filter = ("floor",)
    search_fields = ("project__title", "title", "alt_text")


@admin.register(ProjectTechnicalData)
class ProjectTechnicalDataAdmin(admin.ModelAdmin):
    list_display = ("project", "data_source", "is_verified", "completeness", "roof_area_m2", "verified_at")
    list_filter = ("data_source", "is_verified", "roof_shape")
    search_fields = ("project__external_id", "project__title")
    autocomplete_fields = ("project",)

    @admin.display(description="Заполнено")
    def completeness(self, obj):
        return f"{obj.completeness_percent}%"


@admin.register(ProjectMaterialTakeoff)
class ProjectMaterialTakeoffAdmin(admin.ModelAdmin):
    list_display = ("project", "material", "external_wall_volume_m3", "internal_wall_volume_m3", "data_source", "is_verified", "verified_at")
    list_filter = ("material", "data_source", "is_verified")
    search_fields = ("project__external_id", "project__title", "material__title")
    autocomplete_fields = ("project", "material")


@admin.register(CostRate)
class CostRateAdmin(admin.ModelAdmin):
    list_display = ("title", "component", "target", "rate", "unit", "valid_from", "valid_to", "source", "is_active")
    list_filter = ("component", "unit", "source", "is_active", "valid_from")
    search_fields = (
        "title", "material__title", "package__title", "foundation__title", "roof_covering__title", "note"
    )
    autocomplete_fields = ("material", "package", "foundation", "roof_covering")
    date_hierarchy = "valid_from"
    list_select_related = ("material", "package", "foundation", "roof_covering")
    fieldsets = (
        ("Ставка", {"fields": ("component", "title", "unit", "rate")}),
        ("К чему относится", {"fields": ("material", "package", "foundation", "roof_covering")}),
        ("Период", {"fields": ("valid_from", "valid_to", "is_active")}),
        ("Источник", {"fields": ("source", "note")}),
    )

    @admin.display(description="Объект")
    def target(self, obj):
        return obj.target_label


class PricingRuleInline(admin.TabularInline):
    model = PricingRule
    extra = 0
    fields = (
        "kind", "title", "material", "build_package", "foundation",
        "roof_covering", "extra_option", "percent_change", "is_active", "sort_order"
    )
    autocomplete_fields = ("material", "build_package", "foundation", "roof_covering", "extra_option")


@admin.register(PricingSettings)
class PricingSettingsAdmin(admin.ModelAdmin):
    list_display = ("title", "house_percent", "foundation_percent", "roof_covering_percent", "extra_percent", "rounding_step", "is_active")
    list_editable = ("house_percent", "foundation_percent", "roof_covering_percent", "extra_percent", "rounding_step", "is_active")
    fieldsets = (("Общая индексация", {"fields": ("title", "house_percent", "foundation_percent", "roof_covering_percent", "extra_percent", "rounding_step", "is_active")}),)
    inlines = [PricingRuleInline]


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "target", "percent_change", "is_active", "sort_order")
    list_filter = ("settings", "kind", "is_active")
    list_editable = ("percent_change", "is_active", "sort_order")
    search_fields = (
        "title", "material__title", "build_package__title", "foundation__title",
        "roof_covering__title", "extra_option__title"
    )
    autocomplete_fields = ("material", "build_package", "foundation", "roof_covering", "extra_option")

    @admin.display(description="Объект")
    def target(self, obj):
        return obj.material or obj.build_package or obj.foundation or obj.roof_covering or obj.extra_option or "—"
