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
