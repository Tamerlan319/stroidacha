from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget, Widget

from .models import (
    Project,
    ProjectAddon,
    ProjectCategory,
    ProjectImage,
    ProjectPackage,
    ProjectPackageItem,
    ProjectPackageSection,
    ProjectPlan,
    ProjectPriceOption,
)

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path

from .forms import CatalogExcelImportForm
from .importers import CatalogImportError, import_catalog_excel

class ProjectCategoryWidget(ForeignKeyWidget):
    def clean(self, value, row=None, **kwargs):
        value = str(value or "").strip()

        if not value:
            raise ValueError("Поле category обязательно. Укажи slug или название категории.")

        try:
            return ProjectCategory.objects.get(slug=value)
        except ProjectCategory.DoesNotExist:
            try:
                return ProjectCategory.objects.get(title__iexact=value)
            except ProjectCategory.DoesNotExist:
                raise ValueError(f"Категория не найдена: {value}")


class ConstructionTypeWidget(Widget):
    VALUES = {
        "брус": Project.ConstructionType.TIMBER,
        "timber": Project.ConstructionType.TIMBER,
        "каркас": Project.ConstructionType.FRAME,
        "frame": Project.ConstructionType.FRAME,
        "бревно": Project.ConstructionType.LOG,
        "log": Project.ConstructionType.LOG,
        "другое": Project.ConstructionType.OTHER,
        "other": Project.ConstructionType.OTHER,
    }

    def clean(self, value, row=None, **kwargs):
        value = str(value or "").strip().lower()

        if not value:
            return Project.ConstructionType.OTHER

        if value not in self.VALUES:
            raise ValueError(f"Неизвестный тип строительства: {value}")

        return self.VALUES[value]


class RussianBooleanWidget(Widget):
    TRUE_VALUES = {"1", "true", "yes", "да", "д", "+", "активен"}
    FALSE_VALUES = {"0", "false", "no", "нет", "н", "-", ""}

    def clean(self, value, row=None, **kwargs):
        if isinstance(value, bool):
            return value

        value = str(value or "").strip().lower()

        if value in self.TRUE_VALUES:
            return True

        if value in self.FALSE_VALUES:
            return False

        raise ValueError(f"Некорректное boolean-значение: {value}")


class ProjectResource(resources.ModelResource):
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ProjectCategoryWidget(ProjectCategory, "slug"),
    )

    construction_type = fields.Field(
        column_name="construction_type",
        attribute="construction_type",
        widget=ConstructionTypeWidget(),
    )

    is_active = fields.Field(
        column_name="is_active",
        attribute="is_active",
        widget=RussianBooleanWidget(),
    )

    is_featured = fields.Field(
        column_name="is_featured",
        attribute="is_featured",
        widget=RussianBooleanWidget(),
    )

    class Meta:
        model = Project
        import_id_fields = ("external_id",)
        skip_unchanged = True
        report_skipped = True

        fields = (
            "external_id",
            "title",
            "slug",
            "category",
            "construction_type",
            "area",
            "floors",
            "floor_label",
            "bedrooms",
            "width",
            "length",
            "size_text",
            "price_from",
            "build_days_from",
            "build_days_to",
            "short_description",
            "description",
            "seo_title",
            "seo_description",
            "is_active",
            "is_featured",
            "sort_order",
        )

        export_order = fields

    def before_import_row(self, row, **kwargs):
        external_id = str(row.get("external_id") or "").strip()

        if not external_id:
            raise ValueError("Поле external_id обязательно для импорта.")

        row["external_id"] = external_id


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


class ProjectPlanInline(admin.TabularInline):
    model = ProjectPlan
    extra = 1


class ProjectPriceOptionInline(admin.TabularInline):
    model = ProjectPriceOption
    extra = 1


class ProjectAddonInline(admin.TabularInline):
    model = ProjectAddon
    extra = 1


