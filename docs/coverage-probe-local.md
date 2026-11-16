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
Windows tests cover the lock protocol with a fake fcntl module and fail-closed execution
behavior. Independent Linux validation of the exact Library version 1 bundle is recorded below.

Validation results on Windows, Python 3.13.9 from Idea Studio's existing embedded runtime:

- 29 targeted tests passed after the publication fix: 19 new probe tests, existing grid and parser tests, and
  the four Houston-probe tests. Network-client creation was replaced with a raising
  guard. Probe searches were synthetic stubs; no live requests were made.
- Independent final Windows review at commit `969879451651b4bb82c82a689014dcba55d489a4`
  confirmed the publication defect fixed with no new blocking issue. Its approved
  unsandboxed run passed 29 targeted tests; six additional synthetic edge checks passed.
- Independent revised full discovery ran 100 tests, versus 81 on the base,
  with the same 103 error IDs on both (some tests error in both body and teardown),
  zero assertion failures, plus the same WinError 10038 socket shutdown error. Representative
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
creation disabled. Independent revised full discovery is recorded above.

Independent Linux verification, reported by the parent, checked exact commit
`969879451651b4bb82c82a689014dcba55d489a4`, the expected version 1 ZIP hash and
all 52 manifest hashes. Results: 19/19 probe tests, 9/9 independent lock/checkpoint/
budget/publication checks, and 99/100 full-suite tests. The sole full-suite mismatch
is an unchanged baseline CRLF snapshot mismatch. Fault injection confirmed initial
publication cleanup and successful retry. A two-process same-report race produced one
winner; the loser made zero searches and did not overwrite the report. Verification
used Python loopback-only network guards; kernel network namespaces were unavailable.
These results validate synthetic behavior, not live-source availability or a new horizon.

Local logs beside this worktree are `probe-tests-fix.txt` and
`baseline-reproduction.txt`. The probe tests are the prevention for unknown/empty
misclassification and budget overrun; their success does not validate a live source.

Independent review logs remain preserved in
`C:\Users\Owner\Documents\Codex\2026-11-15\task-6`: `revised-targeted.log`
and its `.json` summary, `revised-edge-checks.log`, `revised-full.log` and its `.json`
summary, `fares-baseline.log` and its `.json` summary, plus the initial
`revised-targeted-sandbox.log` and its `.json` summary (11 hard-link permission errors).
This consolidated evidence update changes documentation only. Source and test Git blobs
remain exactly the independently tested `9698794` candidate. The final Library bundle
contains the complete committed source, the patch series and this report; its manifest
records per-file hashes. No live probe or integration/release action is authorized by
these test results. The next decision is whether to integrate the reviewed candidate
and separately authorize a bounded live probe.
