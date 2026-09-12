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
- Пока боевой бэкенд не отдаёт plan_images в списке проектов, прокси
  дописывает их из карточки каждого проекта.
"""

import json
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

UPSTREAM = "https://brusodel.ru"
HOST = "127.0.0.1"
PORT = 8000

plan_images_cache: dict[str, list[str]] = {}


def fetch_upstream(path):
    request = urllib.request.Request(
        UPSTREAM + path,
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


def plan_images_for(slug):
    if slug not in plan_images_cache:
        try:
            _, _, body = fetch_upstream(f"/api/projects/{slug}/")
            plans = json.loads(body).get("plans") or []
            plan_images_cache[slug] = [plan["image"] for plan in plans if plan.get("image")]
        except Exception as error:  # noqa: BLE001 - dev helper, keep serving
            print(f"  ! plans for {slug}: {error}", file=sys.stderr)
            plan_images_cache[slug] = []
    return plan_images_cache[slug]


def add_plan_images(body):
    data = json.loads(body)
    items = data.get("results") if isinstance(data, dict) else data
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and "plan_images" not in item and item.get("slug"):
                item["plan_images"] = plan_images_for(item["slug"])
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


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

        try:
            status, content_type, body = fetch_upstream(self.path)
        except urllib.error.HTTPError as error:
            self._respond(error.code, error.headers.get("Content-Type", "application/json"), error.read())
            return
        except Exception as error:  # noqa: BLE001
            self._respond(502, "application/json", json.dumps({"detail": str(error)}).encode("utf-8"))
            return

        if path == "/api/projects/" and status == 200:
            body = add_plan_images(body)
            content_type = "application/json"

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
    print(f"Dev API proxy: http://{HOST}:{PORT}/api/ -> {UPSTREAM}/api/ (POST /api/leads/ is mocked)")
    ThreadingHTTPServer((HOST, PORT), ProxyHandler).serve_forever()
