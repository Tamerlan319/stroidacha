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

## Полезные команды

```bash
cd /opt/brusoteka
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml ps
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml logs --tail=200
docker compose --env-file backend/.env.prod -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```
