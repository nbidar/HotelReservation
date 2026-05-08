from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ReservationRequest:
    guest_name: str
    room_type: str
    start_date: date
    end_date: date


CHECK_ROOM_NUMBERS_BY_TYPE = "SELECT room_number FROM rooms WHERE room_type = ?"

CHECK_OVERLAPPING_RESERVATIONS = """
SELECT *
FROM reservations
WHERE room_number = ?
  AND (start_date < ? AND end_date > ?)
""".strip()


LIST_ROOMS = "SELECT room_number, room_type, price, max_capacity, amenities FROM rooms ORDER BY room_number"

LIST_RESERVATIONS = """
SELECT reservation_id, guest_name, room_number, start_date, end_date
FROM reservations
ORDER BY start_date DESC
""".strip()

