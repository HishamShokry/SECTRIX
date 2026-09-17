"""Django settings for Sectrix corporate website."""
from pathlib import Path
import os

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
DEBUG = env_bool("DJANGO_DEBUG", True)
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

LOCAL_APPS = [
    "apps.core",
    "apps.services",
    "apps.case_studies",
    "apps.careers",
    "apps.contact",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

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
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


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
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "noreply@sectrix.com")
CONTACT_INBOX = env("CONTACT_INBOX", "contact@sectrix.com")


# --- Security (production toggles) ---------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = "DENY"


# --- Misc ----------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Search-engine indexing. Keep this False while the site is serving demo
# content so placeholder copy is not indexed or cached by crawlers.
ALLOW_INDEXING = env_bool("DJANGO_ALLOW_INDEXING", False)

SITE_META = {
    "name": "Sectrix",
    "tagline": "Enterprise Cybersecurity for the Modern Threat Landscape",
    "description": (
        "Sectrix delivers enterprise-grade cybersecurity for banks, governments, "
        "and large organizations across the Gulf — threat detection, cloud "
        "security, incident response, and zero trust architecture."
    ),
    "keywords": "cybersecurity, threat detection, zero trust, incident response, cloud security, Gulf, enterprise",
    "url": env("SITE_URL", "https://sectrix.com"),
    "twitter": "@sectrix",
    "email": "contact@sectrix.com",
    "phone": "+971 4 000 0000",
    "address": "Dubai Internet City · Dubai · United Arab Emirates",
}
