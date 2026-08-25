# Развёртывание «Брусодела»

Production-схема рассчитана на Ubuntu 24.04, 2 vCPU, 2 ГБ RAM, 20 ГБ
диска и публичный IPv4.

## Первый запуск VPS

Подключитесь к серверу личным ключом:

```bash
ssh root@194.67.74.142
```

После попадания `scripts/bootstrap-vps.sh` в ветку `main` выполните:

```bash
git clone https://github.com/Tamerlan319/stroidacha.git /tmp/brusoteka-bootstrap
cd /tmp/brusoteka-bootstrap
sudo bash scripts/bootstrap-vps.sh
```

Скрипт устанавливает Docker, включает firewall и fail2ban, создаёт swap
на 2 ГБ, пользователя `brusoteka-deploy`, генерирует production-секреты и
запускает контейнеры.

## DNS

Для `brusodel.ru` нужны записи:

- `A` для `@` → `194.67.74.142`;
- `A` для `www` → `194.67.74.142`.

Caddy автоматически получает и обновляет TLS-сертификаты после обновления
DNS.

## GitHub Actions

В окружении `production` репозитория добавьте секреты:

- `VPS_HOST` — `194.67.74.142`;
- `VPS_USER` — `brusoteka-deploy`;
- `VPS_SSH_KEY` — закрытая часть отдельного ключа автодеплоя.

Публичную часть ключа добавьте в
`/home/brusoteka-deploy/.ssh/authorized_keys`. Закрытый ключ нельзя
сохранять в репозитории.

При pull request выполняются тесты Django, ESLint и production-сборка
Next.js. После push в `main` workflow подключается к VPS, создаёт резервную
копию PostgreSQL, обновляет код, пересобирает контейнеры и проверяет
`https://brusodel.ru/api/health/`.

## Данные сайта

Репозиторий содержит исходный архив медиафайлов, но не содержит дамп
локальной PostgreSQL с проектами, страницами и контактами. Перед публикацией
полного каталога нужно отдельно перенести дамп базы данных.

## Резервные копии

`scripts/deploy.sh` дампит Postgres при каждом деплое. Дамп содержит все
заявки целиком (телефоны, переписку, IP) — по 152-ФЗ его нужно защищать
не хуже рабочей базы, поэтому:

**Шифрование.** Один раз сгенерируйте пару GPG-ключей — приватную часть
не храните на этом же сервере (заберите к себе и в надёжное место):

```bash
gpg --full-generate-key   # RSA 4096, например backup@brusodel.ru
gpg --export backup@brusodel.ru > /tmp/backup-public.asc
sudo -u brusoteka-deploy gpg --homedir /home/brusoteka-deploy/.gnupg \
  --import /tmp/backup-public.asc
shred -u /tmp/backup-public.asc   # публичный ключ не секрет, но убираем за собой
```

Пропишите в `backend/.env.prod`:

```
BACKUP_GPG_RECIPIENT=backup@brusodel.ru
```

Без этой переменной `deploy.sh` продолжит писать бэкап как раньше —
незашифрованным, но выведет предупреждение при каждом деплое, чтобы это
не потерялось молча.

Расшифровка (на своей машине, где лежит приватный ключ):

```bash
gpg --decrypt postgres-20260101T040000Z.sql.gz.gpg | gunzip > postgres.sql
```

**Копия за пределами сервера.** Одна и та же VPS хранит и рабочую базу, и
бэкапы — при компрометации сервера теряется всё сразу. Настройте
[rclone](https://rclone.org/) на S3-совместимое хранилище на территории
РФ (Yandex Object Storage, Selectel и т.п. — не зарубежные S3/Backblaze,
чтобы не создавать новый вопрос по локализации), затем добавьте в
`backend/.env.prod`:

```
BACKUP_REMOTE_RCLONE_TARGET=yandex-s3:brusoteka-backups/
```

Без этой переменной шаг копирования просто пропускается.

## Хранение персональных данных заявок (152-ФЗ)

Вложения заявок (фото, планировки) хранятся в приватном сторадже, не
раздаются Caddy и отдаются только сотрудникам из Django admin. После
первого деплоя изменений безопасности выполните один раз:

```bash
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  exec backend python manage.py migrate_lead_attachments_to_private_storage
```

Проверьте, что скачивание файлов заявки в админке работает, и только
после этого повторите с `--delete-source`, чтобы убрать старые копии из
публичной медиатеки.

Заявки старше `LEAD_RETENTION_MONTHS` месяцев (по умолчанию 24, задаётся
в `backend/.env.prod`) нужно обезличивать по расписанию — в проекте нет
celery/beat, поэтому это обычный `cron` на сервере:

```bash
crontab -u brusoteka-deploy -e
# добавить строку:
0 4 1 * * /opt/brusoteka/scripts/cron-anonymize-leads.sh >> /var/log/brusoteka-anonymize-leads.log 2>&1
```

Проверить, что будет удалено, без реального изменения данных:

```bash
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  exec backend python manage.py anonymize_old_leads --dry-run
```

## Полезные команды

```bash
cd /opt/brusoteka
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml ps
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml logs --tail=200
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```
