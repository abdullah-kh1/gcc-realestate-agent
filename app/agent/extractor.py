import re
from datetime import datetime, timedelta
from typing import Any, Optional

from app import config
from app.agent.language import contains_keyword, normalize

COUNTRY_KEYWORDS = {
    "DUBAI": ["dubai", "uae", "emirates", "abu dhabi", "abudhabi", "sharjah", "ajman", "دبي", "الامارات", "ابوظبي", "الشارقة", "عجمان"],
    "SAUDI": ["saudi", "ksa", "riyadh", "jeddah", "dammam", "السعودية", "الرياض", "جدة", "الدمام", "المملكة"],
    "QATAR": ["qatar", "doha", "lusail", "the pearl", "قطر", "الدوحة", "لوسيل", "اللؤلؤة"],
    "KUWAIT": ["kuwait", "الكويت"],
}

INTENT_KEYWORDS = {
    "GOLDEN_VISA": [
        "golden visa", "residency", "visa", "iqama", "premium residency",
        "الاقامة الذهبية", "الفيزا الذهبية", "فيزا", "اقامة", "الاقامة",
    ],
    "INVESTMENT": [
        "invest", "investment", "investor", "investing", "rental income", "rent out", "roi", "yield", "returns", "flip", "resale",
        "استثمار", "استثمر", "استثماري", "عائد", "ربح",
    ],
    "PERSONAL_USE": [
        "live in", "living", "my family", "for family", "personal use", "own use", "to live", "move to", "relocate", "my home",
        "سكن", "للسكن", "اسكن", "عائلتي", "عيلتي", "استخدام شخصي", "لنفسي", "انتقل",
    ],
}

TIMELINE_KEYWORDS = {
    "OFF_PLAN": [
        "off plan", "off-plan", "offplan", "under construction", "next year", "no rush", "not in a hurry", "later",
        "على الخارطة", "قيد الانشاء", "السنة الجاية", "السنة القادمة", "ما استعجل", "لاحقا", "بعدين",
    ],
    "3_MONTHS": [
        "few months", "next quarter", "three months",
        "شهرين", "ثلاث اشهر", "ثلاثة اشهر", "ثلاث شهور", "ثلاثة شهور", "كم شهر",
    ],
    "IMMEDIATE": [
        "immediately", "immediate", "asap", "right away", "this month", "urgent", "ready to buy", "ready now", "as soon as", "next week",
        "فورا", "حالا", "الحين", "الان", "بسرعة", "جاهز", "هالشهر", "هذا الشهر", "اقرب وقت",
    ],
}

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
}
MONTHS_RE = re.compile(r"(?<![a-z0-9])(\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve)\s*months?(?![a-z])")
MONTHS_AR_RE = re.compile(r"(\d+)\s*(?:اشهر|شهور|شهر)")

CURRENCY_WORDS = {
    "aed": "AED", "dirham": "AED", "dirhams": "AED", "dhs": "AED", "درهم": "AED",
    "sar": "SAR", "riyal": "SAR", "riyals": "SAR", "ريال": "SAR",
    "qar": "QAR", "kwd": "KWD", "dinar": "KWD", "dinars": "KWD", "دينار": "KWD",
    "usd": "USD", "dollar": "USD", "dollars": "USD", "$": "USD", "دولار": "USD",
}
RIYAL_WORDS = {"riyal", "riyals", "ريال"}
MULTIPLIERS = {
    "million": 1_000_000, "mil": 1_000_000, "m": 1_000_000, "مليون": 1_000_000,
    "thousand": 1_000, "k": 1_000, "الف": 1_000,
}
CURRENCY_PATTERN = r"aed|dirhams?|dhs|sar|riyals?|qar|kwd|dinars?|usd|dollars?|\$|درهم|ريال|دينار|دولار"
AMOUNT_RE = re.compile(
    r"(?P<prefix>aed|usd|sar|qar|kwd|\$)?\s*(?P<num>\d[\d,]*(?:\.\d+)?)\s*"
    r"(?:(?P<mult>million|mil|thousand|m|k|مليون|الف)(?![a-z0-9]))?\s*"
    r"(?P<cur>(?:" + CURRENCY_PATTERN + r")(?![a-z]))?"
)
WORD_AMOUNT_RE = re.compile(
    r"(?<![a-z؀-ۿ])(?P<word>مليونين|مليون|million)(?![a-z])\s*"
    r"(?P<cur>(?:" + CURRENCY_PATTERN + r")(?![a-z]))?"
)
NON_BUDGET_TAIL_RE = re.compile(r"(?:sq|sqft|sqm|متر|bed|br\b|bhk|year|month|سنة|سنوات|شهر|اشهر|شهور|غرف|floor|%)")
MIN_PLAIN_BUDGET = 10_000
MAX_PLAIN_BUDGET = 100_000_000

