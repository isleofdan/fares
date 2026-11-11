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

## 2. Ten days of history: what moved, what did not, and what "below typical" means so far (11 Nov 2026)

**What this note rests on.** Fourteen *complete full sweeps* (a sweep is one pass over every route and cabin; "complete" means every planned search ran and the source refused none it was not allowed to, PLAN.md "Complete or not"; "full" means the main grid, not the 7-day week scan): sweeps 2, 4 and 5 on 2 Nov, 7 and 9 on 3 Nov, 10, 12, 14, 16 and 18 on 4–8 Nov, 20 and 22 on 9 Nov, 24 on 10 Nov and 26 on 11 Nov 2026. That is ten *capture days* (UTC dates, the way the page groups them). Sweep 1 was stopped by hand and is left out. All numbers are round-trip prices in US dollars for one adult, read from a copy of the store taken at 14:30 UTC on 11 Nov. Where two sweeps ran on one day, the day's figure is the cheaper of them, as the page does.

**Which grid each sweep used.** Every one of these fourteen sweeps used the *rolling* grid: departures started the day after the capture and stepped every 14 days (sweep 2: every 7 days), so each capture day searched a different set of dates, all on one weekday (2 Nov: Tuesdays; 3 Nov: Wednesdays; then Thursday, Friday, Saturday, Sunday, Monday; 9 Nov: Tuesdays; 10 Nov: Wednesdays; 11 Nov: Thursdays). The *fixed* grid (departures on Mondays counted from 2 Nov 2026, the same dates every day; PLAN.md "fares-lenses") reached the machine at 14:27 UTC on 11 Nov, after sweep 26; its first daily sweep is the run at about 09:38 UTC on 12 Nov. The one fixed-grid sweep so far is the horizon probe, sweep 28 (14:31–14:44 UTC on 11 Nov, every 7 days to a 300-day horizon); the source throttled it, so it is incomplete and not used here (PLAN.md, fares-two close-out, "The wider probe, tried once"). So every table here compares *different departure dates* from one capture day to the next, except the one same-date comparison further down.

### How the day's cheapest moved

Each cell is the day's cheapest trip of that kind over all departure dates in the full sweeps: price, airline, and the departure date it was found on. "Nonstop" means no change of plane; "one-stop" means one change. No search on any route ever returned a first class nonstop, so first class has only a one-stop column.

**Houston**

| Capture day (sweeps) | Business nonstop | Business one-stop | First one-stop |
|---|---|---|---|
| 2 Nov (2, 4, 5) | $3,761 ZIPAIR, 22 Dec | $4,707 American via DFW | $9,352 ANA/United via HNL |
| 3 Nov (7, 9) | $5,699 United, 21 Apr | $4,790 EVA via TPE | $9,613 ANA/United via HNL |
| 4 Nov (10) | $3,716 ZIPAIR, 14 Jan | $4,783 EVA | $9,167 ANA/United |
| 5 Nov (12) | $5,791 ANA, 23 Apr | $4,782 EVA | $10,261 ANA/United |
| 6 Nov (14) | $3,715 ZIPAIR, 16 Jan | $4,790 EVA | $11,860 ANA/United |
| 7 Nov (16) | $5,643 United, 17 Jan | $4,772 EVA | $12,445 ANA/United via ORD |
| 8 Nov (18) | $3,711 ZIPAIR, 18 Jan | $4,686 American via LAX | $9,178 ANA/United |
| 9 Nov (20, 22) | $3,760 ZIPAIR, 22 Dec | $4,699 American via LAX | $9,604 ANA/United |
| 10 Nov (24) | $5,659 United, 12 May | $4,638 WestJet via YYC | $10,828 ANA/United |
| 11 Nov (26) | $3,912 ZIPAIR, 24 Dec | $4,675 American via LAX | $10,781 ANA/United |
| Lowest–highest day (spread) | $3,711–5,791 ($2,080) | $4,638–4,790 ($152) | $9,167–12,445 ($3,278) |

The nonstop's $2,080 swing is not a price moving. ZIPAIR's nonstop showed up only on Monday, Tuesday, Thursday and Saturday departures, and the rolling grid searched one weekday a day: on the days it searched Wednesdays, Fridays or Sundays, ZIPAIR was absent and the cheapest nonstop was United or ANA at $5,643–5,791. On every day ZIPAIR appeared, its cheapest business was $3,711–3,912. The one-stop business barely moved at all ($152). The 10 Nov WestJet trip was business on the long flight and economy on the connection.

