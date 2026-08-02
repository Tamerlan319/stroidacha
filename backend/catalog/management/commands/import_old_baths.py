from catalog.models import ProjectCategory
from seo.models import LandingPage

from .import_old_houses import Command as BaseImportCommand


class Command(BaseImportCommand):
    help = (
        "Импортирует все проекты бань из бруса со старого сайта "
        "stroydacha.online в текущий каталог Django. Обновление выполняется "
        "по external_id (BB-XX)."
    )
    project_kind = "baths"
    project_label_genitive = "бань"
    external_prefix = "BB"

    def normalize_external_id(self, value):
        return value.strip().upper().replace("ББ-", "BB-")

    def after_import(self):
        # Исправляет существующую ошибочную привязку SEO-страницы к домам.
        category = ProjectCategory.objects.get(slug="baths")
        updated = LandingPage.objects.filter(slug="bani-iz-brusa").exclude(
            category=category
        ).update(category=category)
        if updated:
            self.stdout.write(
                self.style.SUCCESS(
                    "Страница /bani-iz-brusa привязана к категории «Бани»."
                )
            )
