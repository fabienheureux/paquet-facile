# Installation

## Prérequis

- Python 3.10 ou supérieur
- Django 4.2 ou supérieur
- Wagtail 6.0 ou supérieur

## Installation via pip

```bash
pip install sites-conformes
```

## Configuration

Ajoutez la configuration suivante à votre fichier `settings.py` :

```python
# =====================
# SITES FACILES CONFIG
# ======================

TEMPLATES[0]["OPTIONS"]["context_processors"].extend([
    "wagtailmenus.context_processors.wagtailmenus",
    "sites_conformes.content_manager.context_processors.skiplinks",
    "sites_conformes.content_manager.context_processors.mega_menus",
])

INSTALLED_APPS.extend([
    "dsfr",
    "sites_conformes",
    "sites_conformes.blog",
    "sites_conformes.content_manager",
    "sites_conformes.events",
    "wagtail.contrib.settings",
    "wagtail.contrib.typed_table_block",
    "wagtail.contrib.routable_page",
    "wagtail_modeladmin",
    "wagtailmenus",
    "wagtailmarkdown",
    "sites_conformes.proconnect",
])

WAGTAILADMIN_PATH = "admin/"
TESTING = False
HOST_URL = "localhost"
PROCONNECT_ACTIVATED = False
HOST_PROTO = "http"
WAGTAIL_I18N_ENABLED = True
```

## Migrations et collecte des fichiers statiques

Après la configuration, exécutez :

```bash
python manage.py migrate
python manage.py collectstatic
```

## Prochaines étapes

- [Configuration avancée →](configuration.md)
