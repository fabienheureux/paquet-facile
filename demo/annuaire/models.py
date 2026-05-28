from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.snippets.models import register_snippet

from .blocks import ListePsychologuesBlock


@register_snippet
class Psychologue(models.Model):
    """Annuaire snippet — one entry per psychologue.

    Coordinates are stored as DecimalField (no PostGIS dependency). For radius
    searches or other spatial queries upgrade to django.contrib.gis.
    """

    nom = models.CharField(max_length=120)
    ville = models.CharField(max_length=80)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Latitude WGS84 (ex: 48.856614 pour Paris)",
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text="Longitude WGS84 (ex: 2.352222 pour Paris)",
    )

    panels = [
        FieldPanel("nom"),
        FieldPanel("ville"),
        FieldPanel("email"),
        FieldPanel("telephone"),
        FieldPanel("latitude"),
        FieldPanel("longitude"),
    ]

    class Meta:
        ordering = ("nom",)
        verbose_name = "Psychologue"
        verbose_name_plural = "Psychologues"

    def __str__(self):
        return f"{self.nom} ({self.ville})"


class AnnuairePage(Page):
    """Wagtail page with a StreamField that surfaces the annuaire block.

    Editors create a page of this type, drop the "Liste des psychologues
    (carte)" block where they want it, and the map renders with all
    Psychologue snippets currently in the database.
    """

    body = StreamField(
        [("liste_psychologues", ListePsychologuesBlock())],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]