NAME_PREFIX_RE = re.compile(
    r"(?:my name is|my name's|call me|i am called|اسمي)\s+(?P<name>[A-Za-z؀-ۿ][A-Za-z؀-ۿ .'-]{0,40})",
    re.IGNORECASE,
)
PLAIN_NAME_RE = re.compile(r"^[A-Za-z؀-ۿ][A-Za-z؀-ۿ .'-]{1,40}$")
NAME_STOP_WORDS = {
    "and", "i", "im", "i'm", "my", "from", "please", "yes", "no", "ok", "okay", "thanks", "thank", "sure", "hi", "hello",
    "hey", "looking", "want", "need", "buy", "property", "apartment", "villa", "budget", "how", "what", "when", "where",
    "why", "wanna", "interested", "can", "could", "do", "is", "are", "tell", "nothing", "none",
    "و", "وابي", "وابغى", "وابغي", "وانا", "ابي", "ابغى", "ابغي", "نعم", "لا", "تمام", "اوكي", "شكرا", "مرحبا", "هلا",
    "السلام", "وش", "شو", "كم", "كيف", "هل",
}

QUESTION_WORDS = {
    "what", "how", "can", "could", "do", "does", "is", "are", "which", "will", "should", "tell", "explain",
    "كم", "كيف", "هل", "ما", "ماذا", "وش", "شو", "ايش", "اش", "ليش", "لماذا",
}
ANYWHERE_QUESTION_WORDS = {"what", "how", "كم", "كيف", "هل", "وش", "شو", "ايش"}
WORD_RE = re.compile(r"[a-z؀-ۿ']+")

IDENTITY_PHRASES = [
    "are you a bot", "are you ai", "are you an ai", "are you a robot", "are you human", "are you real", "are you a real person",
    "real person", "talking to a bot", "talking to a human", "talking to a robot", "is this a bot", "is this ai", "chatgpt",
    "انت بوت", "هل انت بوت", "انت روبوت", "هل انت روبوت", "انت انسان", "هل انت انسان", "انت حقيقي", "هل انت حقيقي",
    "ذكاء اصطناعي", "شخص حقيقي", "انت ذكاء",
]
THANKS_WORDS = ["thanks", "thank you", "thx", "shukran", "شكرا", "مشكور", "يعطيك العافية", "الله يعطيك"]
OTHER_SLOT_PHRASES = [
    "other time", "another time", "none of", "different time", "other options", "other slots", "not available", "later", "none",
    "ما يناسبني", "مو مناسب", "وقت ثاني", "موعد ثاني", "غيرها", "مواعيد ثانية", "ولا واحد",
]

