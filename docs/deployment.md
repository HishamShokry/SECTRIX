# Deployment — production host

Target: a **fresh, dedicated** Ubuntu 24.04 server running the compose stack
(Django + Gunicorn + Postgres 16) directly on the host — no LXC, no nesting.

The stack idles at roughly 450–500 MB, so on a well-specced box RAM is not the
constraint. Size Gunicorn to the host rather than leaving the 1-core default:

| Component | Approx. RSS |
|---|---|
| Ubuntu base | ~100 MB |
| Docker daemon + containerd | ~80 MB |
| Postgres 16-alpine (low traffic) | ~40–60 MB |
| Gunicorn, per worker | ~70 MB |
| nginx | ~10 MB |

Set `GUNICORN_WORKERS` in `.env` to about `(2 × cores) + 1`. Past ~8 workers
this site gains nothing — it is a brochure site with a contact form, not a
compute workload.

> **`bootstrap.sh` assumes it owns the host.** It enables a default-deny
> firewall allowing only SSH/80/443, removes nginx's default site, and restarts
> the Docker daemon. On a host already running other services those steps are
> destructive, so the script runs a preflight check and refuses unless
> `FRESH_HOST_OVERRIDE=1` is set. Run the sections by hand there instead.

## 1. DNS

Point DNS at the server before running the bootstrap — certbot's HTTP-01
challenge needs the name to resolve.

```
A    sectrexconsulting.com       -> <server-ip>
A    www.sectrexconsulting.com   -> <server-ip>
```

## 2. Bootstrap the host

```bash
ssh root@<server-ip>
git clone <repo-url> /opt/sectrix
cd /opt/sectrix
DOMAIN=sectrexconsulting.com EMAIL=ops@sectrexconsulting.com ./deploy/bootstrap.sh
```

If Docker came from Ubuntu's `docker.io` package rather than Docker's own
repository, the Compose **v2 plugin** is missing and `docker compose` fails with
`unknown command`. The standalone `docker-compose` v1 cannot parse this file
(it uses `depends_on` health conditions and a top-level `volumes:` section):

```bash
sudo apt-get install -y docker-compose-v2
docker compose version
```

`deploy/bootstrap.sh` is idempotent and does: fresh-host preflight, a swapfile
only on small hosts (skipped at >= 4 GB RAM), Docker engine + compose plugin,
ufw (SSH + nginx only), container log rotation capped at 30 MB, the nginx site
from `deploy/nginx.conf`, and certbot with auto-renewal.

## 3. Environment

```bash
cp deploy/production.env.example /opt/sectrix/.env
python3 -c "import secrets; print(secrets.token_urlsafe(64))"   # DJANGO_SECRET_KEY
nano /opt/sectrix/.env
```

`DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` must both list the
real domain or Django rejects requests behind the proxy.

## 4. Launch

```bash
cd /opt/sectrix
docker compose up -d --build
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
```

The entrypoint migrates, seeds demo content (while `SECTRIX_SEED_DEMO=true`),
and runs collectstatic before handing off to Gunicorn.

## nginx hardening on a certbot-managed host

When certbot writes its own vhost (the usual case), this repo's
`deploy/nginx.conf` is not what is serving. Install the host-wide drop-in so
the hardening applies to every vhost and to nginx's own error pages:

Keep a checkout on the nginx host, separate from the application's, and pull:

```bash
# once
git clone https://github.com/HishamShokry/SECTRIX.git /opt/sectrix-deploy

# now, and after any future change to the nginx config
cd /opt/sectrix-deploy && git pull
sudo ./deploy/install-nginx-config.sh
```

The installer backs up whatever it replaces, runs `nginx -t`, and **rolls back
automatically** if the new config is rejected, so a bad change cannot take the
site down.

It sets `server_tokens off` (the default banner advertises the exact build and
distribution, e.g. `nginx/1.24.0 (Ubuntu)`, which is a free version-to-CVE
lookup), adds CSP and `Permissions-Policy`, and declares the rate-limit zones.

The zones do nothing until a vhost references them. Pass `--with-ratelimit`
to apply them to the certbot-managed vhost as well:

```bash
sudo ./deploy/install-nginx-config.sh --with-ratelimit \
  /etc/nginx/sites-enabled/sectrexconsulting.com
```

That adds `location /contact/` (5r/m) and `location /admin/` (20r/m) blocks and
a general ceiling on `location /`. It copies the proxy directives out of the
existing `location /`, so the upstream is whatever the file already uses rather
than a hardcoded address, and it leaves every certbot-managed line untouched.
Re-running is a no-op.

Verify: `curl -sSI https://your-domain/ | grep -i server` should read
`Server: nginx` with no version. To remove the header entirely, install
`nginx-extras` and add `more_clear_headers Server;`.

