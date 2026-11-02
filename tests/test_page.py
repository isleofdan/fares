"""Run: .venv/bin/python -m unittest discover -s tests"""

import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "tlv_business_payload.json"

NONSTOP = {
    "origin_airport": "NRT", "dest_airport": "TLV", "outbound_date": "2026-12-03",
    "carriers": "El Al", "carrier_codes": "LY", "flight_numbers": "LY92", "stops": 0, "via": "",
    "duration_min": 800, "price": 7100, "result_list": "best",
}


class PageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["FARES_DATA"] = self.tmp.name
        from fares import config
        importlib.reload(config)
        from fares import capture, gflights
        capture.PAUSE_SECONDS = 0
        self.capture, self.gflights = capture, gflights
        self.rows = gflights.parse_payload(json.loads(FIXTURE.read_text()))

    def tearDown(self):
        os.environ.pop("FARES_DATA", None)
        self.tmp.cleanup()

    def day(self, bump=0):
        g = self.gflights
        rows = [dict(r, price=r["price"] + bump) for r in self.rows]
        self.capture.run(7, 1, search=lambda *a: g.Answer(200, rows))
        # The week scan finds El Al's nonstop on Tel Aviv only, on two of its seven days.
        flies = {dep for dep, _ in self.capture.week_scan_grid(self.capture.datetime.now(self.capture.timezone.utc).date())[:2]}
        nonstop = dict(NONSTOP, price=NONSTOP["price"] + bump)
        self.capture.run(7, None, week_scan=True,
                         search=lambda d, c, dep, ret: g.Answer(200, [nonstop] if d == "TLV" and dep in flies else []))

    def render(self):
        from fares import config, page, store
        return page.render(store.connect(config.store_path()))

    def test_first_day(self):
        self.day()
        out = self.render()
        tlv = out[out.index("<section id=tel-aviv>"):out.index("<section id=barcelona>")]
        self.assertLess(tlv.index("Nonstop: El Al"), tlv.index("Cheapest one-stop"))
        self.assertIn("first capture", tlv)
        self.assertIn("Google Flights", tlv)
        self.assertIn("$7,100", tlv)
        self.assertIn("(2 days a week in today's searches)", tlv)
        self.assertIn("first day of history", tlv)
        hou = out[out.index("<section id=houston>"):out.index("<section id=detroit>")]
        self.assertIn("No nonstop appeared", hou)
        for rid in ("houston", "detroit", "tel-aviv", "barcelona"):
            self.assertIn(f"<section id={rid}>", out)

    def test_mixed_cabins_are_named(self):
        from fares import page
        row = {"segment_cabins": "first,business", "flight_numbers": "EY801 EY595"}
        self.assertIn("EY801 first, EY595 business", page.mixed_cabin_note(row, "first"))
        self.assertEqual(page.mixed_cabin_note(dict(row, segment_cabins="first,first"), "first"), "")
        self.assertEqual(page.mixed_cabin_note(dict(row, segment_cabins=None), "first"), "")

    def test_same_day_sweeps_are_not_history(self):
        self.day()
        self.day(bump=-500)
        out = self.render()
        self.assertNotIn("typical", out[out.index("<section"):])
        self.assertIn("first day of history", out)

    def test_el_al_line_stays_first_when_not_found(self):
        g = self.gflights
        self.capture.run(7, 1, search=lambda *a: g.Answer(200, self.rows))
        out = self.render()
        tlv = out[out.index("<section id=tel-aviv>"):out.index("<section id=barcelona>")]
        self.assertIn("Nonstop: El Al", tlv)
        self.assertIn("none found in this capture", tlv)
        self.assertLess(tlv.index("Nonstop: El Al"), tlv.index("Cheapest one-stop"))

    def test_second_day_compares_with_history(self):
        real = self.capture.now_utc
        self.capture.now_utc = lambda: "2026-11-01T10:00:00Z"  # yesterday
        try:
            self.day()
        finally:
            self.capture.now_utc = real
        self.day(bump=-500)
        out = self.render()
        tlv = out[out.index("<section id=tel-aviv>"):out.index("<section id=barcelona>")]
        self.assertIn("$500 below the typical $7,100", tlv)
        self.assertNotIn("first day of history", tlv)


if __name__ == "__main__":
    unittest.main()
