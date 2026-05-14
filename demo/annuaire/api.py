from rest_framework import serializers
from wagtail.api.v2.views import BaseAPIViewSet

from .models import Psychologue


class PsychologueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Psychologue
        fields = ["id", "nom", "ville", "email", "telephone", "latitude", "longitude"]


class PsychologuesAPIViewSet(BaseAPIViewSet):
    model = Psychologue
    base_serializer_class = PsychologueSerializer
    # Champs exposés dans la réponse détail.
    body_fields = BaseAPIViewSet.body_fields + [
        "nom",
        "ville",
        "email",
        "telephone",
        "latitude",
        "longitude",
    ]
    # Champs exposés dans la réponse liste.
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "nom",
        "ville",
    ]
