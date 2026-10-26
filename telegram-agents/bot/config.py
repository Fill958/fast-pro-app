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

# Почтовые ящики (IMAP). Пустые строки в .env — ящик пропускается.
MAIL_ACCOUNTS = [
    {"name": name, "host": os.getenv(f"{prefix}_IMAP_HOST", host),
     "user": os.getenv(f"{prefix}_USER", ""), "password": os.getenv(f"{prefix}_PASSWORD", "")}
    for name, prefix, host in [
        ("Gmail", "GMAIL", "imap.gmail.com"),
        ("Яндекс", "YANDEX", "imap.yandex.ru"),
        ("ТПУ", "TPU", "mail.tpu.ru"),
    ]
    if os.getenv(f"{prefix}_USER")
]
MAIL_DIGEST_TIMES = os.getenv("MAIL_DIGEST_TIMES", "09:00,18:00").split(",")
MAIL_STATE_FILE = os.getenv("MAIL_STATE_FILE", "mail_state.json")
