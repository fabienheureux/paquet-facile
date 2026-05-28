from .base import *  # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-+^2fx_l%x&0@r9%io-%cujw2@c3f+3v$bb^pea1gp78$khabgr"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS.extend(["debug_toolbar"])  # noqa: F405


try:
    from .local import *  # noqa: F403
except ImportError:
    pass
