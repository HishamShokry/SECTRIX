from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "core:home",
            "core:about",
            "services:list",
            "case_studies:list",
            "careers:list",
            "contact:contact",
        ]

    def location(self, item):
        return reverse(item)
