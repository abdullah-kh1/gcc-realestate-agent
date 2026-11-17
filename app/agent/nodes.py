from datetime import datetime
from typing import Any

from app import config
from app.agent import extractor, responses
from app.agent.graph import END
from app.agent.language import detect_language
from app.tools import calendar as calendar_tool
from app.tools import knowledge

State = dict[str, Any]


def _timestamp() -> str:
    return datetime.now(config.CALENDAR_TZ).isoformat(timespec="seconds")


def _record(state: State, role: str, content: str) -> None:
    state["messages"].append({"role": role, "content": content, "at": _timestamp()})


def _resume(state: State) -> str:
    language = state["language"]
    if state["awaiting"] == "slot_choice" and state["offered_slots"]:
        return responses.slot_prompt(state)
    if state["booking_status"] == "BOOKED":
        return ""
    missing = extractor.next_missing(state)
    if missing:
        return responses.question(missing, language)
    state["is_qualified"] = True
    if not state["lead_name"]:
        state["awaiting"] = "name"
        return responses.ask_name(language)
    return ""


def _join(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


async def ingest(state: State) -> str:
    text = state["incoming"]
    state["language"] = detect_language(text, state["language"])
    state["turns"] += 1
    state["new_fields"] = []
    state["reply"] = ""
    _record(state, "user", text)
    return "extract"


async def extract(state: State) -> str:
    text = state["incoming"]
    faq_like = extractor.is_question(text) and knowledge.detect_topic(text) is not None
    found = extractor.extract_fields(text, state["target_country"])
    had_fields = any(found[key] is not None for key in extractor.FIELD_ORDER)
    if faq_like:
        found = {
            key: (value if key == "target_country" and state["target_country"] is None else None)
            for key, value in found.items()
        }
    for key in extractor.FIELD_ORDER:
        value = found.get(key)
        if value is not None and state[key] != value:
            state[key] = value
            state["new_fields"].append(key)
            if key == "budget_usd":
                state["budget_assumed_currency"] = found.get("budget_assumed_currency")
    name = extractor.extract_name(text, plain_allowed=state["awaiting"] == "name" and not had_fields and not faq_like)
    if name:
        state["lead_name"] = name
        if state["awaiting"] == "name":
            state["awaiting"] = None
    return "dispatch"


async def dispatch(state: State) -> str:
    text = state["incoming"]
    if extractor.is_identity_question(text):
        return "identity"
    topic = knowledge.detect_topic(text) if extractor.is_question(text) else None
    if topic:
        state["pending_topic"] = topic
        return "faq"
    if state["pending_topic"] and "target_country" in state["new_fields"]:
        return "faq"
    if state["awaiting"] == "slot_choice" and state["offered_slots"]:
        return "choose_slot"
    if state["booking_status"] == "BOOKED":
        return "post_booking"
    return "qualify"


async def identity(state: State) -> str:
    state["reply"] = _join(responses.identity(state["language"]), _resume(state))
    return "finish"


async def faq(state: State) -> str:
    language = state["language"]
    country = extractor.detect_country(state["incoming"]) or state["target_country"]
    if country is None:
        state["reply"] = responses.faq_ask_country(language)
        return "finish"
    answer = knowledge.answer(country, state["pending_topic"], language)
    state["pending_topic"] = None
    if answer is None:
        answer = responses.faq_fallback(country, language)
    state["reply"] = _join(answer, _resume(state))
    return "finish"


async def qualify(state: State) -> str:
    missing = extractor.next_missing(state)
    if missing:
        state["reply"] = responses.qualification(state, missing)
        return "finish"
    state["is_qualified"] = True
    if not state["lead_name"]:
        state["awaiting"] = "name"
        state["reply"] = responses.name_request(state)
        return "finish"
    return "offer_slots"


async def offer_slots(state: State) -> str:
    options = await calendar_tool.get_slot_options(
        config.OWNER_ID, config.CALENDAR_TZ_NAME, state["slot_round"], state["language"]
    )
    if not options:
        state["awaiting"] = None
        state["offered_slots"] = []
        state["reply"] = responses.no_slots(state["language"])
        return "finish"
    state["offered_slots"] = [{"iso": option["iso"]} for option in options]
    state["booking_status"] = "SLOTS_OFFERED"
    state["awaiting"] = "slot_choice"
    state["reply"] = responses.offer_slots(state)
    state["slot_note"] = ""
    return "finish"


async def choose_slot(state: State) -> str:
    text = state["incoming"]
    if extractor.wants_other_slots(text):
        state["slot_round"] += 1
        state["slot_note"] = "other"
        return "offer_slots"
    index = extractor.parse_slot_choice(text, [slot["iso"] for slot in state["offered_slots"]])
    if index is None:
        state["reply"] = responses.slot_unclear(state)
        return "finish"
    slot_iso = state["offered_slots"][index]["iso"]
    reference = await calendar_tool.create_calendar_event(
        state["phone_number"], state["lead_name"] or "Guest", slot_iso
    )
    if reference is None:
        state["slot_note"] = "taken"
        return "offer_slots"
    state["selected_slot"] = slot_iso
    state["booking_reference"] = reference
    state["booking_status"] = "BOOKED"
    state["awaiting"] = None
    state["offered_slots"] = []
    state["reply"] = responses.confirmation(state)
    return "finish"


async def post_booking(state: State) -> str:
    if extractor.is_thanks(state["incoming"]):
        state["reply"] = responses.thanks_booked(state)
    else:
        state["reply"] = responses.booked_reminder(state)
    return "finish"


async def finish(state: State) -> str:
    _record(state, "assistant", state["reply"])
    return END
