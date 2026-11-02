"""Run: .venv/bin/python -m unittest discover -s tests"""

import json
import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "tlv_business_payload.json"


class ParseTest(unittest.TestCase):
    def test_reads_both_result_lists(self):
        from fares.gflights import parse_payload

        rows = parse_payload(json.loads(FIXTURE.read_text()))
        self.assertEqual(len(rows), 12)  # 3 "best" + 9 "other"
        self.assertEqual(sum(r["result_list"] == "best" for r in rows), 3)
        first = rows[0]
        self.assertEqual(first["flight_numbers"], "AZ793 AZ810")
        self.assertEqual(first["stops"], 1)
        self.assertEqual(first["price"], 5934)
        self.assertEqual(first["origin_airport"], "HND")
        self.assertEqual(first["dest_airport"], "TLV")
        self.assertEqual(first["via"], "FCO")
        self.assertEqual(rows[3]["via"], "ICN ADD")
        mixed = rows[1]
        self.assertEqual(mixed["carrier_codes"], "TG,LY")


class GridTest(unittest.TestCase):
    def test_weekly_grid_stays_inside_300_days(self):
        from fares.capture import trip_grid

        trips = trip_grid(date(2026, 11, 2), 7)
        self.assertEqual(len(trips), 42)
        self.assertEqual(trips[0], ("2026-11-03", "2026-11-10"))
        self.assertLessEqual((date.fromisoformat(trips[-1][1]) - date(2026, 11, 2)).days, 300)
        self.assertEqual(len(trip_grid(date(2026, 11, 2), 14)), 21)


class CaptureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["FARES_DATA"] = self.tmp.name
        import importlib

        from fares import config
        importlib.reload(config)

    def tearDown(self):
        os.environ.pop("FARES_DATA", None)
        self.tmp.cleanup()

    def test_sweep_writes_rows_and_history_cannot_be_rewritten(self):
        from fares import capture, config, gflights

        capture.PAUSE_SECONDS = 0
        rows = gflights.parse_payload(json.loads(FIXTURE.read_text()))
        result = capture.run(7, 2, search=lambda *a: gflights.Answer(200, rows))
        self.assertEqual(result["queries"], 16)  # 4 routes x 2 cabins x 2 trips
        self.assertEqual(result["counts"]["tel-aviv/first"], 24)
        conn = sqlite3.connect(config.store_path())
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM fares").fetchone()[0], 16 * 12)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE fares SET price = 1")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("DELETE FROM fares")
        log = config.capture_log_path().read_text()
        self.assertIn("done: rows=192 queries=16", log)

    def test_week_scan_is_business_on_seven_consecutive_days(self):
        from fares import capture, gflights

        capture.PAUSE_SECONDS = 0
        seen = []
        result = capture.run(7, None, search=lambda *a: seen.append(a) or gflights.Answer(200, []),
                             week_scan=True)
        self.assertEqual(result["queries"], 28)  # 4 routes x 7 days
        self.assertEqual({a[1] for a in seen}, {"business"})
        departs = sorted({a[2] for a in seen})
        self.assertEqual(len(departs), 7)
        self.assertEqual((date.fromisoformat(departs[-1]) - date.fromisoformat(departs[0])).days, 6)

    def test_throttling_stops_the_sweep(self):
        from fares import capture, gflights

        capture.PAUSE_SECONDS = 0

        def refuse(*a):
            raise gflights.Blocked("HTTP 429")

        result = capture.run(7, 5, search=refuse)
        self.assertTrue(result["throttled"])
        self.assertEqual(result["queries"], 3)


if __name__ == "__main__":
    unittest.main()
