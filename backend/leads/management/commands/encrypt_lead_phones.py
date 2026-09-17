from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from leads.crypto import PREFIX
from leads.models import Lead


class Command(BaseCommand):
    """Шифрует телефоны заявок, сохранённые до того, как задали ключ.

    Запускать один раз после того, как в backend/.env.prod появился
    LEAD_PHONE_ENCRYPTION_KEY и backend перезапущен. Повторный запуск ничего
    не меняет: уже зашифрованные номера пропускаются.
    """

    help = "Шифрует телефоны в заявках, которые сохранены без шифрования."

    def handle(self, *args, **options):
        if not getattr(settings, "LEAD_PHONE_ENCRYPTION_KEY", ""):
            raise CommandError(
                "LEAD_PHONE_ENCRYPTION_KEY не задан — шифровать нечем. "
                "Задайте ключ в backend/.env.prod и перезапустите backend."
            )

        queryset = Lead.objects.exclude(phone="").exclude(phone__startswith=PREFIX)
        encrypted = 0

        for lead in queryset.iterator():
            # Номер без метки прочитан из базы как есть; при сохранении поле
            # его зашифрует (leads/crypto.py).
            lead.save(update_fields=["phone"])
            encrypted += 1

        self.stdout.write(self.style.SUCCESS(f"Зашифровано телефонов: {encrypted}."))
