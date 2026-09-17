"""Real-browser end-to-end tests.

Covers what the Django test client cannot see: the Alpine-driven mobile nav,
JavaScript errors, and layout at phone width.

Skipped automatically when Playwright or its browser is unavailable, or when
SKIP_BROWSER_TESTS=1 is set, so the rest of the suite still runs in CI.
"""
import os
import unittest

# Playwright's sync API drives an event loop, which makes Django treat ORM
# calls on this thread as async-unsafe. The live server runs in its own thread,
# so the guard is a false positive here.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

PAGES = ["core:home", "core:about", "services:list",
         "case_studies:list", "careers:list", "contact:contact"]


@unittest.skipIf(os.environ.get("SKIP_BROWSER_TESTS") == "1", "browser tests disabled")
@unittest.skipIf(sync_playwright is None, "playwright not installed")
class BrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._playwright = sync_playwright().start()
        try:
            cls.browser = cls._playwright.chromium.launch()
        except Exception as exc:  # pragma: no cover - no browser binary
            cls._playwright.stop()
            super().tearDownClass()
            raise unittest.SkipTest(f"chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._playwright.stop()
        super().tearDownClass()

    def open(self, page, url_name, **kwargs):
        page.goto(f"{self.live_server_url}{reverse(url_name)}", **kwargs)

    def test_every_page_loads_without_javascript_errors(self):
        for name in PAGES:
            with self.subTest(page=name):
                page = self.browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                self.open(page, name)
                page.wait_for_load_state("domcontentloaded")
                self.assertEqual(errors, [], f"JS errors on {name}: {errors}")
                page.close()

    def test_no_horizontal_overflow_on_a_phone(self):
        """A page wider than the viewport is the classic mobile layout bug."""
        for name in PAGES:
            with self.subTest(page=name):
                page = self.browser.new_page(viewport={"width": 375, "height": 812})
                self.open(page, name)
                page.wait_for_load_state("networkidle")
                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                )
                self.assertLessEqual(overflow, 1, f"{name} scrolls sideways by {overflow}px")
                page.close()

    def test_mobile_menu_opens_and_closes(self):
        page = self.browser.new_page(viewport={"width": 375, "height": 812})
        self.open(page, "core:home")
        page.wait_for_load_state("networkidle")

        toggle = page.locator("button[aria-label*='menu' i], nav button").first
        panel = page.locator("nav [x-show='open']").first
        if toggle.count() == 0 or not page.evaluate("() => !!window.Alpine"):
            page.close()
            self.skipTest("Alpine.js did not load (CDN unreachable?)")

        self.assertFalse(panel.is_visible())
        toggle.click()
        panel.wait_for(state="visible", timeout=3000)
        self.assertTrue(panel.is_visible())
        toggle.click()
        panel.wait_for(state="hidden", timeout=3000)
        page.close()

    def test_contact_form_submits_end_to_end(self):
        page = self.browser.new_page()
        self.open(page, "contact:contact")
        page.fill("[name='full_name']", "Jane Al-Mansoori")
        page.fill("[name='work_email']", "jane@examplecorp.com")
        page.fill("[name='company']", "Example Corp")
        page.fill("[name='message']", "Browser-driven submission test.")
        page.select_option("[name='interest']", "threat_detection")
        page.click("form button[type='submit'], form input[type='submit']")
        page.wait_for_url("**/contact/thanks/**", timeout=5000)

        from apps.contact.models import ContactInquiry
        self.assertTrue(ContactInquiry.objects.filter(company="Example Corp").exists())
        page.close()

    def test_navigation_between_pages_works(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        self.open(page, "core:home")
        page.click(f"a[href='{reverse('services:list')}']")
        page.wait_for_url(f"**{reverse('services:list')}")
        self.assertIn("Services", page.title())
        page.close()