**Detroit**

| Capture day (sweeps) | Business nonstop (Delta DL274) | Business one-stop | First one-stop |
|---|---|---|---|
| 2 Nov (2, 4, 5) | $4,852, 22 Dec | $4,558 United via ORD | $10,755 ANA/United via ORD |
| 3 Nov (7, 9) | $5,379, 10 Feb | $4,616 Alaska via SEA | $10,747 |
| 4 Nov (10) | $5,371, 11 Feb | $5,007 Air Canada via YYZ | $10,819 |
| 5 Nov (12) | $5,607, 12 Feb | $5,104 Alaska | $11,607 |
| 6 Nov (14) | $5,616, 13 Feb | $5,313 WestJet via YYC | $11,627 |
| 7 Nov (16) | $5,596, 14 Feb | $5,322 WestJet | $11,584 |
| 8 Nov (18) | $4,853, 21 Dec | $4,436 American via ORD | $11,584 |
| 9 Nov (20, 22) | $4,861, 22 Dec | $4,865 American via DFW | $10,825 |
| 10 Nov (24) | $4,858, 23 Dec | $4,862 American via DFW | $10,817 |
| 11 Nov (26) | $4,837, 24 Dec | $4,841 American via DFW | $10,770 |
| Lowest–highest day (spread) | $4,837–5,616 ($779) | $4,436–5,322 ($886) | $10,747–11,627 ($880) |

Delta's nonstop was cheapest on departures between 21 and 24 December ($4,837–4,861) and cost $5,371–5,616 on the February dates that were cheapest on 3–7 Nov. Again the swing follows which dates were searched: the grids of 2 Nov and 8–11 Nov each held a departure between 21 and 24 Dec; those of 3–7 Nov did not (their nearest were 16–20 Dec and 30 Dec–3 Jan). The two WestJet one-stops were business on the long flight and premium economy on the short one.

**Tel Aviv**

| Capture day (sweeps) | Business nonstop (El Al LY92) | Business one-stop | First one-stop |
|---|---|---|---|
| 2 Nov (2, 4, 5) | $5,291, 25 May | $4,417 KLM via AMS | $7,173 Etihad via AUH |
| 3 Nov (7, 9) | $5,627, 19 May | $4,498 LOT via WAW | $7,167 Etihad |
| 4 Nov (10) | $5,816, 25 Mar | $4,300 Air France via CDG | $7,156 Etihad |
| 5 Nov (12) | none found | $4,514 LOT | $7,073 Etihad |
| 6 Nov (14) | none found | $4,508 Thai/El Al via BKK | $7,420 Etihad |
| 7 Nov (16) | $5,361, 6 Jun | $4,749 LOT | $7,555 Etihad |
| 8 Nov (18) | $5,606, 1 Mar | $4,370 LOT | $7,559 Etihad |
| 9 Nov (20, 22) | $5,282, 8 Jun | $3,879 KLM | $7,160 Etihad |
| 10 Nov (24) | $5,278, 9 Jun | $4,247 LOT | $7,155 Etihad |
| 11 Nov (26) | $5,349, 13 May | $3,834 LOT | $7,124 Etihad |
| Lowest–highest day (spread) | $5,278–5,816 ($538, 8 days) | $3,834–4,749 ($915) | $7,073–7,559 ($486) |

On 5 and 6 Nov, which searched only Friday and Saturday departures, no El Al nonstop appeared. Business one-stop is the route that moved most from day to day, and its two lowest days are the two newest: $3,879 (KLM, 9 Nov) and $3,834 (LOT, 11 Nov), both on June departures. First class one-stop was Etihad every day, on 8 of the 10 days on the departure one day after the capture.

**Barcelona** (no nonstop exists)

| Capture day (sweeps) | Business one-stop | First one-stop |
|---|---|---|
| 2 Nov (2, 4, 5) | $3,646 Etihad via AUH | $5,826 Etihad via AUH |
| 3 Nov (7, 9) | $3,643 Etihad | $5,822 Etihad |
| 4 Nov (10) | $3,459 KLM via AMS | $5,813 Etihad |
| 5 Nov (12) | $3,637 Etihad | $5,812 Etihad |
| 6 Nov (14) | $3,643 Etihad | $5,822 Etihad |
| 7 Nov (16) | $3,619 Cathay via HKG | $5,800 Etihad |
| 8 Nov (18) | $3,021 Etihad | $5,800 Etihad |
| 9 Nov (20, 22) | $3,640 Etihad | $5,816 Etihad |
| 10 Nov (24) | $3,058 Shenzhen via SZX | $5,809 British Airways via LHR |
| 11 Nov (26) | $3,622 Etihad | $5,787 Etihad |
| Lowest–highest day (spread) | $3,021–3,646 ($625) | $5,787–5,826 ($39) |

