"""Write one plain HTML page from the store: today's prices on each route against that route's history.

Run: bin/page   (writes /data/home/dan/fares-data/fares.html)
"""

import html
import sqlite3
import statistics
import sys
from datetime import date, datetime, timedelta, timezone

from . import config, store

TOKYO = timezone(timedelta(hours=9))
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CABINS = ("business", "first")


def tokyo_time(utc_iso: str) -> str:
    t = datetime.strptime(utc_iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).astimezone(TOKYO)
    return t.strftime("%-d %b %Y %H:%M") + " Tokyo time"


def short_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{WEEKDAYS[d.weekday()]} {d.day} {d.strftime('%b')}"


def money(n: int) -> str:
    return f"${n:,}"


def latest_captures(conn):
    """The newest completed full sweep, and the newest completed week scan from the same UTC day
    (or None). Interrupted, crashed or throttled sweeps are never shown as today's prices, and an
    older week scan is never mixed into a newer day."""
    full = conn.execute(
        "SELECT * FROM sweeps WHERE completed = 1 AND grid_step_days > 1 AND rows_written > 0"
        " ORDER BY id DESC LIMIT 1").fetchone()
    if full is None:
        return None, None
    scan = conn.execute(
        "SELECT * FROM sweeps WHERE completed = 1 AND grid_step_days = 1 AND rows_written > 0"
        " AND substr(started_at, 1, 10) = ? ORDER BY id DESC LIMIT 1",
        (full["started_at"][:10],)).fetchone()
    return full, scan


def cheapest(rows):
    return min(rows, key=lambda r: r["price"]) if rows else None


def history(conn, route, cabin, kind, carrier, before_day):
    """Cheapest price of this kind of trip on each capture day (UTC date) before `before_day`,
    oldest first. Earlier sweeps on the same day are not history: they are today."""
    cond = "stops = 0 AND carrier_codes = ?" if kind == "nonstop" else "stops = 1"
    args = [route, cabin, before_day] + ([carrier] if kind == "nonstop" else [])
    return conn.execute(
        f"SELECT substr(captured_at, 1, 10) AS day, MIN(price) AS low FROM fares"
        f" WHERE route = ? AND cabin = ? AND substr(captured_at, 1, 10) < ? AND {cond}"
        f" AND sweep_id IN (SELECT id FROM sweeps WHERE completed = 1)"
        f" GROUP BY day ORDER BY day", args).fetchall()


def compare(today_price, past):
    if not past:
        return "first capture: the comparison fills in as days pass"
    lows = [r["low"] for r in past]
    best = min(past, key=lambda r: r["low"])
    typical = int(statistics.median(lows))
    diff = today_price - typical
    word = "below" if diff < 0 else "above"
    return (f"{money(abs(diff))} {word} the typical {money(typical)} over {len(lows)} earlier day(s);"
            f" lowest seen {money(best['low'])} on {best['day']}")


def mixed_cabin_note(row, cabin):
    """Plain words when not every outbound flight is in the searched cabin; empty otherwise."""
    if not row["segment_cabins"]:
        return ""
    cabins = row["segment_cabins"].split(",")
    if all(c == cabin for c in cabins):
        return ""
    flights = row["flight_numbers"].split()
    parts = [f"{f} {c}" for f, c in zip(flights, cabins)]
    return f" <span class=mixed>mixed cabins: {html.escape(', '.join(parts))}</span>"


def fare_line(conn, row, kind, route, cabin, day):
    past = history(conn, route, cabin, kind, row["carrier_codes"], day)
    via = f" via {row['via']}" if row["via"] else ""
    return (
        f"<b>{money(row['price'])}</b> round trip, {html.escape(row['carriers'])}"
        f" ({html.escape(row['flight_numbers'])}{via}), {row['origin_airport']}–{row['dest_airport']},"
        f" out {short_date(row['depart_date'])}, back {short_date(row['return_date'])}"
        f"{mixed_cabin_note(row, cabin)}"
        f"<br><span class=meta>{compare(row['price'], past)} · captured {tokyo_time(row['captured_at'])}"
        f" · {html.escape(row['source'])}</span>"
    )


def nonstop_days(rows):
    """Carrier code -> sorted weekdays on which today's searches found its nonstop departing."""
    days = {}
    for r in rows:
        if r["stops"] == 0:
            days.setdefault(r["carrier_codes"], set()).add(date.fromisoformat(r["depart_date"]).weekday())
    return {c: sorted(d) for c, d in days.items()}


