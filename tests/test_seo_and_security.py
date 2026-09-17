"""Indexing controls, sitemap, and the headers a production deploy depends on."""
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from tests.base import CacheIsolatedTestCase


class RobotsAndIndexingTests(TestCase):
    """Demo copy must stay out of search results until real content ships."""

    @override_settings(ALLOW_INDEXING=False)
    def test_robots_disallows_everything_while_indexing_is_off(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /", body)
        self.assertNotIn("Allow: /", body)

    @override_settings(ALLOW_INDEXING=False)
    def test_pages_carry_noindex_while_indexing_is_off(self):
        for page in ("core:home", "core:about", "services:list", "contact:contact"):
            with self.subTest(page=page):
                body = self.client.get(reverse(page)).content.decode()
                self.assertIn('content="noindex, nofollow"', body)

    @override_settings(ALLOW_INDEXING=True)
    def test_robots_allows_crawling_once_enabled(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("Allow: /", body)
        self.assertIn("Disallow: /admin/", body)
        self.assertIn("sitemap.xml", body)

    @override_settings(ALLOW_INDEXING=True)
    def test_noindex_tag_is_dropped_once_enabled(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertNotIn('content="noindex, nofollow"', body)

    def test_robots_is_served_as_plain_text(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])


class SitemapTests(TestCase):
    def test_sitemap_lists_the_public_pages(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertEqual(self.client.get("/sitemap.xml").status_code, 200)
        for page in ("core:home", "core:about", "services:list", "careers:list"):
            with self.subTest(page=page):
                self.assertIn(reverse(page), body)


class AdminAccessTests(CacheIsolatedTestCase):
    def test_admin_requires_login(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_admin_index_lists_every_editable_section(self):
        User.objects.create_superuser("admin", "admin@example.com", "x" * 24)
        self.client.login(username="admin", password="x" * 24)
        body = self.client.get("/admin/").content.decode()
        for section in ("Home · Trusted By", "Home · Measured Outcomes",
                        "Home · Why Sectrex", "About · Values", "About · Expertise",
                        "About · Leadership", "About · Trajectory",
                        "Careers · Culture", "Site Settings"):
            with self.subTest(section=section):
                self.assertIn(section, body)

    def test_non_staff_cannot_reach_admin(self):
        User.objects.create_user("bob", "bob@example.com", "x" * 24)
        self.client.login(username="bob", password="x" * 24)
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)


class SecurityHeaderTests(TestCase):
    """The production hardening block in settings.py.

    That block is guarded by ``if not DEBUG`` and evaluated at import time, so
    the test runner forcing DEBUG=False later is too late — the suite has to be
    started with DJANGO_DEBUG=False or these headers come from Django's
    defaults instead of this project's configuration.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not getattr(settings, "SECURE_HSTS_SECONDS", 0):
            raise unittest.SkipTest(
                "Run with DJANGO_DEBUG=False to exercise the production security block"
            )

    def test_content_type_nosniff_is_set(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.get("X-Content-Type-Options"), "nosniff")

    def test_clickjacking_protection_is_set(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.get("X-Frame-Options"), "DENY")

    def test_referrer_policy_is_set(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_hsts_is_sent_over_https(self):
        """The domain carries a preload policy, so HSTS must keep working."""
        header = self.client.get(reverse("core:home"), secure=True).get(
            "Strict-Transport-Security", ""
        )
        self.assertIn("max-age=", header)
        self.assertIn("includeSubDomains", header)
        self.assertIn("preload", header)

    def test_session_and_csrf_cookies_are_https_only(self):
        self.assertTrue(settings.SESSION_COOKIE_SECURE)
        self.assertTrue(settings.CSRF_COOKIE_SECURE)
