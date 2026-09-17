# Security Model

This document inventories what the runtime defends against, what it explicitly *doesn't* yet, and where to extend each control. Treat it as the source of truth for a security review.

## What is enforced

### 1. CSRF

Django's `CsrfViewMiddleware` is enabled. Every POST endpoint requires a valid `csrfmiddlewaretoken`. The contact form template includes `{% csrf_token %}`; the admin login does the same. CSRF cookies are `Secure` in production (`CSRF_COOKIE_SECURE = True`).

`DJANGO_CSRF_TRUSTED_ORIGINS` controls which full origins are accepted as form sources. **Set this to your exact production origin** (including scheme) — wildcard subdomains require the `https://*.example.com` form.

### 2. Click-jacking

`XFrameOptionsMiddleware` is enabled. Production sets `X_FRAME_OPTIONS = "DENY"`; dev defaults to `SAMEORIGIN`. The admin and all public pages refuse to be embedded.

### 3. HSTS, TLS, secure cookies (production only)

When `DJANGO_DEBUG=False`, `settings.py` activates:

| Setting | Value | Effect |
|---|---|---|
| `SECURE_HSTS_SECONDS` | 30 days | `Strict-Transport-Security` header |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` | True | Covers subdomains under the same HSTS policy |
| `SECURE_HSTS_PRELOAD` | True | Signals readiness for the browser HSTS preload list |
| `SECURE_PROXY_SSL_HEADER` | `("HTTP_X_FORWARDED_PROTO", "https")` | Trusts proxy-set scheme; **only safe behind a real proxy that strips this header from clients** |
| `SECURE_CONTENT_TYPE_NOSNIFF` | True | `X-Content-Type-Options: nosniff` |
| `SECURE_REFERRER_POLICY` | `strict-origin-when-cross-origin` | Conservative referrer leakage |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | True | Cookies only over TLS |

Before going to prod: set `DJANGO_DEBUG=False`, then verify with `curl -I https://yourdomain.com/` that HSTS and the other headers appear.

### 4. Contact form: honeypot + free-email block + IP hash

`apps/contact/forms.py:ContactInquiryForm`:

- **Honeypot field** `website` is a hidden input. Real browsers don't fill it; most spam bots do. `clean_website` rejects any non-empty value with a `ValidationError`. Bots see a normal-looking success path on validation failure (no special treatment) — they don't learn the field is a trap.
- **Free-email soft-block** rejects gmail, yahoo, hotmail, outlook addresses with a friendly error. This is a quality filter for enterprise inquiries, not a security control. Edit the `free_domains` set to expand or remove.
- **IP hashing** — `apps/contact/views.py:form_valid` stores a **keyed** hash (`salted_hmac`, keyed on `SECRET_KEY`) of the client address, never the address itself. The key matters: a bare SHA-256 of an IPv4 address is reversible by exhausting the 2^32 address space, so an unkeyed digest pseudonymises nothing. The address is read from `X-Forwarded-For` when `DJANGO_BEHIND_PROXY=True` (nginx overwrites that header) and from `REMOTE_ADDR` otherwise — reading `REMOTE_ADDR` behind a proxy would give every visitor the proxy's address and collapse every row to one value.
  The result is still **linkable** to a person, so it remains personal data under GDPR and is covered by the same retention rules as the rest of the row.
- **User-agent truncation** — saved at 400 chars max, to bound storage and resist log-injection-via-UA.

### 5. Manifest-storage static assets

`STORAGES["staticfiles"]` is `whitenoise.storage.CompressedManifestStaticFilesStorage`. This:

- Hashes every static filename (`favicon.svg` → `favicon.9f37729e8bce.svg`).
- Serves them with `Cache-Control: max-age=31536000, immutable`.
- **Fails the build if any `{% static %}` reference points to a missing file**, so a broken asset reference is caught at deploy time, not in production.

### 6. Non-root container runtime

The `sectrix-web` container drops to a non-root user (`uid 1000`, name `sectrix`) before exec'ing the entrypoint. The Postgres container uses the upstream image's default `postgres` user. Neither runs as root once initialized.

### 7. Postgres on host loopback only

`docker-compose.yml` binds Postgres to `127.0.0.1:5433` — not `0.0.0.0`. The DB is reachable from the host (for `psql` debugging) but not from any other machine on the LAN. The web container reaches the DB via Docker's internal network — never via the host loopback mapping.

### 8. Admin authentication

`/admin/` requires session-based auth against `auth_user`. Password validators enforce:

- Minimum length (8)
- Not similar to user attributes
- Not in the common-passwords list
- Not numeric-only

Failed login attempts are logged by Django but **not rate-limited** — see gaps below.

### 9. CSRF + Auth + Session ordering

Middleware order in `settings.MIDDLEWARE`:

```
SecurityMiddleware              ← first; sets security headers
WhiteNoiseMiddleware            ← serves static before any DB hit
SessionMiddleware
CommonMiddleware
CsrfViewMiddleware              ← rejects forged POSTs before they reach views
AuthenticationMiddleware
MessagesMiddleware
XFrameOptionsMiddleware
```

