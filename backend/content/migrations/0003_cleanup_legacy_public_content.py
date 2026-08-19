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
    model = apps.get_model("content", model_name)
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
        "ContactLocation",
        ("title", "address", "short_description", "email", "work_hours"),
    )
    clean_model(
        apps,
        "PortfolioProject",
        ("title", "location", "material", "short_description", "description"),
    )
    clean_model(apps, "PortfolioImage", ("caption", "alt_text"))
    clean_model(apps, "FAQ", ("question", "answer"))
    clean_model(apps, "Advantage", ("title", "description"))
    clean_model(apps, "WorkStep", ("title", "description"))


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0002_contactlocation_portfolioproject_portfolioimage"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
