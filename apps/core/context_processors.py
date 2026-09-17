from django.conf import settings

from .models import SiteSettings


def site_meta(request):
    return {
        # Admin-editable; falls back to settings.SITE_META only if the table
        # is not migrated yet (e.g. during the first deploy).
        "site": _site(),
        "allow_indexing": getattr(settings, "ALLOW_INDEXING", False),
        "nav_items": [
            {"label": "Home", "url_name": "core:home"},
            {"label": "About", "url_name": "core:about"},
            {"label": "Services", "url_name": "services:list"},
            {"label": "Case Studies", "url_name": "case_studies:list"},
            {"label": "Careers", "url_name": "careers:list"},
            {"label": "Contact", "url_name": "contact:contact"},
        ],
    }


def _site():
    try:
        return SiteSettings.load()
    except Exception:
        # Table missing or unreadable — render with the static defaults rather
        # than 500ing the whole site.
        return getattr(settings, "SITE_META", {})
