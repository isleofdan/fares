"""Write one plain HTML page from the store: today's prices on each route against that route's history,
then send it, with a short summary per route, to the Spine's private listener (session fares-three).

Run: bin/page   (writes /data/home/dan/fares-data/fares.html, then sends it to the Spine)
     bin/page --no-push   (writes the page only)
     bin/page --spine <url>   (sends to another address; FARES_SPINE_URL sets the default)
"""

import argparse
import html
import json
import sqlite3
import statistics
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

from . import capture, config, store

TOKYO = timezone(timedelta(hours=9))
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
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


def standing(today_price, past):
    """Where today's price stands against its history: None when there is no earlier day, else the
    word ("below" or "above"), the difference, the typical (median) daily low, the number of earlier
    days and the lowest day. The page's compare() line and the Spine summary both read this."""
    if not past:
        return None
    lows = [r["low"] for r in past]
    typical = int(statistics.median(lows))
    diff = today_price - typical
    return {"word": "below" if diff < 0 else "above", "diff": diff, "typical": typical,
            "days": len(lows), "best": min(past, key=lambda r: r["low"])}


def compare(today_price, past):
    s = standing(today_price, past)
    if s is None:
        return "first capture: the comparison fills in as days pass"
    return (f"{money(abs(s['diff']))} {s['word']} the typical {money(s['typical'])} over {s['days']} earlier day(s);"
            f" lowest seen {money(s['best']['low'])} on {s['best']['day']}")


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


def history_counts(conn, route):
    """Completed full sweeps (never week scans, never incomplete ones) that hold rows for the route,
    the capture days they fall on (UTC dates, the same days `history` groups by), and the first and
    latest capture times. The page's history line and the Spine summary both read this."""
    return conn.execute(
        "SELECT COUNT(DISTINCT sweep_id) AS sweeps, COUNT(DISTINCT substr(captured_at, 1, 10)) AS days,"
        " MIN(captured_at) AS first, MAX(captured_at) AS latest FROM fares WHERE route = ?"
        " AND sweep_id IN (SELECT id FROM sweeps WHERE completed = 1 AND grid_step_days > 1)",
        (route,)).fetchone()


def history_line(conn, route):
    """How much history this route's comparisons rest on (history_counts), with the span of the
    capture times in Tokyo time."""
    r = history_counts(conn, route)
    if not r["sweeps"]:
        return "<p class=history>History: no complete full sweep holds this route yet.</p>"
    sweeps = f"{r['sweeps']} complete full sweep{'s' if r['sweeps'] > 1 else ''}"
    days = f"{r['days']} capture day{'s' if r['days'] > 1 else ''} (UTC dates, as the comparisons count them)"
    return (f"<p class=history>History: {sweeps} on {days},"
            f" {tokyo_time(r['first'])} – {tokyo_time(r['latest'])}.</p>")


def nonstop_days(rows):
    """Carrier code -> sorted weekdays on which today's searches found its nonstop departing."""
    days = {}
    for r in rows:
        if r["stops"] == 0:
            days.setdefault(r["carrier_codes"], set()).add(date.fromisoformat(r["depart_date"]).weekday())
    return {c: sorted(d) for c, d in days.items()}


def today_rows(conn, rid, full, scan):
    """Today's rows for a route: the newest complete full sweep's and the same day's week scan's."""
    q = "SELECT * FROM fares WHERE route = ? AND sweep_id = ?"
    rows = conn.execute(q, (rid, full["id"])).fetchall() if full else []
    scan_rows = conn.execute(q, (rid, scan["id"])).fetchall() if scan else []
    return rows + scan_rows


def history_day(full):
    """History is everything captured on days before today's full sweep."""
    return full["started_at"][:10] if full else "9999"


# --- the good-price line and the verdict (session fares-verdict, 11 Nov 2026) ----------------
#
# Each route and cabin gets a line below which a fare counts as a deal, from the first of these
# that exists (PLAN.md, "Decision: the good-price line"):
#   1. Dan's own number (routes.json good_price.<cabin>.dan);
#   2. once there are OWN_DAYS or more capture days of the same kind of trip (that nonstop
#      carrier, or one-stop), the lowest tenth of our own daily cheapest prices (history());
#   3. the researched line from reported sales (good_price.<cabin>.amount, with its sources);
#   4. none.
# The verdict sets today's cheapest nonstop or one-stop trip (route_summary's row) against it.

OWN_DAYS = 60


