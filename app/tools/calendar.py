import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app import config, store

WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAYS_AR = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]

ZONES = {
    "Asia/Dubai": (4, "GST", "بتوقيت الخليج"),
    "Asia/Riyadh": (3, "AST", "بتوقيت السعودية"),
    "Asia/Qatar": (3, "AST", "بتوقيت قطر"),
    "Asia/Kuwait": (3, "AST", "بتوقيت الكويت"),
}
DEFAULT_ZONE = "Asia/Dubai"


def _zone(name: str) -> tuple[timezone, str, str]:
    offset, label_en, label_ar = ZONES.get(name, ZONES[DEFAULT_ZONE])
    return timezone(timedelta(hours=offset)), label_en, label_ar


def format_label(iso: str, language: str = "en", tz_name: str = DEFAULT_ZONE, now: Optional[datetime] = None) -> str:
    zone, label_en, label_ar = _zone(tz_name)
    moment = datetime.fromisoformat(iso).astimezone(zone)
    reference = (now or datetime.now(zone)).astimezone(zone)
    delta = (moment.date() - reference.date()).days
    hour = moment.hour % 12 or 12
    if language == "ar":
        suffix = "ص" if moment.hour < 12 else "م"
        clock = f"{hour}:{moment.minute:02d} {suffix} {label_ar}"
        if delta == 0:
            day = "اليوم"
        elif delta == 1:
            day = "بكرة"
        elif 1 < delta < 7:
            day = f"يوم {WEEKDAYS_AR[moment.weekday()]}"
        else:
            day = f"يوم {WEEKDAYS_AR[moment.weekday()]} {moment.day} {MONTHS_AR[moment.month - 1]}"
        return f"{day} الساعة {clock}"
    suffix = "AM" if moment.hour < 12 else "PM"
    clock = f"{hour}:{moment.minute:02d} {suffix} {label_en}"
    if delta == 0:
        day = "Today"
    elif delta == 1:
        day = "Tomorrow"
    elif 1 < delta < 7:
        day = WEEKDAYS_EN[moment.weekday()]
    else:
        day = f"{WEEKDAYS_EN[moment.weekday()]} {moment.day} {MONTHS_EN[moment.month - 1]}"
    return f"{day} at {clock}"


def _open_days() -> list[list[datetime]]:
    now = datetime.now(config.CALENDAR_TZ)
    earliest = now + timedelta(hours=config.MIN_LEAD_HOURS)
    taken = store.booked_slots()
    days: list[list[datetime]] = []
    for offset in range(config.SEARCH_DAYS):
        day: date = now.date() + timedelta(days=offset)
        if day.weekday() not in config.WORK_DAYS:
            continue
        slots = []
        for hour in config.SLOT_HOURS:
            start = datetime(day.year, day.month, day.day, hour, 0, tzinfo=config.CALENDAR_TZ)
            if start >= earliest and start.isoformat() not in taken:
                slots.append(start)
        if slots:
            days.append(slots)
    return days


async def get_slot_options(
    owner_id: str,
    timezone: str = DEFAULT_ZONE,
    round_index: int = 0,
    language: str = "en",
) -> list[dict[str, str]]:
    days = _open_days()
    if not days:
        return []
    chosen: list[datetime] = []
    for position in range(config.SLOT_OPTIONS):
        day_slots = days[(round_index * config.SLOT_OPTIONS + position) % len(days)]
        slot = day_slots[(round_index + position) % len(day_slots)]
        if slot not in chosen:
            chosen.append(slot)
    return [{"iso": slot.isoformat(), "label": format_label(slot.isoformat(), language, timezone)} for slot in chosen]


async def get_available_slots(owner_id: str, timezone: str = DEFAULT_ZONE) -> list[str]:
    options = await get_slot_options(owner_id, timezone)
    return [option["label"] for option in options]


async def create_calendar_event(lead_phone: str, lead_name: str, slot_iso: str) -> Optional[str]:
    try:
        start = datetime.fromisoformat(slot_iso).astimezone(config.CALENDAR_TZ)
    except ValueError:
        return None
    if start < datetime.now(config.CALENDAR_TZ):
        return None
    reference = "HP-" + secrets.token_hex(3).upper()
    created = store.insert_booking(reference, lead_phone, lead_name, start.isoformat())
    return reference if created else None
