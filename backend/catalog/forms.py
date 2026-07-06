from django import forms


class CatalogExcelImportForm(forms.Form):
    file = forms.FileField(
        label="Excel-файл",
        help_text="Загрузите .xlsx файл с листами: projects, price_options, addons, package_items",
    )