Barcelona is the steadiest route: on eight of ten days the cheapest business sat between $3,619 and $3,646, and first between $5,787 and $5,826 on every day. The two low days, $3,021 (Etihad, 7 Dec departure, 8 Nov) and $3,058 (Shenzhen Airlines, 25 Nov departure, 10 Nov), were single dates, not a level that held.

### The same departure date on two capture days

Only one pair of full sweeps searched the same dates: sweep 2 on 2 Nov (weekly Tuesdays from 3 Nov) and sweeps 20 and 22 on 9 Nov (every other Tuesday from 10 Nov) share 15 to 19 Tuesday departures per route and cabin, from 10 Nov 2026 to 3 Aug 2027. Comparing each date's cheapest (nonstop or one-stop) a week apart:

| Route, cabin | Dates compared | Within 1 % | Up more than 1 % | Down more than 1 % | Largest moves |
|---|---|---|---|---|---|
| Houston business | 17 | 14 | 1 | 2 | 10 Nov $7,051 → $5,228 (−26 %); 30 Mar $4,794 → $5,828 (+22 %) |
| Houston first | 17 | 13 | 1 | 3 | 2 Feb $11,708 → $9,604 (−18 %) |
| Detroit business | 17 | 9 | 6 | 2 | 24 Nov $5,309 → $6,007 (+13 %) |
| Detroit first | 17 | 16 | 1 | 0 | 10 Nov $20,606 → $21,060 (+2.2 %) |
| Tel Aviv business | 16 | 3 | 6 | 7 | 16 Feb $4,544 → $5,069 (+12 %); 30 Mar $5,677 → $4,905 (−14 %) |
| Tel Aviv first | 15 | 11 | 0 | 4 | 16 Mar $12,650 → $8,832 (−30 %) |
| Barcelona business | 19 | 15 | 3 | 1 | 8 Jun $3,835 → $3,640 (−5 %); 3 Aug $3,711 → $3,822 (+3 %) |
| Barcelona first | 17 | 12 | 1 | 4 | 22 Dec $6,140 → $11,115 (+81 %) |

So in one week most dates held their price to within 1 %: the cheap bucket (section 1) on most flights stayed open. Tel Aviv business is the exception, with 13 of 16 dates moving more than 1 % either way. The big single moves are the bucket jumps section 1 describes: Barcelona first on 22 Dec lost a $6,140 fare and fell back to the $11,115 level the other winter dates sit at. This is the comparison the fixed grid will make every day from 12 Nov; this one pair is all the rolling grid allowed.

### Weekdays and months

**Weekdays: not enough to say.** On the rolling grid each capture day searched a single departure weekday, so a weekday's prices all come from one or two capture days (Tuesdays from 2 and 9 Nov, Mondays only from 8 Nov). A cheaper weekday cannot be told apart from a cheaper capture day. The one weekday fact that holds is which nonstops fly when (Houston's ZIPAIR above). The fixed grid will not answer this either, because it departs only on Mondays; the week scan (seven days in a row, four weeks out) is the only source of weekday prices, and only for business.

**Months: a few clear patterns, from each departure date's cheapest (nonstop or one-stop) on each capture day.**
- November departures (within four weeks of the capture) are dearer on the US routes: Detroit first in November had a median of $20,324 against $10,835–10,844 for every month from December to June; Houston first $14,222 against $11,688–11,708; Detroit business $7,115 against $5,124–5,600.
- Barcelona first has two levels: about $5,800 on Etihad for November 2026 and June 2027 (medians $5,816 and $5,822), and about $10,600 for December to March (medians $10,615–10,628), with a few cheaper dates in between ($5,800 in December, $5,817 in January). April and May ($7,635–7,652) and July and August ($6,745–6,749) sit between.
- Tel Aviv first is cheapest for near departures: the lowest within 60 days of the capture was $7,073, against $7,541 further out, and the month medians from December to June were $7,893–8,872.
- Houston, Detroit and Barcelona business and Detroit first show no cheap season: from December to June their month medians stay within about 13 % of each other (Houston business $4,783–5,374, Detroit business $5,124–5,600, Barcelona business $3,646–4,165, Detroit first $10,835–10,844).

