import annuaire.blocks
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("wagtailcore", "0040_page_draft_title"),
    ]

    operations = [
        migrations.CreateModel(
            name="Psychologue",
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
                ("nom", models.CharField(max_length=120)),
                ("ville", models.CharField(max_length=80)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("telephone", models.CharField(blank=True, max_length=20)),
                (
                    "latitude",
                    models.DecimalField(
                        decimal_places=6,
                        help_text="Latitude WGS84 (ex: 48.856614 pour Paris)",
                        max_digits=9,
                    ),
                ),
                (
                    "longitude",
                    models.DecimalField(
                        decimal_places=6,
                        help_text="Longitude WGS84 (ex: 2.352222 pour Paris)",
                        max_digits=9,
                    ),
                ),
            ],
            options={
                "verbose_name": "Psychologue",
                "verbose_name_plural": "Psychologues",
                "ordering": ("nom",),
            },
        ),
        migrations.CreateModel(
            name="AnnuairePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "body",
                    wagtail.fields.StreamField(
                        [("liste_psychologues", annuaire.blocks.ListePsychologuesBlock())],
                        blank=True,
                        use_json_field=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
    ]
