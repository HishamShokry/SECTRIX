"""Move the hardcoded site copy into the database.

One-time import so the site keeps rendering exactly what it did before the
content became admin-editable. Runs once; later admin edits are never
overwritten by it.
"""
from django.db import migrations


def _icon_key_for(svg, icons):
    """Reverse-map an inline SVG string back to its registry key."""
    for key, markup in icons.items():
        if markup == svg:
            return key
    return "shield"


def load_content(apps, schema_editor):
    try:
        from apps.core import content
        from apps.core.icons import ICONS
    except ImportError:  # pragma: no cover - content module removed later
        return

    from django.conf import settings

    # --- Site-wide identity, previously settings.SITE_META ---------------
    meta = getattr(settings, "SITE_META", {})
    SiteSettings = apps.get_model("core", "SiteSettings")
    SiteSettings.objects.update_or_create(
        pk=1,
        defaults={
            "name": meta.get("name", "Sectrex Consulting"),
            "tagline": meta.get("tagline", ""),
            "description": meta.get("description", ""),
            "keywords": meta.get("keywords", ""),
            "url": meta.get("url", "https://sectrexconsulting.com"),
            "twitter": meta.get("twitter", ""),
            "email": meta.get("email", ""),
            "phone": meta.get("phone", ""),
            "address": meta.get("address", ""),
        },
    )

    def bulk(model_name, rows, build):
        model = apps.get_model("core", model_name)
        if model.objects.exists():
            return  # already populated; never clobber edited content
        model.objects.bulk_create(
            [model(display_order=(i + 1) * 10, **build(r)) for i, r in enumerate(rows)]
        )

    bulk("TrustedByLogo", content.TRUSTED_BY, lambda r: {"name": r})
    bulk("HomeStat", content.HOME_STATS, lambda r: {
        "value": r["value"], "suffix": r.get("suffix", ""), "label": r["label"],
    })
    bulk("HomeFeature", content.HOME_FEATURES, lambda r: {
        "title": r["title"], "body": r["body"],
        "icon_key": _icon_key_for(r.get("icon", ""), ICONS),
    })
    bulk("CompanyValue", content.COMPANY_VALUES, lambda r: {
        "title": r["title"], "body": r["body"],
    })
    bulk("ExpertisePillar", content.EXPERTISE_PILLARS, lambda r: {
        "tag": r["tag"], "title": r["title"], "body": r["body"],
    })
    bulk("LeadershipMember", content.LEADERSHIP, lambda r: {
        "name": r["name"], "role": r["role"], "bio": r["bio"], "initials": r["initials"],
    })
    bulk("TimelineEntry", content.TIMELINE, lambda r: {
        "year": r["year"], "title": r["title"], "body": r["body"],
    })
    bulk("CulturePillar", content.CULTURE_PILLARS, lambda r: {
        "tag": r["tag"], "title": r["title"], "body": r["body"],
    })

    # --- Services -------------------------------------------------------
    # The services page used to render from SERVICE_DETAIL, so the Service
    # rows never needed these fields. seed_demo also wrote the anchor into
    # icon_key, which was harmless while nothing read it and is corrected
    # here by reverse-mapping the SVG the page actually displayed.
    Service = apps.get_model("services", "Service")
    teaser_by_anchor = {t["anchor"]: t for t in content.SERVICE_TEASERS}

    for order, detail in enumerate(content.SERVICE_DETAIL, start=1):
        anchor = detail["anchor"]
        teaser = teaser_by_anchor.get(anchor, {})
        defaults = {
            "title": detail["title"],
            "short_description": teaser.get("summary", detail["intro"])[:240],
            "description": detail["intro"],
            "icon_key": _icon_key_for(detail.get("icon", ""), ICONS),
            "capabilities": detail["capabilities"],
            "anchor": anchor,
            "tag": detail.get("tag", ""),
            "intro": detail["intro"],
            "outcome": detail.get("outcome", "")[:240],
            "display_order": order,
            "is_published": True,
        }
        if not Service.objects.filter(slug=anchor).update(**defaults):
            Service.objects.create(slug=anchor, **defaults)


def unload_content(apps, schema_editor):
    """Reverse: drop the imported rows so the migration is undoable."""
    for model_name in (
        "TrustedByLogo", "HomeStat", "HomeFeature", "CompanyValue",
        "ExpertisePillar", "LeadershipMember", "TimelineEntry",
        "CulturePillar", "SiteSettings",
    ):
        apps.get_model("core", model_name).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        # Needs Service.anchor / tag / intro / outcome to exist.
        ("services", "0002_service_anchor_service_intro_service_outcome_and_more"),
    ]

    operations = [migrations.RunPython(load_content, unload_content)]
