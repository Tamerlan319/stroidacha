#!/usr/bin/env bash

set -Eeuo pipefail

BRUSODEL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRUSODEL_BACKUP_DIR="/opt/brusoteka-backups"
BRUSODEL_ENV_FILE="$BRUSODEL_ROOT/backend/.env.prod"

BRUSODEL_PRIMARY_DOMAIN="brusodel.ru"
BRUSODEL_WWW_DOMAIN="www.brusodel.ru"
BRUSODEL_PUBLIC_IP="194.67.74.142"

cd "$BRUSODEL_ROOT"

if [[ ! -f "$BRUSODEL_ENV_FILE" ]]; then
    echo "Missing backend/.env.prod. Run scripts/bootstrap-vps.sh first." >&2
    exit 1
fi

upsert_env_value() {
    local key="$1"
    local value="$2"

    if grep -qE "^${key}=" "$BRUSODEL_ENV_FILE"; then
        sed -i "s|^${key}=.*|${key}=${value}|" "$BRUSODEL_ENV_FILE"
    else
        printf '\n%s=%s\n' "$key" "$value" >> "$BRUSODEL_ENV_FILE"
    fi
}

# backend/.env.prod is intentionally not stored in Git because it contains
# secrets. These public deployment settings are therefore synchronized here
# on every deploy without touching SECRET_KEY, DB_PASSWORD or mail passwords.
upsert_env_value \
    "ALLOWED_HOSTS" \
    "${BRUSODEL_PRIMARY_DOMAIN},${BRUSODEL_WWW_DOMAIN},${BRUSODEL_PUBLIC_IP},localhost,127.0.0.1"
upsert_env_value \
    "CORS_ALLOWED_ORIGINS" \
    "https://${BRUSODEL_PRIMARY_DOMAIN},https://${BRUSODEL_WWW_DOMAIN}"
upsert_env_value \
    "CSRF_TRUSTED_ORIGINS" \
    "https://${BRUSODEL_PRIMARY_DOMAIN},https://${BRUSODEL_WWW_DOMAIN}"
upsert_env_value \
    "DEFAULT_FROM_EMAIL" \
    "no-reply@${BRUSODEL_PRIMARY_DOMAIN}"

chmod 600 "$BRUSODEL_ENV_FILE"

echo "Production domain settings synchronized:"
echo "  domain: ${BRUSODEL_PRIMARY_DOMAIN}"
echo "  public IP: ${BRUSODEL_PUBLIC_IP}"

BRUSODEL_COMPOSE=(
    docker compose
    --env-file backend/.env.prod
    -f docker-compose.prod.yml
)

mkdir -p "$BRUSODEL_BACKUP_DIR"

if "${BRUSODEL_COMPOSE[@]}" ps --status running --services | grep -qx db; then
    BRUSODEL_BACKUP_FILE="$BRUSODEL_BACKUP_DIR/postgres-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

    "${BRUSODEL_COMPOSE[@]}" exec -T db \
        sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
        | gzip -9 > "$BRUSODEL_BACKUP_FILE"
fi

"${BRUSODEL_COMPOSE[@]}" build --pull
"${BRUSODEL_COMPOSE[@]}" up -d --remove-orphans

# Internal health must not depend on DNS or the public domain. Public domain
# access is verified separately by GitHub Actions after deployment.
"${BRUSODEL_COMPOSE[@]}" exec -T backend \
    python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/', headers={'Host': '127.0.0.1', 'X-Forwarded-Proto': 'https'}); response = urllib.request.urlopen(request, timeout=10); assert response.status == 200"

# A bind-mounted Caddyfile does not itself guarantee that a running Caddy
# process reloads the changed configuration, so validate and reload explicitly.
"${BRUSODEL_COMPOSE[@]}" exec -T caddy \
    caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
"${BRUSODEL_COMPOSE[@]}" exec -T caddy \
    caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

find "$BRUSODEL_BACKUP_DIR" \
    -type f \
    -name 'postgres-*.sql.gz' \
    -mtime +14 \
    -delete

docker image prune -f
docker builder prune -f --filter until=168h

"${BRUSODEL_COMPOSE[@]}" ps
