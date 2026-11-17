from typing import Any

from app import config
from app.tools import calendar as calendar_tool

COUNTRY_NAMES = {
    "DUBAI": {"en": "Dubai (UAE)", "ar": "دبي"},
    "SAUDI": {"en": "Saudi Arabia", "ar": "السعودية"},
    "QATAR": {"en": "Qatar", "ar": "قطر"},
    "KUWAIT": {"en": "Kuwait", "ar": "الكويت"},
}
INTENT_NAMES = {
    "INVESTMENT": {"en": "Investment", "ar": "استثمار"},
    "PERSONAL_USE": {"en": "Personal use", "ar": "سكن شخصي"},
    "GOLDEN_VISA": {"en": "Golden Visa", "ar": "إقامة ذهبية"},
}
INTENT_PHRASES = {
    "INVESTMENT": {"en": "an investment purchase", "ar": "استثمار"},
    "PERSONAL_USE": {"en": "a home for personal use", "ar": "سكن شخصي"},
    "GOLDEN_VISA": {"en": "a Golden Visa route", "ar": "إقامة ذهبية"},
}
TIMELINE_NAMES = {
    "IMMEDIATE": {"en": "Immediate", "ar": "فوري"},
    "3_MONTHS": {"en": "Within 3 months", "ar": "خلال 3 شهور"},
    "OFF_PLAN": {"en": "Off-plan", "ar": "على الخارطة"},
}
TIMELINE_PHRASES = {
    "IMMEDIATE": {"en": "buying right away", "ar": "فوراً"},
    "3_MONTHS": {"en": "moving within about 3 months", "ar": "خلال 3 شهور تقريباً"},
    "OFF_PLAN": {"en": "an off-plan purchase", "ar": "شراء على الخارطة"},
}

GREETING = {
    "en": "Hello, and welcome to {brand}. I'll help you find the right property in the Gulf.",
    "ar": "هلا والله، حياك الله في {brand}. أقدر أساعدك تلقى العقار المناسب في الخليج.",
}
ACK_COUNTRY = {"en": "{value} is a great choice.", "ar": "{value} خيار ممتاز."}
ACK_INTENT = {"en": "Got it, {value}.", "ar": "تمام، {value}."}
ACK_BUDGET = {"en": "Noted, around {value}.", "ar": "تمام، تقريباً {value}."}
ACK_BUDGET_ASSUMED = {
    "en": "Noted, around {value}. I took it as {currency}, tell me if you meant another currency.",
    "ar": "تمام، تقريباً {value}. اعتبرتها {currency}، قلي إذا تقصد عملة ثانية.",
}
ACK_TIMELINE = {"en": "Perfect, {value}.", "ar": "ممتاز، {value}."}
ACK_MULTI = {"en": "Thanks, that helps a lot.", "ar": "شكراً، هذا يفيدني كثير."}

QUESTIONS = {
    "target_country": {
        "en": "Which market are you focused on: Dubai, Saudi Arabia, Qatar or Kuwait?",
        "ar": "أي سوق تفكر فيه: دبي، السعودية، قطر أو الكويت؟",
    },
    "intent": {
        "en": "Is this for investment, personal use, or are you after a Golden Visa?",
        "ar": "العقار للاستثمار، للسكن الشخصي، ولا تبي الإقامة الذهبية؟",
    },
    "budget_usd": {
        "en": "What budget are you working with? Any currency is fine.",
        "ar": "كم الميزانية اللي في بالك؟ تقدر تكتبها بأي عملة.",
    },
    "timeline": {
        "en": "And when are you looking to move forward: right away, within about 3 months, or off-plan for later?",
        "ar": "ومتى تبي تبدأ: فوراً، خلال 3 شهور تقريباً، ولا شراء على الخارطة لاحقاً؟",
    },
}
ASK_NAME = {
    "en": "That gives me a clear picture. May I have your name so I can arrange a call with our senior consultant?",
    "ar": "الصورة صارت واضحة عندي. ممكن اسمك عشان أرتب لك مكالمة مع المستشار؟",
}
OFFER_HEADER = {
    "": {
        "en": "Thank you, {name}. Here are the next available times for a 30-minute call:",
        "ar": "شكراً {name}. هذي أقرب المواعيد المتاحة لمكالمة مدتها 30 دقيقة:",
    },
    "other": {
        "en": "Of course, {name}. Here are some other times:",
        "ar": "أبشر {name}، هذي مواعيد ثانية:",
    },
    "taken": {
        "en": "Sorry {name}, that time was just taken. Here are updated options:",
        "ar": "عذراً {name}، هذا الموعد انحجز توه. هذي الخيارات المحدثة:",
    },
}
OFFER_FOOTER = {
    "en": "Reply with the number or the time that suits you.",
    "ar": "رد برقم الموعد أو الوقت اللي يناسبك.",
}
NO_SLOTS = {
    "en": "I can't see open times right now. Our consultant will message you shortly to arrange a call.",
    "ar": "ما أشوف مواعيد متاحة الحين. المستشار بيتواصل معك قريب عشان يرتب المكالمة.",
}
SLOT_UNCLEAR = {
    "en": "Sorry, which time works for you? Please reply 1, 2 or 3, or say none of these.",
    "ar": "عفواً، أي موعد يناسبك؟ رد بـ 1 أو 2 أو 3، أو قل ما يناسبني أي واحد.",
}
SLOT_PROMPT = {
    "en": "Here are the times again. Which one suits you?",
    "ar": "هذي المواعيد مرة ثانية. أي واحد يناسبك؟",
}
CONFIRMATION = {
    "en": "You're all set, {name}. Your call is confirmed for {label}.\nReference: {reference}\n{summary}\nIs there anything else I can help you with before then?",
    "ar": "تم يا {name}. تأكد موعد مكالمتك {label}.\nالرقم المرجعي: {reference}\n{summary}\nفيه شي ثاني أقدر أساعدك فيه قبل الموعد؟",
}
SUMMARY_PREFIX = {"en": "Noted: ", "ar": "ملخص طلبك: "}
BOOKED_REMINDER = {
    "en": "Your call is confirmed for {label} (reference {reference}). Is there anything else I can help you with?",
    "ar": "موعد مكالمتك مؤكد {label} (الرقم المرجعي {reference}). فيه شي ثاني أقدر أساعدك فيه؟",
}
THANKS_BOOKED = {
    "en": "My pleasure. We look forward to speaking with you {label}.",
    "ar": "حياك الله. نتشرف بك {label}.",
}
IDENTITY = {
    "en": "I'm the virtual assistant for the {brand} team. I can answer your questions and arrange a call with our senior property consultant, who is a real person.",
    "ar": "أنا المساعد الافتراضي لفريق {brand}. أقدر أجاوب أسئلتك وأرتب لك مكالمة مع المستشار العقاري، وهو شخص حقيقي.",
}
FAQ_ASK_COUNTRY = {
    "en": "Which country do you mean: Dubai, Saudi Arabia, Qatar or Kuwait?",
    "ar": "أي دولة تقصد: دبي، السعودية، قطر أو الكويت؟",
}
FAQ_FALLBACK = {
    "en": "I'd rather not quote you something I'm not fully sure of. I'll note it for our consultant to confirm for {country} on the call.",
    "ar": "ما أبي أعطيك معلومة مو متأكد منها 100%. بسجلها للمستشار عشان يأكدها لك عن {country} في المكالمة.",
}


