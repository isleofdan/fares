import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from fares.houston_probe import probe, week_evidence
from fares import store


class Blocked(Exception):
    pass


class ProbeTests(unittest.TestCase):
    def test_nine_and_no_replay(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'probe.json'
            calls, sleeps = [], []
            def search(*args):
                calls.append(args)
                return SimpleNamespace(itineraries=[])
            result = probe(search, Blocked, out, sleeps.append, date(2026, 11, 14))
            self.assertTrue(result['complete'])
            self.assertEqual(len(calls), 9)
            self.assertEqual(len(sleeps), 8)
            self.assertTrue(all(x[0:2] == ('IAH', 'business') for x in calls))
            with self.assertRaises(FileExistsError):
                probe(search, Blocked, out, sleeps.append, date(2026, 11, 14))
            self.assertEqual(len(calls), 9)

    def test_first_block_stops_and_keeps_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'probe.json'
            def search(*args):
                raise Blocked('bot check')
            result = probe(search, Blocked, out, lambda _: None, date(2026, 11, 14))
            self.assertFalse(result['complete'])
            self.assertEqual(len(result['cells']), 1)
            self.assertEqual(json.loads(out.read_text())['cells'][0]['state'], 'blocked')

    def test_no_past_dates(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                probe(None, Blocked, Path(d)/'x.json', today=date(2027, 1, 1))

    def test_empty_store_read_only(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'fares.sqlite'
            conn = store.connect(path); conn.close()
            before = path.read_bytes()
            self.assertEqual(week_evidence(path)['comparisons'], [])
            self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
