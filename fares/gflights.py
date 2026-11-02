"""Google Flights as a fare source, without a key.

fast-flights builds the encoded search (the `tfs` parameter) and we fetch it with the same
browser-like client it uses, so we can see the HTTP status. The page carries its results as
a JSON block in a <script class="ds:1"> tag; we read both result lists ("best" and "other")
ourselves, because fast-flights' own parser reads only the second.
"""

import json
from dataclasses import dataclass

from fast_flights import FlightQuery, Passengers, create_query
from primp import Client
from selectolax.lexbor import LexborHTMLParser

SOURCE = "Google Flights"
URL = "https://www.google.com/travel/flights"
CURRENCY = "USD"
ORIGIN = "TYO"  # Tokyo city code: Narita and Haneda
# Cabin of each flight, as the page codes it. A "first" search can return itineraries that are
# first class on the long flight and business on a connection.
CABIN_NAMES = {1: "economy", 2: "premium economy", 3: "business", 4: "first"}


class Blocked(Exception):
    """The source answered with something other than results (rate limit, consent, bot or unknown page)."""


@dataclass
class Answer:
    status: int
    itineraries: list[dict]


_client = None


def _get_client() -> Client:
    global _client
    if _client is None:
        _client = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True)
    return _client


def build_params(dest: str, cabin: str, depart: str, ret: str) -> dict:
    q = create_query(
        flights=[
            FlightQuery(date=depart, from_airport=ORIGIN, to_airport=dest),
            FlightQuery(date=ret, from_airport=dest, to_airport=ORIGIN),
        ],
        seat=cabin,
        trip="round-trip",
        passengers=Passengers(adults=1),
        language="en-US",
        currency=CURRENCY,
    )
    return q.params()


def extract_payload(html: str):
    """Return the decoded results block, or None when the page has none."""
    script = LexborHTMLParser(html).css_first(r"script.ds\:1")
    if script is None:
        return None
    js = script.text()
    if "data:" not in js:
        return None
    data = js.split("data:", 1)[1].rsplit(",", 1)[0]
    if data.endswith("errorHasStatus: true"):
        return None
    return json.loads(data)


def _date(parts) -> str:
    y, m, d = parts
    return f"{y:04d}-{m:02d}-{d:02d}"


def parse_payload(payload) -> list[dict]:
    """Turn the results block into one dict per itinerary (outbound flights + round-trip price)."""
    out = []
    for list_index, list_name in ((2, "best"), (3, "other")):
        block = payload[list_index] if len(payload) > list_index else None
        if not block or not block[0]:
            continue
        for item in block[0]:
            try:
                flight = item[0]
                price = item[1][0][1] if item[1] and item[1][0] else None
                if price is None:
                    continue
                segments = flight[2]
                codes = [s[22][0] for s in segments]
                out.append({
                    "origin_airport": segments[0][3],
                    "dest_airport": segments[-1][6],
                    "outbound_date": _date(segments[0][20]),
                    "carriers": ", ".join(flight[1]),
                    "carrier_codes": ",".join(dict.fromkeys(codes)),
                    "flight_numbers": " ".join(f"{s[22][0]}{s[22][1]}" for s in segments),
                    "stops": len(segments) - 1,
                    "via": " ".join(s[6] for s in segments[:-1]),
                    "segment_cabins": ",".join(CABIN_NAMES.get(s[16], "unknown") for s in segments),
                    "duration_min": flight[9],
                    "price": int(price),
                    "result_list": list_name,
                })
            except (IndexError, TypeError, KeyError, ValueError):
                continue  # one odd itinerary should not lose the rest
    return out


def search(dest: str, cabin: str, depart: str, ret: str) -> Answer:
    res = _get_client().get(URL, params=build_params(dest, cabin, depart, ret))
    if res.status_code != 200:
        raise Blocked(f"HTTP {res.status_code}")
    return answer_from_page(res.status_code, res.text)


def answer_from_page(status: int, text: str) -> Answer:
    """A real answer, even an empty one, carries the results block (its two lists are then null).
    Any other page (bot check, cookie consent, changed markup) is a refusal, never "no flights"."""
    payload = extract_payload(text)
    if payload is None:
        lower = text.lower()
        if "unusual traffic" in lower or "captcha" in lower:
            raise Blocked("bot check page")
        raise Blocked("unrecognized page (no results block)")
    return Answer(status, parse_payload(payload))
