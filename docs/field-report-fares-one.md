# FIELD REPORT — fares-one — 2 Nov 2026

Session fares-one, on the machine agent-machine-dan, permission mode auto (read with `get_session`: `permission_mode: auto`). Brief: the START HERE note on card `fares`, event 2372. Pull request: https://github.com/isleofdan/fares/pull/1 (open, not merged; a machine session never merges). Nothing changes on Dan's screen yet: the page is a local file on the machine (`/data/home/dan/fares-data/fares.html`), not hosted and not in the Spine, and the daily run is not switched on.

## What stands

- **The OpenRig team did the work.** Rig `fares-one-mixed` (id `01M6EDXKQD76Y95XC15JN9GC99`, a spec copy of `first-project-mixed` with only `name:` changed, started fresh on `~/work/fares-one` with `rig-up-auto.sh`, builder in auto mode). Builder seat `dev-owner@fares-one-mixed`, checker seat `dev-check@fares-one-mixed`.
- Queue items: job `qitem-20261102152805-f8b839c99e48b1fd` (builder, done); check round 1 `qitem-20261102161521-d13d536d9130ff4b` with its verdict handed back as `qitem-20261102161802-79779ace`; check round 2 `qitem-20261102161959-a8ec033d` with its verdict handed back as `qitem-20261102162101-a22ce4e6`.
- The checker's recorded verdict, verbatim: "PASS for candidate 7c3d197. All three findings on ba24f78 are resolved. Fresh suite: 16 tests OK; independent interruption, throttling, unknown-response and stale-scan reproductions pass. Production store checked read-only; renderer matches saved HTML."
- Steps 7.1 to 7.6 are on branch `claude/fares-one`, one commit per step (`0957e72`, `3cb3daf`, `280f46d`, `43a3a13`, `a58d7ad`, `ba24f78`), then the check fixes (`7c3d197`), then my close-out note (`81680c6`) and this report.
- **Fare source: Google Flights**, without a key, read through the `fast-flights` 3.1.0 package (installed in `.venv/` in the clone, declared in `requirements.txt`) with the team's own parser. It was the only keyless candidate that returned prices from a script: Kayak and Momondo send a page that says "Searching" with no prices in it, Skyscanner sends a bot wall, and ITA Matrix sends an empty app shell. A search takes about 1.2 s. It does not give the fare code or booking class.
- **Store and page:** `/data/home/dan/fares-data/fares.sqlite` (append-only: database triggers refuse updates and deletes), `/data/home/dan/fares-data/fares.html`, and `capture.log` in the same folder. FACTS.md names no dedicated folder for job data. It says only that anything that must survive a deploy lives under `/data/home/dan`, so I chose `/data/home/dan/fares-data/`.
- **Daily run: written, not installed.** `bin/daily-loop` has the same shape as the skill-mirror window. Installing it is left for a separately authorized session (see below).
- I ran the tests again myself after the team finished: `Ran 16 tests in 0.885s — OK`.

## Verify (brief section 9)

1. **One full capture run.** Source Google Flights. Sweep 5, every 14 days, 2 Nov 2026 16:04–16:12 UTC: 168 searches, 0 refused, 8.4 minutes, 1,152 rows. Rows per route and cabin: Houston business 115, Houston first 161, Detroit business 174, Detroit first 104, Tel Aviv business 110, Tel Aviv first 82, Barcelona business 256, Barcelona first 150 [`capture.log`, line "sweep 5 done"]. The weekly grid (sweep 2) took 15.8 minutes for 336 searches and 2,293 rows, but 17 of the searches got a bot check. Per step 7.3 the grid was thinned to every 14 days, and sweeps 4 and 5 drew no refusals.
2. **Nonstop carriers and how many days a week the source showed them** (sweep 5 plus week scan 6, captured 2 Nov 2026 16:04–16:14 UTC). "Days seen" means the departure days on which the nonstop appeared in those searches.
   - Houston: ANA NH114 from Haneda, 7 days; United UA6 from Narita, 7 days; ZIPAIR Tokyo ZG16 from Narita, 2 days (Thursday, Saturday).
   - Detroit: Delta DL274 from Haneda, 7 days.
   - Tel Aviv: El Al LY92 from Narita, 2 days (Tuesday, Sunday). This matches the twice-weekly service in the route notes.
   - Barcelona: none found.
   - No nonstop on any route showed up in a first class search.
