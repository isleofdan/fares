# Plan

## Current state

Step 7.1 (skeleton) done. Step 7.2 done: Google Flights chosen as the fare source (see "Fare sources tried"). Step 7.3 done: the capture runs; first real sweeps recorded under "First capture".

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

## First capture (step 7.3)

The capture (`bin/capture`, code in `fares/capture.py`) searches every route and cabin over a grid of 7-night round trips. Departures start tomorrow, and the last trip is back within 300 days. There is a 2-second pause between searches. One row is stored per itinerary returned, in `/data/home/dan/fares-data/fares.sqlite`. The database refuses updates and deletes to fare rows, so history only grows. Each run adds one line to `/data/home/dan/fares-data/capture.log`, plus a line for each refused or failed search. A sweep stops early if the source refuses 3 searches in a row.

Real runs on 2 Nov 2026 (UTC), source Google Flights:

| Sweep | Grid | Searches | Refused | Minutes | Rows written |
|---|---|---|---|---|---|
| 1 | weekly | – | – | 1.5 | 145: stopped by hand after Houston business to add the `via` column. Marked incomplete in the store and left out of the page. |
| 2 | every 7 days (42 trips) | 336 | 17 ("bot check" page) | 15.8 | 2,293 |
| 3 | week scan (see below) | 28 | 0 | 1.4 | 239 |
| 4 | every 14 days (21 trips) | 168 | 0 | 8.4 | 1,140 |

Rows per route and cabin, sweep 2 (weekly) / sweep 4 (every 14 days):

| | Business | First |
|---|---|---|
| Houston | 234 / 114 | 324 / 162 |
| Detroit | 345 / 182 | 210 / 105 |
| Tel Aviv | 229 / 110 | 165 / 78 |
| Barcelona | 478 / 245 | 308 / 144 |

**Thinned to every 14 days.** The weekly sweep took 15.8 minutes, well inside the two-hour limit. But from about its 200th search, Google answered 17 of the 336 searches with a bot-check page instead of results (Tel Aviv first and Barcelona, scattered, never 3 in a row). The brief says to thin the grid if the source throttles, so `bin/capture` now defaults to every 14 days. The 14-day sweep that followed straight after drew no refusals: 168 searches in 8.4 minutes. `bin/capture --every 7` still runs the weekly grid.

**Far-off dates come back empty.** In both sweeps, Houston, Detroit and Tel Aviv returned no itineraries for departures from mid/late June 2027 onward (Tel Aviv from 15 June, the others from 29 June). Barcelona answered through August. This is the same in the refusal-free sweep, so it is not throttling; most likely those fares are not on sale yet. So for three routes the useful horizon today is about 8 months, not 300 days.

**Week scan** (`bin/capture --week-scan`). Business only, seven departures on consecutive days starting 4 weeks out. The main grid always lands on the same weekday, so this is what shows which days each nonstop flies.

## Close-out notes

(none yet)
