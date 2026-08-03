# Generated manually for lead file attachments.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeadAttachment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        upload_to="leads/attachments/%Y/%m/%d",
                        verbose_name="Файл",
                    ),
                ),
                (
                    "original_name",
                    models.CharField(
                        max_length=255,
                        verbose_name="Исходное имя",
                    ),
                ),
                (
                    "content_type",
                    models.CharField(
                        blank=True,
                        max_length=100,
                        verbose_name="Тип файла",
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Размер, байт",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Загружен",
                    ),
                ),
                (
                    "lead",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="leads.lead",
                        verbose_name="Заявка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Файл заявки",
                "verbose_name_plural": "Файлы заявки",
                "ordering": ["id"],
            },
        ),
    ]