def lowest_tenth(lows):
    """The 10th percentile of the daily cheapest prices, by the nearest-rank method: sorted
    ascending, the value at rank ceil(n / 10) counting from 1 (the 6th lowest of 60 days). It is
    always one of our own prices, never interpolated between two."""
    ordered = sorted(lows)
    return ordered[max(1, -(-len(ordered) // 10)) - 1]


def good_price(conn, profile, cabin, kind, carrier, before_day):
    """The good-price line for a route and cabin and the kind of trip today's cheapest is:
    (amount, basis in words), or (None, None) when there is no line."""
    gp = (profile.get("good_price") or {}).get(cabin) or {}
    if gp.get("dan") is not None:
        return int(round(gp["dan"])), "Dan's own number"
    lows = [r["low"] for r in history(conn, profile["id"], cabin, kind, carrier, before_day)]
    if len(lows) >= OWN_DAYS:
        return lowest_tenth(lows), f"lowest tenth of {len(lows)} days of our prices"
    if gp.get("amount") is not None:
        n = len(gp.get("sources") or [])
        return gp["amount"], f"reported sales, {n} source{'s' if n != 1 else ''}"
    return None, None


def is_researched(basis):
    return bool(basis) and basis.startswith("reported sales")


def scope_text():
    """What the daily search covers, from the grid itself (fares/capture.py): the weekday every
    departure falls on and the trip length. See PLAN.md, "Open issues"."""
    return f"{WEEKDAY_NAMES[capture.GRID_EPOCH.weekday()]} departures, {capture.NIGHTS}-night trips"


def route_verdict(conn, profile, full, scan):
    """{business, first}: each None when no nonstop or one-stop trip was found today, else
    {word, price, depart, line, gap, basis, scope}; word "deal" at or under the line, "not a deal"
    above it, "no line yet" without one; gap = price - line."""
    rid = profile["id"]
    today = [r for r in today_rows(conn, rid, full, scan) if r["stops"] <= 1]
    day = history_day(full)
    out = {}
    for cabin in CABINS:
        best = cheapest([r for r in today if r["cabin"] == cabin])
        if best is None:
            out[cabin] = None
            continue
        kind = "nonstop" if best["stops"] == 0 else "one-stop"
        line, basis = good_price(conn, profile, cabin, kind, best["carrier_codes"], day)
        price = best["price"]
        word = "no line yet" if line is None else ("deal" if price <= line else "not a deal")
        out[cabin] = {"word": word, "price": price, "depart": best["depart_date"], "line": line,
                      "gap": None if line is None else price - line, "basis": basis, "scope": scope_text()}
    return out


def verdict_line(cabin, v):
    """One cabin's verdict as a line on the page, every piece escaped."""
    head = f"<span class=cabin>{cabin.title()}</span> "
    if v is None:
        return f"<p class=verdict>{head}none found in this capture</p>"
    if v["word"] == "no line yet":
        said = "<b>no good-price line yet</b>"
    else:
        gap = v["gap"]
        where = (f"{money(-gap)} under" if gap < 0 else f"{money(gap)} over" if gap > 0 else "right at")
        said = (f"<b>{html.escape('a deal' if v['word'] == 'deal' else 'not a deal')}</b>,"
                f" {where} the good-price line {money(v['line'])} ({html.escape(v['basis'])})")
    return (f"<p class=verdict>{head}<b>{money(v['price'])}</b> out {html.escape(short_date(v['depart']))}: {said}."
            f" <span class=meta>{html.escape(v['scope'])}</span></p>")


def sources_list(profile, verdict):
    """The reported sales behind each researched line in use, as links; empty when none."""
    items = []
    for cabin in CABINS:
        v = verdict.get(cabin)
        if not v or not is_researched(v["basis"]):
            continue
        for src in ((profile.get("good_price") or {}).get(cabin) or {}).get("sources") or []:
            items.append(f"<li>{cabin.title()}: <a href=\"{html.escape(src['url'], quote=True)}\">{html.escape(src['note'])}</a>"
                         f" ({money(src['price'])}, read {html.escape(src['read'])})</li>")
    if not items:
        return ""
    return "<details class=sources><summary>Where the good-price line comes from</summary><ul>" + "".join(items) + "</ul></details>"


def route_section(conn, profile, full, scan):
    rid = profile["id"]
    today = today_rows(conn, rid, full, scan)
    day = history_day(full)
    days = nonstop_days(today)
    names = {r["carrier_codes"]: r["carriers"] for r in today if r["stops"] == 0}
    expected = profile.get("always_first") or {}
    first_carrier = expected.get("carrier")
    nonstop_carriers = sorted(names, key=lambda c: (c != first_carrier, c))
    if first_carrier and first_carrier not in nonstop_carriers:
        nonstop_carriers.insert(0, first_carrier)

    verdict = route_verdict(conn, profile, full, scan)
    parts = [f"<section id={rid}><h2>Tokyo – {html.escape(profile['city'])}</h2>",
             *(verdict_line(c, verdict[c]) for c in CABINS),
             "<p class=rules>Rules: " + " ".join(html.escape(r) for r in profile["rules"]) + "</p>",
             history_line(conn, rid)]

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
        # Only the comparisons wait for history; the verdict above can already say "a deal" from
        # Dan's number or reported sales (session fares-verdict).
        reading.append("This is the first day of history, so no price here can be compared with this route's own"
                       " past yet: after a few weeks each price will be marked against this route's usual level.")
    parts.append("<p class=reading>" + html.escape(" ".join(reading)) + "</p>")
    parts.append(sources_list(profile, verdict) + "</section>")
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
.history { font-size:.9rem; margin:.3rem 0; }
.verdict { margin:.35rem 0; font-size:1.02rem; }
.sources { font-size:.85rem; margin-top:.6rem; } .sources li { margin:.2rem 0; }
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
<dt>Typical</dt><dd>The middle value (median) of the cheapest price found on each earlier day: half the days were cheaper, half dearer. A price well below it is cheap for this route; whether it is a deal is the verdict.</dd>
<dt>Verdict</dt><dd>The line at the top of each route: today's cheapest nonstop or one-stop trip against a good-price line (Dan's own number, else the lowest tenth of 60 or more days of our prices, else reported sales), read as a deal (at or under it), not a deal, or no good-price line yet.</dd>
<dt>Week scan</dt><dd>The daily capture searches one departure every two weeks, always on the same weekday, so a separate search of seven days in a row (four weeks out, business) shows which days each nonstop flies. A nonstop that is sold out or not offered on a day searched will not show on that day.</dd>
<dt>Mixed cabins</dt><dd>A first class search can return a trip that is first class on the long flight but business (or lower) on a connecting flight, because few short flights have a first class cabin. Such trips are marked with the cabin of each outbound flight.</dd>
<dt>Capture</dt><dd>One run of the searches; each price is stamped with the time it was seen and where.</dd>
</dl></details>"""
    sections = [route_section(conn, p, full, scan) for p in profiles["routes"]]
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width, initial-scale=1'><title>Premium fares from Tokyo</title>"
            f"<style>{CSS}</style></head><body><h1>Premium fares from Tokyo</h1>{head}{glossary}"
            + "\n".join(sections) + "</body></html>")


# --- the Spine --------------------------------------------------------------------------------

def route_summary(conn, rid, full, scan):
    """One route's line for the Spine, from the same rows and functions the page uses. The page lists
    nonstop and one-stop trips only, so the cheapest is the lowest of those (stops <= 1); its standing
    is compare()'s, against the history of its kind (that nonstop carrier, or one-stop)."""
    today = [r for r in today_rows(conn, rid, full, scan) if r["stops"] <= 1]
    day = history_day(full)
    out = {"route": rid, "cheapest": {}, "against_typical": {}}
    for cabin in CABINS:
        best = cheapest([r for r in today if r["cabin"] == cabin])
        if best is None:
            out["cheapest"][cabin] = out["against_typical"][cabin] = None
            continue
        kind = "nonstop" if best["stops"] == 0 else "one-stop"
        s = standing(best["price"], history(conn, rid, cabin, kind, best["carrier_codes"], day))
        out["cheapest"][cabin] = best["price"]
        out["against_typical"][cabin] = s["word"] if s else "first capture"
    counts = history_counts(conn, rid)
    out["sweeps"], out["days"] = counts["sweeps"], counts["days"]
    # The whole sweep's numbers, as capture.log prints them (queries=, failed=), on every route.
    out["last_run"] = {"searches": full["queries"] if full else 0, "refusals": full["failed_queries"] if full else 0}
    return out


# --- comparison lenses (session fares-lenses, 11 Nov 2026) -----------------------------------
#
# The strip's "below/above typical" (route_summary's against_typical) compares today's cheapest
# trip, on any departure date, with the median of earlier days' cheapest of the same kind. That
# mixes a cheap February date one day with a dear summer date the next. Each lens below answers
# one sharper question, for nonstop and one-stop trips in the cabin (the trips the page lists),
# from complete full sweeps only:
#
#   date    Each departure date's price today against that same date's price on earlier capture
#           days (or, while a date has no earlier day, the same Monday-to-Sunday week); the lens
#           shows the date that stands best against its own history.
#   month   The same, by month of departure.
#   any     Today's cheapest on any date against earlier days' cheapest on any date (the old
#           comparison, of the same kind of trip).
#   lowest  Today's cheapest against the lowest price ever seen for the route and cabin.
#
# Within NEAR (3 %) of the typical the word is "near"; otherwise "below" or "above". A lens with no
# earlier day says "first capture"; the date, month and any lenses with fewer than EARLY_DAYS earlier
# capture days say "early" (session fares-verdict). Each cell carries `days`, the earlier capture
# days it compared with. Every cell has the same keys, so the Spine can show any lens.

NEAR = 0.03
LENSES = ("date", "month", "any", "lowest")
EARLY_DAYS = 7  # below this many earlier capture days a lens says "early" (the lowest lens never does)


def lens_word(price, typical):
    diff = price - typical
    if abs(diff) <= NEAR * typical:
        return "near"
    return "below" if diff < 0 else "above"


def lens_cell(word, price, typical=None, depart=None, basis=None, days=None):
    """`days`: how many earlier capture days the lens compared with (None for "first capture")."""
    return {"word": word, "price": price, "typical": typical,
            "diff": None if typical is None else price - typical, "depart": depart, "basis": basis,
            "days": days}


def week_of(iso):
    d = date.fromisoformat(iso)
    return (d - timedelta(days=d.weekday())).isoformat()


def past_by_day_and_date(conn, route, cabin, before_day):
    """{capture day: {departure date: cheapest price}} over complete full sweeps before `before_day`."""
    out = {}
    for r in conn.execute(
            "SELECT substr(captured_at, 1, 10) AS day, depart_date, MIN(price) AS low FROM fares"
            " WHERE route = ? AND cabin = ? AND stops <= 1 AND substr(captured_at, 1, 10) < ?"
            " AND sweep_id IN (SELECT id FROM sweeps WHERE completed = 1 AND grid_step_days > 1)"
            " GROUP BY day, depart_date", (route, cabin, before_day)):
        out.setdefault(r["day"], {})[r["depart_date"]] = r["low"]
    return out


def grouped_lens(today_lows, past, key, fallback_key=None):
    """today_lows: {departure date: price}. For each group of dates (`key`), today's cheapest in it
    against the median over earlier days of each day's cheapest in it; the group whose price stands
    lowest against its typical wins. `fallback_key` is tried for a group with no earlier day."""
    best = None
    groups = {}
    for d, p in today_lows.items():
        g = key(d)
        if g not in groups or p < groups[g][1]:
            groups[g] = (d, p)
    for g, (d, p) in groups.items():
        basis = None
        for k, name in ((key, None), (fallback_key, "week")):
            if k is None:
                continue
            lows = [min(v for dd, v in dates.items() if k(dd) == k(d))
                    for dates in past.values() if any(k(dd) == k(d) for dd in dates)]
            if lows:
                basis = name
                break
        if not lows:
            continue
        typical = int(statistics.median(lows))
        cell = lens_cell(lens_word(p, typical), p, typical, d, basis, len(lows))
        if best is None or p / typical < best["price"] / best["typical"]:
            best = cell
    return best


def route_lenses(conn, rid, full, scan):
    """The four lenses for one route, each {business: cell or None, first: cell or None}."""
    day = history_day(full)
    out = {lens: {} for lens in LENSES}
    listed = [r for r in today_rows(conn, rid, full, scan) if r["stops"] <= 1]
    for cabin in CABINS:
        rows = [r for r in listed if r["cabin"] == cabin]
        best = cheapest(rows)
        if best is None:
            for lens in LENSES:
                out[lens][cabin] = None
            continue
        grid_rows = [r for r in rows if r["sweep_id"] == full["id"]]
        today_lows = {}
        for r in grid_rows:
            today_lows[r["depart_date"]] = min(r["price"], today_lows.get(r["depart_date"], r["price"]))
        past = past_by_day_and_date(conn, rid, cabin, day)
        first = lens_cell("first capture", best["price"], None, best["depart_date"], None)

        if today_lows and past:
            out["date"][cabin] = grouped_lens(today_lows, past, lambda d: d, week_of) or first
            month = grouped_lens(today_lows, past, lambda d: d[:7])
            out["month"][cabin] = dict(month, depart=month["depart"][:7], basis="month") if month else first
        else:
            out["date"][cabin] = out["month"][cabin] = first
        if out["date"][cabin] is not first and out["date"][cabin]["basis"] is None:
            out["date"][cabin]["basis"] = "date"

        kind = "nonstop" if best["stops"] == 0 else "one-stop"
        s = standing(best["price"], history(conn, rid, cabin, kind, best["carrier_codes"], day))
        out["any"][cabin] = (lens_cell(lens_word(best["price"], s["typical"]), best["price"], s["typical"],
                                       best["depart_date"], "any", s["days"]) if s else first)

        lows = [v for dates in past.values() for v in dates.values()]
        if lows:
            lowest = min(lows)
            word = "below" if best["price"] < lowest else lens_word(best["price"], lowest)
            out["lowest"][cabin] = lens_cell(word, best["price"], lowest, best["depart_date"], "lowest", len(past))
        else:
            out["lowest"][cabin] = first
        # Too few earlier days to say (session fares-verdict); the lowest-seen lens is exempt.
        for lens in ("date", "month", "any"):
            cell = out[lens][cabin]
            if cell is not first and cell["days"] < EARLY_DAYS:
                out[lens][cabin] = dict(cell, word="early")
    return out


def spine_body(conn, page_html, rendered_at):
    """The body POST /internal/fares/page takes (isleofdan/spine, lib/fares.js); None when there is
    no complete full sweep yet, since the Spine needs one's id."""
    full, scan = latest_captures(conn)
    if full is None:
        return None
    return {"rendered_at": rendered_at, "sweep": full["id"], "html": page_html,
            "summary": [dict(route_summary(conn, p["id"], full, scan), lenses=route_lenses(conn, p["id"], full, scan),
                             verdict=route_verdict(conn, p, full, scan))
                        for p in config.load_profiles()["routes"]]}


def one_line(text) -> str:
    return " ".join(str(text).split())[:500]


PUSH_TIMEOUT = 20  # seconds; one try only


def push(url, body, timeout=None) -> bool:
    """Send the body once; print one line either way. Never raises, never retries: the daily loop
    goes on whether or not the Spine answered."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"content-type": "application/json"})
    # Straight to the address: a proxy set in the environment has no route to Dan's private network.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=PUSH_TIMEOUT if timeout is None else timeout) as res:
            res.read()
        print(f"sent page to {url}: sweep {body['sweep']}, {len(body['summary'])} routes")
        return True
    except urllib.error.HTTPError as e:
        # The answer's body can itself fail to arrive whole; the status line is still the answer.
        try:
            text = e.read().decode("utf-8", "replace")
        except Exception as read_error:
            text = f"(its answer broke off: {type(read_error).__name__})"
        try:
            text = json.loads(text).get("error", text)
        except (ValueError, AttributeError):
            pass
        print(f"page not sent to {url}: the Spine answered HTTP {e.code}: {one_line(text)}")
    except urllib.error.URLError as e:
        print(f"page not sent to {url}: {one_line(e.reason)}")
    except (TimeoutError, OSError) as e:
        print(f"page not sent to {url}: {one_line(e) or type(e).__name__}")
    except Exception as e:  # anything else still must not stop the loop
        print(f"page not sent to {url}: {type(e).__name__}: {one_line(e)}")
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bin/page", description="Write the fares page, then send it to the Spine.")
    ap.add_argument("--spine", default=config.spine_url(), metavar="URL",
                    help=f"the Spine's fares route (default: FARES_SPINE_URL, else {config.SPINE_URL})")
    ap.add_argument("--no-push", action="store_true", help="write the page only; send nothing")
    args = ap.parse_args(argv)
    path = config.store_path()
    if not path.exists():
        print(f"no store at {path}; run bin/capture first", file=sys.stderr)
        return 1
    conn = store.connect(path)
    out = config.page_path()
    tmp = out.with_suffix(".html.tmp")
    rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    page_html = render(conn)
    tmp.write_text(page_html, encoding="utf-8")
    tmp.replace(out)
    print(f"wrote {out}")
    if args.no_push:
        return 0
    try:
        body = spine_body(conn, page_html, rendered_at)
    except Exception as e:  # the page is written; a summary that cannot be built must not stop the loop
        print(f"page not sent to {args.spine}: the summary could not be built: {type(e).__name__}: {one_line(e)}")
        return 0
    if body is None:
        print(f"page not sent to {args.spine}: no complete full sweep yet")
        return 0
    try:
        push(args.spine, body)
    except Exception as e:  # push prints its own line; this only guards against a line it could not print
        print(f"page not sent to {args.spine}: {type(e).__name__}: {one_line(e)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
