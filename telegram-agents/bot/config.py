import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
TZ = ZoneInfo(os.getenv("TZ", "Europe/Moscow"))
REMIND_BEFORE_MIN = int(os.getenv("REMIND_BEFORE_MIN", "15"))
MORNING_TIME = os.getenv("MORNING_TIME", "07:30")
SCHEDULE_FILE = os.getenv("SCHEDULE_FILE", "schedule.json")

# Ссылка «Экспорт календаря» из Moodle (stud.lms.tpu.ru → Календарь → Экспорт)
MOODLE_ICAL_URL = os.getenv("MOODLE_ICAL_URL", "")
# Ключ Claude API для советов по заданиям (необязательно)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
STATE_FILE = os.getenv("STATE_FILE", "state.json")
