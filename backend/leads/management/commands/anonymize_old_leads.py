import calendar

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from leads.models import Lead


def months_ago(months: int):
    """Момент времени N календарных месяцев назад (без внешних зависимостей)."""
    now = timezone.now()
    total_months = now.year * 12 + (now.month - 1) - months
    year, month0 = divmod(total_months, 12)
    month = month0 + 1
    day = min(now.day, calendar.monthrange(year, month)[1])
    return now.replace(
        year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0
    )


class Command(BaseCommand):
    """Обезличивает заявки старше срока хранения (152-ФЗ, ст. 5).

    Политика на сайте (/privacy) обещает не хранить ПДн дольше, чем нужно
    для целей обработки, но до этой команды это ничем не было обеспечено —
    заявки хранились бессрочно. Команда не удаляет саму запись Lead (она
    остаётся полезна для статистики по источникам/UTM), но стирает всё, что
    прямо идентифицирует человека: телефон, имя, email, комментарий, IP,
    user-agent, страницу отправки и файлы вложений.

    Комментарий менеджера (manager_comment) намеренно не трогается
    автоматически — если там записаны личные данные клиента, почистите
    вручную при просмотре.

    Предполагается запуск по расписанию (системный cron, т.к. в проекте
    нет celery/beat) — см. scripts/cron-anonymize-leads.sh.
    """

    help = (
        "Обезличивает заявки старше LEAD_RETENTION_MONTHS месяцев: стирает "
        "телефон, имя, email, комментарий, IP, user-agent, страницу "
        "отправки и удаляет вложения, оставляя саму запись для статистики."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--months",
            type=int,
            default=None,
            help="Переопределить LEAD_RETENTION_MONTHS для этого запуска.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только посчитать, сколько заявок будет обезличено, ничего не менять.",
        )

    def handle(self, *args, **options):
        months = (
            options["months"]
            if options["months"] is not None
            else settings.LEAD_RETENTION_MONTHS
        )

        if months <= 0:
            self.stderr.write(
                self.style.ERROR("Срок хранения должен быть положительным числом месяцев.")
            )
            return

        cutoff = months_ago(months)
        queryset = Lead.objects.filter(
            created_at__lt=cutoff,
            anonymized_at__isnull=True,
        )
        total = queryset.count()

        if total == 0:
            self.stdout.write(
                f"Заявок старше {months} мес. (до {cutoff.date()}) для обезличивания не найдено."
            )
            return

        if options["dry_run"]:
            self.stdout.write(
                f"[dry-run] Будет обезличено заявок: {total} "
                f"(созданы до {cutoff.date()}, порог {months} мес.)."
            )
            return

        now = timezone.now()
        anonymized = 0

        for lead in queryset.iterator():
            with transaction.atomic():
                for attachment in lead.attachments.all():
                    if attachment.file:
                        attachment.file.delete(save=False)
                    attachment.delete()

                lead.name = ""
                lead.phone = ""
                lead.email = ""
                lead.message = ""
                lead.ip_address = None
                lead.user_agent = ""
                lead.page_url = ""
                lead.anonymized_at = now
                lead.save(
                    update_fields=[
                        "name",
                        "phone",
                        "email",
                        "message",
                        "ip_address",
                        "user_agent",
                        "page_url",
                        "anonymized_at",
                    ]
                )
                anonymized += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Обезличено заявок: {anonymized} "
                f"(созданы до {cutoff.date()}, порог {months} мес.)."
            )
        )
