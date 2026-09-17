"""seed_demo runs on every container start, so it must never clobber edits."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.careers.models import JobOpening
from apps.case_studies.models import CaseStudy
from apps.services.models import Service
from tests.base import CacheIsolatedTestCase


class SeedDemoTests(TestCase):
    def seed(self):
        call_command("seed_demo", stdout=StringIO())

    def test_seeding_populates_every_demo_model(self):
        self.seed()
        self.assertGreater(Service.objects.count(), 0)
        self.assertGreater(CaseStudy.objects.count(), 0)
        self.assertGreater(JobOpening.objects.count(), 0)

    def test_reseeding_does_not_duplicate_rows(self):
        self.seed()
        counts = (Service.objects.count(), CaseStudy.objects.count(), JobOpening.objects.count())
        self.seed()
        self.assertEqual(
            counts,
            (Service.objects.count(), CaseStudy.objects.count(), JobOpening.objects.count()),
        )

    def test_reseeding_preserves_admin_edits(self):
        """The failure this guards against reverts a client's edits on restart."""
        self.seed()
        service = Service.objects.first()
        service.title = "Edited In Admin"
        service.save()

        study = CaseStudy.objects.first()
        study.title = "Edited Case Study"
        study.save()

        job = JobOpening.objects.first()
        job.title = "Edited Role"
        job.save()

        self.seed()

        self.assertEqual(Service.objects.get(pk=service.pk).title, "Edited In Admin")
        self.assertEqual(CaseStudy.objects.get(pk=study.pk).title, "Edited Case Study")
        self.assertEqual(JobOpening.objects.get(pk=job.pk).title, "Edited Role")

    def test_seeded_services_get_a_real_icon_key(self):
        """Regression: seeding used to write the anchor slug into icon_key."""
        Service.objects.all().delete()
        self.seed()
        for service in Service.objects.all():
            with self.subTest(service=service.anchor):
                self.assertIn("<svg", service.icon)

    def test_deleted_rows_are_restored_on_next_seed(self):
        self.seed()
        Service.objects.all().delete()
        self.seed()
        self.assertGreater(Service.objects.count(), 0)


class ContentMigrationTests(CacheIsolatedTestCase):
    """The data migration ran before these tests, so its output is assertable."""

    def test_imported_content_is_present(self):
        from apps.core.models import (
            CompanyValue, CulturePillar, ExpertisePillar, HomeFeature,
            HomeStat, LeadershipMember, SiteSettings, TimelineEntry, TrustedByLogo,
        )
        for model in (TrustedByLogo, HomeStat, HomeFeature, CompanyValue,
                      ExpertisePillar, LeadershipMember, TimelineEntry, CulturePillar):
            with self.subTest(model=model.__name__):
                self.assertGreater(model.objects.count(), 0)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_site_settings_carry_the_rebranded_values(self):
        from apps.core.models import SiteSettings
        site = SiteSettings.load()
        self.assertIn("Sectrex", site.name)
        self.assertIn("sectrexconsulting.com", site.url)
