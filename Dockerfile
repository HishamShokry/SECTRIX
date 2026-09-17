# syntax=docker/dockerfile:1.7

# ---- CSS build -----------------------------------------------------------
# Tailwind is compiled here rather than loaded from the Play CDN, which is a
# development tool: it ships a compiler to every visitor and leaves the site
# unstyled whenever the CDN is unreachable.
FROM node:22-alpine AS css

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Only what Tailwind scans for class names, so edits elsewhere reuse the layer.
COPY tailwind.config.js ./
COPY static/src ./static/src
COPY templates ./templates
COPY apps ./apps

RUN npx tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --minify


# ---- Base ----------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=sectrix.settings

# psycopg (binary) + Pillow need a few system libs; curl is for the healthcheck.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
        curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache deps layer separately from app code.
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Freshly compiled CSS overwrites whatever the repo carried for local dev.
COPY --from=css /build/static/css/tailwind.css /app/static/css/tailwind.css

# Non-root runtime user with write access to runtime dirs.
RUN useradd --create-home --shell /usr/sbin/nologin --uid 1000 sectrix \
 && mkdir -p /app/staticfiles /app/media \
 && chown -R sectrix:sectrix /app

USER sectrix

EXPOSE 8000

ENTRYPOINT ["./docker/entrypoint.sh"]
CMD ["gunicorn", "sectrix.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--threads", "2", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
