from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_catalog_v2_domain")]

    operations = [
        migrations.AddConstraint(
            model_name="projectimage",
            constraint=models.UniqueConstraint(
                fields=("project",),
                condition=Q(is_primary=True),
                name="uniq_primary_image_per_project",
            ),
        ),
    ]
