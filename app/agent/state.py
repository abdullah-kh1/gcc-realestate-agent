from typing import Any, Optional, TypedDict


class GCCRealEstateState(TypedDict):
    phone_number: str
    language: str
    target_country: Optional[str]
    intent: Optional[str]
    budget_usd: Optional[float]
    budget_assumed_currency: Optional[str]
    timeline: Optional[str]
    messages: list[dict[str, Any]]
    is_qualified: bool
    booking_status: str
    selected_slot: Optional[str]
    booking_reference: Optional[str]
    lead_name: Optional[str]
    awaiting: Optional[str]
    offered_slots: list[dict[str, str]]
    slot_round: int
    slot_note: str
    pending_topic: Optional[str]
    incoming: str
    reply: str
    new_fields: list[str]
    turns: int


def new_state(phone_number: str) -> GCCRealEstateState:
    return {
        "phone_number": phone_number,
        "language": "en",
        "target_country": None,
        "intent": None,
        "budget_usd": None,
        "budget_assumed_currency": None,
        "timeline": None,
        "messages": [],
        "is_qualified": False,
        "booking_status": "NONE",
        "selected_slot": None,
        "booking_reference": None,
        "lead_name": None,
        "awaiting": None,
        "offered_slots": [],
        "slot_round": 0,
        "slot_note": "",
        "pending_topic": None,
        "incoming": "",
        "reply": "",
        "new_fields": [],
        "turns": 0,
    }
