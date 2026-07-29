from django.db import migrations


MATERIALS = [
    {
        "code": "ordinary-150x150",
        "title": "Обычный брус 150×150",
        "group_match": "Обычный брус",
        "title_match": "150x150",
        "fallback_price_per_m2": 13173,
        "description": "Базовый вариант для сезонного дома.",
        "source_note": "stroydacha.online, ДБ-01: 685 000 ₽ / 52 м²",
        "sort_order": 10,
    },
    {
        "code": "ordinary-150x200",
        "title": "Обычный брус 150×200",
        "group_match": "Обычный брус",
        "title_match": "150x200",
        "fallback_price_per_m2": 16038,
        "description": "Увеличенное сечение обычного бруса.",
        "source_note": "stroydacha.online, ДБ-01: 834 000 ₽ / 52 м²",
        "sort_order": 20,
    },
    {
        "code": "profiled-145x145",
        "title": "Профилированный брус 145×145",
        "group_match": "Профилированный брус",
        "title_match": "145x145",
        "fallback_price_per_m2": 15173,
        "description": "Профилированный брус стандартного сечения.",
        "source_note": "stroydacha.online, ДБ-01: 789 000 ₽ / 52 м²",
        "sort_order": 30,
    },
    {
        "code": "profiled-145x195",
        "title": "Профилированный брус 145×195",
        "group_match": "Профилированный брус",
        "title_match": "145x195",
        "fallback_price_per_m2": 18327,
        "description": "Более тёплое сечение профилированного бруса.",
        "source_note": "stroydacha.online, ДБ-01: 953 000 ₽ / 52 м²",
        "sort_order": 40,
    },
    {
        "code": "dry-140x140",
        "title": "Брус камерной сушки 140×140",
        "group_match": "камерной сушки",
        "title_match": "140x140",
        "fallback_price_per_m2": 17173,
        "description": "Профилированный брус камерной сушки.",
        "source_note": "stroydacha.online, ДБ-01: 893 000 ₽ / 52 м²",
        "sort_order": 50,
    },
    {
        "code": "dry-140x190",
        "title": "Брус камерной сушки 140×190",
        "group_match": "камерной сушки",
        "title_match": "140x190",
        "fallback_price_per_m2": 20904,
        "description": "Увеличенное сечение сухого профилированного бруса.",
        "source_note": "stroydacha.online, ДБ-01: 1 087 000 ₽ / 52 м²",
        "sort_order": 60,
    },
]

EXTRAS = [
    {
        "kind": "foundation",
        "code": "screw-piles",
        "title": "Свайно-винтовой фундамент",
        "group_match": "Фундамент",
        "title_match": "Свайн",
        "fallback_price_per_footprint_m2": 2972,
        "minimum_price": 107000,
        "source_note": "stroydacha.online, ДБ-01: 107 000 ₽ при габаритах 6×6",
        "sort_order": 10,
    },
    {
        "kind": "foundation",
        "code": "reinforced-piles",
        "title": "ЖБ сваи (ГОСТ)",
        "group_match": "Фундамент",
        "title_match": "сваи",
        "fallback_price_per_footprint_m2": 3861,
        "minimum_price": 139000,
        "source_note": "stroydacha.online, ДБ-01: 139 000 ₽ при габаритах 6×6",
        "sort_order": 20,
    },
    {
        "kind": "roof",
        "code": "metal-tile",
        "title": "Металлочерепица",
        "group_match": "Кров",
        "title_match": "Металлочерепица",
        "fallback_price_per_footprint_m2": 3722,
        "minimum_price": 134000,
        "source_note": "stroydacha.online, ДБ-01: 134 000 ₽ при габаритах 6×6",
        "sort_order": 10,
    },
    {
        "kind": "roof",
        "code": "ondulin",
        "title": "Ондулин",
        "group_match": "Кров",
        "title_match": "Ондулин",
        "fallback_price_per_footprint_m2": 2944,
        "minimum_price": 106000,
        "source_note": "stroydacha.online, ДБ-01: 106 000 ₽ при габаритах 6×6",
        "sort_order": 20,
    },
    {
        "kind": "roof",
        "code": "flexible-shingles",
        "title": "Гибкая черепица",
        "group_match": "Кров",
        "title_match": "Гибкая",
        "fallback_price_per_footprint_m2": 6250,
        "minimum_price": 225000,
        "source_note": "stroydacha.online, ДБ-01: 225 000 ₽ при габаритах 6×6",
        "sort_order": 30,
    },
    {
        "kind": "roof",
        "code": "metal-profile",
        "title": "Металлопрофиль",
        "group_match": "Кров",
        "title_match": "Металлопрофиль",
        "fallback_price_per_footprint_m2": 3361,
        "minimum_price": 121000,
        "source_note": "stroydacha.online, ДБ-01: 121 000 ₽ при габаритах 6×6",
        "sort_order": 40,
    },
]


def seed(apps, schema_editor):
    Settings = apps.get_model("calculator", "CalculatorSettings")
    Material = apps.get_model("calculator", "CalculatorMaterial")
    Extra = apps.get_model("calculator", "CalculatorExtraOption")

    Settings.objects.get_or_create(
        title="Основной калькулятор",
        defaults={
            "min_area": 20,
            "max_area": 600,
            "price_range_percent": 8,
            "max_references": 5,
            "is_active": True,
        },
    )

    for item in MATERIALS:
        Material.objects.update_or_create(code=item["code"], defaults=item)

    for item in EXTRAS:
        Extra.objects.update_or_create(code=item["code"], defaults=item)


def unseed(apps, schema_editor):
    Material = apps.get_model("calculator", "CalculatorMaterial")
    Extra = apps.get_model("calculator", "CalculatorExtraOption")
    Material.objects.filter(code__in=[item["code"] for item in MATERIALS]).delete()
    Extra.objects.filter(code__in=[item["code"] for item in EXTRAS]).delete()


class Migration(migrations.Migration):
    dependencies = [("calculator", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
