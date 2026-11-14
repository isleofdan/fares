# Houston evidence and publication

Deploy the companion Spine trip-desk change first. Then fast-forward the existing
machine clone to the merged fares change and run bin/page once. The publisher adds
at most 200 business-search observations (five distinct outbound products per date
pair) from the current complete full sweep and same-day week scan. All original
verdicts, rules, El Al ordering and unchecked tactic labels remain unchanged.

Run `bin/houston-probe` first to read existing Houston week scans. It writes
`$FARES_DATA/houston-evidence/week-scans.json`: Monday and cheapest other-day
observations within each complete scan, same cabin, airline, airports, stops,
segment cabins and currency. Missing Monday or comparison is unknown. Flight
numbers are retained to distinguish product changes. This does not establish a
causal weekday effect or measure stay length.

`bin/houston-probe --run` additionally makes exactly nine business searches:
28/29/31 December 2026, each for 5/7/10 nights. Two seconds between requests;
stop at the first refusal, challenge or error, with no retry. The dated probe file
is created exclusively: rerunning refuses to overwrite it or repeat searches.
It refuses past travel dates. An interrupted run remains incomplete.

`bin/capture` and `bin/houston-probe` share a nonblocking flock. Do not invoke the
Python module directly or overlap a capture started before this lock was deployed;
check the existing loop is idle before the first probe. No loop restart is needed.

Probe observations live outside the price store in `houston-evidence/`, never in
daily verdict history. Complete return itineraries, booking classes, total extras,
restrictions and mileage eligibility are not supplied by the capture. Recheck a
candidate and a same-date alternative with the actual airline before recommending
a purchase. Leave Monday/seven-night collection and all price thresholds unchanged
until comparable results justify a specific adjustment.

No broker outreach, reading feed, new destination or automatic recurring probe.
