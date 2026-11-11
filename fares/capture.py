"""One full capture sweep: every route and cabin over a grid of 7-night trips in the next 294 days.

Quiet by design: it writes rows to the store and one summary line to the capture log; it sends
nothing anywhere. Run: bin/capture   (options: --every 7 for the weekly grid, --horizon 300 for the
old 300-day grid, --limit N for a test)
"""

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone

from . import config, gflights, store

# Measured 3 Nov 2026 from complete sweeps 2, 4, 5 and 7: the latest trip any route answered
# (Barcelona) returns 288 days after the sweep day; rounded up to a multiple of 14 days that is 294,
# under the 300-day cap. Houston, Detroit and Tel Aviv answer only to about 225 days out today.
HORIZON_DAYS = 294
NIGHTS = 7
PAUSE_SECONDS = 2.0       # between queries, to stay a light, polite user of the source
BLOCKED_IN_A_ROW_STOP = 3  # stop the sweep if the source refuses this many times running


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Grid departures sit on fixed calendar dates, a whole number of steps after this Monday, so every
# day's sweep searches the same departure dates as the day before (minus the one now past, plus one
# new at the far end). That lets the page compare a date's price with the same date on earlier
# capture days (session fares-lenses, 11 Nov 2026). Before that the grid started "tomorrow", so the
# dates moved by one day each day and never repeated.
GRID_EPOCH = date(2026, 11, 2)


def trip_grid(today: date, every_days: int, horizon_days: int = HORIZON_DAYS) -> list[tuple[str, str]]:
    """Departures on the fixed dates GRID_EPOCH + n * `every_days` (the first one after today),
    7 nights each, returning within `horizon_days`."""
    trips = []
    first = today + timedelta(days=1)
    dep = first + timedelta(days=-(first - GRID_EPOCH).days % every_days)
    while (dep + timedelta(days=NIGHTS) - today).days <= horizon_days:
        trips.append((dep.isoformat(), (dep + timedelta(days=NIGHTS)).isoformat()))
        dep += timedelta(days=every_days)
    return trips


WEEK_SCAN_START_DAYS = 28


def week_scan_grid(today: date) -> list[tuple[str, str]]:
    """Seven departures on consecutive days, four weeks out: the weekly grid always lands on one
    weekday, so this is what shows which days of the week each nonstop flies."""
    first = today + timedelta(days=WEEK_SCAN_START_DAYS)
    return [((first + timedelta(days=i)).isoformat(), (first + timedelta(days=i + NIGHTS)).isoformat())
            for i in range(7)]


def log(line: str) -> None:
    path = config.capture_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{now_utc()} {line}\n")


def run(every_days: int, limit: int | None, search=gflights.search, week_scan: bool = False,
        horizon_days: int = HORIZON_DAYS) -> dict:
    profiles = config.load_profiles()
    today = datetime.now(timezone.utc).date()
    if week_scan:
        trips, cabins, every_days = week_scan_grid(today), ["business"], 1
    else:
        trips, cabins = trip_grid(today, every_days, horizon_days), profiles["cabins"]
    if limit:
        trips = trips[:limit]
    conn = store.connect(config.store_path())
    started = time.monotonic()
    sweep_id = store.start_sweep(conn, now_utc(), gflights.SOURCE, every_days)
    counts, queries, failed, blocked_run, throttled, finished_loop = {}, 0, 0, 0, False, False
    last = {}  # route/cabin -> latest departure that returned at least one itinerary
    try:
        for route in profiles["routes"]:
            dest = route["airports"][0]
            for cabin in cabins:
                key = f"{route['id']}/{cabin}"
                counts[key] = 0
                last[key] = None
                for depart, ret in trips:
                    if throttled:
                        break
                    if queries:
                        time.sleep(PAUSE_SECONDS)
                    queries += 1
                    try:
                        answer = search(dest, cabin, depart, ret)
                        blocked_run = 0
                    except gflights.Blocked as e:
                        failed += 1
                        blocked_run += 1
                        log(f"sweep {sweep_id} blocked {key} {depart}: {e}")
                        throttled = blocked_run >= BLOCKED_IN_A_ROW_STOP
                        continue
                    except Exception as e:  # noqa: BLE001 - network hiccups must not end the sweep
                        failed += 1
                        log(f"sweep {sweep_id} error {key} {depart}: {type(e).__name__}: {e}")
                        continue
                    captured = now_utc()
                    rows = [
                        {
                            **it,
                            "sweep_id": sweep_id,
                            "captured_at": captured,
                            "route": route["id"],
                            "cabin": cabin,
                            "depart_date": depart,
                            "return_date": ret,
                            "currency": gflights.CURRENCY,
                            "source": gflights.SOURCE,
                            "fare_code": None,
                        }
                        for it in answer.itineraries
                    ]
                    counts[key] += store.insert_fares(conn, rows)
                    if rows:
                        last[key] = depart  # trips run in date order
        finished_loop = True
    finally:
        minutes = (time.monotonic() - started) / 60
        total = sum(counts.values())
        per = " ".join(f"{k}={v}" for k, v in counts.items())
        # So the horizon can be re-measured from the log alone (PLAN.md, "fares-two").
        lasts = " ".join(f"last={k}:{v or 'none'}" for k, v in last.items())
        kind = "week scan" if week_scan else "sweep"
        # Complete only if every planned search ran: not throttled, not interrupted or crashed.
        completed = finished_loop and not throttled
        state = "done" if completed else "INCOMPLETE"
        horizon = "" if week_scan else f" within {horizon_days} days"
        note = f"{kind}: {len(trips)} trips every {every_days} days{horizon}; {minutes:.1f} min; {state}"
        store.finish_sweep(conn, sweep_id, now_utc(), queries, failed, total, throttled, note, completed)
        log(f"{kind} {sweep_id} {state}: rows={total} queries={queries} failed={failed} "
            f"throttled={int(throttled)} minutes={minutes:.1f} every={every_days}d"
            + ("" if week_scan else f" horizon={horizon_days}d") + f" {per} {lasts}")
        conn.close()
    return {"sweep_id": sweep_id, "counts": counts, "last": last, "queries": queries, "failed": failed,
            "throttled": throttled, "minutes": minutes, "completed": completed}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    # 14, not 7: the first weekly sweep (2 Nov 2026, 336 queries) drew 17 bot-check refusals,
    # so the grid is thinned per the brief (PLAN.md, "First capture").
    p.add_argument("--every", type=int, default=14, help="days between departures (default 14; 7 for the full weekly grid)")
    p.add_argument("--horizon", type=int, default=HORIZON_DAYS,
                   help=f"days ahead the last 7-night trip must return by (default {HORIZON_DAYS};"
                        " 300 for the old grid)")
    p.add_argument("--limit", type=int, help="only the first N departures (for a quick test)")
    p.add_argument("--week-scan", action="store_true",
                   help="business only, 7 consecutive departure days 4 weeks out (shows nonstop days of week)")
    args = p.parse_args(argv)
    if args.horizon <= NIGHTS:
        p.error(f"--horizon must be more than {NIGHTS} days")
    result = run(args.every, args.limit, week_scan=args.week_scan, horizon_days=args.horizon)
    return 0 if result["completed"] and result["queries"] > result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
