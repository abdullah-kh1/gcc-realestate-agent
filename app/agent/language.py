import re

ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿ]")
LATIN_RE = re.compile(r"[A-Za-z]")
DIACRITICS_RE = re.compile(r"[ً-ٰٟـ]")
DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
LETTER_MAP = str.maketrans(
    {"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي"}
)


def detect_language(text: str, fallback: str = "en") -> str:
    arabic = len(ARABIC_RE.findall(text))
    latin = len(LATIN_RE.findall(text))
    if arabic == 0 and latin == 0:
        return fallback
    return "ar" if arabic >= latin else "en"


def normalize(text: str) -> str:
    text = text.translate(DIGIT_MAP)
    text = DIACRITICS_RE.sub("", text)
    text = text.translate(LETTER_MAP)
    return text.lower().strip()


def contains_keyword(normalized_text: str, keyword: str) -> bool:
    if keyword.isascii():
        pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None
    return keyword in normalized_text
