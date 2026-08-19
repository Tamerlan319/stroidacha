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


def forwards(apps, schema_editor):
    Project = apps.get_model("catalog", "Project")

    for project in Project.objects.all().iterator():
        changed = []
        for field in ("title", "short_description", "description", "seo_title", "seo_description"):
            value = getattr(project, field, None)
            cleaned = clean_text(value)
            if cleaned != value:
                setattr(project, field, cleaned)
                changed.append(field)
        if changed:
            project.save(update_fields=changed)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0012_seed_site_promotions"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
