from django.db import migrations


REPLACEMENTS = (
    ("info@stroidacha.local", "info@brusodel.ru"),
    ("info@brusoteka.ru", "info@brusodel.ru"),
    ("brusoteka.ru", "brusodel.ru"),
    ("БРУСОТЕКА", "БРУСОДЕЛ"),
    ("Брусотека", "Брусодел"),
    ("брусотека", "брусодел"),
)


def clean_text(value):
    if not isinstance(value, str) or not value:
        return value

    cleaned = value
    for old, new in REPLACEMENTS:
        cleaned = cleaned.replace(old, new)
    return cleaned


def clean_model(apps, model_name, fields):
    model = apps.get_model("seo", model_name)
    for obj in model.objects.all().iterator():
        changed = []
        for field in fields:
            value = getattr(obj, field, None)
            cleaned = clean_text(value)
            if cleaned != value:
                setattr(obj, field, cleaned)
                changed.append(field)
        if changed:
            obj.save(update_fields=changed)


def forwards(apps, schema_editor):
    clean_model(
        apps,
        "LandingPage",
        ("title", "h1", "intro_text", "main_text", "seo_title", "seo_description"),
    )
    clean_model(apps, "LandingPageFAQ", ("question", "answer"))
    clean_model(apps, "LandingPageImage", ("alt_text", "caption"))


class Migration(migrations.Migration):
    dependencies = [
        ("seo", "0002_landingpage_menu_sections"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