class ProjectPackageInline(admin.TabularInline):
    model = ProjectPackage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):

    list_display = (
        "external_id",
        "title",
        "category",
        "construction_type",
        "area",
        "floor_label",
        "size_text",
        "price_from",
        "is_active",
        "is_featured",
        "sort_order",
    )

    list_filter = (
        "category",
        "construction_type",
        "is_active",
        "is_featured",
    )

    search_fields = (
        "external_id",
        "title",
        "short_description",
        "description",
    )

    list_editable = (
        "is_active",
        "is_featured",
        "sort_order",
    )

    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "external_id",
                    "title",
                    "slug",
                    "category",
                    "construction_type",
                    "main_image",
                )
            },
        ),
        (
            "Характеристики",
            {
                "fields": (
                    "area",
                    "floors",
                    "floor_label",
                    "bedrooms",
                    "width",
                    "length",
                    "size_text",
                    "price_from",
                    "build_days_from",
                    "build_days_to",
                )
            },
        ),
        (
            "Описание",
            {
                "fields": (
                    "short_description",
                    "description",
                )
            },
        ),
        (
            "SEO",
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Публикация",
            {
                "fields": (
                    "is_active",
                    "is_featured",
                    "sort_order",
                )
            },
        ),
    )

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "import-excel-v2/",
                self.admin_site.admin_view(self.import_excel_v2_view),
                name="catalog_project_import_excel_v2",
            ),
        ]

        return custom_urls + urls

    def import_excel_v2_view(self, request):
        if request.method == "POST":
            form = CatalogExcelImportForm(request.POST, request.FILES)

            if form.is_valid():
                try:
                    result = import_catalog_excel(form.cleaned_data["file"])
                except CatalogImportError as error:
                    self.message_user(request, str(error), level=messages.ERROR)
                except Exception as error:
                    self.message_user(
                        request,
                        f"Неожиданная ошибка импорта: {error}",
                        level=messages.ERROR,
                    )
                else:
                    self.message_user(
                        request,
                        (
                            "Импорт завершён. "
                            f"Проекты созданы: {result['projects_created']}. "
                            f"Проекты обновлены: {result['projects_updated']}. "
                            f"Цены: {result['price_options_created']}. "
                            f"Опции: {result['addons_created']}. "
                            f"Пункты комплектации: {result['package_items_created']}."
                        ),
                        level=messages.SUCCESS,
                    )
                    return redirect("..")
        else:
            form = CatalogExcelImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Импорт проектов из Excel v2",
            "form": form,
        }

        return render(
            request,
            "admin/catalog/project/import_excel_v2.html",
            context,
        )

    inlines = [
        ProjectPriceOptionInline,
        ProjectAddonInline,
        ProjectImageInline,
        ProjectPlanInline,
        ProjectPackageInline,
    ]


@admin.register(ProjectPriceOption)
class ProjectPriceOptionAdmin(admin.ModelAdmin):
    list_display = ("project", "group_title", "title", "price", "sort_order")
    list_filter = ("group_title", "project")
    search_fields = ("project__title", "group_title", "title")


@admin.register(ProjectAddon)
class ProjectAddonAdmin(admin.ModelAdmin):
    list_display = ("project", "group_title", "title", "price", "sort_order")
    list_filter = ("group_title", "project")
    search_fields = ("project__title", "group_title", "title")


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ("project", "image_type", "caption", "alt_text", "sort_order")
    list_filter = ("project", "image_type")
    search_fields = ("project__title", "caption", "alt_text")


@admin.register(ProjectPlan)
class ProjectPlanAdmin(admin.ModelAdmin):
    list_display = ("project", "title", "floor", "alt_text", "sort_order")
    list_filter = ("project", "floor")
    search_fields = ("project__title", "title", "alt_text")


class ProjectPackageSectionInline(admin.TabularInline):
    model = ProjectPackageSection
    extra = 1


@admin.register(ProjectPackage)
class ProjectPackageAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "price_from", "sort_order")
    list_filter = ("project",)
    search_fields = ("title", "project__title")
    inlines = [ProjectPackageSectionInline]


class ProjectPackageItemInline(admin.TabularInline):
    model = ProjectPackageItem
    extra = 1


@admin.register(ProjectPackageSection)
class ProjectPackageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "package", "sort_order")
    list_filter = ("package__project", "package")
    search_fields = ("title", "package__title", "package__project__title")
    inlines = [ProjectPackageItemInline]


@admin.register(ProjectPackageItem)
class ProjectPackageItemAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "short_value", "sort_order")
    list_filter = ("section__package__project", "section__package", "section")
    search_fields = ("title", "value", "section__title")

    def short_value(self, obj):
        return obj.value[:80]

    short_value.short_description = "Значение"