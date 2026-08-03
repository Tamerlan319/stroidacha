from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0002_lead_attachments"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="region",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="Регион строительства",
            ),
        ),
        migrations.AlterField(
            model_name="lead",
            name="source",
            field=models.CharField(
                choices=[
                    ("callback", "Заказать звонок"),
                    ("project_order", "Заказать проект"),
                    ("project_changes", "Внести правки в проект"),
                    ("own_project", "Прислать свой проект"),
                    ("calculator", "Калькулятор"),
                    ("contact_form", "Форма обратной связи"),
                    (
                        "home_phone_consultation",
                        "Консультация с главной страницы",
                    ),
                ],
                default="contact_form",
                max_length=50,
                verbose_name="Источник заявки",
            ),
        ),
    ]
