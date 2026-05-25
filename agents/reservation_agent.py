from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.booking_extraction import BookingExtraction, extract_booking_fields
from database.booking import (
    BookingResult,
    RoomRow,
    book_room,
    book_room_by_number,
    get_available_rooms,
    list_room_types,
    normalize_room_type,
)
from utils.prompts import BOOKING_RESPONSE_PROMPT
from workflows.state import AppState

_ROOM_NUMBER_RE = re.compile(r"\b(?:room\s*#?\s*)?(\d{3})\b", re.IGNORECASE)
_NEW_BOOKING_INTENTS = {
    "book",
    "check_availability",
    "list_room_types",
    "provide_guest_name",
    "change_dates",
    "change_room_type",
}


def _latest_human_text(messages) -> str:
    for message in reversed(messages):
        role = getattr(message, "type", None)
        if role in ("human", "user") or isinstance(message, HumanMessage):
            content = (getattr(message, "content", None) or "").strip()
            if content:
                return content
    return ""


def _parse_room_number(text: str) -> int | None:
    match = _ROOM_NUMBER_RE.search(text or "")
    if not match:
        return None
    number = int(match.group(1))
    return number if 100 <= number <= 999 else None


def _merge_context(
    prior: dict[str, Any] | None,
    extracted: BookingExtraction,
    canonical_types: list[str],
) -> dict[str, Any]:
    ctx: dict[str, Any] = dict(prior or {})

    if extracted.start_date:
        ctx["start_date"] = extracted.start_date.isoformat()
    if extracted.end_date:
        ctx["end_date"] = extracted.end_date.isoformat()
    if extracted.room_type:
        ctx["room_type"] = normalize_room_type(extracted.room_type, canonical_types) or extracted.room_type
    if extracted.guest_name:
        ctx["guest_name"] = extracted.guest_name.strip()
    if extracted.room_number is not None:
        ctx["room_number"] = int(extracted.room_number)

    if extracted.intent == "cancel_booking_intent":
        return {}

    return ctx


