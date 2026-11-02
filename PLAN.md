# Plan

## Current state

Step 7.1 (skeleton) done. Step 7.2 done: Google Flights chosen as the fare source (see "Fare sources tried").

## Decisions

- Persistent place for the store, the page, the logs and the loop log: `/data/home/dan/fares-data/` (outside the repository; per FACTS.md anything that must survive a deploy lives under `/data/home/dan`).
- Python standard library and SQLite by preference. Any third-party package is declared in the repository and installed into a virtualenv in the clone or under `/data/home/dan/fares-data`, never system-wide.
- No keys, accounts or signed-in browsers this session.
- Route rules live in one data file, `routes.json`.

## Fare sources tried

Tried from the machine on 2 Nov 2026 (UTC), with no key, account or browser. The test trip was Tokyo–Tel Aviv business, out 7 Dec 2026, back 14 Dec 2026, plus one query per route and cabin.

| Candidate | What it returned | Query time | Repeated queries blocked? | Fields |
|---|---|---|---|---|
| **Google Flights**, fetched by the `fast-flights` 3.1.0 package (`tools/probe_google_flights.py`) | Results came back for all 8 route/cabin pairs. The package itself read 3–10 rows per query, but the page holds two lists ("best" and "other") and the package reads only the second; reading both gave 12 for the Tel Aviv business test. | 0.95–1.41 s (8 route/cabin queries, then 10 back-to-back repeats) | No: 10 identical back-to-back queries all answered, each with the same 9 rows | Price in USD for the round trip, carrier(s), every flight number, airports, local departure and arrival times, aircraft, duration, number of stops. **No fare code or booking class.** |
| Kayak (`kayak.com/flights/TYO-TLV/…/business`) | HTTP 200, 1.1 MB page saying "Searching", with no prices in it. Prices load afterwards through browser JavaScript. | 2.1 s | n/a (no data without a browser) | none from a script |
| Momondo (same company and page engine as Kayak) | Same as Kayak: a page with no prices, saying "Searching" | 2.3 s | n/a | none |
| Skyscanner (`skyscanner.net/transport/flights/tyoa/tlv/…`) | HTTP 200, a 708-byte page asking to "enable JavaScript" (a bot wall) | 0.4 s | yes, effectively | none |
| ITA Matrix (`matrix.itasoftware.com`) | An 11 KB app shell; searches run in browser JavaScript against an API meant for that page | 0.7 s | n/a | none from a plain request |
| Airline APIs that need a key (Amadeus Self-Service, Duffel, Kiwi Tequila) | Not tried: each needs a signed-up key, which this session does not use | – | – | – |

**Chosen: Google Flights.** It answers from a script in about 1.2 s, repeated queries were not blocked, it covers every carrier on all four routes in business and first, and it needs no key. We call the page through `fast-flights` (it builds the encoded search and fetches the page looking like a normal Chrome browser), but our own code reads the page's embedded data, so both result lists and the stop and flight-number details are kept.

What it does not give:
- No fare code or booking class, so the `fare_code` column stays empty.
- A round-trip search returns outbound flights, each with the cheapest round-trip price that includes it. The return flight is not chosen, so a row is "this outbound, round trip from $X".
- Only the first page of results, typically 5–20 itineraries per search.

Packages are listed in `requirements.txt` and installed into `.venv/` inside the clone. One dependency, `typing_extensions`, is used by fast-flights but not declared by it, so it is listed explicitly.

## Close-out notes

(none yet)
