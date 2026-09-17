"""Content edited in the admin reaches the public pages.

This is the guarantee the admin migration was built for, so each editable
block is exercised: edit it, hide it, reorder it.
"""
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from tests.base import CacheIsolatedTestCase

from apps.core.models import (
    CompanyValue,
    CulturePillar,
    ExpertisePillar,
    HomeFeature,
    HomeStat,
    LeadershipMember,
    SiteSettings,
    TimelineEntry,
    TrustedByLogo,
)
from apps.services.models import Service

# model, page, kwargs for a new row, the text that should appear
EDITABLE_BLOCKS = [
    (TrustedByLogo, "core:home", {"name": "Test Client Bank"}, "Test Client Bank"),
    (HomeStat, "core:home", {"value": "42", "suffix": "%", "label": "Test Metric"}, "Test Metric"),
    (HomeFeature, "core:home", {"title": "Test Feature", "body": "Body copy."}, "Test Feature"),
    (CompanyValue, "core:about", {"title": "Test Value", "body": "Body copy."}, "Test Value"),
    (ExpertisePillar, "core:about", {"tag": "T1", "title": "Test Pillar", "body": "Body."}, "Test Pillar"),
    (LeadershipMember, "core:about",
     {"name": "Test Person", "role": "Tester", "bio": "Bio.", "initials": "TP"}, "Test Person"),
    (TimelineEntry, "core:about", {"year": "2099", "title": "Test Era", "body": "Body."}, "Test Era"),
    (CulturePillar, "careers:list", {"tag": "C1", "title": "Test Culture", "body": "Body."}, "Test Culture"),
]


class EditableContentTests(CacheIsolatedTestCase):
    def test_new_rows_appear_on_their_page(self):
        for model, page, kwargs, expected in EDITABLE_BLOCKS:
            with self.subTest(model=model.__name__):
                obj = model.objects.create(display_order=999, **kwargs)
                body = self.client.get(reverse(page)).content.decode()
                self.assertIn(expected, body)
                obj.delete()

    def test_unpublishing_hides_a_row(self):
        for model, page, kwargs, expected in EDITABLE_BLOCKS:
            with self.subTest(model=model.__name__):
                obj = model.objects.create(display_order=999, **kwargs)
                obj.is_published = False
                obj.save()
                body = self.client.get(reverse(page)).content.decode()
                self.assertNotIn(expected, body)
                obj.delete()

    def test_display_order_controls_sequence(self):
        TrustedByLogo.objects.all().delete()
        TrustedByLogo.objects.create(name="ZZZ Last", display_order=20)
        TrustedByLogo.objects.create(name="AAA First", display_order=10)
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertLess(body.index("AAA First"), body.index("ZZZ Last"))


class SiteSettingsTests(CacheIsolatedTestCase):
    def test_site_name_reaches_the_page_title(self):
        site = SiteSettings.load()
        site.name = "Renamed Company"
        site.save()
        body = self.client.get(reverse("core:home")).content.decode()
        self.assertIn("Renamed Company", body)

    def test_is_a_singleton(self):
        SiteSettings.load()
        SiteSettings.objects.create(name="Second Row")
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_refuses_instance_deletion(self):
        """The site cannot render without these values."""
        with self.assertRaises(ProtectedError):
            SiteSettings.load().delete()
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_refuses_queryset_deletion(self):
        """Regression: Model.delete() is not called for bulk deletes.

        The guard used to live only on the instance method, so
        `objects.all().delete()` removed the row and the site silently
        reverted to field defaults.
        """
        SiteSettings.load()
        with self.assertRaises(ProtectedError):
            SiteSettings.objects.all().delete()
        self.assertEqual(SiteSettings.objects.count(), 1)

        with self.assertRaises(ProtectedError):
            SiteSettings.objects.filter(pk=1).delete()
        self.assertEqual(SiteSettings.objects.count(), 1)


class ServiceContentTests(CacheIsolatedTestCase):
    def test_service_fields_render_on_the_services_page(self):
        Service.objects.create(
            title="Test Service", slug="test-service", anchor="test-service",
            tag="99", short_description="Teaser copy.", description="Long copy.",
            intro="Intro paragraph here.", outcome="A measurable outcome.",
            capabilities=["First capability", "Second capability"],
            icon_key="radar", display_order=999,
        )
        body = self.client.get(reverse("services:list")).content.decode()
        for expected in ("Test Service", "Intro paragraph here.",
                         "A measurable outcome.", "First capability"):
            with self.subTest(text=expected):
                self.assertIn(expected, body)

    def test_icon_key_renders_an_svg(self):
        service = Service.objects.create(
            title="Icon Test", slug="icon-test", short_description="x",
            description="x", icon_key="radar",
        )
        self.assertIn("<svg", service.icon)

    def test_unknown_icon_key_degrades_quietly(self):
        """A bad key must not break the page."""
        service = Service.objects.create(
            title="Bad Icon", slug="bad-icon", short_description="x",
            description="x", icon_key="does-not-exist",
        )
        self.assertEqual(service.icon, "")
        self.assertEqual(self.client.get(reverse("services:list")).status_code, 200)

    def test_anchor_defaults_to_slug(self):
        service = Service.objects.create(
            title="Anchorless", short_description="x", description="x",
        )
        self.assertEqual(service.anchor, service.slug)
