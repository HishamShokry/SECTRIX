"""Sectrex root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from apps.core.sitemaps import StaticViewSitemap

sitemaps = {"static": StaticViewSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include("apps.core.urls")),
    path("services/", include("apps.services.urls")),
    path("case-studies/", include("apps.case_studies.urls")),
    path("careers/", include("apps.careers.urls")),
    path("contact/", include("apps.contact.urls")),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "apps.core.views.handler404"
handler500 = "apps.core.views.handler500"

# Admin branding lives in apps/core/admin.py, where it can follow the editable
# site name. Assigning it here as well would silently win, because urls.py is
# imported after admin autodiscovery.
