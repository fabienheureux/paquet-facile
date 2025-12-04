# Changelog

## Version 2.3.0

### Changements
- ✨ Nouvelle répartition des blocs (#398)
- 🔗 Mise à jour de l'URL Sites Faciles en pied de page (#402)
- 📝 Correction d'une formulation « FranceConnect » → « ProConnect » (#404)
- 🎛️ Boutons d'ancrage gauche/droite/centré dans l'éditeur de texte riche (#403)

## Version 2.2.1

### Corrections
- 🛡️ Empêche l'écrasement des pages publiées lors des mises à jour de modèles (#397)
- 🖼️ Autorise l'écrasement des images dans les scripts d'import (#400)

## Version 2.2.0

### Changements
- 🧭 Nouvelles en-têtes (#373)
- 🖼️ Support des GIF animés (#390)
- 🔐 Possibilité de désactiver la connexion par mot de passe (#391)
- 🔎 Tous les types de pages peuvent apparaître dans la recherche (#392)

## Version 2.1.0

### Nouvelles fonctionnalités
- ✨ Documentation complète en français avec Sphinx

### Suppressions
- 🗑️ Suppression du système de registre `@register_common_block` (non fonctionnel)

### Documentation
- 📚 Documentation Sphinx avec thème Wagtail
- 📚 Guides, tutoriels et références techniques en français
- 📚 Publication automatique sur GitHub Pages


---

## Version 2.0.0

### Changements
- 🔧 Passage à `just` et `uv` pour le dev/deploy
- 🐝 Ajout d'un honeypot (#357)
- 🖼️ Image de prévisualisation (#350)
- 🔄 Ajustements divers (voir release notes upstream)

## Version 1.18.1
- 🐛 Indicateur d'étapes : correction d'un bug d'affichage (#343)

## Version 1.18.0
- 🐘 Bump PostgreSQL minimum (#323)
- 📦 Mises à jour dépendances (Wagtail 7.0) (#337)
- 🏷️ Déplacement des étiquettes dans l'onglet contenu (#325)
- 🖼️ Affichage du "Logo du site" (#328)

## Version 1.17.0
- 🧩 Alt vides pour les tuiles (#305)
- 🛠️ Correction encodage largeur du logo (#307)
- 🔗 Nouveau template tag `canonical_url` (#309)
- ♿ Corrections suite audit accessibilité (#310)

## Version 1.16.0
- 📊 Nouveau bloc tableau (#295)
- 🔗 Liens externes ouvrent dans un nouvel onglet (#301)
- 🤖 Ajout d'un `robots.txt` (#303)
- 📦 Mises à jour dépendances (#302)

## Version 1.15.1
- 📰 Bloc « Lettre d’information et réseaux sociaux » déplacé en aside (#297)
- 🧱 Grille d’éléments : correction d’affichage (#299)
- 📦 Mises à jour dépendances Python & JS (#300)

## Version 1.15.0
- 🗺️ Page « Plan du site » (#279)
- 🧩 Améliorations de composants (#276)
- 🛠️ Nouvelle recette make `upgrade` (#281)
- 🤖 Nouvelle CI `issues-notion-sync` (#282)

## Version 1.14.0
- ♿ Correction accessibilité du champ recherche (#274)
- 📦 Mises à jour dépendances (Wagtail 6.4.1) (#275)
- 🗺️ Génération automatique du sitemap.xml (#271)
- 🔐 Authentification via ProConnect (#273)

## Version 1.13.0
- 📦 Mise à jour Wagtail 6.4 (#270)
- 🛠️ Helper `get_default_site()` (#250)

## Version 1.12.0
- 🔗 Réordonnancement des liens de référence en pied de page (#260)

## Version 1.11.5
- 🛠️ Améliorations du Makefile (#257)

## Version 1.11.4
- 🐛 Import de fichiers S3 corrigé (#256)

## Version 1.11.3
- ⚙️ Variable d'environnement `USE_POETRY` (#254)

## Version 1.11.2
- 📦 Passage à Poetry 2.0 (#253)

## Version 1.11.1
- 🌐 Correction orthographe FR dans le gestionnaire d’étape (#251)

## Version 1.11.0
- 🧭 Carte contact verticale (#242)
- 🧭 Gestion des index de catalogue (#244)
- 🧩 Ajout de blocs manquants (#245)
- 🐛 Corrections blog (#240)

## Version 1.10.2 
- 🎨 Semi-rollback des pictos mode sombre (#235)

## Version 1.10.1 
- 🐛 Corrections pictogrammes en mode sombre (#231, #232)
- 📦 Mises à jour dépendances (Wagtail → 6.3, django-dsfr → 1.4.1) (#234)

## Version 1.10.0 
- ⚠️ Avertissement sur l'utilisation du DSFR (#221)
- 🐳 Corrections Docker (#212)
- 🛠️ Mise en place du système de modèles de pages (#218)
- 🔀 Permet de migrer de versions précédentes (#217)

## Version 1.9.0 
- 🧩 Nouveaux composants : Onglets et Partage (#206)
- 📄 Ajout de `publiccode.yml` (#208)
- 🌐 Mise en place de l'API (#209)
- 🔐 Gestion de l'accès aux pages privées (#216)
- 🧱 Blocs accordéons/étapier pour multi-colonnes (#215)

## Version 1.8.0 
- 📅 Système d'agenda/calendrier (#191)
- 🖼️ Masque le header des cartes horizontales si pas d'image (#199)
- 📢 Mention « Site fait avec Sites faciles » en pied de page (#196)
- 📦 Mises à jour dépendances + nouveau bandeau info (#193)

## Version 1.7.0 
- 🧩 Listes de boutons pour appels à action (#184)
- 📰 Filtrage des articles sur l’index + bloc "Derniers articles" (#186)
- 📦 Mises à jour dépendances Python (#190)

## Version 1.6.1 
- 🐛 Répare l'affichage des tuiles (#180)

## Version 1.6.0 
- ✉️ Envoi de courriels de récupération de mot de passe (#168)
- 🧰 Générateur de formulaire (#169)
- 🌞 Force le thème clair à la première visite si sélecteur désactivé (#174)
- 🐛 Corrections tuiles et ajustements (#176)

## Version 1.5.2 
- 🗂️ Nouveau bloc "Liste des sous-pages" (#148, #150)
- 🧩 Améliorations blocs Mise en avant / Mise en exergue (#147)
- 🖼️ Paramètre `parameters` pour les iframes (#152)

## Version 1.5.1 
- 🐛 Corrections d'affichage pour cartes/vidéos (#146)
