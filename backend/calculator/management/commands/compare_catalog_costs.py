from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import ProjectOffer
from catalog.pricing import PricingService
from calculator.services import HouseCalculatorService


class Command(BaseCommand):
    help = "Сравнивает V4-смету с коммерческой ценой ProjectOffer. По умолчанию — только проверенные техпаспорта."

    def add_arguments(self, parser):
        parser.add_argument("--include-unverified", action="store_true")
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, **options):
        qs = (
            ProjectOffer.objects.filter(
                project__is_active=True,
                base_price__isnull=False,
                build_package__isnull=False,
                project__area__isnull=False,
                project__width__isnull=False,
                project__length__isnull=False,
                project__floors__isnull=False,
            )
            .select_related("project__technical", "material", "build_package")
            .order_by("project__external_id", "material__sort_order", "id")
        )
        if not options["include_unverified"]:
            qs = qs.filter(project__technical__is_verified=True)
        if options["limit"]:
            qs = qs[: options["limit"]]

        calc = HouseCalculatorService()
        pricing = PricingService()
        errors = []
        skipped = 0
        for offer in qs:
            if not options["include_unverified"]:
                material_takeoff = offer.project.material_takeoffs.filter(material=offer.material, is_verified=True).first()
                if material_takeoff is None:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"SKIP {offer}: нет проверенной кубатуры для материала"))
                    continue
            try:
                result = calc.calculate_project_offer(offer)
            except ValueError as exc:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"SKIP {offer}: {exc}"))
                continue
            commercial = pricing.get_offer_price(offer)
            if not commercial:
                continue
            computed = result["total"]
            error = abs(Decimal(computed) - Decimal(commercial)) / Decimal(commercial) * 100
            errors.append(error)
            self.stdout.write(
                f"{offer.project.external_id or offer.project.slug:10} | {offer.material.code:22} | "
                f"каталог {commercial:>10,} | смета {computed:>10,} | Δ {error:6.2f}%"
            )

        if not errors:
            self.stdout.write(self.style.WARNING("Нет проектов для сравнения. Сначала заполните и подтвердите технические паспорта."))
            return
        mape = sum(errors, Decimal("0")) / Decimal(len(errors))
        self.stdout.write("-")
        self.stdout.write(f"Сравнено: {len(errors)}; пропущено: {skipped}; MAPE: {mape:.2f}%")
