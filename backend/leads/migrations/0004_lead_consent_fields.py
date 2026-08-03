from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0003_lead_region_and_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="consent_given_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Дата согласия",
            ),
        ),
        migrations.AddField(
            model_name="lead",
            name="consent_version",
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name="Версия согласия",
            ),
        ),
    ]
