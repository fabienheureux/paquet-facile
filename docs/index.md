# Documentation sites-conformes

Bienvenue dans la documentation de **sites-conformes**, un gestionnaire de contenu basé sur Wagtail et le Système de design de l'État (DSFR).

:::{note}
Cette documentation concerne les fonctionnalités spécifiques à sites-conformes. Pour la documentation générale de Wagtail, consultez [docs.wagtail.org](https://docs.wagtail.org/).
:::

## Qu'est-ce que sites-conformes ?

sites-conformes est un package Python qui étend Wagtail pour créer des sites conformes au [Système de Design de l'État français (DSFR)](https://www.systeme-de-design.gouv.fr/).

**Fonctionnalités principales :**
- 📝 Modèles de pages pour blog, événements et contenu
- 🧩 Blocs StreamField conformes au DSFR
- 🧭 Gabarits et menus adaptés au DSFR
- ♿ Accessibilité RGAA intégrée

```{toctree}
---
maxdepth: 2
caption: Documentation
---
guide/installation
guide/configuration
guide/blocs-personnalises
reference/settings
migration
changelog
```

## Démarrage rapide

```bash
# Installation
pip install sites-conformes

# Ajouter à INSTALLED_APPS
INSTALLED_APPS = [
    "sites_conformes",
    "sites_conformes.blog",
    "sites_conformes.content_manager",
    "sites_conformes.events",
    # ...
]
```

[Voir le guide complet d'installation →](guide/installation.md)

## Besoin d'aide ?

- 📖 [Documentation Wagtail](https://docs.wagtail.org/)
- 💬 [GitHub Discussions](https://github.com/numerique-gouv/sites-faciles/discussions)
- 🐛 [Signaler un bug](https://github.com/numerique-gouv/sites-faciles/issues)