def route_section(conn, profile, full, scan):
    rid = profile["id"]
    q = "SELECT * FROM fares WHERE route = ? AND sweep_id = ?"
    rows = conn.execute(q, (rid, full["id"])).fetchall() if full else []
    scan_rows = conn.execute(q, (rid, scan["id"])).fetchall() if scan else []
    today = rows + scan_rows
    # History is everything captured on days before today's full sweep.
    day = full["started_at"][:10] if full else "9999"
    days = nonstop_days(today)
    names = {r["carrier_codes"]: r["carriers"] for r in today if r["stops"] == 0}
    expected = profile.get("always_first") or {}
    first_carrier = expected.get("carrier")
    nonstop_carriers = sorted(names, key=lambda c: (c != first_carrier, c))
    if first_carrier and first_carrier not in nonstop_carriers:
        nonstop_carriers.insert(0, first_carrier)

    parts = [f"<section id={rid}><h2>Tokyo – {html.escape(profile['city'])}</h2>",
             "<p class=rules>Rules: " + " ".join(html.escape(r) for r in profile["rules"]) + "</p>"]

    reading = []
    for code in nonstop_carriers:
        name = names.get(code) or (expected.get("name") if code == first_carrier else None) or code
        wd = days.get(code)
        freq = (f"seen departing on {', '.join(WEEKDAYS[d] for d in wd)} ({len(wd)} day{'s' if len(wd) > 1 else ''}"
                f" a week in today's searches)" if wd else "not seen departing on any day searched today")
        parts.append(f"<h3>Nonstop: {html.escape(name)} <span class=meta>{freq}"
                     + (f"; week scan captured {tokyo_time(scan['finished_at'])} · {html.escape(scan['source'])}"
                        if scan else "") + "</span></h3><ul>")
        for cabin in CABINS:
            best = cheapest([r for r in today if r["cabin"] == cabin and r["stops"] == 0 and r["carrier_codes"] == code])
            if best:
                parts.append(f"<li><span class=cabin>{cabin.title()}</span> "
                             f"{fare_line(conn, best, 'nonstop', rid, cabin, day)}</li>")
            else:
                parts.append(f"<li><span class=cabin>{cabin.title()}</span> none found in this capture"
                             + (f" (captured {tokyo_time(full['finished_at'])} · {html.escape(full['source'])})" if full else "")
                             + "</li>")
        parts.append("</ul>")
    if not nonstop_carriers:
        parts.append("<h3>Nonstop</h3><ul><li>none found in this capture"
                     + (f" (captured {tokyo_time(full['finished_at'])} · {html.escape(full['source'])})" if full else "")
                     + "</li></ul>")

    parts.append("<h3>Cheapest one-stop</h3><ul>")
    one_stop = {}
    for cabin in CABINS:
        best = cheapest([r for r in today if r["cabin"] == cabin and r["stops"] == 1])
        one_stop[cabin] = best
        if best:
            parts.append(f"<li><span class=cabin>{cabin.title()}</span> "
                         f"{fare_line(conn, best, 'one-stop', rid, cabin, day)}</li>")
        else:
            parts.append(f"<li><span class=cabin>{cabin.title()}</span> none found in this capture</li>")
    parts.append("</ul>")

    # The plain-words reading.
    biz_ns = [cheapest([r for r in today if r["cabin"] == "business" and r["stops"] == 0 and r["carrier_codes"] == c])
              for c in nonstop_carriers]
    biz_ns = [r for r in biz_ns if r]
    if nonstop_carriers:
        seen = [names.get(c, c) for c in nonstop_carriers if c in names]
        missing = [c for c in nonstop_carriers if c not in names]
        if seen:
            reading.append(f"Nonstop service found today: {', '.join(seen)}.")
        if missing:
            missing = [expected.get("name", c) if c == first_carrier else c for c in missing]
            reading.append(f"The expected nonstop ({', '.join(missing)}) did not appear in any search today;"
                           " it may not fly on the days searched, or may be sold out or not sold in this cabin.")
    else:
        reading.append("No nonstop appeared in any search today; every option connects somewhere.")
    ob = one_stop.get("business")
    if ob:
        reading.append(f"The cheapest one-stop business trip is {money(ob['price'])} on {ob['carriers']}"
                       + (f", changing planes in {ob['via']}" if ob["via"] else "") + ".")
        if biz_ns:
            ns = min(biz_ns, key=lambda r: r["price"])
            gap = ns["price"] - ob["price"]
            reading.append(f"Flying nonstop in business costs {money(abs(gap))} {'more' if gap >= 0 else 'less'}"
                           f" ({ns['carriers']}, {money(ns['price'])}).")
    of = one_stop.get("first")
    if of:
        mixed = " with first class on only part of the way" if mixed_cabin_note(of, "first") else ""
        reading.append(f"First class with one stop starts at {money(of['price'])} ({of['carriers']}){mixed}.")
    hubs = sorted({r["via"] for r in today if r["stops"] == 1 and r["via"]})
    if hubs:
        reading.append(f"One-stop trips today connect through {len(hubs)} airports: {', '.join(hubs)}.")
    past_days = conn.execute("SELECT COUNT(DISTINCT substr(captured_at,1,10)) FROM fares WHERE route = ?"
                             " AND substr(captured_at,1,10) < ?"
                             " AND sweep_id IN (SELECT id FROM sweeps WHERE completed = 1)", (rid, day)).fetchone()[0]
    if not past_days:
        reading.append("This is the first day of history, so nothing here can be called a deal yet:"
                       " after a few weeks each price will be marked against this route's usual level.")
    parts.append("<p class=reading>" + html.escape(" ".join(reading)) + "</p></section>")
    return "\n".join(parts)


