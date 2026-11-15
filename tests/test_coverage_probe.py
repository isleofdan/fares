import contextlib
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fares import config, coverage_probe as probe


class Blocked(Exception):
    pass


class CoverageProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name) / "probe.json"
        self.profiles = config.load_profiles()

    def plan(self, **changes):
        args = dict(profiles=self.profiles, routes=["barcelona"], cabins=["business"],
                    start_day=280, end_day=293, step=1, budget=14, today=date(2026, 11, 15))
        args.update(changes)
        return probe.plan(**args)

    def run_probe(self, search, report=None, sleep=lambda _: None):
        # Guard both daily persistence entrypoints, even on failed execution.
        with patch("fares.store.connect", side_effect=AssertionError("daily store touched")), \
                patch("fares.config.capture_log_path", side_effect=AssertionError("daily log touched")):
            return probe.execute(report or self.plan(), search, Blocked, self.output, sleep)

    def test_exact_dates_scope_and_budget(self):
        report = self.plan(cabins=["business", "first"], step=2)
        self.assertEqual(report["planned_queries"], 14)
        self.assertEqual({c["destination"] for c in report["cells"]}, {"BCN"})
        self.assertEqual({c["cabin"] for c in report["cells"]}, {"business", "first"})
        self.assertEqual(report["cells"][0]["depart"], "2027-08-22")
        self.assertEqual(report["cells"][-1]["return"], "2027-09-10")
        self.assertTrue(all(c["itineraries"] is None for c in report["cells"]))

    def test_invalid_scope_rejected_without_output(self):
        for changes in ({"budget": 0}, {"budget": 33}, {"budget": 13}, {"start_day": 0},
                        {"end_day": 294}, {"start_day": 293, "end_day": 280}, {"step": 0},
                        {"step": -1}, {"routes": ["unknown"]}, {"cabins": ["economy"]},
                        {"routes": []}, {"cabins": []}, {"routes": ["barcelona"] * 2},
                        {"cabins": ["business"] * 2}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.plan(**changes)
        self.assertFalse(self.output.exists())

    def test_all_calls_paced_and_empty_distinct_from_observed(self):
        calls, sleeps = [], []
        def search(*args):
            calls.append(args)
            return SimpleNamespace(status=200, itineraries=[{"price": 4000}] if len(calls) == 1 else [])
        original = self.plan()
        result = self.run_probe(search, original, sleeps.append)
        self.assertTrue(result["complete"])
        self.assertEqual(result["attempted_queries"], 14)
        self.assertEqual(len(calls), 14)
        self.assertEqual(sleeps, [2.0] * 13)
        self.assertTrue(all(c[:2] == ("BCN", "business") for c in calls))
        self.assertEqual(result["cells"][0]["state"], "observed")
        self.assertEqual(result["cells"][1]["state"], "empty")
        self.assertEqual(original["attempted_queries"], 0)
        self.assertEqual(json.loads(self.output.read_text()), result)
        with self.assertRaises(FileExistsError):
            self.run_probe(search)
        self.assertEqual(len(calls), 14)

    def test_refusal_error_and_malformed_responses_stop_without_retry(self):
        for failure, state in ((Blocked("HTTP 429"), "blocked"), (TimeoutError("timeout"), "error"),
                               (SimpleNamespace(status=429, itineraries=[]), "error"),
                               (SimpleNamespace(status=200, itineraries=None), "error"),
                               (SimpleNamespace(status=200, itineraries=[object()]), "error")):
            with self.subTest(failure=failure):
                self.output = Path(self.tmp.name) / (str(id(failure)) + ".json")
                calls = []
                def search(*args):
                    calls.append(args)
                    if len(calls) == 1:
                        return SimpleNamespace(status=200, itineraries=[])
                    if isinstance(failure, Exception):
                        raise failure
                    return failure
                result = self.run_probe(search)
                self.assertFalse(result["complete"])
                self.assertEqual(len(calls), 2)
                self.assertEqual(result["stop_reason"], state)
                self.assertEqual(result["cells"][1]["state"], state)
                self.assertIsNone(result["cells"][1]["itineraries"])
                self.assertTrue(all(c["state"] == "not_attempted" for c in result["cells"][2:]))

    def test_interruption_during_search_checkpoints_unknown(self):
        def search(*args):
            checkpoint = json.loads(self.output.read_text())
            self.assertEqual(checkpoint["cells"][0]["state"], "in_flight")
            self.assertEqual(checkpoint["attempted_queries"], 1)
            raise KeyboardInterrupt
        result = self.run_probe(search)
        self.assertFalse(result["complete"])
        self.assertEqual(result["stop_reason"], "interrupted")
        self.assertEqual(result["cells"][0]["state"], "interrupted")
        self.assertIsNone(result["cells"][0]["itineraries"])
        self.assertEqual(json.loads(self.output.read_text()), result)

    def test_interruption_during_pause_preserves_observed_and_unattempted(self):
        def sleep(_):
            raise KeyboardInterrupt
        result = self.run_probe(lambda *a: SimpleNamespace(status=200, itineraries=[]), sleep=sleep)
        self.assertEqual(result["attempted_queries"], 1)
        self.assertEqual(result["cells"][0]["state"], "empty")
        self.assertEqual(result["cells"][1]["state"], "not_attempted")
        self.assertEqual(result["stop_reason"], "interrupted")

    def test_execution_rejects_bad_budget_or_replay(self):
        for mutation in ({"budget": 13}, {"budget": 33}, {"attempted_queries": 1}, {"planned_queries": 1}):
            report = self.plan()
            report.update(mutation)
            with self.assertRaises(ValueError):
                self.run_probe(lambda *a: self.fail("search called"), report)
        self.assertFalse(self.output.exists())

    def test_output_errors_precede_search(self):
        for output in (Path(self.tmp.name) / "fares.sqlite", Path(self.tmp.name) / "missing" / "x.json"):
            self.output = output
            with self.assertRaises((ValueError, FileNotFoundError)):
                self.run_probe(lambda *a: self.fail("search called"))

    def argv(self):
        return ["--route", "barcelona", "--cabin", "business", "--start-day", "280",
                "--end-day", "293", "--budget", "14"]

    def test_cli_default_plan_never_locks_imports_source_or_writes(self):
        with patch.object(probe, "collector_lock", side_effect=AssertionError("locked")), \
                patch.object(probe, "execute", side_effect=AssertionError("executed")), \
                patch.dict(sys.modules, {"fares.gflights": None}), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(probe.main(self.argv()), 0)
        report = json.loads(out.getvalue())
        self.assertEqual(report["stop_reason"], "planned")
        self.assertEqual(report["planned_queries"], 14)
        self.assertEqual(list(Path(self.tmp.name).iterdir()), [])

    def test_cli_requires_run_and_output_together(self):
        for extra in (["--run"], ["--output", str(self.output)]):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                probe.main(self.argv() + extra)

    def test_cli_run_exit_codes_with_stub_source(self):
        from fares import gflights
        for response, expected in ((SimpleNamespace(status=200, itineraries=[]), 0),
                                   (gflights.Blocked("refused"), 1), (KeyboardInterrupt(), 130)):
            output = Path(self.tmp.name) / f"exit-{expected}.json"
            def search(*args):
                if isinstance(response, BaseException):
                    raise response
                return response
            # One cell requires no pause; lock itself is separately tested above.
            argv = ["--route", "barcelona", "--cabin", "business", "--start-day", "293",
                    "--end-day", "293", "--budget", "1", "--run", "--output", str(output)]
            with patch.object(probe, "collector_lock", contextlib.nullcontext), \
                    patch.object(gflights, "search", search), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(probe.main(argv), expected)
            self.assertEqual(json.loads(output.read_text())["attempted_queries"], 1)

    def test_lock_contention_prevents_execution(self):
        with patch.object(probe, "collector_lock", side_effect=RuntimeError("capture locked")), \
                patch.object(probe, "execute", side_effect=AssertionError("executed")), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            probe.main(self.argv() + ["--run", "--output", str(self.output)])
        self.assertFalse(self.output.exists())

    def test_lock_protocol_and_release_on_interrupt(self):
        calls = []
        fake = SimpleNamespace(LOCK_EX=2, LOCK_NB=4, LOCK_UN=8,
                               flock=lambda stream, flags: calls.append((stream.name, flags)))
        with patch.dict(sys.modules, {"fcntl": fake}), patch.object(config, "DATA_DIR", Path(self.tmp.name)):
            with self.assertRaises(KeyboardInterrupt):
                with probe.collector_lock():
                    raise KeyboardInterrupt
        self.assertEqual([flags for _, flags in calls], [6, 8])
        self.assertTrue(all(Path(path).name == "capture.lock" for path, _ in calls))

    def test_actual_lock_refusal_does_not_unlock_another_owner(self):
        calls = []
        def flock(stream, flags):
            calls.append(flags)
            raise BlockingIOError
        fake = SimpleNamespace(LOCK_EX=2, LOCK_NB=4, LOCK_UN=8, flock=flock)
        with patch.dict(sys.modules, {"fcntl": fake}), patch.object(config, "DATA_DIR", Path(self.tmp.name)):
            with self.assertRaisesRegex(RuntimeError, "another capture"):
                with probe.collector_lock():
                    self.fail("lock acquired")
        self.assertEqual(calls, [6])

    def test_unsupported_lock_platform_fails_closed(self):
        with patch.dict(sys.modules, {"fcntl": None}), self.assertRaisesRegex(RuntimeError, "POSIX"):
            with probe.collector_lock():
                self.fail("lock acquired")


if __name__ == "__main__":
    unittest.main()
