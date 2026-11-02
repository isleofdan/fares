"""Probe: does Google Flights (keyless, through the fast-flights package) answer from this machine?

Runs one round-trip query per route and cabin for one date pair, then repeats one
query several times to see whether repeated queries get blocked. Prints timings,
row counts and a sample row. Run: .venv/bin/python tools/probe_google_flights.py
"""

import sys
import time

from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html
from fast_flights.parser import parse

DEPART = sys.argv[1] if len(sys.argv) > 1 else "2026-12-07"
RETURN = sys.argv[2] if len(sys.argv) > 2 else "2026-12-14"
DESTS = ["IAH", "DTW", "TLV", "BCN"]


def query(dest, cabin, origin="TYO"):
    q = create_query(
        flights=[
            FlightQuery(date=DEPART, from_airport=origin, to_airport=dest),
            FlightQuery(date=RETURN, from_airport=dest, to_airport=origin),
        ],
        seat=cabin,
        trip="round-trip",
        passengers=Passengers(adults=1),
        language="en-US",
        currency="USD",
    )
    t0 = time.monotonic()
    html = fetch_flights_html(q)
    dt = time.monotonic() - t0
    try:
        rows = parse(html)
    except Exception as e:  # noqa: BLE001 - a probe reports every failure
        return dt, len(html), None, f"{type(e).__name__}: {e}"
    return dt, len(html), rows, None


for dest in DESTS:
    for cabin in ("business", "first"):
        dt, size, rows, err = query(dest, cabin)
        n = None if rows is None else len(rows)
        print(f"TYO-{dest} {cabin}: {dt:.2f}s html={size}B rows={n} err={err}")
        if rows:
            r = rows[0]
            legs = " ".join(f"{s.from_airport.code}-{s.to_airport.code}" for s in r.flights)
            print(f"   sample: price={r.price} type={r.type} airlines={r.airlines} legs={legs}")

print("repeat test: TYO-TLV business x10")
for i in range(10):
    dt, size, rows, err = query("TLV", "business")
    print(f"  {i}: {dt:.2f}s rows={None if rows is None else len(rows)} err={err}")
