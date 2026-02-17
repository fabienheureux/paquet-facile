# Sites Conformes - Package Python

Ce dépôt contient les outils permettant de transformer [Sites Faciles](https://github.com/numerique-gouv/sites-faciles) en package Python réutilisable.

**Package publié :** [sites-conformes sur PyPI](https://pypi.org/project/sites-conformes/)

## 🎯 Objectif

Sites Faciles est un gestionnaire de contenu basé sur Wagtail et le Système de design de l'État (DSFR). Ce projet le rend installable comme dépendance dans d'autres projets Wagtail.

C'est un soft-fork : aucune fonctionnalité n'est ajoutée, seule la structure du code est adaptée pour l'empaquetage (déplacement de fichiers, ajout de namespaces).

## 🔄 Synchronisation avec le dépôt upstream

Le script `paquet_facile.py` permet de synchroniser ce fork avec le dépôt Sites Faciles officiel et d'appliquer automatiquement les transformations nécessaires à l'empaquetage.

### Structure générée

Le script crée une structure de package Python standard :

```
sites_conformes/              # Racine du package
├── pyproject.toml         # Configuration du package
├── README.md              # Documentation du package
└── sites_conformes/          # Code Python
    ├── __init__.py
    ├── apps.py
    ├── blog/
    ├── content_manager/
    ├── events/
    ├── config/
    ├── management/
    │   └── commands/
    │       └── migrate_contenttype.py
    └── ...
```

### Utilisation du script

```bash
# Synchroniser avec la version v2.1.0
./paquet_facile.py v2.1.0

# Mode dry-run (voir les changements sans les appliquer)
./paquet_facile.py v2.1.0 --dry-run -v

# Avec une configuration personnalisée
./paquet_facile.py v2.2.0 -c ma-config.yml
```

### Options disponibles

- `tag` : Version git à synchroniser (requis, ex: v2.1.0)
- `-v, -vv` : Augmente la verbosité des logs
- `--dry-run` : Simule les changements sans modifier les fichiers
- `-j N` : Nombre de threads pour le traitement parallèle
- `-c CONFIG` : Configuration YAML (défaut: search-and-replace.yml)
- `--repo URL` : URL du dépôt source

### Configuration

Le fichier `search-and-replace.yml` permet de configurer :
- Le nom du package (`package_name`)
- Les règles de transformation du code
- Les applications Django à inclure

Le versioning suit celui de Sites Faciles (tags iso).

## 📦 Utilisation du package

### Installation locale (développement)

```bash
# Depuis un autre projet
pip install -e /chemin/vers/sites-faciles/sites_conformes
```

### Installation depuis PyPI

```bash
pip install sites-conformes
```

### Configuration Django

Voir le [README du package](./sites_conformes/README.md) pour la configuration complète.

Exemple minimal :

```python
INSTALLED_APPS.extend([
    "dsfr",
    "sites_conformes",
    "sites_conformes.blog",
    "sites_conformes.content_manager",
    "sites_conformes.events",
    "wagtail.contrib.settings",
    "wagtail_modeladmin",
    "wagtailmenus",
    "wagtailmarkdown",
])
```

Configuration des URLs :

```python
# urls.py
from sites_conformes.config.urls import *
```

### Migration depuis Sites Faciles

Si vous migrez depuis le dépôt Sites Faciles :

```bash
# 1. Installer le package et configurer INSTALLED_APPS
pip install sites-conformes

# 2. Exécuter les migrations
python manage.py migrate

# 3. Migrer les ContentTypes
python manage.py migrate_contenttype
```

Voir le [README du package](./sites_conformes/README.md) pour plus de détails.

## 🧪 Projet de démonstration

Le répertoire `demo/` contient un projet Wagtail minimal utilisant le package.

```bash
cd demo
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```

## 📚 Ressources

- **Documentation complète :** Voir le [README du package](./sites_conformes/README.md)
- **Projet original :** [Sites Faciles sur GitHub](https://github.com/numerique-gouv/sites-faciles)
- **Package PyPI :** [sites-conformes](https://pypi.org/project/sites-conformes/)
- **Exemple d'intégration :** [PR Que Faire de Mes Objets](https://github.com/incubateur-ademe/quefairedemesobjets/pull/1375)
