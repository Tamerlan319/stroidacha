from django.core.management.base import BaseCommand, CommandError

from seo.old_site_page_importer import (
    DEFAULT_INFO_PAGES,
    OldSitePageImporter,
)


class Command(BaseCommand):
    help = (
        "Импортирует корпоративные страницы и несколько стартовых статей "
        "справочника со старого сайта в SEO-страницы Django."
    )

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=30)
        parser.add_argument("--pause", type=float, default=0.15)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--skip-media", action="store_true")
        parser.add_argument(
            "--replace-media",
            action="store_true",
            help="Удалить изображения этих страниц и скачать их заново.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Перезаписать тексты, уже изменённые вручную в Django Admin.",
        )

    def handle(self, *args, **options):
        importer = OldSitePageImporter(
            timeout=options["timeout"],
            pause=options["pause"],
        )
        created_count = 0
        updated_count = 0
        failed_count = 0

        for index, source in enumerate(DEFAULT_INFO_PAGES, start=1):
            self.stdout.write(
                f"\n[{index}/{len(DEFAULT_INFO_PAGES)}] {source.menu_title}: {source.source_url}"
            )
            try:
                data = importer.parse(source)
                self.stdout.write(
                    f"  H1: {data.h1}; текст: {len(data.main_text)} символов; "
                    f"изображения: {len(data.images)}"
                )
                if options["dry_run"]:
                    continue
                _, created = importer.save(
                    data,
                    overwrite=options["overwrite"],
                    skip_media=options["skip_media"],
                    replace_media=options["replace_media"],
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS("  создана"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING("  обновлена"))
            except Exception as exc:
                failed_count += 1
                self.stderr.write(self.style.ERROR(f"  ОШИБКА: {exc}"))

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("\nDry-run завершён: БД не изменялась."))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"\nИмпорт завершён. Создано: {created_count}; "
                f"обновлено: {updated_count}; ошибок: {failed_count}."
            )
        )
        if failed_count == len(DEFAULT_INFO_PAGES):
            raise CommandError("Не удалось импортировать ни одной страницы.")
