from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from database.db import connect, query_all
from database.queries import AVAILABLE_ROOMS_SQL, INSERT_RESERVATION_SQL, LIST_ROOM_TYPES_SQL


@dataclass(frozen=True)
class RoomRow:
    room_number: int
    room_type: str
    price: float
    max_capacity: int
    amenities: str


@dataclass(frozen=True)
class BookingResult:
    reservation_id: int
    guest_name: str
    room_number: int
    room_type: str
    start_date: date
    end_date: date
    price: float


def list_room_types(db_path: Path) -> list[str]:
    conn = connect(db_path)
    try:
        rows = query_all(conn, LIST_ROOM_TYPES_SQL)
        return [r[0] for r in rows]
    finally:
        conn.close()


def get_available_rooms(
    db_path: Path,
    start_date: date,
    end_date: date,
    room_type: str | None = None,
) -> list[RoomRow]:
    if end_date <= start_date:
        raise ValueError("end_date must be after start_date")

    conn = connect(db_path)
    try:
        rows = query_all(
            conn,
            AVAILABLE_ROOMS_SQL,
            (room_type, room_type, end_date.isoformat(), start_date.isoformat()),
        )
        return [
            RoomRow(
                room_number=int(r[0]),
                room_type=str(r[1]),
                price=float(r[2]),
                max_capacity=int(r[3]),
                amenities=str(r[4] or ""),
            )
            for r in rows
        ]
    finally:
        conn.close()


def book_room(
    db_path: Path,
    guest_name: str,
    start_date: date,
    end_date: date,
    room_type: str,
) -> BookingResult:
    available = get_available_rooms(db_path, start_date, end_date, room_type=room_type)
    if not available:
        raise ValueError(f"No {room_type} room available for the requested dates.")

    room = available[0]
    conn = connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            INSERT_RESERVATION_SQL,
            (guest_name.strip(), room.room_number, start_date.isoformat(), end_date.isoformat()),
        )
        reservation_id = int(cur.lastrowid)
        conn.commit()
    finally:
        conn.close()

    return BookingResult(
        reservation_id=reservation_id,
        guest_name=guest_name.strip(),
        room_number=room.room_number,
        room_type=room.room_type,
        start_date=start_date,
        end_date=end_date,
        price=room.price,
    )


def book_room_by_number(
    db_path: Path,
    guest_name: str,
    start_date: date,
    end_date: date,
    room_number: int,) -> BookingResult:
    available = get_available_rooms(db_path, start_date, end_date, room_type=None)
    room = next((r for r in available if r.room_number == room_number), None)
    if room is None:
        raise ValueError(f"Room {room_number} is not available for the requested dates.")

    conn = connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            INSERT_RESERVATION_SQL,
            (guest_name.strip(), room.room_number, start_date.isoformat(), end_date.isoformat()),
        )
        reservation_id = int(cur.lastrowid)
        conn.commit()
    finally:
        conn.close()

    return BookingResult(
        reservation_id=reservation_id,
        guest_name=guest_name.strip(),
        room_number=room.room_number,
        room_type=room.room_type,
        start_date=start_date,
        end_date=end_date,
        price=room.price,
    )


def normalize_room_type(requested: str | None, canonical_types: list[str]) -> str | None:
    if not requested or not str(requested).strip():
        return None
    raw = str(requested).strip()
    lower_map = {t.lower(): t for t in canonical_types}
    if raw.lower() in lower_map:
        return lower_map[raw.lower()]
    collapsed = raw.lower().replace("-", " ").replace("_", " ")
    for canonical in canonical_types:
        if canonical.lower() == collapsed:
            return canonical
    for canonical in canonical_types:
        if canonical.lower() in collapsed or collapsed in canonical.lower():
            return canonical
    return raw
