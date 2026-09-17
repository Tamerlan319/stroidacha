"""Шифрование телефона в заявке.

Номер лежит в базе и в бэкапах зашифрованным (Fernet: AES-128-CBC +
HMAC-SHA256) и расшифровывается только внутри приложения — в админке и в
письме менеджерам. Ключ — LEAD_PHONE_ENCRYPTION_KEY в backend/.env.prod,
любая длинная случайная строка: из неё SHA-256 выводит ключ Fernet. Без
этой строки номер не прочитать ни из базы, ни из дампа.

Пока ключ не задан, номер сохраняется как есть — заявка важнее, — а
проверка leads.W001 (leads/checks.py) предупреждает об этом при каждом
запуске. Когда ключ задан, `python manage.py encrypt_lead_phones` шифрует
уже сохранённые номера.

Смена или потеря ключа делает сохранённые номера нечитаемыми.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


logger = logging.getLogger(__name__)

# Метка зашифрованного значения: по ней отличаем шифр от номера, сохранённого
# до появления ключа.
PREFIX = "enc:"


class UnreadablePhone(str):
    """Номер, который нечем расшифровать: ключа нет или он другой.

    Показывается в админке пояснением, а при сохранении заявки в базу уходит
    исходный шифр (raw) — иначе правка любого поля заявки затёрла бы номер.
    """

    def __new__(cls, raw):
        obj = super().__new__(cls, "(номер зашифрован — не задан ключ расшифровки)")
        obj.raw = raw
        return obj


def _fernet():
    secret = getattr(settings, "LEAD_PHONE_ENCRYPTION_KEY", "")
    if not secret:
        return None
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_value(value):
    if not value or isinstance(value, UnreadablePhone) or value.startswith(PREFIX):
        return value
    fernet = _fernet()
    if fernet is None:
        return value
    return PREFIX + fernet.encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_value(value):
    if not value or not value.startswith(PREFIX):
        return value
    fernet = _fernet()
    if fernet is None:
        return UnreadablePhone(value)
    try:
        return fernet.decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.error("Не удалось расшифровать телефон заявки: ключ не подходит")
        return UnreadablePhone(value)


class EncryptedPhoneField(models.CharField):
    """Текстовое поле, которое хранит значение в базе зашифрованным.

    Искать и фильтровать по нему на стороне базы нельзя: одинаковые номера
    дают разный шифр.
    """

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if isinstance(value, UnreadablePhone):
            return value.raw
        return encrypt_value(value)
