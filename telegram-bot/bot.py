"""
Телеграм-бот обратной связи для brusodel.ru.

Простая пересылка, без интеграции с CRM сайта:

    пользователь пишет боту -> сообщение уходит админу (TELEGRAM_ADMIN_CHAT_ID)
    в личку -> админ отвечает на пересланное сообщение через "Reply" в
    Telegram -> ответ уходит обратно тому же пользователю от лица бота.

Кто есть кто пересланного сообщения хранится в собственной SQLite (не в БД
сайта — этому процессу вообще не нужен доступ ни к Postgres, ни к Django,
только к Telegram Bot API), в примонтированном томе /app/data, чтобы
привязка переживала рестарт контейнера.

В интернет ходит ТОЛЬКО через socks5-прокси на sidecar-контейнере xray (см.
docker-compose.prod.yml) — Telegram Bot API с российских IP часто недоступен
напрямую. Остальной стек сайта (backend, БД, фронтенд, Caddy) через этот
прокси не ходит и в отдельной сети с ботом не состоит.
"""

import asyncio
import logging
import os
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.types import Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("relay_bot")

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["TELEGRAM_ADMIN_CHAT_ID"])
# Sidecar-контейнер xray резолвится по имени сервиса в docker-сети bot_net —
# см. docker-compose.prod.yml. Порт 10808 — socks-инбаунд в xray/config.json.
SOCKS_PROXY_URL = os.environ.get("TELEGRAM_SOCKS_PROXY", "socks5://xray:10808")

DATA_DIR = Path(os.environ.get("TELEGRAM_BOT_DATA_DIR", "/app/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "relay.sqlite3"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS relay (
            admin_message_id INTEGER PRIMARY KEY,
            user_chat_id INTEGER NOT NULL,
            user_label TEXT NOT NULL
        )
        """
    )
    return conn


def remember(admin_message_id: int, user_chat_id: int, user_label: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO relay (admin_message_id, user_chat_id, user_label) "
            "VALUES (?, ?, ?)",
            (admin_message_id, user_chat_id, user_label),
        )


def lookup(admin_message_id: int) -> tuple[int, str] | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_chat_id, user_label FROM relay WHERE admin_message_id = ?",
            (admin_message_id,),
        ).fetchone()
    return (row[0], row[1]) if row else None


def describe_sender(message: Message) -> str:
    chat = message.chat
    parts = [p for p in (chat.first_name, chat.last_name) if p]
    name = " ".join(parts) or (chat.title or "без имени")
    if chat.username:
        name += f" (@{chat.username})"
    return name


# aiogram сам умеет ходить через socks5, если поставлен aiohttp-socks
# (см. requirements.txt) и передан proxy= в сессию — отдельно поднимать
# aiohttp_socks.ProxyConnector не нужно.
session = AiohttpSession(proxy=SOCKS_PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties())
dp = Dispatcher()


@dp.message(Command("start"), F.chat.id != ADMIN_CHAT_ID)
async def handle_start(message: Message) -> None:
    await message.answer(
        "Здравствуйте! Напишите вопрос по строительству дома или бани из "
        "бруса — ответим здесь же, в этом чате."
    )


@dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def handle_admin_reply(message: Message) -> None:
    """Админ ответил ("Reply") на пересланное сообщение -> уходит пользователю."""
    target = lookup(message.reply_to_message.message_id)

    if target is None:
        await message.reply(
            "Не нашёл, кому это адресовано — отвечайте через Reply прямо "
            "на пересланное сообщение от пользователя, не на произвольное."
        )
        return

    user_chat_id, user_label = target

    try:
        await bot.copy_message(
            chat_id=user_chat_id,
            from_chat_id=ADMIN_CHAT_ID,
            message_id=message.message_id,
        )
    except Exception:
        logger.exception("Не удалось отправить ответ пользователю %s", user_chat_id)
        await message.reply(f"⚠️ Не доставлено ({user_label}) — см. логи бота.")
        return

    await message.reply(f"✅ Отправлено: {user_label}")


@dp.message(F.chat.id == ADMIN_CHAT_ID)
async def handle_admin_other(message: Message) -> None:
    """Сообщение админа в этом чате, но не ответ ни на что — подсказка."""
    await message.reply(
        "Это личный чат бота с админом. Чтобы ответить пользователю, "
        "нажмите Reply на его пересланное сообщение."
    )


@dp.message()
async def handle_user_message(message: Message) -> None:
    """Любое сообщение от постороннего пользователя -> пересылаем админу."""
    label = describe_sender(message)

    forwarded = await bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    remember(forwarded.message_id, message.chat.id, label)

    hint = await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"👆 от {label} (chat_id={message.chat.id}). Ответьте через Reply на это сообщение.",
        reply_to_message_id=forwarded.message_id,
    )
    # Привязываем и подсказку тоже — если админ ответит Reply на неё, а не на
    # само пересланное сообщение, это тоже должно долететь до пользователя.
    remember(hint.message_id, message.chat.id, label)

    await message.answer("Спасибо, вопрос передали — ответим здесь же.")


async def main() -> None:
    logger.info("Стартуем relay-бота, admin_chat_id=%s, proxy=%s", ADMIN_CHAT_ID, SOCKS_PROXY_URL)
    me = await bot.get_me()
    logger.info("Подключились к Telegram как @%s (id=%s)", me.username, me.id)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
