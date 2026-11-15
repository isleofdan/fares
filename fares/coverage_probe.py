"""Plan bounded coverage probes; --run explicitly opts into source searches.

No daily store, capture log, page or publisher is used. Live execution shares
the collector's POSIX flock; planning also works without source dependencies.
"""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import time

from . import config

MAX_QUERIES = 32
NIGHTS = 7
MAX_RETURN_DAYS = 300
PAUSE_SECONDS = 2.0
LIMITS = ("Exploratory source responses only, not verified bookable quotes. "
          "Empty means no parsed itineraries for this query, not no flights or an on-sale boundary. "
          "Blocked, error, in-flight and unattempted cells remain unknown. "
          "Results cannot establish coverage outside the selected dates, airports and cabins, "
          "or change daily history or its horizon.")


def now():
    return datetime.now(timezone.utc).isoformat()


def plan(profiles, routes, cabins, start_day, end_day, step, budget, today=None):
    today = today or datetime.now(timezone.utc).date()
    if not 1 <= budget <= MAX_QUERIES:
        raise ValueError(f"budget must be 1..{MAX_QUERIES}")
    if not 1 <= start_day <= end_day <= MAX_RETURN_DAYS - NIGHTS or step < 1:
        raise ValueError("departure days must be 1..293, start <= end, step >= 1")
    available = {r["id"]: r for r in profiles["routes"]}
    if not routes or not cabins or len(set(routes)) != len(routes) or len(set(cabins)) != len(cabins):
        raise ValueError("select routes and cabins explicitly, without duplicates")
    if any(r not in available for r in routes) or any(c not in profiles["cabins"] for c in cabins):
        raise ValueError("unknown route or cabin")
    count = len(routes) * len(cabins) * len(range(start_day, end_day + 1, step))
    if count > budget:
        raise ValueError(f"scope requires {count} searches, exceeding budget {budget}; narrow scope")
    cells = []
    for route in routes:
        for cabin in cabins:
            for day in range(start_day, end_day + 1, step):
                cells.append({"route": route, "destination": available[route]["airports"][0],
                              "cabin": cabin, "depart": (today + timedelta(days=day)).isoformat(),
                              "return": (today + timedelta(days=day + NIGHTS)).isoformat(),
                              "state": "not_attempted", "itineraries": None})
    return {"schema_version": 1, "kind": "coverage_probe", "as_of": today.isoformat(),
            "origin": "TYO", "currency": "USD", "source": "Google Flights",
            "nights": NIGHTS, "departure_start_day": start_day, "departure_end_day": end_day,
            "step_days": step, "budget": budget, "planned_queries": count,
            "attempted_queries": 0, "complete": False, "stop_reason": "planned",
            "evidence_limits": LIMITS, "cells": cells}


def execute(report, search, blocked, output, sleep=time.sleep):
    """Execute a fresh plan once. Flush before each attempt; never retry a refusal.

    Atomic checkpoints preserve earlier evidence on interruption. A hard kill can
    leave an in_flight cell: its outcome is unknown and must not be called empty.
    """
    report = json.loads(json.dumps(report))
    cells = report["cells"]
    if (report["attempted_queries"] != 0 or not cells
            or len(cells) != report["planned_queries"]
            or not len(cells) <= report["budget"] <= MAX_QUERIES
            or any(c["state"] != "not_attempted" for c in cells)):
        raise ValueError("execution requires a fresh bounded plan")
    output = Path(output)
    if output.suffix != ".json":
        raise ValueError("probe output must be a new .json file")
    report.update(started_at=now(), stop_reason="running")
    def checkpoint(initial=False):
        # Publish complete bytes only. The first hard link exclusively reserves
        # the destination without overwriting a concurrent probe's report.
        # Later checkpoints replace only the report this execution reserved.
        import tempfile
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent,
                                             prefix=output.name + ".", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(report, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            if initial:
                os.link(temporary, output)
            else:
                temporary.replace(output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    checkpoint(initial=True)

    current = None
    try:
        for cell in cells:
            current = None
            if report["attempted_queries"]:
                sleep(PAUSE_SECONDS)
            current = cell
            cell.update(state="in_flight", attempted_at=now())
            report["attempted_queries"] += 1
            checkpoint()
            try:
                answer = search(cell["destination"], cell["cabin"], cell["depart"], cell["return"])
                if answer.status != 200 or not isinstance(answer.itineraries, list):
                    raise ValueError("unrecognized search response")
                # Validate serializability before calling the response observed.
                json.dumps(answer.itineraries)
                cell.update(state="observed" if answer.itineraries else "empty",
                            itineraries=answer.itineraries, captured_at=now())
            except blocked as exc:
                cell.update(state="blocked", reason=str(exc)[:300])
                report["stop_reason"] = "blocked"
                break
            except Exception as exc:
                cell.update(state="error", reason=f"{type(exc).__name__}: {exc}"[:300])
                report["stop_reason"] = "error"
                break
            checkpoint()
        else:
            report.update(complete=True, stop_reason="complete")
    except KeyboardInterrupt:
        if current is not None and current["state"] == "in_flight":
            current["state"] = "interrupted"
        report["stop_reason"] = "interrupted"
    finally:
        report["finished_at"] = now()
        checkpoint()
    return report


@contextmanager
def collector_lock():
    # Same lock as bin/capture and bin/houston-probe. Unsupported platforms fail
    # closed before importing the network source or creating a report.
    try:
        import fcntl
    except ImportError as exc:
        raise RuntimeError("live probes require POSIX flock on the collector host") from exc
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (config.DATA_DIR / "capture.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another capture or probe holds capture.lock") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", action="append", required=True, help="route ID; repeat for each route")
    parser.add_argument("--cabin", action="append", required=True, help="cabin; repeat for each cabin")
    parser.add_argument("--start-day", type=int, required=True, help="first departure offset from today UTC")
    parser.add_argument("--end-day", type=int, required=True, help="inclusive last departure offset")
    parser.add_argument("--step", type=int, default=1, help="days between departures (default 1; not fixed Monday grid)")
    parser.add_argument("--budget", type=int, required=True, help="maximum source calls, 1..32; no retries")
    parser.add_argument("--run", action="store_true", help="explicitly execute the plan (default only prints JSON)")
    parser.add_argument("--output", type=Path, help="new separate .json report; required with --run")
    args = parser.parse_args(argv)
    if args.run != bool(args.output):
        parser.error("--run and --output must be supplied together")
    try:
        report = plan(config.load_profiles(), args.route, args.cabin, args.start_day,
                      args.end_day, args.step, args.budget)
        if args.run:
            with collector_lock():
                from . import gflights
                report = execute(report, gflights.search, gflights.Blocked, args.output)
    except (ValueError, OSError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    return 130 if report["stop_reason"] == "interrupted" else int(args.run and not report["complete"])


if __name__ == "__main__":
    raise SystemExit(main())
