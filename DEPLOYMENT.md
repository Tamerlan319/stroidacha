# Развёртывание «Брусодела»

Production-схема рассчитана на Ubuntu 24.04, 2 vCPU, 2 ГБ RAM, 20 ГБ
диска и публичный IPv4.

## Первый запуск VPS

Подключитесь к серверу личным ключом:

```bash
ssh root@194.67.74.172
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

- `A` для `@` → `194.67.74.172`;
- `A` для `www` → `194.67.74.172`.

Caddy автоматически получает и обновляет TLS-сертификаты после обновления
DNS.

## GitHub Actions

В окружении `production` репозитория добавьте секреты:

- `VPS_HOST` — `194.67.74.172`;
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

## Email-уведомления о заявках

По умолчанию `EMAIL_BACKEND=console.EmailBackend` — письмо о новой заявке
(`leads.services.notify_managers_about_lead`) только пишется в лог
контейнера `backend`, наружу не уходит. Чтобы заявки реально приходили на
почту, в `backend/.env.prod` нужно:

1. Переключить бэкенд на SMTP и заполнить `EMAIL_HOST*` — закомментированный
   пример под Яндекс.Почту уже есть в `backend/.env.prod.example`.
2. Для Яндекс.Почты `EMAIL_HOST_PASSWORD` — это **пароль приложения**
   (Яндекс ID → Пароли и приложения → Пароль для внешнего приложения →
   «Почта»), а не пароль от самого аккаунта — обычный пароль SMTP не
   примет.
3. `DEFAULT_FROM_EMAIL` должен совпадать с `EMAIL_HOST_USER` — иначе Яндекс
   отклонит письмо как подмену отправителя.
4. `LEAD_NOTIFICATION_EMAILS` — один адрес или несколько через запятую,
   куда слать уведомления.

Применить и проверить:

```bash
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  up -d --no-deps backend

docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  exec backend python manage.py sendtestemail you@example.com
```

Если `sendtestemail` не приходит — смотрите ошибку в логах:
`docker compose ... logs --tail=50 backend`.

## Яндекс SmartCaptcha

Форма заявки (`LeadForm`) поддерживает Яндекс SmartCaptcha
(https://cloud.yandex.ru/services/smartcaptcha) — по умолчанию выключена:
без ключей форма работает как раньше, ни фронтенд, ни бэкенд ничего не
требуют.

1. Создайте капчу в Yandex Cloud Console — получите **client key**
   (публичный, для виджета) и **server key** (секретный, для проверки).
2. Впишите в `backend/.env.prod`:

   ```
   SMARTCAPTCHA_SERVER_KEY=...
   NEXT_PUBLIC_SMARTCAPTCHA_CLIENT_KEY=...
   ```

3. `NEXT_PUBLIC_*` Next.js встраивает в клиентский бандл на этапе **сборки**,
   поэтому одного рестарта контейнера недостаточно — нужна пересборка:

   ```bash
   docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
     build frontend
   docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
     up -d --no-deps backend frontend
   ```

`SMARTCAPTCHA_SERVER_KEY` без `NEXT_PUBLIC_SMARTCAPTCHA_CLIENT_KEY` (или
наоборот) не имеет смысла — заполняйте оба сразу.

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

## SEO-страницы по размерам и региону

`generate_seo_landing_pages` создаёт страницы под конкретные размеры
домов/бань (например, «Дома из бруса 7х7») и региональные страницы
Москва/область — по фактическим данным каталога. Не перезаписывает уже
существующие страницы (в том числе изменённые вручную в Django Admin),
если не передан `--overwrite`, поэтому его можно безопасно перезапускать
после добавления новых проектов в каталог:

```bash
# сначала посмотреть, что будет создано
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  exec backend python manage.py generate_seo_landing_pages --dry-run

docker compose --env-file backend/.env.prod -f docker-compose.prod.yml \
  exec backend python manage.py generate_seo_landing_pages
```

Новые страницы публикуются сразу (`is_active=True`) — тексты и FAQ можно
поправить в Django Admin в любой момент, командой они не будут
перезаписаны без `--overwrite`.

## Полезные команды

```bash
cd /opt/brusoteka
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml ps
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml logs --tail=200
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```
