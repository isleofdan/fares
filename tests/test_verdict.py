"""The good-price line, the verdict per route and cabin, and the lenses' `days` and `early`
(session fares-verdict).

Run: .venv/bin/python -m unittest discover -s tests -t .
Nothing leaves the machine: searches are stubs, the one send is to a loopback stub.
"""

import copy
import json
from datetime import date, datetime, timedelta

from tests.test_spine import Base, Stub

ROUTES = ["houston", "detroit", "tel-aviv", "barcelona"]
VERDICT_KEYS = ["basis", "depart", "gap", "line", "price", "scope", "word"]


class VerdictBase(Base):
    def history(self, n, bump=0):
        """`n` earlier capture days (UTC 1 Aug 2026 onwards), then today's."""
        start = datetime(2026, 8, 1, 10, 0, 0)
        for i in range(n):
            self.day(bump=bump, when=(start + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.day()

    def profiles(self):
        from fares import config
        return config.load_profiles()

    def profile(self, rid, **cabins):
        """routes.json's profile for `rid`, with each given cabin's good_price replaced."""
        p = copy.deepcopy(next(r for r in self.profiles()["routes"] if r["id"] == rid))
        for cabin, gp in cabins.items():
            p["good_price"][cabin] = gp
        return p

    def verdict(self, profile):
        c = self.conn()
        full, scan = self.page.latest_captures(c)
        return self.page.route_verdict(c, profile, full, scan)

    def today_cheapest(self, rid, cabin):
        return next(s for s in self.body()["summary"] if s["route"] == rid)["cheapest"][cabin]


class GoodPriceTest(VerdictBase):
    def test_lowest_tenth_is_nearest_rank(self):
        lt = self.page.lowest_tenth
        self.assertEqual(lt(list(range(60, 0, -1))), 6)    # 60 days: the 6th lowest
        self.assertEqual(lt(list(range(1, 62))), 7)        # 61 days: rank ceil(6.1) = 7
        self.assertEqual(lt(list(range(1, 11))), 1)        # 10 days: the lowest
        self.assertEqual(lt([5000, 4000, 4500]), 4000)     # always one of our own prices

    def test_dans_number_wins_over_everything(self):
        self.history(60)
        p = self.profile("tel-aviv", business={"amount": 3900, "sources": [{"url": "u", "read": "r", "price": 1, "note": "n"}], "dan": 4321})
        v = self.verdict(p)["business"]
        self.assertEqual((v["line"], v["basis"]), (4321, "Dan's own number"))

    def test_own_history_at_60_days(self):
        self.history(60)
        c = self.conn()
        full, scan = self.page.latest_captures(c)
        p = self.profile("tel-aviv", business={"amount": 3900, "sources": [], "dan": None})
        today = [r for r in self.page.today_rows(c, "tel-aviv", full, scan) if r["stops"] <= 1 and r["cabin"] == "business"]
        best = self.page.cheapest(today)
        kind = "nonstop" if best["stops"] == 0 else "one-stop"
        lows = [r["low"] for r in self.page.history(c, "tel-aviv", "business", kind, best["carrier_codes"], full["started_at"][:10])]
        self.assertEqual(len(lows), 60)
        v = self.verdict(p)["business"]
        self.assertEqual((v["line"], v["basis"]), (sorted(lows)[5], "lowest tenth of 60 days of our prices"))

    def test_59_days_still_uses_the_researched_line(self):
        self.history(59)
        v = self.verdict(self.profile("houston"))["business"]
        self.assertEqual((v["line"], v["basis"]), (3900, "reported sales, 5 sources"))

    def test_researched_line_from_routes_json(self):
        self.day()
        by = {s["route"]: s["verdict"] for s in self.body()["summary"]}
        self.assertEqual((by["houston"]["business"]["line"], by["houston"]["business"]["basis"]), (3900, "reported sales, 5 sources"))
        self.assertEqual((by["detroit"]["business"]["line"], by["detroit"]["business"]["basis"]), (3550, "reported sales, 5 sources"))
        self.assertEqual((by["barcelona"]["business"]["line"], by["barcelona"]["business"]["basis"]), (2450, "reported sales, 5 sources"))

    def test_no_line(self):
        self.day()
        by = {s["route"]: s["verdict"] for s in self.body()["summary"]}
        # Tel Aviv business has sources but no amount (one publisher); every first class has none.
        for rid, cabin in [("tel-aviv", "business")] + [(r, "first") for r in ROUTES]:
            v = by[rid][cabin]
            self.assertEqual((v["word"], v["line"], v["gap"], v["basis"]), ("no line yet", None, None, None), (rid, cabin))

    def test_routes_json_good_price_matches_the_research_shape(self):
        for r in self.profiles()["routes"]:
            for cabin in ("business", "first"):
                gp = r["good_price"][cabin]
                self.assertEqual(sorted(gp), ["amount", "dan", "sources"])
                self.assertIsNone(gp["dan"])
                for src in gp["sources"]:
                    self.assertEqual(sorted(src), ["note", "price", "read", "url"])


class VerdictWordTest(VerdictBase):
    def setUp(self):
        super().setUp()
        self.day()
        self.price = self.today_cheapest("tel-aviv", "business")

    def word(self, dan):
        return self.verdict(self.profile("tel-aviv", business={"amount": None, "sources": [], "dan": dan}))["business"]

    def test_deal_at_the_line(self):
        v = self.word(self.price)
        self.assertEqual((v["word"], v["gap"]), ("deal", 0))

    def test_deal_under_the_line(self):
        v = self.word(self.price + 100)
        self.assertEqual((v["word"], v["gap"], v["line"]), ("deal", -100, self.price + 100))

    def test_not_a_deal_above_the_line(self):
        v = self.word(self.price - 1)
        self.assertEqual((v["word"], v["gap"]), ("not a deal", 1))

    def test_no_line_yet(self):
        v = self.word(None)
        self.assertEqual((v["word"], v["line"], v["gap"], v["basis"]), ("no line yet", None, None, None))

    def test_verdict_is_the_summarys_cheapest_row(self):
        for s in self.body()["summary"]:
            for cabin in ("business", "first"):
                v = s["verdict"][cabin]
                if s["cheapest"][cabin] is None:
                    self.assertIsNone(v)
                else:
                    self.assertEqual(v["price"], s["cheapest"][cabin])

    def test_a_cabin_with_no_row_is_null(self):
        self.tmp.cleanup()
        super().tearDown()
        super().setUp()
        self.day(only="TLV")
        by = {s["route"]: s["verdict"] for s in self.body()["summary"]}
        for rid in ("houston", "detroit", "barcelona"):
            self.assertEqual(by[rid], {"business": None, "first": None})


class ScopeTest(VerdictBase):
    def tearDown(self):
        self.capture.NIGHTS, self.capture.GRID_EPOCH = 7, date(2026, 11, 2)
        super().tearDown()

    def test_scope_today(self):
        self.assertEqual(self.page.scope_text(), "Monday departures, 7-night trips")

    def test_scope_follows_the_grid(self):
        self.capture.NIGHTS = 10
        self.capture.GRID_EPOCH = date(2026, 11, 4)  # a Wednesday
        self.assertEqual(self.page.scope_text(), "Wednesday departures, 10-night trips")
        self.day()
        for s in self.body()["summary"]:
            for v in s["verdict"].values():
                if v:
                    self.assertEqual(v["scope"], "Wednesday departures, 10-night trips")


class EarlyAndDaysTest(VerdictBase):
    def lenses(self, rid="tel-aviv"):
        return next(s for s in self.body()["summary"] if s["route"] == rid)["lenses"]

    def test_day_zero_is_early_with_no_typical(self):
        # Result check on fares#6: with no earlier day the date, month and any lenses say "early", days 0.
        self.day()
        for s in self.body()["summary"]:
            for lens in ("date", "month", "any"):
                for cabin, cell in s["lenses"][lens].items():
                    if cell:
                        self.assertEqual({k: cell[k] for k in ("word", "days", "typical", "diff", "basis")},
                                         {"word": "early", "days": 0, "typical": None, "diff": None, "basis": None},
                                         (s["route"], lens, cabin))

    def test_day_zero_lowest_says_first_capture(self):
        self.day()
        cells = [c for s in self.body()["summary"] for c in s["lenses"]["lowest"].values() if c]
        self.assertTrue(cells)
        for cell in cells:
            self.assertEqual((cell["word"], cell["days"], cell["typical"]), ("first capture", None, None))

    def test_early_below_seven_days_lowest_exempt(self):
        self.history(6, bump=500)  # today is cheaper: lowest says below, the others early
        L = self.lenses()
        for cabin in ("business", "first"):
            for lens in ("date", "month", "any"):
                self.assertEqual((L[lens][cabin]["word"], L[lens][cabin]["days"]), ("early", 6), (lens, cabin))
            self.assertEqual((L["lowest"][cabin]["word"], L["lowest"][cabin]["days"]), ("below", 6))

    def test_a_real_word_at_seven_days(self):
        self.history(7, bump=500)
        L = self.lenses()
        for cabin in ("business", "first"):
            for lens in ("date", "month", "any", "lowest"):
                self.assertEqual((L[lens][cabin]["word"], L[lens][cabin]["days"]), ("below", 7), (lens, cabin))

    def test_every_lens_cell_carries_days(self):
        self.history(3)
        for s in self.body()["summary"]:
            for lens in s["lenses"].values():
                for cell in lens.values():
                    if cell:
                        self.assertIn("days", cell)
                        self.assertIsInstance(cell["days"], int)


class BodyAndPageTest(VerdictBase):
    def test_body_shape(self):
        self.day()
        b = self.body()
        json.dumps(b)  # serializable as sent
        for s in b["summary"]:
            self.assertEqual(sorted(s["verdict"]), ["business", "first"])
            for v in s["verdict"].values():
                if v is None:
                    continue
                self.assertEqual(sorted(v), VERDICT_KEYS)
                self.assertIn(v["word"], ("deal", "not a deal", "no line yet"))
                self.assertIsInstance(v["price"], int)
                self.assertEqual(date.fromisoformat(v["depart"]).isoformat(), v["depart"])
                self.assertEqual(v["gap"], None if v["line"] is None else v["price"] - v["line"])
                self.assertIsInstance(v["scope"], str)

    def test_each_section_opens_with_the_verdict_lines(self):
        self.day()
        out = self.page.render(self.conn())
        for rid in ROUTES:
            sec = out[out.index(f"<section id={rid}>"):]
            sec = sec[:sec.index("</section>")]
            after_h2 = sec[sec.index("</h2>") + 5:].lstrip()
            self.assertTrue(after_h2.startswith("<p class=verdict><span class=cabin>Business</span>"), after_h2[:120])
            self.assertLess(after_h2.index("<span class=cabin>First</span>"), after_h2.index("<p class=rules>"))
        hou = out[out.index("<section id=houston>"):out.index("<section id=detroit>")]
        self.assertRegex(hou, r"<p class=verdict><span class=cabin>Business</span> <b>\$[\d,]+</b> out \w{3} \d+ \w{3}: <b>(a deal|not a deal)</b>, \$[\d,]+ (under|over) the good-price line \$3,900 \(reported sales, 5 sources\)\. <span class=meta>Monday departures, 7-night trips</span></p>")

    def test_a_first_day_deal_is_not_contradicted_by_the_reading(self):
        # dev-check on 08000dd: a first-day deal from reported sales sat beside "nothing here can be
        # called a deal yet".
        self.day(bump=-3000)
        out = self.page.render(self.conn())
        hou = out[out.index("<section id=houston>"):out.index("<section id=detroit>")]
        self.assertIn("<b>a deal</b>", hou)
        self.assertNotIn("called a deal", out)
        self.assertIn("This is the first day of history, so no price here can be compared with this route&#x27;s own past yet", hou)
        self.assertNotIn("candidate deal", out)
        self.assertIn("<dt>Verdict</dt>", out)

    def test_researched_sources_are_listed_with_links(self):
        self.day()
        out = self.page.render(self.conn())
        hou = out[out.index("<section id=houston>"):out.index("<section id=detroit>")]
        self.assertIn("<details class=sources><summary>Where the good-price line comes from</summary><ul>", hou)
        self.assertIn('<li>Business: <a href="https://www.traicy.com/posts/20241125320947/">JAL sale 22-29 Nov 2024, Tokyo-Dallas DFW business JPY 600,000 (Texas fallback; no Houston business sale found)</a> ($3,784, read 2026-11-11)</li>', hou)
        self.assertGreater(hou.index("class=sources"), hou.index("class=reading"))
        tlv = out[out.index("<section id=tel-aviv>"):out.index("<section id=barcelona>")]
        self.assertNotIn("class=sources", tlv)  # sources but no line: nothing listed

    def test_sources_and_verdict_are_escaped(self):
        self.day()
        profiles = self.profiles()
        hou = profiles["routes"][0]
        hou["good_price"]["business"]["sources"] = [{"url": 'https://x.test/"><script>alert(1)</script>', "read": "2026-11-11", "price": 1, "note": "<b>sale</b> & more"}]
        real = self.page.config.load_profiles
        self.page.config.load_profiles = lambda: profiles
        try:
            out = self.page.render(self.conn())
        finally:
            self.page.config.load_profiles = real
        self.assertNotIn("<script>alert(1)</script>", out)
        self.assertIn('href="https://x.test/&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;"', out)
        self.assertIn("&lt;b&gt;sale&lt;/b&gt; &amp; more", out)
        self.assertIn("(reported sales, 1 source)", out)

    def test_a_route_with_no_good_price_renders_and_sends(self):
        self.day()
        profiles = self.profiles()
        for r in profiles["routes"]:
            if r["id"] in ("detroit", "barcelona"):
                del r["good_price"]
        real = self.page.config.load_profiles
        self.page.config.load_profiles = lambda: profiles
        stub = Stub(200)
        try:
            code, lines = self.run_main("--spine", stub.url)
        finally:
            self.page.config.load_profiles = real
            stub.close()
        self.assertEqual(code, 0)
        self.assertEqual(lines[-1], f"sent page to {stub.url}: sweep 1, 4 routes")
        sent = {s["route"]: s["verdict"] for s in json.loads(stub.bodies[0])["summary"]}
        for rid in ("detroit", "barcelona"):
            for v in sent[rid].values():
                if v:
                    self.assertEqual(v["word"], "no line yet")
        self.assertIn("<section id=detroit>", self.page_text())