3. **Scheduling.** `bin/daily-loop` is in the repository. Mechanism found on the machine: the `skill-mirror` tmux window, started by `/usr/local/bin/start.sh` lines 200–207 (a loop that runs, sleeps 86,400 seconds and appends to a log; window 2 `skill-mirror` shows in `tmux list-windows -t main`). That matches FACTS.md, section "Skill mirror". The installation step left for a separately authorized session on `isleofdan/agent-machine`: make a permanent clone at `/data/home/dan/fares` with its virtualenv (`python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`). Then add this command to `/usr/local/bin/start.sh` (in the agent-machine repository) after the skill-mirror window, line 207, with its two comment lines as given in `PLAN.md`:
   ```sh
   "${AS_DAN[@]}" tmux new-window -d -t main -n fares "$HOME_DIR/fares/bin/daily-loop" \
     || echo "start.sh: starting the fares window failed; continuing." >&2
   ```
   The proposed run time is at boot and then every 24 hours after. Log: `/data/home/dan/fares-data/loop.log`.
4. **The page renders.** Screenshot `docs/fares-page.png` (taken with Playwright 1.56.1's headless Chromium) shows all four route sections: Houston, Detroit, Tel Aviv and Barcelona, nonstops first, then the cheapest one-stop, each line marked "first capture".

   ![The fares page, all four route sections](https://raw.githubusercontent.com/isleofdan/fares/claude/fares-one/docs/fares-page.png)

   Link: https://github.com/isleofdan/fares/blob/claude/fares-one/docs/fares-page.png
5. **The three files exist.** `README.md`, `PLAN.md` (current state, decisions, sources tried, sweeps, daily run, page, close-out note) and `LEARNING.md` (note 1: fare buckets, what Google Flights shows and does not show, and the first capture route by route).

## Divergences

- **`main` was created as an empty commit.** The brief said the first commit creates `main`, but the team's commits went onto the work branch. So I pushed one empty commit, "Start main (empty)" (`54c8e6a`), to `main`, joined it to the branch with a merge commit (`f341892`, no force push), and made `main` the repository's default branch. Pushing the branch first had made `claude/fares-one` the default. This way the pull request shows every file for review.
- **Three routes go blank about 8 months out.** For Houston, Detroit and Tel Aviv, the grid finds nothing for departures from late June 2027 onward (Tel Aviv from mid-June); Barcelona answers through August. The same thing happened in the sweep that met no bot checks, so it is not blocking. Most likely those fares are not on sale yet. The grid still covers 300 days, as the brief asks.
- **The daily loop has been syntax-checked, never run as a loop.** Each of its three commands has been run on its own.

## What the brief got wrong

- **"The persistent place FACTS.md names" does not exist.** Sections 6, 7.3 and 7.4 refer to it, but FACTS.md names no folder for job data. It says only that anything that must survive a deploy lives under `/data/home/dan`. I chose `/data/home/dan/fares-data/`.
- **"Your first commit creates `main`" did not fit the team procedure.** The team works on the brief's branch, so nothing created `main`, and with no base the pull request could not open. Fixed as described under "Divergences" (an empty `main` commit and a merge commit). A brief for an empty repository should have the supervisor create `main` before sending the job.
- **A 300-day grid asks for more than is on sale.** For three of the four routes Google Flights returns nothing beyond about 8 months out, so roughly the last 100 days of the grid come back empty every day. The grid was kept as the brief asks; a later brief can shorten it.

## Checks

1. Brief check, round 1: job `20261102-151551-bb9b9e`, FINDINGS. Fixed in the brief (card event 2367).
2. Brief check, round 2: job `20261102-151830-d33a31`, FINDINGS. Fixed in the brief (event 2369).
3. Brief check, round 3: job `20261102-152112-2762b2`, FINDINGS: one unsourced sentence in section 1. Fixed in event 2372 before launch. No fourth round, under the three-round rule (card event 2373).
4. Team check, round 1: `qitem-20261102161521-d13d536d9130ff4b` → verdict `qitem-20261102161802-79779ace`, FINDINGS on `ba24f78`, three findings. Changed in `7c3d197`:
   - a sweep is now marked complete only when every planned search ran without being throttled, and the page uses only complete sweeps;
   - a page Google sends without a results block now counts as a refused search, not as "no flights";
   - the page shows only a week scan from the same day.
5. Team check, round 2: `qitem-20261102161959-a8ec033d` → verdict `qitem-20261102162101-a22ce4e6`, PASS on `7c3d197`.
6. Result check, round 1: job `20261102-172721-c24407`, FINDINGS on report event 2378: (1) no "What the brief got wrong" section, so I added one; (2) the first paragraph did not say that nothing changes on Dan's screen, so I added that sentence.
7. Result check, round 2: job `20261102-172856-a45adc`, FINDINGS on report event 2380: (1) the report referred to PLAN.md instead of giving the exact start.sh command, so I quoted the command under Verify 3; (2) the screenshot was named but not attached, so I embedded it with a GitHub link under Verify 4.
8. Result check on this version: its verdict is named in the closing message.

## What the next session needs

- **Install the daily run.** Owner: a separately authorized Claude Code session on `isleofdan/agent-machine`. It makes the permanent clone at `/data/home/dan/fares` with its `.venv`, and adds the start.sh command quoted under Verify 3. A merge to that repository's `main` deploys and restarts the machine.
- **Next fares session.** Owner: Claude Code on the machine with the OpenRig team, once history has built up. It puts the page into the Spine (a Wall card and desk for each trip), then works on tactics, brokers and the reading feed.

## Asks

None.

## FACTS.md

I updated `/data/home/dan/FACTS.md`, section "OpenRig": the latest snapshot is now `01M6EMQ5RK813ZM7A3JPE9GT36` for rig `fares-one-mixed` (id `01M6EDXKQD76Y95XC15JN9GC99`), with restore line `rig up 'fares-one-mixed' --existing`, only to continue this job. The team is stopped (`rig down fares-one-mixed --snapshot`).

## Fly machine and OpenRig lessons

- **An empty repository has no base for a pull request.** What happened: Dan created the repository with no commits, the team committed onto the work branch, and when I pushed the branch it became the default with no `main` to target. Cost: three extra steps (an empty `main`, a merge to join unrelated histories, setting the default branch). Fix for next time: when a brief starts on an empty repository, the supervising session pushes an empty "Start main" commit before sending the job, and the builder branches from it.
- **Memory was tight before the team started.** What happened: about 1 GB was available and 1 GB of swap was in use. The cause was the ChatGPT/Codex desktop app (about 1 GB resident, up 10 hours) plus four other Claude Code sessions. Cost: none here, because the two-seat team ran without stalls. Fix: none needed for one team. With two teams at once, that desktop app is the first thing to close.
- **Bare `sleep` is blocked in the foreground.** What happened: a foreground `sleep 45` before reading a seat's screen was refused. Fix: read the screen directly, and put every wait in the background (as the memory rule already says).
- **`rig send` from outside a seat has no sender**, so the builder cannot reply to the supervisor. The closed queue row is the record. No cost.
- **There is no `sqlite3` command on the machine.** To read the store, use Python's `sqlite3` module or the logs.

## Closing message to Dan

The first piece of your fares system is built and checked: https://github.com/isleofdan/fares/pull/1. It's open and not merged; the thread that started this session merges it on your yes. Every two weeks' worth of departure dates over the next 300 days, it searches Google Flights for business and first class round trips from Tokyo to Houston, Detroit, Tel Aviv and Barcelona. One run takes about 9 minutes. It keeps every price in a history that only grows, and it writes one page showing the latest prices against that history. The first run found these nonstops: ANA, United and ZIPAIR to Houston; Delta from Haneda to Detroit, every day; El Al to Tel Aviv on Tuesdays and Sundays; none to Barcelona. Today's cheapest business fares: Houston $4,173 (ZIPAIR nonstop), Detroit $5,012 (one stop), Tel Aviv $4,511 (one stop via Bangkok; El Al nonstop $5,291), Barcelona $3,066 (one stop). The daily run is written but not switched on: a separate session on the machine's own repository has to add it, because that change restarts the machine. Needed from you: nothing to decide.

(The chat copy of this message adds one line naming the result check's verdict on this report, which cannot be inside the report it checks.)
