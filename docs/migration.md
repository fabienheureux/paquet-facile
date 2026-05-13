# Migrer un site existant vers `sites-conformes` (package)

Ce guide concerne les sites déjà construits avec **Sites Conformes** (ou son
ancêtre **Sites Faciles**) qui veulent passer à la version packagée distribuée
sur PyPI. Le but : remplacer une copie locale du code par une dépendance
versionnée, tout en gardant la base de données existante.

:::{warning}
Lisez **tout le guide avant de commencer**. Plusieurs étapes doivent être
exécutées dans l'ordre, et notamment **ne pas lancer `python manage.py
migrate` avant l'étape 4** (voir l'encadré dédié plus bas) sous peine de
casser l'historique des migrations.
:::

## 1. Sauvegarder

Avant de toucher quoi que ce soit, faites une copie de la base de données de
production (via votre outil habituel : `pg_dump`, snapshot du provider, etc.).
Sauvegardez aussi vos médias (filesystem ou bucket S3) si nécessaire.

## 2. Installer le package

```bash
uv add sites-conformes
```

## 3. Supprimer les apps locales que le package fournit maintenant

Si votre projet contient les répertoires `blog/`, `events/`, `forms/`,
`menus/`, `dashboard/`, `proconnect/`, `content_manager/` (ou `core/`) au
niveau projet, ils sont maintenant fournis par le package.

:::{warning}
**Avant de supprimer**, comparez chaque dossier avec son équivalent dans le
package pour récupérer vos personnalisations (nouveaux modèles, templates
ajoutés, migrations locales). Une commande utile :

```bash
diff -r blog/ .venv/lib/python*/site-packages/sites_conformes/blog/
```

Toute différence non triviale doit être reportée ailleurs (un nouveau dossier
applicatif, une sous-classe dans `core/`, etc.) avant la suppression.
:::

Une fois la sauvegarde des personnalisations effectuée :

```bash
git rm -r blog/ events/ forms/ menus/ dashboard/ proconnect/ content_manager/
```

Ajustez ensuite `INSTALLED_APPS` pour utiliser les versions namespacées :

```diff
- "blog",
- "events",
- "content_manager",
+ "sites_conformes.blog",
+ "sites_conformes.events",
+ "sites_conformes.core",
```

:::{danger}
**Ne lancez pas `python manage.py migrate` à ce stade.** Vos tables s'appellent
encore `blog_*`, `content_manager_*`, etc., mais Django pense désormais qu'elles
appartiennent aux apps `sites_conformes.blog`, `sites_conformes.core`, etc.
Lancer `migrate` créerait des tables vides en double et marquerait les
anciennes comme orphelines. Passez directement à l'étape 4.
:::

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
- Le renommage des tables (`blog_*` devient `sites_conformes_blog_*`,
  `content_manager_*` devient `sites_conformes_core_*`, etc.).
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

- Parcourez l'admin Wagtail : toutes vos pages doivent apparaître à leur
  place.
- Visitez les pages publiées principales du site.
- Inspectez `django_migrations` :
  ```sql
  SELECT app, COUNT(*) FROM django_migrations
   WHERE app LIKE 'sites_conformes_%' GROUP BY app ORDER BY app;
  ```
  Tous les labels doivent être préfixés.

