# fares

A personal system that tracks business and first class round-trip airfares from Tokyo on four routes (Houston, Detroit, Tel Aviv, Barcelona).
Once a day it quietly records the prices it finds into a price history on Dan's machine, and nothing is ever overwritten.
A second program turns that history into one plain web page showing today's prices against each route's own past prices.
The aim is to spot real deals and to learn how airfares behave; `LEARNING.md` collects what the data teaches.
Each route opens with a verdict for business and first: today's cheapest fare against a good-price line (Dan's own number, else the lowest tenth of 60+ days of our prices, else reported sales), read as a deal, not a deal, or no line yet; the same verdict goes to the Spine (`PLAN.md`, "Decision: the good-price line"). Each route ends with "Ways to pay less": the tactics in `routes.json` (`tactics`, each a move, why it helps, and its source, a link or our own data in `LEARNING.md`), marked "not yet checked against our prices" until `checked` is true; a route without tactics shows nothing, and they are not sent to the Spine as data (it shows the page as it is).
Route rules live in `routes.json`; current state and decisions are in `PLAN.md`.

## Run it

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
bin/capture              # one full sweep into /data/home/dan/fares-data/fares.sqlite (about 9 min, every 14 days, trips back within 294 days)
bin/capture --week-scan  # seven days in a row, business: which days each nonstop flies
bin/capture --horizon 300  # the older, longer grid (default 294 days, measured; see PLAN.md, fares-two)
bin/page                 # writes /data/home/dan/fares-data/fares.html, then sends it to the Spine (/fares)
bin/page --no-push       # writes the page only, sends nothing
bin/page --spine <url>   # sends to another address (default: FARES_SPINE_URL, else http://spine-dan.internal:8080/internal/fares/page)
bin/daily-loop           # all three, then again every 24 hours (not installed anywhere; see PLAN.md)
.venv/bin/python -m unittest discover -s tests -t .   # tests
```

The send is one plain http POST to the Spine's private listener (Dan's Fly private network, no token), timeout 20 seconds, never retried; success or failure is one printed line, and `bin/page` exits 0 either way, so the daily loop goes on when the Spine is unreachable.

Logs: `capture.log` (one line per sweep) and `loop.log` (the daily loop), both in `/data/home/dan/fares-data/`.