ORDINAL_RE = re.compile(r"^(?:option|number|no|slot|رقم|الخيار|الموعد)?\s*([1-3])\s*[.)]?$")
ORDINAL_WORDS = [
    (["first", "الاول", "الاولي", "الاولى"], 0),
    (["second", "الثاني", "الثانيه", "الثانية"], 1),
    (["third", "الثالث", "الثالثه", "الثالثة"], 2),
]
WEEKDAY_WORDS = [
    ["monday", "الاثنين"], ["tuesday", "الثلاثاء"], ["wednesday", "الاربعاء"], ["thursday", "الخميس"],
    ["friday", "الجمعة"], ["saturday", "السبت"], ["sunday", "الاحد"],
]
TIME_12H_RE = re.compile(r"(?<![0-9:])(\d{1,2})(?::(\d{2}))?\s*(am|pm|ص|م)(?![a-z])")
TIME_24H_RE = re.compile(r"(?<![0-9])([01]?\d|2[0-3]):([0-5]\d)(?![0-9])")
TOMORROW_WORDS = ["tomorrow", "بكرة", "غدا"]
TODAY_WORDS = ["today", "اليوم"]

FIELD_ORDER = ("target_country", "intent", "budget_usd", "timeline")


def _prepare(table: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: [normalize(word) for word in words] for key, words in table.items()}


_COUNTRIES = _prepare(COUNTRY_KEYWORDS)
_INTENTS = _prepare(INTENT_KEYWORDS)
_TIMELINES = _prepare(TIMELINE_KEYWORDS)
_IDENTITY = [normalize(phrase) for phrase in IDENTITY_PHRASES]
_THANKS = [normalize(word) for word in THANKS_WORDS]
_OTHER_SLOTS = [normalize(phrase) for phrase in OTHER_SLOT_PHRASES]
_ORDINAL_WORDS = [([normalize(word) for word in words], index) for words, index in ORDINAL_WORDS]
_WEEKDAYS = [[normalize(word) for word in words] for words in WEEKDAY_WORDS]
_TOMORROW = [normalize(word) for word in TOMORROW_WORDS]
_TODAY = [normalize(word) for word in TODAY_WORDS]
_NAME_STOP = {normalize(word) for word in NAME_STOP_WORDS}


def _first_match(normalized_text: str, table: dict[str, list[str]]) -> Optional[str]:
    for key, words in table.items():
        if any(contains_keyword(normalized_text, word) for word in words):
            return key
    return None


def _any_keyword(normalized_text: str, words: list[str]) -> bool:
    return any(contains_keyword(normalized_text, word) for word in words)


def detect_country(text: str) -> Optional[str]:
    return _first_match(normalize(text), _COUNTRIES)


def detect_intent(text: str) -> Optional[str]:
    return _first_match(normalize(text), _INTENTS)


def detect_timeline(text: str) -> Optional[str]:
    normalized = normalize(text)
    match = MONTHS_RE.search(normalized) or MONTHS_AR_RE.search(normalized)
    if match:
        raw = match.group(1)
        count = int(raw) if raw.isdigit() else WORD_NUMBERS[raw]
        return "3_MONTHS" if count <= 3 else "OFF_PLAN"
    return _first_match(normalized, _TIMELINES)


def _currency_code(word: Optional[str], country: Optional[str]) -> tuple[str, bool]:
    if word:
        if word in RIYAL_WORDS and country == "QATAR":
            return "QAR", False
        return CURRENCY_WORDS[word], False
    return config.COUNTRY_CURRENCY.get(country or "", "USD"), True


def parse_budget(text: str, country: Optional[str] = None) -> Optional[tuple[float, str, bool]]:
    normalized = normalize(text)
    for match in AMOUNT_RE.finditer(normalized):
        if NON_BUDGET_TAIL_RE.match(normalized[match.end():match.end() + 10]):
            continue
        multiplier = match.group("mult")
        currency_word = match.group("cur") or match.group("prefix")
        number = float(match.group("num").replace(",", ""))
        if multiplier is None and currency_word is None:
            if not MIN_PLAIN_BUDGET <= number <= MAX_PLAIN_BUDGET:
                continue
        value = number * MULTIPLIERS.get(multiplier or "", 1)
        code, assumed = _currency_code(currency_word, country)
        return round(value * config.USD_RATES[code], 2), code, assumed
    word_match = WORD_AMOUNT_RE.search(normalized)
    if word_match:
        value = 2_000_000 if word_match.group("word") == "مليونين" else 1_000_000
        code, assumed = _currency_code(word_match.group("cur"), country)
        return round(value * config.USD_RATES[code], 2), code, assumed
    return None


