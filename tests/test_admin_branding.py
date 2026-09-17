"""The admin is branded as the client's console, not stock Django."""
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection
from django.test import override_settings
from django.urls import reverse

from apps.core.models import SiteSettings
from tests.base import CacheIsolatedTestCase

# Assets are asserted by source path, so these tests do not depend on a
# collectstatic run having produced the hashed manifest.
STATIC_OVERRIDE = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


@override_settings(STORAGES=STATIC_OVERRIDE)
class AdminBrandingTests(CacheIsolatedTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_superuser("brand", "brand@example.com", "x" * 24)
        self.client.force_login(self.user)

    def test_header_uses_the_editable_site_name(self):
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn(SiteSettings.load().name, body)

    def test_header_follows_a_site_name_change(self):
        """Renaming the company in Site Settings renames the console too."""
        site = SiteSettings.load()
        site.name = "Renamed Consultancy"
        site.save()
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("Renamed Consultancy", body)

    def test_brand_stylesheet_and_favicon_are_linked(self):
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("css/admin-brand.css", body)
        self.assertIn("favicon.svg", body)

    def test_logo_mark_is_in_the_header(self):
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("sectrex-mark", body)

    def test_index_title_is_set(self):
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("Operations Console", body)

    def test_default_django_branding_is_gone(self):
        body = self.client.get(reverse("admin:index")).content.decode()
        self.assertNotIn("Django administration", body)
        self.assertNotIn("Django site admin", body)

    def test_login_page_is_branded(self):
        self.client.logout()
        body = self.client.get(reverse("admin:login")).content.decode()
        self.assertIn("sectrex-mark", body)
        self.assertIn("css/admin-brand.css", body)
        self.assertNotIn("Django administration", body)

    def test_branding_survives_a_missing_settings_row(self):
        """A fresh database must not lock the admin out.

        Deleted at the SQL layer: the ORM now refuses to remove the singleton,
        but a brand-new database genuinely has no row yet.
        """
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {SiteSettings._meta.db_table}")
        cache.clear()
        self.assertEqual(SiteSettings.objects.count(), 0)
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_brand_stylesheet_is_findable(self):
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(finders.find("css/admin-brand.css"))
