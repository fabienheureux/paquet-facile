# Git blame ignore revs

Le fichier `.git-blame-ignore-revs` liste les commits à exclure de `git blame` — typiquement les PRs de reformatage massif (`black`, `ruff --fix`) qui n'ont pas de valeur sémantique pour l'historique des auteurs.

## Configuration locale (une fois par clone)

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

GitHub respecte ce fichier nativement dans son interface de blame.

## Ajouter un commit

Récupérer le SHA complet puis l'ajouter au fichier avec un commentaire :

```bash
git rev-parse <short-sha>
```

```
# Apply black formatting (2024-06-01)
abc1234def5678abc1234def5678abc1234def5678
```

À utiliser pour les commits **purement mécaniques** (formatage, renommage en masse) — pas pour les correctifs ou les nouvelles fonctionnalités.
