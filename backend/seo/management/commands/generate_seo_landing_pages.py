from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Count

from catalog.models import Project, ProjectCategory

from ...models import LandingPage, LandingPageFAQ


# Как называть страницы и в каком роде склонять существительное ("дом"/
# "баня") в автосгенерированных вопросах FAQ размерных страниц.
CATEGORY_CONFIG = {
    "houses": {
        "slug_prefix": "doma-iz-brusa",
        "hub_phrase": "Дома из бруса",
        "noun_nom": "дом",
        "noun_gen": "дома",
        "noun_acc": "дом",
    },
    "baths": {
        "slug_prefix": "bani-iz-brusa",
        "hub_phrase": "Бани из бруса",
        "noun_nom": "баня",
        "noun_gen": "бани",
        "noun_acc": "баню",
    },
}

# Текст региональных страниц (Москва и область) написан руками, а не
# шаблоном по CATEGORY_CONFIG: центральный элемент этих страниц — честный
# ответ на реальный вопрос клиента ("а почему у вас нет офиса в Москве"), а
# не подстановка слова в заготовку. Такое лучше не автогенерировать.
#
# У компании нет офиса или шоурума в Москве (реальное производство — в
# Костромской области) — ни здесь, ни где-либо ещё на сайте нельзя утверждать
# обратное. См. FAQ ниже: этот факт сознательно проговаривается прямо, а не
# скрывается — это и честно, и снимает возражение до звонка менеджеру.
REGION_PAGES = {
    "houses": {
        "slug": "doma-iz-brusa-moskva",
        "title": "Дома из бруса — Москва и область",
        "h1": "Дома из бруса под ключ с доставкой в Москву и область",
        "intro_text": (
            "Строим и доставляем дома из бруса в Москву и Московскую "
            "область с собственного производства в Костромской области. "
            "Консультация и расчёт — дистанционно, по телефону и "
            "видеосвязи."
        ),
        "main_text": (
            "Хотя производство находится в Костромской области, мы "
            "регулярно строим для заказчиков из Москвы и Подмосковья: "
            "комплект дома и монтажная бригада выезжают в любой район "
            "области, а собственное производство исключает наценку "
            "посредников и позволяет контролировать качество бруса на "
            "каждом этапе.\n\n"
            "Офиса или шоурума в Москве у нас пока нет — вся консультация, "
            "подбор проекта и предварительный расчёт проходят удалённо: по "
            "телефону, видеосвязи и фото или видео вашего участка. Договор "
            "и документы можно подписать дистанционно, а увидеть примеры "
            "реализованных объектов — в разделе «Портфолио»."
        ),
        "seo_title": (
            "Дома из бруса под ключ в Москве и области — доставка и "
            "строительство | Брусодел"
        ),
        "seo_description": (
            "Строим дома из бруса для Москвы и Московской области. Свой "
            "завод, доставка комплекта и бригады по всей области, расчёт и "
            "консультация дистанционно."
        ),
        "faqs": [
            (
                "Строите ли вы дома из бруса в Москве и Московской "
                "области?",
                "Да, комплект дома и монтажная бригада выезжают в любой "
                "район Москвы и Московской области. Точные сроки и "
                "стоимость доставки зависят от расстояния до участка и "
                "уточняются менеджером после заявки.",
            ),
            (
                "У вас есть офис или шоурум в Москве?",
                "Пока нет — очной точки в Москве у нас нет. Консультация, "
                "подбор проекта и расчёт стоимости проходят дистанционно: "
                "по телефону и видеосвязи, документы можно подписать "
                "удалённо.",
            ),
            (
                "Как проходит замер и консультация, если участок в "
                "Подмосковье?",
                "Пришлите фото или видео участка и его параметры — этого "
                "обычно достаточно для предварительного расчёта. При "
                "необходимости выезд на участок для замера согласовывается "
                "отдельно.",
            ),
            (
                "Почему производство находится не в Москве и как это "
                "влияет на цену и сроки?",
                "Собственное производство расположено в Костромской "
                "области. Это исключает наценку посредников и позволяет "
                "контролировать качество бруса на каждом этапе — доставка "
                "до Москвы и области закладывается в общий график "
                "строительства.",
            ),
            (
                "Можно ли посмотреть готовые дома компании?",
                "Фото и описания реализованных проектов — в разделе "
                "«Портфолио». Если хотите увидеть объект вживую, оставьте "
                "заявку — подскажем ближайший к вам построенный дом, "
                "который можно посмотреть по согласованию с владельцем.",
            ),
        ],
    },
    "baths": {
        "slug": "bani-iz-brusa-moskva",
        "title": "Бани из бруса — Москва и область",
        "h1": "Бани из бруса под ключ с доставкой в Москву и область",
        "intro_text": (
            "Строим и доставляем бани из бруса в Москву и Московскую "
            "область с собственного производства в Костромской области. "
            "Консультация и расчёт — дистанционно, по телефону и "
            "видеосвязи."
        ),
        "main_text": (
            "Хотя производство находится в Костромской области, мы "
            "регулярно строим бани для заказчиков из Москвы и Подмосковья: "
            "комплект и монтажная бригада выезжают в любой район области, "
            "а собственное производство исключает наценку посредников и "
            "позволяет контролировать качество бруса на каждом этапе.\n\n"
            "Офиса или шоурума в Москве у нас пока нет — вся консультация, "
            "подбор проекта и предварительный расчёт проходят удалённо: по "
            "телефону, видеосвязи и фото или видео вашего участка. Договор "
            "и документы можно подписать дистанционно, а увидеть примеры "
            "реализованных объектов — в разделе «Портфолио»."
        ),
        "seo_title": (
            "Бани из бруса под ключ в Москве и области — доставка и "
            "строительство | Брусодел"
        ),
        "seo_description": (
            "Строим бани из бруса для Москвы и Московской области. Свой "
            "завод, доставка комплекта и бригады по всей области, расчёт и "
            "консультация дистанционно."
        ),
        "faqs": [
            (
                "Строите ли вы бани из бруса в Москве и Московской "
                "области?",
                "Да, комплект бани и монтажная бригада выезжают в любой "
                "район Москвы и Московской области. Точные сроки и "
                "стоимость доставки зависят от расстояния до участка и "
                "уточняются менеджером после заявки.",
            ),
            (
                "У вас есть офис или шоурум в Москве?",
                "Пока нет — очной точки в Москве у нас нет. Консультация, "
                "подбор проекта и расчёт стоимости проходят дистанционно: "
                "по телефону и видеосвязи, документы можно подписать "
                "удалённо.",
            ),
            (
                "Как проходит консультация, если участок в Подмосковье?",
                "Пришлите фото или видео участка и его параметры — этого "
                "обычно достаточно для предварительного расчёта. При "
                "необходимости выезд на участок для замера согласовывается "
                "отдельно.",
            ),
            (
                "Почему производство находится не в Москве и как это "
                "влияет на цену и сроки?",
                "Собственное производство расположено в Костромской "
                "области. Это исключает наценку посредников и позволяет "
                "контролировать качество бруса на каждом этапе — доставка "
                "до Москвы и области закладывается в общий график "
                "строительства.",
            ),
            (
                "Можно ли посмотреть готовые бани компании?",
                "Фото и описания реализованных проектов — в разделе "
                "«Портфолио». Если хотите увидеть объект вживую, оставьте "
                "заявку — подскажем ближайшую к вам построенную баню, "
                "которую можно посмотреть по согласованию с владельцем.",
            ),
        ],
    },
}


