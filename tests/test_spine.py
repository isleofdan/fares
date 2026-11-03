"""The summary bin/page sends to the Spine, and the send itself (session fares-three).

Run: .venv/bin/python -m unittest discover -s tests -t .
Every server here is a stub on loopback; nothing leaves the machine.
"""

import contextlib
import importlib
import io
import json
import os
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "tlv_business_payload.json"
ROUTES = ["houston", "detroit", "tel-aviv", "barcelona"]
NONSTOP = {
    "origin_airport": "NRT", "dest_airport": "TLV", "outbound_date": "2026-12-03",
    "carriers": "El Al", "carrier_codes": "LY", "flight_numbers": "LY92", "stops": 0, "via": "",
    "duration_min": 800, "price": 7100, "result_list": "best",
}


class Stub:
    """A loopback HTTP server answering every POST with `status` and `answer`, recording each body."""

    def __init__(self, status=200, answer=None, host="127.0.0.1"):
        self.bodies, self.headers = [], []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                n = int(self.headers.get("content-length") or 0)
                stub.bodies.append(self.rfile.read(n).decode("utf-8"))
                stub.headers.append(dict(self.headers))
                data = json.dumps(answer if answer is not None else {"ok": True}).encode()
                self.send_response(status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):
                pass

        cls = type("Server", (HTTPServer,), {"address_family": socket.AF_INET6 if ":" in host else socket.AF_INET})
        self.server = cls((host, 0), Handler)
        port = self.server.server_address[1]
        self.url = f"http://[{host}]:{port}/internal/fares/page" if ":" in host else f"http://{host}:{port}/internal/fares/page"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["FARES_DATA"] = self.tmp.name
        os.environ.pop("FARES_SPINE_URL", None)
        from fares import config
        importlib.reload(config)
        from fares import capture, gflights, page
        capture.PAUSE_SECONDS = 0
        self.capture, self.gflights, self.page = capture, gflights, page
        self.rows = gflights.parse_payload(json.loads(FIXTURE.read_text()))

    def tearDown(self):
        os.environ.pop("FARES_DATA", None)
        os.environ.pop("FARES_SPINE_URL", None)
        self.page.PUSH_TIMEOUT = 20
        self.tmp.cleanup()

    def day(self, bump=0, when=None, only=None):
        """A complete full sweep and a week scan (El Al's nonstop on Tel Aviv); `only` limits the
        full sweep's answers to one destination airport; `when` fixes the capture time."""
        g, cap = self.gflights, self.capture
        real = cap.now_utc
        if when:
            cap.now_utc = lambda: when
        try:
            rows = [dict(r, price=r["price"] + bump) for r in self.rows]
            cap.run(7, 1, search=lambda d, c, dep, ret: g.Answer(200, rows if only in (None, d) else []))
            nonstop = dict(NONSTOP, price=NONSTOP["price"] + bump)
            cap.run(7, None, week_scan=True,
                    search=lambda d, c, dep, ret: g.Answer(200, [nonstop] if d == "TLV" else []))
        finally:
            cap.now_utc = real

    def conn(self):
        from fares import config, store
        return store.connect(config.store_path())

    def body(self):
        c = self.conn()
        return self.page.spine_body(c, self.page.render(c), "2026-11-03T10:00:00Z")

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = self.page.main(list(argv))
        return code, out.getvalue().strip().splitlines()

    def page_text(self):
        from fares import config
        return config.page_path().read_text(encoding="utf-8")


