from django.db import migrations


def seed_pricing(apps, schema_editor):
    PricingSettings = apps.get_model("catalog", "PricingSettings")
    PricingRule = apps.get_model("catalog", "PricingRule")

    settings, _ = PricingSettings.objects.get_or_create(
        title="Основная индексация",
        defaults={
            "house_percent": 0,
            "addon_percent": 0,
            "rounding_step": 1000,
            "is_active": True,
        },
    )

    rules = [
        ("material", "Обычный брус 150×150", "Обычный брус", "150x150", 10),
        ("material", "Обычный брус 150×200", "Обычный брус", "150x200", 20),
        ("material", "Профилированный брус 145×145", "Профилированный брус", "145x145", 30),
        ("material", "Профилированный брус 145×195", "Профилированный брус", "145x195", 40),
        ("material", "Брус камерной сушки 140×140", "Брус камерной сушки", "140x140", 50),
        ("material", "Брус камерной сушки 140×190", "Брус камерной сушки", "140x190", 60),
        ("addon", "Свайный фундамент", "Фундамент", "Свайный", 110),
        ("addon", "ЖБ сваи", "Фундамент", "ЖБ", 120),
        ("addon", "Металлочерепица", "Кровля", "Металлочерепица", 210),
        ("addon", "Ондулин", "Кровля", "Ондулин", 220),
        ("addon", "Гибкая черепица", "Кровля", "Гибкая черепица", 230),
        ("addon", "Металлопрофиль", "Кровля", "Металлопрофиль", 240),
    ]

    for kind, title, group_match, title_match, sort_order in rules:
        PricingRule.objects.get_or_create(
            settings=settings,
            kind=kind,
            title=title,
            defaults={
                "group_match": group_match,
                "title_match": title_match,
                "percent_change": 0,
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def reverse_seed(apps, schema_editor):
    PricingSettings = apps.get_model("catalog", "PricingSettings")
    PricingSettings.objects.filter(title="Основная индексация").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_pricing_indexation"),
    ]

    operations = [
        migrations.RunPython(seed_pricing, reverse_seed),
    ]
