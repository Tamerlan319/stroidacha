"""Проверка Яндекс SmartCaptcha на сервере.

Клиентский виджет (frontend/app/components/LeadForm.tsx) отдаёт одноразовый
токен после того, как посетитель прошёл капчу. Доверять самому факту
рендера виджета нельзя — токен нужно подтвердить у Яндекса напрямую,
секретным серверным ключом, иначе бот может просто не звать виджет и слать
форму напрямую в API.
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VALIDATE_URL = "https://smartcaptcha.yandexcloud.net/validate"
REQUEST_TIMEOUT = 5


def is_smartcaptcha_enabled() -> bool:
    return bool(settings.SMARTCAPTCHA_SERVER_KEY)


def verify_smartcaptcha(token: str, ip_address: str | None) -> bool:
    """True, если токен подтверждён Яндексом (или капча не настроена).

    При сетевой ошибке/таймауте намеренно возвращает False (fail-closed):
    для формы заявок ложное срабатывание (лишний клик "попробуйте ещё раз"
    у реального клиента) дешевле, чем открытая лазейка для ботов при сбое
    внешнего сервиса.
    """
    if not is_smartcaptcha_enabled():
        return True

    if not token:
        return False

    params = {
        "secret": settings.SMARTCAPTCHA_SERVER_KEY,
        "token": token,
    }
    if ip_address:
        params["ip"] = ip_address

    url = f"{VALIDATE_URL}?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        logger.exception("Не удалось проверить SmartCaptcha")
        return False

    if data.get("status") != "ok":
        logger.warning(
            "SmartCaptcha отклонила токен: %s", data.get("message", "без сообщения")
        )
        return False

    return True
