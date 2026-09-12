"""Локальный прокси API для проверки фронтенда без своей базы данных.

Запуск из корня репозитория:

    python scripts/dev_api_proxy.py
    npm --prefix frontend run dev

Прокси слушает 127.0.0.1:8000 — это NEXT_PUBLIC_API_URL из frontend/.env.local.

- GET /api/... берёт данные с https://brusodel.ru/api/... (только чтение).
- POST /api/leads/ на боевой сервер НЕ уходит: прокси сам отвечает «успехом»,
  чтобы проверить окно «Заявка отправлена» без настоящих заявок и писем.
- POST /api/calculator/calculate/ пробрасывается: это чистый расчёт
  (HouseCalculatorService ничего не пишет в базу и никого не уведомляет),
  без него на локальной версии не появится результат калькулятора.
  Остальные POST не пропускаются.
- --catalog-upstream http://127.0.0.1:8001 — список проектов, фильтры
  (/api/projects/facets/) и категории берутся с локального бэкенда. Так
  изменения каталога проверяются на копии данных ещё до выкладки; всё
  остальное (страницы, отзывы, контакты) по-прежнему идёт с brusodel.ru.
"""

import argparse
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

UPSTREAM = "https://brusodel.ru"
HOST = "127.0.0.1"
PORT = 8000
CATALOG_PATHS = frozenset({"/api/projects/", "/api/projects/facets/", "/api/categories/"})

catalog_upstream: str | None = None


def fetch_upstream(path, base=UPSTREAM):
    request = urllib.request.Request(
        base + path,
        headers={"User-Agent": "brusodel-local-dev-proxy", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers.get("Content-Type", "application/json"), response.read()


def post_upstream(path, body, content_type):
    request = urllib.request.Request(
        UPSTREAM + path,
        data=body,
        method="POST",
        headers={
            "User-Agent": "brusodel-local-dev-proxy",
            "Accept": "application/json",
            "Content-Type": content_type or "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, response.headers.get("Content-Type", "application/json"), response.read()


class ProxyHandler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Vary", "Origin")

    def _respond(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):  # noqa: N802 - http.server naming
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):  # noqa: N802
        path = urlsplit(self.path).path
        if not path.startswith("/api/"):
            self._respond(404, "application/json", b'{"detail": "only /api/ is proxied"}')
            return

        base = catalog_upstream if catalog_upstream and path in CATALOG_PATHS else UPSTREAM
        try:
            status, content_type, body = fetch_upstream(self.path, base)
        except urllib.error.HTTPError as error:
            self._respond(error.code, error.headers.get("Content-Type", "application/json"), error.read())
            return
        except Exception as error:  # noqa: BLE001
            self._respond(502, "application/json", json.dumps({"detail": str(error)}).encode("utf-8"))
            return

        self._respond(status, content_type, body)

    def do_POST(self):  # noqa: N802
        path = urlsplit(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""

        if path == "/api/calculator/calculate/":
            try:
                status, content_type, response_body = post_upstream(
                    self.path, body, self.headers.get("Content-Type")
                )
            except urllib.error.HTTPError as error:
                self._respond(error.code, error.headers.get("Content-Type", "application/json"), error.read())
                return
            except Exception as error:  # noqa: BLE001
                self._respond(502, "application/json", json.dumps({"detail": str(error)}).encode("utf-8"))
                return
            self._respond(status, content_type, response_body)
            return

        if path == "/api/leads/":
            print("  [mock] POST /api/leads/ - lead NOT sent to production")
            self._respond(201, "application/json", b'{"id": 0, "detail": "local mock"}')
            return

        self._respond(405, "application/json", b'{"detail": "POST is not proxied"}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local read-only API proxy for the frontend dev server.")
    parser.add_argument(
        "--catalog-upstream",
        metavar="URL",
        help="serve project list, facets and categories from this backend (e.g. http://127.0.0.1:8001)",
    )
    args = parser.parse_args()
    catalog_upstream = args.catalog_upstream.rstrip("/") if args.catalog_upstream else None

    print(f"Dev API proxy: http://{HOST}:{PORT}/api/ -> {UPSTREAM}/api/ (POST /api/leads/ is mocked)")
    if catalog_upstream:
        print(f"Catalog endpoints -> {catalog_upstream}")
    ThreadingHTTPServer((HOST, PORT), ProxyHandler).serve_forever()
