"""Run migrations under an advisory lock.

The entrypoint migrates on every container start, so a rolling redeploy or a
crash-loop can run two `migrate` processes against one database at the same
time and leave the schema half-applied. Postgres advisory locks serialise
them: the second process waits rather than racing.

SQLite has no equivalent and is single-writer anyway, so the lock is skipped.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

# Arbitrary but stable 64-bit key, unique to this project's migrations.
LOCK_ID = 7_213_559_004_112


class Command(BaseCommand):
    help = "Apply migrations, serialised across concurrent container starts."

    def add_arguments(self, parser):
        parser.add_argument("--noinput", action="store_true", default=True)

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            self.stdout.write("Non-Postgres backend; migrating without a lock.")
            call_command("migrate", interactive=False)
            return

        with connection.cursor() as cursor:
            self.stdout.write("Acquiring migration lock…")
            cursor.execute("SELECT pg_advisory_lock(%s)", [LOCK_ID])
            try:
                call_command("migrate", interactive=False)
            finally:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])
                self.stdout.write("Migration lock released.")
