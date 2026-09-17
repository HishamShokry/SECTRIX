"""Every public page renders, with the navigation and metadata it needs."""
from django.test import TestCase
from django.urls import reverse

PUBLIC_PAGES = [
    ("core:home", "core/home.html"),
    ("core:about", "core/about.html"),
    ("services:list", "services/list.html"),
    ("case_studies:list", "case_studies/list.html"),
    ("careers:list", "careers/list.html"),
    ("contact:contact", "contact/contact.html"),
    ("contact:thanks", "contact/thanks.html"),
]


class PublicPageTests(TestCase):
    def test_every_page_returns_200(self):
        for name, _ in PUBLIC_PAGES:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_every_page_uses_its_template(self):
        for name, template in PUBLIC_PAGES:
            with self.subTest(page=name):
                self.assertTemplateUsed(self.client.get(reverse(name)), template)

    def test_every_page_has_a_title_and_description(self):
        for name, _ in PUBLIC_PAGES:
            with self.subTest(page=name):
                body = self.client.get(reverse(name)).content.decode()
                self.assertRegex(body, r"<title>\s*\S.*?</title>")
                self.assertRegex(body, r'<meta name="description" content="\s*\S')

    def test_navigation_links_resolve_on_every_page(self):
        """A broken nav link is invisible until someone clicks it."""
        for name, _ in PUBLIC_PAGES:
            body = self.client.get(reverse(name)).content.decode()
            for target, _ in PUBLIC_PAGES[:-1]:  # 'thanks' is not in the nav
                with self.subTest(page=name, link=target):
                    self.assertIn(f'href="{reverse(target)}"', body)

    def test_404_page_renders(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")

    def test_no_stale_brand_spelling(self):
        """The rebrand left no 'Sectrix' anywhere a visitor can see."""
        for name, _ in PUBLIC_PAGES:
            with self.subTest(page=name):
                body = self.client.get(reverse(name)).content.decode()
                self.assertNotIn("Sectrix", body)
                self.assertNotIn("sectrix.com", body)

    def test_pages_are_not_trivially_empty(self):
        """Guards against a template rendering its shell with no content."""
        for name, _ in PUBLIC_PAGES:
            with self.subTest(page=name):
                body = self.client.get(reverse(name)).content.decode()
                self.assertGreater(len(body), 5000, f"{name} rendered suspiciously small")


class StylesheetTests(TestCase):
    """Tailwind is compiled at build time, not fetched from the Play CDN."""

    def test_compiled_stylesheet_is_linked(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertRegex(body, r'<link rel="stylesheet" href="[^"]*css/tailwind[^"]*\.css"')

    def test_play_cdn_is_not_referenced(self):
        """The Play CDN ships a compiler to every visitor and is dev-only."""
        for name, _ in PUBLIC_PAGES:
            with self.subTest(page=name):
                body = self.client.get(reverse(name)).content.decode()
                self.assertNotIn("cdn.tailwindcss.com", body)
                self.assertNotIn("tailwind.config", body)

    def test_no_third_party_runtime_assets(self):
        """Scripts, styles and fonts are all self-hosted.

        The OpenStreetMap iframe on the contact page is a deliberate exception:
        a map cannot be vendored.
        """
        forbidden = ("cdn.jsdelivr.net", "fonts.googleapis.com",
                     "fonts.gstatic.com", "cdn.tailwindcss.com", "unpkg.com")
        for name, _ in PUBLIC_PAGES:
            body = self.client.get(reverse(name)).content.decode()
            for origin in forbidden:
                with self.subTest(page=name, origin=origin):
                    self.assertNotIn(origin, body)

    def test_vendored_assets_are_findable(self):
        from django.contrib.staticfiles import finders
        for asset in ("css/tailwind.css", "js/alpine.min.js",
                      "fonts/inter-latin-wght-normal.woff2",
                      "fonts/jetbrains-mono-latin-wght-normal.woff2"):
            with self.subTest(asset=asset):
                self.assertIsNotNone(
                    finders.find(asset), f"{asset} missing — run: npm run build",
                )

    def test_alpine_is_loaded_from_our_own_static_files(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertRegex(body, r'<script defer src="[^"]*js/alpine[^"]*\.js"')

    def test_stylesheet_is_actually_served(self):
        from django.contrib.staticfiles import finders
        self.assertIsNotNone(
            finders.find("css/tailwind.css"),
            "static/css/tailwind.css missing — run: npm run build:css",
        )
