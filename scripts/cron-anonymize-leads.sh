#!/usr/bin/env bash
# Ежемесячная (или чаще) очистка ПДн старых заявок по 152-ФЗ — в проекте
# нет celery/beat, поэтому это обычный скрипт для системного cron.
#
# Пример записи в crontab пользователя brusoteka-deploy (1-е число месяца,
# 04:00 по времени сервера):
#   0 4 1 * * /opt/brusoteka/scripts/cron-anonymize-leads.sh >> /var/log/brusoteka-anonymize-leads.log 2>&1
#
# Срок хранения задаётся LEAD_RETENTION_MONTHS в backend/.env.prod
# (по умолчанию 24 месяца, если переменная не задана).

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f backend/.env.prod ]]; then
    echo "Missing backend/.env.prod. Run scripts/bootstrap-vps.sh first." >&2
    exit 1
fi

docker compose \
    --env-file backend/.env.prod \
    -f docker-compose.prod.yml \
    exec -T backend \
    python manage.py anonymize_old_leads
