# Брусотека

Сайт компании по строительству домов, бань и гаражей из бруса под ключ
в России.

## Стек

- Django 5 + Django REST Framework;
- Next.js 16 + React 19;
- PostgreSQL 16;
- Caddy;
- Docker Compose.

## Локальная разработка

Backend использует переменные окружения из `backend/.env`. Frontend использует
`frontend/.env.local`.

```bash
docker compose up -d db
cd backend
python manage.py migrate
python manage.py runserver
```

В отдельном терминале:

```bash
cd frontend
npm ci
npm run dev
```

Production-развёртывание на `brusoteka.ru` описано в
[DEPLOYMENT.md](DEPLOYMENT.md).
