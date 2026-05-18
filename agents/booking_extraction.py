from __future__ import annotations

from datetime import date
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from utils.prompts import BOOKING_EXTRACTION_PROMPT
from dotenv import load_dotenv
load_dotenv()


class BookingExtraction(BaseModel):
    """Structured fields extracted from the guest conversation."""

    intent: Literal[
        "book",
        "check_availability",
        "list_room_types",
        "provide_guest_name",
        "change_dates",
        "change_room_type",
        "cancel_booking_intent",
        "unrelated",
    ] = Field(
        description=(
            "Primary intent for this turn. Use 'book' when the guest wants to reserve a room. "
            "Use 'provide_guest_name' when they only supply a name after availability was discussed. "
            "Use 'check_availability' when they ask what is free without committing to book yet."
        )
    )
    start_date: date | None = Field(
        default=None,
        description="Check-in date (inclusive), ISO YYYY-MM-DD. Null if not stated or inferable.",
    )
    end_date: date | None = Field(
        default=None,
        description="Check-out date (exclusive), ISO YYYY-MM-DD. Null if not stated or inferable.",
    )
    room_type: str | None = Field(
        default=None,
        description=(
            "Requested room category exactly as the guest said it (e.g. Single, Double, Family Suite). "
            "Null if they want any room or did not specify a type."
        ),
    )
    guest_name: str | None = Field(
        default=None,
        description="Full name for the reservation when explicitly given. Null if not provided.",
    )
    room_number: int | None = Field(
        default=None,
        description="Specific room number when the guest requests it (e.g. 104). Null if not specified.",
    )
    notes: str = Field(
        default="",
        description="Brief internal note: ambiguities, assumptions, or missing fields (not shown to guest).",
    )


def _format_prior_context(booking_context: dict | None, today: str, room_types: list[str]) -> str:
    ctx = booking_context or {}
    lines = [
        f"Today's date: {today}",
        f"Canonical room types in the hotel: {', '.join(room_types)}",
        "Prior booking context accumulated from earlier turns:",
    ]
    for key in ("start_date", "end_date", "room_type", "room_number", "guest_name", "pending_step"):
        val = ctx.get(key)
        if val:
            lines.append(f"  - {key}: {val}")
    if len(lines) == 3:
        lines.append("  (none yet)")
    return "\n".join(lines)


def extract_booking_fields(
    llm: ChatOpenAI,
    messages: list[BaseMessage],
    *,
    booking_context: dict | None,
    today: date,
    room_types: list[str],) -> BookingExtraction:
    """
    LLM-only structured extraction (no regex). Merges conversation + prior context.
    """
    human_lines: list[str] = []
    for m in messages:
        role = getattr(m, "type", None) or ""
        content = (getattr(m, "content", None) or "").strip()
        if not content:
            continue
        if role in ("human", "user") or isinstance(m, HumanMessage):
            human_lines.append(f"Guest: {content}")
        elif role in ("ai", "assistant"):
            human_lines.append(f"Assistant: {content}")

    conversation = "\n".join(human_lines[-20:]) or "(no messages)"
    context_block = _format_prior_context(booking_context, today.isoformat(), room_types)

    system = SystemMessage(content=BOOKING_EXTRACTION_PROMPT)
    user = HumanMessage(
        content=(
            f"{context_block}\n\n"
            "--- Conversation (most recent last) ---\n"
            f"{conversation}\n\n"
            "Extract booking fields for the latest guest intent."
        )
    )

    extractor = llm.with_structured_output(BookingExtraction)
    return extractor.invoke([system, user])
