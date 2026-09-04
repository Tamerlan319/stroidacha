"""
Телеграм-бот обратной связи для brusodel.ru.

Пользователь пишет боту -> сообщение уходит админу (TELEGRAM_ADMIN_CHAT_ID) в
личку, плюс попадает в /inbox — список диалогов с сортировкой по свежести и
статусами (новый/активный/закрытый), чтобы при большом числе обращений
ничего не терялось. Админ отвечает либо через Reply на пересланное
сообщение, либо открыв диалог из /inbox кнопкой — дальше можно просто писать
текстом, без Reply, пока диалог открыт. Ответ уходит пользователю от лица
бота.

Никакой БД сайта тут нет и не нужно — своя маленькая SQLite (в
примонтированном томе /app/data), пережившая рестарт контейнера. В интернет
ходит только через socks5-прокси на sidecar-контейнере xray — см.
docker-compose.prod.yml и DEPLOYMENT.md.
"""

import asyncio
import logging
import os
import sqlite3
import time
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

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

PAGE_SIZE = 8
STATUS_EMOJI = {"new": "🆕", "active": "💬", "closed": "✅"}
STATUS_LABEL = {"new": "Новые", "active": "Активные", "closed": "Закрытые", "all": "Все"}
STATUS_ORDER = ("all", "new", "active", "closed")

WELCOME_TEXT = (
    "👋 Здравствуйте! Вы написали в бот компании «Брусодел» — строим дома и "
    "бани из бруса под ключ с 2009 года: своё производство, доставка и "
    "монтаж.\n\n"
    "Расскажите, что вас интересует — подберём проект под участок и бюджет, "
    "посчитаем стоимость, ответим на любые вопросы. Отвечаем сами, здесь же, "
    "в этом чате.\n\n"
    "Если проще — сразу напишите: дом или баня, примерный размер и регион. 🏡"
)


# --- Хранилище -------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            user_chat_id INTEGER PRIMARY KEY,
            user_label TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            last_message_at INTEGER NOT NULL,
            last_message_preview TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS relay (
            admin_message_id INTEGER PRIMARY KEY,
            user_chat_id INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS admin_focus (
            admin_chat_id INTEGER PRIMARY KEY,
            user_chat_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_chat_id INTEGER NOT NULL,
            direction TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_chat_id, created_at);
        """
    )
    return conn


def log_message(user_chat_id: int, direction: str, text: str) -> None:
    """direction: 'in' — от пользователя, 'out' — от админа."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO messages (user_chat_id, direction, text, created_at) VALUES (?, ?, ?, ?)",
            (user_chat_id, direction, text, int(time.time())),
        )


def get_recent_messages(user_chat_id: int, limit: int = 8) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT direction, text, created_at FROM messages "
            "WHERE user_chat_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_chat_id, limit),
        ).fetchall()
    return [dict(row) for row in reversed(rows)]


