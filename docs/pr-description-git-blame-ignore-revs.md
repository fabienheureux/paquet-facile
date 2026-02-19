# PR — Mise en place de `.git-blame-ignore-revs`

## 🎯 Objectif

Éviter que les commits de reformatage massif (formatage automatique, refactoring mécanique) ne polluent `git blame` et masquent les vrais auteurs des modifications fonctionnelles.

## 🔍 Implémentation

- Ajout du fichier `.git-blame-ignore-revs` à la racine du projet
- Création de `docs/git-blame-ignore-revs.md` : documentation sur l'usage

## ⚠️ Informations supplémentaires

Chaque développeur doit exécuter une fois après le clone :

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```
