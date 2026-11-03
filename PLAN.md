# Plan

## Current state

Step 7.1 (skeleton) done. Step 7.2 done: Google Flights chosen as the fare source (see "Fare sources tried"). Step 7.3 done: the capture runs; first real sweeps recorded under "First capture". Step 7.4 done: daily loop written, not installed (see "Daily run"). Step 7.5 done: the page and its screenshot (see "The page"). Step 7.6 done: first learning note in LEARNING.md.

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
- A "first" search returns the best cabin on each flight, so many results are first class only on the long flight (see "The page").

### Keyed sources, recorded for later (fares-two, 3 Nov 2026)

Nothing is wired and no key or account was made. Each cell comes from the source's own page, read as a plain page on 3 Nov 2026. "Not found" means no page I could read says it. Amadeus's and Kiwi's portal pages are drawn by browser JavaScript and came back with no text, so for Amadeus the cells come from Amadeus's own published API specification on GitHub.

| Source | Free tier | What it adds over Google Flights | Key enough, or company account? | Documentation |
|---|---|---|---|---|
| **Amadeus Self-Service**, Flight Offers Search v2.9.1 | Not found (the pricing page has no text without a browser). The spec says the test environment "is based on a subset of the production". | **Fare basis and booking class** per segment (`fareBasis`; `class`, "the code of the booking class, a.k.a. … (RBD)"). **The return flight**: with a return date "only round-trip itineraries are found", each offer holding its itineraries. **More than the first page**: "Maximum number of flight offers returned (Max 250)". | Not found (the sign-up page has no text without a browser). | [API spec (amadeus4dev on GitHub)](https://raw.githubusercontent.com/amadeus4dev/amadeus-open-api-specification/main/spec/json/FlightOffersSearch_v2_swagger_specification.json), [pricing](https://developers.amadeus.com/pricing) |
| **Duffel** | "No upfront fees". $3.00 "for every confirmed order". Searches above a "search to book ratio of 1500:1" cost $0.005 each. Test-mode cost: not found. | **Fare basis** per segment and passenger (`fare_basis_code`, e.g. "OXZ0RO"). Booking class: not found (only `cabin_class`). **The return flight**: "return trips will need two [slices]", and an offer's total is "for all passengers, including taxes". **More than the first page**: the offer request includes "all the offers returned by the airlines". Most per search: not found. | A self-signup test token searches in test mode ("Create a test access token…"). What going live needs: not found. | [pricing](https://duffel.com/pricing), [offer requests](https://duffel.com/docs/api/v2/offer-requests), [offers](https://duffel.com/docs/api/v2/offers), [getting started](https://duffel.com/docs/guides/getting-started-with-flights) |
| **Kiwi.com Tequila** | Not found (the docs page has no text without a browser) | Not found | **Company partnership, by invitation**: "Any new partnerships on the Tequila platform will be on an invitation only basis" (Kiwi.com, 30 May 2024) | [search API docs](https://tequila.kiwi.com/portal/docs/tequila_api/search_api), [access notice](https://media.kiwi.com/articles-and-interviews/better-for-business-kiwi-com-takes-a-new-approach-to-partnerships/) |
| **SerpApi**, Google Flights API (a paid reader of the same Google Flights results) | 250 searches a month free. Starter is $25 a month for 1,000. | Fare basis: not found (only `travel_class`). **The return flight** needs "another request using a departure_token". More than the first page: not found (`best_flights` and `other_flights` only, the same two lists we read). | Self-signup key (`api_key`) | [Google Flights API](https://serpapi.com/google-flights-api), [pricing](https://serpapi.com/pricing) |
| **Travelpayouts** (Aviasales) Data API | Not found | Cabin only (`trip_class`), no fare basis. Cached prices "found by our users during the most recent 48 hours", not live searches. `page` and `limit` go up to 1,000 rows. | Affiliate-network sign-up for a data token. The live search API needs an approved request, and "It's forbidden to automatically collect data from search results". | [API docs](https://travelpayouts.github.io/slate/) |

**Reading.** Only Amadeus and Duffel say they give a fare code. Amadeus adds the booking class and up to 250 offers per search. Duffel's sign-up is self-serve for test mode. Its search fee depends on bookings, which this project never makes, so its pricing does not fit a price tracker. Kiwi is closed to new users. SerpApi is the same Google Flights data behind a key.

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

**Complete or not.** A sweep is marked `completed` only when every planned search ran and the source did not throttle it. Interrupted, crashed and throttled sweeps keep their rows as history, are logged as INCOMPLETE, and are never shown on the page as today's prices. A page with no results block (a bot check, a cookie-consent page, changed markup) counts as a refused search, never as "no flights". A genuine empty answer still carries the results block, with both lists empty. These rules came from dev-check's review of ba24f78. Existing sweeps were backfilled: 2–6 complete, 1 not.

**Week scan** (`bin/capture --week-scan`). Business only, seven departures on consecutive days starting 4 weeks out. The main grid always lands on the same weekday, so this is what shows which days each nonstop flies.

## Daily run (step 7.4): prepared, not installed

**Mechanism found on the machine.** Per FACTS.md, section "Skill mirror": `start.sh` opens tmux window `skill-mirror` in session `main`. That window runs a loop: run `mirror-skills`, sleep 24 hours, repeat, appending output to a log. I checked it on the machine on 2 Nov 2026: `/usr/local/bin/start.sh` lines 200–207 hold that window, `tmux list-windows -t main` shows window 2 `skill-mirror` running, and `~/.agent-machine/skill-mirror/loop.log` was last written at 15:01:57Z that day.

**The loop for fares.** `bin/daily-loop` has the same shape: run the capture now, then the week scan, then sleep out the rest of 24 hours, forever. A failed run does not end the loop. All output is appended to `/data/home/dan/fares-data/loop.log`. It sleeps 24 hours *minus the run's length* (the skill-mirror loop sleeps a full 24 hours after each run), so a ~10-minute capture does not push the run time later each day. Nothing here registers or starts it: installing it would be a change to the machine's own configuration, which is out of scope this session.

**Proposed run time and log.** It runs when the machine boots and then at the same clock time every 24 hours until the next boot, like the skill mirror. One run takes about 10 minutes: the 14-day sweep (~8.5 min) plus the week scan (~1.5 min). Log: `/data/home/dan/fares-data/loop.log`, with each sweep's summary line also in `/data/home/dan/fares-data/capture.log`.

**Installation step left for a separately authorized session on `isleofdan/agent-machine`.**
1. Keep a permanent clone of `isleofdan/fares` at `/data/home/dan/fares` (outside `~/work`, whose job folders get cleared), with its virtualenv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
2. Add these lines to `start.sh` after the skill-mirror window (after line 207):

```sh
# Window "fares": captures premium fares (isleofdan/fares) now and then once a day, forever; quiet.
# Output goes to ~/fares-data/loop.log, each sweep's summary also to capture.log there. By hand: ~/fares/bin/daily-loop
"${AS_DAN[@]}" tmux new-window -d -t main -n fares "$HOME_DIR/fares/bin/daily-loop" \
  || echo "start.sh: starting the fares window failed; continuing." >&2
```

## The page (step 7.5)

`bin/page` (code in `fares/page.py`) writes one HTML file, `/data/home/dan/fares-data/fares.html`, from the newest complete sweep and the newest week scan. Nothing is hosted. `bin/daily-loop` now runs it after each capture. The page has one section per route, in the order of `routes.json`:
- **Nonstop lines first**, one per nonstop carrier the data shows, with business and first. Tel Aviv's El Al line is always first and is shown even when no El Al nonstop was found, as the rules require. Each line also gives the weekdays that nonstop was seen departing, combining the main grid with the week scan.
- **Then the cheapest one-stop** in business and in first.
- Every price names its capture time (Tokyo time) and its source. Each is compared with the cheapest price of the same kind (that nonstop carrier, or one-stop) on each earlier capture day: how far above or below the typical (median) daily low, and the lowest price seen. Sweeps run earlier on the same day are not history, so with one day of data every line says "first capture".
- A plain-words reading under each route, and a list of the words used, at the top of the page.
- **Mixed cabins.** A first class search often returns trips that are first class only on the long flight and business on a connection: 321 of 497 first-search rows in sweep 5. The cabin of each flight is now stored (`segment_cabins`, added after sweep 4; earlier rows hold NULL) and the page names it, e.g. "mixed cabins: EY801 first, EY595 business".

Screenshot: `docs/fares-page.png`, Playwright 1.56.1's headless Chromium, full page with all four route sections, from sweep 5 (16:04–16:12Z, 168 searches, 0 refused, 1,152 rows) and week scan 6 (245 rows), both on 2 Nov 2026 UTC. To take it again: `npm install`, then `npm run screenshot`.

## Close-out notes

### fares-one (2 Nov 2026 UTC, 3 Nov Tokyo time)

- **What stands.** Steps 7.1 to 7.6 are built and committed on branch `claude/fares-one`, by the OpenRig team (builder `dev-owner@fares-one-mixed`, checker `dev-check@fares-one-mixed`). The checker's first round on `ba24f78` found three problems (an interrupted or throttled sweep replaced the last complete one on the page; unrecognised pages counted as "no flights"; a stale week scan could be shown); they were fixed in `7c3d197`, which the checker passed. 16 tests pass.
- **Source chosen and why.** Google Flights, read through `fast-flights` 3.1.0 with our own parser: the only keyless candidate that returned prices from a script (Kayak, Momondo, Skyscanner and ITA Matrix need a browser). About 1.2 s a search. It gives no fare code or booking class.
- **Sweep numbers.** Weekly grid: 336 searches, 15.8 min, 2,293 rows, but 17 searches met a bot check, so the default is now every 14 days: 168 searches, 8.4 min, about 1,150 rows, no refusals in two runs. The store and page are in `/data/home/dan/fares-data/`.
- **Scheduling.** Mechanism found: the skill-mirror window in `/usr/local/bin/start.sh` lines 200 to 207 (a tmux loop: run, sleep 24 hours, append to a log). `bin/daily-loop` copies that shape and is not installed. The installation step (a permanent clone at `/data/home/dan/fares` and the start.sh lines under "Daily run" above) is left for a separately authorized session on `isleofdan/agent-machine`.
- **What the next session needs.** The daily loop installed by that agent-machine session, so days of history build up; then the next fares session (Claude Code on the machine, with the OpenRig team) can put the page into the Spine and start tactics and the reading feed. The loop has been syntax-checked only, never run as a loop.
