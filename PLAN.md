# Plan

## Current state

fares-three (3 Nov 2026): bin/page also sends the page and a summary per route to the Spine's private listener, shown at /fares (see its close-out note). fares-two (3 Nov 2026): horizon fitted to 294 days, history line on the page, keyed sources recorded (see its close-out note). Step 7.1 (skeleton) done. Step 7.2 done: Google Flights chosen as the fare source (see "Fare sources tried"). Step 7.3 done: the capture runs; first real sweeps recorded under "First capture". Step 7.4 done: daily loop written, not installed (see "Daily run"). Step 7.5 done: the page and its screenshot (see "The page"). Step 7.6 done: first learning note in LEARNING.md.

## Open issues

### OPEN ISSUE — the daily search prices Monday departures and 7-night trips only (refiled unchanged so session fares-verdict can read it; first filed 11 Nov 2026 by Personal Shipyard (classic))

Dan, 11 Nov 2026: "make sure the Monday only issue gets preserved to be addressed."

What is checked (isleofdan/fares main at bc541b9, fares/capture.py and PLAN.md close-out "fares-lenses", read 11 Nov 2026): the daily grid departs only on Mondays (2 Nov 2026 plus multiples of 14 days) and every trip is 7 nights. A cheaper fare leaving on another weekday, or for a different length of stay, never appears in the daily history, the comparisons or the deal notes. The only other-weekday evidence is the week scan: seven departures in a row, business, about four weeks out.

Not yet known: whether the weekday or the length of stay moves premium fares on these four routes enough to matter.

To be addressed, in this order:
1. Measure. Session fares-learn-two's learning note already asks which departure weekdays were cheapest; its report should say, per route, how far the cheapest other-weekday business fare in the week scans sits from that week's Monday fare.
2. Decide from that number. Options if it matters: rotate the weekday of the fixed dates, add a second fixed weekday, or widen the week scan; each costs searches, and the weekly grid drew bot checks on 2 Nov (PLAN.md, fares-one close-out).
3. Until decided, any verdict or deal note on the page says it covers Monday departures and 7-night trips.

This issue stays open until a note on this card records the decision. The brief "START HERE — fares-verdict" (event 2574, brief check PASS, job 20261111-142632-245c09) writes it into PLAN.md under "Open issues".

Also part of this issue (Dan, 11 Nov 2026, session fares-verdict): today's cheapest fare can come from the week scan and depart on another weekday, while the verdict's scope still names the grid ("Monday departures, 7-night trips"); the scope stays built from the grid code, and the verdict shows the fare's real departure date beside it.

## Decisions

- Persistent place for the store, the page, the logs and the loop log: `/data/home/dan/fares-data/` (outside the repository; per FACTS.md anything that must survive a deploy lives under `/data/home/dan`).
- Python standard library and SQLite by preference. Any third-party package is declared in the repository and installed into a virtualenv in the clone or under `/data/home/dan/fares-data`, never system-wide.
- No keys, accounts or signed-in browsers this session.
- Route rules live in one data file, `routes.json`.

### Decision: the good-price line (session fares-verdict, 11 Nov 2026)

Each route and cabin has a good-price line: a fare at or under it is a deal. The line comes from the first of these that exists (`good_price()` in `fares/page.py`):
1. **Dan's own number** (`good_price.<cabin>.dan` in `routes.json`; null until he gives one). It wins over everything.
2. **Our own prices**, once the route and cabin have 60 or more complete capture days of the same kind of trip (that nonstop carrier, or one-stop): the lowest tenth (10th percentile, nearest rank) of the daily cheapest prices.
3. **Reported sales** (`good_price.<cabin>.amount` and `sources`): the median of reported round-trip sale prices, rounded to the nearest $50, only when two or more independent publishers report one; else no amount. Yen are converted to US dollars at the day's rate. JAL and ANA sale fares include fuel surcharge but exclude taxes and fees. The Houston and Detroit lines come from JAL and ANA sales to Dallas and Chicago, because no Houston or Detroit business sale was found.
4. **None**: the verdict says "no good-price line yet".

