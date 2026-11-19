"""Real Flask contract tests; PG cases require the guarded local test database."""
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime
import unittest
from unittest.mock import patch
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def events():
    result=[]
    for i,key in enumerate(list('.tie5Roanl')+['Enter']):
        result += [{'key':key,'type':'down','t':i*30}, {'key':key,'type':'up','t':i*30+50}]
    return sorted(result,key=lambda e:e['t'])  # overlapping keys / negative flight are legitimate


class CollectionContract:
    def prepare(self):
        self.pid=self.client.get('/api/get-id').json['participant_id']

    def payload(self,**extra):
        result=dict(participant_id=self.pid,session=1,device_id='MAY01_BANPHIM01',events=events(),request_id=uuid.uuid4().hex)
        result.update(extra)
        return result

    def post(self,data=None):
        return self.client.post('/api/submit-sample',json=self.payload() if data is None else data)

    def records(self):
        return self.web.read_records(self.pid)

    def seed(self,rows):
        if self.web.PG is not None:
            with self.web.PG.transaction():
                for row in rows:self.web.PG.append_sample(self.pid,row)
        else:
            combined=self.records()+rows
            self.web.collected_file(self.pid).write_text('\n'.join(json.dumps(r) for r in combined),encoding='utf-8')

    def test_device_server_metadata_export_and_resume(self):
        p=self.payload(rep=999,collected_at='client-clock',collection_schema_version=-1)
        response=self.post(p);self.assertEqual(response.status_code,200,response.json)
        record=self.records()[0]
        self.assertEqual(record['device_id'],'MAY01_BANPHIM01')
        self.assertEqual(record['rep'],1);self.assertEqual(record['collection_schema_version'],3)
        self.assertIsNotNone(datetime.fromisoformat(record['collected_at'].replace('Z','+00:00')).utcoffset())
        self.assertEqual(self.client.get('/api/participant/'+self.pid).json['sessions']['1'],1)
        with zipfile.ZipFile(io.BytesIO(self.client.get('/admin/export',headers={'X-Admin-Key':'local-test-admin'}).data)) as z:
            exported=json.loads(z.read('collected/'+self.pid+'.jsonl').splitlines()[0])
        self.assertEqual(exported,record)
        # A new client session can continue the same participant on another declared device.
        self.client=self.web.app.test_client()
        p=self.payload();p['device_id']='MAY02_BANPHIM02'
        self.assertEqual(self.post(p).json['rep'],2)
        self.assertEqual([r['device_id'] for r in self.records()],['MAY01_BANPHIM01','MAY02_BANPHIM02'])

    def test_invalid_devices_rejected_without_writes(self):
        for device in [None,'','a b','../x','a'*41,True,[], 'máy01','A\n']:
            p=self.payload();p['device_id']=device
            self.assertEqual(self.post(p).status_code,400)
        p=self.payload();del p['device_id']
        self.assertEqual(self.post(p).status_code,400)
        self.assertEqual(self.records(),[])

    def test_bad_events_rejected_without_writes(self):
        bads=[events()[:-1],list(reversed(events())),
              [dict(key='x',type='up',t=0)]+events(),[events()[0]]+events()]
        for field,value in [('t',-1),('t',True),('t',10**400),('type',[]),('key',{}),('code',False)]:
            bad=events();bad[0][field]=value;bads.append(bad)
        for bad in bads:
            p=self.payload();p['events']=bad
            self.assertEqual(self.post(p).status_code,400)
        self.assertEqual(self.records(),[])

    def test_modifier_and_uppercase_release_accepted_codes_preserved(self):
        p=self.payload()
        for e in p['events']:
            e['code']='Enter' if e['key']=='Enter' else 'Key'+e['key'].upper()
            if e['key']=='R' and e['type']=='up':e['key']='r'
        p['events'] += [dict(key='Shift',type='down',t=0),dict(key='Shift',type='up',t=400)]
        p['events'].sort(key=lambda e:e['t'])
        self.assertEqual(self.post(p).status_code,200)
        self.assertEqual(self.records()[0]['events'],p['events'])

    def test_legacy_gap_appends_without_collision_or_rewriting(self):
        rows=[dict(participant_id=self.pid,session=1,rep=rep,events=events()) for rep in [1,3]]
        self.seed(rows)
        response=self.post()
        self.assertEqual(response.status_code,200)
        self.assertEqual((response.json['rep'],response.json['count']),(4,3))
        self.assertEqual(self.records()[:2],rows)
        self.assertNotIn('device_id',self.records()[0])

    def test_duplicate_legacy_history_blocks_append(self):
        row=dict(participant_id=self.pid,session=1,rep=1,events=events())
        self.seed([row,row]);before=self.records()
        response=self.post()
        self.assertEqual(response.status_code,409)
        self.assertEqual(response.json['issues'],['collection_history_needs_review'])
        self.assertEqual(self.records(),before)

    def test_max_samples_uses_count_and_session_isolation(self):
        rows=[dict(participant_id=self.pid,session=1,rep=i+2,events=events()) for i in range(40)]
        self.seed(rows)
        self.assertEqual(self.post().status_code,409)
        p=self.payload();p['session']=2
        self.assertEqual(self.post(p).json['rep'],1)
        self.assertEqual(len(self.records()),41)

    def test_same_request_returns_original_rep_and_latest_count(self):
        p=self.payload();first=self.post(p)
        self.assertFalse(first.json['replayed'])
        self.assertEqual(self.post().json['rep'],2)
        before=self.records()
        repeated=self.post(p)
        self.assertEqual(repeated.status_code,200)
        self.assertEqual((repeated.json['rep'],repeated.json['count']),(1,2))
        self.assertTrue(repeated.json['replayed'])
        self.assertEqual(self.records(),before)

    def test_request_id_conflict_does_not_replace_original(self):
        p=self.payload();self.assertEqual(self.post(p).status_code,200)
        before=self.records()
        for field,value in [('device_id','OTHER_DEVICE'),('session',2),
                            ('events',[dict(e,t=e['t']+100) for e in events()])]:
            altered=dict(p);altered[field]=value
            response=self.post(altered)
            self.assertEqual(response.status_code,409)
            self.assertIn('request_id_payload_conflict',response.json['issues'])
        self.assertEqual(self.records(),before)

    def test_request_id_required_and_validated(self):
        for value in [None,'',True,[],{},'a'*31,'A'*32,'../x', 'a'*33]:
            self.assertEqual(self.post(self.payload(request_id=value)).status_code,400)
        p=self.payload();del p['request_id']
        self.assertEqual(self.post(p).status_code,400)
        self.assertEqual(self.records(),[])

    def test_replay_still_succeeds_when_session_full(self):
        p=self.payload();self.assertEqual(self.post(p).status_code,200)
        self.seed([dict(participant_id=self.pid,session=1,rep=i,events=events()) for i in range(2,41)])
        response=self.post(p)
        self.assertEqual(response.status_code,200)
        self.assertEqual((response.json['rep'],response.json['count']),(1,40))
        self.assertEqual(self.post().status_code,409)
        self.assertEqual(len(self.records()),40)

    def test_replay_survives_application_reimport(self):
        p=self.payload();self.assertEqual(self.post(p).status_code,200)
        spec=importlib.util.spec_from_file_location('restarted_'+uuid.uuid4().hex,ROOT/'app.py')
        fresh=importlib.util.module_from_spec(spec);spec.loader.exec_module(fresh)
        response=fresh.app.test_client().post('/api/submit-sample',json=p)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json['replayed'])
        self.assertEqual(len(fresh.read_records(self.pid)),1)


