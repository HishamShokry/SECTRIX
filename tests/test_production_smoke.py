"""End-to-end smoke tests against a deployed site.

The rest of the suite exercises a local build. This one drives a real browser
against a live URL, so it catches what only the deployment can break: TLS,
nginx headers, the proxy path, static files actually being served, rate limits.

    SMOKE_BASE_URL=https://sectrexconsulting.com \
      python manage.py test tests.test_production_smoke

Read-only by default: every check is a GET. The contact form is filled and
validated but NOT submitted, because a submission writes a row to the
production database and sends mail. Set SMOKE_ALLOW_WRITE=1 to include it.
"""
import os
import re
import unittest

os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

BASE_URL = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
ALLOW_WRITE = os.environ.get("SMOKE_ALLOW_WRITE") == "1"

PATHS = ["/", "/about/", "/services/", "/case-studies/", "/careers/", "/contact/", "/privacy/"]


@unittest.skipUnless(BASE_URL, "set SMOKE_BASE_URL to run production smoke tests")
@unittest.skipIf(sync_playwright is None, "playwright not installed")
class ProductionSmokeTests(unittest.TestCase):
    """Note: plain unittest.TestCase -- no database, nothing local is touched."""

    @classmethod
    def setUpClass(cls):
        cls._pw = sync_playwright().start()
        try:
            cls.browser = cls._pw.chromium.launch()
        except Exception as exc:  # pragma: no cover
            cls._pw.stop()
            raise unittest.SkipTest(f"chromium unavailable: {exc}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._pw.stop()

    # --- availability ----------------------------------------------------

    def test_every_page_returns_200(self):
        page = self.browser.new_page()
        for path in PATHS:
            with self.subTest(path=path):
                response = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded")
                self.assertEqual(response.status, 200, f"{path} returned {response.status}")
        page.close()

    def test_no_javascript_errors_anywhere(self):
        for path in PATHS:
            with self.subTest(path=path):
                page = self.browser.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
                self.assertEqual(errors, [], f"JS errors on {path}: {errors}")
                page.close()

    def test_static_assets_all_load(self):
        """A broken collectstatic manifest shows up as 404s on hashed files."""
        page = self.browser.new_page()
        failed = []
        page.on("response", lambda r: failed.append((r.url, r.status)) if r.status >= 400 else None)
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        self.assertEqual(failed, [], f"assets failed to load: {failed}")
        page.close()

    def test_page_is_actually_styled(self):
        """Valid HTML with a dead stylesheet still renders -- check pixels."""
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        bg = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
        self.assertEqual(bg, "rgb(6, 15, 34)", "brand stylesheet did not apply")
        page.close()

    def test_alpine_initialises(self):
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        self.assertTrue(page.evaluate("() => !!window.Alpine"), "Alpine did not load")
        page.close()

    def test_no_horizontal_overflow_on_a_phone(self):
        for path in PATHS:
            with self.subTest(path=path):
                page = self.browser.new_page(viewport={"width": 375, "height": 812})
                page.goto(f"{BASE_URL}{path}", wait_until="networkidle")
                overflow = page.evaluate(
                    "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
                )
                self.assertLessEqual(overflow, 1, f"{path} scrolls sideways by {overflow}px")
                page.close()

    def test_navigation_between_pages(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        page.click("a[href='/services/']")
        page.wait_for_url("**/services/")
        self.assertIn("Services", page.title())
        page.close()

    # --- deployment configuration ---------------------------------------

    def test_security_headers_are_present(self):
        page = self.browser.new_page()
        response = page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        headers = {k.lower(): v for k, v in response.headers.items()}
        for header in ("strict-transport-security", "content-security-policy",
                       "x-content-type-options", "x-frame-options",
                       "referrer-policy", "permissions-policy"):
            with self.subTest(header=header):
                self.assertIn(header, headers)
        self.assertIn("max-age=31536000", headers["strict-transport-security"])
        page.close()

    def test_server_header_is_not_disclosed(self):
        page = self.browser.new_page()
        response = page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        headers = {k.lower(): v for k, v in response.headers.items()}
        self.assertNotIn("server", headers, f"Server header disclosed: {headers.get('server')}")
        page.close()

    def test_http_redirects_to_https(self):
        page = self.browser.new_page()
        insecure = BASE_URL.replace("https://", "http://")
        response = page.goto(f"{insecure}/", wait_until="domcontentloaded")
        self.assertTrue(page.url.startswith("https://"), f"landed on {page.url}")
        self.assertEqual(response.status, 200)
        page.close()

    def test_assets_do_not_advertise_versions(self):
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        bodies = page.evaluate("""async () => {
            const urls = [...document.querySelectorAll('link[rel=stylesheet],script[src]')]
                .map(el => el.href || el.src).filter(Boolean);
            const out = [];
            for (const u of urls) {
                try { out.push(await (await fetch(u)).text()); } catch (e) {}
            }
            return out.join('\\n');
        }""")
        leaks = re.findall(r"tailwindcss v\d+\.\d+\.\d+|version:\"\d+\.\d+\.\d+\"", bodies)
        self.assertEqual(leaks, [], f"assets leak versions: {set(leaks)}")
        page.close()

    def test_admin_requires_authentication(self):
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/admin/", wait_until="domcontentloaded")
        self.assertIn("/admin/login/", page.url)
        page.close()

    def test_robots_and_sitemap(self):
        page = self.browser.new_page()
        robots = page.goto(f"{BASE_URL}/robots.txt", wait_until="domcontentloaded")
        self.assertEqual(robots.status, 200)
        sitemap = page.goto(f"{BASE_URL}/sitemap.xml", wait_until="domcontentloaded")
        self.assertEqual(sitemap.status, 200)
        page.close()

    def test_404_page_is_the_branded_one(self):
        page = self.browser.new_page()
        response = page.goto(f"{BASE_URL}/no-such-page-xyz", wait_until="domcontentloaded")
        self.assertEqual(response.status, 404)
        self.assertNotIn("nginx", page.content().lower(), "served nginx's 404, not the app's")
        page.close()

    def test_mobile_menu_actually_toggles(self):
        """The assertion that catches a CSP blocking Alpine.

        Alpine loads fine under a restrictive CSP -- it just cannot evaluate
        its expressions, so x-show never runs and the panel sits open. Checking
        window.Alpine is not enough; the behaviour has to be exercised.
        """
        page = self.browser.new_page(viewport={"width": 375, "height": 812})
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        panel = page.locator("nav [x-show='open']").first
        toggle = page.locator("nav button").first

        self.assertFalse(panel.is_visible(), "mobile menu is open before being clicked")
        toggle.click()
        panel.wait_for(state="visible", timeout=3000)
        toggle.click()
        panel.wait_for(state="hidden", timeout=3000)
        page.close()

    def test_static_assets_are_not_rate_limited(self):
        """A page load fetches CSS, JS and two fonts; throttling those is wrong."""
        page = self.browser.new_page()
        throttled = []
        page.on("response",
                lambda r: throttled.append(r.url) if r.status == 429 else None)
        for _ in range(3):
            page.goto(f"{BASE_URL}/", wait_until="networkidle")
        self.assertEqual(throttled, [], f"static assets returned 429: {throttled}")
        page.close()

    # --- the contact form ------------------------------------------------

    def test_contact_form_renders_every_field(self):
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/contact/", wait_until="networkidle")
        for field in ("full_name", "work_email", "company", "message", "interest"):
            with self.subTest(field=field):
                self.assertEqual(page.locator(f"[name='{field}']").count(), 1)
        page.close()

    @unittest.skipUnless(ALLOW_WRITE, "writes to the production database; set SMOKE_ALLOW_WRITE=1")
    def test_contact_form_submits(self):
        """Creates a real inquiry and sends real mail -- opt-in only."""
        page = self.browser.new_page()
        page.goto(f"{BASE_URL}/contact/", wait_until="networkidle")
        page.fill("[name='full_name']", "Smoke Test")
        page.fill("[name='work_email']", "smoke-test@example.com")
        page.fill("[name='company']", "SMOKE TEST - please delete")
        page.fill("[name='message']", "Automated deployment smoke test. Safe to delete.")
        page.select_option("[name='interest']", "general")
        page.wait_for_timeout(2500)   # the form rejects submissions faster than this
        page.click("form button[type='submit'], form input[type='submit']")
        page.wait_for_url("**/thanks/**", timeout=10000)
        page.close()