def format_dimension(value: Decimal) -> str:
    """Строка без незначащих нулей: 6.00 → "6", 6.50 → "6.5", 60.00 → "60".

    Postgres хранит width/length как NUMERIC(6,2), поэтому значения приходят
    как Decimal с фиксированными двумя знаками после точки (Decimal("6.00")).
    В отличие от float, format(decimal, "g") эти незначащие нули НЕ убирает —
    нужно сначала normalize(), а затем отформатировать как fixed-point,
    иначе normalize() на круглых числах вроде 60.00 даёт "6E+1".
    """
    return format(value.normalize(), "f")


def slugify_dimension(value: Decimal) -> str:
    """То же самое, но без точки — LandingPage.slug не допускает unicode/точки."""
    return format_dimension(value).replace(".", "-")


class Command(BaseCommand):
    help = (
        "Создаёт SEO-страницы под конкретные размеры домов/бань (например, "
        "«Дома из бруса 7х7») по фактическим размерам из каталога, а также "
        "региональные страницы Москва/область — по аналогии с уже "
        "существующими страницами-хабами doma-iz-brusa и bani-iz-brusa. Не "
        "перезаписывает страницы, изменённые вручную в Django Admin, если "
        "не передан --overwrite."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Перезаписать текст уже существующих сгенерированных страниц.",
        )
        parser.add_argument(
            "--min-projects",
            type=int,
            default=2,
            help=(
                "Минимальное количество активных проектов одного размера, "
                "чтобы под него создавалась отдельная страница (иначе "
                "получится почти пустой каталог на странице — плохо для "
                "SEO)."
            ),
        )
        parser.add_argument(
            "--only-sizes",
            action="store_true",
            help="Создать только размерные страницы, без региональных.",
        )
        parser.add_argument(
            "--only-region",
            action="store_true",
            help="Создать только региональные страницы (Москва/область).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]
        do_sizes = not options["only_region"]
        do_region = not options["only_sizes"]

        created = updated = skipped = 0

        if do_sizes:
            self.stdout.write("Размерные страницы:")
            c, u, s = self._generate_size_pages(
                min_projects=options["min_projects"],
                dry_run=dry_run,
                overwrite=overwrite,
            )
            created += c
            updated += u
            skipped += s

        if do_region:
            self.stdout.write("Региональные страницы:")
            c, u, s = self._generate_region_pages(dry_run=dry_run, overwrite=overwrite)
            created += c
            updated += u
            skipped += s

        summary = (
            f"\nСоздано: {created}; обновлено: {updated}; пропущено: {skipped}."
        )
        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry-run завершён: БД не изменялась.{summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Готово.{summary}"))

    def _generate_size_pages(self, *, min_projects, dry_run, overwrite):
        created = updated = skipped = 0

        for category_slug, config in CATEGORY_CONFIG.items():
            category = ProjectCategory.objects.filter(slug=category_slug).first()
            if not category:
                self.stderr.write(self.style.WARNING(
                    f"  категория '{category_slug}' не найдена, пропускаю."
                ))
                continue

            size_groups = (
                Project.objects
                .filter(
                    is_active=True,
                    category=category,
                    width__isnull=False,
                    length__isnull=False,
                )
                # Project.Meta.ordering сортирует по -created_at. Без явного
                # .order_by() Django тянет это поле в GROUP BY вместе с
                # values(), и каждый проект оказывается в своей отдельной
                # "группе" из одного элемента — count__gte ниже никогда не
                # сработает.
                .order_by()
                .values("width", "length")
                .annotate(count=Count("id"))
                .filter(count__gte=min_projects)
                .order_by("width", "length")
            )

            for group in size_groups:
                width = Decimal(group["width"])
                length = Decimal(group["length"])
                size_label = f"{format_dimension(width)}х{format_dimension(length)}"
                slug = (
                    f"{config['slug_prefix']}-"
                    f"{slugify_dimension(width)}x{slugify_dimension(length)}"
                )

                existing = LandingPage.objects.filter(slug=slug).first()
                if existing and not overwrite:
                    skipped += 1
                    self.stdout.write(f"  пропущена (уже существует): {slug}")
                    continue

                footprint = width * length
                footprint_label = format_dimension(footprint)
                h1 = f"{config['hub_phrase']} {size_label} под ключ"

                fields = dict(
                    title=h1,
                    page_type=LandingPage.PageType.SIZE,
                    h1=h1,
                    category=category,
                    filter_width=width,
                    filter_length=length,
                    intro_text=(
                        f"Проекты {config['noun_gen']} {size_label} (пятно "
                        f"застройки {footprint_label} м²) с ценами и фото. "
                        "Выберите вариант ниже и получите точный расчёт под "
                        "ваши параметры."
                    ),
                    main_text=(
                        "Ниже — проекты этого размера с фото, планировками "
                        "и базовой ценой. Каждый проект можно адаптировать "
                        "под ваш участок: изменить материал стен, "
                        "комплектацию, фундамент и кровлю. Актуальная "
                        "стоимость с учётом выбранных параметров "
                        "формируется в карточке проекта и в бесплатном "
                        "расчёте по заявке."
                    ),
                    seo_title=(
                        f"{config['hub_phrase']} {size_label} под ключ — "
                        "цена, проекты, фото | Брусодел"
                    ),
                    seo_description=(
                        f"{config['hub_phrase']} {size_label}: пятно "
                        f"застройки {footprint_label} м², актуальные цены и "
                        "фото. Бесплатный расчёт по вашим параметрам."
                    ),
                )

                if dry_run:
                    action = "будет обновлена" if existing else "будет создана"
                    self.stdout.write(f"  {action}: {slug} ({h1})")
                    if existing:
                        updated += 1
                    else:
                        created += 1
                    continue

                page, was_created = LandingPage.objects.update_or_create(
                    slug=slug, defaults=fields,
                )

                faqs = [
                    (
                        f"Какая площадь застройки у {config['noun_gen']} "
                        f"{size_label}?",
                        f"Пятно застройки — {footprint_label} м². Жилая площадь "
                        "зависит от этажности и планировки конкретного "
                        "проекта — уточняется в карточке каждого варианта "
                        "ниже.",
                    ),
                    (
                        f"Сколько стоит {config['noun_nom']} {size_label}?",
                        "Стоимость зависит от материала стен, комплектации "
                        "и фундамента — базовая цена указана в каждом "
                        "проекте, а точный расчёт под ваши параметры "
                        "сделает менеджер после заявки.",
                    ),
                    (
                        f"Можно ли доставить и построить "
                        f"{config['noun_acc']} {size_label} в Москву и "
                        "область?",
                        "Да, строим и доставляем по всей России, включая "
                        "Москву и область — сроки и стоимость доставки "
                        "уточняются индивидуально.",
                    ),
                ]

                if overwrite:
                    page.faqs.all().delete()
                if overwrite or not page.faqs.exists():
                    for index, (question, answer) in enumerate(faqs):
                        LandingPageFAQ.objects.create(
                            landing_page=page,
                            question=question,
                            answer=answer,
                            sort_order=index,
                        )

                if was_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f"  создана: {slug}"))
                else:
                    updated += 1
                    self.stdout.write(self.style.WARNING(f"  обновлена: {slug}"))

        return created, updated, skipped

    def _generate_region_pages(self, *, dry_run, overwrite):
        created = updated = skipped = 0

        for category_slug, data in REGION_PAGES.items():
            category = ProjectCategory.objects.filter(slug=category_slug).first()
            if not category:
                self.stderr.write(self.style.WARNING(
                    f"  категория '{category_slug}' не найдена, пропускаю."
                ))
                continue

            slug = data["slug"]
            existing = LandingPage.objects.filter(slug=slug).first()
            if existing and not overwrite:
                skipped += 1
                self.stdout.write(f"  пропущена (уже существует): {slug}")
                continue

            fields = dict(
                title=data["title"],
                page_type=LandingPage.PageType.REGION,
                h1=data["h1"],
                category=category,
                intro_text=data["intro_text"],
                main_text=data["main_text"],
                seo_title=data["seo_title"],
                seo_description=data["seo_description"],
            )

            if dry_run:
                action = "будет обновлена" if existing else "будет создана"
                self.stdout.write(f"  {action}: {slug}")
                if existing:
                    updated += 1
                else:
                    created += 1
                continue

            page, was_created = LandingPage.objects.update_or_create(
                slug=slug, defaults=fields,
            )

            if overwrite:
                page.faqs.all().delete()
            if overwrite or not page.faqs.exists():
                for index, (question, answer) in enumerate(data["faqs"]):
                    LandingPageFAQ.objects.create(
                        landing_page=page,
                        question=question,
                        answer=answer,
                        sort_order=index,
                    )

            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  создана: {slug}"))
            else:
                updated += 1
                self.stdout.write(self.style.WARNING(f"  обновлена: {slug}"))

        return created, updated, skipped
