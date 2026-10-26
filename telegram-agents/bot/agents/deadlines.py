"""Агент дедлайнов: читает календарь Moodle и напоминает о сроках сдачи."""
import asyncio
import json
import os
from datetime import date, datetime, timedelta

import aiohttp
import anthropic
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from icalendar import Calendar

from bot import config

router = Router(name="deadlines")
REMIND_DAYS = (3, 1)  # за сколько дней напоминать

_cache: list[dict] = []  # последние загруженные дедлайны


async def fetch_deadlines() -> list[dict]:
    """Скачивает iCal-календарь Moodle и возвращает будущие дедлайны."""
    global _cache
    async with aiohttp.ClientSession() as session:
        async with session.get(config.MOODLE_ICAL_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            resp.raise_for_status()
            cal = Calendar.from_ical(await resp.read())

    now = datetime.now(config.TZ)
    items = []
    for ev in cal.walk("VEVENT"):
        due = ev.decoded("DTSTART")
        if isinstance(due, date) and not isinstance(due, datetime):
            due = datetime.combine(due, datetime.min.time())
        due = due.replace(tzinfo=due.tzinfo or config.TZ).astimezone(config.TZ)
        if due < now:
            continue
        items.append({
            "uid": str(ev.get("UID")),
            "title": str(ev.get("SUMMARY", "Без названия")),
            "course": str(ev.get("CATEGORIES").cats[0]) if ev.get("CATEGORIES") else "",
            "description": str(ev.get("DESCRIPTION", "")),
            "due": due,
        })
    _cache = sorted(items, key=lambda x: x["due"])
    return _cache


def format_deadline(d: dict) -> str:
    left = d["due"] - datetime.now(config.TZ)
    if left.days >= 1:
        left_txt = f"через {left.days} дн."
    else:
        left_txt = f"через {left.seconds // 3600} ч."
    course = f" · {d['course']}" if d["course"] else ""
    return f"📌 {d['title']}{course}\n   до {d['due']:%d.%m %H:%M} ({left_txt})"


@router.message(Command("deadlines"))
async def cmd_deadlines(message: Message):
    items = await fetch_deadlines()
    if not items:
        await message.answer("Ближайших дедлайнов нет 🎉")
        return
    items = items[:10]
    text = "📚 Ближайшие дедлайны:\n\n" + "\n\n".join(
        f"{i}. {format_deadline(d)}" for i, d in enumerate(items, 1))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💡 Совет по №{i}", callback_data=f"advice:{i - 1}")]
        for i in range(1, len(items) + 1)
    ]) if config.ANTHROPIC_API_KEY else None
    await message.answer(text, reply_markup=kb)


def ask_claude(d: dict) -> str:
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = (
        "Ты помощник студента. Дай короткий практичный план, как выполнить задание: "
        "3–5 шагов, с чего начать сегодня, сколько примерно времени заложить. "
        "Пиши по-русски, просто, без лишней воды.\n\n"
        f"Курс: {d['course']}\nЗадание: {d['title']}\n"
        f"Срок: {d['due']:%d.%m.%Y %H:%M}\nОписание из LMS:\n{d['description'][:4000]}"
    )
    response = client.beta.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        return "Не получилось составить совет по этому заданию."
    return "".join(b.text for b in response.content if b.type == "text")


@router.callback_query(F.data.startswith("advice:"))
async def on_advice(callback: CallbackQuery):
    idx = int(callback.data.split(":")[1])
    if idx >= len(_cache):
        await callback.answer("Список устарел, отправь /deadlines ещё раз")
        return
    await callback.answer("Думаю…")
    d = _cache[idx]
    advice = await asyncio.to_thread(ask_claude, d)
    await callback.message.answer(f"💡 {d['title']}\n\n{advice}")


# --- напоминания ---

def _load_sent() -> set[str]:
    try:
        with open(config.STATE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def _save_sent(sent: set[str]):
    with open(config.STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(sent), f)


async def check_and_remind(bot: Bot):
    items = await fetch_deadlines()
    sent = _load_sent()
    now = datetime.now(config.TZ)
    for d in items:
        # Берём самый «срочный» подходящий порог и шлём одно напоминание
        for days in sorted(REMIND_DAYS):
            if d["due"] - now > timedelta(days=days):
                continue
            if f"{d['uid']}:{days}" not in sent:
                await bot.send_message(config.OWNER_ID, f"⏳ Осталось меньше {days} дн.!\n\n{format_deadline(d)}")
                # пороги побольше уже не нужны
                sent.update(f"{d['uid']}:{x}" for x in REMIND_DAYS if x >= days)
            break
    _save_sent(sent)


def setup(bot: Bot, scheduler: AsyncIOScheduler):
    # Проверяем календарь Moodle каждые 3 часа
    scheduler.add_job(check_and_remind, "interval", hours=3, args=[bot],
                      next_run_time=datetime.now(config.TZ) + timedelta(seconds=10))
