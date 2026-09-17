#!/usr/bin/env bash
# Install the host-wide nginx hardening drop-in.
#
# Run on the machine that runs nginx. In a split deployment that is the LXC/VM
# *host*, not the guest running the app — so this repo needs a checkout there
# too, separate from the application's:
#
#   git clone https://github.com/HishamShokry/SECTRIX.git /opt/sectrix-deploy
#   cd /opt/sectrix-deploy && sudo ./deploy/install-nginx-config.sh
#
# To update later:
#
#   cd /opt/sectrix-deploy && git pull && sudo ./deploy/install-nginx-config.sh
#
# Idempotent. Backs up anything it replaces and rolls back if nginx rejects the
# result, so a bad config cannot take the site down.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${HERE}/nginx-security-headers.conf"
DEST="${DEST:-/etc/nginx/conf.d/00-security.conf}"

# Optional: also add limit_req directives to a vhost this repo does not own
# (certbot writes its own). The zones installed above do nothing until a
# vhost references them.
#   ./deploy/install-nginx-config.sh --with-ratelimit /etc/nginx/sites-enabled/example.com
VHOST=""
HIDE_SERVER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-ratelimit)
      VHOST="${2:?usage: --with-ratelimit /etc/nginx/sites-enabled/<vhost>}"
      [[ -f "$VHOST" ]] || { echo "vhost not found: $VHOST" >&2; exit 1; }
      shift 2 ;;
    --hide-server)
      # Removes the Server header outright rather than just its version.
      HIDE_SERVER=1
      shift ;;
    *)
      echo "unknown option: $1" >&2
      echo "usage: $0 [--with-ratelimit <vhost>] [--hide-server]" >&2
      exit 1 ;;
  esac
done
HIDE_SRC="${HERE}/nginx-hide-server.conf"
HIDE_DEST="/etc/nginx/conf.d/01-hide-server.conf"

log() { printf '\033[36m[nginx-config]\033[0m %s\n' "$*" >&2; }

[[ $EUID -eq 0 ]]     || { log "must run as root (writes to /etc/nginx)"; exit 1; }
[[ -f "$SRC" ]]       || { log "source not found: $SRC"; exit 1; }
command -v nginx >/dev/null || { log "nginx is not installed on this machine — are you on the right host?"; exit 1; }

# Keep a copy of whatever is there so a bad deploy is reversible.
if [[ -f "$DEST" ]]; then
  BACKUP="${DEST}.$(date +%Y%m%d%H%M%S).bak"
  cp -a "$DEST" "$BACKUP"
  log "existing config backed up to ${BACKUP}"
  if cmp -s "$SRC" "$DEST" && [[ -z "$VHOST" ]]; then
    log "already up to date; nothing to do"
    exit 0
  fi
fi

install -m 0644 -o root -g root "$SRC" "$DEST"
log "installed ${DEST}"

# Remove the Server header outright, if asked. `more_clear_headers` comes from
# a module that is not installed by default, and referencing it without the
# module stops nginx from starting -- so install the module first and only add
# the snippet once it is actually present.
if [[ "$HIDE_SERVER" == "1" ]]; then
  if ! ls /etc/nginx/modules-enabled/*headers-more* >/dev/null 2>&1; then
    log "installing libnginx-mod-http-headers-more-filter…"
    if ! DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
         libnginx-mod-http-headers-more-filter >/dev/null 2>&1; then
      log "could not install the headers-more module; leaving the Server header as 'nginx'"
      HIDE_SERVER=0
    fi
  fi
  if [[ "$HIDE_SERVER" == "1" ]]; then
    install -m 0644 -o root -g root "$HIDE_SRC" "$HIDE_DEST"
    log "installed ${HIDE_DEST}"
  fi
fi

# Patch the vhost too, if asked. Backed up separately so rollback restores both.
if [[ -n "$VHOST" ]]; then
  VHOST_BACKUP="${VHOST}.$(date +%Y%m%d%H%M%S).bak"
  cp -a "$VHOST" "$VHOST_BACKUP"
  log "vhost backed up to ${VHOST_BACKUP}"
  python3 "${HERE}/add-vhost-ratelimit.py" "$VHOST" | sed 's/^/  /'
fi

if ! nginx -t 2>&1 | sed 's/^/  /'; then
  log "nginx rejected the configuration — rolling back"
  if [[ -n "${VHOST_BACKUP:-}" && -f "${VHOST_BACKUP}" ]]; then
    cp -a "$VHOST_BACKUP" "$VHOST"
    log "restored ${VHOST}"
  fi
  [[ "$HIDE_SERVER" == "1" ]] && rm -f "$HIDE_DEST"
  if [[ -n "${BACKUP:-}" && -f "${BACKUP}" ]]; then
    cp -a "$BACKUP" "$DEST"
  else
    rm -f "$DEST"
  fi
  nginx -t >/dev/null 2>&1 && log "rollback verified" || log "WARNING: nginx config still invalid after rollback"
  exit 1
fi

systemctl reload nginx
log "nginx reloaded"

# Report what the banner now says, which is the point of the exercise.
# Reload is asynchronous -- old workers finish in-flight requests -- so give
# them a moment or this reports the pre-reload value.
sleep 2
BANNER="$(curl -sSI --max-time 5 http://127.0.0.1/ 2>/dev/null | grep -i '^server:' || true)"
log "server header now: ${BANNER:-<none — Server header removed>}"
if [[ -n "$VHOST" ]]; then
  log "done. Rate limiting is active on /contact/ (5r/m) and /admin/ (20r/m)."
else
  log "done. Zones are declared but unused — re-run with --with-ratelimit <vhost> to apply them."
fi
