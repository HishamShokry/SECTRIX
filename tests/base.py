"""Shared test base classes."""
from django.core.cache import cache
from django.test import TestCase


class CacheIsolatedTestCase(TestCase):
    """A TestCase that also rolls back the cache.

    ``SiteSettings.load()`` caches the singleton for five minutes. Django wraps
    each test in a transaction and rolls the database back, but the cache is
    process-global and survives, so a test that edits site settings would leak
    into whatever runs next. Any test touching cached content should use this.
    """

    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()