def brand(language: str) -> str:
    return config.BRAND_NAME_AR if language == "ar" else config.BRAND_NAME


def format_budget(usd: float) -> str:
    return f"USD {usd:,.0f}"


def question(key: str, language: str) -> str:
    return QUESTIONS[key][language]


def ask_name(language: str) -> str:
    return ASK_NAME[language]


def acknowledgement(state: dict[str, Any]) -> str:
    fields = state["new_fields"]
    language = state["language"]
    if not fields:
        return ""
    if len(fields) > 1:
        return ACK_MULTI[language]
    key = fields[0]
    if key == "target_country":
        return ACK_COUNTRY[language].format(value=COUNTRY_NAMES[state[key]][language])
    if key == "intent":
        return ACK_INTENT[language].format(value=INTENT_PHRASES[state[key]][language])
    if key == "budget_usd":
        value = format_budget(state[key])
        currency = state["budget_assumed_currency"]
        if currency:
            return ACK_BUDGET_ASSUMED[language].format(value=value, currency=currency)
        return ACK_BUDGET[language].format(value=value)
    if key == "timeline":
        return ACK_TIMELINE[language].format(value=TIMELINE_PHRASES[state[key]][language])
    return ""


def lead_in(state: dict[str, Any]) -> list[str]:
    language = state["language"]
    parts = []
    if state["turns"] == 1:
        parts.append(GREETING[language].format(brand=brand(language)))
    acknowledged = acknowledgement(state)
    if acknowledged:
        parts.append(acknowledged)
    return parts


def qualification(state: dict[str, Any], missing: str) -> str:
    return "\n".join(lead_in(state) + [question(missing, state["language"])])


def name_request(state: dict[str, Any]) -> str:
    return "\n".join(lead_in(state) + [ask_name(state["language"])])


def slot_lines(state: dict[str, Any]) -> str:
    language = state["language"]
    return "\n".join(
        f"{index}. {calendar_tool.format_label(slot['iso'], language)}"
        for index, slot in enumerate(state["offered_slots"], start=1)
    )


def offer_slots(state: dict[str, Any]) -> str:
    language = state["language"]
    header = OFFER_HEADER[state["slot_note"]][language].format(name=state["lead_name"])
    return "\n".join([header, slot_lines(state), OFFER_FOOTER[language]])


def slot_unclear(state: dict[str, Any]) -> str:
    return "\n".join([SLOT_UNCLEAR[state["language"]], slot_lines(state)])


def slot_prompt(state: dict[str, Any]) -> str:
    return "\n".join([SLOT_PROMPT[state["language"]], slot_lines(state)])


def no_slots(language: str) -> str:
    return NO_SLOTS[language]


def profile_summary(state: dict[str, Any]) -> str:
    language = state["language"]
    parts = [
        COUNTRY_NAMES[state["target_country"]][language],
        INTENT_NAMES[state["intent"]][language],
        f"~{format_budget(state['budget_usd'])}",
        TIMELINE_NAMES[state["timeline"]][language],
    ]
    return SUMMARY_PREFIX[language] + " · ".join(parts)


def slot_label(state: dict[str, Any]) -> str:
    return calendar_tool.format_label(state["selected_slot"], state["language"])


def confirmation(state: dict[str, Any]) -> str:
    return CONFIRMATION[state["language"]].format(
        name=state["lead_name"],
        label=slot_label(state),
        reference=state["booking_reference"],
        summary=profile_summary(state),
    )


def booked_reminder(state: dict[str, Any]) -> str:
    return BOOKED_REMINDER[state["language"]].format(
        label=slot_label(state), reference=state["booking_reference"]
    )


def thanks_booked(state: dict[str, Any]) -> str:
    return THANKS_BOOKED[state["language"]].format(label=slot_label(state))


def identity(language: str) -> str:
    return IDENTITY[language].format(brand=brand(language))


def faq_ask_country(language: str) -> str:
    return FAQ_ASK_COUNTRY[language]


def faq_fallback(country: str, language: str) -> str:
    return FAQ_FALLBACK[language].format(country=COUNTRY_NAMES[country][language])
