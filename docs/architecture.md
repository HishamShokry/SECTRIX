# Architecture

## Stack at a glance

| Layer | Choice | Why this choice |
|---|---|---|
| Web framework | **Django 5** | Mature, batteries-included admin gives editors a real CMS surface for case studies and jobs without a separate headless layer. |
| Templates | **Django Templates** | Server-rendered HTML matches the site's read-mostly, SEO-critical nature. No SPA hydration tax. |
| CSS | **Tailwind (CDN, configured inline)** | Lets the brand tokens live in `base.html` with zero build step. A real build pipeline is a one-file swap when needed — see [`frontend.md`](frontend.md). |
| Interactivity | **Alpine.js** | Three discrete bits of state (nav, mobile menu, case-study filter). Alpine fits in one CDN script; no bundler. |
| DB | **PostgreSQL** in prod, **SQLite** in dev | One toggle — `DJANGO_DB_ENGINE=postgres` — switches drivers. Models are flat enough to be SQLite-compatible for local dev. |
| App server | **Gunicorn** (3 workers × 2 threads) | Standard, predictable. Threaded workers are fine for this read-heavy workload. |
| Static serving | **WhiteNoise** with `CompressedManifestStaticFilesStorage` | Hashed + gzipped assets served by Django itself. No nginx needed in the container; add a reverse proxy when traffic justifies it. |

## App boundaries

```
apps/
├── core/           ← Home, About, sitemap, marketing copy, seed command
├── services/       ← Service model (canonical 6 still render from core.content)
├── case_studies/   ← CaseStudy model + paginated list
├── careers/        ← JobOpening model + list
└── contact/        ← ContactInquiry model + form + view
```

Each app owns its own URLs, views, templates folder, models, and admin. Cross-app imports are deliberate and minimal:

- `apps.core.views.HomeView` pulls counts from `apps.services` and `apps.case_studies` for the home page.
- `apps.core.content` is imported by `apps.services.views` and `apps.careers.views` for static page content. This is the only "shared content" coupling.
- `apps.core.management.commands.seed_demo` writes into all three DB-backed apps.

There is **no shared models app**. If models grow shared concerns, that's a signal to add one — not to introduce circular imports.

## Request lifecycle

A request for `/case-studies/` flows like this:

```
Browser ──► (Docker) ──► gunicorn worker
                              │
                              ├─ WhiteNoiseMiddleware  → if /static/* exists on disk, serve it directly (gzipped, hashed)
                              │
                              ├─ SecurityMiddleware    → HSTS/XFO/CSP headers (production only)
                              ├─ SessionMiddleware     → cookie → session
                              ├─ CSRF, Auth, Messages, Clickjacking
                              │
                              ▼
                      sectrix/urls.py
                              │   path("case-studies/", include("apps.case_studies.urls"))
                              ▼
                      apps/case_studies/urls.py
                              │   path("", CaseStudyListView.as_view(), name="list")
                              ▼
                      apps/case_studies/views.py   → CaseStudyListView (paginated queryset)
                              │
                              ▼
                      templates/case_studies/list.html   → extends base.html → includes partials/
                              │
                              ▼
                      Django Templates render → HTML response
```

The context processor at `apps.core.context_processors.site_meta` runs on every request and injects:

- `site` — the `SITE_META` dict from `settings.py` (name, tagline, address, etc.)
- `nav_items` — the canonical nav, consumed by `partials/navbar.html` and `partials/footer.html`

Adding a new top-level nav item is a one-line edit in that context processor — no template loop changes needed.

## Content strategy — DB vs `core.content`

The site mixes two content sources. The split is intentional:

| Page | Source | Reasoning |
|---|---|---|
| Home (hero, stats, features) | `core.content` | Hand-tuned marketing copy paired with inline SVG icons. No real benefit from a DB admin. |
| About (mission, values, leadership, timeline) | `core.content` | Same — strongly designed, evolves with brand strategy, not with operations. |
| **Services** | `core.content.SERVICE_DETAIL` | Six canonical services from the brief. The `Service` model exists so admin can add future extras, but the page renders the canonical six statically so it always looks complete. |
| **Case Studies** | `CaseStudy` model | Operations team adds case studies as clients consent. Card-style rendering benefits from per-row sorting, tags, sector filters, pagination. |
| **Careers** | `JobOpening` model | Roles change weekly. Admin-managed. |
| **Contact** | `ContactInquiry` model | Inbound submissions. Editable in admin for lifecycle tracking. |

When in doubt: **if it changes more often than once a quarter and a non-engineer should edit it, put it in the DB. Otherwise put it in `core.content`.**

## Static asset pipeline

```
static/                     ← source assets (committed)
   img/favicon.svg
   img/logo.svg
   img/og-default.svg
   site.webmanifest

         │  python manage.py collectstatic  (run in entrypoint.sh)
         ▼

staticfiles/                ← build output (gitignored)
   img/favicon.svg
   img/favicon.9f37729e8bce.svg   ← hashed copy
   img/favicon.9f37729e8bce.svg.gz
   staticfiles.json               ← manifest read by WhiteNoise
```

WhiteNoise serves the hashed copy with `Cache-Control: max-age=31536000, immutable`. Templates that use `{% static "img/favicon.svg" %}` automatically resolve to the hashed URL via the manifest. **If you reference a static file that doesn't exist, `collectstatic` will fail to build the manifest — and the container will refuse to start.** That's a feature.

## Container topology

```
┌─────────────────────────────┐         ┌────────────────────────────┐
│ sectrix-web                 │  TCP    │ sectrix-db                 │
│ python:3.12-slim            │ ──────► │ postgres:16-alpine         │
│ gunicorn @ :8000 (in cnt)   │         │ pg_isready healthcheck     │
│ non-root user (uid 1000)    │         │ volume: pgdata             │
│ volume: media               │         │                            │
└──────────────┬──────────────┘         └────────────────────────────┘
               │ host:8001 → cnt:8000
               ▼
        host network
```

- The web container is **the only thing exposed to host**. The DB is reachable on host loopback `127.0.0.1:5433` for `psql` debugging only.
- No reverse proxy (nginx/Caddy/Traefik) is in front. For production behind a real domain, terminate TLS at the proxy and forward to `web:8000`; the existing `SECURE_PROXY_SSL_HEADER` setting handles the `X-Forwarded-Proto` lift.
- `entrypoint.sh` runs migrations + seed + collectstatic on every boot. Migrations are idempotent; `seed_demo` is `update_or_create`-based and re-runnable; collectstatic is fast on warm filesystems.

## Production gaps (intentional, listed so they're not surprising)

- **No CDN.** WhiteNoise handles caching headers; add a CDN in front when traffic justifies it.
- **No CSP.** Adding a strict Content-Security-Policy header is a single middleware away (`django-csp`) but interacts with the Tailwind Play CDN — see [`security.md`](security.md).
- **No rate limiting on the contact form.** Honeypot + free-email block is the current spam control. Add `django-ratelimit` or Cloudflare turnstile in front when needed.
- **No background queue.** Contact form email is sent inline via Django's `send_mail`. If the SMTP backend is slow, the request blocks. Add Celery / RQ when a real outbound path is wired up.
- **No 2FA on admin.** Use `django-otp` + `django-two-factor-auth` once the admin is exposed to the public internet.
