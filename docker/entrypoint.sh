#!/usr/bin/env bash
# Sectrex container entrypoint.
# - waits for Postgres
# - applies migrations
# - seeds demo content (idempotent, controlled by env)
# - collects static assets
# - hands off to CMD (gunicorn)
set -euo pipefail

log() { printf '\033[36m[entrypoint]\033[0m %s\n' "$*" >&2; }

# ---- Wait for Postgres ---------------------------------------------------
if [[ "${DJANGO_DB_ENGINE:-sqlite}" == "postgres" ]]; then
  : "${POSTGRES_HOST:=db}"
  : "${POSTGRES_PORT:=5432}"
  log "waiting for postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}…"

  python <<'PY'
import os, socket, sys, time
host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"  postgres reachable at {host}:{port}")
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit(f"timeout waiting for postgres at {host}:{port}")
PY
fi

# ---- Migrate -------------------------------------------------------------
# Serialised with a Postgres advisory lock so overlapping container starts
# (rolling redeploy, restart loop) cannot race each other.
log "applying migrations…"
python manage.py safe_migrate

# ---- Seed (idempotent) ---------------------------------------------------
if [[ "${SECTRIX_SEED_DEMO:-true}" == "true" ]]; then
  log "seeding demo content…"
  python manage.py seed_demo
fi

# ---- Collect static ------------------------------------------------------
log "collecting static files…"
python manage.py collectstatic --noinput --clear >/dev/null
log "ready."

exec "$@"
