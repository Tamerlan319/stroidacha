#!/usr/bin/env bash

set -Eeuo pipefail

BRUSODEL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRUSODEL_BACKUP_DIR="/opt/brusoteka-backups"

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

"${BRUSODEL_COMPOSE[@]}" exec -T backend \
    python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/', headers={'Host': 'brusodel.ru', 'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(request, timeout=10)"

find "$BRUSODEL_BACKUP_DIR" -type f -name 'postgres-*.sql.gz' -mtime +14 -delete
docker image prune -f
docker builder prune -f --filter until=168h

"${BRUSODEL_COMPOSE[@]}" ps
