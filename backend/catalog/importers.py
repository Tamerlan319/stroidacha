from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.text import slugify
from openpyxl import load_workbook

from .models import (
    Project,
    ProjectAddon,
    ProjectCategory,
    ProjectPackage,
    ProjectPackageItem,
    ProjectPackageSection,
    ProjectPriceOption,
)


class CatalogImportError(Exception):
    pass


def cell_to_str(value):
    if value is None:
        return ""

    return str(value).strip()


def to_decimal(value):
    value = cell_to_str(value)

    if not value:
        return None

    value = value.replace(" ", "").replace(",", ".")

    try:
        return Decimal(value)
    except InvalidOperation:
        raise CatalogImportError(f"Некорректное число: {value}")


def to_int(value):
    value = cell_to_str(value)

    if not value:
        return None

    value = value.replace(" ", "")

    try:
        return int(float(value))
    except ValueError:
        raise CatalogImportError(f"Некорректное целое число: {value}")


def to_bool(value, default=False):
    if value is None or value == "":
        return default

    if isinstance(value, bool):
        return value

    value = cell_to_str(value).lower()

    true_values = {"1", "true", "yes", "да", "д", "+", "активен"}
    false_values = {"0", "false", "no", "нет", "н", "-", ""}

    if value in true_values:
        return True

    if value in false_values:
        return False

    raise CatalogImportError(f"Некорректное boolean-значение: {value}")


def get_sheet_rows(workbook, sheet_name, required=False):
    if sheet_name not in workbook.sheetnames:
        if required:
            raise CatalogImportError(f"В Excel-файле нет обязательного листа: {sheet_name}")
        return []

    sheet = workbook[sheet_name]
    rows = list(sheet.iter_rows(values_only=True))

    if not rows:
        return []

    headers = [cell_to_str(cell) for cell in rows[0]]
    result = []

    for row_number, row in enumerate(rows[1:], start=2):
        if not any(row):
            continue

        item = {}

        for index, header in enumerate(headers):
            if not header:
                continue

            item[header] = row[index] if index < len(row) else None

        item["_row_number"] = row_number
        result.append(item)

    return result


def get_category(value):
    value = cell_to_str(value)

    if not value:
        raise CatalogImportError("Категория проекта обязательна.")

    try:
        return ProjectCategory.objects.get(slug=value)
    except ProjectCategory.DoesNotExist:
        pass

    try:
        return ProjectCategory.objects.get(title__iexact=value)
    except ProjectCategory.DoesNotExist:
        raise CatalogImportError(f"Категория не найдена: {value}")


def get_construction_type(value):
    value = cell_to_str(value).lower()

    values = {
        "брус": Project.ConstructionType.TIMBER,
        "timber": Project.ConstructionType.TIMBER,
        "каркас": Project.ConstructionType.FRAME,
        "frame": Project.ConstructionType.FRAME,
        "бревно": Project.ConstructionType.LOG,
        "log": Project.ConstructionType.LOG,
        "другое": Project.ConstructionType.OTHER,
        "other": Project.ConstructionType.OTHER,
    }

    if not value:
        return Project.ConstructionType.OTHER

    if value not in values:
        raise CatalogImportError(f"Неизвестный тип строительства: {value}")

    return values[value]