class SummaryTest(Base):
    def shown_prices(self, out, rid, cabin):
        """The prices the page itself lists for a route and cabin (each fare line's bold price)."""
        import re
        sec = out[out.index(f"<section id={rid}>"):]
        sec = sec[:sec.index("</section>")]
        label = f"<span class=cabin>{cabin.title()}</span> <b>$"
        return [int(m.replace(",", "")) for m in re.findall(re.escape(label) + r"([\d,]+)</b>", sec)]

    def test_first_day(self):
        self.day()
        b = self.body()
        self.assertEqual(sorted(b), ["html", "rendered_at", "summary", "sweep"])
        self.assertEqual(b["sweep"], 1)
        self.assertEqual(b["rendered_at"], "2026-11-03T10:00:00Z")
        self.assertEqual([s["route"] for s in b["summary"]], ROUTES)
        for s in b["summary"]:
            self.assertEqual(sorted(s), ["against_typical", "cheapest", "days", "last_run", "route", "sweeps"])
            for cabin in ("business", "first"):
                self.assertEqual(s["cheapest"][cabin], min(self.shown_prices(b["html"], s["route"], cabin)))
                self.assertEqual(s["against_typical"][cabin], "first capture")
            self.assertEqual((s["sweeps"], s["days"]), (1, 1))
            self.assertEqual(s["last_run"], {"searches": 8, "refusals": 0})
        tlv = b["summary"][2]
        expected = min([r["price"] for r in self.rows if r["stops"] <= 1] + [NONSTOP["price"]])
        self.assertEqual(tlv["cheapest"]["business"], expected)

    def test_below_and_above_follow_the_page_line(self):
        self.day(when="2026-11-01T10:00:00Z")
        self.day(bump=-500)
        b = self.body()
        for s in b["summary"]:
            self.assertEqual(s["against_typical"], {"business": "below", "first": "below"})
            self.assertEqual((s["sweeps"], s["days"]), (2, 2))
            # The page says the same of that same price.
            price = f"<b>${s['cheapest']['business']:,}</b>"
            sec = b["html"][b["html"].index(f"<section id={s['route']}>"):]
            line = sec[sec.index(price):]
            self.assertIn("below the typical", line[:line.index("</li>")])

    def test_above(self):
        self.day(when="2026-11-01T10:00:00Z")
        self.day(bump=300)
        for s in self.body()["summary"]:
            self.assertEqual(s["against_typical"], {"business": "above", "first": "above"})

    def test_a_route_with_no_rows_sends_nulls(self):
        self.day(only="TLV")
        by = {s["route"]: s for s in self.body()["summary"]}
        for rid in ("houston", "detroit", "barcelona"):
            self.assertEqual(by[rid]["cheapest"], {"business": None, "first": None})
            self.assertEqual(by[rid]["against_typical"], {"business": None, "first": None})
            self.assertEqual((by[rid]["sweeps"], by[rid]["days"]), (0, 0))
            self.assertEqual(by[rid]["last_run"], {"searches": 8, "refusals": 0})
        self.assertIsNotNone(by["tel-aviv"]["cheapest"]["business"])

    def test_refusals_are_the_sweeps_failed_count(self):
        g = self.gflights
        n = [0]

        def some_refused(*a):
            n[0] += 1
            if n[0] % 4 == 0:
                raise g.Blocked("bot check page")
            return g.Answer(200, self.rows)

        self.assertTrue(self.capture.run(7, 2, search=some_refused)["completed"])
        for s in self.body()["summary"]:
            self.assertEqual(s["last_run"], {"searches": 16, "refusals": 4})

    def test_no_complete_sweep_sends_nothing(self):
        from fares import store, config
        store.connect(config.store_path()).close()
        stub = Stub()
        try:
            code, lines = self.run_main("--spine", stub.url)
        finally:
            stub.close()
        self.assertEqual(code, 0)
        self.assertEqual(stub.bodies, [])
        self.assertEqual(lines[-1], f"page not sent to {stub.url}: no complete full sweep yet")