The verdict, sent to the Spine with each route's summary and shown at the top of each route on the page, sets today's cheapest nonstop or one-stop trip against that line: `deal`, `not a deal` or `no line yet`, with the gap, the basis in words, and the scope of the daily search ("Monday departures, 7-night trips", built from `GRID_EPOCH` and `NIGHTS` in `fares/capture.py`; see "Open issues").

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

**Reading.** Only Amadeus and Duffel say they give a fare code. Amadeus adds the booking class and up to 250 offers per search. Duffel's sign-up is self-serve for test mode. Its search fee depends on bookings, which this project never makes, so its pricing does not fit a price tracker. Kiwi takes new Tequila partnerships by invitation only (Kiwi.com, 30 May 2024). SerpApi is the same Google Flights data behind a key.

Packages are listed in `requirements.txt` and installed into `.venv/` inside the clone. One dependency, `typing_extensions`, is used by fast-flights but not declared by it, so it is listed explicitly.

## First capture (step 7.3)

The capture (`bin/capture`, code in `fares/capture.py`) searches every route and cabin over a grid of 7-night round trips. Departures start tomorrow, and the last trip is back within 294 days (300 until fares-two; `--horizon 300` still runs the old grid, see the fares-two close-out note). There is a 2-second pause between searches. One row is stored per itinerary returned, in `/data/home/dan/fares-data/fares.sqlite`. The database refuses updates and deletes to fare rows, so history only grows. Each run adds one line to `/data/home/dan/fares-data/capture.log`, plus a line for each refused or failed search. A sweep stops early if the source refuses 3 searches in a row.

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

Each route section opens with a history line: how many complete full sweeps (week scans and incomplete sweeps never count) hold rows for that route, on how many capture days, and the Tokyo-time span of their captures. Days are UTC dates, the same days the comparisons group by, and the line says so.

Screenshot: `docs/fares-page.png`, Playwright 1.56.1's headless Chromium, full page with all four route sections, from sweep 9 (09:04–09:13Z on 3 Nov 2026, 168 searches, 0 refused, 1,121 rows) and week scan 8 (08:27–08:29Z the same day, 251 rows). To take it again: `npm install`, then `npm run screenshot`.

## Close-out notes

### fares-one (2 Nov 2026 UTC, 3 Nov Tokyo time)

- **What stands.** Steps 7.1 to 7.6 are built and committed on branch `claude/fares-one`, by the OpenRig team (builder `dev-owner@fares-one-mixed`, checker `dev-check@fares-one-mixed`). The checker's first round on `ba24f78` found three problems (an interrupted or throttled sweep replaced the last complete one on the page; unrecognised pages counted as "no flights"; a stale week scan could be shown); they were fixed in `7c3d197`, which the checker passed. 16 tests pass.
- **Source chosen and why.** Google Flights, read through `fast-flights` 3.1.0 with our own parser: the only keyless candidate that returned prices from a script (Kayak, Momondo, Skyscanner and ITA Matrix need a browser). About 1.2 s a search. It gives no fare code or booking class.
- **Sweep numbers.** Weekly grid: 336 searches, 15.8 min, 2,293 rows, but 17 searches met a bot check, so the default is now every 14 days: 168 searches, 8.4 min, about 1,150 rows, no refusals in two runs. The store and page are in `/data/home/dan/fares-data/`.
- **Scheduling.** Mechanism found: the skill-mirror window in `/usr/local/bin/start.sh` lines 200 to 207 (a tmux loop: run, sleep 24 hours, append to a log). `bin/daily-loop` copies that shape and is not installed. The installation step (a permanent clone at `/data/home/dan/fares` and the start.sh lines under "Daily run" above) is left for a separately authorized session on `isleofdan/agent-machine`.
- **What the next session needs.** The daily loop installed by that agent-machine session, so days of history build up; then the next fares session (Claude Code on the machine, with the OpenRig team) can put the page into the Spine and start tactics and the reading feed. The loop has been syntax-checked only, never run as a loop.

### fares-two (3 Nov 2026 UTC)

