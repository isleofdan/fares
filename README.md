# fares

A personal system that tracks business and first class round-trip airfares from Tokyo on four routes (Houston, Detroit, Tel Aviv, Barcelona).
Once a day it quietly records the prices it finds into a price history on Dan's machine, and nothing is ever overwritten.
A second program turns that history into one plain web page showing today's prices against each route's own past prices.
The aim is to spot real deals and to learn how airfares behave; `LEARNING.md` collects what the data teaches.
Route rules live in `routes.json`; current state and decisions are in `PLAN.md`.

## Run it

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # once
bin/capture              # one full sweep into /data/home/dan/fares-data/fares.sqlite (about 9 min, every 14 days)
bin/capture --week-scan  # seven days in a row, business: which days each nonstop flies
bin/page                 # writes /data/home/dan/fares-data/fares.html
bin/daily-loop           # all three, then again every 24 hours (not installed anywhere; see PLAN.md)
.venv/bin/python -m unittest discover -s tests -t .   # tests
```

Logs: `capture.log` (one line per sweep) and `loop.log` (the daily loop), both in `/data/home/dan/fares-data/`.