def extract_fields(text: str, current_country: Optional[str] = None) -> dict[str, Any]:
    country = detect_country(text)
    budget = parse_budget(text, country or current_country)
    return {
        "target_country": country,
        "intent": detect_intent(text),
        "budget_usd": budget[0] if budget else None,
        "budget_assumed_currency": budget[1] if budget and budget[2] else None,
        "timeline": detect_timeline(text),
    }


def next_missing(state: dict[str, Any]) -> Optional[str]:
    for key in FIELD_ORDER:
        if state.get(key) is None:
            return key
    return None


def _clean_name(raw: str) -> Optional[str]:
    words: list[str] = []
    for word in raw.split():
        if normalize(word) in _NAME_STOP:
            break
        cleaned = word.strip(".'-")
        if cleaned:
            words.append(cleaned)
        if len(words) == 3:
            break
    if not words:
        return None
    name = " ".join(words)
    return name.title() if name.isascii() else name


def extract_name(text: str, plain_allowed: bool) -> Optional[str]:
    match = NAME_PREFIX_RE.search(text)
    if match:
        return _clean_name(match.group("name"))
    if not plain_allowed:
        return None
    candidate = text.strip(" .!?؟،,")
    if not PLAIN_NAME_RE.match(candidate):
        return None
    return _clean_name(candidate)


def is_question(text: str) -> bool:
    if "?" in text or "؟" in text:
        return True
    tokens = WORD_RE.findall(normalize(text))
    if not tokens:
        return False
    return tokens[0] in QUESTION_WORDS or any(token in ANYWHERE_QUESTION_WORDS for token in tokens)


def is_identity_question(text: str) -> bool:
    normalized = normalize(text)
    return any(phrase in normalized for phrase in _IDENTITY)


def is_thanks(text: str) -> bool:
    return _any_keyword(normalize(text), _THANKS)


def wants_other_slots(text: str) -> bool:
    return _any_keyword(normalize(text), _OTHER_SLOTS)


def _parse_time(normalized_text: str) -> Optional[tuple[int, int]]:
    match = TIME_12H_RE.search(normalized_text)
    if match:
        hour = int(match.group(1)) % 12
        minute = int(match.group(2) or 0)
        if match.group(3) in ("pm", "م"):
            hour += 12
        return hour, minute
    match = TIME_24H_RE.search(normalized_text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def _day_matches(normalized_text: str, slot: datetime, now: datetime) -> bool:
    if _any_keyword(normalized_text, _WEEKDAYS[slot.weekday()]):
        return True
    if _any_keyword(normalized_text, _TOMORROW) and slot.date() == (now + timedelta(days=1)).date():
        return True
    return _any_keyword(normalized_text, _TODAY) and slot.date() == now.date()


def parse_slot_choice(text: str, slot_isos: list[str], now: Optional[datetime] = None) -> Optional[int]:
    normalized = normalize(text)
    now = (now or datetime.now(config.CALENDAR_TZ)).astimezone(config.CALENDAR_TZ)
    slots = [datetime.fromisoformat(iso).astimezone(config.CALENDAR_TZ) for iso in slot_isos]
    ordinal = ORDINAL_RE.match(normalized)
    if ordinal:
        index = int(ordinal.group(1)) - 1
        return index if index < len(slots) else None
    candidates = list(range(len(slots)))
    day_hits = [index for index in candidates if _day_matches(normalized, slots[index], now)]
    if day_hits:
        candidates = day_hits
    time_value = _parse_time(normalized)
    if time_value:
        candidates = [index for index in candidates if (slots[index].hour, slots[index].minute) == time_value]
    if (day_hits or time_value) and len(candidates) == 1:
        return candidates[0]
    for words, index in _ORDINAL_WORDS:
        if index < len(slots) and _any_keyword(normalized, words):
            return index
    return None