CSS = """
:root { --bg:#fff; --fg:#1d1d1f; --muted:#5f6368; --line:#e3e3e3; --accent:#0b57d0; }
@media (prefers-color-scheme: dark) { :root { --bg:#151515; --fg:#ececec; --muted:#a0a0a0; --line:#333; --accent:#8ab4f8; } }
body { background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, sans-serif; max-width:52rem; margin:0 auto; padding:1rem; }
h1 { font-size:1.5rem; margin-bottom:.2rem; } h2 { margin-top:2rem; border-bottom:2px solid var(--line); }
h3 { font-size:1.05rem; margin:.8rem 0 .2rem; }
ul { padding-left:1.2rem; margin:.2rem 0; } li { margin:.35rem 0; }
.meta { color:var(--muted); font-size:.85rem; font-weight:normal; }
.mixed { color:#b06000; font-size:.85rem; }
@media (prefers-color-scheme: dark) { .mixed { color:#f6ae5c; } }
.cabin { display:inline-block; min-width:5.5rem; font-weight:600; }
.rules, .intro { color:var(--muted); font-size:.9rem; }
.reading { background:color-mix(in srgb, var(--accent) 8%, transparent); padding:.7rem .9rem; border-radius:6px; }
dl { font-size:.9rem; } dt { font-weight:600; } dd { margin:0 0 .4rem 0; color:var(--muted); }
"""


def render(conn) -> str:
    profiles = config.load_profiles()
    full, scan = latest_captures(conn)
    head = (f"<p class=intro>Latest full capture: {tokyo_time(full['finished_at'])}, {full['queries']} searches on "
            f"{html.escape(full['source'])}, {full['rows_written']} prices recorded. "
            if full else "<p class=intro>No complete capture yet. ")
    if full and full["failed_queries"]:
        head += (f"<b>{full['failed_queries']} of those searches were refused or failed</b>, so some departure dates"
                 " are missing from today's prices. ")
    if full and not scan:
        head += "No week scan finished today, so nonstop weekdays come from the main searches only. "
    head += ("Every price is for one adult, round trip from Tokyo (Narita or Haneda), 7 nights, in US dollars, "
             "as the source showed it at the capture time; taxes included.</p>")
    glossary = """<details><summary>Words used on this page</summary><dl>
<dt>Round trip from</dt><dd>The source lists outbound flights, each with the cheapest round-trip price that includes it. The return flight is not chosen yet.</dd>
<dt>Nonstop</dt><dd>One flight, no change of plane. <b>One-stop</b>: one change of plane on the way out.</dd>
<dt>via</dt><dd>The airport where you change planes, as a three-letter airport code (FRA = Frankfurt).</dd>
<dt>Typical</dt><dd>The middle value (median) of the cheapest price found on each earlier day: half the days were cheaper, half dearer. A price well below it is a candidate deal.</dd>
<dt>Week scan</dt><dd>The daily capture searches one departure every two weeks, always on the same weekday, so a separate search of seven days in a row (four weeks out, business) shows which days each nonstop flies. A nonstop that is sold out or not offered on a day searched will not show on that day.</dd>
<dt>Mixed cabins</dt><dd>A first class search can return a trip that is first class on the long flight but business (or lower) on a connecting flight, because few short flights have a first class cabin. Such trips are marked with the cabin of each outbound flight.</dd>
<dt>Capture</dt><dd>One run of the searches; each price is stamped with the time it was seen and where.</dd>
</dl></details>"""
    sections = [route_section(conn, p, full, scan) for p in profiles["routes"]]
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width, initial-scale=1'><title>Premium fares from Tokyo</title>"
            f"<style>{CSS}</style></head><body><h1>Premium fares from Tokyo</h1>{head}{glossary}"
            + "\n".join(sections) + "</body></html>")


def main(argv=None) -> int:
    path = config.store_path()
    if not path.exists():
        print(f"no store at {path}; run bin/capture first", file=sys.stderr)
        return 1
    conn = store.connect(path)
    out = config.page_path()
    tmp = out.with_suffix(".html.tmp")
    tmp.write_text(render(conn), encoding="utf-8")
    tmp.replace(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
