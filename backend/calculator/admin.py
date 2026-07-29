from django.contrib import admin

from .models import (
    CalculatorFoundation,
    CalculatorMaterial,
    CalculatorRoofCovering,
    CalculatorSettings,
    HouseCostProfile,
)


@admin.register(CalculatorSettings)
class CalculatorSettingsAdmin(admin.ModelAdmin):
    list_display = ("title", "default_package", "min_area", "max_area", "price_range_percent", "is_active", "updated_at")
    list_editable = ("is_active",)
    autocomplete_fields = ("default_package",)


@admin.register(HouseCostProfile)
class HouseCostProfileAdmin(admin.ModelAdmin):
    """В V4 хранит только геометрические допущения быстрого режима.

    Денежные ставки вынесены в Каталог → Сметные ставки. Старые денежные поля
    оставлены физически до cleanup-миграции, но runtime V4 их не использует.
    """

    list_display = ("title", "package", "is_active")
    list_editable = ("is_active",)
    autocomplete_fields = ("package",)
    fieldsets = (
        ("Профиль", {"fields": ("title", "package", "is_active")}),
        ("Стены и перегородки — допущения быстрого режима", {"fields": (
            "first_floor_height_m", "second_floor_height_m", "mansard_knee_wall_height_m",
            "external_openings_ratio", "internal_wall_length_per_m2",
            "internal_wall_length_per_bedroom_m", "partition_height_m", "internal_openings_ratio",
        )}),
        ("Балки — геометрия", {"fields": (
            "joist_spacing_m", "joist_section_width_mm", "joist_section_height_mm",
            "joist_systems_one_floor", "joist_systems_mansard", "joist_systems_two_floor",
        )}),
        ("Стропила и обрешётка — геометрия", {"fields": (
            "rafter_spacing_m", "rafter_section_width_mm", "rafter_section_height_mm",
            "tie_section_width_mm", "tie_section_height_mm", "tie_length_factor",
            "counter_batten_width_mm", "counter_batten_height_mm", "lathing_volume_per_roof_m2",
            "default_roof_pitch_deg", "default_roof_overhang_m",
        )}),
        ("Legacy V3 — больше не участвует в цене", {"fields": (
            "structural_lumber_rate_per_m3", "gable_cladding_rate_per_m2",
            "temporary_roof_rate_per_m2", "consumables_rate_per_wall_m3",
            "first_floor_assembly_rate_per_m2", "mansard_assembly_rate_per_m2",
            "second_floor_assembly_rate_per_m2", "terrace_rate_per_m2", "fixed_package_cost",
            "calibration_samples", "calibration_mape", "calibrated_at",
        ), "classes": ("collapse",), "description": "V4 берёт деньги только из Каталог → Сметные ставки."}),
    )
    readonly_fields = ("calibration_samples", "calibration_mape", "calibrated_at")


@admin.register(CalculatorMaterial)
class CalculatorMaterialAdmin(admin.ModelAdmin):
    list_display = (
        "material", "wall_thickness_mm", "partition_thickness_mm", "wall_waste_percent", "is_active",
    )
    list_editable = ("wall_thickness_mm", "partition_thickness_mm", "wall_waste_percent", "is_active")
    list_filter = ("material__kind", "is_active")
    search_fields = ("material__title", "material__code")
    autocomplete_fields = ("material",)
    fieldsets = (
        ("Материал", {"fields": ("material", "wall_thickness_mm", "partition_thickness_mm", "wall_waste_percent", "description", "sort_order", "is_active")}),
        ("Legacy V3", {"fields": ("wall_rate_per_m3", "partition_rate_per_m3", "fallback_price_per_m2", "source_note"), "classes": ("collapse",), "description": "Денежные ставки V4 здесь не читает."}),
    )


@admin.register(CalculatorFoundation)
class CalculatorFoundationAdmin(admin.ModelAdmin):
    list_display = ("foundation", "pile_spacing_m", "minimum_price", "is_active")
    list_editable = ("pile_spacing_m", "minimum_price", "is_active")
    list_filter = ("foundation__pricing_method", "is_active")
    search_fields = ("foundation__title", "foundation__code")
    autocomplete_fields = ("foundation",)
    fieldsets = (
        ("Геометрия", {"fields": ("foundation", "pile_spacing_m", "minimum_price", "sort_order", "is_active")}),
        ("Legacy V3", {"fields": ("base_extra_price", "fallback_price_per_footprint_m2", "source_note"), "classes": ("collapse",), "description": "Фиксированные добавки и ставки V4 задаются через Сметные ставки."}),
    )


@admin.register(CalculatorRoofCovering)
class CalculatorRoofCoveringAdmin(admin.ModelAdmin):
    list_display = ("covering", "minimum_price", "sort_order", "is_active")
    list_editable = ("minimum_price", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("covering__title", "covering__code")
    autocomplete_fields = ("covering",)
    fieldsets = (
        ("Покрытие", {"fields": ("covering", "minimum_price", "sort_order", "is_active")}),
        ("Legacy V3", {"fields": ("fallback_price_per_footprint_m2", "source_note"), "classes": ("collapse",), "description": "Цена за м² V4 задаётся в Сметных ставках."}),
    )