class PushTest(Base):
    def setUp(self):
        super().setUp()
        self.day()

    def test_success_sends_the_written_page(self):
        stub = Stub(200, {"ok": True, "id": "fares-page-latest"})
        try:
            code, lines = self.run_main("--spine", stub.url)
        finally:
            stub.close()
        self.assertEqual(code, 0)
        self.assertEqual(len(stub.bodies), 1)
        sent = json.loads(stub.bodies[0])
        self.assertEqual(sorted(sent), ["html", "rendered_at", "summary", "sweep"])
        self.assertEqual(sent["html"], self.page_text())
        self.assertEqual([s["route"] for s in sent["summary"]], ROUTES)
        self.assertRegex(sent["rendered_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual({k.lower(): v for k, v in stub.headers[0].items()}.get("content-type"), "application/json")
        self.assertNotIn("authorization", {k.lower() for k in stub.headers[0]})
        self.assertEqual(lines, [f"wrote {Path(self.tmp.name) / 'fares.html'}", f"sent page to {stub.url}: sweep 1, 4 routes"])

    def test_an_ipv6_literal_address(self):
        stub = Stub(200, host="::1")
        try:
            code, lines = self.run_main("--spine", stub.url)
        finally:
            stub.close()
        self.assertEqual(code, 0)
        self.assertTrue(stub.url.startswith("http://[::1]:"))
        self.assertEqual(json.loads(stub.bodies[0])["html"], self.page_text())
        self.assertEqual(lines[-1], f"sent page to {stub.url}: sweep 1, 4 routes")

    def test_the_setting_names_the_default_address(self):
        from fares import config
        self.assertEqual(config.SPINE_URL, "http://spine-dan.internal:8080/internal/fares/page")
        self.assertEqual(config.spine_url(), config.SPINE_URL)
        stub = Stub(200)
        os.environ["FARES_SPINE_URL"] = stub.url
        try:
            code, lines = self.run_main()
        finally:
            stub.close()
        self.assertEqual((code, len(stub.bodies)), (0, 1))
        self.assertEqual(lines[-1], f"sent page to {stub.url}: sweep 1, 4 routes")

    def test_no_push_sends_nothing(self):
        stub = Stub(200)
        os.environ["FARES_SPINE_URL"] = stub.url
        try:
            code, lines = self.run_main("--no-push")
        finally:
            stub.close()
        self.assertEqual((code, stub.bodies), (0, []))
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("wrote "))
        self.assertTrue(Path(self.tmp.name, "fares.html").exists())

    def test_a_refusal_prints_the_spines_error_and_exits_0(self):
        error = "summary[2].route must be one of houston, detroit, tel-aviv, barcelona, not 'tlv'."
        stub = Stub(400, {"error": error})
        try:
            code, lines = self.run_main("--spine", stub.url)
        finally:
            stub.close()
        self.assertEqual(code, 0)
        self.assertEqual(len(stub.bodies), 1)  # one try, no retry
        self.assertEqual(self.page_text(), json.loads(stub.bodies[0])["html"])
        self.assertEqual(lines[-1], f"page not sent to {stub.url}: the Spine answered HTTP 400: {error}")
        self.assertEqual(len(lines), 2)

    def test_an_error_answer_that_breaks_off_prints_one_line_and_exits_0(self):
        # dev-check, fares-three: a 400 declaring 100 bytes of body and closing after 9 made
        # e.read() raise IncompleteRead inside the error handler, and bin/page exit 1.
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        url = f"http://127.0.0.1:{s.getsockname()[1]}/internal/fares/page"

        def answer():
            conn, _ = s.accept()
            data = b""
            while b"\r\n\r\n" not in data:
                data += conn.recv(65536)
            head, rest = data.split(b"\r\n\r\n", 1)
            length = int([l for l in head.split(b"\r\n") if l.lower().startswith(b"content-length:")][0].split(b":")[1])
            while len(rest) < length:
                rest += conn.recv(65536)
            conn.sendall(b"HTTP/1.1 400 Bad Request\r\ncontent-type: application/json\r\ncontent-length: 100\r\n\r\n{\"error\":")
            conn.close()

        t = threading.Thread(target=answer, daemon=True)
        t.start()
        try:
            code, lines = self.run_main("--spine", url)
        finally:
            t.join(5)
            s.close()
        self.assertEqual(code, 0)
        self.assertTrue(Path(self.tmp.name, "fares.html").exists())
        self.assertEqual(len(lines), 2, lines)
        self.assertEqual(lines[-1], f"page not sent to {url}: the Spine answered HTTP 400: (its answer broke off: IncompleteRead)")

    def test_a_closed_port_prints_one_line_and_exits_0(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        url = f"http://127.0.0.1:{port}/internal/fares/page"
        code, lines = self.run_main("--spine", url)
        self.assertEqual(code, 0)
        self.assertTrue(Path(self.tmp.name, "fares.html").exists())
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].startswith(f"page not sent to {url}: "), lines[-1])
        self.assertIn("refused", lines[-1].lower())

    def test_a_silent_listener_times_out_once_and_exits_0(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        s.listen(5)  # accepts the connection, never answers
        url = f"http://127.0.0.1:{s.getsockname()[1]}/internal/fares/page"
        self.page.PUSH_TIMEOUT = 1
        try:
            code, lines = self.run_main("--spine", url)
        finally:
            s.close()
        self.assertEqual(code, 0)
        self.assertTrue(Path(self.tmp.name, "fares.html").exists())
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[-1].startswith(f"page not sent to {url}: "), lines[-1])
        self.assertIn("timed out", lines[-1])

    def test_the_default_timeout_is_20_seconds(self):
        self.assertEqual(self.page.PUSH_TIMEOUT, 20)


if __name__ == "__main__":
    unittest.main()
