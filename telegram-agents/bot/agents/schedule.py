"""Агент расписания: знает пары и напоминает о них."""
import json
from datetime import date, datetime, timedelta

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import config

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

router = Router(name="schedule")


def load_schedule() -> dict:
    with open(config.SCHEDULE_FILE, encoding="utf-8") as f:
        return json.load(f)


def lessons_for(day: date) -> list[dict]:
    lessons = load_schedule().get(DAYS[day.weekday()], [])
    return sorted(lessons, key=lambda x: x["start"])


def format_day(day: date) -> str:
    lessons = lessons_for(day)
    header = f"📅 {DAY_NAMES[day.weekday()]}, {day:%d.%m}"
    if not lessons:
        return f"{header}\nПар нет, можно отдохнуть 🙂"
    lines = [f"• {l['start']}–{l['end']}  {l['title']} ({l.get('room', '')})" for l in lessons]
    return header + "\n" + "\n".join(lines)


def today() -> date:
    return datetime.now(config.TZ).date()


@router.message(Command("today"))
async def cmd_today(message: Message):
    await message.answer(format_day(today()))


@router.message(Command("tomorrow"))
async def cmd_tomorrow(message: Message):
    await message.answer(format_day(today() + timedelta(days=1)))


@router.message(Command("week"))
async def cmd_week(message: Message):
    start = today() - timedelta(days=today().weekday())
    days = [format_day(start + timedelta(days=i)) for i in range(7)]
    await message.answer("\n\n".join(days))


async def send_morning_summary(bot: Bot):
    await bot.send_message(config.OWNER_ID, "Доброе утро! ☀️\n\n" + format_day(today()))


async def plan_today_reminders(bot: Bot, scheduler: AsyncIOScheduler):
    """Ставит напоминания на каждую сегодняшнюю пару."""
    now = datetime.now(config.TZ)
    for lesson in lessons_for(now.date()):
        h, m = map(int, lesson["start"].split(":"))
        start = now.replace(hour=h, minute=m, second=0, microsecond=0)
        remind_at = start - timedelta(minutes=config.REMIND_BEFORE_MIN)
        if remind_at <= now:
            continue
        text = (f"⏰ Через {config.REMIND_BEFORE_MIN} мин: {lesson['title']}\n"
                f"{lesson['start']}–{lesson['end']}, {lesson.get('room', '')}")
        scheduler.add_job(bot.send_message, "date", run_date=remind_at,
                          args=[config.OWNER_ID, text],
                          id=f"lesson-{now.date()}-{lesson['start']}", replace_existing=True)


def setup(bot: Bot, scheduler: AsyncIOScheduler):
    h, m = map(int, config.MORNING_TIME.split(":"))
    scheduler.add_job(send_morning_summary, "cron", hour=h, minute=m, args=[bot])
    # Каждую ночь в 00:05 планируем напоминания на новый день
    scheduler.add_job(plan_today_reminders, "cron", hour=0, minute=5, args=[bot, scheduler])
