import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from scripts.collection_preflight import audit, record_issues


def sample():
    events=[]
    # Overlapping keys are valid, with negative flight time.
    for i,key in enumerate(list('.tie5Roanl')+['Enter']):
        events.extend([dict(key=key,type='down',t=i*30), dict(key=key,type='up',t=i*30+50)])
    return dict(participant_id='TEST_ONLY',session=1,rep=1,device_id='DEVICE_TEST',
                collected_at='2026-11-15T10:00:00+07:00',events=sorted(events,key=lambda e:e['t']))


class PreflightTests(unittest.TestCase):
    def test_valid_overlap_and_modifier(self):
        r=sample()
        r['events'] += [dict(key='Shift',type='down',t=0),dict(key='Shift',type='up',t=400)]
        r['events'].sort(key=lambda e:e['t'])
        self.assertEqual(record_issues(r)[0],[])

    def test_missing_metadata_no_invention(self):
        r=sample(); del r['device_id']; r['collected_at']='2026-11-15T10:00:00'
        self.assertEqual(set(record_issues(r)[0]),{'device_id_missing','collected_at_missing_or_timezone_invalid'})
        self.assertNotIn('device_id',r)

    def test_invalid_pairs_order_repeat_and_case(self):
        mutations=[lambda r:r['events'].pop(),
                   lambda r:r['events'].insert(0,dict(key='x',type='up',t=0)),
                   lambda r:r['events'].reverse(),
                   lambda r:r['events'].insert(1,dict(r['events'][0])),
                   lambda r:r['events'][0].update(key='x')]
        wanted=['down_without_up','up_without_down','event_order_not_monotonic',
                'repeated_down_without_up','phrase_or_case_mismatch']
        for change,code in zip(mutations,wanted):
            r=sample();change(r);self.assertIn(code,record_issues(r)[0])

    def test_same_physical_code_and_uppercase_release(self):
        r=sample()
        for e in r['events']:
            e['code']='Enter' if e['key']=='Enter' else 'Key'+e['key'].upper()
            if e['key']=='R' and e['type']=='up': e['key']='r'
        self.assertEqual(record_issues(r)[0],[])

    def test_invalid_json_shape_nonfinite_and_fields(self):
        for r in [None, [], {'session':True}, dict(sample(),rep=0)]:
            self.assertTrue(record_issues(r)[0])
        for value in [True,float('inf'),-1]:
            r=sample();r['events'][0]['t']=value
            self.assertIn('event_time_invalid',record_issues(r)[0])

    def test_all_duplicate_rows_across_files_even_invalid_marked_and_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=Path(tmp)/'a.jsonl',Path(tmp)/'b.jsonl'
            bad=sample();del bad['device_id']
            a.write_text(json.dumps(bad)+'\n',encoding='utf-8')
            b.write_text(json.dumps(sample())+'\n{bad\nNaN\n',encoding='utf-8')
            before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (a,b)]
            report=audit([a,b])
            self.assertEqual(report['records'],4)
            self.assertEqual(report['duplicate_key_groups'],1)
            self.assertEqual(report['issue_counts']['duplicate_participant_session_rep'],2)
            self.assertEqual(report['issue_counts']['json_invalid'],2)
            self.assertNotIn('TEST_ONLY',json.dumps(report))
            self.assertEqual(before,[hashlib.sha256(p.read_bytes()).hexdigest() for p in (a,b)])
            with self.assertRaises(ValueError):audit([a,a])

    def test_empty_and_duplicate_json_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'empty.jsonl';p.write_text('')
            self.assertEqual(audit([p])['status'],'needs_review')
            p.write_text('{"rep":1,"rep":2}\n')
            self.assertEqual(audit([p])['issue_counts'],{'json_invalid':1})

    def test_malformed_event_types_and_codes_do_not_crash(self):
        for field,value in [('type',[]),('key',{}),('code',False)]:
            r=sample();r['events'][0][field]=value
            self.assertTrue(record_issues(r)[0])


if __name__=='__main__': unittest.main()
