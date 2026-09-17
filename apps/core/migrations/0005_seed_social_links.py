"""Seed the social links that were hardcoded in the footer.

Carries the existing three across so the rendered footer is unchanged, and
they become editable instead of requiring a deploy.
"""
from django.db import migrations

LINKS = [
    # (name, url, icon_key, display_order)
    ("LinkedIn", "https://www.linkedin.com/", "linkedin", 10),
    ("X / Twitter", "https://twitter.com/", "x", 20),
    ("GitHub", "https://github.com/", "github", 30),
]


def seed(apps, schema_editor):
    SocialLink = apps.get_model("core", "SocialLink")
    if SocialLink.objects.exists():
        return  # never clobber edited content
    SocialLink.objects.bulk_create([
        SocialLink(name=name, url=url, icon_key=icon, display_order=order, is_published=True)
        for name, url, icon, order in LINKS
    ])


def unseed(apps, schema_editor):
    apps.get_model("core", "SocialLink").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [("core", "0004_sociallink")]

    operations = [migrations.RunPython(seed, unseed)]
