# Migrer un site existant vers `sites-conformes` (package)

Ce guide concerne les sites déjà construits avec **Sites Conformes** (ou son
ancêtre **Sites Faciles**) qui veulent passer à la version packagée distribuée
sur PyPI. Le but : remplacer une copie locale du code par une dépendance
versionnée, tout en gardant la base de données existante.

## 1. Sauvegarder

```bash
python manage.py dumpdata > backup.json
```

Sauvegardez aussi vos médias (filesystem ou bucket S3) si nécessaire.

## 2. Installer le package

```bash
uv add sites-conformes
```

(Pour les détails de configuration `INSTALLED_APPS`, `DIRS`, context
processors, voir {doc}`guide/installation`. Ce qui suit suppose que cette
étape est faite.)

## 3. Supprimer les apps locales que le package fournit maintenant

Si votre projet contient les répertoires `blog/`, `events/`, `forms/`,
`menus/`, `dashboard/`, `proconnect/`, `content_manager/` (ou `core/`) au
niveau projet — ils sont maintenant fournis par le package. Supprimez-les :

```bash
git rm -r blog/ events/ forms/ menus/ dashboard/ proconnect/ content_manager/
# (gardez core/ et db_storage/ si vous y aviez ajouté du code local)
```

Et ajustez `INSTALLED_APPS` pour utiliser les versions namespacées :

```diff
- "blog",
- "events",
- "content_manager",
+ "sites_conformes.blog",
+ "sites_conformes.events",
+ "sites_conformes.core",
```

## 4. Renommer les tables et l'historique des migrations

Le package préfixe toutes ses tables avec `sites_conformes_`. Vos tables
existantes (`blog_*`, `events_*`, `content_manager_*`, etc.) doivent être
renommées sinon Django croira que ce sont des apps différentes et tentera de
recréer les tables.

Le package fournit une commande qui fait le travail :

```bash
# Aperçu
python manage.py migrate_from_sites_faciles --dry-run

# Application
python manage.py migrate_from_sites_faciles
```

Elle gère :
- Le renommage des tables (`blog_*` → `sites_conformes_blog_*`,
  `content_manager_*` → `sites_conformes_core_*`, etc.).
- La mise à jour de la table `django_migrations` pour refléter les nouveaux
  labels d'app.
- La mise à jour de `django_content_type` pour que les permissions et
  références ContentType pointent vers les bonnes apps.

À noter : l'app `content_manager` est renommée en `core` dans le package,
donc ses tables vont de `content_manager_*` directement à
`sites_conformes_core_*`.

## 5. Appliquer les migrations restantes

```bash
python manage.py migrate
python manage.py collectstatic
```

À ce stade, Django doit pouvoir démarrer sans erreur. Les migrations du
package se présenteront comme déjà appliquées (puisque les tables existent
sous leur nouveau nom).

## 6. Vérifier

- Parcourez l'admin Wagtail — toutes vos pages doivent apparaître à leur
  place.
- Visitez les pages publiées principales du site.
- Inspectez `django_migrations` :
  ```sql
  SELECT app, COUNT(*) FROM django_migrations
   WHERE app LIKE 'sites_conformes_%' GROUP BY app ORDER BY app;
  ```
  Tous les labels doivent être préfixés.

## Dépannage

**`ProgrammingError: relation "blog_xxx" does not exist`**
Une référence ContentType pointe encore vers l'ancien label. Relancez
`migrate_from_sites_faciles` ou corrigez manuellement la ligne fautive dans
`django_content_type`.

**Templates introuvables (`TemplateDoesNotExist: sites_conformes_core/...`)**
Vérifiez que `TEMPLATES[0]["DIRS"]` contient bien le répertoire
`templates/` du package — voir {doc}`guide/installation`.

**Static manquants (`staticfiles.W004`)**
Même cause côté statiques : vérifiez `STATICFILES_DIRS`.

## Référence

La commande `migrate_from_sites_faciles` se trouve dans
`sites_conformes/management/commands/migrate_from_sites_faciles.py`. Ses
listes d'apps et de renommages sont alimentées automatiquement depuis le
`search-and-replace.yml` utilisé pour générer le package, donc elles
restent en phase avec le contenu de la distribution.
