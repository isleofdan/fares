import tempfile
import unittest
from pathlib import Path
from fares import store, page


class CandidatesTest(unittest.TestCase):
    def test_sample_preserves_dates_and_evidence_without_selecting_return(self):
        with tempfile.TemporaryDirectory() as d:
            conn = store.connect(Path(d)/'test.sqlite')
            try:
                sid = store.start_sweep(conn, '2026-11-14T00:00:00Z','Google Flights',14)
                base = dict(sweep_id=sid,captured_at='2026-11-14T00:00:00Z',route='houston',cabin='business',origin_airport='NRT',dest_airport='IAH',depart_date='2026-12-28',return_date='2027-01-04',carriers='Example',carrier_codes='EX',stops=0,via='',segment_cabins='business',duration_min=720,price=4000,currency='USD',source='Google Flights',fare_code=None,result_list='best')
                store.insert_fares(conn,[dict(base,flight_numbers=f'EX{i}',price=4000+i) for i in range(8)])
                store.insert_fares(conn,[dict(base,flight_numbers='EX0',price=4100)])
                store.finish_sweep(conn,sid,'2026-11-14T00:01:00Z',1,0,9,False,'complete',True)
                full, scan = page.latest_captures(conn)
                rows = page.houston_candidates(conn,full,scan)
                self.assertEqual(len(rows),5)
                self.assertEqual(len({r['id'] for r in rows}),5)
                self.assertEqual(rows[0]['price'],4000)
                self.assertEqual(rows[0]['return_date'],'2027-01-04')
                self.assertEqual(rows[0]['captured_at'],'2026-11-14T00:00:00Z')
                self.assertNotIn('return_flights',rows[0])
                self.assertEqual(rows,page.houston_candidates(conn,full,scan))
            finally:
                conn.close()


if __name__ == '__main__':
    unittest.main()