This is the recommended order. CSRF runs **before** Auth so an attacker can't trigger an authenticated action through a forged form even if a session cookie is present.

## What is NOT enforced (intentional gaps)

These are honest gaps to be aware of. Each is solvable; none are blocking for an enterprise marketing site, but all should be revisited before exposing the admin to a hostile public internet.

### No Content-Security-Policy

A strict CSP is the single biggest defense-in-depth improvement available. The complication: the site currently loads Tailwind from `cdn.tailwindcss.com` and fonts from Google. A strict CSP would block them.

The right path is **swap Tailwind to a real build pipeline first** (see [`frontend.md`](frontend.md#switching-to-a-real-tailwind-build)), then add `django-csp` with:

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:")
CSP_FRAME_SRC = ("openstreetmap.org", "www.openstreetmap.org")  # contact map
CSP_SCRIPT_SRC = ("'self'",)  # Alpine self-hosted; remove cdn.jsdelivr.net dependency
```

Until then, the absence of CSP means an XSS bug anywhere on the site has wider reach than it should. Django's template auto-escaping is the primary mitigation — see "XSS posture" below.

### No rate limiting

Three places are anonymously POSTable / GETable and unrated:

1. **Contact form** — abusable for inbox flooding and DB row exhaustion. Mitigate with `django-ratelimit` (one decorator) or Cloudflare Turnstile.
2. **Admin login** — credential-stuffing target. Mitigate with `django-axes` (account-lockout-after-N-failures) or `django-ratelimit` on `/admin/login/`.
3. **Sitemap and robots.txt** — non-issue at current scale, but worth caching in a reverse proxy.

### No 2FA on admin

`django-otp` + `django-two-factor-auth` is the standard Django stack. Add before the admin is reachable on the public internet. Sectrex's threat model — Gulf banks and sovereign agencies as clients — makes a compromised admin a credible threat vector.

### Contact-form email sent synchronously

`apps/contact/views.py:form_valid` calls `send_mail(..., fail_silently=True)` inline. If the SMTP backend is slow, the user waits. If it's down, the failure is silent (intentional: we don't want to surface "your inquiry was saved but the team wasn't notified" to a submitter). Move to a background queue (Celery, RQ, or even Django-Q2) when a real outbound path is wired up.

### No file upload surface

Currently the only `ImageField` is `CaseStudy.cover_image`, and it's only written via `/admin/` (authenticated). Image uploads via Django admin go through Pillow's loader — vulnerable to image-parser bugs in Pillow itself, so **keep Pillow patched**. No public image upload exists.

### No SQL written by hand

All DB access is through the ORM. There is no raw SQL, no `format`-built queries, no untrusted query parameters. SQL injection is mitigated at the architectural layer, not at the code-review layer.

## XSS posture

The site has three patterns that touch HTML:

1. **Default**: `{{ var }}` — Django auto-escapes. Safe.
2. **`|safe` on icon strings** in `home.html`, `about.html`, `services/list.html`. The values are hard-coded SVG strings in `apps/core/content.py`, not user input. **Never** apply `|safe` to anything sourced from `request.POST`, the DB, or any external feed.
3. **Inline JSON-LD** in `partials/head_meta.html` — populated from `settings.SITE_META`, which is set from environment variables. The values go into a `<script type="application/ld+json">` block, which is **not** parsed as executable JS — but it *is* parsed as JSON, so a `</script>` substring in any of those values would still break out. Keep `SITE_META` values free of `<` characters.

## Secret management

- `DJANGO_SECRET_KEY` is read from env; never committed.
- `.env` is git-ignored; `.env.example` is the committed template.
- The Docker Compose default secret key (`dev-change-me-for-prod-please-make-this-long-and-random`) is explicitly marked as a dev fallback. **Do not deploy with that string.**
- Postgres password in `docker-compose.yml` defaults to `sectrix_dev_password` — fine for laptop dev, **must** be overridden via env in any environment reachable from outside the host.

## Audit / log surface

| Event | Where it lands |
|---|---|
| HTTP requests | gunicorn access log (stdout, picked up by `docker compose logs`) |
| Failed admin logins | Django's `django.security` logger (stderr) |
| Exceptions | gunicorn error log (stderr) — set up Sentry or equivalent in prod |
| Contact submissions | `ContactInquiry` table (admin-visible); also emailed to `CONTACT_INBOX` |

There is no separate audit table for admin actions. If you need one, enable `django-simple-history` on the editorial models — it adds an automatic per-revision history table with the actor and timestamp.

## Responsible disclosure

The footer links to a `/responsible-disclosure` page; that URL is a placeholder and not implemented. For a real launch, either ship a `security.txt` at `/.well-known/security.txt` or stand up a real disclosure page. The `disclose@sectrexconsulting.com` mailbox referenced there does not yet exist — make sure it does before publishing the link.
