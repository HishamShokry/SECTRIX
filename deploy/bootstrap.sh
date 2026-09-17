#!/usr/bin/env bash
# Sectrex — one-shot host bootstrap (Ubuntu 24.04, bare metal or VPS).
#
# Prepares a FRESH, DEDICATED host to run the docker-compose stack:
#   swap -> docker -> firewall -> nginx -> certbot
#
# Usage (as root on the target host):
#   DOMAIN=sectrexconsulting.com EMAIL=ops@sectrexconsulting.com ./deploy/bootstrap.sh
#
# Idempotent: safe to re-run.
#
# NOT for a host that already runs other services. It enables a default-deny
# firewall allowing only SSH/80/443, removes nginx's default site, and restarts
# the Docker daemon. On a shared host, run the sections by hand instead.
#
# Does not work inside an LXC/OpenVZ container: swap is host-controlled there.
# The swap step self-skips, but review the firewall step before running.
set -euo pipefail

DOMAIN="${DOMAIN:?set DOMAIN=yourdomain.com}"
EMAIL="${EMAIL:?set EMAIL=you@yourdomain.com for certbot expiry notices}"
APP_DIR="${APP_DIR:-/opt/sectrix}"

log() { printf '\033[36m[bootstrap]\033[0m %s\n' "$*" >&2; }

# ---- 0. Fresh-host preflight --------------------------------------------
# This script assumes it owns the firewall, nginx and the Docker daemon.
# Bail out if something else is already using them. FRESH_HOST_OVERRIDE=1 skips.
if [[ "${FRESH_HOST_OVERRIDE:-0}" != "1" ]]; then
  problems=()

  # Other nginx vhosts would be affected by the default-site removal below.
  if [[ -d /etc/nginx/sites-enabled ]]; then
    others="$(find /etc/nginx/sites-enabled -type l -o -type f 2>/dev/null \
              | grep -vE '/(default|sectrix)$' | wc -l)"
    [[ "$others" -gt 0 ]] && problems+=("nginx already serves ${others} other site(s)")
  fi

  # Enabling ufw with only 22/80/443 open would cut off anything else.
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q '^Status: active'; then
    problems+=("ufw is already active — review its rules before this script rewrites them")
  fi

  # Restarting dockerd for daemon.json would bounce existing containers.
  if command -v docker >/dev/null 2>&1; then
    running="$(docker ps -q 2>/dev/null | wc -l)"
    [[ "$running" -gt 0 ]] && problems+=("${running} container(s) already running — dockerd restart would bounce them")
  fi

  # docker-compose.yml publishes the app on host port 8001.
  if ss -ltn 2>/dev/null | grep -q ':8001 '; then
    problems+=("host port 8001 is already in use — change the port mapping in docker-compose.yml")
  fi

  if (( ${#problems[@]} > 0 )); then
    log "this host does not look fresh:"
    for p in "${problems[@]}"; do log "  - $p"; done
    log ""
    log "Run the sections by hand, or re-run with FRESH_HOST_OVERRIDE=1 if you"
    log "are certain the changes above are safe here."
    exit 1
  fi
  log "preflight passed — host looks fresh"
fi

# ---- 1. Swap -------------------------------------------------------------
# Only worth adding on small hosts. The stack needs ~500 MB; with several GB of
# RAM a swapfile buys nothing, so skip it above the threshold.
# Set SWAP_FORCE=1 to create one regardless.
RAM_MB="$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)"
SWAP_THRESHOLD_MB="${SWAP_THRESHOLD_MB:-4096}"

if [[ -r /proc/1/environ ]] && grep -qa 'container=' /proc/1/environ 2>/dev/null; then
  log "running inside a container — swap is host-controlled, skipping"
elif swapon --show --noheadings 2>/dev/null | grep -q .; then
  log "swap already active, skipping"
elif [[ "${SWAP_FORCE:-0}" != "1" && "${RAM_MB}" -ge "${SWAP_THRESHOLD_MB}" ]]; then
  log "${RAM_MB} MB RAM — ample, skipping swapfile (SWAP_FORCE=1 to override)"
else
  log "creating 1G swapfile (${RAM_MB} MB RAM)…"
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  # Low swappiness: use swap as a safety net, not routinely.
  sysctl -w vm.swappiness=10
  grep -q 'vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# ---- 2. Base packages ----------------------------------------------------
log "installing base packages…"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git ufw nginx

# ---- 3. Docker -----------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  log "installing docker engine + compose plugin…"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
else
  log "docker already installed, skipping engine install"
fi

# Compose v2 is a separate plugin, and Ubuntu's docker.io package does not
# ship it — so check for it independently of the engine. The retired
# standalone docker-compose v1 cannot parse this project's compose file.
if ! docker compose version >/dev/null 2>&1; then
  log "installing compose v2 plugin…"
  apt-get install -y -qq docker-compose-plugin \
    || apt-get install -y -qq docker-compose-v2
  docker compose version >/dev/null 2>&1 \
    || { log "compose v2 still unavailable — install it manually"; exit 1; }
else
  log "compose v2 present, skipping"
fi

# ---- 4. Firewall ---------------------------------------------------------
# Note: docker publishes ports by writing iptables rules that bypass ufw.
# docker-compose.yml binds Postgres to 127.0.0.1 only, and the web container
# to 8001 — reachable externally unless blocked. nginx fronts it on 80/443.
log "configuring ufw…"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# ---- 5. Log rotation for containers -------------------------------------
# Default json-file driver grows without bound; 1 GB disk pressure is real.
if [[ ! -f /etc/docker/daemon.json ]]; then
  log "capping container log size…"
  mkdir -p /etc/docker
  cat > /etc/docker/daemon.json <<'JSON'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
JSON
  systemctl restart docker
fi

# ---- 6. nginx site -------------------------------------------------------
log "installing nginx site for ${DOMAIN}…"
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "${APP_DIR}/deploy/nginx.conf" \
  > /etc/nginx/sites-available/sectrix
ln -sf /etc/nginx/sites-available/sectrix /etc/nginx/sites-enabled/sectrix
rm -f /etc/nginx/sites-enabled/default
mkdir -p /var/www/certbot
nginx -t && systemctl reload nginx

# ---- 7. TLS --------------------------------------------------------------
log "requesting certificate…"
apt-get install -y -qq certbot python3-certbot-nginx
certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --non-interactive --agree-tos -m "${EMAIL}" --redirect
systemctl enable --now certbot.timer

log "done. next: cd ${APP_DIR} && docker compose up -d --build"
