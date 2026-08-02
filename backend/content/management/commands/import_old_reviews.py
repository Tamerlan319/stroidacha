from django.core.management.base import BaseCommand, CommandError

from content.old_site_reviews_importer import (
    REVIEWS_URL,
    OldSiteReviewsImporter,
)


class Command(BaseCommand):
    help = "Импортирует реальные отзывы клиентов со старой страницы stroydacha.online."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=int, default=30)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Обновить подписи и порядок уже импортированных отзывов.",
        )

    def handle(self, *args, **options):
        importer = OldSiteReviewsImporter(timeout=options["timeout"])
        try:
            reviews = importer.parse(REVIEWS_URL)
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"Найдено отзывов: {len(reviews)}")
        for item in reviews:
            self.stdout.write(f"  {item.author_name}: {len(item.text)} символов")

        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS("Dry-run завершён: БД не изменялась."))
            return

        created, updated = importer.save(reviews, overwrite=options["overwrite"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Импорт завершён. Создано: {created}; найдено существующих: {updated}."
            )
        )
