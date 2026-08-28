"""Общие мелочи для admin.py всех приложений — сейчас только превью фото.

Ни один ImageField/FileField в проекте раньше не показывал превью в
списках/инлайнах Django Admin — только виджет выбора файла. При таком
количестве фото в проектах/портфолио/материалах это неудобно: не видно,
что именно выбрано, пока не откроешь файл отдельно.
"""

from django.utils.html import format_html


def thumbnail(file_field, size=48):
    """Небольшая превью-картинка для list_display/inline-полей.

    Безопасна для пустых полей и для полей с приватным storage без
    публичного .url (не роняет страницу — просто показывает прочерк).
    """
    if not file_field:
        return "—"

    try:
        url = file_field.url
    except (ValueError, NotImplementedError):
        return "—"

    return format_html(
        '<img src="{}" class="admin-thumb" style="width:{}px;height:{}px;" loading="lazy" />',
        url,
        size,
        size,
    )
