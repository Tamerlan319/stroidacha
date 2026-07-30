#!/usr/bin/env bash

set -Eeuo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run this script as root." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl fail2ban git gnupg openssl ufw unzip

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
printf '%s\n' \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
    | tee /etc/apt/sources.list.d/docker.list >/dev/null

apt-get update
apt-get install -y \
    containerd.io \
    docker-buildx-plugin \
    docker-ce \
    docker-ce-cli \
    docker-compose-plugin

systemctl enable --now docker fail2ban

if ! id brusoteka-deploy >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash brusoteka-deploy
fi
usermod -aG docker brusoteka-deploy

install -d -m 700 -o brusoteka-deploy -g brusoteka-deploy \
    /home/brusoteka-deploy/.ssh
if [[ -s /root/.ssh/authorized_keys ]]; then
    install -m 600 -o brusoteka-deploy -g brusoteka-deploy \
        /root/.ssh/authorized_keys \
        /home/brusoteka-deploy/.ssh/authorized_keys
fi

ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

if [[ ! -f /swapfile ]]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    printf '%s\n' '/swapfile none swap sw 0 0' | tee -a /etc/fstab >/dev/null
fi
printf '%s\n' 'vm.swappiness=10' > /etc/sysctl.d/99-brusoteka.conf
sysctl --system >/dev/null

install -d -m 755 -o brusoteka-deploy -g brusoteka-deploy \
    /opt/brusoteka \
    /opt/brusoteka-backups

if [[ ! -d /opt/brusoteka/.git ]]; then
    git clone https://github.com/Tamerlan319/stroidacha.git /opt/brusoteka
fi
chown -R brusoteka-deploy:brusoteka-deploy /opt/brusoteka

cd /opt/brusoteka
runuser -u brusoteka-deploy -- git fetch origin main
runuser -u brusoteka-deploy -- git checkout main
runuser -u brusoteka-deploy -- git merge --ff-only origin/main

if [[ ! -f backend/.env.prod ]]; then
    BRUSOTEKA_SECRET_KEY="$(openssl rand -base64 48 | tr -d '\n')"
    BRUSOTEKA_DB_PASSWORD="$(openssl rand -hex 24)"
    umask 077
    tee backend/.env.prod >/dev/null <<ENV
DEBUG=False
SECRET_KEY=$BRUSOTEKA_SECRET_KEY

DB_NAME=brusoteka
DB_USER=brusoteka_user
DB_PASSWORD=$BRUSOTEKA_DB_PASSWORD
DB_HOST=db
DB_PORT=5432

ALLOWED_HOSTS=brusoteka.ru,www.brusoteka.ru,194.67.74.142,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=https://brusoteka.ru,https://www.brusoteka.ru
CSRF_TRUSTED_ORIGINS=https://brusoteka.ru,https://www.brusoteka.ru

DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000

GUNICORN_WORKERS=2

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@brusoteka.ru
LEAD_NOTIFICATION_EMAILS=
ENV
    chown brusoteka-deploy:brusoteka-deploy backend/.env.prod
fi

chown -R brusoteka-deploy:brusoteka-deploy \
    /opt/brusoteka \
    /opt/brusoteka-backups

runuser -u brusoteka-deploy -- bash scripts/deploy.sh

if unzip -Z1 backend/backend.zip | grep -q '^media/'; then
    BRUSOTEKA_TMP_DIR="$(mktemp -d)"
    trap 'rm -rf "$BRUSOTEKA_TMP_DIR"' EXIT
    unzip -q backend/backend.zip 'media/*' -d "$BRUSOTEKA_TMP_DIR"
    docker cp "$BRUSOTEKA_TMP_DIR/media/." brusoteka_backend:/app/media/
fi

echo
echo "Bootstrap complete."
echo "SSH user for GitHub Actions: brusoteka-deploy"
echo "Next: configure DNS and GitHub Actions secrets."
