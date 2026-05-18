from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ReservationRequest:
    guest_name: str
    room_type: str
    start_date: date
    end_date: date


# Rooms blocked when an existing stay overlaps [start, end):
# existing.start_date < end AND existing.end_date > start
AVAILABLE_ROOMS_SQL = """
SELECT r.room_number, r.room_type, r.price, r.max_capacity, r.amenities
FROM rooms r
WHERE (? IS NULL OR r.room_type = ?)
  AND NOT EXISTS (
    SELECT 1
    FROM reservations res
    WHERE res.room_number = r.room_number
      AND res.start_date < ?
      AND res.end_date > ?
  )
ORDER BY r.room_type, r.room_number
""".strip()

INSERT_RESERVATION_SQL = """
INSERT INTO reservations (guest_name, room_number, start_date, end_date)
VALUES (?, ?, ?, ?)
""".strip()

LIST_ROOM_TYPES_SQL = "SELECT DISTINCT room_type FROM rooms ORDER BY room_type"

CHECK_ROOM_NUMBERS_BY_TYPE = "SELECT room_number FROM rooms WHERE room_type = ?"

CHECK_OVERLAPPING_RESERVATIONS = """
SELECT reservation_id, guest_name, start_date, end_date
FROM reservations
WHERE room_number = ?
  AND start_date < ?
  AND end_date > ?
""".strip()

LIST_ROOMS = "SELECT room_number, room_type, price, max_capacity, amenities FROM rooms ORDER BY room_number"

LIST_RESERVATIONS = """
SELECT reservation_id, guest_name, room_number, start_date, end_date
FROM reservations
ORDER BY start_date DESC
""".strip()
