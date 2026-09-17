"""Deployment safety checks.

Run automatically by `manage.py check` (and therefore by `migrate`,
`runserver` and the container entrypoint), so a misconfigured production
deployment is visible rather than silently degraded.

By default these are **warnings**: they are printed but do not stop the site
coming up, because a configuration slip should not become an outage. Set
DJANGO_STRICT_DEPLOY_CHECKS=True to promote them to errors, which refuses the
boot — worth doing once the deployment is settled.

The message ids are stable regardless of level; only the severity changes.
"""
from django.conf import settings
from django.core.checks import Error, Warning, register

INSECURE_KEY_MARKERS = ("django-insecure-", "change-me", "dev-change-me")


def _level():
    """Error when strict mode is on, warning otherwise."""
    return Error if getattr(settings, "STRICT_DEPLOY_CHECKS", False) else Warning


@register()
def check_production_configuration(app_configs, **kwargs):
    """Refuse the configurations that silently leak data or weaken signing."""
    problems = []

    if settings.DEBUG:
        # Everything below only matters for a real deployment.
        return problems

    backend = getattr(settings, "EMAIL_BACKEND", "")
    if "console" in backend or "dummy" in backend:
        problems.append(
            _level()(
                "Email backend would write contact-form PII to the container log.",
                hint=(
                    "The console backend prints the full message -- name, work "
                    "email, phone and the free-text body -- to stdout, which "
                    "Docker persists to disk outside the database's access "
                    "controls. Set DJANGO_EMAIL_BACKEND to "
                    "django.core.mail.backends.smtp.EmailBackend."
                ),
                id="sectrex.E001",   # id is stable; severity follows STRICT_DEPLOY_CHECKS
            )
        )

    if any(marker in settings.SECRET_KEY for marker in INSECURE_KEY_MARKERS):
        problems.append(
            _level()(
                "SECRET_KEY is one of the placeholder values committed to the repository.",
                hint=(
                    "Generate one with: "
                    "python3 -c 'import secrets; print(secrets.token_urlsafe(64))' "
                    "and set DJANGO_SECRET_KEY."
                ),
                id="sectrex.E002",
            )
        )

    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
        problems.append(
            Warning(
                "ALLOWED_HOSTS still holds only local defaults.",
                hint="Set DJANGO_ALLOWED_HOSTS to the public hostname(s).",
                id="sectrex.W003",
            )
        )

    if not getattr(settings, "BEHIND_PROXY", False):
        problems.append(
            Warning(
                "DJANGO_BEHIND_PROXY is not set, so HTTPS cannot be detected "
                "and SECURE_SSL_REDIRECT stays off.",
                hint=(
                    "Set DJANGO_BEHIND_PROXY=True when nginx terminates TLS in "
                    "front of the app -- and make sure the app is not also "
                    "reachable directly, or the X-Forwarded-Proto header can "
                    "be forged."
                ),
                id="sectrex.W004",
            )
        )

    return problems
