"""Django settings for Sectrex corporate website."""
from pathlib import Path
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in {"1", "true", "yes", "on"}


# --- Core ----------------------------------------------------------------

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    "django-insecure-change-me-in-production-replace-with-a-real-secret",
)
# Fail closed: an unset DJANGO_DEBUG must not hand a production host the
# debugger and disable the hardening below.
DEBUG = env_bool("DJANGO_DEBUG", False)
TESTING = "test" in sys.argv
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]


# --- Applications --------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "axes",   # login throttling / lockout for the admin
]

LOCAL_APPS = [
    "apps.core",
    "apps.services",
    "apps.case_studies",
    "apps.careers",
    "apps.contact",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise must come immediately after SecurityMiddleware so it can
    # serve static assets in production without a separate web server.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Must come last: it records the result of the auth attempt.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "sectrix.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

WSGI_APPLICATION = "sectrix.wsgi.application"
ASGI_APPLICATION = "sectrix.asgi.application"


# --- Database ------------------------------------------------------------
# PostgreSQL-ready. Defaults to SQLite for local dev so the project runs
# out of the box; flip DJANGO_DB_ENGINE=postgres + supply DATABASE_URL parts
# in production.

if env("DJANGO_DB_ENGINE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", "sectrix"),
            "USER": env("POSTGRES_USER", "sectrix"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "localhost"),
            "PORT": env("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Auth / passwords ----------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # 8 (Django's default) is too short for the only credential guarding
        # the admin, which is reachable from the public internet.
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Brute-force protection for the admin login. AxesStandaloneBackend must
# precede ModelBackend so lockouts are evaluated before credentials.
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AXES_ENABLED = env_bool("DJANGO_AXES_ENABLED", True) and not TESTING
AXES_FAILURE_LIMIT = int(env("DJANGO_AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = int(env("DJANGO_AXES_COOLOFF_HOURS", "1"))
AXES_LOCKOUT_PARAMETERS = ["ip_address", "username"]
AXES_RESET_ON_SUCCESS = True
# Behind a proxy the client address arrives in X-Forwarded-For; nginx
# overwrites that header, so the leftmost entry is trustworthy here.
AXES_IPWARE_PROXY_COUNT = 1 if env_bool("DJANGO_BEHIND_PROXY", False) else None


# --- I18n / TZ -----------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", "Asia/Dubai")
USE_I18N = True
USE_TZ = True


# --- Static / Media ------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise compresses + hashes assets for far-future caching in production.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --- Email (contact form) ------------------------------------------------

EMAIL_BACKEND = env("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "noreply@sectrexconsulting.com")
CONTACT_INBOX = env("CONTACT_INBOX", "contact@sectrexconsulting.com")

# Retention window for contact inquiries, enforced by the purge_inquiries
# management command. Nothing expires without that command being scheduled.
INQUIRY_RETENTION_DAYS = int(env("DJANGO_INQUIRY_RETENTION_DAYS", "730"))


# --- Security ------------------------------------------------------------
# These apply in every environment. Gating them on DEBUG meant a single
# missing environment variable silently disabled all of them at once.

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
# The admin is the only session surface; a fortnight-long cookie is far
# longer than an editing session needs.
SESSION_COOKIE_AGE = int(env("DJANGO_SESSION_COOKIE_AGE", str(60 * 60 * 12)))
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Trusting X-Forwarded-Proto is only safe when a proxy we control overwrites
# it. Set DJANGO_BEHIND_PROXY=True only when nginx (or equivalent) fronts the
# app; if the app is also reachable directly, a client can forge the header.
BEHIND_PROXY = env_bool("DJANGO_BEHIND_PROXY", False)
if BEHIND_PROXY:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Transport security (HTTPS deployments) ------------------------------

if not DEBUG:
    # Defaults to BEHIND_PROXY: redirecting without a way to detect the
    # original scheme would loop forever behind a TLS-terminating proxy.
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", BEHIND_PROXY)
    # One year — the minimum the HSTS preload list accepts. Ramp this up on a
    # new domain (start at 300) and only then submit for preloading.
    SECURE_HSTS_SECONDS = int(env("DJANGO_HSTS_SECONDS", str(60 * 60 * 24 * 365)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Pillow will happily decode a small file that expands to gigabytes of
# pixels. 40MP is far above any legitimate cover image.
try:
    from PIL import Image as _PILImage

    _PILImage.MAX_IMAGE_PIXELS = 40_000_000
except ImportError:  # pragma: no cover - Pillow is a hard dependency in prod
    pass


# --- Request size limits -------------------------------------------------
# Django's defaults are sane; pinning them documents the intent and keeps the
# form body well under the 12M nginx allows for admin image uploads.
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024        # 2 MB form body
FILE_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024        # spool to disk beyond this
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200
DATA_UPLOAD_MAX_NUMBER_FILES = 10


# --- Logging -------------------------------------------------------------
# Without this, Django routes errors to AdminEmailHandler with an empty
# ADMINS list, i.e. nowhere, and nothing else is recorded at all.

LOG_LEVEL = env("DJANGO_LOG_LEVEL", "INFO").upper()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "axes": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

ADMINS = [
    tuple(a.split(":", 1))
    for a in env("DJANGO_ADMINS", "").split(",")
    if ":" in a
]
SERVER_EMAIL = env("DJANGO_SERVER_EMAIL", DEFAULT_FROM_EMAIL)


# --- Misc ----------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Search-engine indexing. Keep this False while the site is serving demo
# content so placeholder copy is not indexed or cached by crawlers.
ALLOW_INDEXING = env_bool("DJANGO_ALLOW_INDEXING", False)

SITE_META = {
    "name": "Sectrex Consulting",
    "tagline": "Enterprise Cybersecurity for the Modern Threat Landscape",
    "description": (
        "Sectrex delivers enterprise-grade cybersecurity for banks, governments, "
        "and large organizations across the Gulf — threat detection, cloud "
        "security, incident response, and zero trust architecture."
    ),
    "keywords": "cybersecurity, threat detection, zero trust, incident response, cloud security, Gulf, enterprise",
    "url": env("SITE_URL", "https://sectrexconsulting.com"),
    "twitter": "@sectrex",
    "email": "contact@sectrexconsulting.com",
    "phone": "+971 4 000 0000",
    "address": "Dubai Internet City · Dubai · United Arab Emirates",
}
