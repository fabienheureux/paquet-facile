# Migration d'un site Wagtail existant

Ce guide réduit la migration à l'essentiel : sauvegarder, installer, migrer, mettre à jour les tables.

## 1. Sauvegarder
- Exportez la base : `python manage.py dumpdata > backup.json` (ou votre méthode habituelle).
- Sauvegardez les fichiers médias si nécessaire.

## 2. Installer sites-conformes
- Ajoutez la dépendance : `pip install sites-conformes`.
- Suivez la {doc}`page d'installation <guide/installation>` pour compléter `INSTALLED_APPS` et les context processors (pas de configuration Django/Wagtail générique ici : voir leurs docs officielles).

## 3. Appliquer les migrations
```bash
python manage.py migrate
python manage.py collectstatic
```

## 4. Migrer depuis Sites Faciles
Si vous migrez depuis l'ancien projet Sites Faciles, lancez la commande fournie pour renommer les tables et mettre à jour l'historique des migrations :

```bash
python manage.py migrate_from_sites_faciles --dry-run
python manage.py migrate_from_sites_faciles
```

La commande se trouve dans `sites_conformes/management/commands/migrate_from_sites_faciles.py` et gère :
- Le renommage des tables de base de données en les préfixant avec `sites_conformes_`
- La mise à jour de la table `django_migrations` pour refléter les nouveaux noms d'applications
- Le basculement des apps `blog`, `events`, `forms`, `content_manager`, `config` vers leurs équivalents `sites_conformes_*`

## 5. Vérifier
- Parcourez vos pages principales et l'admin Wagtail pour valider le rendu DSFR.
- Inspirez-vous du projet `demo/` pour les gabarits (header, footer, menus). Toute personnalisation Wagtail/Django non spécifique à `sites_conformes` reste documentée sur <https://docs.wagtail.org/> et <https://docs.djangoproject.com/>.
