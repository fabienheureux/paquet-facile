# Installation

Ce guide explique comment ajouter `sites-conformes` à un projet Django existant.
Si vous voulez **migrer un site Sites Conformes existant** vers la version
packagée, consultez plutôt {doc}`../migration`.

## Prérequis

- Python 3.12 ou supérieur
- Django 6.0 ou supérieur
- Wagtail 7.2 ou supérieur
- PostgreSQL

## Installation via uv

```bash
uv add sites-conformes
```

(Si vous utilisez encore `pip` : `pip install sites-conformes`.)

## Configuration

Ajoutez la configuration suivante à votre `config/settings.py`.

### INSTALLED_APPS

```python
INSTALLED_APPS.extend([
    "dsfr",
    # Le package lui-même (fournit les templates de base partagés)
    "sites_conformes",
    # Les apps qu'il contient
    "sites_conformes.core",
    "sites_conformes.blog",
    "sites_conformes.events",
    "sites_conformes.forms",
    "sites_conformes.menus",
    "sites_conformes.dashboard",
    "sites_conformes.proconnect",
    # Dépendances Wagtail/tierces requises
    "wagtail.contrib.settings",
    "wagtail.contrib.typed_table_block",
    "wagtail.contrib.routable_page",
    "wagtail_modeladmin",
    "wagtailmenus",
    "wagtailmarkdown",
    "wagtail_honeypot",
])

# Optionnel — stockage des médias en base de données (Scalingo, Heroku, etc.)
if SF_USE_DB_STORAGE:
    INSTALLED_APPS.append("sites_conformes.db_storage")
```

### Context processors

```python
TEMPLATES[0]["OPTIONS"]["context_processors"].extend([
    "wagtailmenus.context_processors.wagtailmenus",
    "sites_conformes.core.context_processors.skiplinks",
    "sites_conformes.core.context_processors.mega_menus",
])
```

### Templates et fichiers statiques

Le package fournit des templates de base partagés (`base.html`, blocs DSFR,
menus) et des assets statiques. Pour que Django les trouve via le loader
filesystem, ajoutez les chemins suivants :

```python
import sites_conformes

PACKAGE_DIR = Path(sites_conformes.__file__).resolve().parent

TEMPLATES[0]["DIRS"].append(PACKAGE_DIR / "templates")
STATICFILES_DIRS = (PACKAGE_DIR / "static",) + STATICFILES_DIRS
```

(`APP_DIRS = True` couvre déjà les templates spécifiques à chaque app —
`sites_conformes/blog/templates/`, etc. Les ajouts ci-dessus servent
uniquement aux templates au niveau du package.)

### Réglages divers

```python
WAGTAILADMIN_PATH = "admin/"
HOST_URL = "localhost"
HOST_PROTO = "http"
WAGTAIL_I18N_ENABLED = True
PROCONNECT_ACTIVATED = False
```

Voir {doc}`configuration` pour la liste complète des réglages disponibles.

## Migrations et collecte des fichiers statiques

```bash
python manage.py migrate
python manage.py collectstatic
```

## Prochaines étapes

- {doc}`configuration` — réglages spécifiques
- {doc}`../migration` — migration depuis un site Sites Conformes existant
