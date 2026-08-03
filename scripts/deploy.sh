#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="/opt/brusoteka-backups"
PRIMARY_DOMAIN="brusodel.ru"

cd "$PROJECT_ROOT"

if [[ ! -f backend/.env.prod ]]; then
	echo "Missing backend/.env.prod. Run scripts/bootstrap-vps.sh first." >&2
	exit 1
fi

COMPOSE=(
	docker compose
	--env-file backend/.env.prod
	-f docker-compose.prod.yml
)

mkdir -p "$BACKUP_DIR"

if "${COMPOSE[@]}" ps --status running --services | grep -qx db; then
	BACKUP_FILE="$BACKUP_DIR/postgres-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

	"${COMPOSE[@]}" exec -T db \
		sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
		| gzip -9 > "$BACKUP_FILE"
fi

echo "Building application images..."
"${COMPOSE[@]}" build --pull

echo "Starting database, backend and frontend..."
"${COMPOSE[@]}" up -d --remove-orphans

echo "Checking Django health inside backend..."
"${COMPOSE[@]}" exec -T backend \
	python -c "import urllib.request; request = urllib.request.Request('http://127.0.0.1:8000/api/health/', headers={'Host': 'brusodel.ru', 'X-Forwarded-Proto': 'https'}); response = urllib.request.urlopen(request, timeout=10); print('Backend health:', response.status)"

echo "Validating the Caddyfile from the current Git checkout..."
docker run --rm \
	-v "$PROJECT_ROOT/caddy/Caddyfile:/etc/caddy/Caddyfile:ro" \
	caddy:2-alpine \
	caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

echo "Recreating Caddy so the new bind-mounted Caddyfile is attached..."
"${COMPOSE[@]}" up -d --force-recreate --no-deps caddy

echo "Waiting for a valid HTTPS certificate for ${PRIMARY_DOMAIN}..."
HTTPS_READY=0

for attempt in $(seq 1 24); do
	if curl \
		--fail \
		--silent \
		--show-error \
		--max-time 15 \
		--resolve "${PRIMARY_DOMAIN}:443:127.0.0.1" \
		"https://${PRIMARY_DOMAIN}/api/health/" \
		>/dev/null 2>&1
	then
		HTTPS_READY=1
		break
	fi

	if (( attempt % 6 == 0 )); then
		echo "Still waiting for HTTPS (${attempt}/24)..."
	fi

	sleep 5
done

if [[ "$HTTPS_READY" -ne 1 ]]; then
	echo "HTTPS for ${PRIMARY_DOMAIN} is still unavailable." >&2
	echo "Fresh Caddy logs from this deployment:" >&2
	"${COMPOSE[@]}" logs --since=3m --tail=120 caddy >&2 || true
	exit 1
fi

echo "HTTPS is ready: https://${PRIMARY_DOMAIN}"

find "$BACKUP_DIR" \
	-type f \
	-name 'postgres-*.sql.gz' \
	-mtime +14 \
	-delete

docker image prune -f
docker builder prune -f --filter until=168h

"${COMPOSE[@]}" ps
