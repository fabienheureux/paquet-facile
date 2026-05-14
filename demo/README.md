# Demo sites-conformes

Projet Django/Wagtail minimal qui consomme le package [`sites-conformes`](https://pypi.org/project/sites-conformes/)
pour montrer comment l'intégrer dans un site existant. Pas destiné à être déployé.

## Ce qu'il y a dedans

| Dossier      | Rôle                                                                                    |
| ------------ | --------------------------------------------------------------------------------------- |
| `demo/`      | Configuration Django (settings, urls, wsgi) du projet de démo.                          |
| `home/`      | App Wagtail minimale avec une `HomePage`.                                               |
| `search/`    | Vue de recherche Wagtail standard.                                                      |
| `annuaire/`  | App d'exemple : annuaire de psychologues affiché sur une carte Carte Facile + API REST. |

L'app `annuaire/` est l'implémentation runnable du guide
[**Cas pratique — annuaire de psychologues**](../docs/guide/cas-pratique-annuaire.md)
de la documentation.

## Démarrage

```bash
just setup            # uv sync + migrate
just createsuperuser  # crée le compte admin Wagtail
just runserver        # http://localhost:8000
```

Puis dans l'admin Wagtail (`/admin/`) :

1. **Snippets → Psychologues** : ajoutez quelques fiches avec leurs coordonnées
   lat/lng (exemple : Paris `48.856614 / 2.352222`).
2. **Pages → Add child page → Annuaire page** : créez une page contenant le
   bloc *Liste des psychologues (carte)*.
3. Publiez, puis visitez l'URL de la page pour voir la carte interactive.

L'API REST est exposée en `/api/v2/psychologues/` :

```bash
curl http://localhost:8000/api/v2/psychologues/
curl "http://localhost:8000/api/v2/psychologues/?ville=Paris"
```
