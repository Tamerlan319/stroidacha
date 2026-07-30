#!/usr/bin/env bash

set -Eeuo pipefail

BRUSOTEKA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRUSOTEKA_BACKUP_DIR="/opt/brusoteka-backups"

cd "$BRUSOTEKA_ROOT"

if [[ ! -f backend/.env.prod ]]; then
    echo "Missing backend/.env.prod. Run scripts/bootstrap-vps.sh first." >&2
    exit 1
fi

BRUSOTEKA_COMPOSE=(
    docker compose
    --env-file backend/.env.prod
    -f docker-compose.prod.yml
)

mkdir -p "$BRUSOTEKA_BACKUP_DIR"

if "${BRUSOTEKA_COMPOSE[@]}" ps --status running --services | grep -qx db; then
    BRUSOTEKA_BACKUP_FILE="$BRUSOTEKA_BACKUP_DIR/postgres-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
    "${BRUSOTEKA_COMPOSE[@]}" exec -T db \
        sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
        | gzip -9 > "$BRUSOTEKA_BACKUP_FILE"
fi

"${BRUSOTEKA_COMPOSE[@]}" build --pull
"${BRUSOTEKA_COMPOSE[@]}" up -d --remove-orphans

"${BRUSOTEKA_COMPOSE[@]}" exec -T backend \
    python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/', headers={'Host': 'brusoteka.ru', 'X-Forwarded-Proto': 'https'}); urllib.request.urlopen(request, timeout=10)"

find "$BRUSOTEKA_BACKUP_DIR" -type f -name 'postgres-*.sql.gz' -mtime +14 -delete
docker image prune -f
docker builder prune -f --filter until=168h

"${BRUSOTEKA_COMPOSE[@]}" ps
