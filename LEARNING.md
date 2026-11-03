# What the fares data teaches

## 1. Fare buckets, what Google Flights shows, and the first capture (2 Nov 2026)

**What a fare bucket is.** An airline sells the seats in one cabin at several prices at once. Each price comes with its own rules: how far ahead you must buy, whether you can change or refund, how many miles you earn. Each of those price levels has a one-letter code called a *booking class* or *fare bucket*. In business, for example, J is often the full flexible fare, with C, D, I and Z as cheaper, more restricted ones; each airline picks its own letters. Every bucket holds a limited number of seats. When the cheap bucket for a flight sells out, the next sale moves up to the next bucket, so the price jumps even though the seat is the same. That is the main reason a premium fare can move by thousands of dollars from one day to the next, and why a deal usually means "a cheap bucket is open on this flight right now". The full code printed on a ticket, the *fare basis* (for example "ZNN0R1JP"), adds the bucket's rules to that letter.

**What our source shows and does not show.** The capture reads Google Flights.
- It shows: the round-trip price in US dollars for one adult, taxes included; the airlines and flight numbers; the airports, including where you change planes; times, aircraft and total travel time; and the cabin of each flight.
- It does **not** show the booking class or fare basis, so we cannot yet see which bucket a price sits in. We only see the price move.
- A round-trip search lists outbound flights, each with the cheapest round trip that includes it. The return flight is not fixed, so a price is "from".
- Only the first page of results is returned: the 5 to 20 or so trips Google ranks highest. Rare routings and stopover trips may not appear.
- A "first class" search returns the best cabin on every flight. On these routes most results are first class only on the long flight and business on the short connection: in the 2 Nov sweep, 321 of 497 first-search results were mixed like that. The page marks them "mixed cabins".
- No nonstop on any of the four routes appeared in a first class search. Every nonstop found was business.
- Far-off dates: for Houston, Detroit and Tel Aviv, nothing came back for departures from late June 2027 onward (Tel Aviv from mid-June), about 8 months out, most likely because those fares are not on sale yet. Barcelona answered through August 2027.

**What the first capture found, route by route.** These are the nonstops the source showed, from sweep 5 (departures every two weeks, 16:04–16:12 UTC on 2 Nov 2026 = 01:04–01:12 on 3 Nov, Tokyo time) and the week scan that followed it (seven departures in a row, 30 Nov to 6 Dec 2026, run 16:12–16:14 UTC). "Days a week" means the weekdays on which a nonstop showed up in those searches. A nonstop that was sold out or not offered on a searched day would be missed, so these are days seen, not a timetable.

- **Houston.** Three nonstops. ANA NH114 from Haneda, seen all 7 days. United UA6 from Narita, seen all 7 days. ZIPAIR Tokyo ZG16 from Narita, seen Thursday and Saturday (2 a week). ZIPAIR is Japan Airlines' low-cost airline, and its "business" is a lie-flat seat with fewer extras; it was the cheapest nonstop business at $4,173. One-stop trips connected through 16 different airports.
- **Detroit.** One nonstop: Delta DL274 from Haneda (Dan's ideal), seen all 7 days. Its cheapest business was $5,383. The cheapest one-stop business was about $370 less. One-stop trips connected through 16 airports.
- **Tel Aviv.** El Al LY92 from Narita, seen on Tuesday and Sunday: 2 a week, matching the twice-weekly service in the route notes. Its cheapest business was $5,291. The cheapest one-stop business, $4,511 on Thai Airways with El Al via Bangkok, was $780 less. One-stop trips connected through 12 airports, most of them in Europe and the Gulf.
- **Barcelona.** No nonstop. Every trip connects, through 20 different airports; the cheapest business was $3,066 on Shenzhen Airlines via Shenzhen.

This is one day of prices, so none of them can be called a deal yet. The page compares each day with the route's own history once more days are captured.
