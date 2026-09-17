"""Delete contact inquiries past their retention period.

GDPR Art. 5(1)(e) requires personal data to be kept no longer than necessary.
Nothing here expires on its own, so this command is the retention mechanism --
schedule it (cron, systemd timer, or a scheduled container run).

    python manage.py purge_inquiries --dry-run
    python manage.py purge_inquiries
"""
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.contact.models import ContactInquiry


class Command(BaseCommand):
    help = "Delete contact inquiries older than the configured retention period."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=getattr(settings, "INQUIRY_RETENTION_DAYS", 730),
            help="Retention window in days (default: INQUIRY_RETENTION_DAYS).",
        )
        parser.add_argument(
            "--include-unhandled",
            action="store_true",
            help="Also purge inquiries never marked handled. Off by default so "
                 "an unworked lead is not silently discarded.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be deleted without deleting it.",
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options["days"])
        queryset = ContactInquiry.objects.filter(created_at__lt=cutoff)
        if not options["include_unhandled"]:
            queryset = queryset.filter(is_handled=True)

        count = queryset.count()
        if options["dry_run"]:
            self.stdout.write(
                f"Would delete {count} inquiries created before {cutoff:%Y-%m-%d}."
            )
            return

        deleted, _ = queryset.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {deleted} inquiries created before {cutoff:%Y-%m-%d}."
            )
        )
