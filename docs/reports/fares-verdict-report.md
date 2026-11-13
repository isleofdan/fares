# FIELD REPORT — fares-verdict — 2026-11-13

Session fares-verdict ran on Dan's Fly machine `agent-machine-dan` in auto mode, as a Remote Control session started from the Claude Code project thread. It ran in two parts. The first supervising session (11 Nov 2026) did the research and had the OpenRig team build and check both jobs, then stopped at a permission prompt before pushing. This restarted session (13 Nov 2026) took over from that work. It found one more defect in the end to end, had the team fix it and check the fix, and then pushed, opened the pull requests and closed out. The brief is the card `fares`, event 2574, "START HERE — fares-verdict". **Nothing on Dan's screen has changed yet:** both pull requests are unmerged, the live Spine at https://spine-dan.fly.dev/fares runs the old code, and so does the machine's fares copy `~/fares`.

**Status: NOT MERGED.** Both pull requests are open, and this session merged neither:
- Spine: https://github.com/isleofdan/spine/pull/44 (merge first, then deploy)
- fares: https://github.com/isleofdan/fares/pull/6 (merge after the Spine is deployed)

Nothing is live yet. The thread that started this session merges them on Dan's typed yes there.

**Which pull request carries which step.** Step 2 (the Spine) is in spine#44. Steps 3 and 10 (fares code, PLAN.md, README and this report) are in fares#6. Step 1 (research) is the `good_price` data in `routes.json`, in fares#6. Steps 4 and 9 (checks, end to end) changed no file except the screenshots under `docs/reports/fares-verdict/` in fares#6. The result check runs once against each pull request, with this same report.

## What stands

- **The OpenRig team did both code jobs.** Rig `fares-verdict-mixed` ran on the job folder `~/work/fares-verdict`, which holds both clones, `spine` and `fares`. The builder was `dev-owner@fares-verdict-mixed` (Claude Code) and the checker `dev-check@fares-verdict-mixed` (Codex). Queue rows:
  - Job 1, the Spine: owner row `qitem-20261111145307-e4bd8e51be536c2a`.
  - Job 2, fares: owner row `qitem-20261111145825-3efeeed9fbaf492f`.
  - The new-low fix (this session): owner row `qitem-20261113124319-7e13ed2be8496016`.
  - The scope fix (this session, from the result check): owner row `qitem-20261113125324-c328ae3cd2e38bc9`.
  - The day-zero `early` fix (this session, from the second result check): owner row `qitem-20261113130338-a73def4c5b58dceb`.
  - The checker rounds are listed under "Checks".
  - **The team is stopped.** I stopped it once after the scope fix (snapshot `01M7AFQA1GCZB8V55YX3PXWNFW`), restored it with `rig up 'fares-verdict-mixed' --existing` for the day-zero fix, and stopped it again. The last `rig down fares-verdict-mixed --snapshot` on 13 Nov 2026 printed snapshot `01M7AGCPXWZ6ANTH598H2QEC2C` for rig id `01M75HGF33Y48PRFJK0YXWMMSV` and the restore line `rig up 'fares-verdict-mixed' --existing` (only to continue this job). I recorded those three in `/data/home/dan/FACTS.md` (section "OpenRig team is the default", the latest-snapshot sentence), ahead of fares-three's.
