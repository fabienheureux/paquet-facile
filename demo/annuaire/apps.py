from django.apps import AppConfig


class AnnuaireConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "annuaire"
    verbose_name = "Annuaire"

    def ready(self):
        # Le router Wagtail est instancié par le projet (demo.api).
        from demo.api import api_router

        from .api import PsychologuesAPIViewSet

        api_router.register_endpoint("psychologues", PsychologuesAPIViewSet)
