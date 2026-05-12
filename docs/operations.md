# Operations

## Common commands

### Local (no Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env                     # set DJANGO_SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo               # populate services / case studies / jobs
python manage.py runserver
```

### Docker

```bash
docker compose up -d --build             # build + start (web + db)
docker compose logs -f web               # tail web logs
docker compose exec web python manage.py createsuperuser
docker compose exec db psql -U sectrix   # psql shell on the DB
docker compose down                      # stop (volumes preserved)
docker compose down -v                   # stop + wipe DB and media
```

On the current host, the web container is mapped to **host port 8001** because 8000 is held by another stack. Edit `docker-compose.yml` if your host has 8000 free.

## Environment variables reference

The container reads everything from environment. `.env.example` is the canonical list; values below describe what each does.

### Django core

| Var | Default | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev fallback | **Required in prod.** Min 50 random chars. |
| `DJANGO_DEBUG` | `True` (local) / `False` (compose) | Controls security middleware behavior. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated. Add your prod hostname. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | (empty) | Comma-separated full URLs (`https://sectrix.com`). Required when behind a reverse proxy. |
| `DJANGO_TIME_ZONE` | `Asia/Dubai` | Default reflects HQ TZ; data stored as UTC regardless. |

### Database

| Var | Default | Notes |
|---|---|---|
| `DJANGO_DB_ENGINE` | `sqlite` | Set to `postgres` to switch. Compose sets this automatically. |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | `sectrix` / `sectrix` / (compose default) | Match between web and db services in compose. |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `localhost` / `5432` | Compose sets `POSTGRES_HOST=db` so the web service resolves it via Docker DNS. |

### Email (contact form)

| Var | Default | Notes |
|---|---|---|
| `DJANGO_EMAIL_BACKEND` | `console` | Logs to stdout in dev. Use `django.core.mail.backends.smtp.EmailBackend` in prod. |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | empty / 587 / empty / empty / `True` | Standard SMTP config. |
| `DEFAULT_FROM_EMAIL` | `noreply@sectrix.com` | Envelope sender. |
| `CONTACT_INBOX` | `contact@sectrix.com` | Where new inquiries are notified. |

### Site

| Var | Default | Notes |
|---|---|---|
| `SITE_URL` | `https://sectrix.com` | Used in `og:url`, canonical, and sitemap. |
| `SECTRIX_SEED_DEMO` | `true` (compose entrypoint) | Set to `false` to skip seeding on container boot. |

## Admin panel

URL: `/admin/`

### Registered models

| Model | List view | Filters | Search |
|---|---|---|---|
| **Service** | title, icon_key, order, published, updated | published | title, description |
| **CaseStudy** | client, title, sector, region, published, date, order | sector, region, published | client, title, summary, narrative |
| **JobOpening** | title, department, level, type, location, remote, published, posted | department, level, type, remote, published | title, summary, description |
| **ContactInquiry** | created, name, company, interest, handled, handled_by | handled, interest, org_size, created | name, email, company, title, message |

`list_editable` is enabled on `is_published` and `display_order` for the editorial models — flip a row visible right from the changelist.

### Common admin tasks

- **Publish a case study** → tick `is_published` in the changelist. No deploy needed.
- **Reorder services** → edit `display_order` in the changelist (use 10/20/30 spacing for new inserts).
- **Mark a contact inquiry handled** → tick `is_handled` and fill `handled_by` and `internal_notes` from the detail page.
- **Soft-delete content** → flip `is_published` to False. The model is preserved; the public site stops showing it.

## Seed command

`apps/core/management/commands/seed_demo.py` is **idempotent** — it uses `update_or_create(slug=...)` and is safe to run repeatedly. It writes:

- 6 `Service` rows from `core.content.SERVICE_DETAIL`
- 6 `CaseStudy` rows with realistic GCC engagement narratives
- 6 `JobOpening` rows across SOC, cloud, IR, threat intel, offensive, and GRC

Edit `seed_demo.py` to change the seed data; re-running the command updates existing rows in place by slug.

The container entrypoint calls `seed_demo` on every boot unless `SECTRIX_SEED_DEMO=false`. Once a real editorial team is using the admin, set that to `false` in production to avoid stomping on their edits.

## Deployment notes

### Behind a reverse proxy

The web container listens on port 8000 (gunicorn) inside the container. For a real deployment:

1. Terminate TLS at the proxy (Caddy / nginx / Traefik / cloud LB).
2. Set `X-Forwarded-Proto: https` so `SECURE_PROXY_SSL_HEADER` in `settings.py` activates HSTS correctly.
3. Set `DJANGO_DEBUG=False` and `DJANGO_ALLOWED_HOSTS=your.domain` in the container env.
4. Set `DJANGO_CSRF_TRUSTED_ORIGINS=https://your.domain` (full origin, with scheme).
5. Provision a real `DJANGO_SECRET_KEY` and rotate periodically.
6. Set `SECTRIX_SEED_DEMO=false` so editors' admin work is never overwritten.

### Database backups

- `pg_dump` against the `sectrix-db` container is the cheap path:

  ```bash
  docker compose exec -T db pg_dump -U sectrix -d sectrix > backup-$(date +%Y%m%d).sql
  ```

- For real environments, use the managed DB's PITR. Don't rely on volume snapshots alone — they can drift from on-disk WAL state.

### Migrations in CI

Migrations run at container start via `entrypoint.sh`. For deployments where you want migrations to run as a separate step (zero-downtime):

```bash
# In CI, before promoting the new image:
docker run --rm --env-file .env <image> python manage.py migrate --noinput
docker run --rm --env-file .env <image> python manage.py collectstatic --noinput --clear
# Then rolling-update the web fleet.
```

You'll want `SECTRIX_SEED_DEMO=false` to skip the seed step in that flow.

## Troubleshooting

### Container won't start: "Missing staticfiles manifest entry"

You added a `{% static "foo.bar" %}` reference but `foo.bar` doesn't exist in `static/`. WhiteNoise's manifest storage refuses to start with broken references. Fix: either add the asset or remove the reference.

### Contact form rejects all emails as "Please use a work email"

`apps/contact/forms.py:ContactInquiryForm.clean_work_email` soft-blocks gmail / yahoo / hotmail / outlook. To allow them, edit or empty the `free_domains` set. To extend the blocklist, add to the same set.

### `python manage.py runserver` works but Docker container 502s

Almost always: `DJANGO_ALLOWED_HOSTS` or `DJANGO_CSRF_TRUSTED_ORIGINS` doesn't include the host you're hitting. Check `docker compose logs web` for the explicit error — Django logs allowed-hosts rejections clearly.

### Site looks unstyled in Docker but fine in `runserver`

Two causes:

1. WhiteNoise didn't pick up `staticfiles/`. Confirm `python manage.py collectstatic` ran (check `docker compose logs web` for `collecting static files…`).
2. The Tailwind CDN script is blocked by a network policy / CSP. Confirm browser devtools network panel; if CSP is in play, see [`security.md`](security.md) for the CSP-vs-CDN tradeoff.

### "Port 8000 is already allocated"

Some other process holds it. Either kill that or change the host-side port in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"   # ← change the left side
```

### Postgres healthcheck never goes healthy

Almost always a Docker volume permission issue from a previous run. `docker compose down -v` wipes the `pgdata` volume and lets a clean cluster initialize.
