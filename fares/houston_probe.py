"""Bounded Houston evidence. Read existing week scans first; nine optional searches.

Run through bin/houston-probe so capture and probe share an exclusive lock.
The report is a separate JSON file: nothing enters fare history or verdicts.
"""
import argparse
import json
import sqlite3
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from . import config

DEPARTURES = ("2026-12-28", "2026-12-29", "2026-12-31")
NIGHTS = (5, 7, 10)
PAUSE_SECONDS = 2.0


def week_evidence(path):
    """Compare within a scan, cabin, carrier, airports, stops and segment cabins.

    Missing Mondays are explicit. Only seven-night complete Houston business
    scans participate. A lower fare can reflect a different product; retain
    flight numbers to make that visible, without claiming causation.
    """
    conn = sqlite3.connect(f"{Path(path).resolve().as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT f.* FROM fares f JOIN sweeps s ON s.id=f.sweep_id "
                        "WHERE s.completed=1 AND s.grid_step_days=1 AND f.route='houston' "
                        "AND f.cabin='business' AND f.stops<=1 ORDER BY f.sweep_id,f.depart_date,f.price").fetchall()
    groups = {}
    for r in rows:
        if (date.fromisoformat(r["return_date"]) - date.fromisoformat(r["depart_date"])).days != 7:
            continue
        key = (r["sweep_id"], r["carrier_codes"], r["origin_airport"], r["dest_airport"], r["stops"], r["segment_cabins"], r["currency"])
        groups.setdefault(key, {}).setdefault(r["depart_date"], dict(r))
    conn.close()
    results = []
    for key, dates in groups.items():
        monday = next((v for d, v in dates.items() if date.fromisoformat(d).weekday() == 0), None)
        others = [v for d, v in dates.items() if date.fromisoformat(d).weekday() != 0]
        best = min(others, key=lambda r: r["price"], default=None)
        results.append({"group": key, "observed_departures": sorted(dates), "monday": monday,
                        "cheapest_other_day": best,
                        "difference_other_minus_monday": best["price"] - monday["price"] if monday and best else None})
    return {"comparisons": results, "interpretation": "Observed seven-night differences only; missing is unknown. Stay length is not measured by these scans."}


def probe(search, blocked, output, sleep=time.sleep, today=None):
    today = today or date.today()
    if any(date.fromisoformat(d) <= today for d in DEPARTURES):
        raise ValueError("Probe dates are no longer future dates; choose a new bounded plan before running.")
    report = {"kind": "exploratory Houston business", "complete": False, "cells": [],
              "scope": "9 searches; no selected returns, no verified quotes, no statistical conclusion"}
    def write():
        output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Exclusive creation prevents a retry from overwriting or repeating this run.
    with output.open("x", encoding="utf-8") as f:
        json.dump(report, f)
    for depart in DEPARTURES:
        for nights in NIGHTS:
            ret = (date.fromisoformat(depart) + timedelta(days=nights)).isoformat()
            if report["cells"]:
                sleep(PAUSE_SECONDS)
            cell = {"depart": depart, "return": ret, "nights": nights,
                    "captured_at": datetime.now(timezone.utc).isoformat(), "currency": "USD"}
            try:
                answer = search("IAH", "business", depart, ret)
                cell.update(state="observed" if answer.itineraries else "no results", itineraries=answer.itineraries)
            except blocked as e:
                cell.update(state="blocked", reason=str(e)[:300]); report["cells"].append(cell); write(); return report
            except Exception as e:
                cell.update(state="error", reason=str(e)[:300]); report["cells"].append(cell); write(); return report
            report["cells"].append(cell); write()
    report["complete"] = True; write(); return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Also run exactly nine exploratory searches")
    args = parser.parse_args()
    out = config.DATA_DIR / "houston-evidence"
    out.mkdir(parents=True, exist_ok=True)
    evidence = week_evidence(config.store_path())
    (out / "week-scans.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Read {len(evidence['comparisons'])} comparable scan groups; wrote {out / 'week-scans.json'}")
    if args.run:
        from . import gflights
        result = probe(gflights.search, gflights.Blocked, out / "december-2026-probe.json")
        print(f"Probe complete={result['complete']}, cells={len(result['cells'])}; no daily-history writes")
        return 0 if result["complete"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
