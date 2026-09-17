"""Regression tests for the security review fixes.

Each test names the finding it guards so a future change that reintroduces the
defect fails with an explanation rather than a bare assertion error.
"""
import importlib

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.validators import validate_string_list


class FailClosedConfigTests(TestCase):
    """H2: an unset DJANGO_DEBUG must not hand a host the debugger."""

    def test_debug_defaults_to_false(self):
        import os
        os.environ.pop("DJANGO_DEBUG", None)
        module = importlib.import_module("sectrix.settings")
        source = importlib.util.find_spec("sectrix.settings").origin
        with open(source) as fh:
            text = fh.read()
        self.assertIn('DEBUG = env_bool("DJANGO_DEBUG", False)', text,
                      "DEBUG must default to False so a missing env var fails closed")

    def test_proxy_header_is_not_trusted_unconditionally(self):
        """H1: trusting X-Forwarded-Proto is only safe behind a known proxy."""
        source = importlib.util.find_spec("sectrix.settings").origin
        with open(source) as fh:
            text = fh.read()
        self.assertIn("if BEHIND_PROXY:", text)
        self.assertNotIn(
            'SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")\n    SECURE_HSTS',
            text,
        )


class AlwaysOnHeaderTests(TestCase):
    """H2: these were gated behind `if not DEBUG` and vanished as a group."""

    def test_headers_apply_regardless_of_debug(self):
        with override_settings(DEBUG=True):
            response = self.client.get(reverse("core:home"))
        self.assertEqual(response.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.get("X-Frame-Options"), "DENY")
        self.assertEqual(response.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_session_cookie_is_not_permanent(self):
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, 60 * 60 * 24,
                             "admin sessions should not last days")
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)


class TransportSecurityTests(TestCase):
    """M4: preload was asserted at 30 days; the list requires a year."""

    def test_hsts_meets_the_preload_minimum(self):
        self.assertGreaterEqual(settings.SECURE_HSTS_SECONDS, 31_536_000)
        self.assertTrue(settings.SECURE_HSTS_PRELOAD)


class PasswordPolicyTests(TestCase):
    """H4: the admin password is the only gate on the console."""

    def test_minimum_length_is_raised(self):
        validator = next(
            v for v in settings.AUTH_PASSWORD_VALIDATORS
            if v["NAME"].endswith("MinimumLengthValidator")
        )
        self.assertGreaterEqual(validator.get("OPTIONS", {}).get("min_length", 8), 12)

    def test_lockout_backend_is_installed(self):
        self.assertIn("axes", settings.INSTALLED_APPS)
        self.assertEqual(settings.AUTHENTICATION_BACKENDS[0],
                         "axes.backends.AxesStandaloneBackend")
        self.assertIn("axes.middleware.AxesMiddleware", settings.MIDDLEWARE)


class UploadLimitTests(TestCase):
    """Bounded request bodies and a capped image decode size."""

    def test_request_size_limits_are_pinned(self):
        self.assertLessEqual(settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 5 * 1024 * 1024)
        self.assertLessEqual(settings.DATA_UPLOAD_MAX_NUMBER_FIELDS, 1000)

    def test_pillow_decompression_bomb_guard(self):
        from PIL import Image
        self.assertIsNotNone(Image.MAX_IMAGE_PIXELS)
        self.assertLessEqual(Image.MAX_IMAGE_PIXELS, 100_000_000)


class ImageUploadTests(TestCase):
    """M8: the stored filename must not carry an attacker-chosen extension."""

    def test_upload_path_discards_the_submitted_name(self):
        from apps.case_studies.models import case_study_image_path
        path = case_study_image_path(None, "payload.html")
        self.assertFalse(path.endswith(".html"))
        self.assertNotIn("payload", path)
        self.assertTrue(path.startswith("case_studies/"))

    def test_upload_path_keeps_legitimate_extensions(self):
        from apps.case_studies.models import case_study_image_path
        self.assertTrue(case_study_image_path(None, "cover.PNG").endswith(".png"))


