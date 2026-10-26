"""Точка входа: запускает бота и всех агентов."""
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import config
from bot.agents import deadlines, schedule

dp = Dispatcher()
# Бот личный: отвечаем только владельцу
dp.message.filter(F.from_user.id == config.OWNER_ID)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я твой помощник 🤖\n\n"
        "📅 Расписание:\n"
        "/today — пары на сегодня\n"
        "/tomorrow — пары на завтра\n"
        "/week — вся неделя\n\n"
        "📚 Учёба:\n"
        "/deadlines — ближайшие дедлайны из Moodle и советы по заданиям\n\n"
        "Скоро здесь появится почта."
    )


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(config.BOT_TOKEN)
    scheduler = AsyncIOScheduler(timezone=config.TZ)

    dp.include_router(schedule.router)
    schedule.setup(bot, scheduler)
    if config.MOODLE_ICAL_URL:
        dp.include_router(deadlines.router)
        deadlines.setup(bot, scheduler)

    scheduler.start()
    await schedule.plan_today_reminders(bot, scheduler)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
