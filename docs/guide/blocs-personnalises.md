# Blocs StreamField

wagtail-dsfr fournit une collection de blocs StreamField adaptés au DSFR pour composer vos pages sans réinventer les composants.

## Ajouter les blocs à vos pages

wagtail-dsfr utilise un système de `DynamicStreamField` qui permet d'ajouter automatiquement tous les blocs DSFR sans avoir à les importer manuellement. Les blocs disponibles sont chargés dynamiquement via un système de registre.

```python
from wagtail_dsfr.content_manager.abstract import SitesFacilesBasePage

class ContentPage(SitesFacilesBasePage):
    # Les champs hero et body sont déjà définis dans SitesFacilesBasePage
    # avec tous les blocs DSFR disponibles
    pass
```

La classe `SitesFacilesBasePage` fournit :
- `hero` : variantes d'en-têtes (bandeau, image + texte, fond héro)
- `body` : alertes, accordéons, cartes, tableaux, boutons, listes, etc.

## Ajouter vos propres blocs

Pour ajouter vos blocs personnalisés aux blocs DSFR existants, utilisez le décorateur `@register_common_block` :

```python
# Dans votre fichier blocks.py
from wagtail import blocks
from wagtail_dsfr.content_manager.registry import register_common_block

@register_common_block
class CustomBlock(blocks.StructBlock):
    title = blocks.CharBlock(label="Titre")
    content = blocks.RichTextBlock(label="Contenu")
    
    class Meta:
        label = "Mon bloc personnalisé"
        icon = "edit"
```

Vos blocs personnalisés seront automatiquement ajoutés aux pages qui utilisent `DynamicStreamField` ou héritent de `SitesFacilesBasePage`.


## Et les migrations dans tout ça ? 

L'objectif du `DynamicStreamField` est de s'appuyer sur un callable plutôt que sur une liste statique de blocs.  
De ce fait, aucune migration n'est générée via l'utilisation de cette technique.
