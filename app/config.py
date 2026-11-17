import os
from datetime import timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DB_PATH = Path(os.environ.get("AGENT_DB_PATH", str(BASE_DIR / "data" / "agent.db")))

HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))

BRAND_NAME = "Horizon Properties"
BRAND_NAME_AR = "أفق العقارية"

OWNER_ID = "owner-1"
CALENDAR_TZ_NAME = "Asia/Dubai"
CALENDAR_TZ = timezone(timedelta(hours=4))
WORK_DAYS = (0, 1, 2, 3, 4)
SLOT_HOURS = (11, 14, 16)
SLOT_MINUTES = 30
MIN_LEAD_HOURS = 2
SLOT_OPTIONS = 3
SEARCH_DAYS = 14

DEDUPE_TTL_SECONDS = 600
MAX_STORED_MESSAGES = 200
MAX_MESSAGE_LENGTH = 1000

WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")

USD_RATES = {"USD": 1.0, "AED": 0.2723, "SAR": 0.2667, "QAR": 0.2747, "KWD": 3.25}
COUNTRY_CURRENCY = {"DUBAI": "AED", "SAUDI": "SAR", "QATAR": "QAR", "KUWAIT": "KWD"}