- **What stands.** Built and committed on branch `claude/fares-two` by the OpenRig team (builder `dev-owner@fares-two-mixed`, checker `dev-check@fares-two-mixed`): the capture's default horizon is now 294 days, with `--horizon` to change it; each sweep's `capture.log` line names, per route and cabin, the last departure that returned results; the page has a history line in each route; the keyed sources are recorded above under "Keyed sources, recorded for later". Nothing is wired to a keyed source.
- **Measured horizon: 294 days.** Across complete grid sweeps 2, 4, 5 and 7 together, the latest departure that returned at least one itinerary was: Houston and Detroit (business and first) 2027-06-22 (sweep 2, every 7 days; 232 days after 2 Nov), with every later search empty from 2027-06-29; Tel Aviv 2027-06-08 (sweep 2; 218 days), empty from 2027-06-15; Barcelona 2027-08-11 (sweep 7; 281 days after 3 Nov), the last date in the grid, never blank. The 14-day sweeps alone stop at 2027-06-15/16 and 2027-06-01/02 only because they skip the dates between. No route had an empty date inside its answered range. The latest trip any route answered returns 288 days after the sweep day (281 + 7 nights). Rounded up to the next multiple of 14 days that is 294, under the 300-day cap. On the default every-14-days grid this keeps the same 21 trips (the last returns 288 days out); it drops only the 42nd trip of the weekly grid (`--every 7`: 41 trips). It does not cut the three routes that answer only to about 225 days out, because Barcelona answers to the end.
- **Hand run with the new default** (`bin/capture`, sweep 9, 09:04–09:13Z on 3 Nov 2026): 168 searches, 0 failed, 0 throttled, 8.5 minutes, 1,121 rows; marked complete. Its `capture.log` line: `sweep 9 done: rows=1121 queries=168 failed=0 throttled=0 minutes=8.5 every=14d horizon=294d houston/business=130 houston/first=160 detroit/business=177 detroit/first=104 tel-aviv/business=117 tel-aviv/first=75 barcelona/business=226 barcelona/first=132 last=houston/business:2027-06-16 last=houston/first:2027-06-16 last=detroit/business:2027-06-16 last=detroit/first:2027-06-16 last=tel-aviv/business:2027-06-02 last=tel-aviv/first:2027-06-02 last=barcelona/business:2027-08-11 last=barcelona/first:2027-08-11`. The last dates match the measured ones. The HTTP client printed one warning to the terminal, "h2 connection driver error: connection error detected: detected excessive load generating behavior", but no search failed. If it recurs together with refusals, it is the first sign of throttling.
- **Re-measuring the horizon later.** The `last=` fields measure a route's horizon only when it goes blank before the grid ends. They show this for Houston, Detroit and Tel Aviv: watch their `last=` dates move later as fares go on sale. They cannot show a horizon past the grid, because every trip in the grid returns within it. On the default grid (every 14 days, `--horizon` 294 or 300, 21 trips) the last return is 288 days out either way. Barcelona answered on that last date, so its real on-sale horizon is unknown and only known to be at least 288 days. Seeing further needs a deliberate wider probe run by hand: `bin/capture --every 7 --horizon 300` (42 trips, the last back 295 days out). That probe is the weekly grid that drew 17 bot-check refusals on 2 Nov, and it counts only if it finishes complete. If it answers on its last date, the cap of 300 is the limit and widening past it is Dan's decision. Raise `HORIZON_DAYS` in `fares/capture.py` only on such evidence.
- **History is still one Tokyo day.** The page now says so: 5 complete full sweeps on 2 capture days (UTC 2 Nov and 3 Nov), all on 3 Nov in Tokyo time. "Typical" and "lowest seen" rest on one earlier capture day.
- **What the next session needs.** The same as fares-one: the daily loop installed by an authorized `isleofdan/agent-machine` session (see "Daily run"), so that days of history build up. Keyed sources: only Amadeus and Duffel publish a fare code. Using either needs Dan's decision to create a key, and for Duffel a look at its booking-based search fee.
- Tests: 21 pass (16 in fares-one).

### fares-three (3 Nov 2026 UTC)

