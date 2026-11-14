"""Ways to pay less: routes.json's `tactics`, a list at the end of each route section on the page
(session fares-tactics). Page only: the body sent to the Spine does not carry them.

Run: .venv/bin/python -m unittest discover -s tests -t .
Nothing leaves the machine: searches are stubs.
"""

import copy
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tests.test_spine import Base

ROUTES = ["houston", "detroit", "tel-aviv", "barcelona"]
RESEARCH = Path(__file__).resolve().parents[2] / "tactics-research.json"
HOSTILE = '<script>alert("x")</script> & \'quotes\''

# The page as fares/page.py at 8a36a38 (origin/main before this branch) renders the fixture store
# that TacticsTest.setUp builds: the stub captures of tests/test_spine.py's Base.day(), with the
# clock fixed at FIXED_NOW (capture dates and capture times both follow it), and 8a36a38's own
# routes.json, which has no tactics. To make it again, from the clone's root:
#   rm -rf /tmp/fares-8a36a38 && mkdir /tmp/fares-8a36a38
#   git archive 8a36a38 fares routes.json | tar -x -C /tmp/fares-8a36a38
#   .venv/bin/python -m tests.test_tactics --write-baseline /tmp/fares-8a36a38
# (result check on fares#8: the no-tactics test compares with the earlier code, not the new one).
BASELINE = Path(__file__).parent / "fixtures" / "page-8a36a38-no-tactics.html"
FIXED_NOW = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)


class FixedClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return FIXED_NOW if tz else FIXED_NOW.replace(tzinfo=None)