## Security configuration

`apps/core/checks.py` runs on every `manage.py` invocation (including the
container entrypoint's `safe_migrate`) and reports configurations that would
leak data or sign with a placeholder key.

By default these are **warnings** — printed on every start, but the site still
comes up, so a configuration slip does not become an outage. Set
`DJANGO_STRICT_DEPLOY_CHECKS=True` to promote them to errors that block the
boot; worth doing once the deployment has settled.

| Check | Fails when |
|---|---|
| `sectrex.E001` | `DJANGO_EMAIL_BACKEND` is the console backend, which prints full inquiry PII to the container log |
| `sectrex.E002` | `DJANGO_SECRET_KEY` is one of the placeholders committed to this repo |
| `sectrex.W003` | `DJANGO_ALLOWED_HOSTS` still holds only local defaults |
| `sectrex.W004` | `DJANGO_BEHIND_PROXY` is unset, so HTTPS cannot be detected |

Set `DJANGO_BEHIND_PROXY=True` whenever nginx terminates TLS in front of the
app. It enables `SECURE_PROXY_SSL_HEADER` and `SECURE_SSL_REDIRECT` — but only
set it if the app is **not** also reachable directly, or a client can forge
`X-Forwarded-Proto`. `docker-compose.yml` publishes the app on `127.0.0.1:8001`
for exactly that reason.

### Scheduled maintenance

Contact inquiries do not expire on their own. Schedule the purge:

```bash
# /etc/cron.d/sectrix-retention
0 3 * * * root cd /opt/sectrix && docker compose exec -T web python manage.py purge_inquiries
```

Check what it would remove first with `purge_inquiries --dry-run`.

## Demo-content mode

The site currently ships placeholder marketing copy. Two guards are wired to
`DJANGO_ALLOW_INDEXING` (default **False**):

- `robots.txt` serves `Disallow: /` for all agents
- every page carries `<meta name="robots" content="noindex, nofollow">`

Set `DJANGO_ALLOW_INDEXING=True` and restart once real content is live. Leaving
it False keeps placeholder copy out of search indexes and crawler caches, which
matters because indexed pages can persist long after they are edited.

## Going to real content

1. `SECTRIX_SEED_DEMO=false` — otherwise `docker/entrypoint.sh` re-runs
   `seed_demo` on every start and `update_or_create` reverts admin edits.
2. Purge demo rows, then enter real case studies and jobs in `/admin/`.
3. Replace the copy in `apps/core/content.py` (services, home, about, careers
   sections render from that module, not the DB) and redeploy.
4. `DJANGO_ALLOW_INDEXING=True`.

## Contact form email

`DJANGO_EMAIL_BACKEND` defaults to the console backend, which means inquiries
are saved to the database but **no notification is sent**. Point it at
`django.core.mail.backends.smtp.EmailBackend` with real SMTP credentials before
relying on the form. Note DigitalOcean blocks outbound port 25 — use a relay on
587 (SES, Postmark, Mailgun, Google Workspace).

## Operations

```bash
docker compose ps                  # status
docker compose logs -f web         # tail app logs
docker compose up -d --build       # redeploy after a git pull
docker compose restart web         # restart app only
free -h                            # memory headroom
```

### Backups

```bash
# Database
docker compose exec -T db pg_dump -U sectrix sectrix | gzip > sectrix-$(date +%F).sql.gz

# Uploaded media (CaseStudy.cover_image)
docker run --rm -v sectrix_media:/m -v "$PWD":/backup alpine \
  tar czf /backup/media-$(date +%F).tar.gz -C /m .
```

Keep these off the droplet. Contact inquiries contain personal data — never
commit a dump to git.

## Notes

- Docker publishes ports via iptables rules that bypass ufw. `docker-compose.yml`
  binds Postgres to `127.0.0.1:5433` so it is loopback-only, but the web
  container's port 8001 is reachable externally. nginx is the intended entry
  point on 80/443; block 8001 at the provider's network firewall to close it,
  or bind the mapping to `127.0.0.1:8001` in `docker-compose.yml`.
- Check that outbound port 587 is open before relying on the contact form.
  Hosting providers commonly restrict SMTP on new accounts, and the form fails
  silently while `DJANGO_EMAIL_BACKEND` is the console backend.
- `SECURE_SSL_REDIRECT` is not set in `settings.py`; certbot's `--redirect`
  installs the 301 at the nginx layer instead. `manage.py check --deploy`
  reports W008 for this — expected.
- HSTS is enabled with `preload` and a 30-day max-age when `DEBUG=False`
  (`settings.py`). Confirm the domain is final before traffic arrives; browsers
  cache that policy.
