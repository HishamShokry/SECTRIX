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

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/nginx-security-headers.conf"
DEST="${DEST:-/etc/nginx/conf.d/00-security.conf}"

log() { printf '\033[36m[nginx-config]\033[0m %s\n' "$*" >&2; }

[[ $EUID -eq 0 ]]     || { log "must run as root (writes to /etc/nginx)"; exit 1; }
[[ -f "$SRC" ]]       || { log "source not found: $SRC"; exit 1; }
command -v nginx >/dev/null || { log "nginx is not installed on this machine — are you on the right host?"; exit 1; }

# Keep a copy of whatever is there so a bad deploy is reversible.
if [[ -f "$DEST" ]]; then
  BACKUP="${DEST}.$(date +%Y%m%d%H%M%S).bak"
  cp -a "$DEST" "$BACKUP"
  log "existing config backed up to ${BACKUP}"
  if cmp -s "$SRC" "$DEST"; then
    log "already up to date; nothing to do"
    exit 0
  fi
fi

install -m 0644 -o root -g root "$SRC" "$DEST"
log "installed ${DEST}"

if ! nginx -t 2>&1 | sed 's/^/  /'; then
  log "nginx rejected the configuration — rolling back"
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
log "server header now: ${BANNER:-<no response on 127.0.0.1:80; check from outside>}"
log "done. Remember to add limit_req directives to the vhost's location blocks."