class TacticsTest(Base):
    def setUp(self):
        super().setUp()
        self.real_profiles = self.page.config.load_profiles
        self.real_clock = self.capture.datetime
        self.capture.datetime = FixedClock
        try:
            self.day(when=FIXED_NOW.strftime("%Y-%m-%dT%H:%M:%SZ"))
        finally:
            self.capture.datetime = self.real_clock

    def tearDown(self):
        self.page.config.load_profiles = self.real_profiles
        self.capture.datetime = self.real_clock
        super().tearDown()

    def render_with(self, change=None):
        """The page, from routes.json as `change(profiles)` leaves it."""
        profiles = copy.deepcopy(self.real_profiles())
        if change:
            change(profiles)
        self.page.config.load_profiles = lambda: profiles
        try:
            return self.page.render(self.conn())
        finally:
            self.page.config.load_profiles = self.real_profiles

    @staticmethod
    def section(html_text, rid):
        return re.search(rf"<section id={re.escape(rid)}>.*?</section>", html_text, re.S).group(0)

    @staticmethod
    def without_tactics(profiles):
        for r in profiles["routes"]:
            r.pop("tactics", None)

    def test_routes_json_copies_the_research_exactly(self):
        routes = {r["id"]: r for r in self.real_profiles()["routes"]}
        if RESEARCH.exists():  # the research file sits beside the clone on Dan's machine only
            research = json.loads(RESEARCH.read_text(encoding="utf-8"))
            for rid in ROUTES:
                self.assertEqual(routes[rid]["tactics"], research[rid], rid)
        for rid in ROUTES:
            self.assertTrue(routes[rid]["tactics"], rid)
            for t in routes[rid]["tactics"]:
                self.assertEqual(sorted(t), ["checked", "move", "source", "why"])
                self.assertIs(t["checked"], False)
                self.assertTrue(t["source"] == "our data" or t["source"].startswith("https://"), t["source"])

    def test_each_route_ends_with_its_block(self):
        out = self.render_with()
        for p in self.real_profiles()["routes"]:
            s = self.section(out, p["id"])
            self.assertEqual(s.count("<h3>Ways to pay less</h3>"), 1, p["id"])
            block = s[s.index("<h3>Ways to pay less</h3>"):]
            self.assertTrue(block.endswith("</ul></section>"), p["id"])  # last in the section, after the sources
            self.assertEqual(block.count("<li>"), len(p["tactics"]), p["id"])
            self.assertEqual(block.count("not yet checked against our prices"), len(p["tactics"]))
            # the verdict lines still open the section
            self.assertTrue(re.match(r"<section id=[a-z-]+><h2>[^<]*</h2>\n<p class=verdict>", s), p["id"])
            if "<details class=sources>" in s:
                self.assertLess(s.index("<details class=sources>"), s.index("<h3>Ways to pay less</h3>"))

    def test_a_line_reads_move_why_source_and_unchecked(self):
        s = self.section(self.render_with(), "houston")
        t = self.real_profiles()["routes"][0]["tactics"][0]
        self.assertIn(
            '<li><b>Fly ZIPAIR ZG16 from Narita in its lie-flat &quot;ZIP Full-Flat&quot; seat.</b> '
            + t["why"].replace("'", "&#x27;").replace('"', "&quot;")
            + ' <span class=meta>source: <a href="https://www.aviationwire.jp/archives/319331">www.aviationwire.jp</a>'
            ' · not yet checked against our prices</span></li>', s)

    def test_our_data_is_words_not_a_link(self):
        s = self.section(self.render_with(), "detroit")
        line = next(li for li in re.findall(r"<li>.*?</li>", s) if "one-stop business against Delta" in li)
        self.assertIn("<span class=meta>from our own data (LEARNING.md) · not yet checked against our prices</span>", line)
        self.assertNotIn("<a ", line)
        self.assertNotIn("our data", line.replace("our own data", ""))

    def test_hostile_strings_are_escaped(self):
        def hostile(profiles):
            profiles["routes"][0]["tactics"] = [
                {"move": HOSTILE, "why": HOSTILE, "source": 'https://example.com/a?b=1&c="><script>x</script>', "checked": False},
                {"move": "m", "why": "w", "source": 'javascript:alert("x")', "checked": False},
            ]
        s = self.section(self.render_with(hostile), "houston")
        block = s[s.index("<h3>Ways to pay less</h3>"):]
        self.assertNotIn("<script>", block)
        esc = "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt; &amp; &#x27;quotes&#x27;"
        self.assertIn(f"<li><b>{esc}</b> {esc} <span class=meta>source: ", block)
        self.assertIn('<a href="https://example.com/a?b=1&amp;c=&quot;&gt;&lt;script&gt;x&lt;/script&gt;">example.com</a>', block)
        # anything but an http(s) address is shown, never linked
        self.assertIn("<span class=meta>source: javascript:alert(&quot;x&quot;) · not yet", block)
        self.assertEqual(block.count("<a "), 1)

    def test_checked_drops_the_words(self):
        def checked(profiles):
            profiles["routes"][0]["tactics"] = [{"move": "m", "why": "w", "source": "our data", "checked": True}]
        s = self.section(self.render_with(checked), "houston")
        self.assertIn("<li><b>m</b> w <span class=meta>from our own data (LEARNING.md)</span></li>", s)
        self.assertNotIn("not yet checked", s)

    def test_no_tactics_renders_as_before(self):
        before = self.render_with(self.without_tactics)
        self.assertNotIn("Ways to pay less", before)
        # byte for byte the page 8a36a38's own code rendered from the same store (BASELINE above)
        self.assertEqual(before.encode("utf-8"), BASELINE.read_bytes())

        def empty(profiles):
            self.without_tactics(profiles)
            for r in profiles["routes"]:
                r["tactics"] = []
        self.assertEqual(self.render_with(empty), before)

        def one_missing(profiles):
            del profiles["routes"][2]["tactics"]
        out = self.render_with(one_missing)
        self.assertEqual(self.section(out, "tel-aviv"), self.section(before, "tel-aviv"))
        self.assertNotEqual(self.section(out, "houston"), self.section(before, "houston"))

    def test_the_spine_body_carries_no_tactics(self):
        c = self.conn()
        bodies = []
        for change in (None, self.without_tactics):
            out = self.render_with(change)
            body = self.page.spine_body(c, out, "2026-11-03T10:00:00Z")
            self.assertEqual(body["html"], out)
            bodies.append({k: v for k, v in body.items() if k != "html"})
        self.assertEqual(bodies[0], bodies[1])
        self.assertNotIn("tactic", json.dumps(bodies[0]).lower())
        self.assertNotIn("pay less", json.dumps(bodies[0]).lower())


RENDER_OLD = """
import sys
from fares import config, page, store
sys.stdout.write(page.render(store.connect(config.store_path())))
"""


def write_baseline(old_checkout):
    """Builds TacticsTest's fixture store, then renders it with the code in `old_checkout` (its own
    fares/ and routes.json, run in a separate interpreter) and saves the page as BASELINE."""
    t = TacticsTest("test_no_tactics_renders_as_before")
    t.setUp()
    try:
        out = subprocess.run([sys.executable, "-c", RENDER_OLD], cwd=old_checkout, check=True,
                             capture_output=True, env={**os.environ, "PYTHONPATH": str(old_checkout)}).stdout
    finally:
        t.tearDown()
    BASELINE.write_bytes(out)
    print(f"wrote {BASELINE} ({len(out)} bytes) from {old_checkout}")


if __name__ == "__main__" and sys.argv[1:2] == ["--write-baseline"]:
    write_baseline(Path(sys.argv[2]).resolve())
