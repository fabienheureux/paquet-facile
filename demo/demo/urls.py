from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic.base import RedirectView
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from demo.api import api_router

urlpatterns = [
    path("sitemap.xml", sitemap, name="xml_sitemap"),
    path(settings.WAGTAILADMIN_PATH, include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("api/v2/", api_router.urls),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/dsfr/dist/favicon/favicon.ico", permanent=True),
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path("", include("sites_conformes.core.urls")),
    prefix_default_language=False,
)
