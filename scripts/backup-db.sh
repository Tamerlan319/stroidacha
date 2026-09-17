#!/usr/bin/env bash
# Резервная копия базы. В /opt/brusoteka-backups всегда лежит ровно одна,
# самая свежая: в дампе все заявки, а по 152-ФЗ (ст. 5 ч. 7) держать их
# копии дольше необходимого нельзя. Предыдущая копия удаляется только после
# того, как новая записалась целиком, — неудачный дамп не оставит без бэкапа.
#
# Запускается перед каждым деплоем (scripts/deploy.sh) и ежедневно по cron
# (деплой сам ставит запись в crontab пользователя деплоя).

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="/opt/brusoteka-backups"

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

if ! "${COMPOSE[@]}" ps --status running --services | grep -qx db; then
	echo "Database container is not running — backup skipped."
	exit 0
fi

umask 077
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/postgres-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"

# Шифруем asymmetric-ключом GPG, если он настроен (см. DEPLOYMENT.md —
# "Резервные копии"), чтобы приватный ключ для расшифровки не приходилось
# хранить на этом же сервере.
if [[ -n "${BACKUP_GPG_RECIPIENT:-}" ]]; then
	BACKUP_FILE="$BACKUP_FILE.gpg"
	"${COMPOSE[@]}" exec -T db \
		sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
		| gzip -9 \
		| gpg --batch --yes --trust-model always \
			--encrypt --recipient "$BACKUP_GPG_RECIPIENT" \
			--output "$BACKUP_FILE.partial"
else
	echo "WARNING: BACKUP_GPG_RECIPIENT is not set — backup is written UNENCRYPTED. See DEPLOYMENT.md > 'Резервные копии'." >&2
	"${COMPOSE[@]}" exec -T db \
		sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
		| gzip -9 > "$BACKUP_FILE.partial"
fi

mv "$BACKUP_FILE.partial" "$BACKUP_FILE"

# Всё, кроме только что записанной копии, — удаляем.
find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 ! -name "$(basename "$BACKUP_FILE")" -exec rm -rf {} +

# Копия за пределами этого сервера — без неё компрометация VPS означает
# потерю и рабочей БД, и бэкапа разом. Настраивается через rclone (см.
# DEPLOYMENT.md); без настройки шаг пропускается.
if [[ -n "${BACKUP_REMOTE_RCLONE_TARGET:-}" ]]; then
	if command -v rclone >/dev/null 2>&1; then
		rclone copy "$BACKUP_FILE" "$BACKUP_REMOTE_RCLONE_TARGET"
	else
		echo "WARNING: BACKUP_REMOTE_RCLONE_TARGET is set but rclone is not installed on this host — off-site backup copy was skipped." >&2
	fi
fi

echo "Backup written: $BACKUP_FILE"
