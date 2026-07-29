from django.core.management.base import BaseCommand
from django.db.models import Count

from catalog.models import Material, Project, ProjectOffer, ProjectOptionPrice
from catalog.pricing import PricingService


class Command(BaseCommand):
    help = "Проверяет нормализованные цены каталога после миграции."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=20, help="Сколько проблемных проектов показать.")

    def handle(self, *args, **options):
        limit = max(options["limit"], 1)
        projects = Project.objects.filter(construction_type=Project.ConstructionType.TIMBER)
        pricing = PricingService()

        self.stdout.write(f"Проектов домов: {projects.count()}")
        self.stdout.write(f"Материалов в справочнике: {Material.objects.count()}")
        self.stdout.write(f"Ценовых предложений: {ProjectOffer.objects.count()}")
        self.stdout.write(f"Цен дополнительных опций: {ProjectOptionPrice.objects.count()}")

        without_offers = projects.annotate(offer_count=Count("offers")).filter(offer_count=0)
        self.stdout.write(f"Домов без цен по материалам: {without_offers.count()}")
        for project in without_offers[:limit]:
            self.stdout.write(f"  - {project.external_id or project.pk}: {project.title}")

        mismatches = []
        for project in projects.prefetch_related("offers__material"):
            base_prices = [offer.base_price for offer in project.offers.all() if offer.base_price is not None]
            if not base_prices or project.price_from is None:
                continue
            expected = min(base_prices)
            if expected != project.price_from:
                mismatches.append((project, project.price_from, expected, pricing.get_project_price_from(project)))

        self.stdout.write(f"Различий между резервным price_from и минимумом предложений: {len(mismatches)}")
        for project, fallback, expected, effective in mismatches[:limit]:
            self.stdout.write(
                f"  - {project.external_id or project.pk}: fallback={fallback}; base_min={expected}; site={effective}"
            )

        if without_offers.exists():
            self.stdout.write(self.style.WARNING("Есть проекты без нормализованных цен — проверь их вручную."))
        else:
            self.stdout.write(self.style.SUCCESS("Все дома имеют нормализованные цены по материалам."))
