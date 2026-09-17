from django.conf import settings


def site_meta(request):
    return {
        "site": getattr(settings, "SITE_META", {}),
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