- **What stands.** Built and committed on branch `claude/fares-three` by the OpenRig team (builder `dev-owner@fares-three-mixed`, checker `dev-check@fares-three-mixed`), job 2 of 2 from Dan's session fares-three. Job 1 (isleofdan/spine, branch `claude/fares-page`, `lib/fares.js`) added `POST /internal/fares/page` to the Spine's private listener and `/fares` behind its passphrase. Now `bin/page`, after writing the page, builds a summary per route and sends `{ rendered_at, sweep, html, summary }` there.
- **The summary comes from the page's own data.** `fares/page.py` gains `today_rows` and `history_day` (taken out of `route_section`), `history_counts` (taken out of `history_line`) and `standing` (taken out of `compare`: the word, the difference, the typical, the earlier days, the lowest day), and the page and `route_summary` both use them. Per route and cabin: `cheapest` is the lowest price among today's nonstop and one-stop rows (stops <= 1, what the page lists), null when none; `against_typical` is `standing()` of that row against the history of its kind ("below"/"above", "first capture" with no earlier day, null with no row); `sweeps` and `days` are the history line's counts; `last_run` is the newest complete full sweep's `queries` and `failed_queries` (capture.log's `queries=` and `failed=`), the same on every row; `html` is the exact text written to the page file. The page renders byte for byte as before (checked against the live `fares.html` of sweep 9 from a copy of the store).
- **Values from a copy of the live store (sweep 9),** as Dan's brief expected: Houston 4170 above / 9613 above; Detroit 4616 above / 10835 above; Tel Aviv 4498 above / 7167 below; Barcelona 3643 above / 5822 below; every route 5 sweeps on 2 days; last run 168 searches, 0 refusals.
- **The send.** Address in one place: `config.SPINE_URL` = `http://spine-dan.internal:8080/internal/fares/page` (the Spine README, "The private listener"), overridden by `FARES_SPINE_URL`, overridden by `bin/page --spine <url>`; `--no-push` sends nothing. Standard library only (`urllib`, proxies bypassed), timeout 20 s, one try. Success prints `sent page to <url>: sweep N, 4 routes`; any failure prints one `page not sent to <url>: …` line with the Spine's JSON error text when it answered, and `bin/page` exits 0 so `bin/daily-loop` goes on. No complete full sweep yet: nothing sent, one line. No token anywhere.
- **Proof.** 36 tests pass (21 before; 15 new in `tests/test_spine.py`: the summary on the first day, below and above matching the page's own line, nulls for a route with no rows, refusals from the sweep's failed count, nothing sent without a complete sweep; the send to a 200 stub with the body's shape and `html` equal to the written page, an IPv6 literal (`[::1]`), the setting and `FARES_SPINE_URL`, `--no-push`, a 400 stub, a 400 whose body breaks off (the checker's finding on `f6979e0`: the error-body read raised outside the handlers and `bin/page` exited 1; now guarded, with a regression test), a closed port, and a socket that accepts and never answers, each exiting 0 with the page written and one line). End to end on the machine: the job-1 Spine (`4ea713f`) started locally on a free port with a temporary database, `bin/page` run on a copy of the store with `--spine http://[<this machine's private address>]:8797/internal/fares/page`: `sent page to …: sweep 9, 4 routes`, and the Spine's `/fares` showed the values above; a wrong path printed the Spine's 404 text in one line and exited 0.
- **Not done here.** Nothing pushed or deployed. The live loop (`/data/home/dan/fares`, tmux window "fares") still runs the old code until its boot copy is updated after the pull requests merge, and the Spine must be deployed with job 1 first, or the send answers 404 (harmless: one line, the loop goes on).


### fares-lenses (11 Nov 2026 UTC, cloud thread "Improve fare comparisons on Fares page")

- **Why.** Dan asked what "above typical" on the Spine strip compared with. It was today's cheapest trip on any departure date against the median of earlier days' cheapest on any date, of the same kind (that nonstop carrier, or one-stop): not like for like, and a few dollars flipped the word. Worse, `trip_grid` started "tomorrow", so the departure dates shifted by a day every day and the same date was never searched twice.
- **Fixed departure dates.** `trip_grid` now departs on `GRID_EPOCH` (Monday 2 Nov 2026) plus whole steps, the first after today: each day searches the same Mondays as the day before (minus one past, plus one new at the far end). The 14-day grid holds 20 or 21 trips (160 or 168 searches). Departures are now always Mondays; the week scan still covers the other weekdays.
- **Lenses.** `bin/page` sends `lenses` with each route's summary: `date`, `month`, `any`, `lowest`, each `{business, first}` of `{word, price, typical, diff, depart, basis}` (see `route_lenses` in `fares/page.py` for the definitions). Words: `below`, `near` (within 3 %), `above`, `first capture`. `against_typical` is unchanged, so an older Spine still accepts the body only once it knows `lenses` (deploy the Spine first).
- **Same-date history** builds from this change's first daily run on the machine; until then the date lens uses the same Monday-to-Sunday week.
- Tests: 41 of 42 pass here (the IPv6 loopback test cannot run in a cloud container).

