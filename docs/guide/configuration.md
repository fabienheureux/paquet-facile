# Configuration

Ce guide couvre uniquement les réglages spécifiques à `sites_conformes`. Pour la configuration générale Wagtail/Django, référez-vous à leurs documentations officielles.

## HOST_URL
URL de votre site (sans protocole) :
```python
HOST_URL = "monsite.gouv.fr"
```

## HOST_PROTO
Protocole utilisé (`http` ou `https`) :
```python
HOST_PROTO = "https"
```

## WAGTAILADMIN_PATH
Chemin d'accès à l'administration Wagtail :
```python
WAGTAILADMIN_PATH = "admin/"
```

## WAGTAIL_I18N_ENABLED
Active l'internationalisation de Wagtail :
```python
WAGTAIL_I18N_ENABLED = True
```

## PROCONNECT_ACTIVATED
Active l'authentification ProConnect :
```python
PROCONNECT_ACTIVATED = True
```

Pour plus d'informations sur tous les paramètres disponibles, consultez la [référence des settings](../reference/settings.md).
