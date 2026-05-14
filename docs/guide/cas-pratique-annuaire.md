# Cas pratique — annuaire de psychologues

Ce guide répond à une question que les développeurs nous posent souvent : comment
ajouter un nouveau type de contenu métier (par exemple un annuaire de
psychologues) à un site `sites-conformes` ?

Le parcours :

1. Installer `sites-conformes` dans un projet Django existant.
2. Modéliser l’entité `Psychologue` comme un **snippet** Wagtail.
3. Créer un **bloc StreamField** réutilisable qui affiche la liste sur n’importe
   quelle page.
4. Exposer le tout via l’API REST de Wagtail (`/api/v2/`).

L’exemple est volontairement minimal — il ne couvre pas la géolocalisation
(PostGIS) ni la recherche full-text, mais il pose la mécanique commune à ce
type de fonctionnalité.

## 0. Prérequis

`sites-conformes` doit être installé et configuré dans votre projet Django.
Voir [Installation](installation.md) si ce n’est pas fait.

L’exemple suppose une app Django locale nommée `annuaire` :

```bash
python manage.py startapp annuaire
```

Ajoutez `"annuaire"` à `INSTALLED_APPS`, juste après les apps `sites_conformes.*`.

## 1. Le snippet `Psychologue`

Un **snippet** Wagtail est un modèle Django qu’on peut éditer depuis le back
office sans qu’il s’agisse d’une page. Parfait pour des données réutilisables
sur plusieurs pages : un annuaire de psys, une liste de lieux, des contacts…

Documentation Wagtail de référence :
<https://docs.wagtail.org/en/stable/topics/snippets/index.html>.

```python
# annuaire/models.py
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class Psychologue(models.Model):
    nom = models.CharField(max_length=120)
    ville = models.CharField(max_length=80)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    # Pour la géolocalisation, voir django.contrib.gis.db.models.PointField
    # et l’admin Wagtail GIS si vous avez PostGIS.

    panels = [
        FieldPanel("nom"),
        FieldPanel("ville"),
        FieldPanel("email"),
        FieldPanel("telephone"),
    ]

    class Meta:
        ordering = ("nom",)
        verbose_name = "Psychologue"
        verbose_name_plural = "Psychologues"

    def __str__(self):
        return f"{self.nom} ({self.ville})"
```

Migrations habituelles :

```bash
python manage.py makemigrations annuaire
python manage.py migrate
```

Le snippet apparaît immédiatement dans l’admin Wagtail (menu **Snippets →
Psychologues**). Vous pouvez créer quelques fiches pour la suite.

## 2. Un bloc StreamField qui liste les psys

Pour intégrer la liste de psychologues dans une page, on définit un bloc
Wagtail. On veut que l’éditeur puisse simplement **déposer** le bloc dans la
page — pas saisir les psys manuellement, ils viennent de la base.

C’est exactement le rôle de `StaticBlock` : un bloc sans champs éditables qui
rend un template à partir du contexte fourni par `get_context()`.

```python
# annuaire/blocks.py
from wagtail import blocks

from .models import Psychologue


class ListePsychologuesBlock(blocks.StaticBlock):
    """Liste tous les psychologues, paginée par groupes de 20."""

    class Meta:
        icon = "group"
        label = "Liste des psychologues"
        template = "annuaire/blocks/liste_psychologues.html"
        admin_text = "Affiche la liste complète des psychologues."

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        context["psychologues"] = Psychologue.objects.all()
        return context
```

Template DSFR minimal :

```html
{# annuaire/templates/annuaire/blocks/liste_psychologues.html #}
<section class="fr-container fr-py-6w">
  <h2 class="fr-h3">Annuaire des psychologues</h2>
  <ul class="fr-list">
    {% for psy in psychologues %}
      <li>
        <strong>{{ psy.nom }}</strong> — {{ psy.ville }}
        {% if psy.email %}<a href="mailto:{{ psy.email }}">{{ psy.email }}</a>{% endif %}
      </li>
    {% empty %}
      <li>Aucun psychologue dans l’annuaire pour le moment.</li>
    {% endfor %}
  </ul>
</section>
```

