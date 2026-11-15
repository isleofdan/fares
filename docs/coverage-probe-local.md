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

Validation uses synthetic source answers and temporary output files. The parent later
commissioned an independent read-only review and supplied its findings.
The POSIX flock integration needs its real Linux concurrency check; Windows tests cover
the lock protocol with a fake fcntl module and fail-closed execution behavior.

Validation results on Windows, Python 3.13.9 from Idea Studio's existing embedded runtime:

- 29 targeted tests passed after the publication fix: 19 new probe tests, existing grid and parser tests, and
  the four Houston-probe tests. Network-client creation was replaced with a raising
  guard. Probe searches were synthetic stubs; no live requests were made.
- Independent full discovery at commit `ab25f715` ran 96 tests, versus 81 on the base,
  with the same 103 error IDs on both (some tests error in both body and teardown),
  plus the same WinError 10038 shutdown error. Representative
  failures are existing `strftime("%-d ...")` unsupported by Windows and open SQLite
  handles preventing temporary-directory cleanup. Two representative tests were rerun
  on a separate pristine worktree at `acfedc0`, reproducing both failures (three error
  records). No full-suite success is claimed. Socket calls in the broad run were guarded
  to permit loopback only; the source client was disabled.
- `git diff --check` passed. Daily capture, source parser, store, publisher and schedules
  are unchanged. Independent review found the initial-publication defect below.
  No real POSIX-lock concurrency test ran locally.

Independent review reproduced interruption during the initial direct JSON write, leaving
truncated JSON at the permanently reserved destination. Initial publication now writes,
flushes and fsyncs a temporary file before atomically creating an exclusive hard link at
the destination. Existing or concurrent reports are never overwritten. Interruptions
before publication leave no final report; interruptions after publication leave a complete
zero-attempt report. Temporary files are cleaned on ordinary exceptions and interrupts.
Hard kills may leave an unused temporary file, but cannot publish partially written JSON.
There is no nonexclusive fallback for filesystems that cannot create hard links.

Four regression tests cover partial initial-write interruption and successful retry,
competing initial publication, interruption immediately after linking, and unsupported
hard links. The first sandboxed Windows test run could not create hard links (11 errors);
an approved rerun outside that sandbox passed all 29 targeted tests with source-client
creation disabled. Full discovery was not rerun after these four tests were added; Linux
full-suite and real lock-concurrency validation remain outstanding.

The full Linux suite and a synthetic, two-process shared-lock test remain integration
checks before live use. Local logs beside this worktree are `probe-tests-fix.txt` and
`baseline-reproduction.txt`. The probe tests are the prevention for unknown/empty
misclassification and budget overrun; their success does not validate a live source.
