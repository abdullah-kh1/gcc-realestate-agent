import asyncio
from typing import Any

from app import config, store
from app.agent import responses
from app.agent.pipeline import agent
from app.agent.state import new_state
from app.tools import calendar as calendar_tool

PREVIEW_LENGTH = 60


class ConversationService:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock_for(self, phone: str) -> asyncio.Lock:
        return self._locks.setdefault(phone, asyncio.Lock())

    async def handle_message(self, phone: str, text: str) -> dict[str, Any]:
        async with self._lock_for(phone):
            state = store.load_state(phone) or new_state(phone)
            state["incoming"] = text
            state = await agent.ainvoke(state)
            state["messages"] = state["messages"][-config.MAX_STORED_MESSAGES:]
            store.save_state(state)
            return state

    def create_conversation(self, phone: str) -> dict[str, Any]:
        state = new_state(phone)
        store.save_state(state)
        return state


def _shorten(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= PREVIEW_LENGTH else text[: PREVIEW_LENGTH - 1] + "…"


def _status(state: dict[str, Any]) -> str:
    if state["booking_status"] == "BOOKED":
        return "booked"
    if state["is_qualified"]:
        return "qualified"
    return "active" if state["messages"] else "new"


def _title(state: dict[str, Any]) -> str:
    if state["lead_name"]:
        return state["lead_name"]
    for message in state["messages"]:
        if message["role"] == "user":
            return _shorten(message["content"])
    return "New conversation"


def profile_view(state: dict[str, Any]) -> dict[str, Any]:
    country = state["target_country"]
    intent = state["intent"]
    timeline = state["timeline"]
    budget = state["budget_usd"]
    profile = {
        "market": responses.COUNTRY_NAMES[country]["en"] if country else None,
        "purpose": responses.INTENT_NAMES[intent]["en"] if intent else None,
        "budget": responses.format_budget(budget) if budget is not None else None,
        "timeline": responses.TIMELINE_NAMES[timeline]["en"] if timeline else None,
    }
    completed = sum(1 for value in profile.values() if value)
    profile["name"] = state["lead_name"]
    profile["completed"] = completed
    profile["qualified"] = state["is_qualified"]
    return profile


def booking_view(state: dict[str, Any]) -> dict[str, Any]:
    selected = state["selected_slot"]
    return {
        "status": state["booking_status"],
        "label": calendar_tool.format_label(selected, "en") if selected else None,
        "reference": state["booking_reference"],
    }


def conversation_view(state: dict[str, Any]) -> dict[str, Any]:
    language = state["language"]
    return {
        "id": state["phone_number"],
        "title": _title(state),
        "status": _status(state),
        "language": language,
        "messages": state["messages"],
        "profile": profile_view(state),
        "booking": booking_view(state),
        "awaiting": state["awaiting"],
        "slots": [
            {"index": index, "label": calendar_tool.format_label(slot["iso"], language)}
            for index, slot in enumerate(state["offered_slots"], start=1)
        ],
    }


def conversation_summary(state: dict[str, Any], updated_at: str) -> dict[str, Any]:
    last = state["messages"][-1]["content"] if state["messages"] else "No messages yet"
    return {
        "id": state["phone_number"],
        "title": _title(state),
        "preview": _shorten(last),
        "status": _status(state),
        "updated_at": updated_at,
    }


def bookings_view() -> list[dict[str, Any]]:
    return [
        {
            "reference": booking["reference"],
            "name": booking["name"],
            "phone": booking["phone"],
            "slot_iso": booking["slot_iso"],
            "label": calendar_tool.format_label(booking["slot_iso"], "en"),
        }
        for booking in store.list_bookings()
    ]


service = ConversationService()