## 3. Brancher le bloc sur les pages `sites-conformes`

`sites-conformes` expose `CommonStreamBlock` — le groupe de blocs DSFR que les
pages `ContentPage`, `BlogEntryPage`, etc. utilisent. Pour ajouter votre bloc
**partout**, on en hérite :

```python
# annuaire/blocks.py (suite)
from sites_conformes.core.blocks import CommonStreamBlock


class CustomBlockMixin(CommonStreamBlock):
    """Tous les blocs DSFR + les blocs métier de l’annuaire."""

    liste_psychologues = ListePsychologuesBlock()
```

Pour appliquer le mixin aux pages, soit vous étendez les pages
`sites-conformes`, soit vous définissez vos propres pages :

```python
# annuaire/models.py (suite)
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import CustomBlockMixin


class AnnuairePage(Page):
    body = StreamField(CustomBlockMixin(), use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]
```

Migration, puis dans l’admin vous pourrez ajouter une `AnnuairePage` et
glisser-déposer le bloc *Liste des psychologues* parmi les blocs DSFR.

:::{note}
Pour rester aligné avec `sites-conformes`, vous pouvez héberger votre bloc dans
un `STREAMFIELD_COMMON_BLOCKS` étendu plutôt qu’une sous-classe. Voir
`sites_conformes.core.blocks.STREAMFIELD_COMMON_BLOCKS` comme point de départ
si vous préférez la composition à l’héritage.
:::

## 4. Exposer les psychologues via l’API Wagtail

Wagtail fournit nativement une API REST en `/api/v2/`. Voir la documentation
officielle : <https://docs.wagtail.org/en/stable/advanced_topics/api/v2/configuration.html>.

### 4.1 Activer l’endpoint snippets

Wagtail expose les **pages** et les **images/documents** par défaut, mais
**pas les snippets**. Pour les rendre accessibles, écrivez un endpoint :

```python
# annuaire/api.py
from rest_framework import serializers
from wagtail.api.v2.views import BaseAPIViewSet

from .models import Psychologue


class PsychologueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Psychologue
        fields = ["id", "nom", "ville", "email", "telephone"]


class PsychologuesAPIViewSet(BaseAPIViewSet):
    model = Psychologue
    base_serializer_class = PsychologueSerializer
    body_fields = BaseAPIViewSet.body_fields + [
        "nom",
        "ville",
        "email",
        "telephone",
    ]
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "nom",
        "ville",
    ]
```

Enregistrez-le sur le router :

```python
# config/api.py  (ou config/urls.py)
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet

from annuaire.api import PsychologuesAPIViewSet

api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", PagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)
api_router.register_endpoint("psychologues", PsychologuesAPIViewSet)
```

Et branchez le router dans `config/urls.py` :

```python
from django.urls import path
from config.api import api_router

urlpatterns = [
    path("api/v2/", api_router.urls),
    # …
]
```

### 4.2 Exemples d’appels

```bash
# Tous les psychologues, format JSON
curl https://votre-site.fr/api/v2/psychologues/

# Un seul, par id
curl https://votre-site.fr/api/v2/psychologues/42/

# Filtrer par ville (filtres Wagtail standards)
curl "https://votre-site.fr/api/v2/psychologues/?ville=Lyon"

# Pagination — limit/offset
curl "https://votre-site.fr/api/v2/psychologues/?limit=20&offset=40"
```

Les pages qui contiennent le bloc *Liste des psychologues* sont également
disponibles via `/api/v2/pages/`. Le rendu du `StreamField` `body` y apparaît
en JSON.

## Pour aller plus loin

- **Carte interactive** : ajoutez un `PointField` à `Psychologue` (PostGIS
  requis) puis un template qui injecte les coordonnées dans une carte Leaflet
  ou IGN.
- **Recherche** : Wagtail expose un système de recherche full-text intégrable
  au snippet. Voir <https://docs.wagtail.org/en/stable/topics/search/index.html>.
- **Pagination côté template** : utilisez `django.core.paginator.Paginator`
  dans `get_context()` du `StaticBlock`, et lisez `request.GET["page"]` via
  `parent_context["request"]`.
