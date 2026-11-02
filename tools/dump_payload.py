"""Debug helper: fetch one Google Flights round-trip page and save its embedded data block as JSON.

Run: .venv/bin/python tools/dump_payload.py TLV business 2026-12-07 2026-12-14 out.json
"""

import json
import sys

from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html
from selectolax.lexbor import LexborHTMLParser

dest, cabin, dep, ret, out = sys.argv[1:6]
q = create_query(
    flights=[
        FlightQuery(date=dep, from_airport="TYO", to_airport=dest),
        FlightQuery(date=ret, from_airport=dest, to_airport="TYO"),
    ],
    seat=cabin,
    trip="round-trip",
    passengers=Passengers(adults=1),
    language="en-US",
    currency="USD",
)
html = fetch_flights_html(q)
js = LexborHTMLParser(html).css_first(r"script.ds\:1").text()
data = json.loads(js.split("data:", 1)[1].rsplit(",", 1)[0])
with open(out, "w") as f:
    json.dump(data, f, indent=1)
for i, part in enumerate(data):
    print(i, type(part).__name__, len(json.dumps(part)))
