from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class DBPaths:
    primary: Path
    shard1: Path | None = None
    shard2: Path | None = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS rooms (
  room_number INTEGER PRIMARY KEY,
  room_type TEXT NOT NULL,
  price REAL NOT NULL,
  max_capacity INTEGER NOT NULL,
  amenities TEXT
);

CREATE TABLE IF NOT EXISTS reservations (
  reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  guest_name TEXT NOT NULL,
  room_number INTEGER NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  FOREIGN KEY (room_number) REFERENCES rooms(room_number)
);
""".strip()


ROOMS_SEED = [
    (101, "Single", 100, 1, "TV, Wi-Fi"),
    (102, "Double", 150, 2, "TV, Wi-Fi, Balcony"),
    (103, "Suite", 250, 3, "TV, Wi-Fi, Balcony, Jacuzzi"),
    (104, "Deluxe", 200, 2, "TV, Wi-Fi, Mini-bar"),
    (105, "Family Suite", 300, 4, "TV, Wi-Fi, Balcony, Kitchenette"),
    (106, "Executive Suite", 350, 2, "TV, Wi-Fi, Balcony, Jacuzzi, City View"),
    (107, "Double", 150, 2, "TV, Wi-Fi"),
    (108, "Deluxe", 200, 2, "TV, Wi-Fi, Balcony, Fireplace"),
]


RESERVATIONS_SEED = [
    ("Alice Smith", 102, "2025-03-15", "2025-03-18"),
    ("Bob Johnson", 105, "2025-04-22", "2025-04-25"),
    ("Charlie Brown", 106, "2025-06-10", "2025-06-12"),
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(str(db_path), check_same_thread=False)


def init_db(db_path: Path, seed: bool = True) -> None:
    """
    Initializes the SQLite database schema and seeds with example data.
    """
    conn = connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(SCHEMA_SQL)
        if seed:
            cur.executemany("INSERT OR IGNORE INTO rooms VALUES (?, ?, ?, ?, ?)", ROOMS_SEED)
            cur.executemany(
                "INSERT INTO reservations (guest_name, room_number, start_date, end_date) VALUES (?, ?, ?, ?)",
                RESERVATIONS_SEED,
            )
        conn.commit()
    finally:
        conn.close()


def query_all(conn: sqlite3.Connection, sql: str, params: Iterable[Any] | None = None) -> list[tuple[Any, ...]]:
    cur = conn.cursor()
    cur.execute(sql, tuple(params or ()))
    return cur.fetchall()

