"""One full capture sweep: every route and cabin over a grid of 7-night trips in the next 300 days.

Quiet by design: it writes rows to the store and one summary line to the capture log; it sends
nothing anywhere. Run: bin/capture   (options: --every 7 for the weekly grid, --limit N for a test)
"""

import argparse
import sys
import time
from datetime import date, datetime, timedelta, timezone

from . import config, gflights, store

HORIZON_DAYS = 300
NIGHTS = 7
PAUSE_SECONDS = 2.0       # between queries, to stay a light, polite user of the source
BLOCKED_IN_A_ROW_STOP = 3  # stop the sweep if the source refuses this many times running


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def trip_grid(today: date, every_days: int) -> list[tuple[str, str]]:
    """Departures every `every_days` from tomorrow, 7 nights each, returning within the horizon."""
    trips = []
    dep = today + timedelta(days=1)
    while (dep + timedelta(days=NIGHTS) - today).days <= HORIZON_DAYS:
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


def run(every_days: int, limit: int | None, search=gflights.search, week_scan: bool = False) -> dict:
    profiles = config.load_profiles()
    today = datetime.now(timezone.utc).date()
    if week_scan:
        trips, cabins, every_days = week_scan_grid(today), ["business"], 1
    else:
        trips, cabins = trip_grid(today, every_days), profiles["cabins"]
    if limit:
        trips = trips[:limit]
    conn = store.connect(config.store_path())
    started = time.monotonic()
    sweep_id = store.start_sweep(conn, now_utc(), gflights.SOURCE, every_days)
    counts, queries, failed, blocked_run, throttled = {}, 0, 0, 0, False
    try:
        for route in profiles["routes"]:
            dest = route["airports"][0]
            for cabin in cabins:
                key = f"{route['id']}/{cabin}"
                counts[key] = 0
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
    finally:
        minutes = (time.monotonic() - started) / 60
        total = sum(counts.values())
        per = " ".join(f"{k}={v}" for k, v in counts.items())
        kind = "week scan" if week_scan else "sweep"
        note = f"{kind}: {len(trips)} trips every {every_days} days; {minutes:.1f} min"
        store.finish_sweep(conn, sweep_id, now_utc(), queries, failed, total, throttled, note)
        log(f"{kind} {sweep_id} done: rows={total} queries={queries} failed={failed} "
            f"throttled={int(throttled)} minutes={minutes:.1f} every={every_days}d {per}")
        conn.close()
    return {"sweep_id": sweep_id, "counts": counts, "queries": queries, "failed": failed,
            "throttled": throttled, "minutes": minutes}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    # 14, not 7: the first weekly sweep (2 Nov 2026, 336 queries) drew 17 bot-check refusals,
    # so the grid is thinned per the brief (PLAN.md, "First capture").
    p.add_argument("--every", type=int, default=14, help="days between departures (default 14; 7 for the full weekly grid)")
    p.add_argument("--limit", type=int, help="only the first N departures (for a quick test)")
    p.add_argument("--week-scan", action="store_true",
                   help="business only, 7 consecutive departure days 4 weeks out (shows nonstop days of week)")
    args = p.parse_args(argv)
    result = run(args.every, args.limit, week_scan=args.week_scan)
    return 1 if result["throttled"] or result["queries"] == result["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
