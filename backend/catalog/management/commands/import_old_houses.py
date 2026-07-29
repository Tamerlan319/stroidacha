from django.core.management.base import BaseCommand, CommandError

from catalog.old_site_importer import (
    DEFAULT_BASE_URL,
    OldSiteHouseImporter,
    OldSiteImportError,
    save_parsed_project,
)


class Command(BaseCommand):
    help = (
        "Импортирует проекты домов из бруса со старого сайта stroydacha.online "
        "в текущий каталог Django. Обновление выполняется по external_id (DB-XX)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
        parser.add_argument("--limit", type=int, default=None, help="Ограничить число проектов для теста.")
        parser.add_argument("--max-pages", type=int, default=20)
        parser.add_argument("--timeout", type=int, default=30)
        parser.add_argument("--pause", type=float, default=0.15, help="Пауза между HTTP-запросами, сек.")
        parser.add_argument("--dry-run", action="store_true", help="Только скачать и разобрать, БД не менять.")
        parser.add_argument("--skip-media", action="store_true", help="Не скачивать фото и планировки.")
        parser.add_argument(
            "--replace-media",
            action="store_true",
            help="Удалить текущие фото/планы проекта и загрузить их заново со старого сайта.",
        )
        parser.add_argument(
            "--clean-imported-text",
            action="store_true",
            help=(
                "Очистить старые свободные описания/текстовые блоки, созданные ранней версией импортера, "
                "и заменить длинное краткое описание компактным фактическим."
            ),
        )
        parser.add_argument(
            "--prune-related",
            action="store_true",
            help="Удалять старые цены/опции/текстовые блоки, которых нет в импортируемых данных.",
        )
        parser.add_argument(
            "--only",
            default="",
            help="Импортировать только перечисленные коды, например DB-01,DB-02,DB-03.",
        )

    def handle(self, *args, **options):
        try:
            importer = OldSiteHouseImporter(
                base_url=options["base_url"],
                timeout=options["timeout"],
                pause=options["pause"],
                stdout=self.stdout,
            )

            only = {
                item.strip().upper().replace("ДБ-", "DB-")
                for item in options["only"].split(",")
                if item.strip()
            }

            projects = importer.discover_projects(
                limit=options["limit"],
                max_pages=options["max_pages"],
            )
            if only:
                projects = [item for item in projects if item.external_id in only]

            if not projects:
                raise CommandError("На старом сайте не найдено ни одного проекта дома.")

            self.stdout.write(self.style.SUCCESS(f"Найдено проектов: {len(projects)}"))

            created_count = 0
            updated_count = 0
            failed_count = 0

            for number, index in enumerate(projects, start=1):
                self.stdout.write(f"\n[{number}/{len(projects)}] {index.external_id}: {index.url}")
                try:
                    data = importer.parse_project(index)
                    self.stdout.write(
                        f"  {data.title}; площадь={data.area}; размер={data.size_text or '-'}; "
                        f"этажи={data.floors}; цены={len(data.price_options)}; "
                        f"опции={len(data.addons)}; медиа={len(data.media)}"
                    )

                    if options["dry_run"]:
                        continue

                    _, created = save_parsed_project(
                        importer,
                        data,
                        skip_media=options["skip_media"],
                        prune_related=options["prune_related"],
                        replace_media=options["replace_media"],
                        clean_imported_text=options["clean_imported_text"],
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS("  создан"))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.WARNING("  обновлён"))
                except Exception as exc:  # keep the bulk import moving; report all failures at the end
                    failed_count += 1
                    self.stderr.write(self.style.ERROR(f"  ОШИБКА: {exc}"))

            if options["dry_run"]:
                self.stdout.write(self.style.SUCCESS("\nDry-run завершён: база данных не изменялась."))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nИмпорт завершён. Создано: {created_count}; "
                        f"обновлено: {updated_count}; ошибок: {failed_count}."
                    )
                )
                if failed_count:
                    self.stdout.write(
                        "Повтори команду после исправления ошибок: импорт идемпотентный и обновляет проекты по external_id."
                    )
        except OldSiteImportError as exc:
            raise CommandError(str(exc)) from exc