class FileCollectionAPI(CollectionContract,unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(prefix='kg-collection-contract-')
        self.environment=patch.dict(os.environ,{'KEYGUARD_STORAGE':'file','DATABASE_URL':'',
            'KEYGUARD_DATA_DIR':self.folder.name,'KEYGUARD_ADMIN_KEY':'local-test-admin'})
        self.environment.start()
        spec=importlib.util.spec_from_file_location('collection_file_'+uuid.uuid4().hex,ROOT/'app.py')
        self.web=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.web)
        self.client=self.web.app.test_client();self.prepare()

    def tearDown(self):
        self.environment.stop();self.folder.cleanup()

    def test_malformed_file_is_not_silently_skipped(self):
        path=self.web.collected_file(self.pid);path.write_text('{broken\n')
        before=path.read_bytes()
        self.assertEqual(self.post().status_code,409)
        self.assertEqual(path.read_bytes(),before)


@unittest.skipUnless(os.environ.get('KEYGUARD_TEST_DATABASE_URL'),'Local PostgreSQL URL required')
class PostgresCollectionAPI(CollectionContract,unittest.TestCase):
    def setUp(self):
        import sys
        sys.path.insert(0,str(ROOT/'tests'))
        from test_postgres_storage import PostgresIntegrationTest
        PostgresIntegrationTest.setUp(self);self.prepare()

    def tearDown(self):
        from test_postgres_storage import PostgresIntegrationTest
        PostgresIntegrationTest.tearDown(self)

    def test_simultaneous_same_request_is_inserted_once(self):
        from concurrent.futures import ThreadPoolExecutor
        p=self.payload()
        def submit(_):
            with self.web.app.test_client() as c:
                r=c.post('/api/submit-sample',json=p)
                return r.status_code,r.json
        with ThreadPoolExecutor(max_workers=8) as pool:responses=list(pool.map(submit,range(8)))
        self.assertTrue(all(status==200 and body['rep']==1 for status,body in responses))
        self.assertEqual(sum(not body['replayed'] for _,body in responses),1)
        self.assertEqual(len(self.records()),1)

    def test_concurrent_conflicting_request_only_one_wins(self):
        from concurrent.futures import ThreadPoolExecutor
        p=self.payload();other=dict(p,device_id='OTHER_DEVICE')
        def submit(payload):
            with self.web.app.test_client() as c:return c.post('/api/submit-sample',json=payload).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:statuses=list(pool.map(submit,[p,other]))
        self.assertEqual(sorted(statuses),[200,409]);self.assertEqual(len(self.records()),1)

    def test_failed_write_rolls_back_request_and_can_retry(self):
        original=self.web.PG.append_sample
        def fail_after_insert(*args):
            original(*args)
            raise RuntimeError('Synthetic failure after insert')
        p=self.payload()
        with patch.object(self.web.PG,'append_sample',side_effect=fail_after_insert):
            self.assertEqual(self.post(p).status_code,500)
        self.assertEqual(self.records(),[])
        response=self.post(p)
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json['replayed']);self.assertEqual(len(self.records()),1)


if __name__=='__main__':unittest.main()
