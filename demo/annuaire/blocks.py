from wagtail import blocks


class ListePsychologuesBlock(blocks.StaticBlock):
    """Affiche la liste des psychologues sur une carte interactive.

    `StaticBlock` n'a pas de champs éditables : l'éditeur dépose le bloc, le
    template récupère les données via `get_context()`. Idéal pour des données
    qui vivent dans la base et ne se gèrent pas dans l'éditeur de page.
    """

    class Meta:
        icon = "group"
        label = "Liste des psychologues (carte)"
        template = "annuaire/blocks/liste_psychologues.html"
        admin_text = "Affiche tous les psychologues sur une carte Carte Facile."

    def get_context(self, value, parent_context=None):
        from .models import Psychologue

        context = super().get_context(value, parent_context=parent_context)
        qs = Psychologue.objects.all()
        context["psychologues"] = qs
        # Sérialisation JSON-safe (consommée côté JS via json_script).
        # Les DecimalField sont convertis en float pour rester JSON-natif.
        context["psychologues_geojson"] = [
            {
                "nom": psy.nom,
                "ville": psy.ville,
                "lat": float(psy.latitude),
                "lng": float(psy.longitude),
            }
            for psy in qs
        ]
        return context
