#!/usr/bin/env bash
# Sectrix — one-shot droplet bootstrap (Ubuntu 24.04, 1 vCPU / 1 GB).
#
# Prepares a fresh DigitalOcean droplet to run the docker-compose stack:
#   swapfile -> docker -> firewall -> nginx -> certbot
#
# Usage (as root on the droplet):
#   DOMAIN=sectrix.com EMAIL=ops@sectrix.com ./deploy/bootstrap.sh
#
# Idempotent: safe to re-run.
set -euo pipefail

DOMAIN="${DOMAIN:?set DOMAIN=yourdomain.com}"
EMAIL="${EMAIL:?set EMAIL=you@yourdomain.com for certbot expiry notices}"
APP_DIR="${APP_DIR:-/opt/sectrix}"

log() { printf '\033[36m[bootstrap]\033[0m %s\n' "$*" >&2; }

# ---- 1. Swap -------------------------------------------------------------
# DO droplets ship with no swap. 1 GB covers build spikes and keeps the OOM
# killer away from Gunicorn/Postgres when they peak together.
if ! swapon --show | grep -q '/swapfile'; then
  log "creating 1G swapfile…"
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  # Low swappiness: use swap as a safety net, not routinely.
  sysctl -w vm.swappiness=10
  grep -q 'vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
else
  log "swap already present, skipping"
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
  log "docker already installed, skipping"
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
