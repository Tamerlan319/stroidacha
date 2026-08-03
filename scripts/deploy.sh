#!/usr/bin/env bash

set -Eeuo pipefail

BRUSODEL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRUSODEL_BACKUP_DIR="/opt/brusoteka-backups"
BRUSODEL_DOMAIN="brusodel.ru"

cd "$BRUSODEL_ROOT"

if [[ ! -f backend/.env.prod ]]; then
    echo "Missing backend/.env.prod. Run scripts/bootstrap-vps.sh first." >&2
    exit 1
fi

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

echo "Validating and reloading Caddy configuration..."
"${BRUSODEL_COMPOSE[@]}" exec -T caddy \
    caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

"${BRUSODEL_COMPOSE[@]}" exec -T caddy \
    caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

echo "Checking Django health inside the backend container..."
"${BRUSODEL_COMPOSE[@]}" exec -T backend \
    python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/', headers={'Host': 'brusodel.ru', 'X-Forwarded-Proto': 'https'}); response = urllib.request.urlopen(request, timeout=10); print('Backend health:', response.status)"

echo "Waiting for the HTTPS certificate and Caddy route..."
HTTPS_READY=0

for attempt in $(seq 1 30); do
    if curl \
        --fail \
        --silent \
        --show-error \
        --max-time 15 \
        --resolve "${BRUSODEL_DOMAIN}:443:127.0.0.1" \
        "https://${BRUSODEL_DOMAIN}/api/health/" \
        >/dev/null
    then
        HTTPS_READY=1
        echo "HTTPS is ready."
        break
    fi

    echo "HTTPS is not ready yet (${attempt}/30). Waiting 5 seconds..."
    sleep 5
done

if [[ "$HTTPS_READY" -ne 1 ]]; then
    echo "Caddy did not obtain or serve a certificate for ${BRUSODEL_DOMAIN}." >&2
    echo "Check that A records for @ and www point to this VPS public IP." >&2
    echo "Recent Caddy logs:" >&2
    "${BRUSODEL_COMPOSE[@]}" logs --tail=250 caddy >&2 || true
    exit 1
fi

find "$BRUSODEL_BACKUP_DIR" \
    -type f \
    -name 'postgres-*.sql.gz' \
    -mtime +14 \
    -delete

docker image prune -f
docker builder prune -f --filter until=168h

"${BRUSODEL_COMPOSE[@]}" ps