### fares-verdict (11 Nov 2026 UTC, OpenRig team on Dan's machine, job 2 of 2 from Dan's session fares-verdict)

- **What changed.** `routes.json` carries `good_price` per route and cabin (amounts and sources copied from the session's research file). `fares/page.py`: `good_price()`, `route_verdict()` and `scope_text()`; `spine_body` sends `verdict` with each route; each page section opens with the business and first verdict lines and, when a researched line is in use, ends with its sources as links. Lens cells carry `days` (earlier capture days compared with), and the date, month and any lenses say `early` below 7 earlier days (`EARLY_DAYS`), none included: on the first capture day they say `early` with `days` 0 and no typical (result check on fares#6). The lowest lens is exempt and says "first capture" with `days` null. Job 1 (isleofdan/spine, branch `claude/fares-verdict`) accepts and draws both.
- Tests: 67 pass (42 before; 25 new in `tests/test_verdict.py`). dev-check's first round on 08000dd found the first-day reading ("nothing here can be called a deal yet") contradicting a deal from reported sales; the reading now speaks only of the missing comparison, and the glossary names the verdict.

- **Close-out by the supervising session (fares-verdict, restarted 13 Nov 2026 UTC after the first supervising session stopped at a permission prompt).** Re-ran both repositories' tests and the end to end on a fresh read-only copy of the live store (sweep 31). The end to end found one more defect on the Spine side: a "new lowest ever" note was filed again each time the same page was sent again. The deal note already fired once. The builder fixed it on the Spine branch (`622c580`) and the checker reviewed it (see the field report, `docs/reports/fares-verdict-report.md`).
- **The good-price table (all sources read 11 Nov 2026; yen at 158.555 per US dollar that day, from open.er-api.com):**

  | Route | Business line | Basis | First line |
  |---|---|---|---|
  | Houston | $3,900 | 5 JAL sales Tokyo–Dallas, Nov 2024 to Jun 2026 (Texas fallback; no Houston business sale found) | none (no sources) |
  | Detroit | $3,550 | 4 JAL sales and 1 ANA sale Tokyo–Chicago, Jun 2025 to Oct 2026 (Midwest fallback) | none |
  | Tel Aviv | none | 2 Etihad sales ($3,455 and $4,544), both from one publisher (traicy.com), so they are not independent | none |
  | Barcelona | $2,450 | 1 China Eastern deal (premium-flights.com) + 4 Etihad sales (traicy.com), Sep 2025 to Nov 2026 | none |

  Every source, with its link, is in `routes.json` under `good_price` and in the page's "Where the good-price line comes from" lists.
- **Merging, in this order.** 1) The Spine pull request first, then the Spine's deploy workflow, which must succeed. The Spine accepts bodies without `verdict`, so the machine's current fares code still sends without error. 2) Then the fares pull request. If fares went first, the deployed Spine would reject the new body with a 400 for the unknown field `verdict`. That error is one line in `loop.log` and the loop carries on, but the page stays stale.
- **Bringing the machine's running copy up to date (after both merges and the Spine deploy).** As on 11 Nov (card note "Machine updated by a Remote Control session", fares-lenses): a session on the machine runs `git -C /data/home/dan/fares pull --ff-only origin main` (no new packages: standard library only), then `/data/home/dan/fares/bin/page` once. It should print `sent page to http://spine-dan.internal:8080/internal/fares/page: sweep N, 4 routes`. Then it checks https://spine-dan.fly.dev/fares for the verdict lines. `bin/daily-loop` starts each run's `bin/capture` and `bin/page` as new processes, so the loop picks up the new code with no restart. A machine reboot does the same pull by itself (`start.sh`, fast-forward only).