def import_catalog_excel(file_obj):
    workbook = load_workbook(file_obj, data_only=True)

    project_rows = get_sheet_rows(workbook, "projects", required=True)
    price_rows = get_sheet_rows(workbook, "price_options")
    addon_rows = get_sheet_rows(workbook, "addons")
    package_item_rows = get_sheet_rows(workbook, "package_items")

    result = {
        "projects_created": 0,
        "projects_updated": 0,
        "price_options_created": 0,
        "addons_created": 0,
        "package_items_created": 0,
    }

    imported_projects = {}

    with transaction.atomic():
        for row in project_rows:
            row_number = row["_row_number"]
            external_id = cell_to_str(row.get("external_id"))

            if not external_id:
                raise CatalogImportError(f"Лист projects, строка {row_number}: external_id обязателен.")

            title = cell_to_str(row.get("title"))

            if not title:
                raise CatalogImportError(f"Лист projects, строка {row_number}: title обязателен.")

            category = get_category(row.get("category"))

            defaults = {
                "title": title,
                "category": category,
                "construction_type": get_construction_type(row.get("construction_type")),
                "area": to_decimal(row.get("area")),
                "floors": to_decimal(row.get("floors")),
                "floor_label": cell_to_str(row.get("floor_label")),
                "bedrooms": to_int(row.get("bedrooms")),
                "width": to_decimal(row.get("width")),
                "length": to_decimal(row.get("length")),
                "size_text": cell_to_str(row.get("size_text")),
                "price_from": to_int(row.get("price_from")),
                "build_days_from": to_int(row.get("build_days_from")),
                "build_days_to": to_int(row.get("build_days_to")),
                "short_description": cell_to_str(row.get("short_description")),
                "description": cell_to_str(row.get("description")),
                "seo_title": cell_to_str(row.get("seo_title")),
                "seo_description": cell_to_str(row.get("seo_description")),
                "is_active": to_bool(row.get("is_active"), default=True),
                "is_featured": to_bool(row.get("is_featured"), default=False),
                "sort_order": to_int(row.get("sort_order")) or 0,
            }

            slug = cell_to_str(row.get("slug"))

            if slug:
                defaults["slug"] = slugify(slug, allow_unicode=True)

            project, created = Project.objects.update_or_create(
                external_id=external_id,
                defaults=defaults,
            )

            imported_projects[external_id] = project

            if created:
                result["projects_created"] += 1
            else:
                result["projects_updated"] += 1

        imported_project_ids = [project.id for project in imported_projects.values()]

        ProjectPriceOption.objects.filter(project_id__in=imported_project_ids).delete()
        ProjectAddon.objects.filter(project_id__in=imported_project_ids).delete()
        ProjectPackage.objects.filter(project_id__in=imported_project_ids).delete()

        for row in price_rows:
            row_number = row["_row_number"]
            project_external_id = cell_to_str(row.get("project_external_id"))

            project = imported_projects.get(project_external_id)

            if not project:
                raise CatalogImportError(
                    f"Лист price_options, строка {row_number}: проект {project_external_id} не найден в листе projects."
                )

            title = cell_to_str(row.get("title"))

            if not title:
                raise CatalogImportError(f"Лист price_options, строка {row_number}: title обязателен.")

            ProjectPriceOption.objects.create(
                project=project,
                group_title=cell_to_str(row.get("group_title")),
                title=title,
                price=to_int(row.get("price")),
                note=cell_to_str(row.get("note")),
                sort_order=to_int(row.get("sort_order")) or 0,
            )

            result["price_options_created"] += 1

        for row in addon_rows:
            row_number = row["_row_number"]
            project_external_id = cell_to_str(row.get("project_external_id"))

            project = imported_projects.get(project_external_id)

            if not project:
                raise CatalogImportError(
                    f"Лист addons, строка {row_number}: проект {project_external_id} не найден в листе projects."
                )

            title = cell_to_str(row.get("title"))

            if not title:
                raise CatalogImportError(f"Лист addons, строка {row_number}: title обязателен.")

            ProjectAddon.objects.create(
                project=project,
                group_title=cell_to_str(row.get("group_title")),
                title=title,
                price=to_int(row.get("price")),
                description=cell_to_str(row.get("description")),
                sort_order=to_int(row.get("sort_order")) or 0,
            )

            result["addons_created"] += 1

        package_cache = {}
        section_cache = {}

        for row in package_item_rows:
            row_number = row["_row_number"]
            project_external_id = cell_to_str(row.get("project_external_id"))

            project = imported_projects.get(project_external_id)

            if not project:
                raise CatalogImportError(
                    f"Лист package_items, строка {row_number}: проект {project_external_id} не найден в листе projects."
                )

            package_title = cell_to_str(row.get("package_title")) or "Базовая комплектация"
            section_title = cell_to_str(row.get("section_title")) or "Общее"
            title = cell_to_str(row.get("title"))

            if not title:
                raise CatalogImportError(f"Лист package_items, строка {row_number}: title обязателен.")

            package_key = (project.id, package_title)

            if package_key not in package_cache:
                package = ProjectPackage.objects.create(
                    project=project,
                    title=package_title,
                    sort_order=0,
                )
                package_cache[package_key] = package

            package = package_cache[package_key]

            section_key = (package.id, section_title)

            if section_key not in section_cache:
                section = ProjectPackageSection.objects.create(
                    package=package,
                    title=section_title,
                    sort_order=len(section_cache) + 1,
                )
                section_cache[section_key] = section

            section = section_cache[section_key]

            ProjectPackageItem.objects.create(
                section=section,
                title=title,
                value=cell_to_str(row.get("value")),
                sort_order=to_int(row.get("sort_order")) or 0,
            )

            result["package_items_created"] += 1

    return result