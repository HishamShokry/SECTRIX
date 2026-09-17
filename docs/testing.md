# Testing

End-to-end coverage of the public site, the admin editing flow, and the
production configuration. 52 tests, no external services required.

## Running

```bash
# Everything, including real-browser tests
DJANGO_DEBUG=False python manage.py test tests

# Fast layer only — skips Playwright, runs in ~1.5s
DJANGO_DEBUG=False SKIP_BROWSER_TESTS=1 python manage.py test tests

# Inside the container
docker compose exec -e DJANGO_DEBUG=False web python manage.py test tests

# Catch order-dependent failures
DJANGO_DEBUG=False python manage.py test tests --shuffle
```

> **`DJANGO_DEBUG=False` is required.** The production hardening block in
> `sectrix/settings.py` is guarded by `if not DEBUG` and evaluated at import
> time, so the test runner forcing `DEBUG=False` afterwards is too late. Without
> it the security tests skip rather than silently assert Django's defaults.

## What is covered

| Module | Covers |
|---|---|
| `test_pages.py` | Every route returns 200 with its template, title and meta description; navigation links resolve on every page; 404 handler; no stale `Sectrix` spelling; pages are not near-empty shells |
| `test_admin_content.py` | Each editable block appears on its page when created, disappears when unpublished, and respects `display_order`; site settings reach the page title; the settings singleton holds; icons render, unknown keys degrade quietly |
| `test_contact_form.py` | Field rendering, valid submission stored and redirected, inbox notification, honeypot, email validation, required fields, IP hashing, user-agent truncation |
| `test_seo_and_security.py` | `robots.txt` and the `noindex` tag in both indexing modes, sitemap contents, admin auth, security headers, HSTS over HTTPS, secure cookie flags |
| `test_seeding.py` | `seed_demo` populates, does not duplicate, and **does not overwrite admin edits**; seeded services get a real icon key; the content data migration landed |
| `test_browser_e2e.py` | Chromium: no JS errors on any page, no horizontal overflow at 375px, Alpine mobile menu opens and closes, contact form submitted through the browser, navigation between pages |

## Browser tests

Playwright with Chromium. They skip cleanly when Playwright or its browser is
missing, or with `SKIP_BROWSER_TESTS=1`, so CI without browsers still runs the
other 47.

First-time setup:

```bash
pip install playwright && playwright install chromium
```

The module sets `DJANGO_ALLOW_ASYNC_UNSAFE=1`: Playwright's sync API drives an
event loop, which makes Django treat ORM calls on that thread as async-unsafe.
The live server runs in its own thread, so the guard is a false positive.

## Test isolation

`SiteSettings.load()` caches the singleton for five minutes. Django rolls the
database back between tests but the cache is process-global and survives, so
tests touching cached content inherit `CacheIsolatedTestCase` from
`tests/base.py`. Run with `--shuffle` after adding tests that mutate site
settings.
