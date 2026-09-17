"""The contact form is the site's only conversion path, so it gets full cover."""
import hashlib
from smtplib import SMTPException
from unittest import mock

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.contact.models import ContactInquiry
from apps.contact.views import hash_ip

VALID = {
    "full_name": "Jane Al-Mansoori",
    "work_email": "jane@examplecorp.com",
    "phone": "+971 50 000 0000",
    "company": "Example Corp",
    "job_title": "Head of Information Security",
    "country": "United Arab Emirates",
    "organization_size": "501_2000",
    "interest": "threat_detection",
    "message": "We would like to discuss our SOC roadmap.",
}


class ContactSubmissionTests(TestCase):
    def test_form_renders_with_every_field(self):
        body = self.client.get(reverse("contact:contact")).content.decode()
        for field in VALID:
            with self.subTest(field=field):
                self.assertIn(f'name="{field}"', body)

    def test_valid_submission_is_stored_and_redirects(self):
        response = self.client.post(reverse("contact:contact"), VALID)
        self.assertRedirects(response, reverse("contact:thanks"))
        inquiry = ContactInquiry.objects.get()
        self.assertEqual(inquiry.full_name, VALID["full_name"])
        self.assertEqual(inquiry.company, VALID["company"])
        self.assertFalse(inquiry.is_handled)

    def test_valid_submission_notifies_the_inbox(self):
        self.client.post(reverse("contact:contact"), VALID)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [settings.CONTACT_INBOX])
        self.assertIn(VALID["company"], mail.outbox[0].body)
        self.assertIn(VALID["message"], mail.outbox[0].body)

    def test_subject_carries_no_submitter_input(self):
        """Attacker-controlled text in a header let a submitter kill the email."""
        self.client.post(reverse("contact:contact"), VALID)
        self.assertNotIn(VALID["company"], mail.outbox[0].subject)
        self.assertNotIn(VALID["full_name"], mail.outbox[0].subject)

    def test_newline_in_company_cannot_suppress_the_notification(self):
        """Regression: BadHeaderError was swallowed, losing the inquiry silently."""
        self.client.post(reverse("contact:contact"),
                         {**VALID, "company": "Acme\nBcc: attacker@evil.test"})
        self.assertEqual(ContactInquiry.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1, "notification was suppressed by header injection")

    def test_successful_notification_is_recorded(self):
        self.client.post(reverse("contact:contact"), VALID)
        self.assertIsNotNone(ContactInquiry.objects.get().notified_at)

    def test_failed_notification_is_logged_and_flagged(self):
        """A broken mail path must leave a signal, not vanish."""
        with mock.patch("apps.contact.views.send_mail", side_effect=SMTPException("relay down")):
            with self.assertLogs("apps.contact.views", level="ERROR") as logs:
                self.client.post(reverse("contact:contact"), VALID)
        inquiry = ContactInquiry.objects.get()
        self.assertIsNone(inquiry.notified_at)
        self.assertTrue(any("Contact notification failed" in m for m in logs.output))

    def test_honeypot_rejects_bots(self):
        response = self.client.post(reverse("contact:contact"), {**VALID, "website": "http://spam"})
        self.assertEqual(response.status_code, 200)  # redisplayed, not redirected
        self.assertEqual(ContactInquiry.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_invalid_email_is_rejected(self):
        self.client.post(reverse("contact:contact"), {**VALID, "work_email": "not-an-email"})
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_required_fields_are_enforced(self):
        for field in ("full_name", "work_email", "company", "message"):
            with self.subTest(field=field):
                self.client.post(reverse("contact:contact"), {**VALID, field: ""})
                self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_ip_is_hashed_not_stored_raw(self):
        """The model keeps ip_hash, so the raw address must never land in it."""
        self.client.post(reverse("contact:contact"), VALID, REMOTE_ADDR="203.0.113.7")
        inquiry = ContactInquiry.objects.get()
        self.assertNotIn("203.0.113.7", inquiry.ip_hash)
        self.assertEqual(len(inquiry.ip_hash), 64)

    def test_ip_hash_is_keyed_not_a_bare_digest(self):
        """A bare SHA-256 of an IPv4 address is reversible by exhaustion."""
        self.client.post(reverse("contact:contact"), VALID, REMOTE_ADDR="203.0.113.7")
        bare = hashlib.sha256(b"203.0.113.7").hexdigest()
        self.assertNotEqual(ContactInquiry.objects.get().ip_hash, bare)

    @override_settings(BEHIND_PROXY=True)
    def test_client_ip_is_read_from_the_proxy_header(self):
        """Behind nginx, REMOTE_ADDR is the proxy — every row would collide."""
        self.client.post(reverse("contact:contact"), VALID,
                         REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="203.0.113.7, 10.0.0.1")
        expected = hash_ip("203.0.113.7")
        self.assertEqual(ContactInquiry.objects.get().ip_hash, expected)

    def test_long_user_agent_is_truncated_to_field_length(self):
        self.client.post(reverse("contact:contact"), VALID, HTTP_USER_AGENT="x" * 900)
        self.assertLessEqual(len(ContactInquiry.objects.get().user_agent), 400)

    def test_thanks_page_is_reachable_directly(self):
        self.assertEqual(self.client.get(reverse("contact:thanks")).status_code, 200)


class AntiAutomationTests(TestCase):
    """L5: the honeypot alone is bypassed by posting only visible fields."""

    def test_instant_submission_is_rejected(self):
        """A bot posts the moment it has the form; a person cannot."""
        from django.core import signing
        import time

        payload = {**VALID, "rendered_at": signing.dumps(time.time())}
        self.client.post(reverse("contact:contact"), payload)
        self.assertEqual(ContactInquiry.objects.count(), 0)

    def test_submission_after_a_human_pause_is_accepted(self):
        from django.core import signing
        import time

        payload = {**VALID, "rendered_at": signing.dumps(time.time() - 30)}
        response = self.client.post(reverse("contact:contact"), payload)
        self.assertRedirects(response, reverse("contact:thanks"))
        self.assertEqual(ContactInquiry.objects.count(), 1)

    def test_missing_timestamp_does_not_lock_anyone_out(self):
        """Fail open on a missing value: the goal is cost, not a hard gate."""
        response = self.client.post(reverse("contact:contact"), VALID)
        self.assertRedirects(response, reverse("contact:thanks"))

    def test_forged_timestamp_is_ignored(self):
        """The value is signed, so it cannot be back-dated by the client."""
        payload = {**VALID, "rendered_at": "not-a-valid-signature"}
        response = self.client.post(reverse("contact:contact"), payload)
        self.assertRedirects(response, reverse("contact:thanks"))

    def test_honeypot_error_is_visible_to_the_user(self):
        """Attached to a never-rendered field, a false positive was silent."""
        response = self.client.post(reverse("contact:contact"),
                                    {**VALID, "website": "http://spam"})
        self.assertContains(response, "Spam detected.")