### Which airlines were cheapest

The airline of the day's cheapest trip (nonstop or one-stop), out of ten capture days:
- Houston business: ZIPAIR 6, EVA 3, WestJet 1. Houston first: ANA/United via Honolulu or Chicago 10.
- Detroit business: Delta nonstop 3 (9–11 Nov), Alaska 2, WestJet 2, United, Air Canada and American 1 each. Detroit first: ANA/United via Chicago 10.
- Tel Aviv business: LOT 6, KLM 2, Air France 1, Thai/El Al 1. Tel Aviv first: Etihad 10.
- Barcelona business: Etihad 7, KLM, Cathay Pacific and Shenzhen Airlines 1 each. Barcelona first: Etihad 9, British Airways 1.

Every day's cheapest first class trip from 3 Nov on was "mixed cabins" (the 2 Nov rows predate the cabin column): first class on only one of its two flights, the other business, except Houston on 7 Nov, first and economy.

### How often the cheapest was "below typical"

The rule is `standing()` in `fares/page.py` on the main branch at bc541b9, which the page's price lines and the Spine strip's `against_typical` both use: the route's cheapest nonstop or one-stop today (from the day's newest complete full sweep and that day's week scan), against the *typical*, the median of each earlier capture day's cheapest of the same kind (the same nonstop airline, or any one-stop). A price under the typical by any amount is "below", otherwise "above". I replayed it for each capture day as the page saw it then (day 1 is always "first capture", so nine days count):

| Route, cabin | Below | Above | Below by more than 3 % | Sizes of the "below" days |
|---|---|---|---|---|
| Houston business | 4 | 5 | 3 | $248–252 (6 %) three times, $1 once |
| Houston first | 3 | 6 | 2 | $759, $315, $9 |
| Detroit business | 4 | 5 | 4 | $517–619 (10–12 %) |
| Detroit first | 3 | 6 | 2 | $759, $387, $55 |
| Tel Aviv business | 5 | 4 | 4 | $619, $583, $210, $157; $133 (3.0 %) |
| Tel Aviv first | 6 | 3 | 0 | $6–94 (under 1.5 %) |
| Barcelona business | 6 | 3 | 2 | $295, $288; $3–43 four times |
| Barcelona first | 7 | 2 | 0 | $4–26 (under 0.5 %) |

What this shows:
- More than half the "below" days (21 of 38) are within 3 % of the typical, and on Barcelona first and Tel Aviv first every one is. A $4 difference on a $5,800 fare flips the word. The new comparison lenses (`lens_word`, same file) call anything within 3 % "near"; the old strip word does not.
- The typical mixes trips that are not alike: Houston business compares a ZIPAIR nonstop only with earlier ZIPAIR days, which is fair, but "one-stop" compares any one-stop on any date with any other. Detroit business turned "below" on 9–11 Nov only because the cheapest became Delta's nonstop on 22–24 Dec, compared with Delta's February prices on earlier days.
- The history it reads includes the week scans as well as the full sweeps (`history()` counts every complete sweep), so the typical is not only from the main grid.
- The new *date* lens (`route_lenses`, same file) said "below" on 56 of 72 route-cabin-days and "near" on 16 when replayed over the same days. It picks the one date that stands best against its own past, so it leans to "below" by design, and until the fixed grid builds same-date history it compares with the same week, not the same date (its basis was "week" on all but 6 of them).

### What the history cannot show yet

- **How a fare moves as departure nears.** Needs the same dates on many capture days: the fixed grid gives that from 12 Nov. About 4 weeks of daily fixed sweeps (28 capture days) would show whether a date's price drifts or jumps in the last 2–3 months before it.
- **Whether a "below" day is a deal.** Nine earlier days give a median that one odd day can move. About 30 capture days per kind (a month) before the typical is steady; more for the nonstops that appear only on some weekdays.
- **Weekday effects.** Not from the full grid at all (one weekday a day before, Mondays only now). The week scan has seven days in a row in business; about 4 weeks of week scans (28 rows per weekday per route) would say whether a weekday is cheaper.
- **Season.** One capture of each month so far, and nothing past June for three routes (section 1). A month's level against the same month a year earlier needs a year.
- **Which bucket a price is.** The source gives no fare code (section 1, PLAN.md "Keyed sources").

No buying advice follows from ten days: the moves above are mostly which dates were searched, not prices changing.
