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
