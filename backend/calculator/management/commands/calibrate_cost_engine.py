from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "V4: автоматическая регрессионная калибровка runtime-ставок отключена."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        message = (
            "Calculator V4 больше не восстанавливает офисные ставки из конечных цен каталога: "
            "такое разложение неоднозначно и уже показало нестабильные коэффициенты.\n\n"
            "Теперь:\n"
            "  1) количества хранятся в техническом паспорте проекта;\n"
            "  2) ставки с историей — Каталог → Сметные ставки;\n"
            "  3) python manage.py audit_cost_rates проверяет полноту прайса;\n"
            "  4) python manage.py compare_catalog_costs сравнивает смету с ProjectOffer.\n"
            "Для переноса уже вручную проверенных V3-ставок используйте "
            "python manage.py bootstrap_cost_rates (сначала без --apply)."
        )
        if options.get("apply") or options.get("force"):
            raise CommandError(message)
        self.stdout.write(self.style.WARNING(message))
