"""The price store: one SQLite file. Rows are only ever inserted, never updated or deleted."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS sweeps (
    id            INTEGER PRIMARY KEY,
    started_at    TEXT NOT NULL,      -- UTC, ISO 8601
    finished_at   TEXT,               -- UTC; set once when the sweep ends
    source        TEXT NOT NULL,
    grid_step_days INTEGER NOT NULL,
    queries       INTEGER,
    failed_queries INTEGER,
    rows_written  INTEGER,
    throttled     INTEGER,            -- 1 if the source started refusing and the sweep stopped early
    note          TEXT
);

CREATE TABLE IF NOT EXISTS fares (
    id             INTEGER PRIMARY KEY,
    sweep_id       INTEGER NOT NULL REFERENCES sweeps(id),
    captured_at    TEXT NOT NULL,     -- UTC time the query answered
    route          TEXT NOT NULL,     -- route id from routes.json
    cabin          TEXT NOT NULL,     -- business | first
    origin_airport TEXT NOT NULL,     -- airport the outbound actually leaves from (NRT or HND)
    dest_airport   TEXT NOT NULL,
    depart_date    TEXT NOT NULL,
    return_date    TEXT NOT NULL,
    carriers       TEXT NOT NULL,     -- airline names, comma separated
    carrier_codes  TEXT NOT NULL,     -- two-letter codes of every flight, comma separated
    flight_numbers TEXT NOT NULL,     -- outbound flights, e.g. "AZ793 AZ810"
    stops          INTEGER NOT NULL,  -- outbound stops (0 = nonstop)
    via            TEXT,              -- outbound connecting airports, e.g. "FCO" or "ICN ADD"
    segment_cabins TEXT,              -- cabin of each outbound flight, e.g. "first,business"
    duration_min   INTEGER,           -- outbound total travel time
    price          INTEGER NOT NULL,  -- round-trip price, whole units of currency
    currency       TEXT NOT NULL,
    source         TEXT NOT NULL,
    fare_code      TEXT,              -- booking class / fare basis when the source gives one
    result_list    TEXT               -- the source's own grouping ("best" / "other")
);

CREATE INDEX IF NOT EXISTS fares_route_cabin ON fares(route, cabin, captured_at);

-- History only grows: refuse updates and deletes at the database level.
CREATE TRIGGER IF NOT EXISTS fares_no_update BEFORE UPDATE ON fares
BEGIN SELECT RAISE(ABORT, 'fares rows are never changed'); END;
CREATE TRIGGER IF NOT EXISTS fares_no_delete BEFORE DELETE ON fares
BEGIN SELECT RAISE(ABORT, 'fares rows are never deleted'); END;
"""

FARE_COLUMNS = (
    "sweep_id", "captured_at", "route", "cabin", "origin_airport", "dest_airport",
    "depart_date", "return_date", "carriers", "carrier_codes", "flight_numbers", "stops", "via", "segment_cabins",
    "duration_min", "price", "currency", "source", "fare_code", "result_list",
)


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Columns added after the first sweeps of 2 Nov 2026; older rows hold NULL (not recorded).
    cols = {r[1] for r in conn.execute("PRAGMA table_info(fares)")}
    for col in ("via", "segment_cabins"):
        if col not in cols:
            conn.execute(f"ALTER TABLE fares ADD COLUMN {col} TEXT")
    conn.commit()
    return conn


def start_sweep(conn, started_at: str, source: str, grid_step_days: int) -> int:
    cur = conn.execute(
        "INSERT INTO sweeps (started_at, source, grid_step_days) VALUES (?, ?, ?)",
        (started_at, source, grid_step_days),
    )
    conn.commit()
    return cur.lastrowid


def finish_sweep(conn, sweep_id, finished_at, queries, failed, rows, throttled, note):
    conn.execute(
        "UPDATE sweeps SET finished_at=?, queries=?, failed_queries=?, rows_written=?,"
        " throttled=?, note=? WHERE id=? AND finished_at IS NULL",
        (finished_at, queries, failed, rows, int(throttled), note, sweep_id),
    )
    conn.commit()


def insert_fares(conn, rows: list[dict]) -> int:
    sql = f"INSERT INTO fares ({', '.join(FARE_COLUMNS)}) VALUES ({', '.join('?' * len(FARE_COLUMNS))})"
    conn.executemany(sql, [tuple(r.get(c) for c in FARE_COLUMNS) for r in rows])
    conn.commit()
    return len(rows)