def touch_conversation(user_chat_id: int, user_label: str, preview: str) -> None:
    preview = preview[:120]
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO conversations (user_chat_id, user_label, status, last_message_at, last_message_preview)
            VALUES (?, ?, 'new', ?, ?)
            ON CONFLICT(user_chat_id) DO UPDATE SET
                user_label = excluded.user_label,
                last_message_at = excluded.last_message_at,
                last_message_preview = excluded.last_message_preview,
                -- Новое сообщение в закрытом диалоге снова требует внимания.
                status = CASE WHEN status = 'closed' THEN 'new' ELSE status END
            """,
            (user_chat_id, user_label, int(time.time()), preview),
        )


def set_status(user_chat_id: int, status: str) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE conversations SET status = ? WHERE user_chat_id = ?",
            (status, user_chat_id),
        )


def get_conversation(user_chat_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE user_chat_id = ?", (user_chat_id,)
        ).fetchone()
    return dict(row) if row else None


def list_conversations(status_filter: str, limit: int, offset: int) -> list[dict]:
    where = "" if status_filter == "all" else "WHERE status = ?"
    params: tuple = () if status_filter == "all" else (status_filter,)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM conversations {where} "
            "ORDER BY last_message_at DESC LIMIT ? OFFSET ?",
            (*params, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def remember_relay(admin_message_id: int, user_chat_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO relay (admin_message_id, user_chat_id) VALUES (?, ?)",
            (admin_message_id, user_chat_id),
        )


def lookup_relay(admin_message_id: int) -> int | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_chat_id FROM relay WHERE admin_message_id = ?",
            (admin_message_id,),
        ).fetchone()
    return row["user_chat_id"] if row else None


def set_focus(user_chat_id: int | None) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO admin_focus (admin_chat_id, user_chat_id) VALUES (?, ?) "
            "ON CONFLICT(admin_chat_id) DO UPDATE SET user_chat_id = excluded.user_chat_id",
            (ADMIN_CHAT_ID, user_chat_id),
        )


def get_focus() -> int | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT user_chat_id FROM admin_focus WHERE admin_chat_id = ?",
            (ADMIN_CHAT_ID,),
        ).fetchone()
    return row["user_chat_id"] if row and row["user_chat_id"] is not None else None


# --- Вспомогательное ---------------------------------------------------------


def describe_sender(message: Message) -> str:
    chat = message.chat
    parts = [p for p in (chat.first_name, chat.last_name) if p]
    name = " ".join(parts) or (chat.title or "без имени")
    if chat.username:
        name += f" (@{chat.username})"
    return name


def preview_of(message: Message) -> str:
    """Полный текст для лога переписки — обрезка только на отображении."""
    if message.text:
        return message.text
    if message.caption:
        return f"[медиа] {message.caption}"
    if message.photo:
        return "[фото]"
    if message.document:
        return "[документ]"
    if message.voice:
        return "[голосовое]"
    if message.video:
        return "[видео]"
    return "[сообщение]"


def humanize_ago(timestamp: int) -> str:
    delta = max(0, int(time.time()) - timestamp)
    if delta < 60:
        return "только что"
    if delta < 3600:
        return f"{delta // 60} мин назад"
    if delta < 86400:
        return f"{delta // 3600} ч назад"
    return f"{delta // 86400} дн назад"


def build_inbox_view(status_filter: str, page: int) -> tuple[str, InlineKeyboardMarkup]:
    rows: list[list[InlineKeyboardButton]] = []

    tabs = []
    for key in STATUS_ORDER:
        label = STATUS_LABEL[key]
        if key == status_filter:
            label = f"• {label} •"
        tabs.append(InlineKeyboardButton(text=label, callback_data=f"inbox:{key}:0"))
    rows.append(tabs)

    conversations = list_conversations(status_filter, limit=PAGE_SIZE, offset=page * PAGE_SIZE)

    if not conversations:
        text = f"📭 Пусто: «{STATUS_LABEL[status_filter]}» — диалогов нет."
    else:
        lines = [f"📥 Диалоги — {STATUS_LABEL[status_filter]}:"]
        for conv in conversations:
            emoji = STATUS_EMOJI[conv["status"]]
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{emoji} {conv['user_label']} — {humanize_ago(conv['last_message_at'])}",
                        callback_data=f"open:{conv['user_chat_id']}",
                    )
                ]
            )
        text = "\n".join(lines)

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"inbox:{status_filter}:{page - 1}"))
    if len(conversations) == PAGE_SIZE:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"inbox:{status_filter}:{page + 1}"))
    if nav:
        rows.append(nav)

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def build_conversation_view(user_chat_id: int) -> tuple[str, InlineKeyboardMarkup]:
    conv = get_conversation(user_chat_id)
    if conv is None:
        return "Диалог не найден — возможно, уже удалён.", InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К списку", callback_data="inbox:all:0")]]
        )

    lines = [f"💬 {conv['user_label']}", ""]
    history = get_recent_messages(user_chat_id, limit=8)
    if history:
        for msg in history:
            who = "🧑 Клиент" if msg["direction"] == "in" else "🧑‍💼 Вы"
            body = msg["text"]
            if len(body) > 200:
                body = body[:200] + "…"
            lines.append(f"{who} ({humanize_ago(msg['created_at'])}): {body}")
    else:
        lines.append("(сообщений пока нет)")
    lines.append("")
    lines.append(
        "Пишите ответ прямо сюда, обычным сообщением — он уйдёт этому "
        "пользователю, пока диалог открыт."
    )
    text = "\n".join(lines)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Закрыть диалог", callback_data=f"close:{user_chat_id}"),
                InlineKeyboardButton(text="🔙 К списку", callback_data="inbox:all:0"),
            ]
        ]
    )
    return text, keyboard


async def deliver_to_user(source: Message, user_chat_id: int) -> bool:
    try:
        await bot.copy_message(
            chat_id=user_chat_id,
            from_chat_id=ADMIN_CHAT_ID,
            message_id=source.message_id,
        )
    except Exception:
        logger.exception("Не удалось отправить ответ пользователю %s", user_chat_id)
        return False
    set_status(user_chat_id, "active")
    log_message(user_chat_id, "out", preview_of(source))
    return True


# --- Бот ---------------------------------------------------------------------

session = AiohttpSession(proxy=SOCKS_PROXY_URL)
bot = Bot(token=BOT_TOKEN, session=session, default=DefaultBotProperties())
dp = Dispatcher()


@dp.message(Command("start"), F.chat.id != ADMIN_CHAT_ID)
async def handle_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@dp.message(Command("inbox"), F.chat.id == ADMIN_CHAT_ID)
async def cmd_inbox(message: Message) -> None:
    text, keyboard = build_inbox_view("all", 0)
    await message.answer(text, reply_markup=keyboard)


@dp.message(Command("close"), F.chat.id == ADMIN_CHAT_ID)
async def cmd_close(message: Message) -> None:
    focused = get_focus()
    if focused is None:
        await message.answer("Сейчас не открыт ни один диалог — см. /inbox.")
        return
    set_status(focused, "closed")
    set_focus(None)
    await message.answer("Диалог закрыт.")


@dp.callback_query(F.data.startswith("inbox:"))
async def cb_inbox(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    _, status_filter, page = callback.data.split(":")
    text, keyboard = build_inbox_view(status_filter, int(page))
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("open:"))
async def cb_open(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    user_chat_id = int(callback.data.split(":", 1)[1])
    conv = get_conversation(user_chat_id)
    if conv and conv["status"] == "new":
        set_status(user_chat_id, "active")
    set_focus(user_chat_id)
    text, keyboard = build_conversation_view(user_chat_id)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data.startswith("close:"))
async def cb_close(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return
    user_chat_id = int(callback.data.split(":", 1)[1])
    set_status(user_chat_id, "closed")
    if get_focus() == user_chat_id:
        set_focus(None)
    await callback.answer("Диалог закрыт")
    text, keyboard = build_inbox_view("all", 0)
    await callback.message.edit_text(text, reply_markup=keyboard)


@dp.message(F.chat.id == ADMIN_CHAT_ID, F.reply_to_message)
async def handle_admin_reply(message: Message) -> None:
    """Явный Reply на пересланное сообщение — работает независимо от /inbox."""
    user_chat_id = lookup_relay(message.reply_to_message.message_id)
    if user_chat_id is None:
        await message.reply("Не нашёл, кому это адресовано — откройте диалог через /inbox.")
        return

    conv = get_conversation(user_chat_id)
    label = conv["user_label"] if conv else str(user_chat_id)
    ok = await deliver_to_user(message, user_chat_id)
    await message.reply(f"✅ Отправлено: {label}" if ok else f"⚠️ Не доставлено ({label}) — см. логи бота.")


@dp.message(F.chat.id == ADMIN_CHAT_ID)
async def handle_admin_default(message: Message) -> None:
    """Обычное сообщение админа без Reply — уходит в открытый через /inbox диалог."""
    if message.text and message.text.startswith("/"):
        await message.answer("Неизвестная команда. Доступно: /inbox, /close")
        return

    focused = get_focus()
    if focused is None:
        text, keyboard = build_inbox_view("all", 0)
        await message.answer("Не указано, кому отвечать. Выберите диалог:", reply_markup=keyboard)
        return

    conv = get_conversation(focused)
    label = conv["user_label"] if conv else str(focused)
    ok = await deliver_to_user(message, focused)
    await message.reply(f"✅ Отправлено: {label}" if ok else "⚠️ Не доставлено — см. логи бота.")


@dp.message()
async def handle_user_message(message: Message) -> None:
    """Любое сообщение от постороннего пользователя -> пересылаем админу."""
    label = describe_sender(message)
    text = preview_of(message)
    touch_conversation(message.chat.id, label, text)
    log_message(message.chat.id, "in", text)

    forwarded = await bot.forward_message(
        chat_id=ADMIN_CHAT_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    remember_relay(forwarded.message_id, message.chat.id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Открыть диалог", callback_data=f"open:{message.chat.id}"),
                InlineKeyboardButton(text="✅ Закрыть", callback_data=f"close:{message.chat.id}"),
            ]
        ]
    )
    hint = await bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"👆 {label} (chat_id={message.chat.id})",
        reply_to_message_id=forwarded.message_id,
        reply_markup=keyboard,
    )
    remember_relay(hint.message_id, message.chat.id)

    await message.answer("Спасибо! Ваше сообщение передали, ответим здесь же.")


async def setup_commands() -> None:
    await bot.set_my_commands([BotCommand(command="start", description="Начать разговор")])
    await bot.set_my_commands(
        [
            BotCommand(command="inbox", description="Список диалогов"),
            BotCommand(command="close", description="Закрыть открытый диалог"),
        ],
        scope=BotCommandScopeChat(chat_id=ADMIN_CHAT_ID),
    )


async def main() -> None:
    logger.info("Стартуем relay-бота, admin_chat_id=%s, proxy=%s", ADMIN_CHAT_ID, SOCKS_PROXY_URL)
    me = await bot.get_me()
    logger.info("Подключились к Telegram как @%s (id=%s)", me.username, me.id)
    await setup_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