def _normalize_booking_store(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = dict(raw or {})
    if "active_booking" in raw or "completed_bookings" in raw:
        return {
            "active_booking": dict(raw.get("active_booking") or {}),
            "completed_bookings": list(raw.get("completed_bookings") or []),
        }

    legacy = dict(raw)
    completed = []
    if legacy.get("pending_step") == "confirmed" and legacy.get("last_reservation_id") is not None:
        completed.append(
            {
                "reservation_id": legacy.get("last_reservation_id"),
                "guest_name": legacy.get("guest_name"),
                "room_number": legacy.get("room_number"),
                "room_type": legacy.get("room_type"),
                "start_date": legacy.get("start_date"),
                "end_date": legacy.get("end_date"),
            }
        )
    return {"active_booking": legacy, "completed_bookings": completed}


def _booking_summary(ctx: dict[str, Any]) -> dict[str, Any]:
    return {
        "reservation_id": ctx.get("last_reservation_id"),
        "guest_name": ctx.get("guest_name"),
        "room_number": ctx.get("room_number"),
        "room_type": ctx.get("room_type"),
        "start_date": ctx.get("start_date"),
        "end_date": ctx.get("end_date"),
    }


def _should_start_new_booking(store: dict[str, Any], extracted: BookingExtraction) -> bool:
    active = dict(store.get("active_booking") or {})
    if not active:
        return False

    if extracted.booking_scope == "start_new":
        return True

    if extracted.intent == "cancel_booking_intent":
        return True

    active_status = active.get("pending_step")
    if active_status == "confirmed" and extracted.intent in _NEW_BOOKING_INTENTS:
        return extracted.booking_scope != "continue_current"

    return False


def _update_booking_store(
    store: dict[str, Any],
    ctx: dict[str, Any],
    facts: dict[str, Any],
) -> dict[str, Any]:
    updated = {
        "active_booking": dict(ctx or {}),
        "completed_bookings": list(store.get("completed_bookings") or []),
    }

    if facts.get("booking_confirmed"):
        summary = _booking_summary(ctx)
        reservation_id = summary.get("reservation_id")
        if reservation_id is not None and not any(
            item.get("reservation_id") == reservation_id for item in updated["completed_bookings"]
        ):
            updated["completed_bookings"].append(summary)

    return updated


def _parse_ctx_date(ctx: dict[str, Any], key: str) -> date | None:
    raw = ctx.get(key)
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return None


def _format_room_list(rooms: list[RoomRow]) -> list[dict[str, Any]]:
    return [
        {
            "room_number": r.room_number,
            "room_type": r.room_type,
            "price_per_night": r.price,
            "max_capacity": r.max_capacity,
            "amenities": r.amenities,
        }
        for r in rooms
    ]


def _compose_facts(
    *,
    outcome: str,
    start: date | None = None,
    end: date | None = None,
    requested_type: str | None = None,
    available_rooms: list[RoomRow] | None = None,
    ask_guest_name: bool = False,
    booking: BookingResult | None = None,
    error_message: str | None = None,
    missing_fields: list[str] | None = None,
) -> dict[str, Any]:
    facts: dict[str, Any] = {
        "outcome": outcome,
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "requested_room_type": requested_type,
        "ask_guest_name": ask_guest_name,
        "booking_confirmed": booking is not None,
        "error_message": error_message,
        "missing_fields": missing_fields or [],
        "list_available_rooms": _format_room_list(available_rooms or []),
    }
    if booking:
        facts["reservation"] = {
            "reservation_id": booking.reservation_id,
            "guest_name": booking.guest_name,
            "room_number": booking.room_number,
            "room_type": booking.room_type,
            "start_date": booking.start_date.isoformat(),
            "end_date": booking.end_date.isoformat(),
            "price_per_night": booking.price,
        }
    return facts


def _render_response(llm, facts: dict[str, Any]) -> AIMessage:
    system = SystemMessage(content=BOOKING_RESPONSE_PROMPT)
    user = HumanMessage(content=f"facts = {json.dumps(facts, indent=2)}")
    response = llm.invoke([system, user])
    return AIMessage(content=str(response.content).strip())


def _run_booking_logic(
    db_path: Path,
    ctx: dict[str, Any],
    extracted: BookingExtraction,
    today: date,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Deterministic availability + booking. Returns (updated_context, facts).
    """
    canonical = list_room_types(db_path)
    start = _parse_ctx_date(ctx, "start_date")
    end = _parse_ctx_date(ctx, "end_date")
    room_type = ctx.get("room_type")
    if room_type:
        room_type = normalize_room_type(str(room_type), canonical)
        ctx["room_type"] = room_type
    guest_name = (ctx.get("guest_name") or "").strip() or None
    preferred_room = ctx.get("room_number")
    if preferred_room is not None:
        try:
            preferred_room = int(preferred_room)
        except (TypeError, ValueError):
            preferred_room = None

    if extracted.intent == "list_room_types":
        facts = _compose_facts(outcome="list_room_types")
        facts["canonical_room_types"] = canonical
        return ctx, facts

    if extracted.intent == "unrelated":
        return ctx, _compose_facts(
            outcome="unrelated",
            error_message="This assistant only handles room availability and reservations.",
        )

    missing: list[str] = []
    if not start:
        missing.append("check-in date")
    if not end:
        missing.append("check-out date")
    if missing:
        return ctx, _compose_facts(
            outcome="need_dates",
            start=start,
            end=end,
            requested_type=room_type,
            missing_fields=missing,
            error_message="Please provide both check-in and check-out dates.",
        )

    if end <= start:
        return ctx, _compose_facts(
            outcome="invalid_dates",
            start=start,
            end=end,
            error_message="Check-out must be after check-in.",
        )

    if start < today:
        return ctx, _compose_facts(
            outcome="past_dates",
            start=start,
            end=end,
            error_message="Reservation dates cannot be in the past.",
        )

    all_available = get_available_rooms(db_path, start, end, room_type=None)

    if not all_available:
        return (
            {**ctx, "pending_step": "none"},
            _compose_facts(
                outcome="fully_booked",
                start=start,
                end=end,
                requested_type=room_type,
                available_rooms=[],
                error_message="There is no room available for those dates.",
            ),
        )

    if room_type:
        typed_available = get_available_rooms(db_path, start, end, room_type=room_type)
        if not typed_available:
            return (
                {**ctx, "pending_step": "await_room_type_or_dates"},
                _compose_facts(
                    outcome="room_type_unavailable",
                    start=start,
                    end=end,
                    requested_type=room_type,
                    available_rooms=all_available,
                    error_message=f"{room_type} is not available for those dates.",
                ),
            )
        available_for_booking = typed_available
    else:
        available_for_booking = all_available

    if not guest_name:
        return (
            {**ctx, "pending_step": "await_guest_name"},
            _compose_facts(
                outcome="available_ask_name",
                start=start,
                end=end,
                requested_type=room_type,
                available_rooms=available_for_booking,
                ask_guest_name=True,
            ),
        )

    try:
        if preferred_room is not None:
            booking = book_room_by_number(db_path, guest_name, start, end, preferred_room)
        else:
            chosen_type = room_type or available_for_booking[0].room_type
            booking = book_room(db_path, guest_name, start, end, chosen_type)
    except ValueError as exc:
        return (
            ctx,
            _compose_facts(
                outcome="booking_failed",
                start=start,
                end=end,
                requested_type=room_type,
                available_rooms=available_for_booking,
                error_message=str(exc),
            ),
        )

    return (
        {
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "room_type": booking.room_type,
            "room_number": booking.room_number,
            "guest_name": booking.guest_name,
            "pending_step": "confirmed",
            "last_reservation_id": booking.reservation_id,
        },
        _compose_facts(
            outcome="booking_confirmed",
            start=start,
            end=end,
            requested_type=room_type,
            booking=booking,
        ),
    )


def reservation_node(state: AppState, llm, db_path: Path) -> AppState:
    """
    Reservation agent: LLM structured extraction + deterministic DB availability/booking.
    """
    messages = state["messages"]
    today = datetime.now().date()
    booking_store = _normalize_booking_store(state.get("booking_context"))
    prior_ctx = dict(booking_store.get("active_booking") or {})
    canonical = list_room_types(db_path)

    extracted = extract_booking_fields(
        llm,
        messages,
        booking_context=booking_store,
        today=today,
        room_types=canonical,
    )

    if _should_start_new_booking(booking_store, extracted):
        prior_ctx = {}

    last_human = _latest_human_text(messages)
    if extracted.room_number is None and last_human:
        parsed_room = _parse_room_number(last_human)
        if parsed_room is not None:
            extracted = extracted.model_copy(update={"room_number": parsed_room})

    ctx = _merge_context(prior_ctx, extracted, canonical)
    if ctx.get("room_number") is None and last_human:
        parsed_room = _parse_room_number(last_human)
        if parsed_room is not None:
            ctx["room_number"] = parsed_room
    ctx, facts = _run_booking_logic(db_path, ctx, extracted, today)
    response = _render_response(llm, facts)
    updated_store = _update_booking_store(booking_store, ctx, facts)

    return {
        "messages": [response],
        "confidence": state.get("confidence", 100),
        "last_active_agent": "reservation_assistant",
        "booking_context": updated_store,
        "sql_artifact": facts,
    }
