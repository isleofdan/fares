# Bounded coverage probe, local preparation — 15 Nov 2026

Base: current remote main `acfedc004b348efd02260a559822982d4ac80b95`.
The existing Idea Studio fares checkout was clean on `codex/houston-evidence`
at `be64ade62abe63df9bb1fc676598fdb589b9dc57`; it was not changed.
Work uses a separate local bare clone and worktree, branch `codex/bounded-coverage-probe`.
No repository AGENTS.md or .agents instructions were found.

PLAN.md's Barcelona far-horizon question remains unanswered. Its full weekly attempt
stopped at 263 searches before reaching those dates. Current main has no route/date
filter in capture.py, but does have a nine-query Houston-specific probe with a separate
report and shared capture lock. The new coverage command follows those isolation and
locking conventions without changing either existing command.

The default command only plans. Example scope: Barcelona business, departures days
280 through 293 inclusive, seven nights, explicit budget 14. One-day spacing is deliberate:
it gives fourteen bounded far-date samples instead of spending hundreds of earlier queries.
All returns stay within the existing 300-day manual cap. Actual dates, destination airport,
source, cabin, budget and evidence limits appear in the plan/report.

No source searches, live data reads/writes, publication, schedule changes, UI control,
push, PR, merge or deployment were performed. An authorized operator must review the
plan and separately authorize any live probe; results must be reviewed before proposing
any collection-horizon change. This local work does not establish a new Barcelona horizon.

Validation uses synthetic source answers and temporary output files. Independent agent
review was not requested because the task explicitly prohibits contacting agents.
The POSIX flock integration needs its real Linux concurrency check; Windows tests cover
the lock protocol with a fake fcntl module and fail-closed execution behavior.

Validation results on Windows, Python 3.13.9 from Idea Studio's existing embedded runtime:

- 25 targeted tests passed: 15 new probe tests, existing grid and parser tests, and
  the four Houston-probe tests. Network-client creation was replaced with a raising
  guard. Probe searches were synthetic stubs; no live requests were made.
- Full discovery at the initial 11-probe-test revision ran 92 tests and failed with
  103 error records (some tests error in both their body and teardown). Representative
  failures are existing `strftime("%-d ...")` unsupported by Windows and open SQLite
  handles preventing temporary-directory cleanup. Two representative tests were rerun
  on a separate pristine worktree at `acfedc0`, reproducing both failures (three error
  records). No full-suite success is claimed. Socket calls in the broad run were guarded
  to permit loopback only; the source client was disabled.
- `git diff --check` passed. Daily capture, source parser, store, publisher and schedules
  are unchanged. No independent agent review or real POSIX-lock concurrency test ran.

The full Linux suite and a synthetic, two-process shared-lock test remain integration
checks before live use. Local logs beside this worktree are `probe-tests.txt` and
`baseline-reproduction.txt`. The probe tests are the prevention for unknown/empty
misclassification and budget overrun; their success does not validate a live source.
