from wagtail.api.v2.serializers import BaseSerializer
from wagtail.api.v2.views import BaseAPIViewSet

from .models import Psychologue


class PsychologueSerializer(BaseSerializer):
    class Meta:
        model = Psychologue
        fields = ["id", "nom", "ville", "email", "telephone", "latitude", "longitude"]


class PsychologuesAPIViewSet(BaseAPIViewSet):
    model = Psychologue
    base_serializer_class = PsychologueSerializer
    body_fields = BaseAPIViewSet.body_fields + [
        "nom",
        "ville",
        "email",
        "telephone",
        "latitude",
        "longitude",
    ]
    listing_default_fields = BaseAPIViewSet.listing_default_fields + [
        "nom",
        "ville",
    ]
