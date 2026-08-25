import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from leads.models import LeadAttachment


class Command(BaseCommand):
    """Одноразовая миграция вложений заявок в приватное хранилище.

    До этого фикса файлы LeadAttachment лежали в MEDIA_ROOT и раздавались
    Caddy как обычная статика без авторизации (см. аудит по 152-ФЗ). Модель
    теперь пишет новые файлы в PRIVATE_MEDIA_ROOT, но уже загруженные до
    смены хранилища файлы физически остаются на старом месте — эта команда
    переносит их.

    Безопасна для повторного запуска: уже перенесённые файлы пропускаются.
    По умолчанию НИЧЕГО не удаляет из старой директории — сначала убедитесь,
    что скачивание через LeadAttachmentDownloadView работает, и только потом
    запускайте с --delete-source.
    """

    help = (
        "Переносит файлы вложений заявок из публичной медиатеки (MEDIA_ROOT) "
        "в приватное хранилище (PRIVATE_MEDIA_ROOT), закрытое от Caddy."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete-source",
            action="store_true",
            help=(
                "Удалить исходные файлы из MEDIA_ROOT после успешного "
                "копирования. Без этого флага старые файлы остаются на "
                "месте (и остаются публично доступными) до повторного "
                "запуска."
            ),
        )

    def handle(self, *args, **options):
        old_root = Path(settings.MEDIA_ROOT)
        new_root = Path(settings.PRIVATE_MEDIA_ROOT)
        delete_source = options["delete_source"]

        moved = 0
        already_ok = 0
        missing = 0

        attachments = LeadAttachment.objects.exclude(file="").order_by("id")
        total = attachments.count()

        if total == 0:
            self.stdout.write("Вложений заявок не найдено — переносить нечего.")
            return

        for attachment in attachments:
            relative_path = attachment.file.name
            old_path = old_root / relative_path
            new_path = new_root / relative_path

            if new_path.exists():
                already_ok += 1
                if delete_source and old_path.exists():
                    old_path.unlink()
                continue

            if not old_path.exists():
                self.stderr.write(
                    self.style.WARNING(
                        f"[{attachment.pk}] исходный файл не найден: {old_path}"
                    )
                )
                missing += 1
                continue

            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_path, new_path)
            moved += 1

            if delete_source:
                old_path.unlink()

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Всего вложений: {total}. "
                f"Перенесено: {moved}, уже на месте: {already_ok}, "
                f"не найдено в источнике: {missing}."
            )
        )

        if moved and not delete_source:
            self.stdout.write(
                "Старые копии оставлены в MEDIA_ROOT (пока ещё публично "
                "доступны через Caddy). Проверьте скачивание через админку, "
                "затем запустите команду ещё раз с флагом --delete-source, "
                "чтобы убрать их из публичной директории."
            )
