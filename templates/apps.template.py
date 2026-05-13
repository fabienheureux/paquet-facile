from django.apps import AppConfig


class {PackageName}AppConfig(AppConfig):
    name = "{package_name}"
    label = "{package_name}"
    # Brand name — kept untranslated so makemessages doesn't churn locale files.
    verbose_name = "{package_verbose_name}"
    default_auto_field = "django.db.models.AutoField"
