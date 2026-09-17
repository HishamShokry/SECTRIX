"""The contact form is the site's only conversion path, so it gets full cover."""
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from apps.contact.models import ContactInquiry

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
        self.assertIn(VALID["company"], mail.outbox[0].subject)
        self.assertIn(VALID["message"], mail.outbox[0].body)

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
        self.assertEqual(len(inquiry.ip_hash), 64)  # sha256 hex

    def test_long_user_agent_is_truncated_to_field_length(self):
        self.client.post(reverse("contact:contact"), VALID, HTTP_USER_AGENT="x" * 900)
        self.assertLessEqual(len(ContactInquiry.objects.get().user_agent), 400)

    def test_thanks_page_is_reachable_directly(self):
        self.assertEqual(self.client.get(reverse("contact:thanks")).status_code, 200)
