# Sectrix — Corporate Portfolio Website

A premium, dark-themed Django 5 corporate site for Sectrix, an enterprise cybersecurity company targeting Gulf banks, governments, and large organizations.

## Stack

- **Django 5** · view layer, ORM, admin, sitemap, contact form
- **Django Templates** · `base.html` + reusable partials (`navbar`, `footer`, `cta`, `head_meta`, `logo`)
- **Tailwind CSS** · brand tokens (navy / graphite / accent blue) configured inline via Play CDN
- **Alpine.js** · mobile menu, sticky nav state, case-study filters
- **PostgreSQL-ready** · SQLite default for local dev, Postgres via env vars
- **WhiteNoise** · production static serving (already in `requirements.txt`)

## Project layout

```
manage.py
sectrix/                       Django project (settings, urls, wsgi, asgi)
apps/
├── core/                      home, about, sitemaps, marketing copy
│   ├── content.py             single source of truth for marketing text
│   └── management/commands/seed_demo.py
├── services/                  Service model + list view
├── case_studies/              CaseStudy model + list view
├── careers/                   JobOpening model + list view
└── contact/                   ContactInquiry model, form, view, admin
templates/                     base.html, partials/, per-app subfolders
static/img/                    logos, favicon, OG image
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env             # fill in DJANGO_SECRET_KEY at minimum
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo        # populate Services, Case Studies, Jobs
python manage.py runserver
```

Visit `http://localhost:8000/` for the marketing site, `/admin/` for the operations console.

## Switching to PostgreSQL

In `.env`:

```
DJANGO_DB_ENGINE=postgres
POSTGRES_DB=sectrix
POSTGRES_USER=sectrix
POSTGRES_PASSWORD=<secret>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Then `python manage.py migrate`.

## Switching from Tailwind CDN to a build pipeline

The base template currently loads Tailwind via Play CDN with an inline `tailwind.config` for the brand palette and animations. For production, swap to a real build:

1. `pip install django-tailwind` and follow its `python manage.py tailwind init` flow.
2. Copy the `theme.extend` block from `templates/base.html` into the generated `tailwind.config.js`.
3. Remove the two `<script>` tags in `<head>` and replace with `{% load tailwind_tags %}` + `{% tailwind_css %}`.

## Editing site content

- **Marketing copy** for the home and about pages lives in `apps/core/content.py`.
- **Services, case studies, and job openings** are managed through the Django admin.
- **Contact inquiries** are persisted to `ContactInquiry` and emailed to `CONTACT_INBOX`.

## Notes

- The contact form has a honeypot field and a free-email-provider check to soft-block low-quality inquiries.
- Site uses semantic HTML, has a skip-to-content link, supports keyboard navigation, and meets contrast targets across the dark UI.
- `sitemap.xml` and `robots.txt` are wired up.
- Structured-data (`Organization`) JSON-LD is emitted in `<head>`.