- **Spine, branch `claude/fares-verdict` (94d4240, c77c2e2, 8eacfd6, 78c60d8, 622c580, b482852; spine#44):**
  - **The route.** `lib/fares.js` accepts an optional `verdict` per route: `business` and `first`, each `{word, price, depart, line, gap, basis, scope}`, with words `deal`, `not a deal` and `no line yet`. It also accepts the lens word `early`. It refuses calendar-invalid dates and a `gap` that is not `price − line`.
  - **The route box.** Each box on /fares leads with the verdict: price and departure date, "a deal", "not a deal" or "no good-price line yet", the line and the dollar gap, and the scope in small text. The lens tabs sit under it. Each lens says what it compares with and over how many days, and `early` reads "too early to say". A body with no `verdict` draws as before.
  - **Card notes.** The hook that files fare notes on the card is `fileNoteworthy()` / `noteworthy()` in `lib/fares.js`. It now files only when a verdict turns to `deal` or on a new lowest ever by more than 3%. A new low the page before already reported is not filed again (622c580). Every note names the search scope: the cabin's own verdict scope, else that route's other cabin, else any verdict on the page; a page with no verdict at all (an older fares producer) files no notes (b482852, from the result check's finding). The "below typical" notes stop.
- **fares, branch `claude/fares-verdict` (08000dd, 1c4a017, 95cea28, dc7cffe, 1bc8b6c, 6ca436f and this report; fares#6):**
  - **`routes.json`.** `good_price` per route and cabin, filled from step 1, with `dan` null.
  - **`fares/page.py`.** `good_price()` picks the line: Dan's number, then the lowest tenth of 60 or more own capture days, then the researched amount, then none. `route_verdict()` gives the word. `scope_text()` reads the weekday and the nights from `GRID_EPOCH` and `NIGHTS` in `fares/capture.py`.
  - **The page and the body.** The verdict lines open each route section. The sources follow under "Where the good-price line comes from". `verdict` is in the body sent to the Spine. Lens `days` added, and the date, month and any lenses say `early` below 7 earlier days, zero included: on the first capture day they read `early` with `days` 0 (6ca436f, from the second result check). The lowest lens is exempt and keeps "first capture".
  - **`PLAN.md`.** "Open issues" holds the Monday-only and 7-night issue with its three steps. Also the decision record for the good-price line, and the close-out with the good-price table, the merge order and the machine update.
  - **`README.md`.** One sentence on the verdict.
- **Tests.**

  | Repository | Before (main) | After (branch) |
  |---|---|---|
  | fares, `.venv/bin/python -m unittest discover -s tests -t .` | 42 OK | 68 OK |
  | Spine, `node scripts/fares-verdict-test.mjs` | did not exist | 74 checks, 0 failed |
  | Spine, `node scripts/fares-page-test.mjs` | 52, 0 failed | 56, 0 failed |
  | Spine, `node scripts/fares-alerts-test.mjs` | 20, 0 failed | 14, 0 failed |
  | Spine, `node scripts/fares-lenses-test.mjs` | 24, 0 failed | 22, 0 failed |

  The Spine's documented test commands are listed in its README, section "Tests" (line 167 onward). It has no `npm test`. On the Spine side, the alerts and lens checks were rewritten for the new note rule and the new route-box ids. That is why those two counts fell, while the new verdict file adds 74. Spine fares checks in all: 96 before, 166 after.
- **The prerequisite was in place (environment check 3).**
  - fares#4 is MERGED (bc541b9): `GRID_EPOCH` is in `fares/capture.py` and `route_lenses` in `fares/page.py` on main.
  - spine#43 is MERGED (1c41a4d): `lenses` is accepted in `lib/fares.js` on main.
  - Both branches are based on those commits.
- **How the page reaches the Spine today.** The daily loop sends it. `~/fares-data/loop.log` ends with `sent page to http://spine-dan.internal:8080/internal/fares/page: sweep 31, 4 routes`, and the machine copy `~/fares` is at bc541b9. The fares README is correct, and so is FACTS.md ("Fares daily run": "Since fares #3 the page step also sends …"). What is out of date is under "What the brief got wrong".
- **Out of scope, as the brief says.** The card holds briefs for the neighbouring work: "START HERE — fares-tactics" (event 2579) and "START HERE — fares-feed" (event 2580, the reading feed). Keyed fare sources are recorded in fares PLAN.md, "Keyed sources, recorded for later (fares-two)". No brief for brokers was found on the card.
- **The store.** The live store was copied read-only, through the sqlite backup API, into `~/work/fares-verdict/e2e2/fares-data/` (sweep 31). The first session's copy is `~/work/fares-verdict/store-copy.sqlite`. The live store and `~/fares` were not written.
- **Permission mode.** Auto mode (the session's system notice). Every step could run in it.

## What the brief got wrong

- **"FACTS.md is reported to say the machine's daily loop sends nothing."** It does not. FACTS.md, "Fares daily run", says the page step sends the page to the Spine since fares #3, and `~/fares-data/loop.log` confirms it (`sent page to http://spine-dan.internal:8080/internal/fares/page: sweep 31, 4 routes`). FACTS.md needed no change for this.
- **The one document that really is out of date** is the header comment in `bin/daily-loop` in isleofdan/fares: "Prepared only: nothing registers or starts this". In fact `start.sh` runs it in tmux window `fares`. This session left it as it is, because the daily loop is out of scope (section 8). A later fares session can fix it.
- **The merge session.** The brief asks for a merge-session brief and a launch block. The relay that restarted this session overrides that: the thread that started it merges (see "Deliberate divergences").

## The good-price table (step 1)

All sources were read on 11 Nov 2026, with yen at 158.555 to the US dollar that day (open.er-api.com). A line is the median of the reported sale prices, rounded to the nearest $50, and needs at least two independent publishers.

| Route | Cabin | Line | Sources |
|---|---|---|---|
| Houston | business | **$3,900** | JAL sales Tokyo–Dallas (Texas fallback; no Houston business sale found): traicy.com 22–29 Nov 2024 $3,784, 16–30 Jun 2025 $3,898, 18–30 Nov 2025 $3,847, 21–31 May 2026 $4,364; may-money.com 11–21 Jun 2026 $4,364 |
| Houston | first | none | no reported first-class sale |
| Detroit | business | **$3,550** | Tokyo–Chicago (Midwest fallback): traicy.com JAL Jun 2025 $3,267, JAL Nov 2025 $3,217, JAL May 2026 $3,734, ANA 15–21 Oct 2026 $3,532; may-money.com JAL Jun 2026 $3,734 |
| Detroit | first | none | none found |
| Tel Aviv | business | none | Etihad Narita–Tel Aviv $3,455 (May 2026) and $4,544 (Aug 2026), both on traicy.com only, so not two independent publishers |
| Tel Aviv | first | none | none found |
| Barcelona | business | **$2,450** | premium-flights.com China Eastern from $1,930 (Sep 2025); traicy.com Etihad $2,473 (May 2026), $2,227 (Jun 2026), $3,599 (Aug 2026), $3,482 (Nov 2026) |
| Barcelona | first | none | none found |

Each source's link is in `routes.json` and in each route's list on the page. JAL and ANA sale fares include the fuel surcharge but not taxes. The Etihad fares include taxes.

## Verify

- **Tests pass in both repositories.** The counts are in the table above, and the checker's own reruns are under "Checks".
- **End to end on the machine (13 Nov 2026).**
  - **Setup.** The Spine branch ran locally on port 8798 with a temporary database (`~/work/fares-verdict/e2e3/spine-data`). `bin/page` ran on the store copy with `--spine http://[<this machine's private address>]:8798/internal/fares/page` and printed `sent page to …: sweep 31, 4 routes`.
  - **Result.** Signed in to the local /fares, the verdict lines equal the page file's, route for route:

  | Route | Cabin | Price, departure | Line | Basis | Word |
  |---|---|---|---|---|---|
  | Houston | business | $3,731, Mon 28 Dec 2026 | $3,900 ($169 under) | reported sales, 5 sources | a deal |
  | Houston | first | $10,543, Mon 11 Jan 2027 | none | none | no good-price line yet |
  | Detroit | business | $4,442, Mon 25 Jan 2027 | $3,550 ($892 over) | reported sales, 5 sources | not a deal |
  | Detroit | first | $11,481, Mon 14 Dec 2026 | none | none | no good-price line yet |
  | Tel Aviv | business | $4,201, Mon 14 Jun 2027 | none | none | no good-price line yet |
  | Tel Aviv | first | $6,746, Mon 16 Nov 2026 | none | none | no good-price line yet |
  | Barcelona | business | $3,598, Mon 30 Nov 2026 | $2,450 ($1,148 over) | reported sales, 5 sources | not a deal |
  | Barcelona | first | $5,748, Mon 14 Jun 2027 | none | none | no good-price line yet |

  Every verdict carries the scope "Monday departures, 7-night trips". The page file adds the basis in words, for example "(reported sales, 5 sources)". The Spine's box shows the line and the gap.
- **The deal note fires once.** A local test card `fares` was made in the temporary database. Nothing was filed on the real card.

  | Send | Body | Fare notes on the local card |
  |---|---|---|
  | 1 | Real lines (Barcelona business not a deal) | 1: Houston business deal, and Tel Aviv first $6,746 new lowest ever (old low $7,073) |
  | 1b | The same page again | still 1 |
  | 2 | Test copy of `routes.json` with the Barcelona business line raised to $4,000 | 2: "Barcelona business $3,598 out Mon 30 Nov 2026 is a deal (good-price line $4,000); Monday departures, 7-night trips" |
  | 3 | That identical deal body again | still 2 |

  So the second send of the sequence filed exactly one note, and the third filed none. This sequence ran on 622c580. b482852 changes only notes for routes whose own verdict is missing and pages with no verdict at all; every route in this body carries a verdict, and the checker's replay of b482852 (row 7 under "Checks") repeated the once-only result. Before the fix (622c580), the first run of this sequence (temporary database `e2e2`) re-filed the Tel Aviv new-low item on every send, including send 3. That was the defect the team fixed today.
- **Screenshots.**
  - **Setup.** The fares repository's screenshot setup is `tools/screenshot.mjs` (`npm run screenshot`). It shoots the fares page file only, so the local /fares, which needs a sign-in, was shot with the same Playwright install and a sign-in step.
  - **Files.** `docs/reports/fares-verdict/spine-fares-desktop.png` (1200 px), `spine-fares-phone.png` (412 px) and `spine-fares-phone-lowest-tab.png` (412 px, after clicking "Lowest seen").
  - **Width.** No horizontal scroll at either width.
  - **The checker's own screenshots** are in `~/.openrig/shared-docs/rigs/fares-verdict-mixed/state/dev/qa-8eacfd6/`, `page-1200.png` and `page-412.png`.

## UI review (the Spine's /fares and the fares page file)

1. **Speed of the frequent action** (is this a deal?): the answer is now the first line of each route box, with no tab or click.
2. **Recovery**: not applicable. The page is read-only. A wrong researched line is corrected by Dan's own number (`dan` in `routes.json`), which wins.
3. **Finding the tool**: the lens tabs stay in each box, under the verdict. The sources are linked at the end of each route section on the page.
4. **Orientation**: the "Rendered … Tokyo time" header is unchanged, and every verdict names its scope.
5. **Feedback**: clicking a tab changes the comparison text and the prices (checked on the phone screenshot after "Lowest seen").
6. **Interruption**: card notes now come only for a turn to a deal or a real new low, not for every "below typical".
7. **Thumb reach**: the tabs are full-height buttons at 412 px, with no horizontal scroll.
8. **Defaults**: the "Same date" tab stays the default. The verdict needs no choice.

**Not added**: a way for Dan to enter his own line on the page. It is a field in `routes.json` for now, as the brief asks. **From Dan's requests**: 1 (one plain verdict) and 6 (notes only for real deals).

States shot: populated at desktop and phone, and after the frequent action (tab click). An empty state is not applicable: with no page stored, /fares keeps its existing empty line, which is unchanged.

## Checks

| # | Round | Queue row | Candidate | Verdict | What was changed |
|---|---|---|---|---|---|
| 1 | Brief check | job 20261111-142632-245c09 (card event 2577) | brief event 2574 | PASS | — |
| 2 | Team check, Spine | `qitem-20261111150011-be565b33`, verdict on `qitem-20261111150303-9f80ed8c` | 94d4240 | FINDINGS (3 × P2 + 1) | Tabs moved under the verdict, calendar-invalid dates refused, gap must equal price − line, differing deal and new-low fares named separately (c77c2e2, 8eacfd6) |
| 3 | Team check, Spine | `qitem-20261111150550-7a30a6b7`, verdict on `qitem-20261111150654-50e40f6a` | 8eacfd6 | PASS (158 checks) | — |
| 4 | Team check, fares (+ Spine test-only 78c60d8) | `qitem-20261111151046-c7f9a3d9`, verdict on `qitem-20261111151310-d9a72275` | 1c4a017 | FINDINGS (1 × P2) | The first-day reading said nothing could be a deal, against a researched-line deal. Text and glossary fixed, with a regression test (95cea28, dc7cffe) |
| 5 | Team check, fares | `qitem-20261111151356-d89c0647`, verdict on `qitem-20261111151438-c18a2b80` | dc7cffe | PASS | — |
| 6 | Team check, Spine (this session) | `qitem-20261113124526-0c4fde614fc1385d`, verdict on `qitem-20261113124643-4175d4b0` | 622c580 | PASS (163 checks, plus a replay through the private listener) | — (the fix for this session's end-to-end finding) |
| 7 | Team check, Spine (this session) | `qitem-20261113125510-3921c3d5df131f63`, verdict on `qitem-20261113125617-cb30a896` | b482852 | PASS (166 checks, plus five replay scenarios through the private listener) | — (the fix for result check 8's finding 1) |
| 8 | Result check, spine#44, on report event 2601 | job 20261113-125047-5a3f14 | 622c580 + report 2601 | FINDINGS (4) | 1: a new-low note dropped the scope when the route had no verdict; fixed in b482852 (row 7). 2: FACTS.md lacked this team's snapshot; team stopped and FACTS.md updated. 3: the first paragraph did not say nothing changed on Dan's screen; added. 4: the report claimed result checks passed before they ran; the claim is removed and this table lists them |
| 9 | Result check, fares#6, on report event 2601 | job 20261113-125047-7c6112 | 1bc8b6c + report 2601 | FINDINGS (4) | 1: no "What the brief got wrong" section; added. 2, 3, 4: as row 8's 3, 2 and 4 |
| 10 | Result check, spine#44, on report event 2604 | job 20261113-130026-df4a5c | b482852 + report 2604 | FINDINGS (2) | 1: the closing message said the team's checker passed every round, but rounds 2 and 4 found defects; reworded. 2: no completed passing result check was recorded; rows 10 and 11 are now recorded, and the final verdict is named under the table |
| 11 | Result check, fares#6, on report event 2604 | job 20261113-130041-1540cb | 59abf25 + report 2604 | FINDINGS (1) | 1: with zero earlier days the date, month and any lenses read "first capture", not `early` as the brief asks; fixed in 6ca436f (row 12) |
| 12 | Team check, fares (+ Spine drawing) | `qitem-20261113130635-9bea0c467142fa60`, verdict on `qitem-20261113130801-7c7143eb` | 6ca436f (fares), b482852 (Spine, unchanged) | PASS (68 tests; a day-zero body through 79 verdict and 27 lens checks; Playwright shows "too early to say" on the Spine) | — (the fix for row 11) |

**The result-check tools.** `check_result` takes the card, one pull request URL, and the report and brief (as text or as card event ids). It answers at once with a job id, and the checker (Codex on this machine) files its verdict on the card as a `checker:codex` event. `result_check_status` takes that job id and returns state (queued, running, done or failed), verdict (PASS or FINDINGS) and the numbered findings. Only a done PASS counts. **The final verdict.** Dan's rule keeps only the verdict on the report's own final version outside the report. That is the re-check of this version, one per pull request. Both are filed on the card `fares` as `checker:codex` events right after this report's note, and the closing message to Dan names them. The checker's evidence is in `~/.openrig/shared-docs/rigs/fares-verdict-mixed/state/dev/qa-<sha>/review.txt`. Seat prompts that this session answered for the team: 0.

## Deliberate divergences from the brief

- **No merge-session brief, and no launch block.** The relay that restarted this session (Dan, via the thread) says: "Leave out any merge-session launch block for Dan; the thread that started you merges after Dan's typed yes there." So no "START HERE — fares-verdict-merge" note was filed or brief-checked. The card's `next` names the thread as the one that merges.
- **`next` wording.** For the same reason, `next` reads: "The thread that started fares-verdict merges the two pull requests on Dan's typed yes: the Spine first, then its deploy, then fares; then a machine session updates ~/fares as fares PLAN.md's fares-verdict close-out says."
- **The end-to-end sweep.** The end to end used a fresh copy of the store (sweep 31, 13 Nov), not the first session's copy (sweep 26), so the values are today's.

## What the merge must do, in order

1. Merge spine#44 and run the Spine's deploy workflow, which must succeed. The deployed Spine accepts bodies with and without `verdict`.
2. Merge fares#6. If it went first, the live Spine would refuse the new `verdict` field and the `early` word with a 400 naming them. The loop logs that line and goes on, but /fares stays stale.
3. Update the machine's running copy, as fares PLAN.md's fares-verdict close-out says. `git -C /data/home/dan/fares pull --ff-only origin main` brings no new packages. Then run `/data/home/dan/fares/bin/page` once. It should print `sent page to http://spine-dan.internal:8080/internal/fares/page: sweep N, 4 routes`. Then check https://spine-dan.fly.dev/fares. The loop starts `bin/capture` and `bin/page` as new processes each run, so no restart is needed, and a reboot pulls by itself (`start.sh`). The thread decides who runs this: it is one command on the machine, so a machine session does it, not Dan.

## Asks

None. The merge is the thread's, on Dan's typed yes there.

## Fly machine and OpenRig lessons

- **A restart found finished, unpushed work.** The first supervising session stopped at a permission prompt after the team had passed both jobs but before any fares push. The Spine branch was pushed up to 8eacfd6, which left 78c60d8 local. Checking the job folder, the queue history and the checker's `qa-<sha>` folders first gave a full picture in a few minutes and avoided redoing about 20 minutes of team work.
- **A local e2e Spine outlived its session.** The first session's local Spine (pid 18742, port 8797) was still running two days later. A session that starts a local server stops it at close-out. This session stopped both of its own servers.
- **The hook needs a card.** In a temporary database, the hook logs "No card with id fares" and files nothing. The deal-once proof needs a local card made first: `require('./lib/db').open()` and then `wall.fileThread`.
- **Re-sending the same sweep is the real test of "fires once".** The suites tested consecutive pages. Only sending one sweep twice exposed the repeated new-low note.
- **Safety check on `rm -f $R/*.png`.** It was refused because `$R` could expand to root. A literal path, or `"${R:?}"`, passes.
- **`pkill -f <pattern>` killed my own shell (exit 144),** because the pattern was in the command line itself. Kill by the pid that `ss -ltnp` shows.

- **A restored team keeps its context.** `rig up 'fares-verdict-mixed' --existing` brought both seats back in the same clones within a minute, with their conversations intact. The builder took the next job at once, so restoring was cheaper than starting fresh.
- **A wait matched an old file.** My first wait for the checker's verdict on b482852 counted folders and read the newest `review.txt`, so it fired on the old 622c580 PASS. Waiting on the exact candidate's own file (`qa-b482852/review.txt`) fixed it.
- **A placeholder note went to the card (event 2600).** I filed the card fields with a placeholder note instead of the report, and corrected it with the next note (event 2601). A card write's note is the report text itself, never a pointer to be filled in later.

## Closing message to Dan

fares-verdict is done: each route now has a good-price line and one plain verdict, and the card gets a note only for a real deal or a new low.
Today Houston business at $3,731 is a deal (its line is $3,900); Detroit and Barcelona business are not; the other five have no line yet.
Tests: fares 42 → 68, Spine fares checks 96 → 166. The team's checker found defects in two early rounds and passed every corrected candidate. The result checks raised five more points, all now fixed, and their verdict on this final report is on the card fares.
NOT MERGED: two pull requests wait for your yes, the Spine first: https://github.com/isleofdan/spine/pull/44, then https://github.com/isleofdan/fares/pull/6.
