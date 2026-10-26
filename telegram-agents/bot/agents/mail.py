"""Агент почты: читает новые письма из нескольких ящиков, сортирует и присылает сводку.

Письма только читаются: бот не помечает их прочитанными, не удаляет и не отвечает.
"""
import asyncio
import email
import imaplib
import json
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parseaddr

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import config, llm

router = Router(name="mail")

CATEGORIES = {
    "важное": "🔴 Важное",
    "учёба": "📚 Учёба",
    "работа": "💼 Работа",
    "рассылки": "📰 Рассылки и реклама",
    "прочее": "📨 Прочее",
}

_pending: list[dict] = []  # отсортированные письма, ещё не попавшие в сводку


def _decode(value: str | None) -> str:
    return str(make_header(decode_header(value))) if value else ""


def _body_snippet(msg: email.message.Message, limit: int = 600) -> str:
    for part in msg.walk():
        if part.get_content_type() == "text/plain" and not part.get_filename():
            payload = part.get_payload(decode=True) or b""
            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
            return " ".join(text.split())[:limit]
    return ""


def fetch_new(account: dict, state: dict) -> list[dict]:
    """Забирает письма, пришедшие после прошлой проверки (по UID)."""
    name = account["name"]
    with imaplib.IMAP4_SSL(account["host"], 993) as imap:
        imap.login(account["user"], account["password"])
        imap.select("INBOX", readonly=True)
        last_uid = state.get(name)
        if last_uid is None:
            # Первый запуск: берём только письма за последние сутки
            since = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
            _, data = imap.uid("search", None, f"SINCE {since}")
        else:
            _, data = imap.uid("search", None, f"UID {last_uid + 1}:*")
        uids = [int(u) for u in data[0].split() if last_uid is None or int(u) > last_uid]

        letters = []
        for uid in uids[-30:]:  # не больше 30 писем за раз
            _, msg_data = imap.uid("fetch", str(uid), "(BODY.PEEK[])")
            msg = email.message_from_bytes(msg_data[0][1])
            sender_name, sender_addr = parseaddr(_decode(msg.get("From")))
            letters.append({
                "account": name,
                "from": sender_name or sender_addr,
                "from_addr": sender_addr,
                "subject": _decode(msg.get("Subject")) or "(без темы)",
                "snippet": _body_snippet(msg),
            })
        if uids:
            state[name] = max(uids)
        elif last_uid is None:
            _, data = imap.uid("search", None, "ALL")
            all_uids = data[0].split()
            state[name] = int(all_uids[-1]) if all_uids else 0
    return letters


SORT_SCHEMA = {
    "type": "object",
    "properties": {
        "letters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "category": {"type": "string", "enum": list(CATEGORIES)},
                    "summary": {"type": "string"},
                },
                "required": ["id", "category", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["letters"],
    "additionalProperties": False,
}


def sort_letters(letters: list[dict]) -> list[dict]:
    """Раскладывает письма по категориям с помощью Claude (или простых правил без ключа)."""
    if not letters:
        return []
    if not config.ANTHROPIC_API_KEY:
        for l in letters:
            l["category"] = "учёба" if l["from_addr"].endswith("tpu.ru") else "прочее"
            l["summary"] = l["subject"]
        return letters

    listing = "\n\n".join(
        f"[{i}] Ящик: {l['account']}\nОт: {l['from']} <{l['from_addr']}>\nТема: {l['subject']}\nТекст: {l['snippet']}"
        for i, l in enumerate(letters)
    )
    prompt = (
        "Ты личный ассистент студента ТПУ, который ещё и работает. Разложи письма по категориям:\n"
        "важное — нужно действие скоро (сроки, деньги, документы, личные письма от людей);\n"
        "учёба — от вуза, преподавателей, LMS; работа — по работе; "
        "рассылки — реклама, новости, уведомления сервисов; прочее — остальное.\n"
        "Для каждого письма дай summary: одна короткая фраза по-русски, что в нём и что сделать.\n\n"
        + listing
    )
    result = llm.ask(prompt, schema=SORT_SCHEMA, max_tokens=4000)
    by_id = {x["id"]: x for x in (result or {}).get("letters", [])}
    for i, l in enumerate(letters):
        item = by_id.get(i, {})
        l["category"] = item.get("category", "прочее")
        l["summary"] = item.get("summary", l["subject"])
    return letters


def format_digest(letters: list[dict]) -> str:
    if not letters:
        return "📭 Новых писем нет."
    lines = [f"📬 Новых писем: {len(letters)}"]
    for key, title in CATEGORIES.items():
        group = [l for l in letters if l["category"] == key]
        if not group:
            continue
        lines.append(f"\n{title} ({len(group)})")
        if key == "рассылки":
            continue  # рассылки только считаем, не расписываем
        for l in group:
            lines.append(f"• {l['from']} [{l['account']}]: {l['summary']}")
    return "\n".join(lines)


def _load_state() -> dict:
    try:
        with open(config.MAIL_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_state(state: dict):
    with open(config.MAIL_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def check_all() -> tuple[list[dict], list[str]]:
    state = _load_state()
    letters, errors = [], []
    for account in config.MAIL_ACCOUNTS:
        try:
            letters += fetch_new(account, state)
        except Exception as e:  # один сломанный ящик не должен ломать остальные
            errors.append(f"{account['name']}: {e}")
    _save_state(state)
    return sort_letters(letters), errors


async def check_and_alert(bot: Bot):
    letters, errors = await asyncio.to_thread(check_all)
    _pending.extend(letters)
    for l in letters:
        if l["category"] == "важное":
            await bot.send_message(config.OWNER_ID, f"🔴 Важное письмо [{l['account']}]\nОт: {l['from']}\n{l['summary']}")
    for err in errors:
        await bot.send_message(config.OWNER_ID, f"⚠️ Не удалось проверить почту {err}")


async def send_digest(bot: Bot):
    await check_and_alert(bot)
    if _pending:
        await bot.send_message(config.OWNER_ID, format_digest(_pending))
        _pending.clear()


@router.message(Command("mail"))
async def cmd_mail(message: Message):
    await message.answer("Проверяю почту…")
    letters, errors = await asyncio.to_thread(check_all)
    _pending.extend(letters)
    text = format_digest(_pending)
    _pending.clear()
    if errors:
        text += "\n\n⚠️ " + "\n⚠️ ".join(errors)
    await message.answer(text)


def setup(bot: Bot, scheduler: AsyncIOScheduler):
    scheduler.add_job(check_and_alert, "interval", minutes=30, args=[bot])
    for t in config.MAIL_DIGEST_TIMES:
        h, m = map(int, t.split(":"))
        scheduler.add_job(send_digest, "cron", hour=h, minute=m, args=[bot])
