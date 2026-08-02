from django.db import migrations


def seed_promotions(apps, schema_editor):
    SitePromotion = apps.get_model("catalog", "SitePromotion")
    promotions = (
        ("free-delivery", "Бесплатная доставка до 500 км", "От нашего производства до вашего участка.", 10),
        ("free-replanning", "Бесплатная перепланировка", "Адаптируем типовой проект под потребности вашей семьи.", 20),
        ("opening-bars-gift", "Ройки в проёмы в подарок", "Предложение действует для домов из сухого материала.", 30),
        ("generator", "Бензогенератор на время строительства", "Обеспечим бригаду электричеством на участке.", 40),
        ("site-cabin-gift", "Бытовка в подарок", "При заказе дома стоимостью свыше 3 млн рублей.", 50),
        ("entrance-door-gift", "Входная дверь в подарок", "Предложение действует для домов из сухого материала.", 60),
    )
    for code, title, description, sort_order in promotions:
        SitePromotion.objects.update_or_create(
            code=code,
            defaults={
                "title": title,
                "description": description,
                "button_label": "Получить предложение",
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("catalog", "0011_project_page_content")]

    operations = [migrations.RunPython(seed_promotions, noop_reverse)]
