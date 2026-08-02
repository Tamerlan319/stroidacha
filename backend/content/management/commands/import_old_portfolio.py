from django.core.management.base import BaseCommand, CommandError

from content.old_site_portfolio_importer import (
    DEFAULT_PORTFOLIO_URLS,
    OldSitePortfolioImporter,
)


class Command(BaseCommand):
    help = (
        "Импортирует выбранные реализованные объекты и их фотогалереи "
        "со старого сайта stroydacha.online в раздел портфолио."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            action="append",
            dest="urls",
            help=(
                "URL объекта. Флаг можно повторить. Без --url импортируются "
                "четыре согласованных объекта."
            ),
        )
        parser.add_argument("--timeout", type=int, default=30)
        parser.add_argument("--pause", type=float, default=0.15)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--skip-media", action="store_true")
        parser.add_argument(
            "--replace-media",
            action="store_true",
            help="Удалить фото этих объектов из БД и скачать галереи заново.",
        )
        parser.add_argument(
            "--overwrite-text",
            action="store_true",
            help="Заменить описания, ранее отредактированные в Django Admin.",
        )

    def handle(self, *args, **options):
        urls = options["urls"] or list(DEFAULT_PORTFOLIO_URLS)
        importer = OldSitePortfolioImporter(
            timeout=options["timeout"],
            pause=options["pause"],
            stdout=self.stdout,
        )

        created_count = 0
        updated_count = 0
        failed_count = 0
        for index, url in enumerate(urls, start=1):
            self.stdout.write(f"\n[{index}/{len(urls)}] {url}")
            try:
                data = importer.parse(url)
                self.stdout.write(
                    f"  {data.title}; фото={len(data.media)}; "
                    f"площадь={data.area or '-'}; размер={data.size_text or '-'}"
                )
                if options["dry_run"]:
                    continue
                _, created = importer.save(
                    data,
                    overwrite_text=options["overwrite_text"],
                    skip_media=options["skip_media"],
                    replace_media=options["replace_media"],
                    sort_order=index * 10,
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS("  создан"))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING("  обновлён"))
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
        if failed_count == len(urls):
            raise CommandError("Не удалось импортировать ни одного объекта.")