class JSONFieldValidationTests(TestCase):
    """L4: a non-list value reached the template and raised a 500."""

    def test_rejects_non_list(self):
        for bad in (123, {"a": 1}, "text", None):
            with self.subTest(value=bad):
                with self.assertRaises(ValidationError):
                    validate_string_list(bad)

    def test_rejects_non_string_entries(self):
        with self.assertRaises(ValidationError):
            validate_string_list(["fine", 42])

    def test_rejects_oversized_lists(self):
        with self.assertRaises(ValidationError):
            validate_string_list([f"item {i}" for i in range(200)])

    def test_accepts_a_normal_list(self):
        validate_string_list(["24/7 SOC", "MITRE ATT&CK mapped"])


class DeploymentCheckTests(TestCase):
    """H5: a production boot must refuse to log inquiry PII."""

    def test_console_email_backend_is_reported_in_production(self):
        from apps.core.checks import check_production_configuration
        with override_settings(
            DEBUG=False,
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
        ):
            ids = [m.id for m in check_production_configuration(None)]
        self.assertIn("sectrex.E001", ids)

    def test_placeholder_secret_key_is_reported_in_production(self):
        from apps.core.checks import check_production_configuration
        with override_settings(DEBUG=False, SECRET_KEY="django-insecure-change-me"):
            ids = [m.id for m in check_production_configuration(None)]
        self.assertIn("sectrex.E002", ids)

    def test_findings_only_warn_by_default(self):
        """A configuration slip must not take the site down."""
        from django.core.checks import WARNING
        from apps.core.checks import check_production_configuration

        with override_settings(
            DEBUG=False,
            STRICT_DEPLOY_CHECKS=False,
            SECRET_KEY="django-insecure-change-me",
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
        ):
            messages = check_production_configuration(None)
        self.assertTrue(messages)
        for message in messages:
            with self.subTest(id=message.id):
                self.assertEqual(message.level, WARNING)
                self.assertFalse(message.is_serious())

    def test_strict_mode_promotes_them_to_errors(self):
        from django.core.checks import ERROR
        from apps.core.checks import check_production_configuration

        with override_settings(
            DEBUG=False,
            STRICT_DEPLOY_CHECKS=True,
            SECRET_KEY="django-insecure-change-me",
            EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend",
        ):
            serious = [m for m in check_production_configuration(None) if m.level >= ERROR]
        self.assertEqual({m.id for m in serious}, {"sectrex.E001", "sectrex.E002"})

    def test_checks_stay_quiet_in_development(self):
        from apps.core.checks import check_production_configuration
        with override_settings(DEBUG=True):
            self.assertEqual(check_production_configuration(None), [])


class DeadSinkTests(TestCase):
    """L1: an undefined loop variable rendered through |safe site-wide."""

    def test_footer_has_no_unescaped_sink(self):
        import re
        from pathlib import Path

        footer = Path(settings.BASE_DIR, "templates/partials/footer.html").read_text()
        # Strip {# ... #} comments first: the removal is documented inline and
        # that note legitimately mentions the filter it replaced.
        active = re.sub(r"\{#.*?#\}", "", footer, flags=re.S)
        self.assertNotIn("|safe", active, "footer must not render unescaped HTML")
        self.assertNotIn("{% for net in social %}", active)


class PrivacyNoticeTests(TestCase):
    """M7: the contact form collected consent with no notice to point at."""

    def test_privacy_page_is_published(self):
        response = self.client.get(reverse("core:privacy"))
        self.assertEqual(response.status_code, 200)

    def test_it_states_the_retention_period_actually_enforced(self):
        body = self.client.get(reverse("core:privacy")).content.decode()
        self.assertIn(str(settings.INQUIRY_RETENTION_DAYS), body)

    def test_it_covers_the_required_topics(self):
        body = self.client.get(reverse("core:privacy")).content.decode().lower()
        for topic in ("what we collect", "how long we keep it", "your rights",
                      "openstreetmap", "legitimate interest"):
            with self.subTest(topic=topic):
                self.assertIn(topic, body)

    def test_footer_links_to_it(self):
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn(reverse("core:privacy"), body)
